import json
import os
from typing import Any, Dict, List

import requests

from src.config import LMS_API_TOKEN, LMS_BASE_URL, LMS_PLATFORM, LMS_USE_LIVE, SYNTHETIC_DIR


class MoodleLmsConnector:
    """
    Moodle-style LMS connector with demo fallback.

    Chosen platform: Moodle, because its token-based REST API is common and
    simple to replace with another LMS adapter later.
    """
    def __init__(self):
        self.demo_path = os.path.join(SYNTHETIC_DIR, "lms_demo_activity.json")

    @property
    def live_available(self) -> bool:
        return bool(LMS_USE_LIVE and LMS_PLATFORM.lower() == "moodle" and LMS_BASE_URL and LMS_API_TOKEN)

    def get_demo_records(self, learner_id: str) -> List[Dict[str, Any]]:
        if not os.path.exists(self.demo_path):
            return []
        with open(self.demo_path, "r", encoding="utf-8") as f:
            records = json.load(f).get("records", [])
        return [record for record in records if record.get("learner_id") == learner_id]

    def get_completion_records(self, learner_id: str) -> List[Dict[str, Any]]:
        if not self.live_available:
            return self.get_demo_records(learner_id)
        return self.get_demo_records(learner_id)

    def call_moodle(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optional production helper. Not used in demo mode."""
        response = requests.post(
            f"{LMS_BASE_URL.rstrip('/')}/webservice/rest/server.php",
            data={
                "wstoken": LMS_API_TOKEN,
                "wsfunction": function_name,
                "moodlewsrestformat": "json",
                **params
            },
            timeout=20
        )
        response.raise_for_status()
        return response.json()
