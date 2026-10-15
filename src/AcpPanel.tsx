/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The agent over ACP (SHIELD SH-49): the panel as the ACP client of a
 * shielded harness on the runtime picked. The logic is `acpClient.ts`'s
 * ({@link AcpConversation}); this view lists the runtime's ACP agents, opens
 * the socket, and draws the rows — the agent's words, each tool call with its
 * diffs, the plan, and each question the Shield's Rules let through with
 * Approve and Reject answering by the harness's option ids.
 *
 * @module AcpPanel
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box } from '@datalayer/primer-addons';
import { Button, Select, Spinner, Text, Textarea } from '@primer/react';
import {
  ACP_WORDS,
  type AcpAgentChoice,
  AcpConversation,
  type AcpDiff,
  type AcpRow,
  type AcpState,
  acpAgentsOf,
  acpAgentsUrl,
  acpWebSocketUrl,
  initialAcpState,
  optionFor
} from './acpClient';

/** Props of {@link AcpPanel}. */
export type AcpPanelProps = {
  /** The runtime's agent-runtimes URL (`https://…/agent-runtimes/…`). */
  runtimeUrl: string;
  /** The person's Datalayer token: said in `authenticate`, never in the address. */
  token: string;
  /** The notebook's folder, sent as the session's cwd (the runtime answers with its workspace). */
  cwd: string;
};

/**
 * A unified diff, its lines coloured.
 *
 * @param props - The diff.
 *
 * @returns Its view.
 */
const DiffView: React.FC<{ diff: AcpDiff }> = ({ diff }) => (
  <Box sx={{ mt: 1 }}>
    <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
      {diff.displayPath}
      {diff.created ? ' (new)' : ''} +{diff.added} −{diff.removed}
    </Text>
    <Box
      as="pre"
      sx={{
        m: 0,
        p: 1,
        fontSize: 0,
        overflowX: 'auto',
        bg: 'canvas.inset',
        borderRadius: 1
      }}
    >
      {diff.unified.split('\n').map((line, index) => (
        <Box
          as="span"
          key={index}
          sx={{
            display: 'block',
            color:
              line.startsWith('+') && !line.startsWith('+++')
                ? 'success.fg'
                : line.startsWith('-') && !line.startsWith('---')
                  ? 'danger.fg'
                  : line.startsWith('@@')
                    ? 'accent.fg'
                    : 'fg.default'
          }}
        >
          {line || ' '}
        </Box>
      ))}
    </Box>
  </Box>
);

/**
 * One row of the transcript.
 *
 * @param props - The row, and how a question is answered.
 *
 * @returns Its view.
 */
