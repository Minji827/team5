import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app


class DeploymentTests(unittest.TestCase):
    def test_built_frontend_and_api_share_origin(self):
        client = TestClient(app)
        self.assertEqual(client.get("/api/health").json(), {"ok": True})
        page = client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("/assets/", page.text)
        for path in ["/.env", "/data/processed/fin/places.csv", "/backend/app/main.py", "/api/does-not-exist"]:
            self.assertEqual(client.get(path).status_code, 404)

    def test_disabled_mail_never_connects_to_smtp(self):
        with patch.dict(os.environ, {"EMAIL_DELIVERY_ENABLED": "false"}), patch("app.routers.notify.smtplib.SMTP_SSL") as smtp:
            response = TestClient(app).post("/api/notify/email", json={"email": "test@example.com", "email_consent": True, "stops": []})
            self.assertEqual(response.status_code, 503)
            smtp.assert_not_called()

    def test_brevo_sends_selected_language_without_smtp(self):
        from app.routers.notify import EMAIL_COPY
        with patch.dict(os.environ, {"EMAIL_DELIVERY_ENABLED": "true", "BREVO_API_KEY": "test-only-key", "EMAIL_FROM": "sender@example.com"}), patch("app.routers.notify.requests.post") as post, patch("app.routers.notify.smtplib.SMTP_SSL") as smtp:
            post.return_value.json.return_value = {"messageId": "test-id"}
            for language in ["ko", "en", "ja", "zh-TW"]:
                response = TestClient(app).post("/api/notify/email", json={"email": "test@example.com", "email_consent": True, "language": language, "total_minutes": 40, "stops": [{"order": 1, "name": "용두산공원", "category": "관광명소", "address": "부산 중구"}]})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["sent"])
                payload = post.call_args.kwargs["json"]
                self.assertEqual(payload["subject"], EMAIL_COPY[language]["subject"])
                self.assertIn(EMAIL_COPY[language]["categories"]["관광명소"], payload["textContent"])
                self.assertEqual(payload["sender"]["email"], "sender@example.com")
                self.assertEqual(payload["to"], [{"email": "test@example.com"}])
            smtp.assert_not_called()

    def test_brevo_failure_is_not_reported_as_sent(self):
        import requests
        with patch.dict(os.environ, {"EMAIL_DELIVERY_ENABLED": "true", "BREVO_API_KEY": "test-only-key", "EMAIL_FROM": "sender@example.com"}), patch("app.routers.notify.requests.post") as post:
            client = TestClient(app)
            request = {"email": "test@example.com", "email_consent": True, "stops": []}
            post.side_effect = requests.Timeout()
            self.assertEqual(client.post("/api/notify/email", json=request).status_code, 502)
            post.side_effect = None
            post.return_value.json.return_value = {}
            self.assertEqual(client.post("/api/notify/email", json=request).status_code, 502)
            post.reset_mock()
            self.assertEqual(client.post("/api/notify/email", json={**request, "email_consent": False}).status_code, 400)
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
