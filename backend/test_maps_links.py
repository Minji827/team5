import unittest
from urllib.parse import parse_qs, urlparse
from app.routers.notify import EmailRequest, build_google_maps_links, build_email_body, EMAIL_COPY
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
                    self.assertIn(EMAIL_COPY[language]['maps_note'],body)
                    self.assertIn('stop=0&stop=1',body)
                    response=client.post('/api/notify/email',json=req.model_dump() | {'email_consent':True})
                    self.assertEqual(response.status_code,200)
                    self.assertTrue(response.json()['sent'])
                    self.assertEqual(post.call_args.kwargs['json']['textContent'],body)

    def request(self, count=2, **changes):
        return EmailRequest(email="test@example.com", start_lat=35.1, start_lon=129.03,
            stops=[dict(id=str(i), order=i+1, name=f"가게 {i} & 카페", address=f"부산 중구 도로 {i}",
                        category="식당", lat=35.11, lon=129.04) for i in range(count)], **changes)

    def test_named_places_at_same_coordinates_remain_distinct(self):
        req = self.request(start_label="남포역 부산 중구 구덕로 지하 12")
        links = build_google_maps_links(req)
        query = parse_qs(urlparse(links[0]).query)
        self.assertEqual(query["origin"], [req.start_label])
        self.assertEqual(query["destination"], ["가게 1 & 카페 부산 중구 도로 1"])
        self.assertEqual(query["waypoints"], ["가게 0 & 카페 부산 중구 도로 0"])
        self.assertEqual(query["api"], ["1"])
        self.assertEqual(query["travelmode"], ["walking"])
        self.assertNotIn("가게", links[0])

    def test_long_roundtrip_preserves_every_stop_with_mobile_limits(self):
        req = self.request(11, return_to_start=True, start_label="남포역")
        links = build_google_maps_links(req)
        points = []
        for index, link in enumerate(links):
            query = parse_qs(urlparse(link).query)
            waypoints = query["waypoints"][0].split("|") if query.get("waypoints") else []
            self.assertLessEqual(len(waypoints), 3)
            segment = query["origin"] + waypoints + query["destination"]
            if points:
                self.assertEqual(points[-1], segment[0])
            points.extend(segment if index == 0 else segment[1:])
        self.assertEqual(points, ["남포역"] + [f"{s.name} {s.address}" for s in req.stops] + ["남포역"])
        self.assertIn("(1/3)", build_email_body(req))

    def test_single_destination_and_coordinate_fallback(self):
        req = self.request(1, start_label="내 위치")
        query = parse_qs(urlparse(build_google_maps_links(req)[0]).query)
        self.assertEqual(query["origin"], ["35.1,129.03"])
        self.assertNotIn("waypoints", query)
        req.start_lat = None
        self.assertEqual(build_google_maps_links(req), [])


if __name__ == "__main__":
    unittest.main()
