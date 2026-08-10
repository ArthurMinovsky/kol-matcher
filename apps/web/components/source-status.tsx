import type { AnalyzeResponse } from '@/lib/types'

const statusColor: Record<string, string> = {
  LIVE: 'status-live',
  CACHED: 'status-cached',
  PARTIAL: 'status-partial',
  FAILED: 'status-failed',
}

export function SourceStatus({ status }: { status: AnalyzeResponse['source_status'] }) {
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
    </section>
  )
}
