"""Base repository with common CRUD operations."""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from aws_lambda_powertools import Logger
from .table import DynamoDBTable

logger = Logger()

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository for DynamoDB operations."""
    
    def __init__(self, table: Optional[DynamoDBTable] = None):
        """Initialize repository.
        
        Args:
            table: DynamoDBTable instance (creates new if not provided)
        """
        self.table = table or DynamoDBTable()
    
    def get(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Get item by primary key."""
        return self.table.get_item(pk, sk)
    
    def create(self, item: Dict[str, Any]) -> None:
        """Create new item."""
        item['updated_at'] = datetime.utcnow().isoformat()
        self.table.put_item(item)
        logger.info(f"Created item: {item.get('PK')}")
    
    def update(self, pk: str, sk: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update item."""
        updates['updated_at'] = datetime.utcnow().isoformat()
        result = self.table.update_item(pk, sk, updates)
        logger.info(f"Updated item: {pk}#{sk}")
        return result
    
    def delete(self, pk: str, sk: str) -> None:
        """Delete item."""
        self.table.delete_item(pk, sk)
        logger.info(f"Deleted item: {pk}#{sk}")
    
    def list_by_pk(self, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List items by partition key."""
        return self.table.query(pk, sk_prefix)
    
    def list_by_gsi(self, gsi_name: str, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List items by GSI."""
        return self.table.query_gsi(gsi_name, pk, sk_prefix)
