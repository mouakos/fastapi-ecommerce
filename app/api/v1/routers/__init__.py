from fastapi import APIRouter

from app.api.v1.routers.addresses import router as address_router
from app.api.v1.routers.admin import router as admin_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.carts import router as cart_router
from app.api.v1.routers.categories import router as category_router
from app.api.v1.routers.healthcheck import router as health_check_router
from app.api.v1.routers.orders import router as order_router
from app.api.v1.routers.payments import router as payment_router
from app.api.v1.routers.products import router as product_router
from app.api.v1.routers.reviews import router as review_router
from app.api.v1.routers.users import router as user_router
from app.api.v1.routers.wishlists import router as wishlist_router

router = APIRouter()

router.include_router(health_check_router, prefix="/health", tags=["Health Check"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(product_router, prefix="/products", tags=["Products"])
router.include_router(category_router, prefix="/categories", tags=["Categories"])
router.include_router(cart_router, prefix="/cart", tags=["Cart"])
router.include_router(order_router, prefix="/orders", tags=["Orders"])
router.include_router(wishlist_router, prefix="/wishlist", tags=["Wishlist"])
router.include_router(payment_router, prefix="/payments", tags=["Payments"])
router.include_router(review_router, prefix="/reviews", tags=["Reviews"])
router.include_router(admin_router, prefix="/admin", tags=["Admin"])
router.include_router(address_router, prefix="/addresses", tags=["Addresses"])
