import { Award, CheckCircle2, RotateCcw, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { submitAssessment } from "../api";
import type { AssessmentResult, Quiz } from "../types";
import { TooltipButton } from "./TooltipButton";

type AssessmentPanelProps = {
  quiz: Quiz;
  employeeId: string;
  textInput: string;
  onAssessmentComplete?: () => void | Promise<void>;
};

type BadgeTier = {
  key: "perfect" | "ready" | "conditional" | "not-ready";
  ribbon: string;
  title: string;
  status: string;
  message: string;
};

function getBadgeTier(score: number): BadgeTier {
  if (score === 100) {
    return {
      key: "perfect",
      ribbon: "Perfect",
      title: "Perfect Score!",
      status: "Status: 100% Mastery",
      message: "You answered every checkpoint question correctly. You are ready to keep moving through the learning plan."
    };
  }

  if (score >= 75) {
    return {
      key: "ready",
      ribbon: "Victory",
      title: "Quiz Completed!",
      status: "Status: Exam Ready",
      message: "You understood this class segment well enough to continue final exam preparation."
    };
  }

  if (score >= 65) {
    return {
      key: "conditional",
      ribbon: "Review",
      title: "Passed With Review",
      status: "Status: Targeted Remediation",
      message: "You crossed the checkpoint threshold. Review weak domains before the next class or final exam simulation."
    };
  }

  return {
    key: "not-ready",
    ribbon: "Retry",
    title: "Not Ready Yet",
    status: "Status: Remediation Needed",
      message: "Your score is below the checkpoint threshold. Revisit this class material, then retake the checkpoint."
  };
}

function ResultBadge({ result }: { result: AssessmentResult }) {
  const tier = getBadgeTier(result.score_percentage);

  return (
    <div className={`result-badge-card ${tier.key}`}>
      <div className="result-badge-orb" aria-hidden="true">
        <div className="result-badge-glow" />
        <div className="result-badge-body">
          <div className="result-badge-ribbon">{tier.ribbon}</div>
          <Award size={48} />
          <strong>{Math.round(result.score_percentage)}%</strong>
        </div>
      </div>

      <div className="result-badge-copy">
        <h3>{tier.title}</h3>
        <p className="result-badge-status">{tier.status}</p>
        <p>{tier.message}</p>
        <small>
          Recommendation: {result.booking_recommendation}. {result.remediation_plan}
        </small>
      </div>
    </div>
  );
}

export function AssessmentPanel({ quiz, employeeId, textInput, onAssessmentComplete }: AssessmentPanelProps) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const assessmentResult = await submitAssessment(employeeId, textInput, answers);
      setResult(assessmentResult);
      await onAssessmentComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assessment submission failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel assessment-panel">
      <div className="section-heading">
        <div>
          <p>Grounded practice</p>
          <h2>Weekly checkpoint</h2>
        </div>
        <span>{answeredCount}/{quiz.questions.length} answered</span>
      </div>

      <div className="quiz-list">
        {quiz.questions.map((question) => (
          <article className="question-block" key={question.question_id}>
            <div className="question-meta">
              <span>Q{question.question_id}</span>
              <small>{question.domain}</small>
            </div>
            <h3>{question.question_text}</h3>
            <div className="option-list">
              {question.options.map((option, index) => (
                <label className="option-row" key={option}>
                  <input
                    type="radio"
                    name={`question-${question.question_id}`}
                    checked={answers[String(question.question_id)] === index}
                    onChange={() =>
                      setAnswers((current) => ({ ...current, [String(question.question_id)]: index }))
                    }
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
            <details>
              <summary>Citation</summary>
              <p>{question.citation}</p>
            </details>
          </article>
        ))}
      </div>

      {error ? <p className="error-banner">{error}</p> : null}

      {result ? <ResultBadge result={result} /> : null}

      <div className="button-row">
        <TooltipButton
          tooltip="Fill the assessment with correct demo answers to preview the passing path"
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
        <TooltipButton
          tooltip="Clear all selected answers and reset the local assessment state"
          icon={<RotateCcw size={16} />}
          variant="ghost"
          onClick={() => {
            setAnswers({});
            setResult(null);
            setError(null);
          }}
        >
          Clear
        </TooltipButton>
        <TooltipButton
          tooltip="Submit selected answers and calculate readiness, booking guidance, and badge eligibility"
          icon={<Send size={16} />}
          variant="primary"
          onClick={submit}
          disabled={loading || answeredCount === 0}
        >
          {loading ? "Submitting" : "Submit checkpoint"}
        </TooltipButton>
      </div>
    </section>
  );
}
