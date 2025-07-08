import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, SortAsc, Star, Calendar, Play } from 'lucide-react'
import GenreFilter from './GenreFilter.jsx'
import MovieGrid from './MovieGrid.jsx'
import SearchBar from './SearchBar.jsx'
import SortSelector from './SortSelector.jsx'
import { useMovies } from '../hooks/useMovies.js'
import { useDebounce } from '../hooks/useDebounce.js'

const MovieApp = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('')
  const [sortBy, setSortBy] = useState('rating')
  const [isLoading, setIsLoading] = useState(false)

  const debouncedSearch = useDebounce(searchQuery, 300)
  const { movies, loading, error, refetch } = useMovies({
    search: debouncedSearch,
    genre: selectedGenre,
    sort: sortBy
  })

  // Listen for legacy events from existing templates
  useEffect(() => {
    const handleGenreFilter = (event) => {
      setSelectedGenre(event.detail.genre)
    }

    const handleSortMovies = (event) => {
      setSortBy(event.detail.sortBy)
    }

    window.addEventListener('genreFilter', handleGenreFilter)
    window.addEventListener('sortMovies', handleSortMovies)

    return () => {
      window.removeEventListener('genreFilter', handleGenreFilter)
      window.removeEventListener('sortMovies', handleSortMovies)
    }
  }, [])

  const filteredMovies = useMemo(() => {
    if (!movies) return []

    let filtered = [...movies]

    // Search filter
    if (debouncedSearch) {
      filtered = filtered.filter(movie =>
        movie.title.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        movie.genre?.toLowerCase().includes(debouncedSearch.toLowerCase())
      )
    }

    // Genre filter
    if (selectedGenre) {
      filtered = filtered.filter(movie =>
        movie.genre?.toLowerCase() === selectedGenre.toLowerCase()
      )
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title)
        case 'year_desc':
          return (b.year || 0) - (a.year || 0)
        case 'year_asc':
          return (a.year || 0) - (b.year || 0)
        case 'rating':
        default:
          return (b.rating || 0) - (a.rating || 0)
      }
    })

    return filtered
  }, [movies, debouncedSearch, selectedGenre, sortBy])

  const handleSearchChange = (query) => {
    setSearchQuery(query)
  }

  const handleGenreChange = (genre) => {
    setSelectedGenre(genre)
    // Update URL for backward compatibility
    const url = new URL(window.location.href)
    if (genre) {
      url.searchParams.set('genre', genre)
    } else {
      url.searchParams.delete('genre')
    }
    window.history.pushState({}, '', url)
  }

  const handleSortChange = (sort) => {
    setSortBy(sort)
    // Update URL for backward compatibility
    const url = new URL(window.location.href)
    if (sort) {
      url.searchParams.set('sort', sort)
    } else {
      url.searchParams.delete('sort')
    }
    window.history.pushState({}, '', url)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="react-movie-app"
    >
      {/* Enhanced Header with Real-time Stats */}
      <motion.div
        className="movie-app-header"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="stats-bar">
          <div className="stat-item">
            <Star className="stat-icon" />
            <span className="stat-value">{filteredMovies.length}</span>
            <span className="stat-label">Filme gefunden</span>
          </div>
          {selectedGenre && (
            <div className="stat-item">
              <Filter className="stat-icon" />
              <span className="stat-value">{selectedGenre}</span>
              <span className="stat-label">Genre aktiv</span>
            </div>
          )}
        </div>
      </motion.div>

      {/* Enhanced Search and Filter Controls */}
      <motion.div
        className="controls-section"
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <SearchBar
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="🔍 Filme durchsuchen..."
          isLoading={loading}
        />

        <div className="filter-controls">
          <GenreFilter
            selectedGenre={selectedGenre}
            onGenreChange={handleGenreChange}
          />

          <SortSelector
            value={sortBy}
            onChange={handleSortChange}
          />
        </div>
      </motion.div>

      {/* Movie Grid with Enhanced Animations */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            className="loading-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="cosmic-loader">
              <div className="loader-ring"></div>
              <div className="loader-text">Lade Filme...</div>
            </div>
          </motion.div>
        ) : error ? (
          <motion.div
            key="error"
            className="error-state"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
          >
            <div className="error-content">
              <h3>⚠️ Fehler beim Laden</h3>
              <p>{error}</p>
              <button onClick={refetch} className="btn btn-primary">
                Erneut versuchen
              </button>
            </div>
          </motion.div>
        ) : (
          <MovieGrid
            key="movies"
            movies={filteredMovies}
            searchQuery={debouncedSearch}
          />
        )}
      </AnimatePresence>

      {/* Results Summary */}
      <motion.div
        className="results-summary"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {filteredMovies.length === 0 && !loading && (
          <div className="no-results">
            <h3>🎬 Keine Filme gefunden</h3>
            <p>Versuche andere Suchbegriffe oder Genre-Filter</p>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}

export default MovieApp
