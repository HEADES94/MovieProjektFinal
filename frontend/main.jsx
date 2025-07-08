import React from 'react'
import ReactDOM from 'react-dom/client'
import MovieApp from './components/MovieApp.jsx'
import './styles/main.css'

// Initialize React app
const root = ReactDOM.createRoot(document.getElementById('react-root'))
root.render(
  <React.StrictMode>
    <MovieApp />
  </React.StrictMode>
)

// Export global functions for backward compatibility with existing templates
window.filterByGenre = (genre) => {
  window.dispatchEvent(new CustomEvent('genreFilter', { detail: { genre } }))
}

window.sortMovies = () => {
  const sortSelect = document.getElementById('sortSelect')
  if (sortSelect) {
    window.dispatchEvent(new CustomEvent('sortMovies', { detail: { sortBy: sortSelect.value } }))
  }
}
