/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat as ChatPanel } from '@datalayer/agent-runtimes';
import { JupyterReactTheme } from '@datalayer/jupyter-react';
import { ServerConnection } from '@jupyterlab/services';
import { Box } from '@datalayer/primer-addons';
import {
  ActionList,
  ActionMenu,
  Button,
  Spinner,
  Text,
} from '@primer/react';
import {
  getRuntimes,
  iamStore,
  SignInSimple,
  type IRuntimePod,
} from '@datalayer/core';
import { AiAgentIcon } from '@datalayer/icons-react';

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
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    Boolean(iamStore.getState().token)
  );
  const [authError, setAuthError] = useState<string | null>(null);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [isLoadingRuntimes, setIsLoadingRuntimes] = useState(false);
  const [runtimes, setRuntimes] = useState<IRuntimePod[]>([]);
  const [selectedRuntimePodName, setSelectedRuntimePodName] = useState<
    string | null
  >(null);

  const visibleRuntimes = useMemo(() => {
    const agentRuntimes = runtimes.filter(runtime => {
      const candidate = `${runtime.environment_name} ${runtime.given_name}`;
      return /agent/i.test(candidate);
    });
    return agentRuntimes.length > 0 ? agentRuntimes : runtimes;
  }, [runtimes]);

  const selectedRuntime = useMemo(
    () =>
      visibleRuntimes.find(runtime => runtime.pod_name === selectedRuntimePodName) ??
      null,
    [visibleRuntimes, selectedRuntimePodName]
  );

  const loadCloudRuntimes = useCallback(async () => {
    setIsLoadingRuntimes(true);
    setRuntimeError(null);
    try {
      const cloudRuntimes = await getRuntimes();
      setRuntimes(cloudRuntimes);
      if (cloudRuntimes.length === 0) {
        setSelectedRuntimePodName(null);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load cloud runtimes.';
      setRuntimeError(message);
      throw err;
    } finally {
      setIsLoadingRuntimes(false);
    }
  }, []);

  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      return;
    }
    loadCloudRuntimes().catch(() => {
      setIsAuthenticated(false);
      setAuthError('Please sign in to list cloud runtimes.');
    });
  }, [isReady, isAuthenticated, loadCloudRuntimes]);

  const handleSignIn = useCallback(async (authToken: string) => {
    setAuthError(null);
    try {
      await iamStore.getState().refreshUserByToken(authToken);
      setIsAuthenticated(true);
      await loadCloudRuntimes();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Authentication failed.';
      setAuthError(message);
      setIsAuthenticated(false);
    }
  }, [loadCloudRuntimes]);

  const handleApiKeySignIn = useCallback(async (apiKey: string) => {
    setAuthError(null);
    try {
      await iamStore.getState().login(apiKey);
      setIsAuthenticated(true);
      await loadCloudRuntimes();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Token authentication failed.';
      setAuthError(message);
      setIsAuthenticated(false);
    }
  }, [loadCloudRuntimes]);

  const handleLogout = useCallback(() => {
    iamStore.getState().logout();
    setIsAuthenticated(false);
    setSelectedRuntimePodName(null);
    setRuntimes([]);
    setRuntimeError(null);
    setAuthError(null);
  }, []);

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

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
        <JupyterReactTheme>
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <SignInSimple
              title="Jupyter AI Agents"
              description="Sign in with username/password or token to access cloud agent runtimes."
              leadingIcon={<AiAgentIcon size={24} />}
              onSignIn={(jwtToken: string) => {
                void handleSignIn(jwtToken);
              }}
              onApiKeySignIn={(apiKey: string) => {
                void handleApiKeySignIn(apiKey);
              }}
            />
            {authError && (
              <Box sx={{ px: 3, pb: 3 }}>
                <Text sx={{ color: 'danger.fg', fontSize: 1 }}>{authError}</Text>
              </Box>
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
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                border: '1px solid',
                borderColor: 'border.default',
                borderRadius: 2,
                overflow: 'hidden',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 2,
                  p: 2,
                  borderBottom: '1px solid',
                  borderColor: 'border.default',
                  bg: 'canvas.subtle',
                }}
              >
                <ActionMenu>
                  <ActionMenu.Button>
                    {selectedRuntime ? selectedRuntime.given_name : 'Select cloud runtime'}
                  </ActionMenu.Button>
                  <ActionMenu.Overlay width="large">
                    <ActionList selectionVariant="single">
                      <ActionList.GroupHeading>
                        Cloud Agent Runtimes
                      </ActionList.GroupHeading>
                      {visibleRuntimes.map(runtime => (
                        <ActionList.Item
                          key={runtime.pod_name}
                          selected={runtime.pod_name === selectedRuntimePodName}
                          onSelect={() => {
                            setSelectedRuntimePodName(runtime.pod_name);
                          }}
                        >
                          {runtime.given_name}
                          <ActionList.Description variant="block">
                            {runtime.environment_name} | {runtime.pod_name}
                          </ActionList.Description>
                        </ActionList.Item>
                      ))}
                    </ActionList>
                  </ActionMenu.Overlay>
                </ActionMenu>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Button
                    size="small"
                    variant="invisible"
                    onClick={() => {
                      void loadCloudRuntimes();
                    }}
                  >
                    Refresh
                  </Button>
                  <Button
                    size="small"
                    variant="invisible"
                    onClick={handleLogout}
                  >
                    Logout
                  </Button>
                </Box>
              </Box>

              {isLoadingRuntimes ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flex: 1,
                    gap: 2,
                  }}
                >
                  <Spinner />
                  <Text sx={{ color: 'fg.muted', fontSize: 1 }}>
                    Loading cloud runtimes...
                  </Text>
                </Box>
              ) : runtimeError ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'danger.fg', fontSize: 1 }}>{runtimeError}</Text>
                </Box>
              ) : visibleRuntimes.length === 0 ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'fg.muted', fontSize: 1 }}>
                    No cloud runtimes available for this account.
                  </Text>
                </Box>
              ) : !selectedRuntime ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'fg.muted', fontSize: 1 }}>
                    Select a cloud agent runtime to enable chat.
                  </Text>
                </Box>
              ) : !selectedRuntime.ingress ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'danger.fg', fontSize: 1 }}>
                    Selected runtime has no ingress URL. Please choose another runtime.
                  </Text>
                </Box>
              ) : (
                <ChatPanel
                  protocol="vercel-ai"
                  baseUrl={selectedRuntime.ingress}
                  authToken={iamStore.getState().token}
                  runtimeId={selectedRuntime.pod_name}
                  historyEndpoint={`${selectedRuntime.ingress}/api/v1/history`}
                  height="100%"
                  showModelSelector={true}
                  showToolsMenu={true}
                  showInformation={false}
                  showTokenUsage={false}
                  suggestions={[
                    {
                      title: 'Get started',
                      message: 'What can you help me with?',
                    },
                    {
                      title: 'Notebook help',
                      message: 'Can you help me with my Jupyter notebook?',
                    },
                  ]}
                />
              )}
            </Box>
          </QueryClientProvider>
        </Box>
      </JupyterReactTheme>
    </div>
  );
};
