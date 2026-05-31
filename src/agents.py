import os
import json
import random
import re
from typing import Dict, Any, List, Tuple
from src.config import (
    LearnerProfile, StudyPlan, Quiz, QuizQuestion, ReadinessReport,
    ManagerInsights, BuddyMatch, RiskAssessment, LearningActivityRecord,
    LearningActivityReport, FORCE_MOCK_MODE,
    AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION,
    schema_safe_dict, SYNTHETIC_DIR
)
from src.iq_integration import FoundryIQ, FabricIQ, WorkIQ
from src.guardrails import GuardrailsPipeline, GuardrailException
from src.scheduling import generate_workload_aware_schedule

# Optional Azure AI Imports
try:
    from openai import AzureOpenAI
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
except ImportError:
    AzureOpenAI = None
    AIProjectClient = None
    DefaultAzureCredential = None

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.reasoning_traces = []

    def log_reasoning(self, step: str):
        self.reasoning_traces.append(f"[{self.name}] {step}")

    def get_traces(self) -> List[str]:
        return self.reasoning_traces

    def clear_traces(self):
        self.reasoning_traces = []

class LearnerProfilerAgent(BaseAgent):
    """
    Agent 1: LearnerProfilerAgent
    Converts inputs into a structured LearnerProfile.
    Implements a 3-tier fallback chain (Foundry SDK -> OpenAI JSON Mode -> Local Mock).
    """
    def __init__(self):
        super().__init__(
            "LearnerProfilerAgent",
            "Profiling",
            "Convert user background context and exam requests into a structured LearnerProfile."
        )

    def _profile_schema_prompt(self, text_input: str, employee_id: str, target_cert: str, work_signals: Dict[str, Any]) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You convert certification-prep learner text into strict JSON only. "
                    "Use synthetic-safe fields. Do not invent real emails, phone numbers, or private data. "
                    "Return keys: learner_id, employee_id, name, role, certification_target, "
                    "practice_score_avg, hours_studied, exam_outcome, status."
                )
            },
            {
                "role": "user",
                "content": json.dumps({
                    "text_input": text_input,
                    "employee_id": employee_id,
                    "target_certification": target_cert,
                    "work_signals": work_signals
                })
            }
        ]

    def _normalize_profile_data(self, raw: Dict[str, Any], employee_id: str, target_cert: str) -> Dict[str, Any]:
        def _safe_float(value: Any, default: float) -> float:
            if value is None or value == "":
                return default
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        seeded_profile = None
        learners_path = os.path.join(SYNTHETIC_DIR, "learners.json")
        if os.path.exists(learners_path):
            with open(learners_path, "r", encoding="utf-8") as f:
                for learner in json.load(f):
                    if learner["employee_id"] == employee_id or learner["learner_id"] == employee_id:
                        seeded_profile = learner
                        break

        default_name = seeded_profile.get("name") if seeded_profile else "Candidate Employee"
        default_role = seeded_profile.get("role") if seeded_profile else "Software Engineer"
        default_exam_outcome = seeded_profile.get("exam_outcome") if seeded_profile else "None"
        default_status = seeded_profile.get("status") if seeded_profile else "IN PROGRESS"

        name = str(default_name if seeded_profile else raw.get("name") or default_name).strip()[:80]
        role = str(default_role if seeded_profile else raw.get("role") or default_role).strip()[:80]
        learner_id = (
            seeded_profile["learner_id"]
            if seeded_profile
            else str(raw.get("learner_id") or f"L-{random.randint(1009, 9999)}").strip()[:32]
        )
        return {
            "learner_id": learner_id,
            "employee_id": seeded_profile["employee_id"] if seeded_profile else employee_id,
            "name": name,
            "role": role,
            "certification_target": target_cert,
            "practice_score_avg": (
                seeded_profile["practice_score_avg"]
                if seeded_profile
                else _safe_float(raw.get("practice_score_avg"), 50.0)
            ),
            "hours_studied": (
                seeded_profile["hours_studied"]
                if seeded_profile
                else _safe_float(raw.get("hours_studied"), 0.0)
            ),
            "exam_outcome": str(default_exam_outcome if seeded_profile else raw.get("exam_outcome") or default_exam_outcome),
            "status": str(default_status if seeded_profile else raw.get("status") or default_status)
        }

    def _call_chat_json(self, client, text_input: str, employee_id: str, target_cert: str, work_signals: Dict[str, Any]) -> Dict[str, Any]:
        response = client.chat.completions.create(
            model=AZURE_AI_MODEL_DEPLOYMENT,
            messages=self._profile_schema_prompt(text_input, employee_id, target_cert, work_signals),
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def execute(self, text_input: str, employee_id: str, work_iq: WorkIQ, fabric_iq: FabricIQ) -> LearnerProfile:
        self.clear_traces()
        self.log_reasoning("Parsing profiling input...")
        
        # Merge calendar signals from Work IQ
        work_signals = work_iq.get_signals_by_employee(employee_id)
        self.log_reasoning(f"Retrieved Work IQ signals for {employee_id}: meetings={work_signals.get('meeting_hours_per_week')}h, focus={work_signals.get('focus_hours_per_week')}h.")

        # Determine target cert using Fabric IQ
        profile_lower = text_input.lower()
        target_cert = "AZ-204"  # Default
        cert_patterns = [
            "AI-102", "AZ-204", "AZ-400", "AZ-900", "AI-900", "DP-900",
            "SC-900", "PL-900", "MS-900", "MB-910", "AZ-104", "AZ-305",
            "DP-203", "PL-200", "PL-300", "SC-300", "MS-102", "AZ-500"
        ]
        for cert_id in cert_patterns:
            if cert_id.lower() in profile_lower or cert_id.replace("-", "").lower() in profile_lower:
                target_cert = cert_id
                break
        else:
            if "security" in profile_lower:
                target_cert = "SC-900"
            elif "power bi" in profile_lower or "analytics" in profile_lower:
                target_cert = "PL-300"
            elif "power platform" in profile_lower or "automation" in profile_lower:
                target_cert = "PL-900"
            elif "data engineer" in profile_lower:
                target_cert = "DP-203"
            elif "data" in profile_lower:
                target_cert = "DP-900"
            elif "microsoft 365" in profile_lower or "workplace" in profile_lower:
                target_cert = "MS-900"
            elif "dynamics" in profile_lower or "sales" in profile_lower:
                target_cert = "MB-910"
            elif "architect" in profile_lower:
                target_cert = "AZ-305"
            elif "admin" in profile_lower or "operations" in profile_lower:
                target_cert = "AZ-104"
            elif "ai" in profile_lower:
                target_cert = "AI-900"
            elif "devops" in profile_lower:
                target_cert = "AZ-400"
            
        self.log_reasoning(f"Fabric IQ mapped input target certification: {target_cert}")

        # 3-Tier Fallback Chain implementation
        profile_data = None
        
        # Tier 1: Try Azure AI Foundry Projects SDK.
        if not FORCE_MOCK_MODE and AZURE_AI_PROJECT_ENDPOINT and AIProjectClient is not None and DefaultAzureCredential is not None:
            self.log_reasoning("Tier 1: Querying Azure AI Foundry project client...")
            try:
                project = AIProjectClient(
                    endpoint=AZURE_AI_PROJECT_ENDPOINT,
                    credential=DefaultAzureCredential()
                )
                client = project.get_openai_client()
                raw_profile = self._call_chat_json(client, text_input, employee_id, target_cert, work_signals)
                profile_data = self._normalize_profile_data(raw_profile, employee_id, target_cert)
                self.log_reasoning("Tier 1: Successfully profiled via Azure AI Foundry project client.")
            except Exception as e:
                self.log_reasoning(f"Tier 1: Failed. Error: {e}. Falling back to Tier 2...")

        # Tier 2: Try Direct Azure OpenAI JSON Mode
        if profile_data is None and not FORCE_MOCK_MODE and AzureOpenAI is not None and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
            self.log_reasoning("Tier 2: Querying Azure OpenAI model directly with JSON schema...")
            try:
                client = AzureOpenAI(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version=AZURE_OPENAI_API_VERSION
                )
                raw_profile = self._call_chat_json(client, text_input, employee_id, target_cert, work_signals)
                profile_data = self._normalize_profile_data(raw_profile, employee_id, target_cert)
                self.log_reasoning("Tier 2: Successfully profiled via Azure OpenAI JSON Mode.")
            except Exception as e:
                self.log_reasoning(f"Tier 2: Failed. Error: {e}. Falling back to Tier 3...")
        elif profile_data is None and not FORCE_MOCK_MODE:
            self.log_reasoning("Tier 2: Skipped. AZURE_OPENAI_ENDPOINT/API_KEY are not configured.")

        # Tier 3: Deterministic Rule-Based Fallback
        if profile_data is None:
            self.log_reasoning("Tier 3: Running rule-based deterministic parsing engine...")
            
            # Match existing learners in learners.json if any
            learners_path = os.path.join(SYNTHETIC_DIR, "learners.json")
            matched_learner = None
            if os.path.exists(learners_path):
                with open(learners_path, "r", encoding="utf-8") as f:
                    learners = json.load(f)
                    for l in learners:
                        if l["employee_id"] == employee_id or l["learner_id"] == employee_id:
                            matched_learner = l
                            break
                            
            if matched_learner:
                self.log_reasoning(f"Tier 3: Found pre-seeded profile for {matched_learner.get('name')}.")
                profile_data = {
                    "learner_id": matched_learner["learner_id"],
                    "employee_id": matched_learner["employee_id"],
                    "name": matched_learner["name"],
                    "role": matched_learner["role"],
                    "certification_target": target_cert,
                    "practice_score_avg": matched_learner["practice_score_avg"],
                    "hours_studied": matched_learner["hours_studied"],
                    "exam_outcome": matched_learner["exam_outcome"],
                    "status": matched_learner["status"]
                }
            else:
                self.log_reasoning("Tier 3: Generating new synthetic profile from input clues.")
                name = "Candidate Employee"
                name_match = re.search(r'(?:i am|name is|my name is)\s+([A-Za-z\s]+)', text_input, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                profile_data = {
                    "learner_id": f"L-{random.randint(1009, 9999)}",
                    "employee_id": employee_id,
                    "name": name,
                    "role": "Software Engineer",
                    "certification_target": target_cert,
                    "practice_score_avg": 50.0,
                    "hours_studied": 0.0,
                    "exam_outcome": "None",
                    "status": "NOT YET"
                }
                
        # Merge Work IQ signals without letting connector metadata overwrite profile identity.
        safe_work_signals = work_signals.copy()
        safe_work_signals.pop("employee_id", None)
        profile_data.update(safe_work_signals)
        self.log_reasoning("Profile creation successfully finalized.")
        return LearnerProfile(**profile_data)

class LearningPathCuratorAgent(BaseAgent):
    """
    Agent 2: LearningPathCuratorAgent
    Maps exam domains to curated resource links from MS Learn.
    Grounded in Foundry IQ.
    """
    def __init__(self):
        super().__init__(
            "LearningPathCuratorAgent",
            "Content Curation",
            "Cure learning modules and map them to certification domains with citations."
        )

    def execute(self, profile: LearnerProfile, foundry_iq: FoundryIQ, fabric_iq: FabricIQ) -> List[Dict[str, Any]]:
        self.clear_traces()
        self.log_reasoning(f"Curating study resources for cert: {profile.certification_target}...")
        
        # Load domains from Fabric IQ
        cert = fabric_iq.get_certification(profile.certification_target)
        if not cert:
            self.log_reasoning("Error: Cert metadata not found.")
            return []

        curated_paths = []
        for d in cert.get("domains", []):
            self.log_reasoning(f"Searching Foundry IQ for domain: {d['name']}...")
            search_res = foundry_iq.search_knowledge(d["name"], profile.certification_target)
            
            citation = "Grounded Link"
            resource_url = "https://learn.microsoft.com/en-us/credentials/certifications/"
            registry_resource = fabric_iq.get_learning_resource(profile.certification_target, d["name"])
            resource_url = registry_resource.get("learn_path_url", resource_url)
            resource_title = registry_resource.get("resource_title", f"{profile.certification_target} Microsoft Learn course")
            
            # Parse link and key citation from guides
            if search_res:
                block = search_res[0]["text"]
                citation = search_res[0]["citation"]
                # Keep the named course/path from the local registry. Older guide links are used only
                # when the registry has no specific course URL for this domain.
                url_match = re.search(r'\[.*\]\((https://learn\.microsoft\.com/[^\)]+)\)', block)
                if url_match and not registry_resource.get("resource_title"):
                    resource_url = url_match.group(1)
                    
            curated_paths.append({
                "domain_name": d["name"],
                "resource_title": resource_title,
                "resource_url": resource_url,
                "certification_url": registry_resource.get("certification_url", "https://learn.microsoft.com/en-us/credentials/certifications/"),
                "skills_covered": d["skills"],
                "citation": citation
            })
            self.log_reasoning(f"Mapped {d['name']} to course: {resource_title} ({resource_url}) with citation: {citation}")
            
        return curated_paths

class StudyPlanAgent(BaseAgent):
    """
    Agent 3: StudyPlanAgent
    Allocates hours to domains using the Workload-Aware Largest Remainder algorithm.
    """
    def __init__(self):
        super().__init__(
            "StudyPlanAgent",
            "Scheduling",
            "Create a personalized capacity-aware Gantt study schedule."
        )

    def execute(self, profile: LearnerProfile, cert_data: Dict[str, Any], weeks: int = 4) -> StudyPlan:
        self.clear_traces()
        self.log_reasoning(f"Running Largest Remainder algorithm for {profile.name} (budget={profile.weekly_study_budget_hours}h/wk)...")
        plan = generate_workload_aware_schedule(profile, cert_data, weeks)
        self.log_reasoning(f"Generated {plan.total_weeks}-week study plan with total study time: {plan.total_hours} hours.")
        for week in plan.schedule:
            if week.workload_adjusted:
                self.log_reasoning(f"Week {week.week_number} adjusted: {week.adjustment_reason}")
        return plan

class EngagementAgent(BaseAgent):
    """
    Agent 4: EngagementAgent
    Recommends reminders and focus windows based on Work IQ.
    """
    def __init__(self):
        super().__init__(
            "EngagementAgent",
            "User Engagement",
            "Keep user engaged and suggest focus study windows."
        )

    def execute(self, profile: LearnerProfile, plan: StudyPlan) -> Dict[str, Any]:
        self.clear_traces()
        self.log_reasoning(f"Formulating study reminder strategy based on focus slot: {profile.preferred_learning_slot}...")
        
        reminder_msg = ""
        study_slot = "9:00 AM - 10:00 AM" if profile.preferred_learning_slot == "Morning" else "3:00 PM - 4:00 PM"
        
        if profile.meeting_hours_per_week > 22:
            reminder_msg = f"Hey {profile.name}, we noticed a meeting-heavy schedule this week. Let's tackle a quick 20-min learning flashcard during your focus block at {study_slot} to avoid fatigue."
            self.log_reasoning("High meeting warning reminder triggered.")
        else:
            reminder_msg = f"Hi {profile.name}! It's a great week for studying. We've set aside your dedicated block at {study_slot} for {profile.certification_target} practice."
            self.log_reasoning("Standard reminder generated.")
            
        return {
            "learner_id": profile.learner_id,
            "preferred_slot": profile.preferred_learning_slot,
            "recommended_time": study_slot,
            "reminder_message": reminder_msg
        }

class AssessmentAgent(BaseAgent):
    """
    Agent 5: AssessmentAgent
    Generates domain-proportional quiz questions based on guides. Grounded in Foundry IQ.
    """
    def __init__(self):
        super().__init__(
            "AssessmentAgent",
            "Quiz Assessment",
            "Generate grounded practice questions based on certification guides."
        )

    def _extract_question_blocks(self, block: str) -> List[Dict[str, Any]]:
        pattern = re.compile(
            r'-\s*\*\*Question:\*\*\s*(?P<question>.+?)\n'
            r'-\s*\*\*Options:\*\*\s*\n'
            r'\s*1\.\s*(?P<o1>.+?)\n'
            r'\s*2\.\s*(?P<o2>.+?)\n'
            r'\s*3\.\s*(?P<o3>.+?)\n'
            r'\s*4\.\s*(?P<o4>.+?)\n'
            r'-\s*\*\*Correct Answer:\*\*\s*(?P<answer>\d)\n'
            r'-\s*\*\*Explanation:\*\*\s*(?P<explanation>.+?)(?=\n###|\n---|\Z)',
            re.DOTALL
        )
        questions = []
        for match in pattern.finditer(block):
            questions.append({
                "question_text": match.group("question").strip(),
                "options": [
                    match.group("o1").strip(),
                    match.group("o2").strip(),
                    match.group("o3").strip(),
                    match.group("o4").strip(),
                ],
                "correct_option_index": int(match.group("answer")) - 1,
                "explanation": " ".join(match.group("explanation").strip().split())
            })
        return questions

    def execute(self, profile: LearnerProfile, foundry_iq: FoundryIQ, fabric_iq: FabricIQ) -> Quiz:
        self.clear_traces()
        self.log_reasoning(f"Retrieving practice questions for target: {profile.certification_target}...")
        
        cert = fabric_iq.get_certification(profile.certification_target)
        if not cert:
            raise ValueError(f"Certification {profile.certification_target} not found in ontology.")

        domains = cert.get("domains", [])
        quiz_questions = []
        q_id = 1
        
        max_questions = 10
        for d in domains:
            if len(quiz_questions) >= max_questions:
                break
            self.log_reasoning(f"Searching index for practice question on domain: {d['name']}...")
            search_res = foundry_iq.search_knowledge(d["name"], profile.certification_target)
            
            # Defaults
            q_text = f"Review the key objectives for {d['name']}. What is the recommended deployment pattern?"
            options = ["Blue-Green Swap", "Canary Rollout", "Direct Hotfix", "Multi-Region Hub"]
            correct_idx = 1
            citation = f"[{profile.certification_target.replace('-', '')}-D-GEN]"
            explanation = f"Always review safety guides. [Citation: {citation}]"
            
            # If questions are pre-seeded in the guide, extract them
            if search_res:
                block = search_res[0]["text"]
                citation = search_res[0]["citation"]
                extracted = self._extract_question_blocks(block)
                for item in extracted:
                    if len(quiz_questions) >= max_questions:
                        break
                    quiz_questions.append(
                        QuizQuestion(
                            question_id=q_id,
                            domain=d["name"],
                            question_text=item["question_text"],
                            options=item["options"],
                            correct_option_index=item["correct_option_index"],
                            citation=citation,
                            explanation=item["explanation"]
                        )
                    )
                    self.log_reasoning(f"Grounded question {q_id} generated with citation: {citation}")
                    q_id += 1
                if extracted:
                    continue

            quiz_questions.append(
                QuizQuestion(
                    question_id=q_id,
                    domain=d["name"],
                    question_text=q_text,
                    options=options,
                    correct_option_index=correct_idx,
                    citation=citation,
                    explanation=explanation
                )
            )
            q_id += 1
            self.log_reasoning(f"Grounded question {q_id-1} generated with citation: {citation}")
            
        return Quiz(
            quiz_id=f"Q-{random.randint(100, 999)}",
            learner_id=profile.learner_id,
            certification_target=profile.certification_target,
            questions=quiz_questions
        )

class ProgressAgent(BaseAgent):
    """
    Agent 6: ProgressAgent
    Calculates Reazon's WorkIQ-aware readiness score:
    0.45 * exam domain mastery + 0.25 * latest assessment + 0.15 * study hours + 0.15 * workload fit.
    """
    def __init__(self):
        super().__init__(
            "ProgressAgent",
            "Readiness Tracking",
            "Compute exact readiness scores using certification weights."
        )

    def execute(self, profile: LearnerProfile, quiz_score: float, cert_data: Dict[str, Any]) -> ReadinessReport:
        self.clear_traces()
        self.log_reasoning(f"Calculating exam-weighted readiness score for {profile.name}...")
        
        # 1. Domain Rating (average rating of domains)
        # We simulate the user's rating across the domains based on their past practice history
        # (For this mock calculation, we map it around their profile practice score)
        domains = cert_data.get("domains", [])
        domain_scores = {}
        total_weighted_domain_score = 0.0
        
        # Simulate slight differences in domain readiness
        random.seed(profile.name)
        for i, d in enumerate(domains):
            # Scale slightly around the learner's average practice score
            variance = random.uniform(-10.0, 10.0)
            score = max(30.0, min(100.0, profile.practice_score_avg + variance))
            domain_scores[d["name"]] = round(score, 1)
            total_weighted_domain_score += (score * d["weight"])
            
        self.log_reasoning(f"Ontology domain weights applied. Weighted domain average: {round(total_weighted_domain_score, 2)}%.")
        
        # 2. Hours utilization (cap at 100%)
        recommended_hours = cert_data.get("recommended_hours", 20)
        hours_util = min(100.0, (profile.hours_studied / recommended_hours) * 100.0)
        self.log_reasoning(f"Hours utilization: {profile.hours_studied}/{recommended_hours} hours ({round(hours_util, 1)}%).")

        # 3. Latest assessment score
        self.log_reasoning(f"Recent mock assessment score: {quiz_score}%.")

        # 4. Workload fit from Work IQ signals. Learners with enough focus time and fewer
        # meeting-heavy weeks get a higher execution-confidence contribution.
        focus_capacity = min(100.0, (profile.focus_hours_per_week / max(1, profile.weekly_study_budget_hours)) * 100.0)
        meeting_penalty = max(0, profile.meeting_hours_per_week - 22) * 2.0
        workload_fit = round(max(40.0, min(100.0, focus_capacity - meeting_penalty)), 1)
        self.log_reasoning(
            f"Workload fit: {workload_fit}% from focus={profile.focus_hours_per_week}h, meetings={profile.meeting_hours_per_week}h."
        )

        # Reazon readiness formula:
        # 0.45 * Exam Domain Mastery + 0.25 * Latest Assessment
        # + 0.15 * Study Hours Utilization + 0.15 * Workload Fit
        overall = (
            (0.45 * total_weighted_domain_score)
            + (0.25 * quiz_score)
            + (0.15 * hours_util)
            + (0.15 * workload_fit)
        )
        overall = round(overall, 1)
        self.log_reasoning(
            "Overall readiness score: "
            f"{overall}% (Formula: 0.45*Domain + 0.25*Assessment + 0.15*Hours + 0.15*Workload Fit)."
        )

        return ReadinessReport(
            learner_id=profile.learner_id,
            certification_target=profile.certification_target,
            domain_scores=domain_scores,
            hours_utilization=hours_util,
            workload_fit=workload_fit,
            practice_score_avg=profile.practice_score_avg,
            overall_readiness=overall,
            booking_recommendation="NOT YET",  # Determined by Recommender
            remediation_plan=""
        )

class BookingRecommenderAgent(BaseAgent):
    """
    Agent 7: BookingRecommenderAgent
    Issues final GO / CONDITIONAL GO / NOT YET booking recommendation.
    """
    def __init__(self):
        super().__init__(
            "BookingRecommenderAgent",
            "Exam Booking Recommendation",
            "Determine exam booking readiness and formulate remediation plan."
        )

    def execute(self, report: ReadinessReport, cert_data: Dict[str, Any]) -> ReadinessReport:
        self.clear_traces()
        self.log_reasoning("Analyzing readiness report thresholds...")
        
        score = report.overall_readiness
        rec = "NOT YET"
        plan = ""
        
        # Find weakest domain
        weakest_domain = min(report.domain_scores, key=report.domain_scores.get)
        weakest_score = report.domain_scores[weakest_domain]
        
        if score >= 75.0:
            rec = "GO"
            plan = f"Ready for bookings! Keep reviewing concepts. Focus on maintaining high marks on your weakest domain '{weakest_domain}' ({weakest_score}%)."
            self.log_reasoning("Booking readiness: GO issued.")
        elif score >= 65.0:
            rec = "CONDITIONAL GO"
            plan = f"Conditional Go! You may book the exam but we recommend completing a 2-hour remediation module specifically for your weakest area: '{weakest_domain}' ({weakest_score}%)."
            self.log_reasoning("Booking readiness: CONDITIONAL GO issued.")
        else:
            rec = "NOT YET"
            plan = f"Booking not recommended yet. Please focus study efforts on '{weakest_domain}' ({weakest_score}%) and retake the practice assessment."
            self.log_reasoning("Booking readiness: NOT YET issued. Remediation study plan loop scheduled.")

        report.booking_recommendation = rec
        report.remediation_plan = plan
        return report

class LearningActivityVerifierAgent(BaseAgent):
    """
    Agent 8: LearningActivityVerifierAgent
    Verifies whether planned learning was actually completed using Microsoft Learn/LMS/Teams-style evidence.
    """
    def __init__(self):
        super().__init__(
            "LearningActivityVerifierAgent",
            "Learning Evidence Verification",
            "Calculate learning completion confidence from attendance, module progress, checkpoints, and reflections."
        )

    def _confidence_for_record(self, record: LearningActivityRecord) -> float:
        attendance_ratio = min(1.0, record.attendance_minutes / max(1, record.expected_minutes))
        attendance_score = attendance_ratio * 25.0
        module_score = 35.0 if record.status.lower() == "completed" else min(35.0, (record.watch_percentage / 100.0) * 35.0)
        checkpoint_score = min(30.0, (record.checkpoint_score / 100.0) * 30.0)
        reflection_score = 10.0 if record.reflection_submitted else 0.0
        return round(attendance_score + module_score + checkpoint_score + reflection_score, 1)

    def execute(
        self,
        profile: LearnerProfile,
        plan: StudyPlan,
        activity_records: List[LearningActivityRecord]
    ) -> LearningActivityReport:
        self.clear_traces()
        self.log_reasoning(f"Verifying learning activity evidence for {profile.name}...")

        planned_domains = []
        for week in plan.schedule:
            for focus in week.focus_domains:
                planned_domains.append(focus.split(" (")[0])

        relevant = [
            r for r in activity_records
            if r.learner_id == profile.learner_id and r.certification_target == profile.certification_target
        ]

        confidence_by_domain = {}
        evidence_summary = []
        for record in relevant:
            confidence = self._confidence_for_record(record)
            confidence_by_domain[record.domain_name] = max(confidence_by_domain.get(record.domain_name, 0.0), confidence)
            evidence_summary.append(
                f"{record.domain_name}: {confidence}% confidence from {record.source} "
                f"(status={record.status}, checkpoint={record.checkpoint_score}%)."
            )
            self.log_reasoning(evidence_summary[-1])

        total_modules = max(1, len(set(planned_domains)))
        completed_modules = sum(1 for domain in set(planned_domains) if confidence_by_domain.get(domain, 0.0) >= 70.0)
        confidences = [confidence_by_domain.get(domain, 0.0) for domain in set(planned_domains)]
        average_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0
        weak_domains = [domain for domain in set(planned_domains) if confidence_by_domain.get(domain, 0.0) < 70.0]

        if not relevant:
            recommendation = "No external learning evidence found yet. Ask learner to complete a checkpoint or sync Microsoft Learn/LMS activity."
            evidence_summary.append("No activity records found for this learner and certification.")
        elif weak_domains:
            recommendation = f"Reinforce {weak_domains[0]} before final exam; completion evidence is below 70% confidence."
        else:
            recommendation = "Learning evidence is strong enough to continue toward final exam readiness."

        self.log_reasoning(
            f"Completion confidence average={average_confidence}%, completed={completed_modules}/{total_modules} modules."
        )

        return LearningActivityReport(
            learner_id=profile.learner_id,
            certification_target=profile.certification_target,
            completed_modules=completed_modules,
            total_modules=total_modules,
            average_completion_confidence=average_confidence,
            weak_domains=weak_domains,
            evidence_summary=evidence_summary,
            recommendation=recommendation
        )

class ManagerInsightsAgent(BaseAgent):
    """
    Agent 9: ManagerInsightsAgent
    Aggregates metrics, displays risk heatmaps, and tracks completion patterns.
    """
    def __init__(self):
        super().__init__(
            "ManagerInsightsAgent",
            "Managerial Dashboards",
            "Aggregate team performance and identify calendar burnout risks."
        )

    def execute(
        self,
        profiles: List[LearnerProfile],
        readiness_reports: List[ReadinessReport],
        work_iq: WorkIQ
    ) -> ManagerInsights:
        self.clear_traces()
        self.log_reasoning("Generating manager insights summary...")
        
        total_learners = len(profiles)
        if total_learners == 0:
            return ManagerInsights(
                total_learners=0,
                average_readiness=0.0,
                readiness_by_exam={},
                at_risk_learners=[],
                buddy_recommendations=[]
            )

        # Average readiness
        avg_ready = sum(r.overall_readiness for r in readiness_reports) / len(readiness_reports)
        avg_ready = round(avg_ready, 1)
        self.log_reasoning(f"Calculated average team readiness score: {avg_ready}%.")

        # Readiness by exam
        exam_sums = {}
        exam_counts = {}
        for r in readiness_reports:
            exam = r.certification_target
            exam_sums[exam] = exam_sums.get(exam, 0.0) + r.overall_readiness
            exam_counts[exam] = exam_counts.get(exam, 0) + 1
            
        readiness_by_exam = {e: round(exam_sums[e] / exam_counts[e], 1) for e in exam_sums}
        self.log_reasoning("Aggregated readiness averages per certification track.")

        # At risk learners (meeting hours > 22)
        at_risk = []
        for p in profiles:
            risk_tier, reason = work_iq.evaluate_burnout_risk(p.employee_id)
            if risk_tier in ["High", "Medium"]:
                at_risk.append(
                    RiskAssessment(
                        learner_id=p.learner_id,
                        name=p.name,  # Manager insights must not contain personal emails, names are fine but emails are scrubbed
                        meeting_hours=p.meeting_hours_per_week,
                        risk_level=risk_tier,
                        reason=reason
                    )
                )
        self.log_reasoning(f"Identified {len(at_risk)} learners at risk of workload burnout.")

        # Buddy recommendations (completed by Peer Collaboration agent)
        return ManagerInsights(
            total_learners=total_learners,
            average_readiness=avg_ready,
            readiness_by_exam=readiness_by_exam,
            at_risk_learners=at_risk,
            buddy_recommendations=[]
        )

class PeerCollaborationAgent(BaseAgent):
    """
    Agent 10: PeerCollaborationAgent
    Matches learners with shared certifications and compatible calendars.
    """
    def __init__(self):
        super().__init__(
            "PeerCollaborationAgent",
            "Peer Matching",
            "Recommends team study buddy pairings for shared targets."
        )

    def execute(self, profiles: List[LearnerProfile]) -> List[BuddyMatch]:
        self.clear_traces()
        self.log_reasoning("Scanning learner directory for buddy matching pairs...")
        
        matches = []
        matched_ids = set()
        
        # Match by shared cert and common preferred slot
        for i in range(len(profiles)):
            p1 = profiles[i]
            if p1.learner_id in matched_ids:
                continue
                
            for j in range(i + 1, len(profiles)):
                p2 = profiles[j]
                if p2.learner_id in matched_ids:
                    continue
                    
                if p1.certification_target == p2.certification_target:
                    # Same cert! Check slot overlap
                    if p1.preferred_learning_slot == p2.preferred_learning_slot:
                        matches.append(
                            BuddyMatch(
                                learner_a_id=p1.learner_id,
                                learner_a_name=p1.name,
                                learner_b_id=p2.learner_id,
                                learner_b_name=p2.name,
                                certification_target=p1.certification_target,
                                common_slot=p1.preferred_learning_slot
                            )
                        )
                        matched_ids.add(p1.learner_id)
                        matched_ids.add(p2.learner_id)
                        self.log_reasoning(f"Matched {p1.name} & {p2.name} for {p1.certification_target} ({p1.preferred_learning_slot}).")
                        break
                        
        return matches

class QualityCriticAgent(BaseAgent):
    """
    Agent 11: QualityCriticAgent
    Runs the Reazon guardrail policy at all agent boundaries.
    """
    def __init__(self):
        super().__init__(
            "QualityCriticAgent",
            "Quality Audit & Safety",
            "Run guardrail checks across all agent boundaries."
        )
        self.guardrails = GuardrailsPipeline()

    def audit_input(self, text: str) -> str:
        self.clear_traces()
        self.log_reasoning("Auditing user input...")
        res = self.guardrails.validate_profile_input(text)
        # Copy trace logs
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []
        return res

    def audit_profile(self, profile: LearnerProfile):
        self.clear_traces()
        self.log_reasoning("Auditing generated profile...")
        self.guardrails.validate_profile(profile)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_study_plan(self, plan: StudyPlan):
        self.clear_traces()
        self.log_reasoning("Auditing generated study plan...")
        self.guardrails.validate_study_plan(plan)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_quiz(self, quiz: Quiz):
        self.clear_traces()
        self.log_reasoning("Auditing generated assessment...")
        self.guardrails.validate_quiz(quiz)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_readiness(self, report: ReadinessReport):
        self.clear_traces()
        self.log_reasoning("Auditing readiness report calculations...")
        self.guardrails.validate_readiness_report(report)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_final_exam_result(self, result):
        self.clear_traces()
        self.log_reasoning("Auditing final exam badge unlock...")
        self.guardrails.validate_final_exam_result(result)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_learning_activity_report(self, report):
        self.clear_traces()
        self.log_reasoning("Auditing learning activity verification report...")
        self.guardrails.validate_learning_activity_report(report)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []

    def audit_manager_insights(self, insights: ManagerInsights):
        self.clear_traces()
        self.log_reasoning("Auditing manager dashboard aggregate metrics...")
        self.guardrails.validate_manager_insights(insights)
        for t in self.guardrails.traces:
            self.log_reasoning(f"[{t['rule_id']}] Status: {t['status']} - {t['message']}")
        self.guardrails.traces = []
