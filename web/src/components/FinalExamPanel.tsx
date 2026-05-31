import { AlertCircle, CheckCircle2, Clock, Flag, RotateCcw, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getFinalExam, submitAssessment } from "../api";
import type { AssessmentResult, LearnerOption, Quiz } from "../types";
import { TooltipButton } from "./TooltipButton";

type FinalExamPanelProps = {
  selectedLearner?: LearnerOption;
  prompt: string;
  onAssessmentComplete?: () => void | Promise<void>;
};

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
}

function examTypeLabel(quiz: Quiz | null) {
  if (!quiz) return "Final exam simulator";
  if (quiz.question_count_standard?.toLowerCase().includes("fundamentals")) return "Fundamentals exam simulation";
  if (quiz.question_count_standard?.toLowerCase().includes("mos")) return "MOS exam simulation";
  return "Role-based exam simulation";
}

function FinalExamResult({ result }: { result: AssessmentResult }) {
  return (
    <section className={`final-result ${result.passed ? "pass" : "retry"}`}>
      {result.passed ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
      <div>
        <p>{result.passed ? "Final simulator passed" : "Final simulator needs remediation"}</p>
        <h3>{Math.round(result.score_percentage)}%</h3>
        <span>
          {result.booking_recommendation}.{" "}
          {result.badge_name ? `Badge unlocked: ${result.badge_name}` : result.remediation_plan}
        </span>
      </div>
    </section>
  );
}

export function FinalExamPanel({ selectedLearner, prompt, onAssessmentComplete }: FinalExamPanelProps) {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [flagged, setFlagged] = useState<Record<string, boolean>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = quiz?.questions[currentIndex];
  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const flaggedCount = useMemo(() => Object.values(flagged).filter(Boolean).length, [flagged]);

  useEffect(() => {
    if (!quiz || result) return;
    const timer = window.setInterval(() => {
      setRemainingSeconds((current) => Math.max(0, current - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [quiz, result]);

  useEffect(() => {
    if (quiz && remainingSeconds === 0 && !result && answeredCount > 0) {
      void submit();
    }
  }, [remainingSeconds]);

  const startExam = async () => {
    if (!selectedLearner) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});
    setFlagged({});
    setCurrentIndex(0);
    try {
      const data = await getFinalExam(selectedLearner.employee_id, prompt);
      setQuiz(data);
      setRemainingSeconds((data.duration_minutes ?? 45) * 60);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start final exam simulator");
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    if (!selectedLearner || !quiz || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const assessmentResult = await submitAssessment(selectedLearner.employee_id, prompt, answers, "final");
      setResult(assessmentResult);
      await onAssessmentComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Final exam submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const resetExam = () => {
    setQuiz(null);
    setAnswers({});
    setFlagged({});
    setCurrentIndex(0);
    setRemainingSeconds(0);
    setResult(null);
    setError(null);
  };

  return (
    <div className="exam-grid">
      <section className="command-strip exam-command">
        <div>
          <p>Certification readiness</p>
          <h2>{selectedLearner ? `${selectedLearner.name} - ${selectedLearner.certification_target}` : "Select a worker"}</h2>
          <span>
            Start a timed final exam simulator after class checkpoints and study-plan work. The question count and timer follow
            Microsoft-style exam categories while staying synthetic for demo safety.
          </span>
        </div>
        <TooltipButton
          tooltip="Generate a timed final exam simulator for the selected worker"
          icon={<Clock size={18} />}
          variant="primary"
          onClick={startExam}
          disabled={!selectedLearner || loading}
        >
          {loading ? "Preparing exam" : "Start final exam"}
        </TooltipButton>
      </section>

      <section className="panel exam-simulator">
        <div className="exam-header">
          <div>
            <p>{examTypeLabel(quiz)}</p>
            <h2>{quiz?.certification_target ?? "Final exam simulator"}</h2>
          </div>
          <div className="exam-clock">
            <Clock size={18} />
            <strong>{quiz ? formatTime(remainingSeconds) : "--:--"}</strong>
            <span>{quiz?.duration_minutes ?? "-"} min exam</span>
          </div>
        </div>

        <div className="exam-meta-strip">
          <span>{quiz?.question_count_standard ?? "40-60 questions for most certification exams"}</span>
          <span>{quiz ? `${quiz.seat_minutes} min seat time` : "Seat time includes instructions and comments"}</span>
          <span>{answeredCount}/{quiz?.questions.length ?? 0} answered</span>
          <span>{flaggedCount} flagged</span>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}

        {!quiz ? (
          <div className="empty-state exam-empty">
            Select a worker, run the learning workspace if you want preparation evidence, then start the final exam simulator.
          </div>
        ) : currentQuestion ? (
          <div className="exam-body">
            <aside className="exam-question-nav" aria-label="Question navigation">
              {quiz.questions.map((question, index) => {
                const key = String(question.question_id);
                const isAnswered = answers[key] !== undefined;
                return (
                  <button
                    className={`${index === currentIndex ? "active" : ""} ${isAnswered ? "answered" : ""} ${flagged[key] ? "flagged" : ""}`}
                    key={question.question_id}
                    type="button"
                    onClick={() => setCurrentIndex(index)}
                    aria-label={`Question ${index + 1}${isAnswered ? ", answered" : ""}${flagged[key] ? ", flagged" : ""}`}
                  >
                    {index + 1}
                  </button>
                );
              })}
            </aside>

            <article className="exam-question-card">
              <div className="question-meta">
                <span>Q{currentIndex + 1}</span>
                <small>{currentQuestion.domain}</small>
              </div>
              <h3>{currentQuestion.question_text}</h3>
              <div className="option-list">
                {currentQuestion.options.map((option, index) => (
                  <label className="option-row" key={option}>
                    <input
                      type="radio"
                      name={`final-question-${currentQuestion.question_id}`}
                      checked={answers[String(currentQuestion.question_id)] === index}
                      onChange={() =>
                        setAnswers((current) => ({ ...current, [String(currentQuestion.question_id)]: index }))
                      }
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>

              <div className="exam-actions">
                <TooltipButton
                  tooltip="Flag this question for review before submitting"
                  icon={<Flag size={16} />}
                  variant={flagged[String(currentQuestion.question_id)] ? "secondary" : "ghost"}
                  onClick={() =>
                    setFlagged((current) => ({
                      ...current,
                      [String(currentQuestion.question_id)]: !current[String(currentQuestion.question_id)]
                    }))
                  }
                >
                  {flagged[String(currentQuestion.question_id)] ? "Flagged" : "Flag"}
                </TooltipButton>
                <TooltipButton
                  tooltip="Move to the previous question"
                  variant="secondary"
                  onClick={() => setCurrentIndex((current) => Math.max(0, current - 1))}
                  disabled={currentIndex === 0}
                >
                  Previous
                </TooltipButton>
                <TooltipButton
                  tooltip="Move to the next question"
                  variant="secondary"
                  onClick={() => setCurrentIndex((current) => Math.min((quiz?.questions.length ?? 1) - 1, current + 1))}
                  disabled={currentIndex === quiz.questions.length - 1}
                >
                  Next
                </TooltipButton>
              </div>
            </article>
          </div>
        ) : null}

        {result ? <FinalExamResult result={result} /> : null}

        {quiz ? (
          <div className="button-row">
            <TooltipButton
              tooltip="Fill every question with the correct demo answer"
              icon={<CheckCircle2 size={16} />}
              variant="secondary"
              onClick={() => {
                const correctAnswers = Object.fromEntries(
                  quiz.questions.map((question) => [String(question.question_id), question.correct_option_index])
                );
                setAnswers(correctAnswers);
              }}
            >
              Fill demo pass
            </TooltipButton>
            <TooltipButton tooltip="Reset the current final exam attempt" icon={<RotateCcw size={16} />} variant="ghost" onClick={resetExam}>
              Reset
            </TooltipButton>
            <TooltipButton
              tooltip="Submit final exam answers and calculate badge eligibility"
              icon={<Send size={16} />}
              variant="primary"
              onClick={submit}
              disabled={submitting || answeredCount === 0}
            >
              {submitting ? "Submitting" : "Submit final exam"}
            </TooltipButton>
          </div>
        ) : null}
      </section>
    </div>
  );
}
