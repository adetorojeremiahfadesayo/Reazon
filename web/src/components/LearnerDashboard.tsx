import {
  Activity,
  BookOpen,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  Clock,
  Download,
  Play,
  ShieldCheck,
  Trophy
} from "lucide-react";
import type { LearnerOption, LearnerWorkspace, ReportFile } from "../types";
import { AssessmentPanel } from "./AssessmentPanel";
import { StatCard } from "./StatCard";
import { TooltipButton } from "./TooltipButton";
import { TraceConsole } from "./TraceConsole";

type LearnerDashboardProps = {
  selectedLearner?: LearnerOption;
  workspace: LearnerWorkspace | null;
  reports: ReportFile[];
  reportsLoading: boolean;
  onRefreshReports: () => void | Promise<void>;
  prompt: string;
  onPromptChange: (prompt: string) => void;
  weeks: number;
  onRun: () => void;
  loading: boolean;
};

function extractHours(label: string) {
  const match = label.match(/\((\d+)h\)/);
  return match ? Number(match[1]) : 0;
}

function formatDomainName(label: string) {
  return label.replace(/\s\(\d+h\)/, "");
}

const pipelineSteps = [
  { label: "Profile", icon: BrainCircuit },
  { label: "Curation", icon: BookOpen },
  { label: "Schedule", icon: CalendarDays },
  { label: "Assess", icon: CheckCircle2 },
  { label: "Verify", icon: ShieldCheck },
  { label: "Badge", icon: Trophy }
];

