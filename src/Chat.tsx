/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat as ChatPanel } from '@datalayer/agent-runtimes/lib/chat/Chat';
import { AgentRuntimesClient } from '@datalayer/agent-runtimes/lib/client/AgentRuntimesClient';
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
  coreStore,
  iamStore,
  SignInSimple,
} from '@datalayer/core';
import { DEFAULT_SERVICE_URLS } from '@datalayer/core/lib/api/constants';
import { AiAgentIcon } from '@datalayer/icons-react';

import '../style/index.css';
import { useAIAgentsStore } from './store';
import {
  useNotebookTools,
  type FrontendToolDefinition
} from '@datalayer/agent-runtimes/lib/tools/adapters/agent-runtimes/notebookHooks';
import { useLexicalTools } from '@datalayer/agent-runtimes/lib/tools/adapters/agent-runtimes/lexicalHooks';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false
    }
  }
});

interface IRuntimePod {
  pod_name: string;
  ingress: string;
  given_name: string;
  environment_name: string;
}

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
            setIsReady(true);
            setError(null);
            setIsChecking(false);
          } else if (response.status === 503) {
            // Agent not available - backend hasn't initialized yet
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
  useEffect(() => {
    // JupyterLab serves this extension from localhost, but IAM/runtimes are
    // cloud services; ensure service URLs do not fall back to local origins.
    coreStore.getState().setConfiguration({
      iamUrl: DEFAULT_SERVICE_URLS.IAM,
      runtimesUrl: DEFAULT_SERVICE_URLS.RUNTIMES,
      aiAgentsUrl: DEFAULT_SERVICE_URLS.AI_AGENTS,
    });
  }, []);

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

  // The runtime ingress points at the Jupyter server path
  // (`.../jupyter/server/...`). The agent-runtimes server is exposed under
  // `.../agent-runtimes/...` on the same host, so rewrite the path the same way
  // the Datalayer UI does to avoid hitting the Jupyter server (CORS/404).
  const selectedRuntimeEndpoint = useMemo(() => {
    if (!selectedRuntime?.ingress) {
      return undefined;
    }
    return selectedRuntime.ingress.replace(
      '/jupyter/server/',
      '/agent-runtimes/'
    );
  }, [selectedRuntime]);

  const loadCloudRuntimes = useCallback(async () => {
    setIsLoadingRuntimes(true);
    setRuntimeError(null);
    try {
      const token = iamStore.getState().token;
      if (!token) {
        throw new Error('Please sign in to list cloud agents.');
      }
      const client = new AgentRuntimesClient({ token });
      const cloudRuntimes = (await client.listRuntimes()).map((runtime: any) =>
        runtime.rawData()
      );
      setRuntimes(cloudRuntimes);
      if (cloudRuntimes.length === 0) {
        setSelectedRuntimePodName(null);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load cloud agents.';
      setRuntimeError(message);
      throw err;
    } finally {
      setIsLoadingRuntimes(false);
    }
  }, []);

  // The doorbell of the store: anything that created or terminated a code
  // sandbox — the Datalayer UI plugins do — rings it, and the list reloads.
  const refreshSeq = useAIAgentsStore(state => state.refreshSeq);

  /*
   * The frontend tools of the editor in front of the user.
   *
   * The lab plugin publishes which Datalayer editor is focused; the same
   * hooks the web application's editors use build the tools of that editor
   * — the notebook ones over the notebook store, the document ones over the
   * lexical store, both keyed by the editor's id. Hooks are unconditional,
   * so both are built and the active editor picks; with no Datalayer editor
   * focused the chat carries no editor tools.
   */
  const activeEditor = useAIAgentsStore(state => state.activeEditor);
  const notebookTools = useNotebookTools(
    activeEditor?.kind === 'notebook' ? activeEditor.id : 'jp-ai-agents-idle'
  );
  const documentTools = useLexicalTools(
    activeEditor?.kind === 'document' ? activeEditor.id : 'jp-ai-agents-idle'
  );
  const frontendTools: FrontendToolDefinition[] = !activeEditor
    ? []
    : activeEditor.kind === 'notebook'
      ? notebookTools
      : documentTools;
  useEffect(() => {
    if (!isReady || !isAuthenticated) {
      return;
    }
    loadCloudRuntimes().catch(() => {
      setIsAuthenticated(false);
      setAuthError('Please sign in to list cloud runtimes.');
    });
  }, [isReady, isAuthenticated, loadCloudRuntimes, refreshSeq]);

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
              loginUrl={`${DEFAULT_SERVICE_URLS.IAM}/api/iam/v1/login`}
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
                  {/* Nothing to pick: the button says so and does not open. */}
                  <ActionMenu.Button disabled={visibleRuntimes.length === 0}>
                    {selectedRuntime ? selectedRuntime.given_name : 'Select cloud agent'}
                  </ActionMenu.Button>
                  <ActionMenu.Overlay width="large">
                    <ActionList selectionVariant="single">
                      <ActionList.GroupHeading>
                        Cloud Agents
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
                      {selectedRuntimePodName && (
                        <>
                          <ActionList.Divider />
                          {/* The same word as the code sandbox dialog: letting
                              go of the agent, not cancelling the menu. */}
                          <ActionList.Item
                            variant="danger"
                            onSelect={() => {
                              setSelectedRuntimePodName(null);
                            }}
                          >
                            Unassign
                            <ActionList.Description variant="block">
                              Let go of this agent; the chat waits for another.
                            </ActionList.Description>
                          </ActionList.Item>
                        </>
                      )}
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
                    Loading cloud agents...
                  </Text>
                </Box>
              ) : runtimeError ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'danger.fg', fontSize: 1 }}>{runtimeError}</Text>
                </Box>
              ) : visibleRuntimes.length === 0 ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'fg.muted', fontSize: 1 }}>
                    No cloud agents available for this account.
                  </Text>
                </Box>
              ) : !selectedRuntime ? (
                <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Text sx={{ color: 'fg.muted', fontSize: 1 }}>
                    Select a cloud agent to enable chat.
                  </Text>
                  {/* The agents, right where the choice is asked for: one
                      row and one button each, so picking one is a click
                      rather than a trip to the dropdown above. */}
                  {visibleRuntimes.map(runtime => (
                    <Box
                      key={runtime.pod_name}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        p: 2,
                        border: '1px solid',
                        borderColor: 'border.default',
                        borderRadius: 2,
                      }}
                    >
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Text
                          sx={{
                            display: 'block',
                            fontSize: 1,
                            fontWeight: 'semibold',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                          title={runtime.pod_name}
                        >
                          {runtime.given_name}
                        </Text>
                        <Text
                          sx={{
                            display: 'block',
                            fontSize: 0,
                            color: 'fg.muted',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {runtime.environment_name}
                        </Text>
                      </Box>
                      <Button
                        size="small"
                        onClick={() => {
                          setSelectedRuntimePodName(runtime.pod_name);
                        }}
                      >
                        Use
                      </Button>
                    </Box>
                  ))}
                </Box>
              ) : !selectedRuntimeEndpoint ? (
                <Box sx={{ p: 3 }}>
                  <Text sx={{ color: 'danger.fg', fontSize: 1 }}>
                    Selected runtime has no ingress URL. Please choose another runtime.
                  </Text>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
                  <Box sx={{ flex: 1, minHeight: 0 }}>
                    <ChatPanel
                      protocol="vercel-ai"
                      baseUrl={selectedRuntimeEndpoint}
                      authToken={iamStore.getState().token}
                      agentId="default"
                      height="100%"
                      frontendTools={frontendTools}
                      // The chat sits in a JupyterLab sidebar, next to the
                      // panels of the application: it wears the theme of the
                      // lab (the JupyterReactTheme above), not its own — the
                      // internal boundary would restyle it as the web
                      // application.
                      disableInternalJupyterTheme
                      showModelSelector={true}
                      showToolsMenu={true}
                      showInformation={false}
                      showTokenUsage={false}
                      showToolApprovalBanner={false}
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
                  </Box>
                </Box>
              )}
            </Box>
          </QueryClientProvider>
        </Box>
      </JupyterReactTheme>
    </div>
  );
};
