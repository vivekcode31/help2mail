"""
Security utilities — OAuth scopes and session helpers.
"""

# Google OAuth2 scopes required by the application
# - openid + userinfo: for login and profile
# - gmail.send: for sending emails on behalf of the user
GOOGLE_SCOPES: list[str] = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.send",
]

SESSION_USER_KEY = "user_email"
