import React from 'react'
import { motion } from 'framer-motion'
import { SortAsc, Star, Calendar, AlphabeticallyIcon } from 'lucide-react'

const SortSelector = ({ value, onChange }) => {
  const sortOptions = [
    { value: 'rating', label: '⭐ Beste Bewertung', icon: Star },
    { value: 'title', label: '🔤 Titel A-Z', icon: AlphabeticallyIcon },
    { value: 'year_desc', label: '📅 Neuste zuerst', icon: Calendar },
    { value: 'year_asc', label: '📅 Älteste zuerst', icon: Calendar }
  ]

  return (
    <motion.div
      className="sort-selector-react"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
    >
      <div className="sort-icon">
        <SortAsc size={20} />
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="sort-select-react"
      >
        {sortOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </motion.div>
  )
}

export default SortSelector
