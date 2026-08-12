import type { AnalyzeResponse } from '@/lib/types'

const statusColor: Record<string, string> = {
  LIVE: 'status-live',
  CACHED: 'status-cached',
  PARTIAL: 'status-partial',
  FAILED: 'status-failed',
}

export function SourceStatus({
  status,
  provenance,
}: {
  status: AnalyzeResponse['source_status']
  provenance?: AnalyzeResponse['provider_provenance']
}) {
  return (
    <section className="panel compact">
      <div className="source-strip">
        {Object.entries(status).map(([key, value]) => (
          <div key={key} className={`source-badge ${statusColor[value] || 'status-failed'}`}>
            <span className="source-key">{key}</span>
            <span className="source-value">{value}</span>
          </div>
        ))}
      </div>
      {provenance && (
        <div className="source-provenance" aria-label="Provider provenance">
          {Object.entries(provenance).map(([key, value]) => (
            <span key={key}>{key}: {value}</span>
          ))}
        </div>
      )}
    </section>
  )
}
