/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React from 'react'
import { createPortal } from 'react-dom'

export interface IWithPortalProps {
  children: React.ReactNode
  type: 'portal' | 'select' | 'dropdown' | 'popover'
}

export const PORTAL_ROOT_ID = 'datalayer-portal-root'

// Component to handle portal mounting and theme synchronization
// Ensure portal root exists
function ensurePortalRoot(): HTMLElement {
  let root = document.getElementById(PORTAL_ROOT_ID)
  if (!root) {
    root = document.createElement('div')
    root.id = PORTAL_ROOT_ID
    root.setAttribute('data-portal-root', '')
    root.setAttribute('style', `
      position: fixed;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 9999;
    `)
    document.body.appendChild(root)
  }
  return root
}

export function WithPortal({ children, type }: IWithPortalProps) {
  const [portalContainer, setPortalContainer] = React.useState<HTMLElement | null>(null)
  const [initialized, setInitialized] = React.useState(false)

  // Create portal root on mount
  React.useEffect(() => {
    if (!initialized) {
      ensurePortalRoot()
      setInitialized(true)
    }
  }, [initialized])

  React.useEffect(() => {
    if (!initialized) return

    const portalRoot = ensurePortalRoot()

    // Create portal container if it doesn't exist
    let container = portalRoot.querySelector(`[data-portal-host][data-slot="${type}-portal"]`) as HTMLElement
    if (!container) {
      container = document.createElement('div')
      container.setAttribute('data-portal-host', '')
      container.setAttribute('data-slot', `${type}-portal`)
      container.setAttribute('style', `
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 0;
        pointer-events: none;
        z-index: 50;
      `)
      portalRoot.appendChild(container)
    }

    // Set initial theme
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light'
    container.setAttribute('data-theme', currentTheme)
    portalRoot.setAttribute('data-theme', currentTheme)

    // Copy all CSS variables from document root to portal root
    const rootStyles = getComputedStyle(document.documentElement)
    const cssVars = Array.from(rootStyles).filter(prop => prop.startsWith('--'))
    cssVars.forEach(prop => {
      const value = rootStyles.getPropertyValue(prop)
      portalRoot.style.setProperty(prop, value)
      container.style.setProperty(prop, value)
    })

    // Setup theme observer
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          const theme = document.documentElement.getAttribute('data-theme') || 'light'
          portalRoot.setAttribute('data-theme', theme)
          container.setAttribute('data-theme', theme)

          // Re-sync CSS variables on theme change
          const styles = getComputedStyle(document.documentElement)
          cssVars.forEach(prop => {
            const value = styles.getPropertyValue(prop)
            portalRoot.style.setProperty(prop, value)
            container.style.setProperty(prop, value)
          })
        }
      })
    })

    // Observe theme changes on document root
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    })

    // Store the container reference
    setPortalContainer(container)

    return () => {
      observer.disconnect()
      if (container && container.childNodes.length === 0) {
        container.remove()
      }
      if (portalRoot && portalRoot.childNodes.length === 0) {
        portalRoot.remove()
      }
      setPortalContainer(null)
    }
  }, [type, initialized])

  if (!portalContainer) {
    return null
  }

  return createPortal(children, portalContainer)
}



// Shorthand components for different portal types
export function PortalHost({ children }: { children: React.ReactNode }) {
  return <WithPortal type="portal">{children}</WithPortal>
}

export function SelectPortal({ children }: { children: React.ReactNode }) {
  return <WithPortal type="select">{children}</WithPortal>
}

export function DropdownPortal({ children }: { children: React.ReactNode }) {
  return <WithPortal type="dropdown">{children}</WithPortal>
}

export function PopoverPortal({ children }: { children: React.ReactNode }) {
  return <WithPortal type="popover">{children}</WithPortal>
}