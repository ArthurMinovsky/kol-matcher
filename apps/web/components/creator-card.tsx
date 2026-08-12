'use client'

import { useState } from 'react'
import type { Recommendation, BrandProfile } from '@/lib/types'
import { ScoreBreakdown } from './score-breakdown'

export function CreatorCard({ rec, brand }: { rec: Recommendation; brand: BrandProfile }) {
  const [open, setOpen] = useState(false)
  const c = rec.creator
  return (
    <article className="creator-card">
      <div className="creator-summary">
        <button
          type="button"
          className="creator-toggle"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          <div className="rank">#{rec.rank}</div>
          <div className="creator-name">
            <strong>{c.display_name || c.username}</strong>
            <span className="username">@{c.username}</span>
          </div>
          <div className="match-score">{rec.match_score.toFixed(1)}</div>
        </button>
        {c.tiktok_url && (
          <a className="creator-link" href={c.tiktok_url} target="_blank" rel="noreferrer">
            TikTok ↗
          </a>
        )}
      </div>

      {open && (
        <div className="creator-detail">
          <p className="rationale">
            <strong>Why this match:</strong> {rec.rationale}
          </p>
          <ScoreBreakdown rec={rec} />
          <p className="explanation">{rec.explanation}</p>
          <ul className="limitations">
            {rec.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
          <div className="trust-row">
            <span className="trust-pill">Coverage: {rec.evidence_coverage.toFixed(0)}%</span>
            <span className="trust-pill">Audience: {rec.audience_verification}</span>
            <span className="trust-pill">Confidence: {rec.recommendation_confidence}</span>
            <span className="trust-pill">Source: {c.source_type}</span>
          </div>
        </div>
      )}
    </article>
  )
}
