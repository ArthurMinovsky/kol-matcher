'use client'

import { useState } from 'react'
import { AnalysisForm } from '@/components/analysis-form'
import { BrandProfilePanel } from '@/components/brand-profile'
import { RecommendationTable } from '@/components/recommendation-table'
import { SourceStatus } from '@/components/source-status'
import { analyzeBrand } from '@/lib/api'
import type { AnalyzeResponse } from '@/lib/types'

export default function Home() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runAnalyze = async (payload: Parameters<typeof analyzeBrand>[0]) => {
    setLoading(true)
    setError(null)
    try {
      const data = await analyzeBrand(payload)
      setResult(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-dot"></span> TikTok KOL matching · beta</div>
          <h1>Find Thai TikTok creators that fit your <span className="highlight">brand.</span></h1>
          <p>Enter your brand name and Facebook page. The demo ranks creators deterministically with explainable scores.</p>
        </div>
        <AnalysisForm onAnalyze={runAnalyze} loading={loading} />
      </section>

      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="loading">Analyzing…</div>}

      {result && (
        <>
          <BrandProfilePanel brand={result.brand_profile} />
          <SourceStatus status={result.source_status} provenance={result.provider_provenance} />
          <RecommendationTable recommendations={result.recommendations} brand={result.brand_profile} />
        </>
      )}
    </main>
  )
}
