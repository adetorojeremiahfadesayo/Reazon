import json
import os
from typing import Any, Dict, List, Optional

import requests

from src.config import (
    AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID,
    GRAPH_USE_LIVE, SYNTHETIC_DIR
)


class MicrosoftGraphConnector:
    """
    Microsoft Graph connector with demo fallback.

    Live mode uses app-only OAuth client credentials. Demo mode reads synthetic
    Graph-style calendar and class attendance signals.
    """
    def __init__(self):
        self.demo_path = os.path.join(SYNTHETIC_DIR, "graph_demo_activity.json")

    @property
    def live_available(self) -> bool:
        return bool(GRAPH_USE_LIVE and AZURE_TENANT_ID and AZURE_CLIENT_ID and AZURE_CLIENT_SECRET)

    def _load_demo_users(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.demo_path):
            return []
        with open(self.demo_path, "r", encoding="utf-8") as f:
            return json.load(f).get("users", [])

    def get_demo_user(self, employee_id: str) -> Optional[Dict[str, Any]]:
        for user in self._load_demo_users():
            if user.get("employee_id") == employee_id:
                return user
        return None

    def get_work_signals(self, employee_id: str) -> Optional[Dict[str, Any]]:
        demo_user = self.get_demo_user(employee_id)
        if demo_user:
            return {
                "employee_id": employee_id,
                "meeting_hours_per_week": demo_user.get("meeting_hours_per_week", 15),
                "focus_hours_per_week": demo_user.get("focus_hours_per_week", 15),
                "preferred_learning_slot": demo_user.get("preferred_learning_slot", "Morning"),
                "weekly_study_budget_hours": demo_user.get("weekly_study_budget_hours", 5)
            }
        return None

    def get_attendance_records(self, employee_id: str) -> List[Dict[str, Any]]:
        demo_user = self.get_demo_user(employee_id)
        if demo_user:
            return demo_user.get("class_attendance", [])
        return []

    def _access_token(self) -> str:
        token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
        response = requests.post(
            token_url,
            data={
                "client_id": AZURE_CLIENT_ID,
                "client_secret": AZURE_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials"
            },
            timeout=20
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_live_calendar_events(self, user_principal_name: str) -> List[Dict[str, Any]]:
        """Optional production helper. Not used in demo mode."""
        token = self._access_token()
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user_principal_name}/calendar/events",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20
        )
        response.raise_for_status()
        return response.json().get("value", [])
