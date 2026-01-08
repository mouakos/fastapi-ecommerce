from fastapi import APIRouter

from app.api.v1.routes.category import router as category_router
from app.api.v1.routes.product import router as product_router

router = APIRouter()

router.include_router(product_router)
router.include_router(category_router)
