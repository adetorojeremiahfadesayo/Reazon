import { BrainCircuit, FileQuestion, Gauge, HelpCircle, RefreshCw, Users } from "lucide-react";
import type { AppView, Health, LearnerOption } from "../types";
import { TooltipButton } from "./TooltipButton";

type AppShellProps = {
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  learners: LearnerOption[];
  selectedEmployeeId: string;
  onLearnerChange: (employeeId: string) => void;
  weeks: number;
  onWeeksChange: (weeks: number) => void;
  health?: Health | null;
  onRefreshHealth: () => void;
  onStartTour: () => void;
  children: React.ReactNode;
};

const titleByView: Record<AppView, string> = {
  learner: "Learning workspace",
  exam: "Final exam simulator",
  manager: "Program manager portal"
};

export function AppShell({
  activeView,
  onViewChange,
  learners,
  selectedEmployeeId,
  onLearnerChange,
  weeks,
  onWeeksChange,
  health,
  onRefreshHealth,
  onStartTour,
  children
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">R</div>
          <div>
            <strong>Reazon</strong>
            <span>Microsoft Certification Readiness</span>
          </div>
        </div>

        <nav className="view-nav" aria-label="Primary views" data-tour="view-nav">
          <TooltipButton
            tooltip="Open the learner workspace for study plans, exams, badges, and traces"
            icon={<BrainCircuit size={18} />}
            variant={activeView === "learner" ? "primary" : "ghost"}
            onClick={() => onViewChange("learner")}
          >
            Learning Space
          </TooltipButton>
          <TooltipButton
            tooltip="Open the final exam simulator for timed certification readiness attempts"
            icon={<FileQuestion size={18} />}
            variant={activeView === "exam" ? "primary" : "ghost"}
            onClick={() => onViewChange("exam")}
          >
            Final Exam
          </TooltipButton>
          <TooltipButton
            tooltip="Open the manager portal for team readiness, risks, and buddy matching"
            icon={<Users size={18} />}
            variant={activeView === "manager" ? "primary" : "ghost"}
            onClick={() => onViewChange("manager")}
          >
            Manager Portal
          </TooltipButton>
        </nav>

        <div className="side-note">
          <Gauge size={18} />
          <span>Microsoft certification readiness program using synthetic Microsoft Learn, LMS, and Work IQ signals.</span>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyeline">Reazon: Microsoft Certification Readiness</p>
            <h1>{titleByView[activeView]}</h1>
          </div>

          <div className="topbar-controls" data-tour="learner-controls">
            <label>
              Person
              <select
                value={selectedEmployeeId}
                onChange={(event) => onLearnerChange(event.target.value)}
                title="Choose the worker or intern persona used by the pipeline"
              >
                {learners.map((learner) => (
                  <option key={learner.employee_id} value={learner.employee_id}>
                    {learner.name} - {learner.role} - {learner.certification_target}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Weeks
              <select
                value={weeks}
                onChange={(event) => onWeeksChange(Number(event.target.value))}
                title="Choose the study plan duration"
              >
                {[3, 4, 5, 6, 8].map((week) => (
                  <option key={week} value={week}>
                    {week}
                  </option>
                ))}
              </select>
            </label>

            <div className={`health-pill ${health?.status === "healthy" ? "ok" : "warn"}`}>
              <span>{health?.status ?? "checking"}</span>
              <small>{health?.mock_mode ? "Mock mode" : "Live mode"}</small>
            </div>

            <TooltipButton
              tooltip="Refresh the backend health indicator"
              icon={<RefreshCw size={16} />}
              variant="ghost"
              onClick={onRefreshHealth}
            />

            <TooltipButton
              tooltip="Start a guided tour for judges"
              icon={<HelpCircle size={16} />}
              variant="secondary"
              onClick={onStartTour}
            >
              Guided tour
            </TooltipButton>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}
