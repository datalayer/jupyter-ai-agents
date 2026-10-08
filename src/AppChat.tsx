/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * A deployed application's agent, talked to in the AI Agents panel
 * (STUDIO A-19).
 *
 * The conversation is `@datalayer/agent-runtimes`' `<Chat>` over the
 * runtime's session API — an AG-UI run on
 * `<kept runtime>/api/v1/apps/agents/<agent>/ag-ui/`, each thread a session
 * (R-02), as the application's hosted page speaks to it. The person's token
 * goes only with the requests `signedHeaders` signs: the runtimes their
 * deployments are kept on, ai-agents' Tool Approvals, Spacer's items.
 *
 * Before the chat opens, the application's Appspec is read from its Spacer
 * item, and only the version the deployment runs decides — another one is
 * refused in a sentence. One that takes only a signed user (D-21) is opened
 * with a user token ai-agents signs for the person (`fetchUserToken`, with
 * their own token), put in each run's body as
 * `forwardedProps.loop.user_token` (`signedRunFetch`) while the chat is
 * open; what its host may pass (D-10) decides whether its
 * agent is given `host_context`, answered with the open notebook's selected
 * cell as `page`. Its approvals (R-05) are ai-agents' Tool Approvals,
 * polled while the chat is open and answered by `<Chat>`'s approval banner;
 * its tool calls are listed as the transcript's lines (A-06) under the
 * chat. The same design as the VS Code extension's `AppChat.tsx` (A-18).
 *
 * @module AppChat
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { Chat as ChatPanel } from '@datalayer/agent-runtimes/lib/chat/Chat';
import { Box } from '@datalayer/primer-addons';
import { Text } from '@primer/react';

import {
  agUiEndpoint,
  APP_CHAT_WORDS,
  appHostOf,
  appItemUrl,
  type AppChatApproval,
  type AppChatHandle,
  type AppHost,
  decideApprovalUrl,
  hostContextTool,
  type NotebookContext,
  notebookContextRefusal,
  pendingApprovalsOf,
  pendingApprovalsUrl,
  fetchUserToken,
  revisionRefusal,
  type SignedUser,
  signedHeaders,
  signedRunFetch,
  signedUserFresh,
  signsRequest,
  takesSignedUser,
  toolLineOf,
  userTokenRefusal
} from './appChat';

/** How often the approvals the agent waits on are read, while open. */
const APPROVALS_POLL_MS = 3_000;

/** Props for {@link AppChat}. */
export type AppChatProps = {
  /** The deployment talked to. */
  handle: AppChatHandle;
  /** The ai-agents and Spacer base URLs. */
  services: { aiAgentsUrl: string; spacerUrl: string };
  /** The person's Datalayer token. */
  token: string | undefined;
  /** What the token may be sent with (`signedPrefixesOf`). */
  prefixes: readonly string[];
  /** The person signed in. */
  user: { handle: string } | null;
  /** Reads the open notebook's selected cell now. */
  readNotebook: () => Promise<NotebookContext | undefined>;
};

/**
 * The detail of a refused answer, or its status.
 *
 * @param response - The answer.
 * @param what - What was asked, for the sentence.
 *
 * @returns The sentence.
 */
async function refusalOf(response: Response, what: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === 'string' && body.detail) {
      return body.detail;
    }
  } catch {
    // The status says it.
  }
  return `${what} was refused (${response.status}).`;
}

/**
 * A deployed application's chat: its Appspec read, then `<Chat>` on its
 * session API with its approvals, `host_context` and the transcript.
 *
 * @param props - Component props.
 *
 * @returns React element.
 */
