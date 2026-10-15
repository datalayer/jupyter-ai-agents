/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The agent over ACP (SHIELD SH-49): the panel's side of the runtime's ACP
 * route — the frames it sends, in order (initialize, authenticate with the
 * token in a message, session/new, the prompt), and the route's frames drawn
 * as rows. `EDIT_THEN_PUSH` is what agent-runtimes' route sent for the fake
 * harness's "edit then push" (recorded 2026-10-16 against the route served
 * by uvicorn; the workspace and the session id renamed): the Shield's own
 * *do it* write with its diff, the harness's edit, and the push the Rules
 * asked the panel about.
 */

import {
  AcpConversation,
  type AcpFrame,
  type AcpRow,
  acpAgentsOf,
  acpAgentsUrl,
  acpPanelEnabledOf,
  acpWebSocketUrl,
  displayPathOf,
  optionFor,
  unifiedDiff,
  withUpdate,
  initialAcpState
} from '../acpClient';

const TOKEN = 'header.payload.signature';

const EDIT_THEN_PUSH: Record<string, any>[] = [
  {
    jsonrpc: '2.0',
    id: 1,
    result: {
      protocolVersion: 1,
      authMethods: [
        {
          id: 'bearer',
          name: 'Bearer token',
          description: "The person's Datalayer token in `_meta.token`."
        }
      ],
      agentCapabilities: {
        loadSession: true,
        agent: {
          id: 'shield-fake',
          name: 'Fake harness (shielded)',
          description: '',
          version: '1.0.0'
        }
      }
    }
  },
  {
    jsonrpc: '2.0',
    id: 2,
    result: {}
  },
  {
    jsonrpc: '2.0',
    id: 3,
    result: {
      sessionId: 's-1',
      _meta: {
        datalayer: {
          workspace: '/runtime/workspace'
        }
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        sessionUpdate: 'agent_thought_chunk',
        content: {
          type: 'text',
          text: 'thinking'
        }
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        toolCallId: 'c1',
        title: 'Edit hello.txt',
        kind: 'edit',
        status: 'pending',
        rawInput: {
          path: 'hello.txt'
        },
        locations: [
          {
            path: 'hello.txt',
            line: null
          }
        ],
        sessionUpdate: 'tool_call'
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        toolCallId: 'shield_1',
        title: 'Write hello.txt — do it',
        kind: 'edit',
        status: 'in_progress',
        rawInput: {
          path: 'hello.txt',
          command: null
        },
        locations: [
          {
            path: 'hello.txt',
            line: null
          }
        ],
        sessionUpdate: 'tool_call'
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        sessionUpdate: 'tool_call_update',
        toolCallId: 'shield_1',
        status: 'completed',
        rawOutput: null,
        content: [
          {
            type: 'diff',
            path: 'hello.txt',
            oldText: null,
            newText: 'hello, shield\n'
          }
        ]
      }
    }
  },
  {
    jsonrpc: '2.0',
    id: 'perm_585bb5cc6029',
    method: 'session/request_permission',
    params: {
      sessionId: 's-1',
      toolCall: {
        toolCallId: 'c4',
        title: 'git push origin main',
        kind: 'execute',
        status: 'pending',
        rawInput: {
          command: 'git push origin main'
        },
        content: [
          {
            type: 'content',
            content: {
              type: 'text',
              text: "git push origin main (`git push origin main`): ask me first — session rule 'git push' (the command is shown)"
            }
          }
        ]
      },
      options: [
        {
          optionId: 'allow',
          name: 'Allow',
          kind: 'allow_once'
        },
        {
          optionId: 'reject',
          name: 'Reject',
          kind: 'reject_once'
        }
      ]
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        sessionUpdate: 'tool_call_update',
        toolCallId: 'c1',
        status: 'completed',
        rawOutput: null,
        content: [
          {
            type: 'diff',
            path: 'hello.txt',
            oldText: '',
            newText: 'hello, shield\n'
          }
        ]
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        toolCallId: 'c4',
        title: 'git push origin main',
        kind: 'execute',
        status: 'pending',
        rawInput: {
          sentence:
            "git push origin main (`git push origin main`): ask me first — session rule 'git push' (the command is shown)",
          command: 'git push origin main'
        },
        sessionUpdate: 'tool_call'
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        sessionUpdate: 'agent_message_chunk',
        content: {
          type: 'text',
          text: "push: field_meta=None option_id='allow' outcome='selected'"
        }
      }
    }
  },
  {
    jsonrpc: '2.0',
    method: 'session/update',
    params: {
      sessionId: 's-1',
      update: {
        sessionUpdate: 'agent_message_chunk',
        content: {
          type: 'text',
          text: 'done'
        }
      }
    }
  },
  {
    jsonrpc: '2.0',
    id: 4,
    result: {
      stopReason: 'end_turn'
    }
  }
];

