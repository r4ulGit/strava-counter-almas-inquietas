import boto3
from botocore.exceptions import ClientError
import api_config as config

# Initialize DynamoDB resource (shared across invocations in the same Lambda instance)
dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
activities_table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)
athletes_table = dynamodb.Table(config.ATHLETES_TABLE_NAME)


def get_all_activities() -> list[dict]:
    """
    Full scan of the ACTIVUM_ACT table with automatic pagination.

    Returns:
        List of all activity items from DynamoDB.
    Raises:
        Exception on DynamoDB errors.
    """
    try:
        response = activities_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = activities_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        return items
    except ClientError as e:
        print(f"❌ DynamoDB Error (activities): {e}")
        raise


def get_top_athletes(limit: int = 10) -> list[dict]:
    """
    Scans the ACTIVUM_USR table, sorts by currentKm descending, and returns top N athletes.
    Sorting is done in-memory since DynamoDB Scan does not support ORDER BY.

    Args:
        limit: Maximum number of athletes to return.

    Returns:
        List of athlete items sorted by currentKm descending.
    Raises:
        Exception on DynamoDB errors.
    """
    try:
        response = athletes_table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = athletes_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        items.sort(key=lambda x: float(x.get('currentKm', 0)), reverse=True)
        return items[:limit]
    except ClientError as e:
        print(f"❌ DynamoDB Error (athletes): {e}")
        raise
