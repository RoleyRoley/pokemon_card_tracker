import { useState } from 'react'

export default function ListingCard({ listing }) {
  const [imageError, setImageError] = useState(false)

  const formatPrice = (amount, currency = 'GBP') => {
    try {
      return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount)
    } catch {
      return `${currency} ${Number(amount).toFixed(2)}`
    }
  }

  return (
    <div className="listing-card">
      <div className="listing-image">
        {listing.image_url && !imageError ? (
          <img
            src={listing.image_url}
            alt={listing.title}
            onError={() => setImageError(true)}
          />
        ) : (
          '🎴'
        )}
        <div className={`listing-status ${listing.sold ? '' : 'unsold'}`}>
          {listing.sold ? 'SOLD' : 'ACTIVE'}
        </div>
      </div>

      <div className="listing-content">
        <div className="listing-title">{listing.title}</div>
        <div className="listing-price">{formatPrice(listing.price, listing.currency || 'GBP')}</div>

        {listing.condition_text && (
          <div className="listing-condition">{listing.condition_text}</div>
        )}

        {listing.date_text && (
          <div className="listing-meta">{listing.date_text}</div>
        )}

        {listing.shipping_text && (
          <div className="listing-shipping">{listing.shipping_text}</div>
        )}

        <div className="listing-actions">
          <a
            href={listing.listing_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            View on eBay →
          </a>
        </div>
      </div>
    </div>
  )
}
