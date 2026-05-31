import json
import os
import pytest

from src.config import DOCUMENTS_DIR, SYNTHETIC_DIR
from src.main import OrchestratorEngine
from src.connectors.graph_connector import MicrosoftGraphConnector
from src.connectors.lms_connector import MoodleLmsConnector


def test_startup_pack_has_18_certifications_and_docs():
    with open(os.path.join(SYNTHETIC_DIR, "certifications.json"), encoding="utf-8") as f:
        data = json.load(f)
    certs = data["certifications"]
    assert len(certs) == 18
    for cert in certs:
        guide = os.path.join(DOCUMENTS_DIR, f"{cert['id'].lower().replace('-', '')}_guide.md")
        assert os.path.exists(guide)


def test_learner_pipeline_returns_cited_resources_and_quiz():
    engine = OrchestratorEngine()
    profile, paths, plan, engagement, quiz = engine.run_learner_pipeline(
        "pytest_pipeline",
        "I am Avery Stone and I want AZ-204.",
        "EMP-001",
    )
    assert profile.certification_target == "AZ-204"
    assert paths
    assert all("learn.microsoft.com" in p["resource_url"] for p in paths)
    assert sum(w.hours_allocated for w in plan.schedule) == plan.total_hours
    assert engagement["recommended_time"]
    assert len(quiz.questions) == 10
    assert all(q.citation.startswith("[Ref:") for q in quiz.questions)


def test_final_exam_badge_threshold_and_persistence():
    engine = OrchestratorEngine()
    profile, _, _, _, quiz = engine.run_learner_pipeline(
        "pytest_badge",
        "I want to prepare for AI-900.",
        "EMP-005",
    )
    failed = engine.run_final_exam_evaluation("pytest_badge", profile, quiz, 64.9)
    assert not failed.passed
    assert failed.badge is None

    passed = engine.run_final_exam_evaluation("pytest_badge", profile, quiz, 65.0)
    assert passed.passed
    assert passed.badge is not None
    assert any(b.badge_id == passed.badge.badge_id for b in engine.get_badges_by_learner(profile.learner_id))


def test_learning_activity_verification_uses_evidence_signals():
    engine = OrchestratorEngine()
    profile, _, plan, _, _ = engine.run_learner_pipeline(
        "pytest_activity",
        "I want to prepare for AZ-204.",
        "EMP-001",
    )
    report = engine.run_learning_activity_verification("pytest_activity", profile, plan)
    assert report.learner_id == profile.learner_id
    assert 0 <= report.average_completion_confidence <= 100
    assert report.total_modules >= report.completed_modules
    assert report.evidence_summary
    assert report.recommendation


def test_reazon_readiness_formula_is_exam_and_workiq_aware():
    engine = OrchestratorEngine()
    profile, _, _, _, quiz = engine.run_learner_pipeline(
        "pytest_reazon_formula",
        "I want to prepare for AZ-204.",
        "EMP-001",
    )
    report = engine.run_assessment_evaluation("pytest_reazon_formula", profile, quiz, 80.0)
    cert = engine.fabric_iq.get_certification(profile.certification_target)
    weighted_domain = sum(
        report.domain_scores[domain["name"]] * domain["weight"]
        for domain in cert["domains"]
    )
    expected = round(
        (0.45 * weighted_domain)
        + (0.25 * 80.0)
        + (0.15 * report.hours_utilization)
        + (0.15 * report.workload_fit),
        1,
    )
    assert report.overall_readiness == pytest.approx(expected)
    assert 0 <= report.workload_fit <= 100


def test_graph_and_lms_demo_connectors_return_synthetic_signals():
    graph = MicrosoftGraphConnector()
    lms = MoodleLmsConnector()
    signals = graph.get_work_signals("EMP-001")
    assert signals["meeting_hours_per_week"] == 26
    assert graph.get_attendance_records("EMP-001")
    assert lms.get_completion_records("L-1001")


def test_worker_comments_apply_penalty_after_three_misses():
    engine = OrchestratorEngine()
    profiles = []
    for learner_id in ["EMP-010"]:
        profile, _, _, _, _ = engine.run_learner_pipeline(
            f"pytest_comment_{learner_id}",
            "I want to prepare for MB-910.",
            learner_id,
        )
        profiles.append(profile)
    comments = engine.generate_worker_learning_comments(profiles)
    assert comments
    assert comments[0].missed_count >= 3
    assert comments[0].penalty_applied
    assert "Three misses carries a penalty" in comments[0].comment


def test_pdf_exports_are_created(tmp_path):
    engine = OrchestratorEngine()
    profile, _, plan, _, quiz = engine.run_learner_pipeline(
        "pytest_pdf",
        "I want to prepare for SC-900.",
        "EMP-007",
    )
    readiness = engine.run_assessment_evaluation("pytest_pdf", profile, quiz, 80.0)
    badge_result = engine.run_final_exam_evaluation("pytest_pdf", profile, quiz, 80.0)

    study_pdf = engine.export_study_plan_report(profile, plan)
    readiness_pdf = engine.export_readiness_report(profile, readiness)
    badge_pdf = engine.export_badge_report(badge_result.badge)

    for path in [study_pdf, readiness_pdf, badge_pdf]:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 500
