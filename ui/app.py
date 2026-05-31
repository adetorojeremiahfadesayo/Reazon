import os
import sys
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import uuid

# Fix Python path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import OrchestratorEngine
from src.config import LearnerProfile, StudyPlan, Quiz, ReadinessReport, ManagerInsights, FinalExamResult, LearningActivityReport

# Initialize Streamlit Page Settings
st.set_page_config(
    page_title="Microsoft Startup Professional Exam Pack",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Vanilla CSS injection for modern dark-glassmorphism feel)
st.markdown("""
<style>
    /* Main Layout */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Title Banner */
    .banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #3b0764;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
    }
    .banner h1 {
        color: #f8fafc;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    .banner p {
        color: #94a3b8;
        margin: 8px 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Cards */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    .section-shell {
        background: rgba(15, 23, 42, 0.42);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 10px;
        padding: 18px;
        margin: 18px 0;
    }
    
    /* Stat Badge */
    .stat-val {
        font-size: 2rem;
        font-weight: 700;
        color: #818cf8;
        line-height: 1;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Booking Recommendations */
    .rec-go {
        color: #10b981;
        font-weight: bold;
        background: rgba(16, 185, 129, 0.15);
        padding: 4px 12px;
        border-radius: 9999px;
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: inline-block;
    }
    .rec-cond {
        color: #f59e0b;
        font-weight: bold;
        background: rgba(245, 158, 11, 0.15);
        padding: 4px 12px;
        border-radius: 9999px;
        border: 1px solid rgba(245, 158, 11, 0.3);
        display: inline-block;
    }
    .rec-notyet {
        color: #ef4444;
        font-weight: bold;
        background: rgba(239, 68, 68, 0.15);
        padding: 4px 12px;
        border-radius: 9999px;
        border: 1px solid rgba(239, 68, 68, 0.3);
        display: inline-block;
    }
    
    /* Trace Console styling */
    .trace-item {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        padding: 4px 8px;
        border-radius: 4px;
        margin-bottom: 2px;
    }
    .trace-curator { color: #f472b6; background: rgba(244, 114, 182, 0.05); }
    .trace-planner { color: #60a5fa; background: rgba(96, 165, 250, 0.05); }
    .trace-engagement { color: #fbbf24; background: rgba(251, 191, 36, 0.05); }
    .trace-assessment { color: #34d399; background: rgba(52, 211, 153, 0.05); }
    .trace-recommender { color: #a78bfa; background: rgba(167, 139, 250, 0.05); }
    .trace-critic { color: #f87171; background: rgba(248, 113, 113, 0.08); font-weight: bold; }
    .trace-other { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# Initialize Engine
@st.cache_resource
def get_engine():
    return OrchestratorEngine()

engine = get_engine()

# Helper to fetch active learners
def load_all_learners():
    path = os.path.join(engine.work_iq.work_signals_path)
    # We map data from learners.json
    learners_path = os.path.join(engine.fabric_iq.certifications_path.replace("certifications.json", "learners.json"))
    with open(learners_path, "r", encoding="utf-8") as f:
        return json.load(f)

learners = load_all_learners()

# Initialize Session States
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())[:8]
if "active_learner" not in st.session_state:
    st.session_state["active_learner"] = learners[0]["learner_id"]
if "quiz_active" not in st.session_state:
    st.session_state["quiz_active"] = None
if "user_answers" not in st.session_state:
    st.session_state["user_answers"] = {}
if "quiz_submitted" not in st.session_state:
    st.session_state["quiz_submitted"] = False
if "pipelines_run" not in st.session_state:
    st.session_state["pipelines_run"] = {}
if "final_exam_results" not in st.session_state:
    st.session_state["final_exam_results"] = {}

# Header Banner
st.markdown("""
<div class="banner">
    <h1>Microsoft Startup Professional Exam Pack</h1>
    <p>10-agent Microsoft certification readiness platform for startup teams</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - View Navigation & Configuration
st.sidebar.markdown("### 🛠️ Configuration Console")
view_mode = st.sidebar.radio(
    "Active Workspace Profile",
    ["Personal Learner Space", "Manager Insights Portal"]
)

# Active Learner selection (Shared across sidebars)
learner_options = {l["learner_id"]: f"{l['name']} ({l['role']})" for l in learners}
selected_learner_id = st.sidebar.selectbox(
    "Current Learner Persona",
    options=list(learner_options.keys()),
    format_func=lambda x: learner_options[x]
)

# Trigger reload if user changes persona
if selected_learner_id != st.session_state["active_learner"]:
    st.session_state["active_learner"] = selected_learner_id
    st.session_state["quiz_active"] = None
    st.session_state["user_answers"] = {}
    st.session_state["quiz_submitted"] = False

# Quick Environment Details in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌐 Intelligence Environment")
mock_toggle = st.sidebar.checkbox("FORCE MOCK MODE (Zero-Cred API)", value=True, disabled=True)
st.sidebar.caption("Mock mode runs the complete 10-agent pipeline locally in under 0.5s for 100% demo uptime.")

# Fetch active learner full info
active_learner_raw = next(l for l in learners if l["learner_id"] == st.session_state["active_learner"])
work_signals_raw = engine.work_iq.get_signals_by_employee(active_learner_raw["employee_id"])

# ----------------- VIEW 1: LEARNER SPACE -----------------
if view_mode == "Personal Learner Space":
    st.header(f"🧑‍💻 Learner Hub: {active_learner_raw['name']}")
    
    # 1. Profile Summary & Capacity Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{active_learner_raw['role']}</div>
            <div class="stat-label">Current Role</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{active_learner_raw['certification_target']}</div>
            <div class="stat-label">Certification Goal</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{work_signals_raw['meeting_hours_per_week']} hrs</div>
            <div class="stat-label">Weekly Meetings (Work IQ)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{work_signals_raw['weekly_study_budget_hours']} hrs</div>
            <div class="stat-label">Allocated Budget (Work IQ)</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Main Action: Generate & Run Pipeline
    if st.button("🚀 Execute Collaborative Agent Pipeline", type="primary"):
        with st.spinner("Orchestrating agents..."):
            text_prompt = f"I am {active_learner_raw['name']}, working as a {active_learner_raw['role']}. My target exam is {active_learner_raw['certification_target']}."
            # Run Orchestrator Pipeline
            profile, paths, plan, eng, quiz = engine.run_learner_pipeline(
                st.session_state["session_id"],
                text_prompt,
                active_learner_raw["employee_id"]
            )
            
            # Save results to session state
            st.session_state["pipelines_run"][st.session_state["active_learner"]] = {
                "profile": profile,
                "paths": paths,
                "plan": plan,
                "engagement": eng,
                "quiz": quiz
            }
            st.session_state["quiz_active"] = quiz
            st.session_state["user_answers"] = {}
            st.session_state["quiz_submitted"] = False
            st.session_state["final_exam_results"].pop(st.session_state["active_learner"], None)

    # Check if pipeline has been run
    pipeline_cache = st.session_state["pipelines_run"].get(st.session_state["active_learner"])

    if pipeline_cache:
        profile: LearnerProfile = pipeline_cache["profile"]
        paths = pipeline_cache["paths"]
        plan: StudyPlan = pipeline_cache["plan"]
        eng = pipeline_cache["engagement"]
        quiz: Quiz = pipeline_cache["quiz"]
        earned_badges = engine.get_badges_by_learner(profile.learner_id)
        activity_report: LearningActivityReport = engine.run_learning_activity_verification(
            st.session_state["session_id"],
            profile,
            plan
        )

        col_left, col_right = st.columns([2, 1])

        with col_left:
            # Plan Timeline (Gantt Chart representation)
            st.subheader("📅 Workload-Aware Gantt Schedule")
            
            gantt_data = []
            for w in plan.schedule:
                for d in w.focus_domains:
                    # Parse domain name and hours
                    d_clean = d.split(" (")[0]
                    d_hours = d.split(" (")[1].replace("h)", "")
                    gantt_data.append({
                        "Week": f"Week {w.week_number}",
                        "Domain": d_clean,
                        "Hours": int(d_hours),
                        "Workload Warning": w.adjustment_reason if w.workload_adjusted else "Standard Load"
                    })
            
            df_gantt = pd.DataFrame(gantt_data)
            fig_gantt = px.bar(
                df_gantt,
                x="Hours",
                y="Week",
                color="Domain",
                orientation="h",
                hover_data=["Workload Warning"],
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="Hours Distributed via Largest Remainder Algorithm"
            )
            fig_gantt.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0',
                height=300,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_gantt, use_container_width=True)

            # Show warning alerts if capacity adjusted
            for w in plan.schedule:
                if w.workload_adjusted:
                    st.warning(f"⚠️ **Week {w.week_number} Schedule Alert:** {w.adjustment_reason}")

            st.markdown("</div>", unsafe_allow_html=True)

            # Study Material Curation Table
            st.subheader("📚 Curated Learning Path & Grounded Citations")
            path_df = pd.DataFrame(paths)
            st.dataframe(
                path_df,
                column_config={
                    "domain_name": "Objective Domain",
                    "resource_url": st.column_config.LinkColumn("MS Learn Target URL"),
                    "skills_covered": "Skills List",
                    "citation": "Grounded Citation"
                },
                hide_index=True,
                use_container_width=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-shell'>", unsafe_allow_html=True)
            st.subheader("Learning Activity Verification")
            c_act1, c_act2, c_act3 = st.columns(3)
            with c_act1:
                st.metric("Completion Confidence", f"{activity_report.average_completion_confidence}%")
            with c_act2:
                st.metric("Completed Modules", f"{activity_report.completed_modules}/{activity_report.total_modules}")
            with c_act3:
                st.metric("Weak Domains", len(activity_report.weak_domains))
            st.info(activity_report.recommendation)
            if activity_report.evidence_summary:
                with st.expander("Evidence Signals", expanded=False):
                    for item in activity_report.evidence_summary:
                        st.write(f"- {item}")

            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            # Work IQ Engagement Card
            st.subheader("🔔 Engagement Agent Context")
            st.markdown(f"""
            <div class="glass-card">
                <h4>🎯 Dynamic Focus Window</h4>
                <p><strong>Suggested Study block:</strong> {eng['recommended_time']} ({eng['preferred_slot']})</p>
                <div style="background: rgba(96, 165, 250, 0.1); border-left: 4px solid #60a5fa; padding: 12px; border-radius: 4px; font-style: italic;">
                    "{eng['reminder_message']}"
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            if earned_badges:
                st.subheader("Earned Badges")
                for badge in earned_badges:
                    st.markdown(f"""
                    <div class="glass-card" style="border-color: rgba(16, 185, 129, 0.45);">
                        <div style="font-weight: 800; color: #34d399;">{badge.name}</div>
                        <div class="stat-label">Score: {badge.score}%</div>
                        <code>{badge.badge_id}</code>
                    </div>
                    """, unsafe_allow_html=True)

            # Final Exam section
            st.subheader("📝 Grounded Practice Assessment")
            
            if quiz:
                with st.form("quiz_form"):
                    st.write(f"**Final Exam ID:** `{quiz.quiz_id}`")
                    st.caption("Pass score: 65%. Passing unlocks the Microsoft Startup Professional badge for this certification.")
                    for q in quiz.questions:
                        st.write(f"**Q{q.question_id}:** {q.question_text}")
                        # Keep track of chosen options
                        user_sel = st.radio(
                            "Options:",
                            options=q.options,
                            key=f"q_{q.question_id}",
                            index=None
                        )
                        if user_sel:
                            st.session_state["user_answers"][q.question_id] = q.options.index(user_sel)
                        st.write("---")
                    
                    submit_quiz = st.form_submit_button("Submit Final Exam")
                    
                    if submit_quiz:
                        st.session_state["quiz_submitted"] = True

                # Display Results after Submission
                if st.session_state["quiz_submitted"]:
                    correct_count = 0
                    total_q = len(quiz.questions)
                    
                    st.markdown("### 📊 Scoring Audit")
                    for q in quiz.questions:
                        chosen_idx = st.session_state["user_answers"].get(q.question_id)
                        correct_idx = q.correct_option_index
                        
                        st.markdown(f"**Q{q.question_id}:** {q.question_text}")
                        if chosen_idx is not None:
                            st.write(f"Your Answer: *{q.options[chosen_idx]}*")
                        else:
                            st.write("Your Answer: *No Answer*")
                            
                        st.write(f"Correct Answer: *{q.options[correct_idx]}*")
                        
                        if chosen_idx == correct_idx:
                            correct_count += 1
                            st.markdown(f"✅ **Correct!** (Source: `{q.citation}`)")
                        else:
                            st.markdown(f"❌ **Incorrect.** (Source: `{q.citation}`)")
                            
                        # Bullet citation justification
                        st.info(f"💡 *Grounding Context:* {q.explanation}")
                        st.write("---")
                        
                    quiz_percentage = (correct_count / total_q) * 100.0
                    final_exam_result: FinalExamResult = engine.run_final_exam_evaluation(
                        st.session_state["session_id"],
                        profile,
                        quiz,
                        quiz_percentage
                    )
                    st.session_state["final_exam_results"][st.session_state["active_learner"]] = final_exam_result

                    if final_exam_result.passed:
                        st.success(f"Final Exam Score: **{quiz_percentage}%** ({correct_count}/{total_q}) - PASSED")
                        st.markdown("### Badge Unlocked")
                        st.markdown(f"""
                        <div class="glass-card" style="border-color: rgba(16, 185, 129, 0.55); background: rgba(6, 78, 59, 0.32);">
                            <div style="font-size: 2rem; font-weight: 800; color: #34d399;">{final_exam_result.badge.name}</div>
                            <div class="stat-label">Badge ID</div>
                            <code>{final_exam_result.badge.badge_id}</code>
                            <div style="margin-top: 10px;">Issued to <strong>{final_exam_result.badge.issued_to}</strong> for scoring <strong>{final_exam_result.badge.score}%</strong>.</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Final Exam Score: **{quiz_percentage}%** ({correct_count}/{total_q}) - NOT PASSED")
                        st.info(final_exam_result.message)

                    # Run Progress & Recommendation Agents
                    readiness_report = engine.run_assessment_evaluation(
                        st.session_state["session_id"],
                        profile,
                        quiz,
                        quiz_percentage
                    )

                    # Store report back in cache
                    pipeline_cache["readiness"] = readiness_report

                    # Displays Readiness Score
                    st.markdown("### 🏆 Final Readiness Profile")
                    
                    # GO / NOT YET badge
                    badge_style = "rec-go" if readiness_report.booking_recommendation == "GO" else ("rec-cond" if readiness_report.booking_recommendation == "CONDITIONAL GO" else "rec-notyet")
                    st.markdown(f"Booking recommendation: <span class='{badge_style}'>{readiness_report.booking_recommendation}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Readiness Score:** `{readiness_report.overall_readiness}%` (Recommended target >= 75%)")
                    st.markdown(f"**Remediation Plan:** {readiness_report.remediation_plan}")

                    # Radar Chart of domain scores
                    categories = list(readiness_report.domain_scores.keys())
                    scores = list(readiness_report.domain_scores.values())

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=scores + [scores[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name='Domain Strengths',
                        line_color='#818cf8'
                    ))
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                color='#94a3b8'
                            ),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e2e8f0',
                        margin=dict(l=40, r=40, t=10, b=10),
                        height=250
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # 3. Agent Trace Console (Bottom expandable layout)
        st.markdown("---")
        with st.expander("👁️ View Live Agent Traces & Boundary Guardrails", expanded=True):
            traces = engine.get_traces_by_session(st.session_state["session_id"])
            if traces:
                for t in traces:
                    agent = t["agent"]
                    content = t["content"]
                    
                    # Choose style based on agent
                    css_class = "trace-other"
                    if "Curator" in agent:
                        css_class = "trace-curator"
                    elif "Planner" in agent or "Study" in agent:
                        css_class = "trace-planner"
                    elif "Engagement" in agent:
                        css_class = "trace-engagement"
                    elif "Assessment" in agent:
                        css_class = "trace-assessment"
                    elif "Recommender" in agent or "Progress" in agent:
                        css_class = "trace-recommender"
                    elif "Critic" in agent or "Guardrail" in agent:
                        css_class = "trace-critic"
                        
                    st.markdown(f"<div class='trace-item {css_class}'>[{agent}] {content}</div>", unsafe_allow_html=True)
            else:
                st.info("No traces recorded for this session. Execute the agent pipeline to view traces.")

# ----------------- VIEW 2: MANAGER PORTAL -----------------
else:
    st.header("📊 Manager Readiness Dashboard")

    # Generate mock readiness reports for all learners
    with st.spinner("Aggregating team metrics across Fabric IQ semantic layer..."):
        all_profiles = []
        all_reports = []
        all_badges = engine.get_all_badges()
        
        # Load and run metrics for all users
        for l in learners:
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
            
            # Map mock assessment score
            mock_score = l["practice_score_avg"] + 4.0
            cert_data = engine.fabric_iq.get_certification(temp_profile.certification_target)
            
            # Run report evaluation
            temp_report = engine.progress.execute(temp_profile, mock_score, cert_data)
            temp_report = engine.recommender.execute(temp_report, cert_data)
            all_reports.append(temp_report)

        # Run Manager Pipeline
        manager_session_id = f"manager_{st.session_state['session_id']}"
        insights = engine.run_manager_pipeline(manager_session_id, all_profiles, all_reports)

    # 1. Summary Statistics cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{insights.total_learners}</div>
            <div class="stat-label">Total Active Enrolled</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{insights.average_readiness}%</div>
            <div class="stat-label">Average Team Readiness</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{len(insights.at_risk_learners)}</div>
            <div class="stat-label">Workload Burnout Risks</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-val">{len(all_badges)}</div>
            <div class="stat-label">Badges Unlocked</div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # Chart 1: Readiness by track
        st.subheader("📈 Average Readiness by Certification Target")
        tracks = list(insights.readiness_by_exam.keys())
        scores = list(insights.readiness_by_exam.values())
        
        df_track = pd.DataFrame({"Certification": tracks, "Average Readiness (%)": scores})
        fig_track = px.bar(
            df_track,
            x="Certification",
            y="Average Readiness (%)",
            color="Certification",
            color_discrete_sequence=px.colors.qualitative.Safe,
            range_y=[0, 100]
        )
        fig_track.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0',
            height=300,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig_track, use_container_width=True)

        # Peer Buddy Match Suggestions
        st.subheader("👥 Recommended Peer Study Pairs (Fabric IQ)")
        if insights.buddy_recommendations:
            buddy_data = []
            for b in insights.buddy_recommendations:
                buddy_data.append({
                    "Learner A": b.learner_a_name,
                    "Learner B": b.learner_b_name,
                    "Target Certification": b.certification_target,
                    "Common Available Window": b.common_slot
                })
            st.dataframe(pd.DataFrame(buddy_data), hide_index=True, use_container_width=True)
        else:
            st.info("No buddy pairs identified matching same goals and calendars.")

        st.subheader("Unlocked Certification Badges")
        if all_badges:
            badge_data = [
                {
                    "Learner": b.issued_to,
                    "Certification": b.certification_target,
                    "Badge": b.name,
                    "Score": b.score,
                    "Badge ID": b.badge_id
                }
                for b in all_badges
            ]
            st.dataframe(pd.DataFrame(badge_data), hide_index=True, use_container_width=True)
        else:
            st.info("No final exam badges unlocked yet.")

    with col2:
        st.subheader("Worker Learning Comments")
        if insights.learner_comments:
            comments_data = [
                {
                    "Learner": c.name,
                    "Certification": c.certification_target,
                    "Misses": c.missed_count,
                    "Penalty": "Yes" if c.penalty_applied else "No",
                    "Comment": c.comment
                }
                for c in insights.learner_comments
            ]
            st.dataframe(pd.DataFrame(comments_data), hide_index=True, use_container_width=True)

        # Calendar Risk Heatmap list
        st.subheader("⚠️ Calendar Overload & Exam Failure Risk Heatmap")
        
        risk_data = []
        for r in insights.at_risk_learners:
            risk_data.append({
                "Learner": r.name,
                "Meeting Hours/wk": r.meeting_hours,
                "Risk Status": r.risk_level,
                "Justification": r.reason
            })
            
        if risk_data:
            df_risk = pd.DataFrame(risk_data)
            st.dataframe(
                df_risk,
                column_config={
                    "Risk Status": st.column_config.SelectboxColumn(
                        "Risk Tier",
                        options=["High", "Medium", "Low"]
                    )
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("No workload burnout risks detected! All calendars are within healthy boundaries.")

    # 3. Agent Trace Console
    st.markdown("---")
    with st.expander("👁️ View Live Manager Analytics Agent Traces", expanded=True):
        m_traces = engine.get_traces_by_session(f"manager_{st.session_state['session_id']}")
        if m_traces:
            for t in m_traces:
                agent = t["agent"]
                content = t["content"]
                css_class = "trace-other"
                if "Manager" in agent:
                    css_class = "trace-curator"
                elif "Peer" in agent:
                    css_class = "trace-planner"
                elif "Critic" in agent:
                    css_class = "trace-critic"
                st.markdown(f"<div class='trace-item {css_class}'>[{agent}] {content}</div>", unsafe_allow_html=True)
        else:
            st.info("Execute manager metrics pipeline to view traces.")
