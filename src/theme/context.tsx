/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React from 'react'

// Theme context type
export type Theme = 'light' | 'dark' | 'system'

// Theme context value interface
interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
}

// Create theme context with default values
export const ThemeContext = React.createContext<ThemeContextValue>({
  theme: 'system',
  setTheme: () => undefined
})

// Custom hook to use theme context
export function useTheme() {
  const context = React.useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}