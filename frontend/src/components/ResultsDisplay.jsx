import { useMemo } from 'react'
import ListingCard from './ListingCard'

export default function ResultsDisplay({
  results,
  sortBy,
  setSortBy,
  filterStatus,
  setFilterStatus,
}) {
  const sortedAndFiltered = useMemo(() => {
    let listings = []

    if (filterStatus === 'sold' || filterStatus === 'both') {
      listings = [...results.sold_listings]
    }

    if (filterStatus === 'unsold' || filterStatus === 'both') {
      listings = [...listings, ...results.unsold_listings]
    }

    // Sort listings
    if (sortBy === 'price-asc') {
      listings.sort((a, b) => a.price - b.price)
    } else if (sortBy === 'price-desc') {
      listings.sort((a, b) => b.price - a.price)
    }

    return listings
  }, [results, sortBy, filterStatus])

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Search Results: "{results.query_used}"</h2>
      </div>

      <div className="filter-bar">
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="price-asc">Price: Low to High</option>
          <option value="price-desc">Price: High to Low</option>
        </select>

        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="sold">Sold Only</option>
          <option value="unsold">Unsold Only</option>
          {results.unsold_listings.length > 0 && (
            <option value="both">All Listings</option>
          )}
        </select>
      </div>

      {sortedAndFiltered.length > 0 ? (
        <div className="listings-grid">
          {sortedAndFiltered.map((listing) => (
            <ListingCard
              key={listing.listing_url}
              listing={listing}
            />
          ))}
        </div>
      ) : (
        <div className="no-results">
          <p>No listings found</p>
        </div>
      )}

      {results.unsold_listings.length > 0 && filterStatus === 'sold' && (
        <p style={{ textAlign: 'center', color: '#666', marginTop: '1rem' }}>
          💡 {results.unsold_listings.length} unsold listings available. Select "All Listings" to view them.
        </p>
      )}
    </div>
  )
}
