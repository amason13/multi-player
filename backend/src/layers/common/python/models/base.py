"""Base entity model with DynamoDB key helpers."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Base entity with common DynamoDB attributes."""
    
    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")
    gsi1_pk: Optional[str] = Field(None, description="GSI1 partition key")
    gsi1_sk: Optional[str] = Field(None, description="GSI1 sort key")
    entity_type: str = Field(..., description="Entity type (e.g., USER, LEAGUE)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ttl: Optional[int] = Field(None, description="TTL epoch seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format."""
        item = self.dict(exclude_none=True)
        # Convert datetime to ISO format strings
        if isinstance(item.get('created_at'), datetime):
            item['created_at'] = item['created_at'].isoformat()
        if isinstance(item.get('updated_at'), datetime):
            item['updated_at'] = item['updated_at'].isoformat()
        return item
