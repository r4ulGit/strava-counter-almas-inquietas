import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that converts DynamoDB Decimal types to int or float."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def json_response(data: dict, status: int = 200) -> dict:
    """
    Wraps data in a Lambda-compatible response dict.

    Args:
        data: The response body as a dict.
        status: HTTP status code.

    Returns:
        A Lambda response dict with statusCode and JSON body.
    """
    return {
        'statusCode': status,
        'body': json.dumps(data, cls=DecimalEncoder)
    }
