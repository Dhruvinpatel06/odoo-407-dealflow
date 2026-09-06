"""Approvals module package.

Provides approval configuration (ApprovalPolicy) and approval execution workflows.
"""

from app.modules.approvals.repository import (
    ApprovalPolicyRepository,
    approval_policy_repository,
)
from app.modules.approvals.router import policy_router, router
from app.modules.approvals.schemas import (
    ApprovalPolicyCreateRequest,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdateRequest,
)
from app.modules.approvals.service import (
    ApprovalPolicyService,
    approval_policy_service,
)

__all__ = [
    "ApprovalPolicyRepository",
    "approval_policy_repository",
    "ApprovalPolicyService",
    "approval_policy_service",
    "ApprovalPolicyCreateRequest",
    "ApprovalPolicyUpdateRequest",
    "ApprovalPolicyResponse",
    "router",
    "policy_router",
]
