import re
from typing import List, Any
from src.config import (
    LearnerProfile, StudyPlan, Quiz, ReadinessReport, ManagerInsights,
    FinalExamResult, LearningActivityReport, FINAL_EXAM_PASS_THRESHOLD
)

class GuardrailException(Exception):
    """Raised when an agent output violates safety or quality rules."""
    pass

class GuardrailsPipeline:
    """
    Validates agent boundaries for safety, grounding, scoring, and data quality.
    """
    def __init__(self):
        self.traces = []
        self.valid_certs = {
            "AI-200", "AI-901", "AZ-400", "AZ-900", "DP-600", "DP-700", "DP-900",
            "SC-900", "SC-100", "PL-900", "MS-900", "MB-800", "AZ-104", "AZ-305",
            "PL-200", "PL-300", "SC-300", "MS-102", "AZ-500"
        }

    def _log(self, rule_id: str, status: str, message: str):
        self.traces.append({"rule_id": rule_id, "status": status, "message": message})

    def _has_pii(self, text: str) -> bool:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+?\d[\d\s().-]{8,}\d)\b'
        return bool(re.search(email_pattern, text) or re.search(phone_pattern, text))

    def _assert_no_pii(self, text: str, rule_id: str, context: str):
        if self._has_pii(text):
            self._log(rule_id, "FAIL", f"PII detected in {context}.")
            raise GuardrailException(f"Unanonymized PII detected in {context}.")

    def validate_profile_input(self, text: str) -> str:
        if not isinstance(text, str):
            self._log("GR-01", "FAIL", "Profile input must be text.")
            raise GuardrailException("Profile input must be text.")

        cleaned = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[SCRUBBED_EMAIL]", text)
        cleaned = re.sub(r'\b(?:\+?\d[\d\s().-]{8,}\d)\b', "[SCRUBBED_PHONE]", cleaned)
        self._log("GR-02", "PASS", "PII scrubbing complete.")
        
        stripped = text.strip()
        if len(stripped) < 5:
            self._log("GR-03", "FAIL", "Input too short.")
            raise GuardrailException("Input text is too short for profiling.")
        if len(stripped) > 4000:
            self._log("GR-03", "FAIL", "Input too long.")
            raise GuardrailException("Input text is too long for profiling.")
        self._log("GR-03", "PASS", "Input length is within bounds.")

        blocked_terms = ["shit", "fuck", "bitch", "idiot"]
        if any(term in text.lower() for term in blocked_terms):
            self._log("GR-04", "FAIL", "Input blocked for offensive language.")
            raise GuardrailException("Input blocked by offensive language guardrail.")

        injection_terms = [
            "ignore previous instructions", "ignore all previous instructions",
            "system prompt", "developer message", "reveal your prompt",
            "jailbreak", "bypass guardrails"
        ]
        if any(term in text.lower() for term in injection_terms):
            self._log("GR-05", "FAIL", "Prompt injection phrase detected.")
            raise GuardrailException("Input blocked by prompt injection guardrail.")
        self._log("GR-04", "PASS", "Offensive language check passed.")
        self._log("GR-05", "PASS", "Prompt injection check passed.")
        return cleaned

    def validate_profile(self, profile: LearnerProfile):
        if not profile.learner_id or not profile.employee_id or not profile.name.strip():
            self._log("GR-06", "FAIL", "Profile identity fields are incomplete.")
            raise GuardrailException("Profile identity fields are incomplete.")
        self._log("GR-06", "PASS", "Profile identity fields validated.")

        if profile.certification_target not in self.valid_certs:
            self._log("GR-07", "FAIL", f"Unknown cert: {profile.certification_target}")
            raise GuardrailException(f"Unknown certification target: {profile.certification_target}")
        self._log("GR-07", "PASS", "Certification target is supported.")
        
        if not (0 <= profile.practice_score_avg <= 100):
            self._log("GR-08", "FAIL", "Practice score out of bounds.")
            raise GuardrailException("Invalid practice score range.")
        self._log("GR-08", "PASS", "Practice score bounds validated.")

        if profile.hours_studied < 0:
            self._log("GR-09", "FAIL", "Hours studied cannot be negative.")
            raise GuardrailException("Hours studied cannot be negative.")
        self._log("GR-09", "PASS", "Hours studied bounds validated.")

        if not (0 <= profile.weekly_study_budget_hours <= 40):
            self._log("GR-10", "FAIL", "Weekly study budget out of bounds.")
            raise GuardrailException("Invalid weekly study budget; value must be between 0 and 40 hours.")
        self._log("GR-10", "PASS", "Weekly study budget bounds validated.")

        if not (0 <= profile.meeting_hours_per_week <= 80 and 0 <= profile.focus_hours_per_week <= 80):
            self._log("GR-11", "FAIL", "Workload signals are out of bounds.")
            raise GuardrailException("Workload signals are out of bounds.")
        self._log("GR-11", "PASS", "Workload signal bounds validated.")

    def validate_study_plan(self, plan: StudyPlan):
        if not plan.schedule:
            self._log("GR-12", "FAIL", "Study plan is empty.")
            raise GuardrailException("Study plan is empty.")
        self._log("GR-12", "PASS", "Study plan is not empty.")

        if plan.total_weeks != len(plan.schedule):
            self._log("GR-13", "FAIL", "Study plan week count mismatch.")
            raise GuardrailException("Study plan week count does not match schedule.")
        if [w.week_number for w in plan.schedule] != list(range(1, plan.total_weeks + 1)):
            self._log("GR-13", "FAIL", "Study plan weeks are not sequential.")
            raise GuardrailException("Study plan weeks must be sequential.")
        self._log("GR-13", "PASS", "Study plan week sequence validated.")

        for week in plan.schedule:
            if week.hours_allocated < 0:
                self._log("GR-14", "FAIL", f"Negative hours in Week {week.week_number}.")
                raise GuardrailException(f"Negative hours in Week {week.week_number}")
            if week.hours_allocated > 0 and not week.focus_domains:
                self._log("GR-15", "FAIL", f"Week {week.week_number} has hours but no domains.")
                raise GuardrailException(f"Week {week.week_number} must include at least one focus domain.")
            if week.hours_allocated > 40:
                self._log("GR-16", "FAIL", f"Week {week.week_number} exceeds realistic weekly load.")
                raise GuardrailException(f"Week {week.week_number} exceeds the weekly study limit.")
        self._log("GR-14", "PASS", "Study plan hours are non-negative.")
        self._log("GR-15", "PASS", "Study weeks with hours include focus domains.")
        self._log("GR-16", "PASS", "Weekly study hours are within bounds.")

        if sum(week.hours_allocated for week in plan.schedule) != plan.total_hours:
            self._log("GR-17", "FAIL", "Total plan hours do not match weekly sum.")
            raise GuardrailException("Study plan total hours must equal the sum of weekly hours.")
        self._log("GR-17", "PASS", "Study plan total hours match weekly allocation.")

        if plan.certification_target not in self.valid_certs:
            self._log("GR-18", "FAIL", "Study plan certification is unsupported.")
            raise GuardrailException("Study plan certification target is unsupported.")
        self._log("GR-18", "PASS", "Study plan certification target validated.")

    def validate_quiz(self, quiz: Quiz):
        if quiz.certification_target not in self.valid_certs:
            self._log("GR-19", "FAIL", "Quiz certification is unsupported.")
            raise GuardrailException("Quiz certification target is unsupported.")
        self._log("GR-19", "PASS", "Quiz certification target validated.")

        for q in quiz.questions:
            if not q.citation or "[" not in q.citation:
                self._log("GR-21", "FAIL", f"Missing citation in Q{q.question_id}")
                raise GuardrailException(f"Question {q.question_id} lacks valid grounding citations.")
            if "http://" in q.citation:
                self._log("GR-22", "FAIL", f"Insecure citation in Q{q.question_id}.")
                raise GuardrailException(f"Question {q.question_id} contains an insecure citation.")
        self._log("GR-21", "PASS", "Assessment citations are present.")
        self._log("GR-22", "PASS", "Assessment citations avoid insecure links.")

        if not (10 <= len(quiz.questions) <= 60):
            self._log("GR-20", "FAIL", "Quiz question count is outside the final exam range.")
            raise GuardrailException("Assessment must contain 10 to 60 questions.")
        self._log("GR-20", "PASS", "Assessment question count validated.")

        for q in quiz.questions:
            if len(q.options) != 4:
                self._log("GR-23", "FAIL", f"Q{q.question_id} option count is invalid.")
                raise GuardrailException(f"Q{q.question_id} does not have exactly 4 options.")
            if not (0 <= q.correct_option_index < len(q.options)):
                self._log("GR-24", "FAIL", f"Q{q.question_id} correct answer index is invalid.")
                raise GuardrailException(f"Q{q.question_id} has an invalid correct answer index.")
            if not q.question_text.strip() or not q.explanation.strip():
                self._log("GR-25", "FAIL", f"Q{q.question_id} is missing question text or explanation.")
                raise GuardrailException(f"Q{q.question_id} is missing question text or explanation.")
        self._log("GR-23", "PASS", "Assessment option counts validated.")
        self._log("GR-24", "PASS", "Assessment answer indexes validated.")
        self._log("GR-25", "PASS", "Assessment question text and explanations validated.")

    def validate_readiness_report(self, report: ReadinessReport):
        if report.certification_target not in self.valid_certs:
            self._log("GR-26", "FAIL", "Readiness certification is unsupported.")
            raise GuardrailException("Readiness certification target is unsupported.")
        self._log("GR-26", "PASS", "Readiness certification target validated.")

        if not (0 <= report.overall_readiness <= 100):
            self._log("GR-27", "FAIL", "Readiness score out of bounds.")
            raise GuardrailException("Calculated readiness out of bounds.")
        if not (0 <= report.hours_utilization <= 100):
            self._log("GR-28", "FAIL", "Hours utilization out of bounds.")
            raise GuardrailException("Hours utilization out of bounds.")
        if not (0 <= report.workload_fit <= 100):
            self._log("GR-28B", "FAIL", "Workload fit out of bounds.")
            raise GuardrailException("Workload fit out of bounds.")
        if not (0 <= report.practice_score_avg <= 100):
            self._log("GR-29", "FAIL", "Practice score snapshot out of bounds.")
            raise GuardrailException("Practice score snapshot out of bounds.")
        for domain, score in report.domain_scores.items():
            if not domain.strip() or not (0 <= score <= 100):
                self._log("GR-30", "FAIL", "Domain score out of bounds.")
                raise GuardrailException("Domain score out of bounds.")
        if report.booking_recommendation not in {"GO", "CONDITIONAL GO", "NOT YET"}:
            self._log("GR-31", "FAIL", "Booking recommendation is invalid.")
            raise GuardrailException("Booking recommendation is invalid.")
        if not report.remediation_plan.strip():
            self._log("GR-32", "FAIL", "Remediation plan is empty.")
            raise GuardrailException("Readiness report must include a remediation plan.")
        self._log("GR-27", "PASS", "Readiness score bounds validated.")
        self._log("GR-28", "PASS", "Hours utilization bounds validated.")
        self._log("GR-28B", "PASS", "Workload fit bounds validated.")
        self._log("GR-29", "PASS", "Practice score snapshot bounds validated.")
        self._log("GR-30", "PASS", "Domain score bounds validated.")
        self._log("GR-31", "PASS", "Booking recommendation category validated.")
        self._log("GR-32", "PASS", "Remediation plan presence validated.")

    def validate_final_exam_result(self, result: FinalExamResult):
        if not (0 <= result.final_exam_score <= 100):
            self._log("GR-33", "FAIL", "Final exam score out of bounds.")
            raise GuardrailException("Final exam score out of bounds.")
        if result.pass_threshold != FINAL_EXAM_PASS_THRESHOLD:
            self._log("GR-34", "FAIL", "Final exam pass threshold was changed unexpectedly.")
            raise GuardrailException("Final exam pass threshold does not match system policy.")
        if result.passed and result.badge is None:
            self._log("GR-35", "FAIL", "Passing final exam did not unlock badge.")
            raise GuardrailException("Final exam pass must unlock a badge.")
        if not result.passed and result.badge is not None:
            self._log("GR-36", "FAIL", "Badge issued on failed final exam.")
            raise GuardrailException("Badge cannot be issued for a failed final exam.")
        if result.badge and result.badge.score < result.pass_threshold:
            self._log("GR-37", "FAIL", "Badge score is below threshold.")
            raise GuardrailException("Badge cannot be issued below the pass threshold.")
        if result.badge and result.badge.certification_target != result.certification_target:
            self._log("GR-38", "FAIL", "Badge certification target mismatch.")
            raise GuardrailException("Badge certification target must match the final exam.")
        self._log("GR-33", "PASS", "Final exam score bounds validated.")
        self._log("GR-34", "PASS", "Final exam pass threshold validated.")
        self._log("GR-35", "PASS", "Passing final exam unlocks a badge.")
        self._log("GR-36", "PASS", "Failed final exam does not issue a badge.")
        self._log("GR-37", "PASS", "Badge score threshold validated.")
        self._log("GR-38", "PASS", "Badge certification target validated.")

    def validate_learning_activity_report(self, report: LearningActivityReport):
        if not (0 <= report.average_completion_confidence <= 100):
            self._log("GR-39", "FAIL", "Learning activity confidence out of bounds.")
            raise GuardrailException("Learning activity confidence out of bounds.")
        if report.completed_modules > report.total_modules:
            self._log("GR-40", "FAIL", "Completed modules exceed total modules.")
            raise GuardrailException("Completed learning modules cannot exceed total planned modules.")
        if report.total_modules < 1:
            self._log("GR-41", "FAIL", "Learning activity report has no planned modules.")
            raise GuardrailException("Learning activity report must include at least one planned module.")
        for item in report.evidence_summary:
            self._assert_no_pii(item, "GR-42", "learning activity evidence")
        self._log("GR-39", "PASS", "Learning activity confidence bounds validated.")
        self._log("GR-40", "PASS", "Learning activity completion counts validated.")
        self._log("GR-41", "PASS", "Learning activity planned module count validated.")
        self._log("GR-42", "PASS", "Learning activity evidence privacy validated.")

    def validate_manager_insights(self, insights: ManagerInsights):
        if insights.total_learners < 0:
            self._log("GR-43", "FAIL", "Manager total learner count is invalid.")
            raise GuardrailException("Manager total learner count is invalid.")
        if not (0 <= insights.average_readiness <= 100):
            self._log("GR-44", "FAIL", "Manager average readiness is out of bounds.")
            raise GuardrailException("Manager average readiness is out of bounds.")
        for exam, score in insights.readiness_by_exam.items():
            if exam not in self.valid_certs or not (0 <= score <= 100):
                self._log("GR-45", "FAIL", "Manager readiness-by-exam entry is invalid.")
                raise GuardrailException("Manager readiness-by-exam entry is invalid.")
        for risk in insights.at_risk_learners:
            self._assert_no_pii(risk.name, "GR-46", "manager insights")
            self._assert_no_pii(risk.reason, "GR-46", "manager insights")
            if risk.risk_level not in {"Low", "Medium", "High"}:
                self._log("GR-47", "FAIL", "Risk level is invalid.")
                raise GuardrailException("Risk level is invalid.")
        for comment in insights.learner_comments:
            self._assert_no_pii(comment.name, "GR-48", "worker learning comments")
            self._assert_no_pii(comment.comment, "GR-48", "worker learning comments")
            if comment.missed_count >= 3 and not comment.penalty_applied:
                self._log("GR-49", "FAIL", "Three-miss penalty was not applied.")
                raise GuardrailException("Three-miss penalty must be applied.")
        self._log("GR-43", "PASS", "Manager total learner count validated.")
        self._log("GR-44", "PASS", "Manager average readiness bounds validated.")
        self._log("GR-45", "PASS", "Manager readiness-by-exam entries validated.")
        self._log("GR-46", "PASS", "Manager risk privacy validated.")
        self._log("GR-47", "PASS", "Manager risk level categories validated.")
        self._log("GR-48", "PASS", "Worker learning comment privacy validated.")
        self._log("GR-49", "PASS", "Three-miss penalty policy validated.")

    def validate_buddy_match(self, matches: List[Any]):
        for m in matches:
            if not m.certification_target:
                raise GuardrailException("Buddy match missing target certification.")
            if m.certification_target not in self.valid_certs:
                raise GuardrailException("Buddy match certification target is unsupported.")
            if m.learner_a_id == m.learner_b_id:
                raise GuardrailException("Buddy match cannot pair a learner with themself.")
        self._log("GR-50", "PASS", "Peer collaboration pairings validated.")

    def audit_final_output(self, content: str):
        self._assert_no_pii(content, "GR-51", "final output")
        self._log("GR-51", "PASS", "Final output safety scan completed.")
        return content
