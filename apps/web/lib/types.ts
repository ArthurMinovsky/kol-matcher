export type SourceState = 'LIVE' | 'CACHED' | 'PARTIAL' | 'FAILED'

export interface BrandProfile {
  brand_name: string
  industry?: string | null
  description?: string | null
  products: string[]
  audience_hypothesis?: string | null
  topics: string[]
  tone?: string | null
  content_styles: string[]
  thai_keywords: string[]
  english_keywords: string[]
  campaign_goal?: string | null
  website_url?: string | null
  facebook_url?: string | null
  desired_style_tags: string[]
  extraction_method: 'fixture' | 'llm' | 'heuristic'
  analysis_rationale?: string | null
}

export interface CreatorProfile {
  username: string
  display_name?: string | null
  bio?: string | null
  tiktok_url?: string | null
  follower_count?: number | null
  topic_tags: string[]
  style_tags: string[]
  source_type: string
}

export interface ScoringEvidence {
  signal: string
  value: string
  source?: string | null
  weight?: number | null
  available?: boolean
  matched_keywords?: string[] | null
  algorithm_key?: string | null
  raw_score?: number | null
}

export interface Recommendation {
  rank: number
  creator: CreatorProfile
  match_score: number
  bm25_relevance: number
  llm_relevance: number
  relevance: number
  engagement: number
  thailand_relevance: number
  style_fit: number
  evidence_coverage: number
  audience_verification: string
  recommendation_confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  rationale: string
  explanation: string
  limitations: string[]
  scoring_evidence?: ScoringEvidence[] | null
}

export interface AnalyzeResponse {
  brand_profile: BrandProfile
  recommendations: Recommendation[]
  source_status: Record<string, SourceState>
  provider_provenance?: Record<string, string>
  limitations: string[]
}
