import React from 'react'
import root from 'react-shadow/styled-components'

export interface IShadowRootProps {
  children: React.ReactNode
  id?: string
  styles?: string | string[]
}

// Maps Shadow DOM part names to their slot attribute values
const SHADOW_SLOTS = {
  portal: 'portal-host',
  select: 'select-portal',
  dropdown: 'dropdown-portal',
  popover: 'popover-portal'
} as const

export function ShadowRoot({ children, styles = '', id = 'shadow-root' }: IShadowRootProps) {
  // Create a container for each type of portal content
  const portalHosts = React.useRef<Record<string, HTMLDivElement | null>>({})

  // Initialize portal containers and handle theme propagation
  React.useLayoutEffect(() => {
    // Create portal hosts
    Object.entries(SHADOW_SLOTS).forEach(([key, slot]) => {
      if (!portalHosts.current[key]) {
        const host = document.createElement('div')
        host.setAttribute('data-portal-host', '')
        host.setAttribute('data-slot', slot)
        // Ensure portal host gets themed
        if (document.documentElement.hasAttribute('data-theme')) {
          const theme = document.documentElement.getAttribute('data-theme')
          host.setAttribute('data-theme', theme || '')
        }
        portalHosts.current[key] = host
      }
    })

    // Set up theme observation and propagation
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'data-theme'
        ) {
          const theme = (mutation.target as HTMLElement).getAttribute('data-theme')
          Object.values(portalHosts.current).forEach(host => {
            if (host) {
              host.setAttribute('data-theme', theme || '')
            }
          })
        }
      })
    })

    // Observe theme changes on documentElement and shadow host
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    })

    const shadowHost = document.getElementById(id)
    if (shadowHost) {
      observer.observe(shadowHost, {
        attributes: true,
        attributeFilter: ['data-theme']
      })
    }

    return () => {
      Object.values(portalHosts.current).forEach(host => {
        host?.parentElement?.removeChild(host)
      })
      portalHosts.current = {}
      observer.disconnect()
    }
  }, [id])

  // Handle portal host mounting
  const portalHostRefs = Object.entries(SHADOW_SLOTS).map(([key, slot]) => ({
    key,
    slot,
    ref: React.useCallback((node: HTMLDivElement | null) => {
      if (node && portalHosts.current[key]) {
        node.appendChild(portalHosts.current[key]!)
      }
    }, [key])
  }))

  // Insert styles
  React.useInsertionEffect(() => {
    if (!styles) return

    const styleContent = Array.isArray(styles) ? styles.join('\n') : styles
    const styleElement = document.createElement('style')
    styleElement.textContent = styleContent

    const shadowRoot = document.getElementById(id)?.shadowRoot
    if (shadowRoot) {
      // Remove any existing style elements
      shadowRoot.querySelectorAll('style').forEach(el => el.remove())
      // Insert new style element at the beginning of shadow root
      shadowRoot.insertBefore(styleElement, shadowRoot.firstChild)
    }
  }, [id, styles])

  return (
    <root.div id={id} data-theme-sync="" data-shadow-root="">
      {/* Main content */}
      {children}

      {/* Portal containers */}
      {portalHostRefs.map(({ key, slot, ref }) => (
        <div key={key} ref={ref} data-portal-host="" data-slot={slot} data-theme="" />
      ))}
    </root.div>
  )
}