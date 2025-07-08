import { useState, useEffect } from 'react'
import axios from 'axios'

export const useMovies = ({ search, genre, sort }) => {
  const [movies, setMovies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchMovies = async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (search) params.append('search', search)
      if (genre) params.append('genre', genre)
      if (sort) params.append('sort', sort)

      const response = await axios.get(`/api/movies?${params.toString()}`)
      setMovies(response.data.movies || [])
    } catch (err) {
      setError(err.response?.data?.error || 'Fehler beim Laden der Filme')
      console.error('Error fetching movies:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMovies()
  }, [search, genre, sort])

  return {
    movies,
    loading,
    error,
    refetch: fetchMovies
  }
}
