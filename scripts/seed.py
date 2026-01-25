"""Seed the database with realistic end-to-end data.

This script is intended for local development.

What it does:
        - Optional `--reset`: drops and recreates all tables (DANGER: data loss).
        - Seeds categories, products, users, addresses, carts, orders, payments,
          reviews, and wishlist items.

Run examples:
        python scripts/seed.py --reset
        python scripts/seed.py --reset --seed 123 --users 50 --products 200
"""

from __future__ import annotations

import argparse
import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

import phonenumbers
import ulid
from faker import Faker
from phonenumbers import PhoneNumberFormat, PhoneNumberType
from phonenumbers.phonenumberutil import example_number_for_type
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, async_engine
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.order import Order, OrderAddress, OrderAddressKind, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.review import Review, ReviewStatus
from app.models.user import User, UserRole
from app.models.wishlist_item import WishlistItem
from app.utils.datetime import utcnow

SEED_TARGETS: set[str] = {
    "categories",
    "products",
    "users",
    "addresses",
    "carts",
    "orders",
    "wishlist",
    "reviews",
}

# Dependencies for a target to be meaningful.
_TARGET_DEPS: dict[str, set[str]] = {
    "products": {"categories"},
    "addresses": {"users"},
    "carts": {"users", "products"},
    "orders": {"users", "addresses", "products"},
    "wishlist": {"users", "products"},
    "reviews": {"users", "products"},
}


def _parse_targets(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip().lower() for part in value.split(",") if part.strip()}


def _resolve_targets(*, only: set[str], skip: set[str]) -> set[str]:
    selected = set(SEED_TARGETS) if not only else set(only)

    unknown = (selected | skip) - SEED_TARGETS
    if unknown:
        raise ValueError(
            f"Unknown seed targets: {sorted(unknown)}. Allowed: {sorted(SEED_TARGETS)}"
        )

    # If a target is requested, include its dependencies automatically.
    changed = True
    while changed:
        before = set(selected)
        for target in list(selected):
            selected |= _TARGET_DEPS.get(target, set())
        changed = selected != before

    if not skip:
        return selected

    # Skip also removes dependent targets (FK-safe + no missing prerequisites).
    reverse: dict[str, set[str]] = {t: set() for t in SEED_TARGETS}
    for target, deps in _TARGET_DEPS.items():
        for dep in deps:
            reverse[dep].add(target)

    to_remove = set(skip)
    queue = list(skip)
    while queue:
        dep = queue.pop()
        for dependent in reverse.get(dep, set()):
            if dependent not in to_remove:
                to_remove.add(dependent)
                queue.append(dependent)

    return selected - to_remove


@dataclass(frozen=True)
class SeedCounts:
    """Counts for each entity to seed."""

    categories: int
    child_categories: int
    products: int
    users: int
    carts: int
    max_cart_items: int
    max_orders_per_user: int
    max_items_per_order: int
    wishlist_items_per_user: int
    review_probability: float


def _unique_slug(value: str, *, used: set[str], max_length: int = 100) -> str:
    base = slugify(value)[:max_length].strip("-") or "item"
    candidate = base
    i = 2
    while candidate in used:
        suffix = f"-{i}"
        candidate = (base[: max_length - len(suffix)] + suffix).strip("-")
        i += 1
    used.add(candidate)
    return candidate


def _money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _apply_percentage_discount(amount: Decimal, discount_percentage: int) -> Decimal:
    """Return amount after applying an integer percentage discount."""
    discount = Decimal(discount_percentage) / Decimal("100")
    factor = Decimal("1") - discount
    return (amount * factor).quantize(Decimal("0.01"))


def _tax_rate_for_country(country_code: str) -> Decimal:
    """Very small dev-only tax heuristic.

    For real tax logic, integrate a provider (Stripe Tax / TaxJar / Avalara).
    """
    eu_like = {
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SE",
        "SI",
        "SK",
    }
    return Decimal("0.20") if country_code.upper() in eu_like else Decimal("0.00")


