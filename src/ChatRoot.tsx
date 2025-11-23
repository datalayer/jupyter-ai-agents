/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React from 'react';
import root from 'react-shadow';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatComponent } from '@datalayer/core';
import { PORTAL_ROOT_ID } from './shadow/with-portal';

// Import styles as processed CSS string for Shadow DOM injection
import shadowStyles from '!!css-loader?importLoaders=1&exportType=string!postcss-loader!../style/index.css';

type ThemeMode = 'light' | 'dark';

type PortalType =
  | 'select'
  | 'dropdown'
  | 'tooltip'
  | 'hover-card'
  | 'dialog'
  | 'sheet'
  | 'popover'
  | 'portal';

const SLOT_TYPE_MAP: Record<string, PortalType> = {
  'select-content': 'select',
  'dropdown-menu-content': 'dropdown',
  'dropdown-menu-sub-content': 'dropdown',
  'tooltip-content': 'tooltip',
  'hover-card-content': 'hover-card',
  'dialog-content': 'dialog',
  'dialog-overlay': 'dialog',
  'sheet-content': 'sheet',
  'sheet-overlay': 'sheet',
  'popover-content': 'popover',
  'portal-portal': 'portal',
  'select-portal': 'select',
  'dropdown-portal': 'dropdown',
  'popover-portal': 'popover'
};

const PORTAL_SELECTORS = Object.keys(SLOT_TYPE_MAP)
  .map(slot => `[data-slot="${slot}"]`)
  .join(', ');

const PORTAL_CONTAINER_SELECTORS = [
  '[data-radix-select-portal]',
  '[data-radix-select-content-wrapper]',
  '[data-radix-dropdown-menu-portal]',
  '[data-radix-dropdown-menu-content-wrapper]',
  '[data-radix-tooltip-portal]',
  '[data-radix-tooltip-content-wrapper]',
  '[data-radix-hover-card-portal]',
  '[data-radix-hover-card-content-wrapper]',
  '[data-radix-dialog-portal]',
  '[data-radix-dialog-content-wrapper]',
  '[data-radix-sheet-portal]',
  '[data-radix-sheet-content-wrapper]',
  '[data-radix-popover-portal]',
  '[data-radix-popover-content-wrapper]'
];

interface IPortalManagerOptions {
  getSourceElement: () => HTMLElement | null;
  styles: string;
}

interface IPortalManager {
  handleElement(element: HTMLElement): void;
  syncTheme(theme: ThemeMode): void;
  dispose(): void;
}

