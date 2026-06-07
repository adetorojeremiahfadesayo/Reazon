from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_web_file(path: str) -> str:
    return (ROOT / "web" / "src" / path).read_text(encoding="utf-8")


def test_judge_demo_flow_is_exposed_from_app_shell():
    app = read_web_file("App.tsx")
    shell = read_web_file("components/AppShell.tsx")

    assert "runJudgeDemo" in app
    assert "Run judge demo" in shell
    assert "submitAssessment" in app
    assert "getManagerInsights" in app


def test_learner_workspace_surfaces_explainability_and_cache_strategy():
    learner = read_web_file("components/LearnerDashboard.tsx")
    trace = read_web_file("components/TraceConsole.tsx")

    assert "Why this recommendation?" in learner
    assert "Learner comparison" in learner
    assert "Intentional failure path" in learner
    assert "Cache strategy" in trace
    assert "cacheStatus" in trace


def test_manager_portal_surfaces_next_best_actions_and_report_status():
    manager = read_web_file("components/ManagerDashboard.tsx")
    reports = read_web_file("components/ReportList.tsx")

    assert "Next-best manager actions" in manager
    assert "Compare selected learner to cohort" in manager
    assert "Evidence status" in reports
