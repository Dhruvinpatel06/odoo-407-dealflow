"""Customers and Customer Tiers endpoints router."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.exceptions import ForbiddenError, ResourceNotFoundError
from app.models.user import User
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerTierCreateRequest,
    CustomerTierResponse,
    CustomerTierUpdateRequest,
    CustomerUpdate,
)
from app.modules.customers.service import customer_service
from app.modules.fulfillment.schemas import OrderResponse
from app.modules.quotations.schemas import QuotationResponse
from app.modules.subscriptions.schemas import SubscriptionResponse

router = APIRouter()

customer_router = APIRouter(prefix="/customers", tags=["customers"])
tier_router = APIRouter(prefix="/customer-tiers", tags=["customer-tiers"])


# --- Customer Endpoints ---


@customer_router.get(
    "",
    response_model=List[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="List/Search Customers",
)
def list_customers(
    search: Optional[str] = None,
    customer_tier_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[CustomerResponse]:
    """
    List and search B2B customers.
    Used by Sales Rep quotation creation and administrative screens.
    Defaults to returning active customers only.
    """
    customers = customer_service.list_customers(
        db=db,
        search=search,
        customer_tier_id=customer_tier_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [CustomerResponse.model_validate(c) for c in customers]


@customer_router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer",
)
def create_customer(
    request: CustomerCreate,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """
    Create a new B2B customer/account record.
    Accessible to ADMIN, SALES_MANAGER, and SALES_REP.
    """
    customer = customer_service.create_customer(db=db, request=request)
    return CustomerResponse.model_validate(customer)


@customer_router.get(
    "/me",
    response_model=CustomerDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated Customer Profile",
)
def get_current_customer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CustomerDetailResponse:
    """
    Retrieve customer record associated with the authenticated customer user.
    """
    if not current_user.customer_id:
        raise ResourceNotFoundError("No customer record associated with current user")
    customer = customer_service.get_customer_by_id(db=db, customer_id=current_user.customer_id)
    return CustomerDetailResponse.model_validate(customer)


@customer_router.get(
    "/{id}",
    response_model=CustomerDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer Details",
)
def get_customer(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
                UserRole.CUSTOMER,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> CustomerDetailResponse:
    """
    Retrieve customer details including customer tier association.
    Accessible to internal roles and the customer user owning this record.
    """
    if current_user.role == UserRole.CUSTOMER and current_user.customer_id != id:
        raise ForbiddenError("You do not have permission to access another customer's data")
    customer = customer_service.get_customer_by_id(db=db, customer_id=id)
    return CustomerDetailResponse.model_validate(customer)


@customer_router.patch(
    "/{id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Customer",
)
def update_customer(
    id: uuid.UUID,
    request: CustomerUpdate,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """
    Update an existing B2B customer record.
    Accessible to ADMIN, SALES_MANAGER, and SALES_REP.
    """
    customer = customer_service.update_customer(
        db=db, customer_id=id, request=request
    )
    return CustomerResponse.model_validate(customer)


@customer_router.delete(
    "/{id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Customer",
)
def delete_customer(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """
    Deactivate a customer following logical-deactivation convention.
    Accessible to ADMIN and SALES_MANAGER.
    """
    customer = customer_service.deactivate_customer(db=db, customer_id=id)
    return CustomerResponse.model_validate(customer)


@customer_router.get(
    "/{id}/quotations",
    response_model=List[QuotationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Quotation History",
)
def get_customer_quotations(
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
                UserRole.CUSTOMER,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[QuotationResponse]:
    """
    Retrieve quotation history belonging to a specific customer.
    Accessible to internal roles and the customer user owning this record.
    """
    if current_user.role == UserRole.CUSTOMER and current_user.customer_id != id:
        raise ForbiddenError("You do not have permission to access another customer's data")
    quotations = customer_service.get_customer_quotations(
        db=db, customer_id=id, skip=skip, limit=limit
    )
    return [QuotationResponse.model_validate(q) for q in quotations]


@customer_router.get(
    "/{id}/orders",
    response_model=List[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Order History",
)
def get_customer_orders(
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
                UserRole.CUSTOMER,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[OrderResponse]:
    """
    Retrieve order history belonging to a specific customer.
    Accessible to internal roles and the customer user owning this record.
    """
    if current_user.role == UserRole.CUSTOMER and current_user.customer_id != id:
        raise ForbiddenError("You do not have permission to access another customer's data")
    orders = customer_service.get_customer_orders(
        db=db, customer_id=id, skip=skip, limit=limit
    )
    return [OrderResponse.model_validate(o) for o in orders]


@customer_router.get(
    "/{id}/subscriptions",
    response_model=List[SubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Subscription History",
)
def get_customer_subscriptions(
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
                UserRole.CUSTOMER,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[SubscriptionResponse]:
    """
    Retrieve subscription history belonging to a specific customer.
    Accessible to internal roles and the customer user owning this record.
    """
    if current_user.role == UserRole.CUSTOMER and current_user.customer_id != id:
        raise ForbiddenError("You do not have permission to access another customer's data")
    subscriptions = customer_service.get_customer_subscriptions(
        db=db, customer_id=id, skip=skip, limit=limit
    )
    return [SubscriptionResponse.model_validate(s) for s in subscriptions]


# --- Customer Tier Endpoints ---


@tier_router.get(
    "",
    response_model=List[CustomerTierResponse],
    status_code=status.HTTP_200_OK,
    summary="List Customer Tiers",
)
def list_customer_tiers(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[CustomerTierResponse]:
    """List customer tiers with optional active status filtering."""
    tiers = customer_service.list_tiers(
        db=db, is_active=is_active, skip=skip, limit=limit
    )
    return [CustomerTierResponse.model_validate(t) for t in tiers]


@tier_router.post(
    "",
    response_model=CustomerTierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Customer Tier",
)
def create_customer_tier(
    request: CustomerTierCreateRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> CustomerTierResponse:
    """Create a new customer tier."""
    tier = customer_service.create_tier(db=db, request=request)
    return CustomerTierResponse.model_validate(tier)


@tier_router.get(
    "/{id}",
    response_model=CustomerTierResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Customer Tier",
)
def get_customer_tier(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> CustomerTierResponse:
    """Retrieve a customer tier by ID."""
    tier = customer_service.get_tier_by_id(db=db, tier_id=id)
    return CustomerTierResponse.model_validate(tier)


@tier_router.patch(
    "/{id}",
    response_model=CustomerTierResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Customer Tier",
)
def update_customer_tier(
    id: uuid.UUID,
    request: CustomerTierUpdateRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> CustomerTierResponse:
    """Update a customer tier configuration."""
    tier = customer_service.update_tier(db=db, tier_id=id, request=request)
    return CustomerTierResponse.model_validate(tier)


@tier_router.delete(
    "/{id}",
    response_model=CustomerTierResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Customer Tier",
)
def delete_customer_tier(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> CustomerTierResponse:
    """Deactivate a customer tier following logical-deactivation convention."""
    tier = customer_service.deactivate_tier(db=db, tier_id=id)
    return CustomerTierResponse.model_validate(tier)


router.include_router(customer_router)
router.include_router(tier_router)
