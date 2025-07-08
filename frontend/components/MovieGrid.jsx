import React from 'react'
import { motion } from 'framer-motion'
import { Star, Calendar, Play, Eye } from 'lucide-react'

const MovieCard = ({ movie, index }) => {
  const cardVariants = {
    hidden: { opacity: 0, y: 50, scale: 0.9 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.4,
        delay: index * 0.05,
        ease: "easeOut"
      }
    },
    hover: {
      y: -12,
      scale: 1.03,
      transition: { duration: 0.2 }
    }
  }

  const handleClick = () => {
    if (movie.id) {
      window.location.href = `/movie/${movie.id}`
    }
  }

  return (
    <motion.div
      className="movie-card-react"
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      onClick={handleClick}
      data-movie-id={movie.id}
    >
      <div className="movie-poster-react">
        <img
          src={movie.poster_url || '/static/default_poster.jpg'}
          alt={movie.title}
          loading="lazy"
        />
        <div className="movie-overlay">
          <motion.button
            className="play-button"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <Play size={24} />
          </motion.button>
        </div>
        {movie.rating && (
          <div className="rating-badge-react">
            <Star size={14} />
            {movie.rating.toFixed(1)}
          </div>
        )}
      </div>

      <div className="movie-info-react">
        <h3 className="movie-title-react">{movie.title}</h3>
        <div className="movie-meta-react">
          <span className="movie-year">
            <Calendar size={14} />
            {movie.year || 'N/A'}
          </span>
          <span className="movie-genre">{movie.genre}</span>
        </div>
      </div>
    </motion.div>
  )
}

const MovieGrid = ({ movies, searchQuery }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.02
      }
    }
  }

  return (
    <motion.div
      className="movies-grid-react"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {movies.map((movie, index) => (
        <MovieCard
          key={movie.id || index}
          movie={movie}
          index={index}
        />
      ))}
    </motion.div>
  )
}

export default MovieGrid
