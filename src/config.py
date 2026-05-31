import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Path Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTHETIC_DIR = os.path.join(BASE_DIR, "data", "synthetic")
DOCUMENTS_DIR = os.path.join(BASE_DIR, "data", "documents")
REPORTS_DIR = os.path.join(BASE_DIR, "data", "reports")
DB_PATH = os.path.join(BASE_DIR, "data", "orchestrator.db")

load_dotenv(os.path.join(BASE_DIR, ".env"))

# Azure AI Configuration
FORCE_MOCK_MODE = os.getenv("FORCE_MOCK_MODE", "true").lower() in {"1", "true", "yes", "on"}
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
AZURE_AI_MODEL_DEPLOYMENT = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
FINAL_EXAM_PASS_THRESHOLD = 65.0

# Optional live connector configuration. Demo mode is default to keep hackathon data synthetic.
GRAPH_USE_LIVE = os.getenv("GRAPH_USE_LIVE", "false").lower() in {"1", "true", "yes", "on"}
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
GRAPH_TEST_USER_UPN = os.getenv("GRAPH_TEST_USER_UPN", "")

LMS_PLATFORM = os.getenv("LMS_PLATFORM", "moodle")
LMS_USE_LIVE = os.getenv("LMS_USE_LIVE", "false").lower() in {"1", "true", "yes", "on"}
LMS_BASE_URL = os.getenv("LMS_BASE_URL", "")
LMS_API_TOKEN = os.getenv("LMS_API_TOKEN", "")

# Ensure directories exist
os.makedirs(SYNTHETIC_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def schema_safe_dict(model: BaseModel) -> Dict[str, Any]:
    """Helper to convert Pydantic models to JSON-safe dictionaries."""
    return model.model_dump()

# Data Models
class LearnerProfile(BaseModel):
    learner_id: str
    employee_id: str
    name: str
    role: str
    certification_target: str
    practice_score_avg: float
    hours_studied: float
    exam_outcome: str = "None"
    status: str = "IN PROGRESS"
    meeting_hours_per_week: int = 15
    focus_hours_per_week: int = 15
    preferred_learning_slot: str = "Morning"
    weekly_study_budget_hours: int = 5

class StudyWeek(BaseModel):
    week_number: int
    focus_domains: List[str]
    hours_allocated: int
    workload_adjusted: bool
    adjustment_reason: Optional[str] = None

class StudyPlan(BaseModel):
    learner_id: str
    certification_target: str
    total_weeks: int
    total_hours: int
    schedule: List[StudyWeek]

class QuizQuestion(BaseModel):
    question_id: int
    domain: str
    question_text: str
    options: List[str]
    correct_option_index: int
    citation: str
    explanation: str

class Quiz(BaseModel):
    quiz_id: str
    learner_id: str
    certification_target: str
    questions: List[QuizQuestion]

class ReadinessReport(BaseModel):
    learner_id: str
    certification_target: str
    domain_scores: Dict[str, float]
    hours_utilization: float
    workload_fit: float = 100.0
    practice_score_avg: float
    overall_readiness: float
    booking_recommendation: str
    remediation_plan: str

class ExamBadge(BaseModel):
    badge_id: str
    name: str
    certification_target: str
    issued_to: str
    score: float
    criteria: str

class FinalExamResult(BaseModel):
    learner_id: str
    certification_target: str
    final_exam_score: float
    passed: bool
    pass_threshold: float = FINAL_EXAM_PASS_THRESHOLD
    badge: Optional[ExamBadge] = None
    message: str

class LearningActivityRecord(BaseModel):
    learner_id: str
    certification_target: str
    domain_name: str
    module_id: str
    source: str
    status: str
    attendance_minutes: int = 0
    expected_minutes: int = 45
    watch_percentage: float = 0.0
    checkpoint_score: float = 0.0
    reflection_submitted: bool = False

class LearningActivityReport(BaseModel):
    learner_id: str
    certification_target: str
    completed_modules: int
    total_modules: int
    average_completion_confidence: float
    weak_domains: List[str]
    evidence_summary: List[str]
    recommendation: str

class WorkerLearningComment(BaseModel):
    learner_id: str
    name: str
    certification_target: str
    missed_count: int
    penalty_applied: bool
    comment: str

class RiskAssessment(BaseModel):
    learner_id: str
    name: str
    meeting_hours: int
    risk_level: str
    reason: str

class BuddyMatch(BaseModel):
    learner_a_id: str
    learner_a_name: str
    learner_b_id: str
    learner_b_name: str
    certification_target: str
    common_slot: str

class ManagerInsights(BaseModel):
    total_learners: int
    average_readiness: float
    readiness_by_exam: Dict[str, float]
    at_risk_learners: List[RiskAssessment]
    buddy_recommendations: List[BuddyMatch]
    learner_comments: List[WorkerLearningComment] = []
