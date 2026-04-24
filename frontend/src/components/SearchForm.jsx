import { useState } from 'react'

export default function SearchForm({ onSearch, loading }) {
  const [formData, setFormData] = useState({
    cardName: '',
    conditionType: 'raw',
    grader: 'PSA',
    grade: 8,
    includeUnsold: false,
    maxResults: 20,
  })

  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const newErrors = {}
    if (!formData.cardName.trim() || formData.cardName.length < 2) {
      newErrors.cardName = 'Card name must be at least 2 characters'
    }
    if (formData.conditionType === 'graded' && !formData.grader) {
      newErrors.grader = 'Please select a grader'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setErrors({})
    onSearch(formData)
  }

  const handleClear = () => {
    setFormData({
      cardName: '',
      conditionType: 'raw',
      grader: 'PSA',
      grade: 8,
      includeUnsold: false,
      maxResults: 20,
    })
    setErrors({})
  }

  return (
    <div className="search-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="form-group">
          <label htmlFor="cardName">Card Name</label>
          <input
            id="cardName"
            type="text"
            name="cardName"
            value={formData.cardName}
            onChange={handleChange}
            placeholder="e.g., Charizard, Pikachu"
            disabled={loading}
          />
          {errors.cardName && <span style={{ color: '#c33', fontSize: '0.85rem' }}>{errors.cardName}</span>}
        </div>

        <div className="form-group">
          <label>Condition Type</label>
          <div className="condition-group">
            <label className="radio-label">
              <input
                type="radio"
                name="conditionType"
                value="raw"
                checked={formData.conditionType === 'raw'}
                onChange={handleChange}
                disabled={loading}
              />
              Raw
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="conditionType"
                value="graded"
                checked={formData.conditionType === 'graded'}
                onChange={handleChange}
                disabled={loading}
              />
              Graded
            </label>
          </div>
        </div>

        {formData.conditionType === 'graded' && (
          <>
            <div className="form-group">
              <label htmlFor="grader">Grader</label>
              <select
                id="grader"
                name="grader"
                value={formData.grader}
                onChange={handleChange}
                disabled={loading}
              >
                <option value="PSA">PSA</option>
                <option value="ACE">ACE</option>
              </select>
              {errors.grader && <span style={{ color: '#c33', fontSize: '0.85rem' }}>{errors.grader}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="grade">Grade (1-10)</label>
              <select
                id="grade"
                name="grade"
                value={formData.grade}
                onChange={handleChange}
                disabled={loading}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </>
        )}

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="includeUnsold"
              checked={formData.includeUnsold}
              onChange={handleChange}
              disabled={loading}
            />
            Include Unsold Listings
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="maxResults">Results per Page</label>
          <select
            id="maxResults"
            name="maxResults"
            value={formData.maxResults}
            onChange={handleChange}
            disabled={loading}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
        </div>

        <div className="button-group">
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Searching...' : '🔍 Search'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleClear}
            disabled={loading}
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  )
}
