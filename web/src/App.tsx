import { useEffect, useMemo, useState } from "react";
import { getHealth, getLearners, getManagerInsights, getReports, runLearnerWorkspace, submitAssessment } from "./api";
import { AppShell } from "./components/AppShell";
import { FinalExamPanel } from "./components/FinalExamPanel";
import { GuidedTour } from "./components/GuidedTour";
import { LearnerDashboard } from "./components/LearnerDashboard";
import { ManagerDashboard } from "./components/ManagerDashboard";
import type {
  AppView,
  AssessmentResult,
  Health,
  LearnerOption,
  LearnerWorkspace,
  ManagerInsights,
  ReportFile
} from "./types";

const TOUR_STORAGE_KEY = "reazon-guided-tour-seen";

function getPersonaGoal(role: string) {
  return role.toLowerCase().includes("intern")
    ? "I am taking the exam to qualify for a worker role."
    : "I am taking the exam to prepare for promotion.";
}

function buildPrompt(learner: LearnerOption) {
  return `I am ${learner.name}, a ${learner.role}. ${getPersonaGoal(learner.role)} My target exam is ${learner.certification_target}.`;
}

export function App() {
  const [activeView, setActiveView] = useState<AppView>("learner");
  const [learners, setLearners] = useState<LearnerOption[]>([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const [weeks, setWeeks] = useState(4);
  const [prompt, setPrompt] = useState("I want to study for a Microsoft certification exam.");
  const [health, setHealth] = useState<Health | null>(null);
  const [workspace, setWorkspace] = useState<LearnerWorkspace | null>(null);
  const [managerInsights, setManagerInsights] = useState<ManagerInsights | null>(null);
  const [reports, setReports] = useState<ReportFile[]>([]);
  const [loadingLearner, setLoadingLearner] = useState(false);
  const [loadingManager, setLoadingManager] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);
  const [loadingJudgeDemo, setLoadingJudgeDemo] = useState(false);
  const [judgeDemoStatus, setJudgeDemoStatus] = useState("Ready to run a guided judge demo.");
  const [judgeAssessmentResult, setJudgeAssessmentResult] = useState<AssessmentResult | null>(null);
  const [tourOpen, setTourOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedLearner = useMemo(
    () => learners.find((learner) => learner.employee_id === selectedEmployeeId),
    [learners, selectedEmployeeId]
  );

  const refreshHealth = async () => {
    try {
      setHealth(await getHealth());
    } catch {
      setHealth({ status: "offline", mock_mode: true });
    }
  };

  useEffect(() => {
    refreshHealth();
    getLearners()
      .then((items) => {
        setLearners(items);
        if (items[0]) {
          setSelectedEmployeeId(items[0].employee_id);
          setPrompt(buildPrompt(items[0]));
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load learners"));
  }, []);

  const updateLearner = (employeeId: string) => {
    const learner = learners.find((item) => item.employee_id === employeeId);
    setSelectedEmployeeId(employeeId);
    setWorkspace(null);
    if (learner) {
      setPrompt(buildPrompt(learner));
    }
  };

  const runWorkspace = async () => {
    if (!selectedEmployeeId) return;
    setLoadingLearner(true);
    setError(null);
    try {
      const data = await runLearnerWorkspace(selectedEmployeeId, prompt, weeks);
      setWorkspace(data);
      await refreshReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Learner pipeline failed");
    } finally {
      setLoadingLearner(false);
    }
  };

  const runJudgeDemo = async () => {
    if (!selectedEmployeeId) return;
    setLoadingJudgeDemo(true);
    setLoadingLearner(true);
    setError(null);
    setJudgeAssessmentResult(null);
    setActiveView("learner");
    try {
      setJudgeDemoStatus("1/4 Building learner workspace, plan, citations, and trace evidence.");
      const data = await runLearnerWorkspace(selectedEmployeeId, prompt, weeks);
      setWorkspace(data);

      setJudgeDemoStatus("2/4 Auto-filling the checkpoint with the synthetic passing path.");
      const answers = Object.fromEntries(
        data.quiz.questions.map((question) => [String(question.question_id), question.correct_option_index])
      );
      const result = await submitAssessment(selectedEmployeeId, prompt, answers);
      setJudgeAssessmentResult(result);

      setJudgeDemoStatus("3/4 Refreshing generated report evidence and cache-aware traces.");
      await refreshReports();

      setJudgeDemoStatus("4/4 Loading manager cohort analytics for triage and next-best actions.");
      setManagerInsights(await getManagerInsights());
      setActiveView("manager");
      setJudgeDemoStatus("Judge demo completed: learner evidence, checkpoint result, PDFs, and manager triage are ready.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Judge demo failed");
      setJudgeDemoStatus("Judge demo stopped. Check the error banner and trace console.");
    } finally {
      setLoadingLearner(false);
      setLoadingJudgeDemo(false);
    }
  };

  const refreshManager = async () => {
    setLoadingManager(true);
    setError(null);
    try {
      setManagerInsights(await getManagerInsights());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Manager pipeline failed");
    } finally {
      setLoadingManager(false);
    }
  };

  const refreshReports = async () => {
    setLoadingReports(true);
    setError(null);
    try {
      setReports(await getReports());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load reports");
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    refreshReports();
  }, []);

  useEffect(() => {
    try {
      if (window.localStorage.getItem(TOUR_STORAGE_KEY) !== "true") {
        setTourOpen(true);
      }
    } catch {
      setTourOpen(true);
    }
  }, []);

  const closeTour = () => {
    try {
      window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
    } catch {
      // If storage is unavailable, still let the visitor close the tour.
    }
    setTourOpen(false);
  };

  const renderedView =
    activeView === "learner" ? (
      <LearnerDashboard
        selectedLearner={selectedLearner}
        workspace={workspace}
        learners={learners}
        judgeDemoStatus={judgeDemoStatus}
        judgeAssessmentResult={judgeAssessmentResult}
        reports={reports}
        reportsLoading={loadingReports}
        onRefreshReports={refreshReports}
        prompt={prompt}
        onPromptChange={setPrompt}
        weeks={weeks}
        onRun={runWorkspace}
        loading={loadingLearner}
      />
    ) : activeView === "exam" ? (
      <FinalExamPanel selectedLearner={selectedLearner} prompt={prompt} onAssessmentComplete={refreshReports} />
    ) : (
      <ManagerDashboard
        insights={managerInsights}
        selectedLearner={selectedLearner}
        reports={reports}
        reportsLoading={loadingReports}
        loading={loadingManager}
        onRefresh={refreshManager}
        onRefreshReports={refreshReports}
      />
    );

  return (
    <AppShell
      activeView={activeView}
      onViewChange={setActiveView}
      learners={learners}
      selectedEmployeeId={selectedEmployeeId}
      onLearnerChange={updateLearner}
      weeks={weeks}
      onWeeksChange={setWeeks}
      health={health}
      onRefreshHealth={refreshHealth}
      onStartTour={() => setTourOpen(true)}
      onRunJudgeDemo={runJudgeDemo}
      judgeDemoStatus={judgeDemoStatus}
      judgeDemoRunning={loadingJudgeDemo}
    >
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="view-transition" key={activeView}>
        {renderedView}
      </div>
      <GuidedTour
        active={tourOpen}
        activeView={activeView}
        onViewChange={setActiveView}
        onClose={closeTour}
      />
    </AppShell>
  );
}
