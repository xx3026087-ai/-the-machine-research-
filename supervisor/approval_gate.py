"""Human approval gate for system changes."""

import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of system changes."""
    PROMPT_UPDATE = "prompt_update"
    CONFIG_CHANGE = "config_change"
    MODEL_RETRAIN = "model_retrain"
    CODE_MODIFICATION = "code_modification"
    DEPLOYMENT = "deployment"
    ALERT_RULE = "alert_rule"


class ApprovalStatus(Enum):
    """Status of approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class ChangeRequest:
    """Request for system change."""
    id: str
    change_type: ChangeType
    title: str
    description: str
    proposed_change: Dict
    requester: str
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approval_comments: List[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ApprovalGate:
    """Manages approval workflow for system changes."""

    def __init__(self, config: Dict):
        self.config = config
        self.pending_requests: Dict[str, ChangeRequest] = {}
        self.approved_requests: List[ChangeRequest] = []
        self.rejected_requests: List[ChangeRequest] = []
        self.approval_required_for = config.get("approval_required_for", [
            ChangeType.CODE_MODIFICATION,
            ChangeType.DEPLOYMENT,
            ChangeType.MODEL_RETRAIN
        ])
        self.auto_approve_for = config.get("auto_approve_for", [
            ChangeType.PROMPT_UPDATE,
            ChangeType.CONFIG_CHANGE
        ])

    def submit_change_request(self, request: ChangeRequest) -> str:
        """Submit a change request for approval."""
        logger.info(f"Change request submitted: {request.id} ({request.change_type.value})")
        
        # Check if this type auto-approves
        if request.change_type in self.auto_approve_for:
            self._auto_approve(request)
            return request.id
        
        # Otherwise, add to pending
        if request.change_type in self.approval_required_for:
            self.pending_requests[request.id] = request
            self._notify_approvers(request)
            return request.id
        
        logger.warning(f"Change type {request.change_type} not recognized")
        return None

    def _auto_approve(self, request: ChangeRequest) -> None:
        """Auto-approve low-risk changes."""
        request.status = ApprovalStatus.APPROVED
        request.approved_by = "system_auto"
        request.approved_at = datetime.now()
        self.approved_requests.append(request)
        logger.info(f"Auto-approved change request: {request.id}")

    def _notify_approvers(self, request: ChangeRequest) -> None:
        """Notify human approvers of pending request."""
        # Placeholder: send email/Slack/etc
        logger.info(f"Approval notification sent for {request.id}")

    def approve_request(self, request_id: str, approver: str, comments: str = "") -> bool:
        """Approve a pending change request."""
        if request_id not in self.pending_requests:
            logger.warning(f"Request {request_id} not found in pending")
            return False
        
        request = self.pending_requests.pop(request_id)
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver
        request.approved_at = datetime.now()
        if comments:
            request.approval_comments = [comments]
        
        self.approved_requests.append(request)
        logger.info(f"Request {request_id} approved by {approver}")
        return True

    def reject_request(self, request_id: str, approver: str, reason: str) -> bool:
        """Reject a pending change request."""
        if request_id not in self.pending_requests:
            logger.warning(f"Request {request_id} not found in pending")
            return False
        
        request = self.pending_requests.pop(request_id)
        request.status = ApprovalStatus.REJECTED
        request.approval_comments = [reason]
        
        self.rejected_requests.append(request)
        logger.info(f"Request {request_id} rejected by {approver}: {reason}")
        return True

    def get_pending_requests(self) -> List[ChangeRequest]:
        """Get all pending approval requests."""
        return list(self.pending_requests.values())

    def get_request_status(self, request_id: str) -> Optional[Dict]:
        """Get detailed status of a change request."""
        # Check all lists
        if request_id in self.pending_requests:
            req = self.pending_requests[request_id]
            return {
                "id": req.id,
                "status": "pending",
                "change_type": req.change_type.value,
                "title": req.title,
                "created_at": req.created_at.isoformat()
            }
        
        for req in self.approved_requests:
            if req.id == request_id:
                return {
                    "id": req.id,
                    "status": "approved",
                    "change_type": req.change_type.value,
                    "approved_by": req.approved_by,
                    "approved_at": req.approved_at.isoformat()
                }
        
        for req in self.rejected_requests:
            if req.id == request_id:
                return {
                    "id": req.id,
                    "status": "rejected",
                    "change_type": req.change_type.value,
                    "reason": req.approval_comments[0] if req.approval_comments else "unknown"
                }
        
        return None

    def get_approval_statistics(self) -> Dict:
        """Get approval workflow statistics."""
        return {
            "pending_count": len(self.pending_requests),
            "approved_count": len(self.approved_requests),
            "rejected_count": len(self.rejected_requests),
            "total_count": len(self.pending_requests) + len(self.approved_requests) + len(self.rejected_requests),
            "approval_rate": len(self.approved_requests) / (len(self.approved_requests) + len(self.rejected_requests) + 1)
        }
