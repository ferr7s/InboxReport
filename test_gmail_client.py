import unittest

from gmail_client import extract_email


class GmailClientTests(unittest.TestCase):
    def test_extract_email_reads_sender_subject_and_snippet(self):
        message = {
            "snippet": "Please approve the report.",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Manager <manager@example.com>"},
                    {"name": "Subject", "value": "Report approval"},
                ]
            },
        }

        email = extract_email(message)

        self.assertEqual(email["sender"], "Manager <manager@example.com>")
        self.assertEqual(email["subject"], "Report approval")
        self.assertEqual(email["snippet"], "Please approve the report.")

    def test_extract_email_uses_defaults_for_missing_headers(self):
        email = extract_email({"snippet": ""})

        self.assertEqual(email["sender"], "(unknown sender)")
        self.assertEqual(email["subject"], "(no subject)")
        self.assertEqual(email["snippet"], "")


if __name__ == "__main__":
    unittest.main()
