import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: ReactNode;
  tone?: "blue" | "green" | "amber" | "red" | "neutral";
  helper?: string;
};

export function StatCard({ label, value, tone = "neutral", helper }: StatCardProps) {
  return (
    <section className={`stat-card ${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      {helper ? <span>{helper}</span> : null}
    </section>
  );
}