export function AppChat(props: AppChatProps): React.JSX.Element {
  const { handle, services, token, prefixes, user, readNotebook } = props;
  const [host, setHost] = useState<AppHost | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [approvals, setApprovals] = useState<AppChatApproval[]>([]);
  const [lines, setLines] = useState<string[]>([]);

  /** A fetch carrying the person's token only where it is signed. */
  const signedFetch = useCallback(
    (url: string, init: RequestInit = {}): Promise<Response> =>
      fetch(url, {
        ...init,
        headers: signedHeaders(
          url,
          token,
          prefixes,
          (init.headers as Record<string, string> | undefined) ?? {}
        )
      }),
    [token, prefixes]
  );

  // The Appspec, from the application's Spacer item.
  useEffect(() => {
    let live = true;
    setHost(null);
    setProblem(null);
    setLines([]);
    void (async () => {
      try {
        const response = await signedFetch(
          appItemUrl(services.spacerUrl, handle.appUid)
        );
        if (!response.ok) {
          throw new Error(await refusalOf(response, 'Reading the application'));
        }
        const read = appHostOf(await response.json());
        if (live) {
          setHost(read);
        }
      } catch (error) {
        if (live) {
          setProblem(error instanceof Error ? error.message : String(error));
        }
      }
    })();
    return () => {
      live = false;
    };
  }, [handle.appUid, services.spacerUrl, signedFetch]);

  // Only the version deployed decides who its user is and what is passed.
  const revisionRefused = host ? revisionRefusal(handle, host) : '';
  const signed = Boolean(host && !revisionRefused && takesSignedUser(host));
  const [signedRefused, setSignedRefused] = useState('');
  const [signedReady, setSignedReady] = useState(false);
  const signedUser = useRef<SignedUser | null>(null);

  // A signed application (D-21): ai-agents signs the person, asked with
  // their own token; the user token goes in each run's body.
  const userToken = useCallback(async (): Promise<string> => {
    if (!signedUserFresh(signedUser.current, Date.now() / 1000)) {
      if (!token) {
        throw new Error('Sign in to Datalayer to talk to your applications.');
      }
      signedUser.current = await fetchUserToken(
        services.aiAgentsUrl,
        handle.uid,
        token
      );
    }
    return signedUser.current!.token;
  }, [services.aiAgentsUrl, handle.uid, token]);

  useEffect(() => {
    signedUser.current = null;
    setSignedRefused('');
    setSignedReady(false);
    if (!signed) {
      return;
    }
    let live = true;
    userToken()
      .then(() => {
        if (live) {
          setSignedReady(true);
        }
      })
      .catch(error => {
        if (live) {
          setSignedRefused(
            userTokenRefusal(
              handle.name,
              error instanceof Error ? error.message : String(error)
            )
          );
        }
      });
    const original = window.fetch;
    window.fetch = signedRunFetch(original.bind(window), handle, userToken);
    return () => {
      live = false;
      window.fetch = original;
    };
  }, [signed, handle, userToken]);

  const refused = revisionRefused || signedRefused;
  const waiting = signed && !signedReady && !signedRefused;

  // The approvals its agent waits on, while the chat is open.
  const readApprovals = useCallback(async (): Promise<void> => {
    try {
      const response = await signedFetch(
        pendingApprovalsUrl(services.aiAgentsUrl, handle.agentId)
      );
      if (response.ok) {
        setApprovals(pendingApprovalsOf(await response.json(), handle.agentId));
      }
    } catch {
      // Read again at the next tick.
    }
  }, [services.aiAgentsUrl, handle.agentId, signedFetch]);

  useEffect(() => {
    if (!host || refused) {
      return;
    }
    void readApprovals();
    const timer = setInterval(() => {
      void readApprovals();
    }, APPROVALS_POLL_MS);
    return () => {
      clearInterval(timer);
    };
  }, [host, refused, readApprovals]);

  const decide = useCallback(
    async (approvalId: string, approved: boolean): Promise<boolean> => {
      const response = await signedFetch(
        decideApprovalUrl(services.aiAgentsUrl, approvalId, approved),
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({})
        }
      );
      await readApprovals();
      return response.ok;
    },
    [services.aiAgentsUrl, readApprovals, signedFetch]
  );

  // What JupyterLab passes as the host (D-10): only the version deployed's
  // terms, never a guess.
  const notebookLine = host ? notebookContextRefusal(handle, host) : '';
  const frontendTools = useMemo(() => {
    if (!host || revisionRefusal(handle, host)) {
      return [];
    }
    const tool = hostContextTool(host, readNotebook, user);
    return tool ? [tool] : [];
  }, [host, handle, readNotebook, user]);

  const endpoint = agUiEndpoint(handle);

  if (problem || !host || refused || waiting) {
    return (
      <Box sx={{ p: 3 }}>
        <Text sx={{ color: problem ? 'danger.fg' : 'fg.muted', fontSize: 1 }}>
          {problem || refused || APP_CHAT_WORDS.reading}
        </Text>
      </Box>
    );
  }

  return (
    <Box
      sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}
    >
      <Box
        sx={{
          px: 2,
          py: 1,
          fontSize: 0,
          color: 'fg.muted',
          borderBottom: '1px solid',
          borderColor: 'border.default'
        }}
      >
        {notebookLine || APP_CHAT_WORDS.passesNotebook}
      </Box>
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ChatPanel
          key={handle.uid}
          protocol="ag-ui"
          baseUrl={handle.url}
          endpoint={endpoint}
          configEndpoint={`${handle.url}/api/v1/configure`}
          // The token goes with the session route only when it is signed.
          authToken={signsRequest(endpoint, prefixes) ? token : undefined}
          agentId={handle.agentId}
          height="100%"
          frontendTools={frontendTools}
          // The panel wears the lab's theme, as the runtimes' chat does.
          disableInternalJupyterTheme
          showInformation={false}
          showTokenUsage={false}
          onToolCallStart={({ toolName }) => {
            setLines(said => [
              ...said,
              toolLineOf(handle.name, toolName, host)
            ]);
          }}
          pendingApprovals={approvals}
          onApproveApproval={approvalId => decide(approvalId, true)}
          onRejectApproval={approvalId => decide(approvalId, false)}
        />
      </Box>
      <details
        style={{
          padding: '4px 8px',
          fontSize: '12px',
          borderTop: '1px solid var(--jp-border-color2)',
          maxHeight: '30%',
          overflow: 'auto',
          flexShrink: 0
        }}
      >
        <summary>
          {APP_CHAT_WORDS.transcript} ({lines.length})
        </summary>
        {lines.length === 0 ? (
          <Text as="p" sx={{ m: 0 }}>
            {APP_CHAT_WORDS.noLines}
          </Text>
        ) : (
          lines.map((line, index) => (
            <Text
              as="p"
              key={`${index}-${line}`}
              sx={{ my: '2px', fontFamily: 'mono' }}
            >
              {line}
            </Text>
          ))
        )}
      </details>
    </Box>
  );
}

export default AppChat;
