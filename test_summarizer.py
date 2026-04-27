import unittest

from summarizer import build_email_text, limit_text, summarize_emails


class SummarizerTests(unittest.TestCase):
    def test_limit_text_collapses_whitespace_and_truncates(self):
        self.assertEqual(limit_text("  hello\n\nworld  ", 8), "hello...")

    def test_build_email_text_keeps_only_relevant_fields(self):
        emails = [
            {
                "sender": "Alice <alice@example.com>",
                "subject": "Budget review",
                "snippet": "Please review the budget by Friday.",
                "body": "This full body should not be included.",
            }
        ]

        text = build_email_text(emails, snippet_limit=80, total_limit=500)

        self.assertIn("From: Alice <alice@example.com>", text)
        self.assertIn("Subject: Budget review", text)
        self.assertIn("Snippet: Please review the budget by Friday.", text)
        self.assertNotIn("full body", text)

    def test_summarize_emails_uses_one_chat_completion_request(self):
        client = FakeOpenAIClient("Critical\n- None")
        emails = [{"sender": "Bob", "subject": "Deploy", "snippet": "Deploy at 5pm"}]

        digest = summarize_emails(emails, client=client, model="test-model")

        self.assertEqual(digest, "Critical\n- None")
        self.assertEqual(client.calls, 1)
        request = client.last_request
        self.assertEqual(request["model"], "test-model")
        self.assertIn("Critical", request["messages"][0]["content"])
        self.assertIn("Deploy at 5pm", request["messages"][1]["content"])


class FakeOpenAIClient:
    def __init__(self, content):
        self.calls = 0
        self.last_request = None
        self.chat = self
        self.completions = self
        self._content = content

    def create(self, **kwargs):
        self.calls += 1
        self.last_request = kwargs
        return FakeResponse(self._content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeMessage:
    def __init__(self, content):
        self.content = content


if __name__ == "__main__":
    unittest.main()
