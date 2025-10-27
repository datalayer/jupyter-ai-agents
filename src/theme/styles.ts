/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import type { Theme } from './context'

// Define theme CSS
export const lightThemeClass = {
  background: '0 0% 100%',
  foreground: '222.2 84% 4.9%',
  card: '0 0% 100%',
  cardForeground: '222.2 84% 4.9%',
  popover: '0 0% 100%',
  popoverForeground: '222.2 84% 4.9%',
  primary: '222.2 47.4% 11.2%',
  primaryForeground: '210 40% 98%',
  secondary: '210 40% 96.1%',
  secondaryForeground: '222.2 47.4% 11.2%',
  muted: '210 40% 96.1%',
  mutedForeground: '215.4 16.3% 46.9%',
  accent: '210 40% 96.1%',
  accentForeground: '222.2 47.4% 11.2%',
  destructive: '0 84.2% 60.2%',
  destructiveForeground: '210 40% 98%',
  border: '214.3 31.8% 91.4%',
  input: '214.3 31.8% 91.4%',
  ring: '222.2 84% 4.9%'
}

export const darkThemeClass = {
  background: '222.2 84% 4.9%',
  foreground: '210 40% 98%',
  card: '222.2 84% 4.9%',
  cardForeground: '210 40% 98%',
  popover: '222.2 84% 4.9%',
  popoverForeground: '210 40% 98%',
  primary: '210 40% 98%',
  primaryForeground: '222.2 47.4% 11.2%',
  secondary: '217.2 32.6% 17.5%',
  secondaryForeground: '210 40% 98%',
  muted: '217.2 32.6% 17.5%',
  mutedForeground: '215 20.2% 65.1%',
  accent: '217.2 32.6% 17.5%',
  accentForeground: '210 40% 98%',
  destructive: '0 62.8% 30.6%',
  destructiveForeground: '210 40% 98%',
  border: '217.2 32.6% 17.5%',
  input: '217.2 32.6% 17.5%',
  ring: '212.7 26.8% 83.9%'
}

// Generate CSS variables string
export function generateThemeVariables(theme: Theme = 'light') {
  const vars = theme === 'dark' ? darkThemeClass : lightThemeClass
  return `
    --background: ${vars.background};
    --foreground: ${vars.foreground};
    --card: ${vars.card};
    --card-foreground: ${vars.cardForeground};
    --popover: ${vars.popover};
    --popover-foreground: ${vars.popoverForeground};
    --primary: ${vars.primary};
    --primary-foreground: ${vars.primaryForeground};
    --secondary: ${vars.secondary};
    --secondary-foreground: ${vars.secondaryForeground};
    --muted: ${vars.muted};
    --muted-foreground: ${vars.mutedForeground};
    --accent: ${vars.accent};
    --accent-foreground: ${vars.accentForeground};
    --destructive: ${vars.destructive};
    --destructive-foreground: ${vars.destructiveForeground};
    --border: ${vars.border};
    --input: ${vars.input};
    --ring: ${vars.ring};
    --radius: 0.5rem;
  `
}

// Generate theme CSS string
export function generateThemeCSS() {
  return `
    /* Light theme variables */
    :host, :root, [data-theme="light"] {
      ${generateThemeVariables('light')}
      color-scheme: light;
    }

    /* Dark theme variables */
    :host([data-theme="dark"]), [data-theme="dark"] {
      ${generateThemeVariables('dark')}
      color-scheme: dark;
    }

    /* Base styles */
    :host, [data-portal], [data-portal-host] {
      background-color: hsl(var(--background));
      color: hsl(var(--foreground));
    }

    /* Portal styles */
    [data-portal-host] {
      position: relative;
      z-index: 50;
      isolation: isolate;
    }

    [data-portal-host] * {
      box-sizing: border-box;
    }
  `
}