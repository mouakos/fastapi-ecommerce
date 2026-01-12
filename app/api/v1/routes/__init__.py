from fastapi import APIRouter

from app.api.v1.routes.auth_route import auth_router
from app.api.v1.routes.cart_route import cart_router
from app.api.v1.routes.category_route import category_router
from app.api.v1.routes.meta_route import meta_router
from app.api.v1.routes.order_route import order_route
from app.api.v1.routes.product_route import product_router
from app.api.v1.routes.user_route import user_router
from app.api.v1.routes.wishlist_route import wishlist_route

router = APIRouter()

router.include_router(meta_router)
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(product_router)
router.include_router(category_router)
router.include_router(cart_router)
router.include_router(order_route)
router.include_router(wishlist_route)
