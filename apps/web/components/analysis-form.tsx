'use client'

import { useState } from 'react'

export function AnalysisForm({
  onAnalyze,
  loading,
}: {
  onAnalyze: (payload: { brand_name: string; facebook_url: string; campaign_goal: string; website_url?: string }) => void
  loading: boolean
}) {
  const [brandName, setBrandName] = useState('')
  const [facebookUrl, setFacebookUrl] = useState('')
  const [campaignGoal, setCampaignGoal] = useState('product review')
  const [websiteUrl, setWebsiteUrl] = useState('')

  const goals = ['product review', 'awareness', 'conversion', 'launch']

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
          <label htmlFor="brand-name">Brand name</label>
          <input
            id="brand-name"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            placeholder="e.g. Dr. Pong Clinic"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="facebook-url">Facebook page URL</label>
          <input
            id="facebook-url"
            type="url"
            value={facebookUrl}
            onChange={(e) => setFacebookUrl(e.target.value)}
            placeholder="https://www.facebook.com/drpongclinic"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="campaign-goal">Campaign goal</label>
          <select id="campaign-goal" value={campaignGoal} onChange={(e) => setCampaignGoal(e.target.value)}>
            {goals.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <details className="optional-site">
          <summary>Optional: website URL</summary>
            <input
              id="website-url"
            type="url"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </details>

        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze & Find KOLs'}
        </button>

        <div className="demo-hint">
          <button
            type="button"
            className="btn-link"
            onClick={() => {
              setBrandName('Dr. Pong Clinic')
              setFacebookUrl('https://www.facebook.com/drpongclinic')
            }}
            disabled={loading}
          >
            Try Dr. Pong test case →
          </button>
        </div>
      </form>
    </section>
  )
}
