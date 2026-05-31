import sys
import os
import json
import re
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure src/ is on the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import OrchestratorEngine
from src.config import (
    LearnerProfile, StudyPlan, Quiz, ReadinessReport,
    ManagerInsights, FinalExamResult, FINAL_EXAM_PASS_THRESHOLD, REPORTS_DIR
)

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class LearnerProfileRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to study for a Microsoft certification exam."
    weeks: int = 4

class LearnerProfileResponse(BaseModel):
    learner_id: str
    name: str
    role: str
    certification_target: str
    practice_score_avg: float
    meeting_hours_per_week: int
    weekly_study_budget_hours: int
    preferred_learning_slot: str

class StudyPlanRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to study for a Microsoft certification exam."
    weeks: int = 4

class StudyWeekResponse(BaseModel):
    week_number: int
    focus_domains: List[str]
    hours_allocated: int
    workload_adjusted: bool
    adjustment_reason: Optional[str] = None

class StudyPlanResponse(BaseModel):
    learner_id: str
    certification_target: str
    total_weeks: int
    total_hours: int
    schedule: List[StudyWeekResponse]

class QuizRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to take a practice assessment."

class QuizQuestionResponse(BaseModel):
    question_id: int
    domain: str
    question_text: str
    options: List[str]
    correct_option_index: int
    citation: str
    explanation: str

class QuizResponse(BaseModel):
    quiz_id: str
    learner_id: str
    certification_target: str
    questions: List[QuizQuestionResponse]
    assessment_type: str = "checkpoint"
    duration_minutes: int = 20
    seat_minutes: int = 30
    question_count_standard: str = "10 checkpoint questions"

class QuizSubmitRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to take a practice assessment."
    answers: dict  # question_id -> selected_option_index
    assessment_type: str = "checkpoint"

class AssessmentResultResponse(BaseModel):
    score_percentage: float
    passed: bool
    overall_readiness: float
    booking_recommendation: str
    remediation_plan: str
    badge_id: Optional[str] = None
    badge_name: Optional[str] = None

class LearningActivityRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to verify my learning activity."
    weeks: int = 4

class LearningActivityResponse(BaseModel):
    learner_id: str
    certification_target: str
    completed_modules: int
    total_modules: int
    average_completion_confidence: float
    weak_domains: List[str]
    evidence_summary: List[str]
    recommendation: str

class ManagerInsightsRequest(BaseModel):
    pass  # Uses all learners from synthetic data

class ManagerInsightsResponse(BaseModel):
    total_learners: int
    average_readiness: float
    readiness_by_exam: dict
    at_risk_learners: List[dict]
    buddy_recommendations: List[dict]
    learner_comments: List[dict] = []

class LearnerOptionResponse(BaseModel):
    learner_id: str
    employee_id: str
    name: str
    role: str
    certification_target: str
    practice_score_avg: float
    hours_studied: float
    exam_outcome: str
    status: str

class LearnerWorkspaceRequest(BaseModel):
    employee_id: str
    text_input: str = "I want to study for a Microsoft certification exam."
    weeks: int = 4

class LearnerWorkspaceResponse(BaseModel):
    session_id: str
    profile: dict
    learning_paths: List[dict]
    plan: dict
    engagement: dict
    quiz: dict
    activity: dict
    badges: List[dict]
    traces: List[dict]

class ReportFileResponse(BaseModel):
    file_name: str
    report_type: str
    learner_id: str
    certification_target: str
    size_bytes: int
    modified_at: str
    download_url: str

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CertPrep-Ex Multi-Agent System",
    description="10-agent orchestration for Microsoft certification readiness. "
                "Integrates with Microsoft Copilot Studio via REST API.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

engine = OrchestratorEngine()


