from flask import request, jsonify, g, abort
from flask_httpauth import HTTPBasicAuth
import json
import requests
import logging
import re

from simple_api import app
from simple_api.firebase_authentication import firebase_auth
from simple_api.token_system import generate_auth_token, verify_auth_token

# Configure logging
logger = logging.getLogger(__name__)

http_basic_auth = HTTPBasicAuth()

# Validation constants
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
MIN_PASSWORD_LENGTH = 8


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_password(password: str) -> tuple:
    """
    Validate password strength.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not has_letter or not has_number:
        return False, "Password must contain at least one letter and one number"
    
    return True, None


@app.route("/")
@app.route("/index")
def index():
    return jsonify(
        {
            "endpoints": [
                {
                    "endpoint": "/api/register",
                    "about": "register email and password through POST",
                },
                {
                    "endpoint": "/api/token",
                    "about": "send email and password to get authentication token to access the other parts of api",
                },
            ]
        }
    )


@app.route("/api/token")
@http_basic_auth.login_required
def get_auth_token():
    # g.user was set by the verify_password method to store
    # the user object for further usage
    token = generate_auth_token(g.user["idToken"])
    return jsonify({"token": token.decode("ascii")})


@app.route("/api/resource")
@http_basic_auth.login_required
def get_secret_resource():
    return "This is the secret Resource"


def _parse_firebase_error(e):
    error_json = e.args[1]
    error = json.loads(error_json)
    error_code = error["error"]["code"]
    return error, error_code


@app.route("/api/register", methods=["POST"])
def register_user():
    """Register a new user with email and password."""
    # Check if request has JSON data
    if not request.is_json:
        logger.warning("Registration attempt without JSON content type")
        return jsonify({
            "error": "Bad Request",
            "message": "Content-Type must be application/json"
        }), 400
    
    email = request.json.get("email")
    password = request.json.get("password")
    
    # Validate email
    if not email:
        logger.warning("Registration attempt without email")
        return jsonify({
            "error": "Validation Error",
            "message": "Email is required"
        }), 400
    
    email = email.strip()
    if not validate_email(email):
        logger.warning(f"Registration attempt with invalid email format: {email[:20]}...")
        return jsonify({
            "error": "Validation Error",
            "message": "Invalid email format"
        }), 400
    
    # Validate password
    is_valid, password_error = validate_password(password)
    if not is_valid:
        logger.warning(f"Registration attempt with invalid password for: {email}")
        return jsonify({
            "error": "Validation Error",
            "message": password_error
        }), 400

    try:
        user = firebase_auth.create_user_with_email_and_password(email, password)
        firebase_auth.send_email_verification(user["idToken"])
        logger.info(f"User registered successfully: {email}")
    except requests.exceptions.HTTPError as e:
        error, error_code = _parse_firebase_error(e)
        logger.error(f"Firebase error during registration for {email}: {error}")
        return jsonify(error), error_code
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred during registration"
        }), 500
        
    return jsonify({"email": email, "message": "Email verification link sent"}), 200


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    """Send password reset email to user."""
    # Check if request has JSON data
    if not request.is_json:
        logger.warning("Password reset attempt without JSON content type")
        return jsonify({
            "error": "Bad Request",
            "message": "Content-Type must be application/json"
        }), 400
    
    email = request.json.get("email")
    
    # Validate email
    if not email:
        logger.warning("Password reset attempt without email")
        return jsonify({
            "error": "Validation Error",
            "message": "Email is required"
        }), 400
    
    email = email.strip()
    if not validate_email(email):
        logger.warning(f"Password reset attempt with invalid email format: {email[:20]}...")
        return jsonify({
            "error": "Validation Error",
            "message": "Invalid email format"
        }), 400

    try:
        firebase_auth.send_password_reset_email(email)
        logger.info(f"Password reset email sent to: {email}")
    except requests.exceptions.HTTPError as e:
        error, error_code = _parse_firebase_error(e)
        logger.error(f"Firebase error during password reset for {email}: {error}")
        return jsonify(error), error_code
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }), 500
        
    return jsonify({"email": email, "message": "Password reset link sent"}), 200


@http_basic_auth.verify_password
def verify_password(email_or_token, password):
    """Verify user credentials or authentication token.
    
    Args:
        email_or_token: Either an email address or an auth token
        password: Password (empty if using token auth)
        
    Returns:
        bool: True if authentication successful, False otherwise
    """
    # First try token authentication
    if email_or_token and verify_auth_token(email_or_token):
        logger.debug("User authenticated via token")
        return True

    # Then try email/password authentication
    if not email_or_token or not password:
        logger.debug("Missing email or password for authentication")
        return False
    
    try:
        # user is just a dictionary returned by firebase
        user = firebase_auth.sign_in_with_email_and_password(email_or_token, password)
        # set g.user to store the user object
        # g acts like a global variable which other
        # functions like get_auth_token() can use
        g.user = user
        logger.debug(f"User authenticated via email: {email_or_token}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Authentication failed for {email_or_token}: HTTP error")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error during authentication: {e}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout during authentication: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {type(e).__name__}: {e}")
        return False
