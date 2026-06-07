import sys
import os

# Adjust path to import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import OrchestratorEngine
from src.config import LearnerProfile, StudyPlan, Quiz, QuizQuestion, ReadinessReport, ManagerInsights, RiskAssessment
from src.guardrails import GuardrailException

def run_tests():
    print("==================================================")
    print("🧪 CERTPREP-EX SYSTEM BOUNDARY & PIPELINE TESTS")
    print("==================================================")
    
    engine = OrchestratorEngine()
    passed_tests = 0
    total_tests = 0

    def assert_test(name: str, condition: bool):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if condition:
            print(f"✅ PASS: {name}")
            passed_tests += 1
        else:
            print(f"❌ FAIL: {name}")

    # --- TEST 1: Pipeline execution & data integrity ---
    print("\n--- Test Suite 1: Learner Pipeline & Calculations ---")
    try:
        session = "verify_test_session"
        # Test Case A: Pre-seeded learner loading & signal merging
        profile, paths, plan, eng, quiz = engine.run_learner_pipeline(
            session,
            "I want to prepare for the AZ-104 developer exam.",
            "EMP-001"
        )
        assert_test("Profiler loaded pre-seeded name (Avery Stone)", profile.name == "Avery Stone")
        assert_test("Profiler mapped correct cert AZ-104", profile.certification_target == "AZ-104")
        assert_test("Profiler merged Work IQ meeting signals", profile.meeting_hours_per_week == 26)

        # Test Case B: Parsing brand new user profile
        new_profile, _, _, _, _ = engine.run_learner_pipeline(
            "new_session",
            "I want to prepare for the AI-200 exam. My name is Alex.",
            "EMP-999"
        )
        assert_test("Profiler mapped fresh user name (Alex)", new_profile.name == "Alex")
        assert_test("Profiler mapped correct cert AI-200 for new user", new_profile.certification_target == "AI-200")
        
        # Check Curation URL mapping
        assert_test("Curated modules mapping is non-empty", len(paths) > 0)
        assert_test("Curated modules contain MS Learn URLs", all("learn.microsoft.com" in p["resource_url"] for p in paths))
        
        # Check largest remainder hour distribution
        assert_test("Study Plan Gantt schedule generated", len(plan.schedule) == 4)
        assert_test("Plan total hours matches sum of weeks", sum(w.hours_allocated for w in plan.schedule) == plan.total_hours)
        
        # Check Work IQ workload adaptation
        week2_adjusted = plan.schedule[1].workload_adjusted
        assert_test("Work IQ automatically adjusted Week 2 budget due to high meetings", week2_adjusted)
        
        # Check Assessment questions
        assert_test("Quiz has 10 final exam questions", len(quiz.questions) == 10)
        assert_test("Quiz options contain 4 items per question", all(len(q.options) == 4 for q in quiz.questions))
        assert_test("Questions contain valid source citations", all(q.citation and "[Ref:" in q.citation for q in quiz.questions))
        
    except Exception as e:
        print(f"Exception raised in Test Suite 1: {e}")
        assert_test("Learner pipeline completed without errors", False)

    # --- TEST 2: Evaluation & Readiness Reporting ---
    print("\n--- Test Suite 2: Assessment Evaluation & Recommendations ---")
    try:
        # Score 80.0 -> Should trigger GO or CONDITIONAL GO depending on overall weights
        report = engine.run_assessment_evaluation(session, profile, quiz, 80.0)
        assert_test("Readiness report generated", report is not None)
        assert_test("Overall readiness calculated in [0, 100]", 0.0 <= report.overall_readiness <= 100.0)
        
        # Verify recommendation categories
        assert_test("Booking recommender returned valid category", report.booking_recommendation in ["GO", "CONDITIONAL GO", "NOT YET"])
        
        # Score 40.0 -> Should trigger NOT YET
        fail_report = engine.run_assessment_evaluation(session, profile, quiz, 40.0)
        assert_test("Low score triggers NOT YET booking status", fail_report.booking_recommendation == "NOT YET")
        assert_test("Low score remediation plan points to weakest domain", "remediation" in fail_report.remediation_plan.lower() or "focus" in fail_report.remediation_plan.lower())

        passed_final = engine.run_final_exam_evaluation(session, profile, quiz, 65.0)
        assert_test("Final exam score of 65 unlocks pass status", passed_final.passed)
        assert_test("Final exam pass unlocks a badge", passed_final.badge is not None)
        assert_test("Unlocked badge is tied to learner certification", passed_final.badge.certification_target == profile.certification_target)
        persisted_badges = engine.get_badges_by_learner(profile.learner_id)
        assert_test("Unlocked badge is persisted to badge store", any(b.badge_id == passed_final.badge.badge_id for b in persisted_badges))

        failed_final = engine.run_final_exam_evaluation(session, profile, quiz, 64.9)
        assert_test("Final exam score below 65 does not pass", not failed_final.passed)
        assert_test("Final exam failure does not unlock badge", failed_final.badge is None)
        
    except Exception as e:
        print(f"Exception raised in Test Suite 2: {e}")
        assert_test("Evaluation pipeline completed without errors", False)

    # --- TEST 3: Manager Dashboard Aggregation ---
    print("\n--- Test Suite 3: Manager Metrics & Peer Matching ---")
    try:
        # Load multiple synthetic profiles
        learners_list = []
        reports_list = []
        
        # Seed 3 profiles for manager aggregation
        p1 = LearnerProfile(
            learner_id="L-1", employee_id="EMP-001", name="Alex", role="Engineer",
            certification_target="AI-200", practice_score_avg=70, hours_studied=10,
            meeting_hours_per_week=26, focus_hours_per_week=8, preferred_learning_slot="Morning"
        )
        p2 = LearnerProfile(
            learner_id="L-2", employee_id="EMP-002", name="Blake", role="Engineer",
            certification_target="AI-200", practice_score_avg=85, hours_studied=20,
            meeting_hours_per_week=10, focus_hours_per_week=20, preferred_learning_slot="Morning"
        )
        p3 = LearnerProfile(
            learner_id="L-3", employee_id="EMP-003", name="Charlie", role="Engineer",
            certification_target="AZ-104", practice_score_avg=55, hours_studied=5,
            meeting_hours_per_week=15, focus_hours_per_week=15, preferred_learning_slot="Afternoon"
        )
        
        c_data_ai = engine.fabric_iq.get_certification("AI-200")
        c_data_az = engine.fabric_iq.get_certification("AZ-104")
        
        r1 = engine.progress.execute(p1, 75.0, c_data_ai)
        r2 = engine.progress.execute(p2, 90.0, c_data_ai)
        r3 = engine.progress.execute(p3, 60.0, c_data_az)
        
        insights = engine.run_manager_pipeline("manager_test", [p1, p2, p3], [r1, r2, r3])
        
        assert_test("Manager portal compiled 3 learners", insights.total_learners == 3)
        assert_test("Manager portal calculated team average", insights.average_readiness > 0)
        
        # Burnout risk check (EMP-001 has 26 meetings)
        assert_test("Burnout risk assessment flagged high meeting user", len(insights.at_risk_learners) > 0)
        assert_test("At risk learner name logged correctly", insights.at_risk_learners[0].name == "Alex")
        
        # Buddy Match check (p1 and p2 have same cert and slot)
        assert_test("Peer buddy recommendation matched Alex and Blake", len(insights.buddy_recommendations) == 1)
        assert_test("Buddy matches have correct target cert", insights.buddy_recommendations[0].certification_target == "AI-200")
        
    except Exception as e:
        print(f"Exception raised in Test Suite 3: {e}")
        assert_test("Manager pipeline completed without errors", False)

    # --- TEST 4: Boundary Guardrails ---
    print("\n--- Test Suite 4: Guardrail Rules & Boundary Exceptions ---")
    
    # 4a. PII Email scrubbing check
    scrubbed = engine.critic.audit_input("My name is test and email is hello@world.com")
    assert_test("Rule 1: Email PII scrubbed from raw input", "hello@world.com" not in scrubbed and "[SCRUBBED_EMAIL]" in scrubbed)
    
    # 4b. Input toxicity check
    try:
        engine.critic.audit_input("This platform is absolute shit!")
        assert_test("Rule 2: Toxicity check failed to catch offensive terms", False)
    except GuardrailException as ge:
        assert_test("Rule 2: Toxicity check correctly BLOCKED harmful input", "blocked" in str(ge).lower())
        
    # 4c. Budget study hours bounds check
    bad_profile = LearnerProfile(
        learner_id="L-BAD", employee_id="EMP-BAD", name="Bad", role="Tester",
        certification_target="AZ-104", practice_score_avg=50, hours_studied=10,
        weekly_study_budget_hours=50  # Over 40 limit!
    )
    try:
        engine.critic.audit_profile(bad_profile)
        assert_test("Rule 4: Hours budget failed to catch bounds violation", False)
    except GuardrailException as ge:
        assert_test("Rule 4: Hours budget correctly BLOCKED study hours over 40 limit", "weekly study budget" in str(ge).lower())

    # 4d. Citations check on Quiz
    bad_quiz = Quiz(
        quiz_id="Q-BAD", learner_id="L-1001", certification_target="AZ-104",
        questions=[
            QuizQuestion(
                question_id=1, domain="Develop compute", question_text="What?",
                options=["A", "B", "C", "D"], correct_option_index=0,
                citation="", explanation="No citations provided here."
            )
        ]
    )
    try:
        engine.critic.audit_quiz(bad_quiz)
        assert_test("Rule 9: Citations check failed to catch empty citations", False)
    except GuardrailException as ge:
        assert_test("Rule 9: Citations check correctly BLOCKED uncited quiz question", "citations" in str(ge).lower())

    # 4e. Anonymization check on Manager Dashboard
    bad_insights = ManagerInsights(
        total_learners=1, average_readiness=80.0, readiness_by_exam={},
        at_risk_learners=[
            RiskAssessment(
                learner_id="L-1", name="leak@secret.com", meeting_hours=28,
                risk_level="High", reason="Heavy workload"
            )
        ],
        buddy_recommendations=[]
    )
    try:
        engine.critic.audit_manager_insights(bad_insights)
        assert_test("Rule 16: Anonymization check failed to catch email leak", False)
    except GuardrailException as ge:
        assert_test("Rule 16: Anonymization check correctly BLOCKED email PII leak in manager insights", "unanonymized" in str(ge).lower())

    # Summary
    print("\n==================================================")
    print(f"📊 TEST RUN SUMMARY: {passed_tests} / {total_tests} PASSED")
    print("==================================================")
    
    if passed_tests == total_tests:
        print("🏆 ALL AGENT BOUNDARY CHECKS PASSED SUCCESSFULLY!")
        return True
    else:
        print("🚨 SOME AGENT BOUNDARY CHECKS FAILED!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
