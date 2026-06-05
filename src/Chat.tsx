/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat as ChatPanel } from '@datalayer/agent-runtimes';
import { JupyterReactTheme } from '@datalayer/jupyter-react';
import { ServerConnection } from '@jupyterlab/services';
import { Box } from '@datalayer/primer-addons';

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
 * Get Jupyter server base URL and token
 */
function getJupyterSettings() {
  const settings = ServerConnection.makeSettings();
  return {
    baseUrl: settings.baseUrl,
    token: settings.token
  };
}

/**
 * Hook to ensure agent exists and is ready
 * Uses the unified agent store for state persistence
 */
function useEnsureAgent(
  baseUrl: string,
  token: string
): {
  isReady: boolean;
  error: string | null;
} {
  const [isChecking, setIsChecking] = useState(true);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function checkAgentStatus() {
      try {
        // Check if agent is available by querying configure endpoint
        const headers: HeadersInit = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `token ${token}`;
        }

        // Ensure proper URL construction with slash
        const configUrl = baseUrl.endsWith('/')
          ? `${baseUrl}agent_runtimes/configure`
          : `${baseUrl}/agent_runtimes/configure`;

        const response = await fetch(configUrl, {
          method: 'GET',
          headers,
          credentials: 'include'
        });

        if (mounted) {
          if (response.ok) {
            console.log('[JupyterAIAgents] Agent is ready');
            setIsReady(true);
            setError(null);
            setIsChecking(false);
          } else if (response.status === 503) {
            // Agent not available - backend hasn't initialized yet
            console.log('[JupyterAIAgents] Waiting for agent initialization...');
            setIsReady(false);
            setError(
              'Agent is initializing. Please ensure API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.) are configured.'
            );
            setIsChecking(false);
          } else {
            const errorText = await response.text().catch(() => 'Unknown error');
            setIsReady(false);
            setError(`Agent status check failed: ${errorText}`);
            setIsChecking(false);
          }
        }
      } catch (err) {
        if (mounted) {
          console.error('[JupyterAIAgents] Error checking agent status:', err);
          const errorMessage = err instanceof Error ? err.message : 'Failed to connect to Jupyter server';
          setIsReady(false);
          setError(errorMessage);
          setIsChecking(false);
        }
      }
    }

    checkAgentStatus();

    return () => {
      mounted = false;
    };
  }, [baseUrl, token]);

  return { isReady: isReady && !isChecking, error };
}

/**
 * Chat component that provides necessary context providers
 * Wrapper div ensures proper height propagation in JupyterLab
 */
export const Chat: React.FC = () => {
  const { baseUrl, token } = getJupyterSettings();
  const { isReady, error } = useEnsureAgent(baseUrl, token);

  // Show loading state while initializing
  if (!isReady) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
        <JupyterReactTheme>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              padding: 4,
              textAlign: 'center'
            }}
          >
            {error ? (
              <>
                <Box sx={{ fontSize: 2, fontWeight: 'bold', mb: 2 }}>
                  ⚠️ Agent Not Available
                </Box>
                <Box sx={{ color: 'danger.fg', mb: 3 }}>
                  {error}
                </Box>
                <Box sx={{ fontSize: 1, color: 'fg.muted' }}>
                  Please check the Jupyter server logs and ensure your environment is configured correctly.
                </Box>
              </>
            ) : (
              <>
                <Box sx={{ fontSize: 2, fontWeight: 'bold', mb: 2 }}>
                  🤖 Initializing Agent...
                </Box>
                <Box sx={{ color: 'fg.muted' }}>
                  Connecting to Jupyter AI Agents backend
                </Box>
              </>
            )}
          </Box>
        </JupyterReactTheme>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      <JupyterReactTheme>
        <Box sx={{ height: '100%' }}>
          <QueryClientProvider client={queryClient}>
            <ChatPanel 
              protocol="vercel-ai-jupyter"
              baseUrl={baseUrl}
              height="100%"
              showModelSelector={true}
              showToolsMenu={true}
              suggestions={[
                {
                  title: '💡 Get started',
                  message: 'What can you help me with?',
                },
                {
                  title: '📓 Notebook help',
                  message: 'Can you help me with my Jupyter notebook?',
                },
              ]}
            />
          </QueryClientProvider>
        </Box>
      </JupyterReactTheme>
    </div>
  );
};