function createPortalManager({
  getSourceElement,
  styles
}: IPortalManagerOptions): IPortalManager {
  if (typeof window === 'undefined') {
    return {
      handleElement: () => undefined,
      syncTheme: () => undefined,
      dispose: () => undefined
    };
  }

  let rootElement: HTMLElement | null = null;
  const themedElements = new Set<HTMLElement>();
  let currentTheme: ThemeMode = 'light';
  const styleAttribute = 'data-datalayer-portal-styles';

  const ensureGlobalStyles = () => {
    // Inject styles into document head for portals that are children of body
    if (!document.head.querySelector(`style[${styleAttribute}]`)) {
      const styleElement = document.createElement('style');
      styleElement.setAttribute(styleAttribute, 'true');
      // Add additional rules to override Lucide icon sizes and fix Switch component
      const additionalStyles = `
        /* Force size-4 to override inline SVG attributes */
        .size-4 {
          width: 1rem !important;
          height: 1rem !important;
        }
        
        /* Fix Switch component in portals */
        [data-slot="switch"] {
          height: 1.15rem !important;
          width: 2rem !important;
          border-radius: 9999px !important;
          display: inline-flex !important;
          align-items: center !important;
          flex-shrink: 0 !important;
        }
        
        [data-slot="switch-thumb"] {
          width: 1rem !important;
          height: 1rem !important;
          border-radius: 9999px !important;
          display: block !important;
          pointer-events: none !important;
        }
      `;
      styleElement.textContent = styles + additionalStyles;
      document.head.appendChild(styleElement);
      console.log('[ChatRoot] Injected global styles into document head');
    }
  };

  const ensureRoot = () => {
    if (rootElement && document.body.contains(rootElement)) {
      return rootElement;
    }

    rootElement = document.getElementById(PORTAL_ROOT_ID) as HTMLElement | null;
    if (!rootElement) {
      rootElement = document.createElement('div');
      rootElement.id = PORTAL_ROOT_ID;
      rootElement.setAttribute('data-portal-root', '');
      document.body.appendChild(rootElement);
    }

    // Also ensure global styles are injected
    ensureGlobalStyles();

    return rootElement;
  };

  const copyCssVariables = (target: HTMLElement) => {
    const source = getSourceElement() ?? document.documentElement;
    const computed = getComputedStyle(source);
    for (let index = 0; index < computed.length; index += 1) {
      const property = computed[index];
      if (property.startsWith('--')) {
        const value = computed.getPropertyValue(property);
        target.style.setProperty(property, value);
      }
    }
  };

  const applyTheme = (
    element: HTMLElement,
    options: { toggleDarkClass?: boolean } = {}
  ) => {
    element.setAttribute('data-theme', currentTheme);
    if (options.toggleDarkClass) {
      element.classList.toggle('dark', currentTheme === 'dark');
    }
    copyCssVariables(element);
  };

  const findPortalContainer = (element: HTMLElement) => {
    for (const selector of PORTAL_CONTAINER_SELECTORS) {
      const container = element.closest(selector);
      if (container) {
        return container as HTMLElement;
      }
    }
    const parent = element.parentElement;
    return parent instanceof HTMLElement ? parent : element;
  };

  const handleElement = (element: HTMLElement) => {
    const slot = element.dataset.slot;
    if (!slot) {
      return;
    }

    const type = SLOT_TYPE_MAP[slot];
    if (!type) {
      return;
    }

    console.log('[ChatRoot] Handling portal element:', {
      slot,
      type,
      element,
      computedTransform: element.style.transform,
      parentTransform: element.parentElement?.style.transform
    });

    ensureRoot();
    const container = findPortalContainer(element);
    const nodes = new Set<HTMLElement>();
    nodes.add(element);
    if (container) {
      nodes.add(container);
    }

    nodes.forEach(node => {
      themedElements.add(node);
      applyTheme(node, { toggleDarkClass: true });
    });
    
    // Fix positioning issue: Radix calculates wrong positions across Shadow DOM boundary
    // The transform is on the wrapper element (parentElement), not the content element
    const wrapper = element.parentElement;
    if (wrapper && wrapper.style.transform.includes('-200%')) {
      // Find the trigger button in shadow DOM
      const sourceElement = getSourceElement();
      const shadowRoot = sourceElement?.shadowRoot;
      if (shadowRoot) {
        let trigger: Element | null = null;
        let triggerSelector: string = '';
        
        if (type === 'tooltip') {
          // Tooltip trigger
          triggerSelector = '[data-slot="tooltip-trigger"]';
          trigger = shadowRoot.querySelector(triggerSelector);
        } else if (type === 'dropdown') {
          // For dropdown, try multiple selectors since it might use asChild
          // Try: dropdown trigger, or button with aria-haspopup, or data-state=open
          const possibleSelectors = [
            '[data-slot="dropdown-menu-trigger"]',
            'button[aria-haspopup="menu"]',
            'button[aria-expanded="true"]',
            '[role="button"][aria-haspopup="menu"]'
          ];
          
          for (const selector of possibleSelectors) {
            trigger = shadowRoot.querySelector(selector);
            if (trigger) {
              triggerSelector = selector;
              break;
            }
          }
          
          if (!trigger) {
            console.log('[ChatRoot] Could not find dropdown trigger with any selector:', possibleSelectors);
          }
        } else {
          triggerSelector = '[data-state="open"]';
          trigger = shadowRoot.querySelector(triggerSelector);
        }
        
        if (trigger) {
          const triggerRect = trigger.getBoundingClientRect();
          
          // For tooltip, we need to position it above the trigger
          // For dropdown, position it below
          let newX = triggerRect.left;
          let newY: number;
          
          if (type === 'tooltip') {
            // Get tooltip dimensions to position above
            const tooltipHeight = element.offsetHeight || 40; // fallback height
            newY = triggerRect.top - tooltipHeight - 5; // 5px gap
            // Center horizontally
            const tooltipWidth = element.offsetWidth || 100;
            newX = triggerRect.left + (triggerRect.width - tooltipWidth) / 2;
          } else if (type === 'dropdown') {
            // Check if dropdown should be above (side="top") or below
            const side = element.getAttribute('data-side');
            if (side === 'top') {
              // Position above
              const dropdownHeight = element.offsetHeight || 200;
              newY = triggerRect.top - dropdownHeight - 5;
            } else {
              // Position below (default)
              newY = triggerRect.bottom + 5;
            }
          } else {
            // Default: below
            newY = triggerRect.bottom + 5;
          }
          
          wrapper.style.transform = `translate(${newX}px, ${newY}px)`;
          wrapper.style.position = 'fixed';
          wrapper.style.top = '0';
          wrapper.style.left = '0';
          
          console.log('[ChatRoot] Fixed positioning:', {
            slot,
            type,
            triggerRect: {
              top: triggerRect.top,
              bottom: triggerRect.bottom,
              left: triggerRect.left,
              right: triggerRect.right,
              width: triggerRect.width,
              height: triggerRect.height
            },
            elementDimensions: { width: element.offsetWidth, height: element.offsetHeight },
            calculatedPosition: { x: newX, y: newY },
            oldTransform: 'translate(0px, -200%)',
            newTransform: wrapper.style.transform,
            wrapperStyles: {
              position: wrapper.style.position,
              top: wrapper.style.top,
              left: wrapper.style.left
            }
          });
        } else {
          console.log('[ChatRoot] Could not find trigger:', { triggerSelector, shadowRoot });
        }
      } else {
        console.log('[ChatRoot] No shadow root found:', { sourceElement });
      }
    }
    
    console.log('[ChatRoot] Applied theme to portal:', {
      slot,
      finalTransform: element.style.transform,
      finalParentTransform: element.parentElement?.style.transform
    });
  };

  const syncTheme = (theme: ThemeMode) => {
    currentTheme = theme;
    const root = ensureRoot();
    applyTheme(root, { toggleDarkClass: true });

    Array.from(themedElements).forEach(element => {
      if (!element.isConnected) {
        themedElements.delete(element);
        return;
      }
      applyTheme(element, { toggleDarkClass: true });
    });
  };

  const dispose = () => {
    themedElements.clear();
    if (rootElement) {
      rootElement.remove();
      rootElement = null;
    }
  };

  return {
    handleElement,
    syncTheme,
    dispose
  };
}

