import React from 'react'
import { ShadowRoot } from './shadow-root'
import { ShadowPortal } from './shadow-portal'
import {
  PortalHost,
  SelectPortal,
  DropdownPortal,
  PopoverPortal,
  WithPortal
} from './with-portal'

import { generateThemeCSS } from '../theme/styles'

// Re-export components
export {
  ShadowRoot,
  ShadowPortal,
  PortalHost,
  SelectPortal,
  DropdownPortal,
  PopoverPortal,
  WithPortal
}

// Default styles that should be applied in shadow DOM contexts
export const defaultStyles = `
  ${generateThemeCSS()}

  /* Base shadow DOM styles */
  :host {
    all: initial;
    display: block;
    contain: content;
  }
  
  /* Inject Tailwind styles */
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  /* Ensure portal styles */
  [data-portal-host] {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    width: 100%;
    pointer-events: none;
    z-index: 50;
  }

  [data-portal-host] > * {
    pointer-events: auto;
  }
  /* Base variables from Tailwind */
  :host {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  [data-theme="dark"] {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }

  /* Base portal styles */
  [data-portal-host] {
    position: relative;
    z-index: 50;
  }

  /* Reset styles for portals */
  [data-portal-host] * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  /* Styles for specific portal types */
  [data-slot="select-portal"],
  [data-slot="dropdown-portal"],
  [data-slot="popover-portal"] {
    position: fixed;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  [data-slot="select-portal"] > *,
  [data-slot="dropdown-portal"] > *,
  [data-slot="popover-portal"] > * {
    pointer-events: all;
  }
`

// Helper to combine default styles with user styles
export function combineStyles(userStyles?: string | string[]): string[] {
  const styles = [defaultStyles]
  if (userStyles) {
    if (Array.isArray(userStyles)) {
      styles.push(...userStyles)
    } else {
      styles.push(userStyles)
    }
  }
  return styles
}

// Create a pre-configured ShadowRoot with default styles
export function ThemedShadowRoot({ 
  children,
  styles,
  ...props
}: React.ComponentProps<typeof ShadowRoot>) {
  return (
    <ShadowRoot 
      {...props}
      styles={combineStyles(styles)}
      data-shadow-root=""
    >
      {children}
    </ShadowRoot>
  )
}