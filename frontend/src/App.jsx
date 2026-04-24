import { useState } from 'react'
import axios from 'axios'
import SearchForm from './components/SearchForm'
import ResultsDisplay from './components/ResultsDisplay'
import StatCard from './components/StatCard'

const API_BASE_URL = 'http://localhost:8000'

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState(null)
  const [sortBy, setSortBy] = useState('price-asc')
  const [filterStatus, setFilterStatus] = useState('sold')

  const formatPrice = (amount, currency = 'GBP') => {
    if (amount === null || amount === undefined) {
      return 'N/A'
    }

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

  const handleSearch = async (formData) => {
    setLoading(true)
    setError(null)
    setQuery(formData)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/search`, {
        card_name: formData.cardName,
        condition_type: formData.conditionType,
        grader: formData.conditionType === 'graded' ? formData.grader : null,
        grade: formData.conditionType === 'graded' ? formData.grade : null,
        include_unsold: formData.includeUnsold,
        max_results: formData.maxResults,
      })
      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search. Please try again.')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <header>
        <h1>🎮 Pokemon Card Price Tracker</h1>
      </header>
      
      <main>
        <SearchForm onSearch={handleSearch} loading={loading} />

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching eBay listings...</p>
          </div>
        )}

        {results && !loading && (
          <>
            {(() => {
              const statsCurrency =
                results.sold_listings?.[0]?.currency ||
                results.unsold_listings?.[0]?.currency ||
                'GBP'

              return (
            <div className="stats-grid">
              <StatCard
                label="Total Results"
                value={results.sold_listings.length}
                icon="📊"
              />
              <StatCard
                label="Lowest Price"
                value={formatPrice(results.sold_stats.lowest_price, statsCurrency)}
                icon="📉"
              />
              <StatCard
                label="Highest Price"
                value={formatPrice(results.sold_stats.highest_price, statsCurrency)}
                icon="📈"
              />
              <StatCard
                label="Average Price"
                value={formatPrice(results.sold_stats.average_price, statsCurrency)}
                icon="💰"
              />
              <StatCard
                label="Median Price"
                value={formatPrice(results.sold_stats.median_price, statsCurrency)}
                icon="⚖️"
              />
            </div>
              )
            })()}

            <ResultsDisplay
              results={results}
              sortBy={sortBy}
              setSortBy={setSortBy}
              filterStatus={filterStatus}
              setFilterStatus={setFilterStatus}
            />
          </>
        )}

        {!loading && !results && !error && (
          <div className="no-results">
            <p style={{ fontSize: '2rem', marginBottom: '1rem' }}>🔍</p>
            <p>Search for a Pokemon card to see pricing information</p>
          </div>
        )}
      </main>
    </>
  )
}
