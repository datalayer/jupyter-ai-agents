import React from 'react'
import { type Theme, ThemeContext } from './context'
import { useSystemTheme } from './hooks'
import { generateThemeCSS } from './styles'

// Theme provider props
interface IThemeProviderProps {
  children: React.ReactNode
  defaultTheme?: Theme
}

// Theme provider component
export function ThemeProvider({ children, defaultTheme = 'system' }: IThemeProviderProps) {
  const [theme, setTheme] = React.useState<Theme>(defaultTheme)
  const systemTheme = useSystemTheme()
  
  // Compute the effective theme that should be applied
  const effectiveTheme = theme === 'system' ? systemTheme : theme

  React.useEffect(() => {
    const styleId = 'datalayer-theme-styles'
    let styleElement = document.getElementById(styleId) as HTMLStyleElement

    if (!styleElement) {
      styleElement = document.createElement('style')
      styleElement.id = styleId
      document.head.appendChild(styleElement)
    }

    // Add the theme styles to the document
    styleElement.textContent = generateThemeCSS()

    // Update both document root and all themed elements
    const root = document.documentElement
    root.setAttribute('data-theme', effectiveTheme)
    
    // Helper function to inject styles into a shadow root
    function injectStylesIntoShadowRoot(shadowRoot: ShadowRoot) {
      let styleElement = shadowRoot.getElementById(styleId)
      if (!styleElement) {
        styleElement = document.createElement('style')
        styleElement.id = styleId
        shadowRoot.insertBefore(styleElement, shadowRoot.firstChild)
      }
      styleElement.textContent = generateThemeCSS()
    }

    // Find and update all shadow roots
    function updateShadowRoots(root: Element | Document | DocumentFragment) {
      const elements = root.querySelectorAll('*')
      elements.forEach(element => {
        // Update theme attribute
        if (element instanceof HTMLElement) {
          const hasThemeAttr = element.hasAttribute('data-theme')
          if (hasThemeAttr) {
            element.setAttribute('data-theme', effectiveTheme)
          }
        }

        // Update shadow roots
        if (element.shadowRoot) {
          injectStylesIntoShadowRoot(element.shadowRoot)
          element.shadowRoot.host.setAttribute('data-theme', effectiveTheme)
          updateShadowRoots(element.shadowRoot)
        }
      })
    }

    // Initial update of shadow roots
    updateShadowRoots(document)

    // Observe DOM for new shadow roots
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node instanceof Element) {
            if (node.shadowRoot) {
              injectStylesIntoShadowRoot(node.shadowRoot)
              node.shadowRoot.host.setAttribute('data-theme', effectiveTheme)
            }
            updateShadowRoots(node)
          }
        })
      })
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true
    })

    return () => {
      observer.disconnect()
    }
  }, [effectiveTheme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <div data-theme={effectiveTheme}>{children}</div>
    </ThemeContext.Provider>
  )
}