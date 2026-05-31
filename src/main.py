import os
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Tuple
from src.config import (
    DB_PATH, FINAL_EXAM_PASS_THRESHOLD, LearnerProfile, StudyPlan, Quiz,
    ReadinessReport, ManagerInsights, ExamBadge, FinalExamResult,
    LearningActivityRecord, LearningActivityReport, WorkerLearningComment,
    SYNTHETIC_DIR
)
from src.iq_integration import FoundryIQ, FabricIQ, WorkIQ
from src.agents import (
    LearnerProfilerAgent, LearningPathCuratorAgent, StudyPlanAgent,
    EngagementAgent, AssessmentAgent, ProgressAgent, BookingRecommenderAgent,
    LearningActivityVerifierAgent, ManagerInsightsAgent, PeerCollaborationAgent,
    QualityCriticAgent
)
from src.reports import export_badge_pdf, export_readiness_pdf, export_study_plan_pdf
from src.connectors.graph_connector import MicrosoftGraphConnector
from src.connectors.lms_connector import MoodleLmsConnector

class OrchestratorEngine:
    def __init__(self):
        # Initialize Intelligence Layers
        self.foundry_iq = FoundryIQ()
        self.fabric_iq = FabricIQ()
        self.work_iq = WorkIQ()
        self.graph_connector = MicrosoftGraphConnector()
        self.lms_connector = MoodleLmsConnector()

        # Initialize 10 Agents
        self.profiler = LearnerProfilerAgent()
        self.curator = LearningPathCuratorAgent()
        self.planner = StudyPlanAgent()
        self.engagement = EngagementAgent()
        self.assessment = AssessmentAgent()
        self.progress = ProgressAgent()
        self.recommender = BookingRecommenderAgent()
        self.activity_verifier = LearningActivityVerifierAgent()
        self.manager = ManagerInsightsAgent()
        self.peers = PeerCollaborationAgent()
        self.critic = QualityCriticAgent()

        # Database Setup
        self._init_db()

    def _load_learning_activity_records(self) -> List[LearningActivityRecord]:
        path = os.path.join(SYNTHETIC_DIR, "learning_activity.json")
        records = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                records.extend(LearningActivityRecord(**record) for record in json.load(f))
        return records

    def _activity_records_for_profile(self, profile: LearnerProfile) -> List[LearningActivityRecord]:
        records = self._load_learning_activity_records()
        attendance_by_module = {
            item.get("module_id"): item
            for item in self.graph_connector.get_attendance_records(profile.employee_id)
        }
        lms_by_module = {
            item.get("module_id"): item
            for item in self.lms_connector.get_completion_records(profile.learner_id)
        }
        existing_modules = {record.module_id for record in records if record.learner_id == profile.learner_id}

        for module_id in set(attendance_by_module) | set(lms_by_module):
            if module_id in existing_modules:
                continue
            attendance = attendance_by_module.get(module_id, {})
            lms = lms_by_module.get(module_id, {})
            records.append(
                LearningActivityRecord(
                    learner_id=profile.learner_id,
                    certification_target=profile.certification_target,
                    domain_name=module_id,
                    module_id=module_id,
                    source="Microsoft Graph + Moodle LMS demo",
                    status=lms.get("status", "completed" if attendance.get("joined") else "missed"),
                    attendance_minutes=attendance.get("attendance_minutes", 0),
                    expected_minutes=attendance.get("expected_minutes", 45),
                    watch_percentage=lms.get("watch_percentage", 0.0),
                    checkpoint_score=lms.get("checkpoint_score", 0.0),
                    reflection_submitted=lms.get("reflection_submitted", False)
                )
            )
        return records

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                agent_name TEXT,
                trace_content TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS badges (
                badge_id TEXT PRIMARY KEY,
                learner_id TEXT,
                certification_target TEXT,
                issued_to TEXT,
                score REAL,
                badge_json TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_agent_traces(self, session_id: str, agent):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for t in agent.get_traces():
            c.execute(
                "INSERT INTO traces (session_id, agent_name, trace_content) VALUES (?, ?, ?)",
                (session_id, agent.name, t)
            )
        conn.commit()
        conn.close()

    def get_traces_by_session(self, session_id: str) -> List[Dict[str, str]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT agent_name, trace_content FROM traces WHERE session_id = ?", (session_id,))
        rows = c.fetchall()
        conn.close()
        return [{"agent": r["agent_name"], "content": r["trace_content"]} for r in rows]

    def clear_session_traces(self, session_id: str):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM traces WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def save_badge(self, badge: ExamBadge, learner_id: str):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO badges
            (badge_id, learner_id, certification_target, issued_to, score, badge_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                badge.badge_id,
                learner_id,
                badge.certification_target,
                badge.issued_to,
                badge.score,
                json.dumps(badge.model_dump())
            )
        )
        conn.commit()
        conn.close()

    def get_badges_by_learner(self, learner_id: str) -> List[ExamBadge]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT badge_json FROM badges WHERE learner_id = ? ORDER BY certification_target",
            (learner_id,)
        )
        rows = c.fetchall()
        conn.close()
        return [ExamBadge(**json.loads(r["badge_json"])) for r in rows]

    def get_all_badges(self) -> List[ExamBadge]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT badge_json FROM badges ORDER BY certification_target, issued_to")
        rows = c.fetchall()
        conn.close()
        return [ExamBadge(**json.loads(r["badge_json"])) for r in rows]

    def run_learner_pipeline(
        self,
        session_id: str,
        text_input: str,
        employee_id: str,
        weeks: int = 4
    ) -> Tuple[LearnerProfile, List[Dict[str, Any]], StudyPlan, Dict[str, Any], Quiz]:
        """
        Runs the full learner planning flow:
        Input Audit -> Profile -> Profile Audit -> Curation -> Scheduling -> Schedule Audit -> Engagement -> Quiz Generation -> Quiz Audit.
        """
        self.clear_session_traces(session_id)

        # 1. Input Audit
        clean_text = self.critic.audit_input(text_input)
        self.save_agent_traces(session_id, self.critic)

        # 2. Learner Profile
        profile = self.profiler.execute(clean_text, employee_id, self.work_iq, self.fabric_iq)
        self.save_agent_traces(session_id, self.profiler)

        # 3. Profile Audit
        self.critic.audit_profile(profile)
        self.save_agent_traces(session_id, self.critic)

        # 4-6. Run independent content, scheduling, and assessment agents concurrently.
        cert_data = self.fabric_iq.get_certification(profile.certification_target)
        with ThreadPoolExecutor(max_workers=3) as executor:
            curated_future = executor.submit(self.curator.execute, profile, self.foundry_iq, self.fabric_iq)
            plan_future = executor.submit(self.planner.execute, profile, cert_data, weeks)
            quiz_future = executor.submit(self.assessment.execute, profile, self.foundry_iq, self.fabric_iq)

            curated_paths = curated_future.result()
            plan = plan_future.result()
            quiz = quiz_future.result()

        self.save_agent_traces(session_id, self.curator)
        self.save_agent_traces(session_id, self.planner)
        self.save_agent_traces(session_id, self.assessment)

        # 7. Study Plan Audit
        self.critic.audit_study_plan(plan)
        self.save_agent_traces(session_id, self.critic)

        # 8. Engagement
        engagement_report = self.engagement.execute(profile, plan)
        self.save_agent_traces(session_id, self.engagement)

        # 9. Quiz Audit
        self.critic.audit_quiz(quiz)
        self.save_agent_traces(session_id, self.critic)

        return profile, curated_paths, plan, engagement_report, quiz

    def run_assessment_evaluation(
        self,
        session_id: str,
        profile: LearnerProfile,
        quiz: Quiz,
        score: float
    ) -> ReadinessReport:
        """
        Runs the assessment evaluation flow:
        Progress Evaluation -> Booking Recommender -> Readiness Audit.
        """
        cert_data = self.fabric_iq.get_certification(profile.certification_target)
        
        # 1. Progress Evaluation
        report = self.progress.execute(profile, score, cert_data)
        self.save_agent_traces(session_id, self.progress)

        # 2. Booking Recommender
        final_report = self.recommender.execute(report, cert_data)
        self.save_agent_traces(session_id, self.recommender)

        # 3. Readiness Audit
        self.critic.audit_readiness(final_report)
        self.save_agent_traces(session_id, self.critic)

        return final_report

    def run_learning_activity_verification(
        self,
        session_id: str,
        profile: LearnerProfile,
        plan: StudyPlan
    ) -> LearningActivityReport:
        records = self._activity_records_for_profile(profile)
        report = self.activity_verifier.execute(profile, plan, records)
        self.save_agent_traces(session_id, self.activity_verifier)
        self.critic.audit_learning_activity_report(report)
        self.save_agent_traces(session_id, self.critic)
        return report

    def run_final_exam_evaluation(
        self,
        session_id: str,
        profile: LearnerProfile,
        quiz: Quiz,
        score: float
    ) -> FinalExamResult:
        """
        Evaluates the final exam attempt and unlocks a certification badge at 65%+.
        """
        passed = score >= FINAL_EXAM_PASS_THRESHOLD
        badge = None
        if passed:
            badge = ExamBadge(
                badge_id=f"MS-STARTUP-{profile.certification_target}-{profile.learner_id}",
                name=f"{profile.certification_target} Startup Professional Badge",
                certification_target=profile.certification_target,
                issued_to=profile.name,
                score=round(score, 1),
                criteria=f"Passed final exam with at least {FINAL_EXAM_PASS_THRESHOLD}%"
            )

        result = FinalExamResult(
            learner_id=profile.learner_id,
            certification_target=profile.certification_target,
            final_exam_score=round(score, 1),
            passed=passed,
            badge=badge,
            message=(
                f"Badge unlocked for {profile.certification_target}."
                if passed
                else f"Final exam not passed yet. Retake after remediation; target score is {FINAL_EXAM_PASS_THRESHOLD}%."
            )
        )
        self.critic.audit_final_exam_result(result)
        self.save_agent_traces(session_id, self.critic)
        if result.badge:
            self.save_badge(result.badge, profile.learner_id)
        return result

    def run_manager_pipeline(
        self,
        session_id: str,
        profiles: List[LearnerProfile],
        reports: List[ReadinessReport]
    ) -> ManagerInsights:
        """
        Runs the manager analytics flow:
        Peer Buddy Matching -> Dashboard Aggregation -> Insights Audit.
        """
        self.clear_session_traces(session_id)

        # 1. Peer Study Buddy Matching
        buddy_matches = self.peers.execute(profiles)
        self.save_agent_traces(session_id, self.peers)

        # 2. Manager Insights Aggregation
        insights = self.manager.execute(profiles, reports, self.work_iq)
        insights.buddy_recommendations = buddy_matches
        insights.learner_comments = self.generate_worker_learning_comments(profiles)
        self.save_agent_traces(session_id, self.manager)

        # 3. Manager Insights Audit
        self.critic.audit_manager_insights(insights)
        self.save_agent_traces(session_id, self.critic)

        return insights

    def generate_worker_learning_comments(self, profiles: List[LearnerProfile]) -> List[WorkerLearningComment]:
        comments = []
        for profile in profiles:
            cert = self.fabric_iq.get_certification(profile.certification_target)
            if not cert:
                continue
            records = self._activity_records_for_profile(profile)
            evidence_by_domain = {}
            for record in records:
                if record.learner_id != profile.learner_id or record.certification_target != profile.certification_target:
                    continue
                confidence = self.activity_verifier._confidence_for_record(record)
                evidence_by_domain[record.domain_name] = max(evidence_by_domain.get(record.domain_name, 0.0), confidence)

            missed_count = 0
            for domain in cert.get("domains", []):
                domain_name = domain["name"]
                domain_confidence = evidence_by_domain.get(domain_name, 0.0)
                if domain_confidence < 70.0:
                    missed_count += 1

            penalty = missed_count >= 3
            if penalty:
                comment = (
                    f"{profile.name}, you did not meet up with {missed_count} planned learning checkpoints. "
                    "Three misses carries a penalty: your readiness is flagged for manager review and remediation is required before final booking."
                )
            elif missed_count > 0:
                comment = (
                    f"{profile.name}, you have {missed_count} missed or weak learning checkpoint(s). "
                    "Please catch up before attempting the final exam."
                )
            else:
                comment = f"{profile.name}, your class/module evidence is on track for {profile.certification_target}."

            comments.append(
                WorkerLearningComment(
                    learner_id=profile.learner_id,
                    name=profile.name,
                    certification_target=profile.certification_target,
                    missed_count=missed_count,
                    penalty_applied=penalty,
                    comment=comment
                )
            )
        return comments

    def export_study_plan_report(self, profile: LearnerProfile, plan: StudyPlan) -> str:
        return export_study_plan_pdf(profile, plan)

    def export_readiness_report(self, profile: LearnerProfile, report: ReadinessReport) -> str:
        return export_readiness_pdf(profile, report)

    def export_badge_report(self, badge: ExamBadge) -> str:
        return export_badge_pdf(badge)

# CLI Runner for development testing
if __name__ == "__main__":
    print("Initializing Orchestrator Engine...")
    engine = OrchestratorEngine()
    
    # Run test profile for EMP-001 (Jane Doe)
    session = "cli_test_session"
    print("\n--- Running Learner Pipeline for Jane Doe ---")
    profile, paths, plan, eng, quiz = engine.run_learner_pipeline(
        session,
        "I am Jane Doe. I want to study for the AZ-204 exam.",
        "EMP-001"
    )
    print(f"Profile: {profile.name} - Target: {profile.certification_target}")
    print(f"Engagement: {eng['reminder_message']}")
    print(f"Questions Generated: {len(quiz.questions)}")
    
    print("\n--- Evaluating Assessment (Simulated 80% Quiz Score) ---")
    report = engine.run_assessment_evaluation(session, profile, quiz, 80.0)
    print(f"Readiness: {report.overall_readiness}% - Booking: {report.booking_recommendation}")
    print(f"Remediation: {report.remediation_plan}")

    # Dump logs
    print("\n--- Traces Recorded ---")
    for t in engine.get_traces_by_session(session):
        print(f"[{t['agent']}] {t['content']}")
