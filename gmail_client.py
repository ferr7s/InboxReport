import html
import os


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_QUERY = "newer_than:1d -category:promotions"


def get_gmail_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"Missing Google OAuth client file: {credentials_file}")

        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(
            host=os.getenv("OAUTH_HOST", "localhost"),
            bind_addr=os.getenv("OAUTH_BIND_ADDR", "0.0.0.0"),
            port=int(os.getenv("OAUTH_PORT", "8080")),
            open_browser=False,
        )

    token_dir = os.path.dirname(token_file)
    if token_dir:
        os.makedirs(token_dir, exist_ok=True)
    with open(token_file, "w", encoding="utf-8") as token:
        token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_recent_emails(service, query=DEFAULT_QUERY, max_results=50):
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = response.get("messages", [])
    emails = []

    for message in messages:
        detail = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"],
            )
            .execute()
        )
        emails.append(extract_email(detail))

    return emails


def extract_email(message):
    headers = message.get("payload", {}).get("headers", [])
    return {
        "sender": _clean(_header(headers, "From") or "(unknown sender)"),
        "subject": _clean(_header(headers, "Subject") or "(no subject)"),
        "snippet": _clean(message.get("snippet", "")),
    }


def _header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _clean(value):
    return " ".join(html.unescape(str(value or "")).split())