function collectPortalElements(node: Node): HTMLElement[] {
  if (!(node instanceof HTMLElement)) {
    return [];
  }

  const elements = new Set<HTMLElement>();
  const slot = node.dataset.slot;
  if (slot && SLOT_TYPE_MAP[slot]) {
    elements.add(node);
  }
  if (PORTAL_SELECTORS.length > 0) {
    node
      .querySelectorAll<HTMLElement>(PORTAL_SELECTORS)
      .forEach(element => elements.add(element));
  }
  return Array.from(elements);
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false
    }
  }
});

/**
 * Root component that provides necessary context providers
 * Wrapped in Shadow DOM to isolate styles from JupyterLab
 */
export const ChatRoot: React.FC = () => {
  const [isDarkTheme, setIsDarkTheme] = React.useState(false);
  const shadowHostRef = React.useRef<HTMLDivElement | null>(null);
  const portalManagerRef = React.useRef<IPortalManager | null>(null);

  React.useEffect(() => {
    const checkTheme = () => {
      // JupyterLab has a data-jp-theme-name attribute on the documentElement
      // that will be either 'JupyterLab Light' or 'JupyterLab Dark'
      const themeName = document.documentElement.getAttribute('data-jp-theme-name');
      setIsDarkTheme(themeName?.includes('Dark') ?? false);
    };

    // Check immediately
    checkTheme();

    // Set up an observer to watch for theme changes
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-jp-theme-name']
    });

    return () => observer.disconnect();
  }, []);

  const themeMode: ThemeMode = isDarkTheme ? 'dark' : 'light';

  React.useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const host = shadowHostRef.current;
    if (!host) {
      return undefined;
    }

    if (!portalManagerRef.current) {
      portalManagerRef.current = createPortalManager({
        getSourceElement: () => shadowHostRef.current,
        styles: shadowStyles
      });
    }

    const manager = portalManagerRef.current;
    manager.syncTheme(themeMode);

    const handleNode = (node: Node) => {
      collectPortalElements(node).forEach(element => manager.handleElement(element));
    };

    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(handleNode);
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Apply to existing portals on mount / theme change
    handleNode(document.body);

    return () => {
      observer.disconnect();
    };
  }, [themeMode]);

  React.useEffect(() => () => {
    portalManagerRef.current?.dispose();
    portalManagerRef.current = null;
  }, []);
  
  return (
    <root.div ref={shadowHostRef} className={isDarkTheme ? 'dark' : ''}>
      <style>{shadowStyles}</style>
      <div className="datalayer-chatbot custom-scrollbar">
        <QueryClientProvider client={queryClient}>
          <ChatComponent />
        </QueryClientProvider>
      </div>
    </root.div>
  );
};
