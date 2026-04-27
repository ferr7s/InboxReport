import os

from dotenv import load_dotenv

from gmail_client import DEFAULT_QUERY, fetch_recent_emails, get_gmail_service
from summarizer import summarize_emails


def main():
    load_dotenv()
    require_env("OPENAI_API_KEY")

    service = get_gmail_service()
    emails = fetch_recent_emails(
        service,
        query=os.getenv("GMAIL_QUERY", DEFAULT_QUERY),
        max_results=env_int("MAX_EMAILS", 50),
    )

    digest = summarize_emails(emails)
    print(digest)
    write_digest(digest, os.getenv("OUTPUT_FILE", "daily_digest.md"))


def require_env(name):
    if not os.getenv(name):
        raise RuntimeError(f"Missing required environment variable: {name}")


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value else default


def write_digest(digest, path):
    with open(path, "w", encoding="utf-8") as file:
        file.write(digest.rstrip() + "\n")


if __name__ == "__main__":
    main()
