import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import type { AppView } from "../types";
import { TooltipButton } from "./TooltipButton";

type TourStep = {
  selector: string;
  view: AppView;
  eyebrow: string;
  title: string;
  body: string;
};

type GuidedTourProps = {
  active: boolean;
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  onClose: () => void;
};

const tourSteps: TourStep[] = [
  {
    selector: '[data-tour="view-nav"]',
    view: "learner",
    eyebrow: "Orientation",
    title: "Two judging paths",
    body: "Use Intern Space to demo the learner journey, then Manager Portal to show cohort analytics and intervention signals."
  },
  {
    selector: '[data-tour="learner-controls"]',
    view: "learner",
    eyebrow: "Input controls",
    title: "Pick the intern and plan length",
    body: "Judges can switch the synthetic learner persona and study duration to see how the pipeline adapts its recommendations."
  },
  {
    selector: '[data-tour="agent-pipeline"]',
    view: "learner",
    eyebrow: "Core workflow",
    title: "Run the learner agent pipeline",
    body: "This starts profiling, course curation, scheduling, assessment, activity verification, booking guidance, and trace logging."
  },
  {
    selector: '[data-tour="pipeline-stages"]',
    view: "learner",
    eyebrow: "What it means",
    title: "Follow the reasoning stages",
    body: "The stage rail shows how Reazon turns learner context into a workload-aware certification plan and badge decision."
  },
  {
    selector: '[data-tour="manager-command"]',
    view: "manager",
    eyebrow: "Manager view",
    title: "Refresh cohort intelligence",
    body: "This portal summarizes readiness, risk, buddy matches, and remediation comments so program leads know where to help."
  },
  {
    selector: '[data-tour="report-evidence"]',
    view: "manager",
    eyebrow: "Evidence",
    title: "Open generated PDFs",
    body: "Reports provide judge-friendly proof of outputs, including readiness summaries, study plans, and badge certificates."
  }
];

export function GuidedTour({ active, activeView, onViewChange, onClose }: GuidedTourProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const step = tourSteps[stepIndex];

  useEffect(() => {
    if (active) {
      setStepIndex(0);
    }
  }, [active]);

  useEffect(() => {
    if (!active || !step) return;
    if (activeView !== step.view) {
      onViewChange(step.view);
      return;
    }

    const updateTarget = () => {
      const target = document.querySelector(step.selector);
      if (target) {
        target.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
        window.setTimeout(() => setTargetRect(target.getBoundingClientRect()), 180);
      } else {
        setTargetRect(null);
      }
    };

    updateTarget();
    window.addEventListener("resize", updateTarget);
    window.addEventListener("scroll", updateTarget, true);
    return () => {
      window.removeEventListener("resize", updateTarget);
      window.removeEventListener("scroll", updateTarget, true);
    };
  }, [active, activeView, onViewChange, step]);

  const spotlightStyle = useMemo(() => {
    if (!targetRect) return undefined;
    return {
      inlineSize: targetRect.width + 16,
      blockSize: targetRect.height + 16,
      insetInlineStart: targetRect.left - 8,
      insetBlockStart: targetRect.top - 8
    };
  }, [targetRect]);

  const cardStyle = useMemo(() => {
    if (!targetRect) return undefined;
    const roomBelow = window.innerHeight - targetRect.bottom;
    const top = roomBelow > 220 ? targetRect.bottom + 18 : Math.max(18, targetRect.top - 238);
    const left = Math.min(Math.max(18, targetRect.left), window.innerWidth - 378);
    return { insetBlockStart: top, insetInlineStart: left };
  }, [targetRect]);

  if (!active || !step) return null;

  const isLastStep = stepIndex === tourSteps.length - 1;
  const next = () => {
    if (isLastStep) {
      onClose();
      return;
    }
    setStepIndex((current) => current + 1);
  };

  return (
    <div className="guided-tour" role="dialog" aria-modal="true" aria-labelledby="guided-tour-title">
      <div className="tour-scrim" />
      {spotlightStyle ? <div className="tour-spotlight" style={spotlightStyle} /> : null}
      <section className="tour-card" style={cardStyle}>
        <div className="tour-card-header">
          <div>
            <p>{step.eyebrow}</p>
            <h2 id="guided-tour-title">{step.title}</h2>
          </div>
          <TooltipButton tooltip="Skip guided tour" icon={<X size={16} />} variant="ghost" onClick={onClose} />
        </div>
        <p className="tour-body">{step.body}</p>
        <div className="tour-progress" aria-label={`Step ${stepIndex + 1} of ${tourSteps.length}`}>
          {tourSteps.map((item, index) => (
            <span className={index === stepIndex ? "active" : ""} key={item.title} />
          ))}
        </div>
        <div className="tour-actions">
          <button className="tour-skip" type="button" onClick={onClose}>
            Skip
          </button>
          <button className="tour-next" type="button" onClick={next}>
            {isLastStep ? "Finish" : "Next"}
          </button>
        </div>
      </section>
    </div>
  );
}