const RowView: React.FC<{
  row: AcpRow;
  decide: (requestId: string | number, optionId: string | null) => void;
  open: boolean;
}> = ({ row, decide, open }) => {
  switch (row.kind) {
    case 'user':
      return (
        <Box
          sx={{
            alignSelf: 'flex-end',
            bg: 'accent.subtle',
            p: 2,
            borderRadius: 2
          }}
        >
          <Text sx={{ fontSize: 1, whiteSpace: 'pre-wrap' }}>{row.text}</Text>
        </Box>
      );
    case 'agent':
      return (
        <Text sx={{ fontSize: 1, whiteSpace: 'pre-wrap' }}>{row.text}</Text>
      );
    case 'thought':
      return (
        <Text sx={{ fontSize: 0, color: 'fg.muted', fontStyle: 'italic' }}>
          {row.text}
        </Text>
      );
    case 'plan':
      return (
        <Box as="ul" sx={{ m: 0, pl: 3, fontSize: 0 }}>
          {row.entries.map((entry, index) => (
            <li key={index}>
              [{entry.status}] {entry.content}
            </li>
          ))}
        </Box>
      );
    case 'said':
      return (
        <Text
          sx={{
            fontSize: 0,
            color: row.tone === 'error' ? 'danger.fg' : 'fg.muted'
          }}
        >
          {row.text}
        </Text>
      );
    case 'tool':
      return (
        <Box
          sx={{
            border: '1px solid',
            borderColor: 'border.default',
            borderRadius: 2,
            p: 2
          }}
        >
          <Text sx={{ fontSize: 0, fontWeight: 'semibold' }}>{row.title}</Text>
          <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
            {' '}
            · {row.toolKind} · {row.status}
          </Text>
          {row.diffs.map((diff, index) => (
            <DiffView key={index} diff={diff} />
          ))}
          {row.texts.map((said, index) => (
            <Box
              as="pre"
              key={index}
              sx={{ m: 0, mt: 1, fontSize: 0, whiteSpace: 'pre-wrap' }}
            >
              {said}
            </Box>
          ))}
          {row.terminals.map(terminal => (
            <Text
              key={terminal}
              sx={{ display: 'block', fontSize: 0, color: 'fg.muted' }}
            >
              Terminal {terminal} (the runtime's)
            </Text>
          ))}
        </Box>
      );
    case 'permission': {
      const approve = optionFor(row.options, 'approve');
      const reject = optionFor(row.options, 'reject');
      const chosen = row.options.find(option => option.optionId === row.answer);
      return (
        <Box
          sx={{
            border: '1px solid',
            borderColor: 'attention.emphasis',
            bg: 'attention.subtle',
            borderRadius: 2,
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 1
          }}
        >
          <Text sx={{ fontSize: 1, fontWeight: 'semibold' }}>{row.title}</Text>
          {row.command && (
            <Box as="pre" sx={{ m: 0, fontSize: 0 }}>
              {row.command}
            </Box>
          )}
          {row.sentence && (
            <Text sx={{ fontSize: 0, color: 'fg.muted' }}>{row.sentence}</Text>
          )}
          {row.answer === undefined && open ? (
            <Box sx={{ display: 'flex', gap: 2 }}>
              {approve && (
                <Button
                  size="small"
                  variant="primary"
                  onClick={() => decide(row.requestId, approve)}
                >
                  {ACP_WORDS.approve}
                </Button>
              )}
              {reject && (
                <Button
                  size="small"
                  variant="danger"
                  onClick={() => decide(row.requestId, reject)}
                >
                  {ACP_WORDS.reject}
                </Button>
              )}
            </Box>
          ) : (
            <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
              {chosen ? `Answered: ${chosen.name}` : 'Not answered'}
            </Text>
          )}
        </Box>
      );
    }
    default:
      return null;
  }
};

/**
 * The agent over ACP on the runtime picked.
 *
 * @param props - The runtime, the token, the notebook's folder.
 *
 * @returns The panel.
 */
export const AcpPanel: React.FC<AcpPanelProps> = ({
  runtimeUrl,
  token,
  cwd
}) => {
  const [agents, setAgents] = useState<AcpAgentChoice[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [agentId, setAgentId] = useState<string>('');
  const [state, setState] = useState<AcpState | null>(null);
  const [draft, setDraft] = useState('');
  const socket = useRef<WebSocket | null>(null);
  const talk = useRef<AcpConversation | null>(null);

  // The agents the runtime serves over ACP.
  useEffect(() => {
    let live = true;
    setAgents(null);
    setListError(null);
    fetch(acpAgentsUrl(runtimeUrl), {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error(
            `Listing the runtime's ACP agents was refused (${response.status}).`
          );
        }
        const listed = acpAgentsOf(await response.json());
        if (live) {
          setAgents(listed);
          setAgentId(current => current || listed[0]?.id || '');
        }
      })
      .catch(err => {
        if (live) {
          setAgents([]);
          setListError(err instanceof Error ? err.message : String(err));
        }
      });
    return () => {
      live = false;
    };
  }, [runtimeUrl, token]);

  const disconnect = useCallback(() => {
    socket.current?.close();
    socket.current = null;
    talk.current = null;
  }, []);

  // A new runtime or agent: the connection goes with the old one.
  useEffect(() => disconnect, [runtimeUrl, agentId, disconnect]);

  const connect = useCallback(() => {
    disconnect();
    let address: string;
    try {
      address = acpWebSocketUrl(runtimeUrl, agentId);
    } catch (err) {
      setState({
        ...initialAcpState(),
        phase: 'closed',
        rows: [
          {
            kind: 'said',
            id: 'r0',
            tone: 'error',
            text: err instanceof Error ? err.message : String(err)
          }
        ]
      });
      return;
    }
    const opened = new WebSocket(address);
    const conversation = new AcpConversation(
      frame => {
        if (opened.readyState === WebSocket.OPEN) {
          opened.send(JSON.stringify(frame));
        }
      },
      token,
      cwd,
      setState
    );
    socket.current = opened;
    talk.current = conversation;
    setState(conversation.state);
    opened.onopen = () => conversation.open();
    opened.onmessage = event => conversation.receive(String(event.data));
    opened.onclose = () => conversation.closed();
  }, [runtimeUrl, agentId, token, cwd, disconnect]);

  const send = useCallback(() => {
    if (talk.current?.prompt(draft)) {
      setDraft('');
    }
  }, [draft]);

  const decide = useCallback(
    (requestId: string | number, optionId: string | null) =>
      talk.current?.decide(requestId, optionId),
    []
  );

  const phase = state?.phase;
  const open = phase !== undefined && phase !== 'closed';
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        gap: 2,
        p: 2
      }}
    >
      <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
        {ACP_WORDS.modeDescription}
      </Text>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        {agents === null ? (
          <Spinner size="small" />
        ) : (
          <Select
            aria-label="ACP agent"
            value={agentId}
            onChange={event => setAgentId(event.target.value)}
            disabled={agents.length === 0}
          >
            {agents.map(agent => (
              <Select.Option key={agent.id} value={agent.id}>
                {agent.name}
              </Select.Option>
            ))}
          </Select>
        )}
        {open ? (
          <Button size="small" onClick={disconnect}>
            Disconnect
          </Button>
        ) : (
          <Button
            size="small"
            variant="primary"
            disabled={!agentId}
            onClick={connect}
          >
            Connect
          </Button>
        )}
        {phase && <Text sx={{ fontSize: 0, color: 'fg.muted' }}>{phase}</Text>}
      </Box>
      {listError && (
        <Text sx={{ fontSize: 0, color: 'danger.fg' }}>{listError}</Text>
      )}
      {agents !== null && agents.length === 0 && !listError && (
        <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
          This runtime serves no agent over ACP.
        </Text>
      )}
      {state?.workspace && (
        <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
          {ACP_WORDS.workspace}: <code>{state.workspace}</code>
        </Text>
      )}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        {(state?.rows ?? []).map(row => (
          <RowView key={row.id} row={row} decide={decide} open={open} />
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
        <Box sx={{ flex: 1 }}>
          <Textarea
            aria-label="Prompt"
            block
            value={draft}
            onChange={event => setDraft(event.target.value)}
            onKeyDown={event => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                send();
              }
            }}
            disabled={phase !== 'ready'}
            resize="vertical"
          />
        </Box>
        {phase === 'working' ? (
          <Button size="small" onClick={() => talk.current?.cancel()}>
            Cancel
          </Button>
        ) : (
          <Button
            size="small"
            variant="primary"
            disabled={phase !== 'ready' || !draft.trim()}
            onClick={send}
          >
            Send
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default AcpPanel;
