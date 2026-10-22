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


if __name__ == "__main__":
    unittest.main()
