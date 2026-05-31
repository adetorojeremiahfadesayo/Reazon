import { Download, RefreshCw } from "lucide-react";
import type { ReportFile } from "../types";
import { TooltipButton } from "./TooltipButton";

type ReportListProps = {
  title: string;
  eyebrow: string;
  emptyText: string;
  reports: ReportFile[];
  loading: boolean;
  onRefresh: () => void;
  dataTour?: string;
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ReportList({ title, eyebrow, emptyText, reports, loading, onRefresh, dataTour }: ReportListProps) {
  return (
    <section className="panel embedded-reports" data-tour={dataTour}>
      <div className="section-heading">
        <div>
          <p>{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <TooltipButton
          tooltip="Refresh available PDF evidence from the backend reports folder"
          icon={<RefreshCw size={16} />}
          variant="ghost"
          onClick={onRefresh}
          disabled={loading}
        />
      </div>

      {reports.length === 0 ? (
        <p className="empty-state">{emptyText}</p>
      ) : (
        <div className="report-mini-list">
          {reports.map((report) => (
            <article className="report-mini-row" key={report.file_name}>
              <div>
                <strong>{report.report_type}</strong>
                <span>{report.file_name}</span>
                <small>
                  {report.certification_target} - {formatBytes(report.size_bytes)}
                </small>
              </div>
              <a
                href={report.download_url}
                target="_blank"
                rel="noreferrer"
                title={`Open ${report.file_name}`}
                aria-label={`Open ${report.file_name}`}
              >
                <Download size={16} />
              </a>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
