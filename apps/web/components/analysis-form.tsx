'use client'

import { useState } from 'react'

export function AnalysisForm({
  onAnalyze,
  onDemo,
  loading,
}: {
  onAnalyze: (payload: { brand_name: string; facebook_url: string; campaign_goal: string; website_url?: string }) => void
  onDemo: () => void
  loading: boolean
}) {
  const [brandName, setBrandName] = useState('')
  const [facebookUrl, setFacebookUrl] = useState('')
  const [campaignGoal, setCampaignGoal] = useState('educational skincare')
  const [websiteUrl, setWebsiteUrl] = useState('')

  const goals = ['educational skincare', 'product review', 'awareness', 'conversion', 'launch']

  return (
    <section className="finder-card">
      <div className="card-head">
        <div>
          <h2 id="finder-title">Find TikTok KOLs for your brand</h2>
          <p className="card-sub">Enter your brand name and Facebook page to get started.</p>
        </div>
        <span className="beta-pill">BETA</span>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          onAnalyze({ brand_name: brandName, facebook_url: facebookUrl, campaign_goal: campaignGoal, website_url: websiteUrl })
        }}
      >
        <div className="field">
          <label>Brand name</label>
          <input
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            placeholder="e.g. Dr. Pong Clinic"
            required
          />
        </div>

        <div className="field">
          <label>Facebook page URL</label>
          <input
            type="url"
            value={facebookUrl}
            onChange={(e) => setFacebookUrl(e.target.value)}
            placeholder="https://www.facebook.com/drpongclinic"
            required
          />
        </div>

        <div className="field">
          <label>Campaign goal</label>
          <select value={campaignGoal} onChange={(e) => setCampaignGoal(e.target.value)}>
            {goals.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <details className="optional-site">
          <summary>Optional: website URL</summary>
          <input
            type="url"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </details>

        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze & Find KOLs'}
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            setBrandName('Dr. Pong Clinic')
            setFacebookUrl('https://www.facebook.com/drpongclinic')
            setCampaignGoal('educational skincare')
            onDemo()
          }}
          disabled={loading}
        >
          Load Dr. Pong Demo
        </button>
      </form>
    </section>
  )
}
