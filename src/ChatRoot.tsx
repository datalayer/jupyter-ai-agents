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
  return (
    <root.div>
      <style>
        {`
          :host {
            all: initial;
            display: block;
            height: 100%;
            contain: content;
          }
          .jupyter-ai-chat-shadow-host {
            height: 100%;
            width: 100%;
            background: var(--jp-layout-color1);
            color: var(--jp-content-font-color1);
          }
        `}
      </style>
  <style>{shadowStyles}</style>
      <div className="jupyter-ai-chat-shadow-host">
        <QueryClientProvider client={queryClient}>
          <ChatComponent />
        </QueryClientProvider>
      </div>
    </root.div>
  );
};