@app.get("/health", tags=["System"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "mock_mode": True}


@app.get("/api/learners", response_model=List[LearnerOptionResponse], tags=["Learner"])
def list_learners():
    """
    Returns the synthetic learner personas available to the web app.
    """
    learners_path = os.path.join(engine.fabric_iq.certifications_path.replace("certifications.json", "learners.json"))
    with open(learners_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/reports", response_model=List[ReportFileResponse], tags=["Reports"])
def list_reports():
    """
    Lists generated PDF reports so the web app can expose a reports center.
    """
    reports = []
    if not os.path.exists(REPORTS_DIR):
        return reports

    for file_name in sorted(os.listdir(REPORTS_DIR)):
        if not file_name.lower().endswith(".pdf"):
            continue
        path = os.path.join(REPORTS_DIR, file_name)
        if not os.path.isfile(path):
            continue

        stem = file_name[:-4]
        report_type = "Badge certificate" if stem.startswith(("MS-STARTUP", "MS-WORKFORCE")) else "Readiness report"
        if "study_plan" in stem:
            report_type = "Study plan"
        elif "readiness" in stem:
            report_type = "Readiness report"

        learner_match = re.search(r"(?:L|EMP)-\d+", stem)
        cert_match = re.search(r"(?:AI|AZ|DP|MB|MS|PL|SC)-\d{3}", stem)
        learner_id = learner_match.group(0) if learner_match else "Unknown"
        certification_target = cert_match.group(0) if cert_match else "Unknown"

        stat = os.stat(path)
        reports.append(
            ReportFileResponse(
                file_name=file_name,
                report_type=report_type,
                learner_id=learner_id,
                certification_target=certification_target,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                download_url=f"/reports/{file_name}"
            )
        )
    return reports


@app.post("/api/learner/workspace", response_model=LearnerWorkspaceResponse, tags=["Learner"])
def run_learner_workspace(request: LearnerWorkspaceRequest):
    """
    Runs the complete learner workspace flow used by the React app.
    """
    session_id = f"web_{uuid.uuid4().hex[:8]}"
    try:
        profile, learning_paths, plan, engagement, quiz = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id, request.weeks
        )
        activity = engine.run_learning_activity_verification(session_id, profile, plan)
        engine.export_study_plan_report(profile, plan)
        badges = engine.get_badges_by_learner(profile.learner_id)
        traces = engine.get_traces_by_session(session_id)
        return LearnerWorkspaceResponse(
            session_id=session_id,
            profile=profile.model_dump(),
            learning_paths=learning_paths,
            plan=plan.model_dump(),
            engagement=engagement,
            quiz=quiz.model_dump(),
            activity=activity.model_dump(),
            badges=[badge.model_dump() for badge in badges],
            traces=traces
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/profile", response_model=LearnerProfileResponse, tags=["Learner"])
def get_learner_profile(request: LearnerProfileRequest):
    """
    Runs the learner profiling pipeline and returns the structured profile.
    """
    session_id = f"api_{uuid.uuid4().hex[:8]}"
    try:
        profile, _, _, _, _ = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id, request.weeks
        )
        return LearnerProfileResponse(
            learner_id=profile.learner_id,
            name=profile.name,
            role=profile.role,
            certification_target=profile.certification_target,
            practice_score_avg=profile.practice_score_avg,
            meeting_hours_per_week=profile.meeting_hours_per_week,
            weekly_study_budget_hours=profile.weekly_study_budget_hours,
            preferred_learning_slot=profile.preferred_learning_slot
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/plan", response_model=StudyPlanResponse, tags=["Learner"])
def get_study_plan(request: StudyPlanRequest):
    """
    Runs the full learner pipeline and returns the study plan.
    """
    session_id = f"api_{uuid.uuid4().hex[:8]}"
    try:
        _, _, plan, _, _ = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id, request.weeks
        )
        schedule = [
            StudyWeekResponse(
                week_number=w.week_number,
                focus_domains=w.focus_domains,
                hours_allocated=w.hours_allocated,
                workload_adjusted=w.workload_adjusted,
                adjustment_reason=w.adjustment_reason
            )
            for w in plan.schedule
        ]
        return StudyPlanResponse(
            learner_id=plan.learner_id,
            certification_target=plan.certification_target,
            total_weeks=plan.total_weeks,
            total_hours=plan.total_hours,
            schedule=schedule
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/assessment", response_model=QuizResponse, tags=["Learner"])
def get_quiz(request: QuizRequest):
    """
    Generates a grounded practice quiz.
    """
    session_id = f"api_{uuid.uuid4().hex[:8]}"
    try:
        _, _, _, _, quiz = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id
        )
        questions = [
            QuizQuestionResponse(
                question_id=q.question_id,
                domain=q.domain,
                question_text=q.question_text,
                options=q.options,
                correct_option_index=q.correct_option_index,
                citation=q.citation,
                explanation=q.explanation
            )
            for q in quiz.questions
        ]
        return QuizResponse(
            quiz_id=quiz.quiz_id,
            learner_id=quiz.learner_id,
            certification_target=quiz.certification_target,
            questions=questions,
            assessment_type=quiz.assessment_type,
            duration_minutes=quiz.duration_minutes,
            seat_minutes=quiz.seat_minutes,
            question_count_standard=quiz.question_count_standard
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/final-exam", response_model=QuizResponse, tags=["Learner"])
def get_final_exam(request: QuizRequest):
    """
    Generates a Microsoft-style final exam simulator question set.
    This stays synthetic and grounded to the certification ontology for demo speed.
    """
    session_id = f"api_final_{uuid.uuid4().hex[:8]}"
    try:
        profile, _, _, _, _ = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id
        )
        quiz = engine.assessment.execute(profile, engine.foundry_iq, engine.fabric_iq, assessment_type="final")
        engine.critic.audit_quiz(quiz)
        questions = [
            QuizQuestionResponse(
                question_id=q.question_id,
                domain=q.domain,
                question_text=q.question_text,
                options=q.options,
                correct_option_index=q.correct_option_index,
                citation=q.citation,
                explanation=q.explanation
            )
            for q in quiz.questions
        ]
        return QuizResponse(
            quiz_id=quiz.quiz_id,
            learner_id=quiz.learner_id,
            certification_target=quiz.certification_target,
            questions=questions,
            assessment_type=quiz.assessment_type,
            duration_minutes=quiz.duration_minutes,
            seat_minutes=quiz.seat_minutes,
            question_count_standard=quiz.question_count_standard
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/assessment/submit", response_model=AssessmentResultResponse, tags=["Learner"])
def submit_assessment(request: QuizSubmitRequest):
    """
    Submits quiz answers and returns readiness score + booking recommendation.
    Re-runs the pipeline to get the quiz, then evaluates answers.
    This is a stateless version. In production, cache the quiz by session.
    """
    session_id = f"api_{uuid.uuid4().hex[:8]}"
    try:
        # Re-run learner pipeline to get profile + quiz
        profile, _, _, _, quiz = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id
        )
        if request.assessment_type == "final":
            quiz = engine.assessment.execute(profile, engine.foundry_iq, engine.fabric_iq, assessment_type="final")
            engine.critic.audit_quiz(quiz)

        # Score the answers
        correct_count = 0
        total_q = len(quiz.questions)
        for q in quiz.questions:
            chosen_idx = request.answers.get(str(q.question_id))
            if chosen_idx is not None and chosen_idx == q.correct_option_index:
                correct_count += 1

        score_percentage = (correct_count / total_q) * 100.0 if total_q > 0 else 0.0

        # Run assessment evaluation
        readiness_report = engine.run_assessment_evaluation(
            session_id, profile, quiz, score_percentage
        )

        engine.export_readiness_report(profile, readiness_report)

        final_result = None
        if request.assessment_type == "final":
            # Run final exam evaluation (badge unlock logic)
            final_result = engine.run_final_exam_evaluation(
                session_id, profile, quiz, score_percentage
            )
            if final_result.badge:
                engine.export_badge_report(final_result.badge)

        return AssessmentResultResponse(
            score_percentage=round(score_percentage, 1),
            passed=final_result.passed if final_result else score_percentage >= FINAL_EXAM_PASS_THRESHOLD,
            overall_readiness=readiness_report.overall_readiness,
            booking_recommendation=readiness_report.booking_recommendation,
            remediation_plan=readiness_report.remediation_plan,
            badge_id=final_result.badge.badge_id if final_result and final_result.badge else None,
            badge_name=final_result.badge.name if final_result and final_result.badge else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learner/activity", response_model=LearningActivityResponse, tags=["Learner"])
def verify_learning_activity(request: LearningActivityRequest):
    """
    Verifies real-learning evidence from synthetic Microsoft Learn/LMS/Teams-style records.
    """
    session_id = f"api_activity_{uuid.uuid4().hex[:8]}"
    try:
        profile, _, plan, _, _ = engine.run_learner_pipeline(
            session_id, request.text_input, request.employee_id, request.weeks
        )
        report = engine.run_learning_activity_verification(session_id, profile, plan)
        return LearningActivityResponse(**report.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manager/insights", response_model=ManagerInsightsResponse, tags=["Manager"])
def get_manager_insights(request: ManagerInsightsRequest):
    """
    Returns aggregate readiness data for all learners in the system.
    """
    session_id = f"api_manager_{uuid.uuid4().hex[:8]}"
    try:
        # Load all learners from synthetic data
        learners_path = os.path.join(engine.fabric_iq.certifications_path.replace("certifications.json", "learners.json"))
        with open(learners_path, "r", encoding="utf-8") as f:
            learners_data = json.load(f)

        all_profiles = []
        all_reports = []
        for l in learners_data:
            work_signals = engine.work_iq.get_signals_by_employee(l["employee_id"]).copy()
            work_signals.pop("employee_id", None)
            temp_profile = LearnerProfile(
                learner_id=l["learner_id"],
                employee_id=l["employee_id"],
                name=l["name"],
                role=l["role"],
                certification_target=l["certification_target"],
                practice_score_avg=l["practice_score_avg"],
                hours_studied=l["hours_studied"],
                exam_outcome=l["exam_outcome"],
                status=l["status"],
                **work_signals
            )
            all_profiles.append(temp_profile)
            mock_score = l["practice_score_avg"] + 4.0
            cert_data = engine.fabric_iq.get_certification(temp_profile.certification_target)
            temp_report = engine.progress.execute(temp_profile, mock_score, cert_data)
            temp_report = engine.recommender.execute(temp_report, cert_data)
            all_reports.append(temp_report)

        insights = engine.run_manager_pipeline(session_id, all_profiles, all_reports)

        return ManagerInsightsResponse(
            total_learners=insights.total_learners,
            average_readiness=insights.average_readiness,
            readiness_by_exam=insights.readiness_by_exam,
            at_risk_learners=[
                {"name": r.name, "meeting_hours": r.meeting_hours, "risk_level": r.risk_level, "reason": r.reason}
                for r in insights.at_risk_learners
            ],
            buddy_recommendations=[
                {"learner_a": b.learner_a_name, "learner_b": b.learner_b_name,
                 "certification_target": b.certification_target, "common_slot": b.common_slot}
                for b in insights.buddy_recommendations
            ],
            learner_comments=[
                {
                    "name": c.name,
                    "certification_target": c.certification_target,
                    "missed_count": c.missed_count,
                    "penalty_applied": c.penalty_applied,
                    "comment": c.comment
                }
                for c in insights.learner_comments
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
