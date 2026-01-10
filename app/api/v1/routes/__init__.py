from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.cart import router as cart_router
from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.product import router as product_router
from app.api.v1.routes.user import router as user_router

router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(product_router)
router.include_router(category_router)
router.include_router(cart_router)
