export type LearnerOption = {
  learner_id: string;
  employee_id: string;
  name: string;
  role: string;
  certification_target: string;
  practice_score_avg: number;
  hours_studied: number;
  exam_outcome: string;
  status: string;
};

export type LearnerProfile = LearnerOption & {
  meeting_hours_per_week: number;
  focus_hours_per_week: number;
  preferred_learning_slot: string;
  weekly_study_budget_hours: number;
};

export type StudyWeek = {
  week_number: number;
  focus_domains: string[];
  hours_allocated: number;
  workload_adjusted: boolean;
  adjustment_reason?: string | null;
};

export type StudyPlan = {
  learner_id: string;
  certification_target: string;
  total_weeks: number;
  total_hours: number;
  schedule: StudyWeek[];
};

export type LearningPath = {
  domain_name?: string;
  resource_title?: string;
  resource_url?: string;
  skills_covered?: string[];
  citation?: string;
};

export type EngagementReport = {
  recommended_time?: string;
  preferred_slot?: string;
  reminder_message?: string;
};

export type QuizQuestion = {
  question_id: number;
  domain: string;
  question_text: string;
  options: string[];
  correct_option_index: number;
  citation: string;
  explanation: string;
};

export type Quiz = {
  quiz_id: string;
  learner_id: string;
  certification_target: string;
  questions: QuizQuestion[];
};

export type LearningActivityReport = {
  learner_id: string;
  certification_target: string;
  completed_modules: number;
  total_modules: number;
  average_completion_confidence: number;
  weak_domains: string[];
  evidence_summary: string[];
  recommendation: string;
};

export type Badge = {
  badge_id: string;
  name: string;
  certification_target: string;
  issued_to: string;
  score: number;
  criteria: string;
};

export type Trace = {
  agent: string;
  content: string;
};

export type LearnerWorkspace = {
  session_id: string;
  profile: LearnerProfile;
  learning_paths: LearningPath[];
  plan: StudyPlan;
  engagement: EngagementReport;
  quiz: Quiz;
  activity: LearningActivityReport;
  badges: Badge[];
  traces: Trace[];
};

export type AssessmentResult = {
  score_percentage: number;
  passed: boolean;
  overall_readiness: number;
  booking_recommendation: string;
  remediation_plan: string;
  badge_id?: string | null;
  badge_name?: string | null;
};

export type ManagerInsights = {
  total_learners: number;
  average_readiness: number;
  readiness_by_exam: Record<string, number>;
  at_risk_learners: Array<{
    name: string;
    meeting_hours: number;
    risk_level: string;
    reason: string;
  }>;
  buddy_recommendations: Array<{
    learner_a: string;
    learner_b: string;
    certification_target: string;
    common_slot: string;
  }>;
  learner_comments: Array<{
    name: string;
    certification_target: string;
    missed_count: number;
    penalty_applied: boolean;
    comment: string;
  }>;
};

export type Health = {
  status: string;
  mock_mode: boolean;
};

export type AppView = "learner" | "manager";

export type ReportFile = {
  file_name: string;
  report_type: string;
  learner_id: string;
  certification_target: string;
  size_bytes: number;
  modified_at: string;
  download_url: string;
};
