import type { ScoreBreakdown } from "@/lib/types";

function scoreTone(score: number) {
  if (score >= 75) return "high";
  if (score >= 55) return "medium";
  return "low";
}

export function Score({ score, breakdown }: { score: number; breakdown: ScoreBreakdown }) {
  return (
    <details className="score-details">
      <summary aria-label={`Lead score ${score} out of 100. Open explanation`}>
        <span className={`score-ring ${scoreTone(score)}`} style={{ "--score": score } as React.CSSProperties}><strong>{score}</strong></span>
      </summary>
      <div className="score-popover">
        <strong>Why this score</strong>
        {breakdown.reasons.map((reason) => <span key={reason}>{reason}</span>)}
      </div>
    </details>
  );
}
