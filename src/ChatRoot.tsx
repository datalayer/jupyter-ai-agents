/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/*
 * Copyright (c) 2023-2024 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import root from 'react-shadow';
import { ChatComponent } from './ChatWidget';
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

    if (!rootElement.querySelector(`style[${styleAttribute}]`)) {
      const styleElement = document.createElement('style');
      styleElement.setAttribute(styleAttribute, 'true');
      styleElement.textContent = styles;
      rootElement.insertBefore(styleElement, rootElement.firstChild);
    }

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