export function LearnerDashboard({
  selectedLearner,
  workspace,
  reports,
  reportsLoading,
  onRefreshReports,
  prompt,
  onPromptChange,
  weeks,
  onRun,
  loading
}: LearnerDashboardProps) {
  const profile = workspace?.profile;
  const learner = profile ?? selectedLearner;
  const learnerReports = reports.filter((report) => {
    const learnerMatch = learner
      ? report.learner_id === learner.learner_id || report.learner_id === learner.employee_id
      : false;
    return learnerMatch && (report.report_type === "Study plan" || report.report_type === "Badge certificate");
  });
  const studyPlanReport = learnerReports.find((report) => report.report_type === "Study plan");
  const badgeReportById = new Map(
    learnerReports
      .filter((report) => report.report_type === "Badge certificate")
      .map((report) => [report.file_name.replace(/\.pdf$/i, ""), report])
  );

  return (
    <div className="dashboard-grid">
      <section className="command-strip" data-tour="agent-pipeline">
        <div>
          <p>Agent pipeline</p>
          <h2>{learner ? `${learner.name} - ${learner.certification_target}` : "Select a learner"}</h2>
          <span>
            Run the workforce development flow for profiling, course curation, scheduling, checkpoint assessment, activity
            verification, booking guidance, and guardrail traces.
          </span>
        </div>
        <label className="prompt-box">
          Worker prompt
          <textarea
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            title="Edit the learner request sent to the profiling agent"
          />
          {learner ? (
            <div className="prompt-tags">
              <span>Role: {learner.role}</span>
              <span>Exam: {learner.certification_target}</span>
            </div>
          ) : null}
        </label>
        <TooltipButton
          tooltip="Execute the full learner pipeline for the selected persona and current week count"
          icon={<Play size={18} />}
          variant="primary"
          onClick={onRun}
          disabled={!selectedLearner || loading}
        >
          {loading ? "Running agents" : "Execute pipeline"}
        </TooltipButton>
      </section>

      <section className="pipeline-stage-rail" aria-label="Agent pipeline stages" data-tour="pipeline-stages">
        {pipelineSteps.map((step, index) => {
          const StepIcon = step.icon;
          const stageState = workspace ? "complete" : loading && index === 0 ? "running" : "pending";
          return (
            <article className={`stage ${stageState}`} key={step.label}>
              <StepIcon size={18} />
              <span>{step.label}</span>
              <small className="sr-only">{stageState}</small>
            </article>
          );
        })}
      </section>

      <section className="metric-grid">
        <StatCard label="Worker pathway" value={learner?.role ?? "-"} tone="blue" helper="Role/persona input" />
        <StatCard
          label="Certification"
          value={learner?.certification_target ?? "-"}
          tone="green"
          helper={`${weeks} week plan`}
        />
        <StatCard
          label="Practice average"
          value={`${learner?.practice_score_avg ?? 0}%`}
          tone="amber"
          helper="Synthetic baseline"
        />
        <StatCard
          label="Weekly study budget"
          value={profile ? `${profile.weekly_study_budget_hours}h` : "-"}
          tone="neutral"
          helper={profile ? `${profile.meeting_hours_per_week}h meetings` : "Run pipeline"}
        />
      </section>

      {!workspace ? (
        <section className="panel first-run">
          <BrainCircuit size={34} />
          <div>
            <h2>Ready for the web workflow</h2>
            <p>
              Select a worker or intern, adjust the prompt if needed, and execute the pipeline. Results will populate the
              study plan, learning resources, activity verification, weekly checkpoint, badge state, and trace console.
            </p>
          </div>
        </section>
      ) : (
        <>
          <section className="panel plan-panel">
            <div className="section-heading">
              <div>
                <p>Largest Remainder allocation</p>
                <h2>Workload-aware study plan</h2>
              </div>
              <div className="plan-header-actions">
                <span>{workspace.plan.total_hours} total hours</span>
                {studyPlanReport ? (
                  <a
                    className="pdf-icon-link"
                    href={studyPlanReport.download_url}
                    target="_blank"
                    rel="noreferrer"
                    title="Download this worker's auto-generated study plan PDF"
                    aria-label="Download study plan PDF"
                  >
                    <Download size={17} />
                  </a>
                ) : (
                  <button
                    className="pdf-icon-link disabled"
                    type="button"
                    disabled
                    title={
                      reportsLoading
                        ? "Checking for the auto-generated study plan PDF"
                        : "The study plan PDF is being created automatically"
                    }
                    aria-label="Study plan PDF is not ready yet"
                  >
                    <Download size={17} />
                  </button>
                )}
              </div>
            </div>

            <div className="timeline-list">
              {workspace.plan.schedule.map((week) => (
                <article className="timeline-row" key={week.week_number}>
                  <div className="week-index">W{week.week_number}</div>
                  <div className="week-content">
                    <div className="week-header">
                      <strong>{week.hours_allocated}h allocated</strong>
                      {week.workload_adjusted ? <span className="status warning">Adjusted</span> : <span className="status ok">Standard</span>}
                    </div>
                    <div
                      className="domain-allocation-list"
                      aria-label={`Week ${week.week_number} domain allocation`}
                    >
                      {week.focus_domains.map((domain) => {
                        const hours = extractHours(domain);
                        const width = week.hours_allocated > 0 ? Math.min(100, (hours / week.hours_allocated) * 100) : 0;
                        return (
                          <div className="domain-allocation-row" key={domain}>
                            <span>{formatDomainName(domain)}</span>
                            <div>
                              <i style={{ inlineSize: `${width}%` }} />
                            </div>
                            <strong>{hours > 0 ? `${hours}h` : "-"}</strong>
                          </div>
                        );
                      })}
                    </div>
                    {week.adjustment_reason ? <small>{week.adjustment_reason}</small> : null}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="panel engagement-panel">
            <div className="section-heading">
              <div>
                <p>Work IQ</p>
                <h2>Focus window</h2>
              </div>
              <Clock size={20} />
            </div>
            <strong>{workspace.engagement.recommended_time ?? "No window"}</strong>
            <p>{workspace.engagement.reminder_message}</p>
            <div className="activity-summary">
              <span>
                <Activity size={16} />
                {workspace.activity.average_completion_confidence}% confidence
              </span>
              <span>
                <CheckCircle2 size={16} />
                {workspace.activity.completed_modules}/{workspace.activity.total_modules} modules
              </span>
            </div>
          </section>

          <section className="panel path-panel">
            <div className="section-heading">
              <div>
                <p>Foundry IQ citations</p>
                <h2>Curated course path</h2>
              </div>
              <BookOpen size={20} />
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Domain</th>
                    <th>Resource</th>
                    <th>Skills</th>
                    <th>Citation</th>
                  </tr>
                </thead>
                <tbody>
                  {workspace.learning_paths.map((path, index) => (
                    <tr key={`${path.domain_name}-${index}`}>
                      <td>{path.domain_name}</td>
                      <td>
                        {path.resource_url ? (
                          <a href={path.resource_url} target="_blank" rel="noreferrer">
                            {path.resource_title ?? "Assigned Microsoft Learn course"}
                          </a>
                        ) : (
                          path.resource_title ?? "Resource"
                        )}
                      </td>
                      <td>{path.skills_covered?.join(", ")}</td>
                      <td>{path.citation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel activity-panel">
            <div className="section-heading">
              <div>
                <p>LMS + Graph evidence</p>
                <h2>Learning activity verification</h2>
              </div>
              <ShieldCheck size={20} />
            </div>
            <p>{workspace.activity.recommendation}</p>
            <div className="evidence-list">
              {workspace.activity.evidence_summary.slice(0, 5).map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </section>

          <section className="panel badge-panel">
            <div className="section-heading">
              <div>
                <p>Credential state</p>
              <h2>Unlocked badges</h2>
              </div>
              <Trophy size={20} />
            </div>
            {workspace.badges.length === 0 ? (
              <p className="empty-state">No badges yet. Passing the final exam simulator at 65%+ unlocks one.</p>
            ) : (
              workspace.badges.map((badge) => {
                const badgeReport = badgeReportById.get(badge.badge_id);
                return (
                  <article className="badge-row" key={badge.badge_id}>
                    <div>
                      <strong>{badge.name}</strong>
                      <span>{badge.score}% - {badge.badge_id}</span>
                    </div>
                    {badgeReport ? (
                      <a
                        className="pdf-icon-link"
                        href={badgeReport.download_url}
                        target="_blank"
                        rel="noreferrer"
                        title="Download this person's badge certificate PDF"
                        aria-label="Download badge certificate PDF"
                      >
                        <Download size={17} />
                      </a>
                    ) : null}
                  </article>
                );
              })
            )}
          </section>

          <AssessmentPanel
            quiz={workspace.quiz}
            employeeId={workspace.profile.employee_id}
            textInput={prompt}
            onAssessmentComplete={onRefreshReports}
          />
          <TraceConsole traces={workspace.traces} />
        </>
      )}
    </div>
  );
}
