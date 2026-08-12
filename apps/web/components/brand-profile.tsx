import type { BrandProfile } from '@/lib/types'

export function BrandProfilePanel({ brand }: { brand: BrandProfile }) {
  const badge =
    brand.extraction_method === 'heuristic'
      ? { text: 'Low-confidence heuristic profile', cls: 'badge-warn' }
      : brand.extraction_method === 'llm'
      ? { text: 'AI-inferred from inputs', cls: 'badge-info' }
      : { text: 'Committed fixture profile', cls: 'badge-ok' }

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Brand Intelligence</h2>
        <span className={`badge ${badge.cls}`}>{badge.text}</span>
      </div>
      <h3>{brand.brand_name}</h3>
      {brand.industry && <p className="meta">{brand.industry}</p>}
      {brand.description && <p>{brand.description}</p>}
      {brand.analysis_rationale && (
        <p className="rationale">
          <strong>Analysis rationale:</strong> {brand.analysis_rationale}
        </p>
      )}

      <div className="tag-grid">
        <div>
          <span className="tag-label">Topics</span>
          <div className="tags">
            {brand.topics.map((t) => (
              <span key={t} className="tag">{t}</span>
            ))}
          </div>
        </div>
        <div>
          <span className="tag-label">Style tags</span>
          <div className="tags">
            {brand.content_styles.map((t) => (
              <span key={t} className="tag">{t}</span>
            ))}
          </div>
        </div>
        <div>
          <span className="tag-label">Desired styles</span>
          <div className="tags">
            {brand.desired_style_tags.map((t) => (
              <span key={t} className="tag tag-accent">{t}</span>
            ))}
          </div>
        </div>
        {brand.thai_keywords && brand.thai_keywords.length > 0 && (
          <div>
            <span className="tag-label">Thai Keywords</span>
            <div className="tags">
              {brand.thai_keywords.map((t) => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
          </div>
        )}
        {brand.english_keywords && brand.english_keywords.length > 0 && (
          <div>
            <span className="tag-label">English Keywords</span>
            <div className="tags">
              {brand.english_keywords.map((t) => (
                <span key={t} className="tag">{t}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {brand.audience_hypothesis && (
        <p className="hypothesis">
          <strong>Audience hypothesis:</strong> {brand.audience_hypothesis}
        </p>
      )}
    </section>
  )
}
