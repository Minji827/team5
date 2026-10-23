import unittest
from app.routers.notify import EmailRequest, build_email_body, EMAIL_COPY
from unittest.mock import patch
import os
from fastapi.testclient import TestClient
from app.main import app


class MapsLinksTests(unittest.TestCase):
    def test_complete_course_email_in_all_languages(self):
        with patch.dict(os.environ, {'EMAIL_DELIVERY_ENABLED':'true', 'BREVO_API_KEY':'test-key', 'EMAIL_FROM':'sender@example.com'}), \
                patch('app.routers.notify.requests.post') as post:
            post.return_value.json.return_value={'messageId':'mock-message'}
            client=TestClient(app)
            for language in EMAIL_COPY:
                with self.subTest(language=language):
                    req=self.request(language=language, return_to_start=True, return_minutes=5, max_minutes=180)
                    body=build_email_body(req)
                    self.assertIn(EMAIL_COPY[language]['course_link'],body)
                    self.assertNotIn('https://www.google.com/maps/dir/', body)
                    self.assertIn('stop=0&stop=1',body)
                    response=client.post('/api/notify/email',json=req.model_dump() | {'email_consent':True})
                    self.assertEqual(response.status_code,200)
                    self.assertTrue(response.json()['sent'])
                    self.assertEqual(post.call_args.kwargs['json']['textContent'],body)

    def request(self, count=2, **changes):
        return EmailRequest(email="test@example.com", start_lat=35.1, start_lon=129.03,
            stops=[dict(id=str(i), order=i+1, name=f"가게 {i} & 카페", address=f"부산 중구 도로 {i}",
                        category="식당", lat=35.11, lon=129.04) for i in range(count)], **changes)

    def test_email_preserves_addresses_without_multi_stop_maps_footer(self):
        for language in EMAIL_COPY:
            req = self.request(11, language=language, return_to_start=True)
            body = build_email_body(req)
            for stop in req.stops:
                self.assertIn(stop.address, body)
            self.assertIn(EMAIL_COPY[language]['course_link'], body)
            self.assertNotIn('maps/dir/', body)
            self.assertNotIn('(1/3)', body)

if __name__ == "__main__":
    unittest.main()
