"""Invitation repository for DynamoDB operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable
from ..utils.exceptions import NotFoundError, ValidationError

logger = Logger()


class InvitationRepository:
    """Repository for invitation-related DynamoDB operations.
    
    Handles all invitation operations including creation, retrieval, and response.
    Uses single-table design with item collections and sparse GSI for pending invitations.
    
    Access Patterns:
    - Pattern #21: Send league invitation
    - Pattern #22: Get pending invitations
    - Pattern #23: Accept/reject invitation
    """
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize invitation repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    # Invitation CRUD Operations
    
    def create_invitation(self, invitation_id: str, league_id: str, inviter_id: str,
                         invitee_email: str, invitee_id: Optional[str] = None,
                         **kwargs) -> Dict[str, Any]:
        """Create a new league invitation.
        
        Args:
            invitation_id: Unique invitation identifier (UUID)
            league_id: League ID
            inviter_id: User ID of inviter
            invitee_email: Email of invitee
            invitee_id: Optional user ID of invitee (if already registered)
            **kwargs: Additional attributes (message, etc.)
            
        Returns:
            Created invitation item
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        if not all([invitation_id, league_id, inviter_id, invitee_email]):
            raise ValidationError("All required fields must be provided")
        
        now = datetime.utcnow().isoformat()
        
        item = {
            'PK': f'INVITATION#{invitation_id}',
            'SK': 'METADATA',
            'entity_type': 'INVITATION',
            'invitation_id': invitation_id,
            'league_id': league_id,
            'inviter_id': inviter_id,
            'invitee_email': invitee_email,
            'invitee_id': invitee_id,
            'status': 'PENDING',
            'created_at': now,
            'updated_at': now,
            **kwargs
        }
        
        self.table.put_item(item)
        
        # Add to invitee's pending invitations (if user ID known)
        if invitee_id:
            self._add_to_user_invitations(invitee_id, invitation_id, league_id, inviter_id, now)
        
        logger.info(f"Created invitation {invitation_id} for {invitee_email}")
        return item
    
    def get_invitation(self, invitation_id: str) -> Optional[Dict[str, Any]]:
        """Get invitation details by ID.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            Invitation item or None if not found
        """
        return self.table.get_item(f'INVITATION#{invitation_id}', 'METADATA')
    
    def update_invitation(self, invitation_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update invitation.
        
        Args:
            invitation_id: Invitation ID
            updates: Dictionary of attributes to update
            
        Returns:
            Updated invitation item
        """
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(
            f'INVITATION#{invitation_id}',
            'METADATA',
            updates
        )
        logger.info(f"Updated invitation {invitation_id}")
        return result
    
    def delete_invitation(self, invitation_id: str) -> None:
        """Delete an invitation.
        
        Args:
            invitation_id: Invitation ID
        """
        self.table.delete_item(f'INVITATION#{invitation_id}', 'METADATA')
        logger.info(f"Deleted invitation {invitation_id}")
    
    # Invitation Response Operations
    
    def accept_invitation(self, invitation_id: str, invitee_id: str) -> Dict[str, Any]:
        """Accept a league invitation.
        
        Args:
            invitation_id: Invitation ID
            invitee_id: User ID accepting invitation
            
        Returns:
            Updated invitation item
        """
        result = self.update_invitation(
            invitation_id,
            {
                'status': 'ACCEPTED',
                'invitee_id': invitee_id,
                'responded_at': datetime.utcnow().isoformat()
            }
        )
        
        # Remove from pending invitations
        self.table.delete_item(f'USER#{invitee_id}', f'INVITATION#{invitation_id}')
        
        logger.info(f"Accepted invitation {invitation_id}")
        return result
    
    def reject_invitation(self, invitation_id: str, invitee_id: str) -> Dict[str, Any]:
        """Reject a league invitation.
        
        Args:
            invitation_id: Invitation ID
            invitee_id: User ID rejecting invitation
            
        Returns:
            Updated invitation item
        """
        result = self.update_invitation(
            invitation_id,
            {
                'status': 'REJECTED',
                'invitee_id': invitee_id,
                'responded_at': datetime.utcnow().isoformat()
            }
        )
        
        # Remove from pending invitations
        self.table.delete_item(f'USER#{invitee_id}', f'INVITATION#{invitation_id}')
        
        logger.info(f"Rejected invitation {invitation_id}")
        return result
    
    # Invitation Retrieval Operations
    
    def get_pending_invitations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all pending invitations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of invitations to return
            
        Returns:
            List of pending invitation items
        """
        items = self.table.query(f'USER#{user_id}', 'INVITATION#')
        return items[:limit] if limit else items
    
    def get_sent_invitations(self, inviter_id: str, league_id: str) -> List[Dict[str, Any]]:
        """Get all invitations sent by a user for a league.
        
        Args:
            inviter_id: User ID of inviter
            league_id: League ID
            
        Returns:
            List of invitation items
        """
        # This would require a GSI lookup
        # For now, return empty list - implement with GSI query
        logger.warning("get_sent_invitations requires GSI - not implemented")
        return []
    
    def get_league_invitations(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all invitations for a league.
        
        Args:
            league_id: League ID
            
        Returns:
            List of invitation items
        """
        # This would require a GSI lookup
        # For now, return empty list - implement with GSI query
        logger.warning("get_league_invitations requires GSI - not implemented")
        return []
    
    def get_pending_invitation_count(self, user_id: str) -> int:
        """Get count of pending invitations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of pending invitations
        """
        invitations = self.get_pending_invitations(user_id)
        return len(invitations)
    
    # Invitation Status Operations
    
    def get_invitation_status(self, invitation_id: str) -> Optional[str]:
        """Get the status of an invitation.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            Invitation status or None if not found
        """
        invitation = self.get_invitation(invitation_id)
        if invitation:
            return invitation.get('status')
        return None
    
    def is_pending(self, invitation_id: str) -> bool:
        """Check if an invitation is pending.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            True if pending, False otherwise
        """
        status = self.get_invitation_status(invitation_id)
        return status == 'PENDING'
    
    def is_accepted(self, invitation_id: str) -> bool:
        """Check if an invitation is accepted.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            True if accepted, False otherwise
        """
        status = self.get_invitation_status(invitation_id)
        return status == 'ACCEPTED'
    
    def is_rejected(self, invitation_id: str) -> bool:
        """Check if an invitation is rejected.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            True if rejected, False otherwise
        """
        status = self.get_invitation_status(invitation_id)
        return status == 'REJECTED'
    
    # Helper Methods
    
    def _add_to_user_invitations(self, user_id: str, invitation_id: str,
                                league_id: str, inviter_id: str, now: str) -> None:
        """Internal helper to add invitation to user's pending invitations.
        
        Args:
            user_id: User ID
            invitation_id: Invitation ID
            league_id: League ID
            inviter_id: Inviter user ID
            now: Current timestamp
        """
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'INVITATION#{invitation_id}',
            'entity_type': 'USER_INVITATION',
            'invitation_id': invitation_id,
            'league_id': league_id,
            'inviter_id': inviter_id,
            'status': 'PENDING',
            'created_at': now,
            'updated_at': now
        }
        self.table.put_item(item)
    
    def send_bulk_invitations(self, league_id: str, inviter_id: str,
                             invitee_emails: List[str]) -> List[Dict[str, Any]]:
        """Send invitations to multiple users.
        
        Args:
            league_id: League ID
            inviter_id: User ID of inviter
            invitee_emails: List of invitee emails
            
        Returns:
            List of created invitation items
        """
        import uuid
        
        invitations = []
        for email in invitee_emails:
            invitation_id = str(uuid.uuid4())
            invitation = self.create_invitation(
                invitation_id=invitation_id,
                league_id=league_id,
                inviter_id=inviter_id,
                invitee_email=email
            )
            invitations.append(invitation)
        
        logger.info(f"Sent {len(invitations)} invitations for league {league_id}")
        return invitations
    
    def resend_invitation(self, invitation_id: str) -> Dict[str, Any]:
        """Resend a pending invitation.
        
        Args:
            invitation_id: Invitation ID
            
        Returns:
            Updated invitation item
        """
        invitation = self.get_invitation(invitation_id)
        if not invitation:
            raise NotFoundError(f"Invitation {invitation_id} not found")
        
        if invitation.get('status') != 'PENDING':
            raise ValidationError(f"Can only resend pending invitations")
        
        return self.update_invitation(
            invitation_id,
            {'resent_at': datetime.utcnow().isoformat()}
        )
