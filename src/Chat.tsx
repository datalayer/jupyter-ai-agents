/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatComponent } from '@datalayer/agent-runtimes';
import { JupyterReactTheme } from '@datalayer/jupyter-react/lib/theme/JupyterReactTheme';

import '../style/index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false
    }
  }
});

/**
 * Chat component that provides necessary context providers
 * Wrapper div ensures proper height propagation in JupyterLab
 */
export const Chat: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      <JupyterReactTheme>
        <QueryClientProvider client={queryClient}>
          <ChatComponent />
        </QueryClientProvider>
      </JupyterReactTheme>
    </div>
  );
};
