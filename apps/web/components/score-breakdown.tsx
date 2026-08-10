import type { Recommendation } from '@/lib/types'

export function ScoreBreakdown({ rec }: { rec: Recommendation }) {
  const bars = [
    { label: 'Relevance', value: rec.relevance, weight: 45 },
    { label: 'Engagement', value: rec.engagement, weight: 25 },
    { label: 'Thailand', value: rec.thailand_relevance, weight: 15 },
    { label: 'Style Fit', value: rec.style_fit, weight: 15 },
  ]

  const keywordEvidence = rec.scoring_evidence?.find(
    (e) => e.signal === 'Keyword Match'
  )
  const llmEvidence = rec.scoring_evidence?.find(
    (e) => e.signal === 'LLM Judge'
  )

  return (
    <div className="score-breakdown">
      {bars.map((b) => (
        <div key={b.label} className="score-row">
          <span>
            {b.label} <small>({b.weight}%)</small>
          </span>
          <div className="bar">
            <div className="bar-fill" style={{ width: `${b.value}%` }} />
          </div>
          <span>{b.value.toFixed(0)}</span>
        </div>
      ))}
      {keywordEvidence && (
        <div className="score-row sub-score">
          <span>
            └ Keyword Match <small>(25%)</small>
          </span>
          <div className="bar">
            <div
              className="bar-fill secondary"
              style={{ width: `${parseFloat(keywordEvidence.value)}%` }}
            />
          </div>
          <span>{parseFloat(keywordEvidence.value).toFixed(0)}</span>
        </div>
      )}
      {llmEvidence && (
        <div className="score-row sub-score">
          <span>
            └ LLM Judge <small>(20%)</small>
          </span>
          <div className="bar">
            <div
              className="bar-fill secondary"
              style={{ width: `${parseFloat(llmEvidence.value)}%` }}
            />
          </div>
          <span>{parseFloat(llmEvidence.value).toFixed(0)}</span>
        </div>
      )}
    </div>
  )
}
