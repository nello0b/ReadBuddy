# app/services/auth/auth0.py

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from config import AUTH0_DOMAIN, AUTH0_AUDIENCE, DEBUG_MODE
import requests

ALGORITHMS = ["RS256"]
_jwks = None  # Cache JWKS keys

def get_jwks():
    global _jwks
    if _jwks is None:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_url)
        if response.status_code != 200:
            raise ValueError("Unable to fetch JWKS")
        _jwks = response.json()["keys"]
    return _jwks

def verify_auth0_token(token: str):
    if DEBUG_MODE:
        print("[DEBUG] Starting token verification")
    jwks = get_jwks()
    if DEBUG_MODE:
        print(f"[DEBUG] JWKS fetched: {len(jwks)} keys")
    unverified_header = jwt.get_unverified_header(token)
    if DEBUG_MODE:
        print(f"[DEBUG] Unverified JWT header: {unverified_header}")

    rsa_key = {}
    for key in jwks:
        if key["kid"] == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            if DEBUG_MODE:
                print(f"[DEBUG] Matching RSA key found: {rsa_key['kid']}")
            break

    if not rsa_key:
        if DEBUG_MODE:
            print("[ERROR] Unable to find RSA key matching token header")
        raise ValueError("Unable to find RSA key matching token header")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        if DEBUG_MODE:
            print("[DEBUG] JWT successfully decoded")
    except ExpiredSignatureError:
        if DEBUG_MODE:
            print("[ERROR] Token has expired")
        raise ValueError("Token has expired")
    except JWTClaimsError:
        if DEBUG_MODE:
            print("[ERROR] Incorrect claims. Check audience and issuer.")
        raise ValueError("Incorrect claims. Check audience and issuer.")
    except JWTError as e:
        if DEBUG_MODE:
            print(f"[ERROR] Unable to parse authentication token: {e}")
        raise ValueError("Unable to parse authentication token.")

    # 🔄 Fetch full user profile from /userinfo
    userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    if DEBUG_MODE:
        print(f"[DEBUG] Fetching userinfo from {userinfo_url}")
    userinfo_response = requests.get(userinfo_url, headers=headers)
    if DEBUG_MODE:
        print(f"[DEBUG] Userinfo response status: {userinfo_response.status_code}")
    userinfo = userinfo_response.json()
    if DEBUG_MODE:
        print(f"[DEBUG] Userinfo fetched: {userinfo}")

    # 🔁 Merge important profile fields
    payload.update({
        "email": userinfo.get("email"),
        "name": userinfo.get("name")
    })
    if DEBUG_MODE:
        print(f"[DEBUG] Final payload: {payload}")

    return payload
