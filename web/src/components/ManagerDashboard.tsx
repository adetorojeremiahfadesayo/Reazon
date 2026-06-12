import { AlertTriangle, RefreshCw, Users } from "lucide-react";
import { type CSSProperties, useMemo, useState } from "react";
import type { LearnerOption, ManagerInsights, ReportFile } from "../types";
import { ReportList } from "./ReportList";
import { StatCard } from "./StatCard";
import { TooltipButton } from "./TooltipButton";

const READINESS_THRESHOLD = 65;
const MAX_RISK_MEETING_HOURS = 40;
const RISK_COLORS: Record<string, string> = {
  High: "#c2410c",
  Medium: "#b7791f",
  Low: "#0f9f6e"
};

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
  const [riskView, setRiskView] = useState<"compact" | "detailed">("compact");
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<"High" | "Medium" | "Low">("High");
  const readinessReports = useMemo(() => {
    if (!selectedLearner) return [];
    return reports.filter(
      (report) =>
        report.report_type === "Readiness report" &&
        (report.learner_id === selectedLearner.learner_id || report.learner_id === selectedLearner.employee_id)
    );
  }, [reports, selectedLearner]);
  const readinessTitle = selectedLearner ? `${selectedLearner.name} readiness PDF` : "Selected person readiness PDF";
  const sortedReadiness = useMemo(() => {
    if (!insights) return [];
    return Object.entries(insights.readiness_by_exam)
      .map(([exam, score]) => ({ exam, score }))
      .sort((a, b) => a.score - b.score);
  }, [insights]);
  const readinessLow = sortedReadiness[0];
  const readinessHigh = sortedReadiness[sortedReadiness.length - 1];
  const atRiskPercent = insights?.total_learners
    ? Math.round((insights.at_risk_learners.length / insights.total_learners) * 100)
    : 0;
  const sortedRisks = useMemo(() => {
    if (!insights) return [];
    const riskRank: Record<string, number> = { High: 3, Medium: 2, Low: 1 };
    return [...insights.at_risk_learners].sort(
      (a, b) => (riskRank[b.risk_level] ?? 0) - (riskRank[a.risk_level] ?? 0) || b.meeting_hours - a.meeting_hours
    );
  }, [insights]);
  const riskGroups = useMemo(() => {
    const groups = { High: [] as typeof sortedRisks, Medium: [] as typeof sortedRisks, Low: [] as typeof sortedRisks };
    sortedRisks.forEach((risk) => {
      if (risk.risk_level === "High" || risk.risk_level === "Medium" || risk.risk_level === "Low") {
        groups[risk.risk_level].push(risk);
      }
    });
    return groups;
  }, [sortedRisks]);
  const totalRiskCount = sortedRisks.length;
  const highPercent = totalRiskCount ? Math.round((riskGroups.High.length / totalRiskCount) * 100) : 0;
  const mediumPercent = totalRiskCount ? Math.round((riskGroups.Medium.length / totalRiskCount) * 100) : 0;
  const selectedRisks = riskGroups[selectedRiskLevel];
  const selectedLearnerRisk = sortedRisks.find((risk) => risk.name === selectedLearner?.name);
  const nextBestActions = selectedRiskLevel === "High"
    ? ["Protect study focus time this week", "Move learner to a 6 week plan", "Assign a study buddy"]
    : selectedRiskLevel === "Medium"
      ? ["Monitor checkpoint completion", "Recommend a 2 hour weak-domain review", "Keep buddy pairing active"]
      : ["Maintain current plan", "Schedule final simulator when evidence is ready", "Refresh reports after checkpoint"];
  const progressByRole = useMemo(() => {
    if (!selectedLearner) return [];
    const roleFamily = selectedLearner.role.split(" - ")[0] || selectedLearner.role;
    return [
      {
        label: roleFamily,
        value: `${selectedLearner.practice_score_avg}%`,
        helper: "Selected role baseline"
      },
      {
        label: selectedLearner.certification_target,
        value: sortedReadiness.find((item) => item.exam === selectedLearner.certification_target)?.score
          ? `${sortedReadiness.find((item) => item.exam === selectedLearner.certification_target)?.score}%`
          : "pending",
        helper: "Track readiness"
      },
      {
        label: selectedLearnerRisk?.risk_level ?? "Low",
        value: selectedLearnerRisk ? `${selectedLearnerRisk.meeting_hours}h` : "clear",
        helper: "Capacity risk"
      }
    ];
  }, [selectedLearner, selectedLearnerRisk, sortedReadiness]);

  return (
    <div className="manager-grid">
      <section className="command-strip manager-command" data-tour="manager-command">
        <div>
          <p>Workforce cohort analytics</p>
          <h2>Aggregate readiness and development risk</h2>
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
            ? `No readiness PDF is available for ${selectedLearner.name} yet. Submit that person's final exam to generate one automatically.`
            : "Select a person to view their readiness PDF."
        }
        reports={readinessReports}
        loading={reportsLoading}
        onRefresh={onRefreshReports}
      />

      <section className="panel manager-action-panel">
        <div className="section-heading">
          <div>
            <p>Next-best manager actions</p>
            <h2>Program triage queue</h2>
          </div>
        </div>
        <div className="manager-action-grid">
          {nextBestActions.map((action) => (
            <article key={action}>
              <strong>{action}</strong>
              <span>{selectedRiskLevel} risk lens</span>
            </article>
          ))}
        </div>
      </section>

      <section className="panel manager-compare-panel">
        <div className="section-heading">
          <div>
            <p>Compare selected learner to cohort</p>
            <h2>{selectedLearner ? selectedLearner.name : "No learner selected"}</h2>
          </div>
        </div>
        <div className="comparison-grid">
          <article>
            <strong>{selectedLearner?.certification_target ?? "-"}</strong>
            <span>Certification track</span>
          </article>
          <article>
            <strong>{selectedLearner?.practice_score_avg ?? 0}%</strong>
            <span>Practice baseline</span>
          </article>
          <article>
            <strong>{selectedLearnerRisk?.risk_level ?? "Low"}</strong>
            <span>{selectedLearnerRisk?.reason ?? "No workload risk in manager triage"}</span>
          </article>
        </div>
      </section>

      <section className="panel role-progress-panel">
        <div className="section-heading">
          <div>
            <p>Progress by role</p>
            <h2>Role, track, and capacity summary</h2>
          </div>
        </div>
        <div className="comparison-grid">
          {progressByRole.length ? (
            progressByRole.map((item) => (
              <article key={`${item.label}-${item.helper}`}>
                <strong>{item.label}</strong>
                <span>{item.value}</span>
                <span>{item.helper}</span>
              </article>
            ))
          ) : (
            <article>
              <strong>Select a learner</strong>
              <span>Role progress appears after cohort insights are refreshed.</span>
            </article>
          )}
        </div>
      </section>

      {insights ? (
        <>
          <section className="metric-grid manager-metrics">
            <StatCard label="Active people" value={insights.total_learners} tone="blue" helper="Synthetic cohort" />
            <StatCard
              label="Average readiness"
              value={`${insights.average_readiness}%`}
              tone="green"
              helper={`${READINESS_THRESHOLD}% booking threshold`}
            />
            <StatCard
              label="At-risk learners"
              value={`${insights.at_risk_learners.length} of ${insights.total_learners}`}
              tone="red"
              helper={`${atRiskPercent}% need attention`}
            />
            <StatCard
              label="Buddy matches"
              value={insights.buddy_recommendations.length}
              tone="amber"
              helper="Same-track pairs"
            />
          </section>

          <section className="panel readiness-chart">
            <div className="section-heading">
              <div>
                <p>Fabric IQ semantic layer</p>
                <h2>Readiness by development track</h2>
              </div>
              <Users size={20} />
            </div>
            <div className="readiness-summary">
              <span>Lowest: {readinessLow ? `${readinessLow.exam} ${readinessLow.score}%` : "-"}</span>
              <span>Highest: {readinessHigh ? `${readinessHigh.exam} ${readinessHigh.score}%` : "-"}</span>
              <span>Cohort average: {insights.average_readiness}%</span>
            </div>
            <div
              className="bar-list readiness-bars"
              aria-label={`Readiness ranked from lowest to highest. Booking threshold is ${READINESS_THRESHOLD} percent. Cohort average is ${insights.average_readiness} percent.`}
            >
              {sortedReadiness.map(({ exam, score }) => (
                <div className="bar-row" key={exam}>
                  <span>{exam}</span>
                  <div
                    className="bar-track"
                    style={
                      {
                        "--threshold": `${READINESS_THRESHOLD}%`,
                        "--average": `${insights.average_readiness}%`
                      } as CSSProperties
                    }
                  >
                    <i className={score < READINESS_THRESHOLD ? "below-threshold" : ""} style={{ inlineSize: `${score}%` }} />
                  </div>
                  <strong>{score}%</strong>
                </div>
              ))}
            </div>
            <div className="chart-legend" aria-hidden="true">
              <span><i className="threshold-line" /> {READINESS_THRESHOLD}% threshold</span>
              <span><i className="average-line" /> Cohort average</span>
            </div>
          </section>

          <section className="panel risk-panel">
            <div className="section-heading">
              <div>
                <p>Calendar overload</p>
                <h2>Interactive risk triage</h2>
              </div>
              <AlertTriangle size={20} />
            </div>
            <div className="risk-view-tabs" aria-label="Risk view mode">
              <button
                type="button"
                className={riskView === "compact" ? "active" : ""}
                onClick={() => setRiskView("compact")}
              >
                Compact pieces
              </button>
              <button
                type="button"
                className={riskView === "detailed" ? "active" : ""}
                onClick={() => setRiskView("detailed")}
              >
                Detailed bars
              </button>
            </div>

            {riskView === "compact" ? (
              <div className="risk-compact-layout">
                <div
                  className="risk-donut animated-chart"
                  style={
                    {
                      "--high": `${highPercent}%`,
                      "--medium": `${highPercent + mediumPercent}%`
                    } as CSSProperties
                  }
                  role="img"
                  aria-label={`Risk distribution: ${riskGroups.High.length} high, ${riskGroups.Medium.length} medium, ${riskGroups.Low.length} low.`}
                >
                  <div>
                    <strong>{totalRiskCount}</strong>
                    <span>at risk</span>
                  </div>
                </div>

                <div className="risk-tile-board">
                  {(["High", "Medium", "Low"] as const).map((level) => (
                    <button
                      type="button"
                      className={selectedRiskLevel === level ? `risk-tile active ${level.toLowerCase()}` : `risk-tile ${level.toLowerCase()}`}
                      key={level}
                      onClick={() => setSelectedRiskLevel(level)}
                      aria-pressed={selectedRiskLevel === level}
                    >
                      <span className="risk-dot" style={{ background: RISK_COLORS[level] }} />
                      <strong>{level}</strong>
                      <small>{riskGroups[level].length} worker(s)</small>
                    </button>
                  ))}
                </div>

                <div className="risk-focus-card">
                  <div>
                    <p>{selectedRiskLevel} risk workers</p>
                    <h3>{selectedRisks.length ? selectedRisks.map((risk) => risk.name).join(", ") : "No workers in this tier"}</h3>
                  </div>
                  <div className="risk-focus-list">
                    {selectedRisks.length ? (
                      selectedRisks.map((risk) => (
                        <article key={risk.name}>
                          <strong>{risk.name}</strong>
                          <span>{risk.meeting_hours}h/wk meetings</span>
                          <small>{risk.reason}</small>
                        </article>
                      ))
                    ) : (
                      <article>
                        <strong>Clear tier</strong>
                        <span>No immediate manager action.</span>
                        <small>Keep monitoring checkpoint activity.</small>
                      </article>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="risk-heatmap" aria-label="At-risk learners ranked by risk level and meeting load">
                {sortedRisks.map((risk) => (
                  <article className={`risk-row ${risk.risk_level.toLowerCase()}`} key={risk.name}>
                    <div className="risk-row-header">
                      <strong>{risk.name}</strong>
                      <span className="risk-level">{risk.risk_level}</span>
                    </div>
                    <div className="risk-meter">
                      <span>Meeting load</span>
                      <div>
                        <i style={{ inlineSize: `${Math.min(100, (risk.meeting_hours / MAX_RISK_MEETING_HOURS) * 100)}%` }} />
                      </div>
                      <strong>{risk.meeting_hours}h/wk</strong>
                    </div>
                    <p>{risk.reason}</p>
                    <small>{risk.meeting_hours >= 30 ? "Action: protect study time this week" : "Action: monitor workload and checkpoints"}</small>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="panel buddy-panel">
            <div className="section-heading">
              <div>
                <p>Peer collaboration</p>
                <h2>Study buddy matches</h2>
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
                <h2>Remediation notes</h2>
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
            <p>Refresh insights to aggregate workforce readiness, risk, learning comments, and peer study matches.</p>
          </div>
        </section>
      )}
    </div>
  );
}
