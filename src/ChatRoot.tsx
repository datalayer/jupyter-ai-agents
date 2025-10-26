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

// Import styles as processed CSS string for Shadow DOM injection
import shadowStyles from '!!css-loader?importLoaders=1&exportType=string!postcss-loader!../style/index.css';

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
  
  return (
    <root.div className={isDarkTheme ? 'dark' : ''}>
      <style>{shadowStyles}</style>
      <div className="datalayer-chatbot custom-scrollbar">
        <QueryClientProvider client={queryClient}>
          <ChatComponent />
        </QueryClientProvider>
      </div>
    </root.div>
  );
};
