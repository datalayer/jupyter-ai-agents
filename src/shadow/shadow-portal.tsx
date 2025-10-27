import React from 'react'
import { createPortal } from 'react-dom'

export interface IShadowPortalProps {
  children: React.ReactNode
  styles?: string | string[]
}

export function ShadowPortal({ children, styles = '' }: IShadowPortalProps) {
  const portalRef = React.useRef<HTMLDivElement | null>(null)
  const shadowRootRef = React.useRef<ShadowRoot | null>(null)
  const hostRef = React.useRef<HTMLDivElement | null>(null)

  // Initialize shadow root and portal container
  React.useLayoutEffect(() => {
    if (!portalRef.current) {
      return
    }

    // Create and attach shadow root
    const shadowRoot = portalRef.current.attachShadow({ mode: 'open' })
    shadowRootRef.current = shadowRoot

    // Insert styles first
    if (styles) {
      const styleContent = Array.isArray(styles) ? styles.join('\n') : styles
      const styleElement = document.createElement('style')
      styleElement.textContent = styleContent
      shadowRoot.appendChild(styleElement)
    }

    // Create portal host
    const host = document.createElement('div')
    host.setAttribute('data-portal-host', '')
    shadowRoot.appendChild(host)
    hostRef.current = host

    // Cleanup
    return () => {
      shadowRootRef.current = null
      hostRef.current = null
    }
  }, [])

  // Sync theme between shadow roots and handle theme propagation
  React.useLayoutEffect(() => {
    if (!portalRef.current || !shadowRootRef.current) {
      return
    }

    function propagateTheme(theme: string | null) {
      if (portalRef.current) {
        portalRef.current.setAttribute('data-theme', theme || '')
      }
      if (shadowRootRef.current) {
        const host = shadowRootRef.current.host as HTMLElement
        host.setAttribute('data-theme', theme || '')
      }
      if (hostRef.current) {
        hostRef.current.setAttribute('data-theme', theme || '')
      }
    }

    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (
          mutation.type === 'attributes' &&
          mutation.attributeName === 'data-theme'
        ) {
          const theme = (mutation.target as HTMLElement).getAttribute('data-theme')
          propagateTheme(theme)
        }
      })
    })

    // Find closest themed ancestor in light DOM or shadow DOM
    function findThemedAncestor(element: Element | null): Element | null {
      while (element) {
        // Check for theme in current element
        if (element.hasAttribute('data-theme')) {
          return element
        }
        
        // Check in shadow DOM
        if (element.shadowRoot) {
          const shadowThemed = element.shadowRoot.querySelector('[data-theme]')
          if (shadowThemed) {
            return shadowThemed
          }
        }

        // Move up through shadow boundaries
        const rootNode = element.getRootNode() as ShadowRoot | Document
        if (rootNode instanceof ShadowRoot) {
          element = rootNode.host
        } else {
          element = element.parentElement
        }
      }
      return null
    }

    // Find themed parent
    let themedParent = findThemedAncestor(portalRef.current)
    if (!themedParent) {
      themedParent = document.querySelector('[data-theme]')
    }

    if (themedParent) {
      observer.observe(themedParent, {
        attributes: true,
        attributeFilter: ['data-theme']
      })

      // Initial theme sync
      const theme = themedParent.getAttribute('data-theme')
      propagateTheme(theme)
    }

    return () => {
      observer.disconnect()
    }
  }, [])

  return (
    <div ref={portalRef} data-theme-sync="" data-shadow-root="">
      {hostRef.current && createPortal(children, hostRef.current)}
    </div>
  )
}