import json
import api_config as config
import auth
import rate_limiter
import services
import utils


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_cors_headers(origin: str) -> dict:
    """
    Returns CORS headers. Allows the request origin if it is in the
    configured whitelist, otherwise falls back to the first allowed origin.
    """
    allowed = [o.strip() for o in config.CORS_ALLOWED_ORIGINS.split(',')]
    allowed_origin = origin if origin in allowed else (allowed[0] if allowed else '*')
    return {
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key,X-Timestamp,X-Nonce,X-Signature',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Content-Type': 'application/json',
    }


def _parse_event(event: dict) -> tuple[str, str, dict, str]:
    """
    Parses a Lambda event (supports both Function URL payload v1.0 and v2.0).

    Returns:
        (method, path, headers, client_ip)
    """
    if event is None:
        return 'GET', '/', {}, '127.0.0.1'

    # Normalise headers (Lambda lowercases them in v2.0, not always in v1.0)
    raw_headers = event.get('headers') or {}
    headers = {k.lower(): v for k, v in raw_headers.items()}

    # HTTP method
    method = (
        event.get('requestContext', {}).get('http', {}).get('method')
        or event.get('httpMethod', 'GET')
    ).upper()

    # Path
    path = (
        event.get('rawPath')
        or event.get('path', '/')
    )

    # Client IP
    client_ip = (
        event.get('requestContext', {}).get('http', {}).get('sourceIp')
        or event.get('requestContext', {}).get('identity', {}).get('sourceIp', '0.0.0.0')
    )

    return method, path, headers, client_ip


def _make_response(status: int, body: dict, origin: str) -> dict:
    cors = _get_cors_headers(origin)
    return {
        'statusCode': status,
        'headers': cors,
        'body': json.dumps(body, cls=utils.DecimalEncoder),
    }


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _handle_token_request(headers: dict, origin: str) -> dict:
    """POST /auth/token — validates HMAC and issues a Bearer token."""
    if not auth.is_auth_enabled():
        # Passthrough mode — return a dummy response (client won't need a token)
        return _make_response(200, {'token': 'passthrough', 'ttl': 999999}, origin)

    api_key = headers.get('x-api-key', '')
    timestamp = headers.get('x-timestamp', '')
    nonce = headers.get('x-nonce', '')
    signature = headers.get('x-signature', '')

    if not auth.verify_signature(api_key, timestamp, nonce, signature):
        print("🔐 Auth rejected: invalid signature or expired timestamp")
        return _make_response(401, {'error': 'Unauthorized'}, origin)

    token, ttl = auth.generate_token()
    print("🔐 Auth success: token issued")
    return _make_response(200, {'token': token, 'ttl': ttl}, origin)


def _handle_data_request(headers: dict, origin: str) -> dict:
    """GET / — validates Bearer token and returns dashboard data."""
    if auth.is_auth_enabled():
        auth_header = headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            return _make_response(401, {'error': 'Unauthorized'}, origin)
        token = auth_header[len('Bearer '):]
        if not auth.verify_token(token):
            return _make_response(401, {'error': 'Unauthorized: invalid or expired token'}, origin)

    try:
        data = services.build_dashboard_data()
        print(f"📊 Dashboard data: total_km={data['total_km']}, activities={data['total_activities']}")
        return _make_response(200, data, origin)
    except Exception as e:
        print(f"🔥 Critical Error: {e}")
        return _make_response(500, {'error': str(e)}, origin)


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def process_activities(event, context):
    """
    Main Lambda handler.
    Routes:
      OPTIONS *         → CORS preflight
      POST /auth/token  → Issue Bearer token (HMAC auth)
      GET  /            → Return dashboard data (requires Bearer if auth enabled)
    """
    method, path, headers, client_ip = _parse_event(event)
    origin = headers.get('origin', '*')

    print(f"🌐 {method} {path} from {client_ip}")

    # CORS preflight
    if method == 'OPTIONS':
        return _make_response(200, {}, origin)

    # Rate limiting
    if rate_limiter.is_rate_limited(client_ip):
        print(f"🚦 Rate limited: {client_ip}")
        return _make_response(429, {'error': 'Too Many Requests'}, origin)

    # Route: POST /auth/token
    if method == 'POST' and path.rstrip('/') in ('/auth/token', '/auth'):
        return _handle_token_request(headers, origin)

    # Route: GET /
    if method == 'GET' and path in ('/', ''):
        return _handle_data_request(headers, origin)

    return _make_response(404, {'error': 'Not Found'}, origin)


# ---------------------------------------------------------------------------
# Local Flask development server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from flask import Flask, Response, request
        from flask_cors import CORS
    except ImportError:
        print("❌ Error: Install Flask with 'pip install flask flask-cors'")
        exit(1)

    app = Flask(__name__)
    CORS(app)

    print("\n🌍 STARTING LOCAL SERVER...")
    print(f"   👉 Goal: {config.GOAL_KM} km | Last activities: {config.LAST_ACT}")
    print(f"   👉 Auth enabled: {auth.is_auth_enabled()}")
    print("   👉 Listening at: http://127.0.0.1:5000\n")

    @app.route("/", methods=['GET', 'OPTIONS'])
    def local_data():
        mock_event = {
            'httpMethod': request.method,
            'path': '/',
            'headers': dict(request.headers),
            'requestContext': {'identity': {'sourceIp': '127.0.0.1'}}
        }
        result = process_activities(mock_event, None)
        return Response(
            response=result['body'],
            status=result['statusCode'],
            mimetype='application/json',
            headers={k: v for k, v in result.get('headers', {}).items()}
        )

    @app.route("/auth/token", methods=['POST', 'OPTIONS'])
    def local_auth():
        mock_event = {
            'httpMethod': request.method,
            'path': '/auth/token',
            'headers': dict(request.headers),
            'requestContext': {'identity': {'sourceIp': '127.0.0.1'}}
        }
        result = process_activities(mock_event, None)
        return Response(
            response=result['body'],
            status=result['statusCode'],
            mimetype='application/json',
            headers={k: v for k, v in result.get('headers', {}).items()}
        )

    app.run(port=5000, debug=True)