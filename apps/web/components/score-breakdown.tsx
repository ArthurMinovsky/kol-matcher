import type { Recommendation } from '@/lib/types'

export function ScoreBreakdown({ rec }: { rec: Recommendation }) {
  const bars = [
    { label: 'Combined Relevance', value: rec.relevance, weight: 45 },
    { label: 'Engagement', value: rec.engagement, weight: 25 },
    { label: 'Thailand', value: rec.thailand_relevance, weight: 15 },
    { label: 'Style Fit', value: rec.style_fit, weight: 15 },
  ]

  const bm25Evidence = rec.scoring_evidence?.find(
    (e) => e.signal === 'BM25 Content Match'
  )
  const llmEvidence = rec.scoring_evidence?.find(
    (e) => e.signal === 'LLM Judge Relevance'
  )
  const bm25Available = bm25Evidence?.available ?? rec.bm25_relevance > 0
  const llmAvailable = llmEvidence?.available ?? false

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
      <div className="score-row sub-score">
        <span>
          └ BM25 <small>(20%)</small>{!bm25Available && <small> · unavailable</small>}
        </span>
        <div className="bar">
          <div
            className="bar-fill secondary"
            style={{ width: `${rec.bm25_relevance}%` }}
          />
        </div>
        <span>{rec.bm25_relevance.toFixed(0)}</span>
      </div>
      <div className="score-row sub-score">
        <span>
          └ LLM Judge <small>(25%)</small>{!llmAvailable && <small> · unavailable</small>}
        </span>
        <div className="bar">
          <div
            className="bar-fill secondary"
            style={{ width: `${rec.llm_relevance}%` }}
          />
        </div>
        <span>{rec.llm_relevance.toFixed(0)}</span>
      </div>
      {bm25Evidence?.matched_keywords && bm25Evidence.matched_keywords.length > 0 && (
        <div className="keyword-tags">
          {bm25Evidence.matched_keywords.map((kw) => (
            <span key={kw} className="keyword-pill">{kw}</span>
          ))}
        </div>
      )}
    </div>
  )
}
