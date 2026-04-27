import os


DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_SNIPPET_LIMIT = 500
DEFAULT_TOTAL_LIMIT = 12000

DIGEST_PROMPT = """Write a concise daily email digest.
Use these exact sections:
Critical
Important
Action Items
Other

Rules:
- Summarize all emails together in one digest.
- Use short bullets.
- Ignore low-signal content unless it affects the user.
- Mention sender names when useful.
- Put explicit tasks and deadlines under Action Items."""


def limit_text(text, limit):
    cleaned = " ".join(str(text or "").split())
    if limit <= 0:
        return ""
    if len(cleaned) <= limit:
        return cleaned
    if limit <= 3:
        return "." * limit
    return cleaned[: limit - 3].rstrip() + "..."


def build_email_text(
    emails,
    snippet_limit=DEFAULT_SNIPPET_LIMIT,
    total_limit=DEFAULT_TOTAL_LIMIT,
):
    blocks = []
    for index, email in enumerate(emails, start=1):
        sender = limit_text(email.get("sender", "(unknown sender)"), 200)
        subject = limit_text(email.get("subject", "(no subject)"), 200)
        snippet = limit_text(email.get("snippet", ""), snippet_limit)
        blocks.append(
            f"{index}. From: {sender}\n"
            f"Subject: {subject}\n"
            f"Snippet: {snippet}"
        )

    text = "\n\n".join(blocks)
    if len(text) <= total_limit:
        return text
    if total_limit <= 3:
        return "." * total_limit
    return text[: total_limit - 3].rstrip() + "..."


def summarize_emails(emails, client=None, model=None):
    if not emails:
        return empty_digest()

    if client is None:
        from openai import OpenAI

        client = OpenAI()

    model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    email_text = build_email_text(emails)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "developer", "content": DIGEST_PROMPT},
            {"role": "user", "content": f"Emails from the last 24h:\n\n{email_text}"},
        ],
    )
    return response.choices[0].message.content.strip()


def empty_digest():
    return """Critical
- None

Important
- None

Action Items
- None

Other
- No matching emails in the last 24 hours."""
