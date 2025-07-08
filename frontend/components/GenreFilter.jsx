import React from 'react'
import { motion } from 'framer-motion'

const GenreFilter = ({ selectedGenre, onGenreChange }) => {
  const genres = [
    { id: '', name: 'Alle Genres', emoji: '🎬' },
    { id: 'Action', name: 'Action', emoji: '🚀' },
    { id: 'Drama', name: 'Drama', emoji: '🎭' },
    { id: 'Comedy', name: 'Comedy', emoji: '😄' },
    { id: 'Horror', name: 'Horror', emoji: '👻' },
    { id: 'Romance', name: 'Romance', emoji: '💕' },
    { id: 'Sci-Fi', name: 'Sci-Fi', emoji: '🛸' },
    { id: 'Thriller', name: 'Thriller', emoji: '⚡' },
    { id: 'Animation', name: 'Animation', emoji: '🎌' },
    { id: 'Fantasy', name: 'Fantasy', emoji: '🧙' },
    { id: 'Crime', name: 'Crime', emoji: '🕵️' }
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  }

  const buttonVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
    hover: {
      scale: 1.05,
      y: -3,
      transition: { duration: 0.2 }
    },
    tap: { scale: 0.95 }
  }

  return (
    <motion.div
      className="genre-filter-react"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {genres.map((genre) => (
        <motion.button
          key={genre.id}
          className={`genre-btn-react ${selectedGenre === genre.id ? 'active' : ''}`}
          onClick={() => onGenreChange(genre.id)}
          variants={buttonVariants}
          whileHover="hover"
          whileTap="tap"
        >
          <span className="genre-emoji">{genre.emoji}</span>
          <span className="genre-name">{genre.name}</span>
        </motion.button>
      ))}
    </motion.div>
  )
}

export default GenreFilter
