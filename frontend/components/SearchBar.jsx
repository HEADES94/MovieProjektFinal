import React from 'react'
import { motion } from 'framer-motion'
import { Search, X } from 'lucide-react'

const SearchBar = ({ value, onChange, placeholder, isLoading }) => {
  const handleClear = () => {
    onChange('')
  }

  return (
    <motion.div
      className="search-container-react"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.1 }}
    >
      <div className="search-input-wrapper">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`search-input-react ${isLoading ? 'loading' : ''}`}
          disabled={isLoading}
        />
        {value && (
          <motion.button
            className="search-clear"
            onClick={handleClear}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <X size={16} />
          </motion.button>
        )}
      </div>
      {isLoading && (
        <motion.div
          className="search-loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="loading-spinner"></div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default SearchBar
