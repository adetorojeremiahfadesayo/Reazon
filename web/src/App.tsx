import { useEffect, useMemo, useState } from "react";
import { getHealth, getLearners, getManagerInsights, getReports, runLearnerWorkspace } from "./api";
import { AppShell } from "./components/AppShell";
import { GuidedTour } from "./components/GuidedTour";
import { LearnerDashboard } from "./components/LearnerDashboard";
import { ManagerDashboard } from "./components/ManagerDashboard";
import type { AppView, Health, LearnerOption, LearnerWorkspace, ManagerInsights, ReportFile } from "./types";

const TOUR_STORAGE_KEY = "reazon-guided-tour-seen";

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
          setPrompt(
            `I am ${items[0].name}, working as a ${items[0].role}. My target exam is ${items[0].certification_target}.`
          );
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load learners"));
  }, []);

  const updateLearner = (employeeId: string) => {
    const learner = learners.find((item) => item.employee_id === employeeId);
    setSelectedEmployeeId(employeeId);
    setWorkspace(null);
    if (learner) {
      setPrompt(`I am ${learner.name}, working as a ${learner.role}. My target exam is ${learner.certification_target}.`);
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
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {activeView === "learner" ? (
        <LearnerDashboard
          selectedLearner={selectedLearner}
          workspace={workspace}
          reports={reports}
          reportsLoading={loadingReports}
          onRefreshReports={refreshReports}
          prompt={prompt}
          onPromptChange={setPrompt}
          weeks={weeks}
          onRun={runWorkspace}
          loading={loadingLearner}
        />
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
      )}
      <GuidedTour
        active={tourOpen}
        activeView={activeView}
        onViewChange={setActiveView}
        onClose={closeTour}
      />
    </AppShell>
  );
}
