import { AlertTriangle, RefreshCw, Users } from "lucide-react";
import { useMemo } from "react";
import type { LearnerOption, ManagerInsights, ReportFile } from "../types";
import { ReportList } from "./ReportList";
import { StatCard } from "./StatCard";
import { TooltipButton } from "./TooltipButton";

type ManagerDashboardProps = {
  insights: ManagerInsights | null;
  selectedLearner?: LearnerOption;
  reports: ReportFile[];
  reportsLoading: boolean;
  loading: boolean;
  onRefresh: () => void;
  onRefreshReports: () => void;
};

export function ManagerDashboard({
  insights,
  selectedLearner,
  reports,
  reportsLoading,
  loading,
  onRefresh,
  onRefreshReports
}: ManagerDashboardProps) {
  const readinessReports = useMemo(() => {
    if (!selectedLearner) return [];
    return reports.filter(
      (report) =>
        report.report_type === "Readiness report" &&
        (report.learner_id === selectedLearner.learner_id || report.learner_id === selectedLearner.employee_id)
    );
  }, [reports, selectedLearner]);
  const readinessTitle = selectedLearner ? `${selectedLearner.name} readiness PDF` : "Selected intern readiness PDF";

  return (
    <div className="manager-grid">
      <section className="command-strip manager-command" data-tour="manager-command">
        <div>
          <p>Intern cohort analytics</p>
          <h2>Aggregate readiness and internship risk</h2>
          <span>Refresh the program pipeline to recompute readiness by track, risk flags, peer matches, and manager comments.</span>
        </div>
        <TooltipButton
          tooltip="Run the manager insights pipeline for all synthetic learners"
          icon={<RefreshCw size={18} />}
          variant="primary"
          onClick={onRefresh}
          disabled={loading}
        >
          {loading ? "Refreshing" : "Refresh insights"}
        </TooltipButton>
      </section>

      <ReportList
        dataTour="report-evidence"
        title={readinessTitle}
        eyebrow="Manager evidence"
        emptyText={
          selectedLearner
            ? `No readiness PDF is available for ${selectedLearner.name} yet. Submit that intern's assessment to generate one automatically.`
            : "Select an intern to view their readiness PDF."
        }
        reports={readinessReports}
        loading={reportsLoading}
        onRefresh={onRefreshReports}
      />

      {insights ? (
        <>
          <section className="metric-grid manager-metrics">
            <StatCard label="Active interns" value={insights.total_learners} tone="blue" helper="Synthetic cohort" />
            <StatCard label="Average readiness" value={`${insights.average_readiness}%`} tone="green" helper="Team score" />
            <StatCard label="At-risk learners" value={insights.at_risk_learners.length} tone="red" helper="Workload pressure" />
            <StatCard label="Buddy matches" value={insights.buddy_recommendations.length} tone="amber" helper="Same-track peers" />
          </section>

          <section className="panel readiness-chart">
            <div className="section-heading">
              <div>
                <p>Fabric IQ semantic layer</p>
                <h2>Readiness by internship track</h2>
              </div>
              <Users size={20} />
            </div>
            <div className="bar-list">
              {Object.entries(insights.readiness_by_exam).map(([exam, score]) => (
                <div className="bar-row" key={exam}>
                  <span>{exam}</span>
                  <div>
                    <i style={{ inlineSize: `${score}%` }} />
                  </div>
                  <strong>{score}%</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="panel risk-panel">
            <div className="section-heading">
              <div>
                <p>Calendar overload</p>
                <h2>Risk heatmap</h2>
              </div>
              <AlertTriangle size={20} />
            </div>
            <div className="risk-list">
              {insights.at_risk_learners.map((risk) => (
                <article className="risk-row" key={risk.name}>
                  <strong>{risk.name}</strong>
                  <span>{risk.risk_level} - {risk.meeting_hours} meeting hours/week</span>
                  <p>{risk.reason}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel buddy-panel">
            <div className="section-heading">
              <div>
                <p>Peer collaboration</p>
                <h2>Intern study buddy matches</h2>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Learner A</th>
                    <th>Learner B</th>
                    <th>Certification</th>
                    <th>Common slot</th>
                  </tr>
                </thead>
                <tbody>
                  {insights.buddy_recommendations.map((buddy) => (
                    <tr key={`${buddy.learner_a}-${buddy.learner_b}`}>
                      <td>{buddy.learner_a}</td>
                      <td>{buddy.learner_b}</td>
                      <td>{buddy.certification_target}</td>
                      <td>{buddy.common_slot}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel comments-panel">
            <div className="section-heading">
              <div>
                <p>Worker learning comments</p>
                <h2>Intern remediation notes</h2>
              </div>
            </div>
            <div className="comment-list">
              {insights.learner_comments.map((comment) => (
                <article className={comment.penalty_applied ? "comment-row penalty" : "comment-row"} key={comment.name}>
                  <strong>{comment.name} - {comment.certification_target}</strong>
                  <span>{comment.missed_count} missed checkpoint(s)</span>
                  <p>{comment.comment}</p>
                </article>
              ))}
            </div>
          </section>

        </>
      ) : (
        <section className="panel first-run">
          <Users size={34} />
          <div>
            <h2>Manager portal is ready</h2>
            <p>Refresh insights to aggregate intern readiness, risk, learning comments, and peer study matches.</p>
          </div>
        </section>
      )}
    </div>
  );
}
