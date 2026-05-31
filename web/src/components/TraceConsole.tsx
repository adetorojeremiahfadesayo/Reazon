import type { Trace } from "../types";

type TraceConsoleProps = {
  traces: Trace[];
};

const toneForAgent = (agent: string) => {
  if (agent.includes("Critic") || agent.includes("Guardrail")) return "critic";
  if (agent.includes("Assessment")) return "assessment";
  if (agent.includes("Manager") || agent.includes("Peer")) return "manager";
  if (agent.includes("Planner") || agent.includes("Study")) return "planner";
  if (agent.includes("Engagement")) return "engagement";
  return "neutral";
};

export function TraceConsole({ traces }: TraceConsoleProps) {
  return (
    <section className="panel trace-panel">
      <div className="section-heading">
        <div>
          <p>Guardrails</p>
          <h2>Live agent trace console</h2>
        </div>
        <span>{traces.length} events</span>
      </div>

      <div className="trace-list">
        {traces.length === 0 ? (
          <p className="empty-state">Run the learner pipeline to inspect agent traces and audits.</p>
        ) : (
          traces.map((trace, index) => (
            <article className={`trace-row ${toneForAgent(trace.agent)}`} key={`${trace.agent}-${index}`}>
              <strong>[{trace.agent}]</strong>
              <span>{trace.content}</span>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