_VALID_SEED_COUNTRIES: tuple[str, ...] = (
    "US",
    "DE",
    "FR",
    "NL",
    "ES",
    "IT",
    "GB",
    "CA",
    "CH",
    "AT",
)


def _valid_country_code() -> str:
    return random.choice(_VALID_SEED_COUNTRIES)


def _valid_e164_phone_number(country_code: str) -> str:
    """Generate a valid E.164 phone number for a given ISO alpha-2 region."""
    number = example_number_for_type(country_code, PhoneNumberType.MOBILE)
    if number is None:
        number = example_number_for_type(country_code, PhoneNumberType.FIXED_LINE_OR_MOBILE)
    if number is None:
        # Fallback to a known-valid US example.
        return "+12025550123"
    return phonenumbers.format_number(number, PhoneNumberFormat.E164)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the seeding script."""
    parser = argparse.ArgumentParser(description="Seed the database with Faker data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    parser.add_argument("--seed", type=int, default=123, help="Random seed for deterministic data")
    parser.add_argument(
        "--show-logins",
        action="store_true",
        help="Print example seeded login credentials (dev only).",
    )
    parser.add_argument(
        "--only",
        default=None,
        help=(
            "Comma-separated list of targets to seed (dependencies included automatically). "
            f"Allowed: {', '.join(sorted(SEED_TARGETS))}"
        ),
    )
    parser.add_argument(
        "--skip",
        default=None,
        help=(
            "Comma-separated list of targets to skip (also skips dependents). "
            f"Allowed: {', '.join(sorted(SEED_TARGETS))}"
        ),
    )
    parser.add_argument("--users", type=int, default=25, help="Number of users to create")
    parser.add_argument("--products", type=int, default=120, help="Number of products to create")
    parser.add_argument("--categories", type=int, default=8, help="Number of top-level categories")
    return parser.parse_args(argv)


async def _reset_db(*, async_engine: AsyncEngine) -> None:
    """Drop and recreate all tables."""
    logger.warning("seed_reset_db_start")
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.warning("seed_reset_db_done")


async def _ensure_superuser(
    *,
    session: AsyncSession,
) -> User:
    """Ensure configured superuser exists and return it."""
    stmt = await session.exec(select(User).where(User.email == settings.superuser_email))
    user = stmt.first()
    if user:
        return user

    admin = User(
        email=settings.superuser_email,
        hashed_password=hash_password(settings.superuser_password),
        is_superuser=True,
        role=UserRole.ADMIN,
        is_active=True,
        first_name="Admin",
        last_name="User",
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def _seed_categories(
    *,
    session: AsyncSession,
    faker: Faker,
    seed_counts: SeedCounts,
    slug_used_categories: set[str],
) -> list[Category]:
    logger.info("seed_categories_start")
    parents: list[Category] = []
    faker.unique.clear()
    for _ in range(seed_counts.categories):
        name = f"{faker.unique.word().title()} {faker.word().title()}"[:100]
        parents.append(
            Category(
                name=name,
                slug=_unique_slug(name, used=slug_used_categories),
                description=faker.sentence(nb_words=12)[:500],
                image_url=faker.image_url(width=640, height=480),
            )
        )
    session.add_all(parents)
    await session.commit()

    children: list[Category] = []
    for parent in parents:
        for _ in range(seed_counts.child_categories):
            name = f"{faker.unique.word().title()} {parent.name}"[:100]
            children.append(
                Category(
                    name=name,
                    slug=_unique_slug(name, used=slug_used_categories),
                    parent_id=parent.id,
                    description=faker.sentence(nb_words=10)[:500],
                    image_url=faker.image_url(width=640, height=480),
                )
            )
    session.add_all(children)
    await session.commit()
    all_categories = parents + children
    logger.info("seed_categories_done", count=len(all_categories))
    return all_categories


async def _seed_products(
    *,
    session: AsyncSession,
    faker: Faker,
    seed_counts: SeedCounts,
    categories: list[Category],
    slug_used_products: set[str],
) -> list[Product]:
    logger.info("seed_products_start")
    products: list[Product] = []
    for _ in range(seed_counts.products):
        name = faker.unique.catch_phrase()[:255]
        product_slug = _unique_slug(name, used=slug_used_products)
        category = random.choice(categories)
        price = _money(faker.pydecimal(left_digits=3, right_digits=2, positive=True))
        stock = random.randint(0, 200)
        discount_percentage = random.choices(
            [0, 5, 10, 15, 20, 25, 30, 40, 50],
            weights=[60, 8, 8, 6, 5, 4, 3, 3, 3],
            k=1,
        )[0]
        products.append(
            Product(
                name=name,
                slug=product_slug,
                description=faker.paragraph(nb_sentences=3)[:2000],
                price=price,
                stock=stock,
                sku=f"PRD-{ulid.new().str}",
                image_url=faker.image_url(width=800, height=800),
                is_active=True,
                discount_percentage=discount_percentage,
                category_id=category.id,
            )
        )
    session.add_all(products)
    await session.commit()
    logger.info("seed_products_done", count=len(products))
    return products


async def _seed_users(
    *,
    session: AsyncSession,
    faker: Faker,
    seed_counts: SeedCounts,
    show_logins: bool,
) -> tuple[list[User], list[str]]:
    logger.info("seed_users_start")
    users: list[User] = []
    user_country_codes: list[str] = []
    for _ in range(seed_counts.users):
        is_active = random.random() > 0.04
        now = utcnow()
        country_code = _valid_country_code()
        phone_number = _valid_e164_phone_number(country_code)
        users.append(
            User(
                email=faker.unique.email().lower(),
                hashed_password=hash_password("Password123!"),
                first_name=faker.first_name()[:50],
                last_name=faker.last_name()[:50],
                phone_number=phone_number,
                role=UserRole.USER,
                is_superuser=False,
                is_active=is_active,
                newsletter_subscribed=random.random() < 0.35,
                last_login=(now - timedelta(days=random.randint(0, 60))) if is_active else None,
                deleted_at=(now - timedelta(days=random.randint(0, 60))) if not is_active else None,
            )
        )
        user_country_codes.append(country_code)
    session.add_all(users)
    await session.commit()
    logger.info("seed_users_done", count=len(users))

    if show_logins:
        sample_emails = [u.email for u in users[: min(5, len(users))]]
        logger.warning(
            "seed_login_examples",
            password="Password123!",
            emails=sample_emails,
        )

    return users, user_country_codes


async def _seed_addresses(
    *,
    session: AsyncSession,
    faker: Faker,
    users: list[User],
    user_country_codes: list[str],
) -> dict[str, list[Address]]:
    logger.info("seed_addresses_start")
    addresses: list[Address] = []
    user_addresses: dict[str, list[Address]] = {}

    for idx, user in enumerate(users):
        country_code = (
            user_country_codes[idx] if idx < len(user_country_codes) else _valid_country_code()
        )
        shipping = Address(
            user_id=user.id,
            full_name=f"{user.first_name} {user.last_name}".strip() or faker.name(),
            company=faker.company()[:100] if random.random() < 0.2 else None,
            line1=faker.street_address()[:255],
            line2=faker.secondary_address()[:255] if random.random() < 0.3 else None,
            city=faker.city()[:100],
            state=faker.state()[:100] if random.random() < 0.6 else None,
            postal_code=faker.postcode()[:20],
            country=country_code,
            phone_number=user.phone_number,
            is_default_shipping=True,
            is_default_billing=False,
        )
        billing = Address(
            user_id=user.id,
            full_name=shipping.full_name,
            company=shipping.company,
            line1=shipping.line1,
            line2=shipping.line2,
            city=shipping.city,
            state=shipping.state,
            postal_code=shipping.postal_code,
            country=country_code,
            phone_number=shipping.phone_number,
            is_default_shipping=False,
            is_default_billing=True,
        )
        extra: list[Address] = []
        if random.random() < 0.35:
            extra.append(
                Address(
                    user_id=user.id,
                    full_name=shipping.full_name,
                    company=None,
                    line1=faker.street_address()[:255],
                    line2=None,
                    city=faker.city()[:100],
                    state=faker.state()[:100] if random.random() < 0.6 else None,
                    postal_code=faker.postcode()[:20],
                    country=country_code,
                    phone_number=shipping.phone_number,
                    is_default_shipping=False,
                    is_default_billing=False,
                )
            )

        user_addr_list = [shipping, billing, *extra]
        addresses.extend(user_addr_list)
        user_addresses[str(user.id)] = user_addr_list

    session.add_all(addresses)
    await session.commit()
    logger.info("seed_addresses_done", count=len(addresses))
    return user_addresses


async def _seed_carts(
    *,
    session: AsyncSession,
    users: list[User],
    in_stock_products: list[Product],
    seed_counts: SeedCounts,
) -> None:
    logger.info("seed_carts_start")
    carts: list[Cart] = []
    cart_users = random.sample(users, k=min(seed_counts.carts, len(users)))
    for user in cart_users:
        cart = Cart(user_id=user.id)
        session.add(cart)
        await session.flush()
        cart_products = random.sample(
            in_stock_products,
            k=min(len(in_stock_products), random.randint(1, seed_counts.max_cart_items)),
        )
        for product in cart_products:
            unit_price = _apply_percentage_discount(product.price, product.discount_percentage)
            session.add(
                CartItem(
                    cart_id=cart.id,
                    product_id=product.id,
                    quantity=random.randint(1, 3),
                    unit_price=unit_price,
                    product_name=product.name,
                    product_image_url=product.image_url,
                )
            )
        carts.append(cart)
    await session.commit()
    logger.info("seed_carts_done", count=len(carts))


async def _seed_orders(
    *,
    session: AsyncSession,
    faker: Faker,
    users: list[User],
    user_addresses: dict[str, list[Address]],
    in_stock_products: list[Product],
    seed_counts: SeedCounts,
) -> None:
    logger.info("seed_orders_start")
    payments: list[Payment] = []
    order_numbers: set[str] = set()
    order_items_count = 0
    orders_count = 0

    for user in users:
        num_orders = random.randint(0, seed_counts.max_orders_per_user)
        if num_orders == 0:
            continue
        addrs = user_addresses[str(user.id)]
        shipping_addr = next((a for a in addrs if a.is_default_shipping), addrs[0])
        billing_addr = next((a for a in addrs if a.is_default_billing), addrs[0])

        for _ in range(num_orders):
            base = faker.date_time_this_year().strftime("%Y%m%d")
            order_number = f"ORD-{base}-{random.randint(100000, 999999)}"
            while order_number in order_numbers:
                order_number = f"ORD-{base}-{random.randint(100000, 999999)}"
            order_numbers.add(order_number)

            status_choice = random.choices(
                [
                    OrderStatus.PENDING,
                    OrderStatus.PAID,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED,
                    OrderStatus.CANCELED,
                ],
                weights=[30, 25, 20, 15, 10],
                k=1,
            )[0]

            order = Order(
                user_id=user.id,
                status=status_choice,
                total_amount=_money("0.00"),
                order_number=order_number,
            )
            session.add(order)
            await session.flush()

            session.add(
                OrderAddress(
                    order_id=order.id,
                    kind=OrderAddressKind.SHIPPING,
                    full_name=shipping_addr.full_name,
                    company=shipping_addr.company,
                    line1=shipping_addr.line1,
                    line2=shipping_addr.line2,
                    city=shipping_addr.city,
                    state=shipping_addr.state,
                    postal_code=shipping_addr.postal_code,
                    country=shipping_addr.country,
                    phone_number=shipping_addr.phone_number,
                )
            )
            session.add(
                OrderAddress(
                    order_id=order.id,
                    kind=OrderAddressKind.BILLING,
                    full_name=billing_addr.full_name,
                    company=billing_addr.company,
                    line1=billing_addr.line1,
                    line2=billing_addr.line2,
                    city=billing_addr.city,
                    state=billing_addr.state,
                    postal_code=billing_addr.postal_code,
                    country=billing_addr.country,
                    phone_number=billing_addr.phone_number,
                )
            )

            chosen_products = random.sample(
                in_stock_products,
                k=min(
                    len(in_stock_products),
                    random.randint(1, seed_counts.max_items_per_order),
                ),
            )
            subtotal = Decimal("0.00")
            for product in chosen_products:
                qty = random.randint(1, 3)
                unit_price = _apply_percentage_discount(product.price, product.discount_percentage)
                subtotal += unit_price * qty
                session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=qty,
                        unit_price=unit_price,
                        product_name=product.name,
                        product_image_url=product.image_url,
                    )
                )
                order_items_count += 1

            shipping_amount = _money(faker.pydecimal(left_digits=2, right_digits=2, positive=True))
            tax_rate = _tax_rate_for_country(shipping_addr.country)
            tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))

            order.shipping_amount = shipping_amount
            order.tax_amount = tax_amount
            order.total_amount = (subtotal + shipping_amount + tax_amount).quantize(Decimal("0.01"))

            now = utcnow()
            if status_choice in {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED}:
                order.paid_at = now - timedelta(days=random.randint(0, 30))
            if status_choice in {OrderStatus.SHIPPED, OrderStatus.DELIVERED}:
                order.shipped_at = (order.paid_at or now) + timedelta(days=random.randint(1, 5))
            if status_choice == OrderStatus.DELIVERED:
                order.delivered_at = (order.shipped_at or now) + timedelta(
                    days=random.randint(1, 7)
                )
            if status_choice == OrderStatus.CANCELED:
                order.canceled_at = now - timedelta(days=random.randint(0, 30))

            if status_choice == OrderStatus.CANCELED:
                pay_status = PaymentStatus.FAILED
            elif status_choice == OrderStatus.PENDING:
                pay_status = PaymentStatus.PENDING
            else:
                pay_status = PaymentStatus.SUCCESS

            payments.append(
                Payment(
                    order_id=order.id,
                    amount=order.total_amount,
                    currency="usd",
                    payment_method=random.choice(["card", "paypal"]),
                    status=pay_status,
                    transaction_id=str(faker.uuid4()),
                )
            )
            orders_count += 1

    session.add_all(payments)
    await session.commit()
    logger.info(
        "seed_orders_done",
        orders=orders_count,
        order_items=order_items_count,
        payments=len(payments),
    )


async def _seed_wishlist_and_reviews(
    *,
    session: AsyncSession,
    faker: Faker,
    users: list[User],
    products: list[Product],
    admin_user: User | None,
    seed_counts: SeedCounts,
    targets: set[str],
) -> None:
    logger.info("seed_wishlist_reviews_start")
    wishlist_count = 0
    review_count = 0

    for user in users:
        if "wishlist" in targets:
            wishlist_products = random.sample(
                products, k=min(len(products), seed_counts.wishlist_items_per_user)
            )
            for product in wishlist_products:
                session.add(WishlistItem(user_id=user.id, product_id=product.id))
                wishlist_count += 1

        if "reviews" in targets and random.random() < seed_counts.review_probability:
            reviewed_products = random.sample(products, k=min(len(products), random.randint(1, 3)))
            for product in reviewed_products:
                review_status_choice = random.choices(
                    [ReviewStatus.APPROVED, ReviewStatus.PENDING, ReviewStatus.REJECTED],
                    weights=[70, 25, 5],
                    k=1,
                )[0]
                review = Review(
                    user_id=user.id,
                    product_id=product.id,
                    rating=random.randint(1, 5),
                    comment=faker.sentence(nb_words=16)[:1000],
                    status=review_status_choice,
                )
                if review_status_choice in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
                    review.moderated_at = utcnow()
                    review.moderated_by = getattr(admin_user, "id", None)
                session.add(review)
                review_count += 1

    await session.commit()
    logger.info(
        "seed_wishlist_reviews_done",
        wishlist_items=wishlist_count,
        reviews=review_count,
    )


async def _seed_data(
    *,
    session: AsyncSession,
    faker: Faker,
    seed_counts: SeedCounts,
    targets: set[str],
    show_logins: bool,
) -> None:
    """Seed all entities in FK-safe order into the provided session."""
    slug_used_categories: set[str] = set()
    slug_used_products: set[str] = set()

    categories: list[Category] = []
    products: list[Product] = []
    users: list[User] = []
    user_country_codes: list[str] = []
    user_addresses: dict[str, list[Address]] = {}
    admin_user: User | None = None

    if "categories" in targets:
        categories = await _seed_categories(
            session=session,
            faker=faker,
            seed_counts=seed_counts,
            slug_used_categories=slug_used_categories,
        )

    if "products" in targets:
        products = await _seed_products(
            session=session,
            faker=faker,
            seed_counts=seed_counts,
            categories=categories,
            slug_used_products=slug_used_products,
        )

    if "users" in targets:
        users, user_country_codes = await _seed_users(
            session=session,
            faker=faker,
            seed_counts=seed_counts,
            show_logins=show_logins,
        )

    if "users" in targets or "reviews" in targets:
        admin_user = await _ensure_superuser(session=session)
        if show_logins:
            logger.warning(
                "seed_superuser",
                email=settings.superuser_email,
                password_source="settings.superuser_password",
            )

    if "addresses" in targets:
        user_addresses = await _seed_addresses(
            session=session,
            faker=faker,
            users=users,
            user_country_codes=user_country_codes,
        )

    if {"carts", "orders", "wishlist", "reviews"} & targets:
        in_stock_products = [p for p in products if p.stock > 0 and p.is_active]
        if not in_stock_products:
            raise RuntimeError("No in-stock products available to seed carts/orders.")

    if "carts" in targets:
        await _seed_carts(
            session=session,
            users=users,
            in_stock_products=in_stock_products,
            seed_counts=seed_counts,
        )

    if "orders" in targets:
        await _seed_orders(
            session=session,
            faker=faker,
            users=users,
            user_addresses=user_addresses,
            in_stock_products=in_stock_products,
            seed_counts=seed_counts,
        )

    if {"wishlist", "reviews"} & targets:
        await _seed_wishlist_and_reviews(
            session=session,
            faker=faker,
            users=users,
            products=products,
            admin_user=admin_user,
            seed_counts=seed_counts,
            targets=targets,
        )


async def run(argv: Sequence[str] | None = None) -> None:
    """Run the seeding process.

    Imports app modules lazily so `--help` works without environment variables.
    """
    # Delay app imports so `python scripts/seed.py --help` works even without env.
    args = parse_args(argv)

    try:
        targets = _resolve_targets(
            only=_parse_targets(args.only),
            skip=_parse_targets(args.skip),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if not targets:
        return

    random.seed(args.seed)
    faker = Faker()
    faker.seed_instance(args.seed)
    Faker.seed(args.seed)

    seed_counts = SeedCounts(
        categories=args.categories,
        child_categories=2,
        products=args.products,
        users=args.users,
        carts=max(1, int(args.users * 0.6)),
        max_cart_items=6,
        max_orders_per_user=3,
        max_items_per_order=5,
        wishlist_items_per_user=5,
        review_probability=0.55,
    )

    if args.reset:
        await _reset_db(async_engine=async_engine)

    logger.info("seed_targets", targets=sorted(targets))

    async with AsyncSessionLocal() as session:
        await _seed_data(
            session=session,
            faker=faker,
            seed_counts=seed_counts,
            targets=targets,
            show_logins=args.show_logins,
        )


def main() -> None:
    """CLI entrypoint."""
    asyncio.run(run())


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(async_engine.dispose())