/** A conversation whose sent frames are kept, answered by the recorded ones. */
function conversation(): { talk: AcpConversation; sent: AcpFrame[] } {
  const sent: AcpFrame[] = [];
  const talk = new AcpConversation(
    frame => sent.push(frame),
    TOKEN,
    '/home/jovyan/notebooks'
  );
  return { talk, sent };
}

const feed = (talk: AcpConversation, frames: Record<string, any>[]) =>
  frames.forEach(frame => talk.receive(JSON.stringify(frame)));

const rowsOf = <K extends AcpRow['kind']>(talk: AcpConversation, kind: K) =>
  talk.state.rows.filter(
    (row): row is Extract<AcpRow, { kind: K }> => row.kind === kind
  );

describe('acpAgentEnabled', () => {
  it('is on only when set to true', () => {
    expect(acpPanelEnabledOf(undefined)).toBe(false);
    expect(acpPanelEnabledOf({})).toBe(false);
    expect(acpPanelEnabledOf({ acpAgentEnabled: 'true' })).toBe(false);
    expect(acpPanelEnabledOf({ acpAgentEnabled: true })).toBe(true);
  });
});

describe("the runtime's ACP addresses", () => {
  it("is the runtime's websocket, with the agent in the path", () => {
    expect(
      acpWebSocketUrl(
        'https://r1.datalayer.run/agent-runtimes/pool/pod-1/',
        'shield-fake'
      )
    ).toBe(
      'wss://r1.datalayer.run/agent-runtimes/pool/pod-1/api/v1/acp/ws/shield-fake'
    );
    expect(acpWebSocketUrl('http://127.0.0.1:8765', 'apps/a b')).toBe(
      'ws://127.0.0.1:8765/api/v1/acp/ws/apps/a%20b'
    );
    expect(acpAgentsUrl('http://127.0.0.1:8765/')).toBe(
      'http://127.0.0.1:8765/api/v1/acp/agents'
    );
  });

  it('never carries a token in the address', () => {
    expect(() =>
      acpWebSocketUrl('https://r1.datalayer.run/x?token=abc', 'a')
    ).toThrow('A token never goes in the address');
    expect(() => acpWebSocketUrl('ftp://x', 'a')).toThrow('not http(s)');
    expect(() => acpWebSocketUrl('http://x', ' ')).toThrow('Name the agent');
  });

  it('lists the agents the runtime serves over ACP', () => {
    expect(
      acpAgentsOf({
        agents: [{ id: 'shield-fake', name: 'Fake' }, { name: 'no id' }]
      })
    ).toEqual([{ id: 'shield-fake', name: 'Fake', description: '' }]);
    expect(acpAgentsOf(null)).toEqual([]);
  });
});

describe('unifiedDiff', () => {
  it('says a new file against /dev/null', () => {
    expect(unifiedDiff('hello.txt', null, 'hello, shield\n')).toBe(
      '--- /dev/null\n+++ b/hello.txt\n@@ -0,0 +1,1 @@\n+hello, shield\n'
    );
  });

  it('says an edit with three lines of context, in hunks', () => {
    const before = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
      .map(l => `${l}\n`)
      .join('');
    const after = before.replace('b\n', 'B\n').replace('k\n', 'K\nK2\n');
    expect(unifiedDiff('x.py', before, after)).toBe(
      [
        '--- a/x.py',
        '+++ b/x.py',
        '@@ -1,5 +1,5 @@',
        ' a',
        '-b',
        '+B',
        ' c',
        ' d',
        ' e',
        '@@ -8,5 +8,6 @@',
        ' h',
        ' i',
        ' j',
        '-k',
        '+K',
        '+K2',
        ' l',
        ''
      ].join('\n')
    );
  });

  it('is empty when nothing changed', () => {
    expect(unifiedDiff('x', 'same\n', 'same\n')).toBe('');
  });
});

