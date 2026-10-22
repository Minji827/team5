import unittest
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from app.main import app
from app.services.walking import walking_leg, WalkingError
from app.routers.recommend import timed_catalog


class WalkingTests(unittest.TestCase):
    @patch("app.services.walking.requests.post")
    def test_summary_seconds_and_geometry(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"features": [
            {"properties": {"totalTime": 125, "totalDistance": 150}},
            {"geometry": {"type": "LineString", "coordinates": [[129, 35], [129.1, 35.1]]}}]}
        result = walking_leg(35, 129, 35.1, 129.1)
        self.assertEqual(result["leg_minutes"], 2.1)
        self.assertEqual(result["leg_path"][0], [35, 129])
        self.assertNotIn("appKey", post.call_args.kwargs["params"])

    @patch("app.services.walking.requests.post")
    def test_auth_failure_does_not_leak_response(self, post):
        post.return_value = Mock(status_code=403, text="private upstream data")
        with self.assertRaises(WalkingError) as exc:
            walking_leg(35, 129, 35.1, 129.1)
        self.assertNotIn("private upstream data", str(exc.exception))

    @patch("app.services.route.walking_leg")
    def test_recommend_and_swap_include_stay_and_start_leg(self, leg):
        leg.return_value = {"leg_minutes": 10, "leg_distance_m": 500, "leg_path": []}
        client = TestClient(app)
        response = client.post("/api/recommend", json={"start_lat":35.1,"start_lon":129.03,
            "stop_count":3,"categories":["식당"],"max_minutes":30})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_walk_minutes"], 30)
        self.assertEqual(data["total_minutes"], 30 + sum(s["duration_min"] for s in data["stops"]))
        self.assertTrue(data["over_budget"])
        ids = [s["id"] for s in data["stops"]]
        ids[0] = data["alternatives"][0]["id"]
        swap = client.post("/api/recommend/recalculate", json={"start_lat":35.1,
            "start_lon":129.03,"stop_ids":ids})
        self.assertEqual(swap.status_code, 200)
        self.assertEqual(swap.json()["stops"][0]["id"], ids[0])
        self.assertEqual(swap.json()["total_walk_minutes"], 30)
        self.assertEqual(client.post("/api/recommend/recalculate", json={"start_lat":35.1,
            "start_lon":129.03,"stop_ids":["unknown"]}).status_code, 422)

    def test_catalog_durations(self):
        catalog = timed_catalog()
        self.assertTrue(catalog.duration_min.gt(0).all())
        self.assertTrue(catalog.loc[catalog.place_type.eq("market"), "duration_min"].eq(60).all())


if __name__ == "__main__":
    unittest.main()
