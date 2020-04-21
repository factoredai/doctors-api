from functools import wraps
import json
from jose import jwt
from six.moves.urllib.request import urlopen


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


class AuthHandler:
    def __init__(self, auth0_domain, algorithms, api_identifier):
        self.auth0_domain = auth0_domain
        self.algorithms = algorithms
        self.api_identifier = api_identifier

    def _get_token_auth_header(self, request):
        """Obtains the access token from the Authorization Header
        """
        auth = request.headers.get("Authorization", None)
        if not auth:
            return AuthError({"code": "authorization_header_missing",
                              "message":
                                "Authorization header is expected"}, 401)

        parts = auth.split()

        if parts[0].lower() != "bearer":
            return AuthError({"code": "invalid_header",
                              "message":
                                "Authorization header must start with"
                                " Bearer"}, 401)
        elif len(parts) == 1:
            return AuthError({"code": "invalid_header",
                              "message": "Token not found"}, 401)
        elif len(parts) > 2:
            return AuthError({"code": "invalid_header",
                              "message":
                                "Authorization header must be"
                                " Bearer token"}, 401)

        token = parts[1]
        return token

    def get_payload(self, request):

        token = self._get_token_auth_header(request)

        if isinstance(token, AuthError):
            return token

        jsonurl = urlopen("https://"+self.auth0_domain+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError:
            return AuthError({
                "code": "invalid_header",
                "message": "Invalid header. Use an RS256 signed JWT Access Token"}, 401)
        if unverified_header["alg"] == "HS256":
            return AuthError({
                "code": "invalid_header",
                "message": "Invalid header. Use an RS256 signed JWT Access Token"}, 401)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=self.algorithms,
                    audience=self.api_identifier,
                    issuer="https://"+self.auth0_domain+"/"
                )
            except jwt.ExpiredSignatureError:
                return AuthError({
                    "code": "token_expired",
                    "message": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                return AuthError({
                    "code": "invalid_claims",
                    "message": "incorrect claims, please check the audience and issuer"}, 401)
            except Exception:
                return AuthError({
                    "code": "invalid_header",
                    "message": "Unable to parse authentication  token."}, 401)

            return payload
        return AuthError({
            "code": "invalid_header",
            "message": "Unable to find appropriate key"}, 401)


def requires_scope(required_scope, request):
    """Determines if the required scope is present in the access token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header(request)
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False