describe('displayPathOf', () => {
  it('says a path in the workspace relative to it', () => {
    expect(
      displayPathOf('/runtime/workspace/nb/a.ipynb', '/runtime/workspace/')
    ).toBe('nb/a.ipynb');
    expect(displayPathOf('/etc/hostname', '/runtime/workspace')).toBe(
      '/etc/hostname'
    );
    expect(displayPathOf('hello.txt', undefined)).toBe('hello.txt');
  });
});

describe("AcpConversation against the route's frames", () => {
  it('initializes, authenticates in a message and opens a session, in order', () => {
    const { talk, sent } = conversation();
    talk.open();
    expect(sent[0]).toMatchObject({ id: 1, method: 'initialize' });
    feed(talk, EDIT_THEN_PUSH.slice(0, 1));
    // The token in `_meta.token`, never in the address.
    expect(sent[1]).toEqual({
      jsonrpc: '2.0',
      id: 2,
      method: 'authenticate',
      params: { methodId: 'bearer', _meta: { token: TOKEN } }
    });
    feed(talk, EDIT_THEN_PUSH.slice(1, 2));
    expect(sent[2]).toMatchObject({
      method: 'session/new',
      params: { cwd: '/home/jovyan/notebooks', mcpServers: [] }
    });
    feed(talk, EDIT_THEN_PUSH.slice(2, 3));
    expect(talk.state.phase).toBe('ready');
    expect(talk.state.sessionId).toBe('s-1');
    expect(talk.state.workspace).toBe('/runtime/workspace');
    expect(talk.state.agentName).toBe('Fake harness (shielded)');
  });

  it('draws the diffs, asks the push and answers it with the option id', () => {
    const { talk, sent } = conversation();
    talk.open();
    feed(talk, EDIT_THEN_PUSH.slice(0, 3));
    expect(talk.prompt('edit then push')).toBe(true);
    expect(sent[3]).toEqual({
      jsonrpc: '2.0',
      id: 4,
      method: 'session/prompt',
      params: {
        sessionId: 's-1',
        prompt: [{ type: 'text', text: 'edit then push' }]
      }
    });
    expect(talk.prompt('again')).toBe(false); // one turn at a time
    // Up to the permission request.
    feed(talk, EDIT_THEN_PUSH.slice(3, 8));
    const [asked] = rowsOf(talk, 'permission');
    expect(asked).toMatchObject({
      requestId: 'perm_585bb5cc6029',
      title: 'git push origin main',
      toolKind: 'execute',
      command: 'git push origin main'
    });
    expect(asked.sentence).toContain('ask me first');
    expect(optionFor(asked.options, 'approve')).toBe('allow');
    expect(optionFor(asked.options, 'reject')).toBe('reject');
    talk.decide(asked.requestId, 'allow');
    expect(sent[4]).toEqual({
      jsonrpc: '2.0',
      id: 'perm_585bb5cc6029',
      result: { outcome: { outcome: 'selected', optionId: 'allow' } }
    });
    // Answered once: a second click sends nothing.
    talk.decide(asked.requestId, 'reject');
    expect(sent).toHaveLength(5);
    feed(talk, EDIT_THEN_PUSH.slice(8));
    expect(talk.state.phase).toBe('ready');
    expect(talk.state.stopReason).toBe('end_turn');
    const tools = rowsOf(talk, 'tool');
    expect(tools.map(t => [t.toolCallId, t.title, t.status])).toEqual([
      ['c1', 'Edit hello.txt', 'completed'],
      ['shield_1', 'Write hello.txt — do it', 'completed'],
      ['c4', 'git push origin main', 'pending']
    ]);
    // The Shield's write: a new file. The harness's edit: from empty.
    expect(tools[1].diffs).toEqual([
      {
        path: 'hello.txt',
        displayPath: 'hello.txt',
        created: true,
        unified:
          '--- /dev/null\n+++ b/hello.txt\n@@ -0,0 +1,1 @@\n+hello, shield\n',
        added: 1,
        removed: 0
      }
    ]);
    expect(tools[0].diffs[0].unified).toContain('--- a/hello.txt');
    expect(rowsOf(talk, 'thought').map(r => r.text)).toEqual(['thinking']);
    // The two message chunks, one row.
    expect(rowsOf(talk, 'agent').map(r => r.text)).toEqual([
      "push: field_meta=None option_id='allow' outcome='selected'done"
    ]);
    expect(rowsOf(talk, 'user').map(r => r.text)).toEqual(['edit then push']);
    expect(rowsOf(talk, 'said')).toEqual([]);
  });

  it('answers cancelled, and closes a question the turn ended without', () => {
    const { talk, sent } = conversation();
    talk.open();
    feed(talk, EDIT_THEN_PUSH.slice(0, 3));
    talk.prompt('push');
    feed(talk, [EDIT_THEN_PUSH[7]]);
    talk.decide('perm_585bb5cc6029', null);
    expect(sent[sent.length - 1]).toEqual({
      jsonrpc: '2.0',
      id: 'perm_585bb5cc6029',
      result: { outcome: { outcome: 'cancelled' } }
    });
    // An option the harness did not offer is not sent.
    const { talk: other, sent: otherSent } = conversation();
    other.open();
    feed(other, EDIT_THEN_PUSH.slice(0, 3));
    other.prompt('push');
    feed(other, [EDIT_THEN_PUSH[7]]);
    other.decide('perm_585bb5cc6029', 'always');
    expect(otherSent).toHaveLength(4);
    feed(other, [{ jsonrpc: '2.0', id: 4, result: { stopReason: 'refusal' } }]);
    expect(rowsOf(other, 'permission')[0].answer).toBeNull();
    expect(rowsOf(other, 'said').map(r => [r.tone, r.text])).toEqual([
      ['error', 'The turn ended refused: the Shield said why above.']
    ]);
  });

  it("refuses the panel's filesystem and says the route's errors", () => {
    const { talk, sent } = conversation();
    talk.open();
    feed(talk, EDIT_THEN_PUSH.slice(0, 3));
    talk.receive(
      JSON.stringify({
        jsonrpc: '2.0',
        id: 'fs1',
        method: 'fs/read_text_file',
        params: { path: '/etc/hostname' }
      })
    );
    expect(sent[sent.length - 1]).toMatchObject({
      id: 'fs1',
      error: { code: -32601 }
    });
    talk.prompt('x');
    talk.receive(
      JSON.stringify({
        jsonrpc: '2.0',
        id: 4,
        error: { code: -32001, message: 'Session not found: s-1' }
      })
    );
    expect(talk.state.phase).toBe('ready');
    expect(rowsOf(talk, 'said').map(r => r.text)).toEqual([
      'Session not found: s-1'
    ]);
    talk.receive('not json');
    expect(rowsOf(talk, 'said')).toHaveLength(2);
  });

  it('stops when the runtime takes no token in a message, or none is held', () => {
    const { talk, sent } = conversation();
    talk.open();
    feed(talk, [
      {
        jsonrpc: '2.0',
        id: 1,
        result: { protocolVersion: 1, agentCapabilities: {} }
      }
    ]);
    expect(sent).toHaveLength(1);
    expect(talk.state.phase).toBe('closed');
    expect(rowsOf(talk, 'said')[0].text).toContain(
      'needs a newer agent-runtimes'
    );
    const none: AcpFrame[] = [];
    const anonymous = new AcpConversation(f => none.push(f), '', '/');
    anonymous.open();
    expect(none).toEqual([]);
    expect(anonymous.state.phase).toBe('closed');
  });

  it('keeps a plan as one row, replaced by the next', () => {
    const planned = withUpdate(initialAcpState(), {
      sessionUpdate: 'plan',
      entries: [{ content: 'one', status: 'pending', priority: 'medium' }]
    });
    const replanned = withUpdate(planned, {
      sessionUpdate: 'plan',
      entries: [{ content: 'one', status: 'completed', priority: 'medium' }]
    });
    expect(replanned.rows).toHaveLength(1);
    expect(replanned.rows[0]).toMatchObject({
      kind: 'plan',
      entries: [{ content: 'one', status: 'completed' }]
    });
  });
});
