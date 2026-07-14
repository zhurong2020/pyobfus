CREDENTIALS = {
    "api_token": "sk_live_7f3d9a2b8c1e4f60",
    "hmac_secret": "whsec_2a4c6e8f0b1d3f5a9",
}


def auth_header():
    """Return the Authorization header value for the billing API."""
    return "Bearer " + CREDENTIALS.get("api_token")


def signing_key_suffix():
    """Return the last four characters of the webhook signing secret."""
    return CREDENTIALS.get("hmac_secret")[-4:]
