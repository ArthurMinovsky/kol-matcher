import type { Recommendation, BrandProfile } from '@/lib/types'
import { CreatorCard } from './creator-card'

export function RecommendationTable({
  recommendations,
  brand,
}: {
  recommendations: Recommendation[]
  brand: BrandProfile
}) {
  return (
    <section className="panel">
      <h2>Top {recommendations.length} KOL Recommendations</h2>
      <div className="recommendation-list">
        {recommendations.map((rec) => (
          <CreatorCard key={rec.creator.username} rec={rec} brand={brand} />
        ))}
      </div>
    </section>
  )
}
