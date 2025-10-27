import React from 'react'

// Custom hook to handle system color scheme
export function useSystemTheme() {
  const [systemTheme, setSystemTheme] = React.useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  React.useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => setSystemTheme(e.matches ? 'dark' : 'light')

    query.addEventListener('change', handler)
    return () => query.removeEventListener('change', handler)
  }, [])

  return systemTheme
}