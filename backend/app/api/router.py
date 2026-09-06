"""Central API router aggregating module routers."""

from fastapi import APIRouter

from app.modules.approvals.router import router as approvals_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.customers.router import router as customers_router
from app.modules.discounts.router import router as discounts_router
from app.modules.pricing.router import router as pricing_router
from app.modules.quotations.order_router import order_router
from app.modules.quotations.router import pipeline_router
from app.modules.quotations.router import router as quotations_router
from app.modules.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(customers_router)
api_router.include_router(catalog_router)
api_router.include_router(pricing_router)
api_router.include_router(discounts_router)
api_router.include_router(approvals_router)
api_router.include_router(quotations_router)
api_router.include_router(pipeline_router)
api_router.include_router(order_router)


