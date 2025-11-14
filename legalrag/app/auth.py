from fastapi import Header, HTTPException
from clerk_backend_api import Clerk
import os
import logging
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# Initialize Clerk
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY")
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)

# Extract the Clerk publishable key domain from secret key or use default
# The JWKS URL is at https://clerk.DOMAIN/.well-known/jwks.json
CLERK_JWKS_URL = "https://charmed-deer-66.clerk.accounts.dev/.well-known/jwks.json"

async def get_current_user(authorization: str = Header(None)) -> str:
    """
    Validates the Clerk JWT token and returns the user_id.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]

    try:
        # Get the signing key from Clerk's JWKS
        jwks_client = PyJWKClient(CLERK_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify and decode the JWT
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Clerk doesn't use standard aud claim
        )

        # Extract user_id from the token (Clerk uses 'sub' claim)
        user_id = decoded_token.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        logger.info(f"Authenticated user: {user_id}")
        return user_id

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
