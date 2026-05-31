from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_study_plan_endpoint():
    response = client.post(
        "/api/learner/plan",
        json={
            "employee_id": "EMP-004",
            "text_input": "I am a startup founder preparing for AZ-900.",
            "weeks": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["certification_target"] == "AZ-900"
    assert body["schedule"]
    assert sum(w["hours_allocated"] for w in body["schedule"]) == body["total_hours"]


def test_assessment_and_submit_endpoint_unlocks_badge_when_answers_are_correct():
    quiz_response = client.post(
        "/api/learner/assessment",
        json={
            "employee_id": "EMP-005",
            "text_input": "I want to prepare for AI-900.",
        },
    )
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()
    answers = {str(q["question_id"]): q["correct_option_index"] for q in quiz["questions"]}

    submit_response = client.post(
        "/api/learner/assessment/submit",
        json={
            "employee_id": "EMP-005",
            "text_input": "I want to prepare for AI-900.",
            "answers": answers,
        },
    )
    assert submit_response.status_code == 200
    body = submit_response.json()
    assert body["passed"]
    assert body["badge_id"]


def test_manager_insights_endpoint():
    response = client.post("/api/manager/insights", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["total_learners"] >= 18
    assert body["readiness_by_exam"]
    assert body["learner_comments"]
    assert any(item["penalty_applied"] for item in body["learner_comments"])


def test_learning_activity_endpoint():
    response = client.post(
        "/api/learner/activity",
        json={
            "employee_id": "EMP-001",
            "text_input": "I want to prepare for AZ-204.",
            "weeks": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["learner_id"] == "L-1001"
    assert body["certification_target"] == "AZ-204"
    assert 0 <= body["average_completion_confidence"] <= 100
    assert body["evidence_summary"]


def test_workspace_uses_specific_courses_and_auto_creates_study_plan_pdf():
    workspace_response = client.post(
        "/api/learner/workspace",
        json={
            "employee_id": "EMP-004",
            "text_input": "I am a startup founder preparing for AZ-900.",
            "weeks": 4,
        },
    )
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    assert workspace["learning_paths"]
    assert all(path.get("resource_title") for path in workspace["learning_paths"])
    assert all("/training/browse/" not in path.get("resource_url", "") for path in workspace["learning_paths"])

    reports_response = client.get("/api/reports")
    assert reports_response.status_code == 200
    reports = reports_response.json()
    assert any(
        report["report_type"] == "Study plan"
        and report["learner_id"] == workspace["profile"]["learner_id"]
        and report["certification_target"] == workspace["profile"]["certification_target"]
        for report in reports
    )


def test_reports_endpoint_lists_generated_pdfs():
    response = client.get("/api/reports")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if body:
        report = body[0]
        assert report["file_name"].endswith(".pdf")
        assert report["download_url"].startswith("/reports/")
