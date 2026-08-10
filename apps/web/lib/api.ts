import type { AnalyzeResponse } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export async function analyzeBrand(payload: {
  brand_name: string
  facebook_url: string
  campaign_goal: string
  website_url?: string
}): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export async function loadDrPongDemo(): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/api/demo/drpong?top_n=15`)
  if (!res.ok) throw new Error('Demo request failed')
  return res.json()
}
