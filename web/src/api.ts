import type {
  AssessmentResult,
  Health,
  LearnerOption,
  LearnerWorkspace,
  ManagerInsights,
  ReportFile
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<Health>("/health");
}

export function getLearners() {
  return request<LearnerOption[]>("/api/learners");
}

export function runLearnerWorkspace(employeeId: string, textInput: string, weeks: number) {
  return request<LearnerWorkspace>("/api/learner/workspace", {
    method: "POST",
    body: JSON.stringify({
      employee_id: employeeId,
      text_input: textInput,
      weeks
    })
  });
}

export function submitAssessment(
  employeeId: string,
  textInput: string,
  answers: Record<string, number>
) {
  return request<AssessmentResult>("/api/learner/assessment/submit", {
    method: "POST",
    body: JSON.stringify({
      employee_id: employeeId,
      text_input: textInput,
      answers
    })
  });
}

export function getManagerInsights() {
  return request<ManagerInsights>("/api/manager/insights", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function getReports() {
  return request<ReportFile[]>("/api/reports");
}
