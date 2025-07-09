import requests
import urllib.parse

from bsapi import APIError

BS_OAUTH_AUTH_URL = "https://auth.brightspace.com/oauth2/auth"
BS_OAUTH_TOKEN_URL = "https://auth.brightspace.com/core/connect/token"
BS_OAUTH_SCOPE = "core:*:*"


def create_auth_url(
    client_id: str, redirect_uri: str, scope: str = BS_OAUTH_SCOPE
) -> str:
    """Create OAuth 2.0 authorization URL."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
    }
    query = urllib.parse.urlencode(params)
    return f"{BS_OAUTH_AUTH_URL}?{query}"


def exchange_code_for_token(
    client_id: str, client_secret: str, redirect_uri: str, authorization_code: str
) -> dict:
    """Exchange authorization code for access token using explicit form encoding."""

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Python-BS-API-Client/1.0",
    }

    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(BS_OAUTH_TOKEN_URL, data=data, headers=headers)
    if response.status_code != 200:
        raise APIError(
            f"Token exchange failed: {response.status_code}: {response.text}"
        )

    return response.json()


def parse_callback_url(callback_url: str) -> str:
    """Parse OAuth callback URL to extract authorization code."""
    components = urllib.parse.urlsplit(callback_url)
    query_dict = urllib.parse.parse_qs(components.query)

    if "code" not in query_dict:
        raise ValueError("Missing authorization code in callback URL")
    if len(query_dict["code"]) != 1:
        raise ValueError("Invalid authorization code in callback URL")

    return query_dict["code"][0]
