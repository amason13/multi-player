"""DynamoDB table wrapper with single-table design support."""
import os
from typing import Any, Dict, List, Optional
import boto3
from aws_lambda_powertools import Logger

logger = Logger()


class DynamoDBTable:
    """Wrapper for DynamoDB single-table operations."""
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize DynamoDB table client.
        
        Args:
            table_name: DynamoDB table name (defaults to TABLE_NAME env var)
        """
        self.table_name = table_name or os.environ.get('TABLE_NAME')
        if not self.table_name:
            raise ValueError("TABLE_NAME environment variable not set")
        
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
    
    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Get item by partition and sort key."""
        try:
            response = self.table.get_item(Key={'PK': pk, 'SK': sk})
            return response.get('Item')
        except Exception as e:
            logger.exception(f"Error getting item: {e}")
            raise
    
    def put_item(self, item: Dict[str, Any]) -> None:
        """Put item into table."""
        try:
            self.table.put_item(Item=item)
        except Exception as e:
            logger.exception(f"Error putting item: {e}")
            raise
    
    def update_item(self, pk: str, sk: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update item attributes."""
        try:
            update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
            expression_values = {f":{k}": v for k, v in updates.items()}
            
            response = self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return response.get('Attributes', {})
        except Exception as e:
            logger.exception(f"Error updating item: {e}")
            raise
    
    def delete_item(self, pk: str, sk: str) -> None:
        """Delete item from table."""
        try:
            self.table.delete_item(Key={'PK': pk, 'SK': sk})
        except Exception as e:
            logger.exception(f"Error deleting item: {e}")
            raise
    
    def query(self, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query items by partition key."""
        try:
            key_condition = "PK = :pk"
            expression_values = {":pk": pk}
            
            if sk_prefix:
                key_condition += " AND begins_with(SK, :sk)"
                expression_values[":sk"] = sk_prefix
            
            response = self.table.query(
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except Exception as e:
            logger.exception(f"Error querying items: {e}")
            raise
    
    def query_gsi(self, gsi_name: str, pk: str, sk_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query items using GSI."""
        try:
            key_condition = f"{gsi_name}PK = :pk"
            expression_values = {":pk": pk}
            
            if sk_prefix:
                key_condition += f" AND begins_with({gsi_name}SK, :sk)"
                expression_values[":sk"] = sk_prefix
            
            response = self.table.query(
                IndexName=gsi_name,
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except Exception as e:
            logger.exception(f"Error querying GSI: {e}")
            raise
