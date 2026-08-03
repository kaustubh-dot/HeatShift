import { useCallback, useEffect, useRef, useState } from "react";

export const PLAN_TRANSFORMATION_TIMINGS = {
  kickoff: 0,
  highlight: 300,
  transform: 500,
  settle: 250,
} as const;

export type TransformationPhase = "baseline" | "highlight" | "transforming" | "settled";

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;
}

export function usePlanTransformation(): {
  phase: TransformationPhase;
  replay: () => void;
} {
  const [reducedMotion, setReducedMotion] = useState(prefersReducedMotion);
  const [phase, setPhase] = useState<TransformationPhase>(() => (prefersReducedMotion() ? "settled" : "baseline"));
  const timers = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    for (const timer of timers.current) window.clearTimeout(timer);
    timers.current = [];
  }, []);

  const replay = useCallback(() => {
    clearTimers();
    if (reducedMotion) {
      setPhase("settled");
      return;
    }

    setPhase("highlight");
    timers.current.push(
      window.setTimeout(() => {
        setPhase("transforming");
        timers.current.push(
          window.setTimeout(() => {
            setPhase("settled");
          }, PLAN_TRANSFORMATION_TIMINGS.transform + PLAN_TRANSFORMATION_TIMINGS.settle),
        );
      }, PLAN_TRANSFORMATION_TIMINGS.highlight),
    );
  }, [clearTimers, reducedMotion]);

  useEffect(() => {
    const mediaQuery = typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(prefers-reduced-motion: reduce)")
      : null;
    const handleChange = () => setReducedMotion(mediaQuery?.matches ?? false);
    mediaQuery?.addEventListener?.("change", handleChange);
    return () => mediaQuery?.removeEventListener?.("change", handleChange);
  }, []);

  useEffect(() => {
    clearTimers();
    if (reducedMotion) {
      setPhase("settled");
      return () => clearTimers();
    }

    const kickoff = window.setTimeout(replay, PLAN_TRANSFORMATION_TIMINGS.kickoff);
    timers.current.push(kickoff);
    return () => clearTimers();
  }, [clearTimers, reducedMotion, replay]);

  return { phase, replay };
}
