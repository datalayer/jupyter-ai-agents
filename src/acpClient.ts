/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * An agent over ACP in the AI Agents panel (SHIELD SH-49).
 *
 * The panel is the ACP *client* of a shielded harness on a Datalayer runtime:
 * it opens the runtime's ACP endpoint, `<runtime>/api/v1/acp/ws/<agent>`,
 * and speaks ACP over it — `initialize`, then `authenticate` with methodId
 * `bearer` and the person's token in `_meta.token` (a browser's websocket
 * carries no header, and a token never goes in the address), then
 * `session/new`, whose answer says the runtime's workspace
 * (`_meta.datalayer.workspace`): the harness edits the files there, not the
 * notebook's own folder. Each prompt is a `session/prompt`; what comes back
 * is drawn as rows — the agent's words and thoughts, each tool call with its
 * diffs as unified diffs (paths said relative to the workspace), its text
 * and its terminals, the plan, and each `session/request_permission` the
 * Shield's Rules let through (*ask me first*) with its options, answered by
 * the option id the person chose. What the Rules did themselves (*do it*,
 * *leave it to me*) never reaches the panel as a question: it shows as the
 * harness's tool calls and the Shield's sentences.
 *
 * Pure: no JupyterLab, no React, no WebSocket — the frames are handed in and
 * out ({@link AcpConversation}); `AcpPanel.tsx`, the view, wires a socket
 * to it (named apart from it by more than case: a case-insensitive file
 * system would take one for the other).
 *
 * @module acpClient
 */

/** The plugin's setting turning the mode on (off by default). */
export const ACP_PANEL_SETTING = 'acpAgentEnabled';

/** The one authentication method the runtime's route takes in a message. */
export const ACP_AUTH_METHOD = 'bearer';

/** ACP's protocol version the panel speaks. */
export const ACP_PROTOCOL_VERSION = 1;

/** Names in a query string that would carry a token: never sent. */
const ADDRESS_TOKENS = ['token', 'access_token', 'bearer', 'api_key', 'apikey'];

/**
 * Reads a value as a record.
 *
 * @param value - Anything.
 *
 * @returns It, when it is a plain object; else an empty one.
 */
const record = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};

/**
 * Reads a value as a string.
 *
 * @param value - Anything.
 *
 * @returns It, when it is a string; else an empty one.
 */
const text = (value: unknown): string =>
  typeof value === 'string' ? value : '';

/**
 * Whether the agent over ACP is turned on (`acpAgentEnabled`, off by default).
 *
 * @param composite - The plugin's settings, as JupyterLab composes them.
 *
 * @returns True only when the setting is exactly `true`.
 */
export function acpPanelEnabledOf(composite: unknown): boolean {
  return record(composite)[ACP_PANEL_SETTING] === true;
}

/**
 * The runtime's ACP endpoint for an agent, as a websocket address.
 *
 * @param runtimeUrl - The runtime's agent-runtimes URL (`http(s)://…`).
 * @param agentId - The agent whose harness is talked to.
 *
 * @returns The `ws(s)://…/api/v1/acp/ws/<agent>` address.
 *
 * @throws When the URL is not http(s), or carries a token in its query.
 */
export function acpWebSocketUrl(runtimeUrl: string, agentId: string): string {
  const url = new URL(runtimeUrl);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new Error(`The runtime's address is not http(s): ${runtimeUrl}`);
  }
  for (const name of url.searchParams.keys()) {
    if (ADDRESS_TOKENS.includes(name.toLowerCase())) {
      throw new Error(
        'A token never goes in the address: the panel authenticates in a message.'
      );
    }
  }
  if (!agentId.trim()) {
    throw new Error('Name the agent to talk to over ACP.');
  }
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.search = '';
  url.hash = '';
  const agent = agentId
    .split('/')
    .map(segment => encodeURIComponent(segment))
    .join('/');
  url.pathname = `${url.pathname.replace(/\/+$/, '')}/api/v1/acp/ws/${agent}`;
  return url.toString();
}

/**
 * The runtime's ACP agents listing address.
 *
 * @param runtimeUrl - The runtime's agent-runtimes URL.
 *
 * @returns `<runtime>/api/v1/acp/agents`.
 */
export function acpAgentsUrl(runtimeUrl: string): string {
  return `${runtimeUrl.replace(/\/+$/, '')}/api/v1/acp/agents`;
}

/** An agent the runtime serves over ACP. */
export type AcpAgentChoice = { id: string; name: string; description: string };

/**
 * The agents of the runtime's `GET /api/v1/acp/agents`.
 *
 * @param body - The listing's JSON.
 *
 * @returns Each agent with an id.
 */
export function acpAgentsOf(body: unknown): AcpAgentChoice[] {
  const agents = record(body).agents;
  return (Array.isArray(agents) ? agents : []).flatMap(item => {
    const agent = record(item);
    const id = text(agent.id);
    return id
      ? [
          {
            id,
            name: text(agent.name) || id,
            description: text(agent.description)
          }
        ]
      : [];
  });
}

/**
 * A path as the panel says it: relative to the runtime's workspace when it
 * lies in it, as given otherwise.
 *
 * @param path - The harness's path (absolute or the workspace's relative).
 * @param workspace - The runtime's workspace, when the route said it.
 *
 * @returns The path to show.
 */
export function displayPathOf(path: string, workspace?: string): string {
  if (!workspace) {
    return path;
  }
  const root = workspace.replace(/\/+$/, '');
  if (path === root) {
    return '.';
  }
  return path.startsWith(`${root}/`) ? path.slice(root.length + 1) : path;
}

/**
 * The lines of a text, as a diff counts them.
 *
 * @param value - The text.
 *
 * @returns Its lines, without a last empty one after a final newline.
 */
function linesOf(value: string): string[] {
  if (value === '') {
    return [];
  }
  const lines = value.split('\n');
  if (lines[lines.length - 1] === '') {
    lines.pop();
  }
  return lines;
}

/** One line of an edit script. */
type Edit = { op: ' ' | '-' | '+'; line: string; a: number; b: number };

/**
 * The edit script from one list of lines to another (longest common
 * subsequence; texts a harness edits are a file's, so the table is small).
 *
 * @param before - The old lines.
 * @param after - The new lines.
 *
 * @returns Each line kept, removed or added, with its line numbers.
 */
function editsOf(before: string[], after: string[]): Edit[] {
  const n = before.length;
  const m = after.length;
  const common: number[][] = Array.from({ length: n + 1 }, () =>
    new Array<number>(m + 1).fill(0)
  );
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      common[i][j] =
        before[i] === after[j]
          ? common[i + 1][j + 1] + 1
          : Math.max(common[i + 1][j], common[i][j + 1]);
    }
  }
  const edits: Edit[] = [];
  let i = 0;
  let j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && before[i] === after[j]) {
      edits.push({ op: ' ', line: before[i], a: i, b: j });
      i++;
      j++;
    } else if (i < n && (j >= m || common[i + 1][j] >= common[i][j + 1])) {
      // A removal before an addition, as `diff -u` writes a change.
      edits.push({ op: '-', line: before[i], a: i, b: j });
      i++;
    } else {
      edits.push({ op: '+', line: after[j], a: i, b: j });
      j++;
    }
  }
  return edits;
}

/**
 * A unified diff of a harness's edit, as `diff -u` writes it (three lines of
 * context); a new file is said against `/dev/null`.
 *
 * @param path - The file's path, as shown.
 * @param oldText - Its text before (`null` or absent: a new file).
 * @param newText - Its text after.
 *
 * @returns The diff, ending with a newline; empty when nothing changed.
 */
export function unifiedDiff(
  path: string,
  oldText: string | null | undefined,
  newText: string
): string {
  const created = oldText === null || oldText === undefined;
  const before = linesOf(oldText ?? '');
  const after = linesOf(newText);
  const edits = editsOf(before, after);
  if (edits.every(edit => edit.op === ' ')) {
    return '';
  }
  const context = 3;
  const hunks: string[] = [];
  let index = 0;
  while (index < edits.length) {
    if (edits[index].op === ' ') {
      index++;
      continue;
    }
    // A hunk: the changes from here, joined while the context between them
    // is short enough to touch, with the context around them.
    const start = Math.max(0, index - context);
    let end = index;
    let last = index;
    while (end < edits.length) {
      if (edits[end].op !== ' ') {
        last = end;
      } else if (end - last > 2 * context) {
        break;
      }
      end++;
    }
    const stop = Math.min(edits.length, last + context + 1);
    const slice = edits.slice(start, stop);
    const oldCount = slice.filter(edit => edit.op !== '+').length;
    const newCount = slice.filter(edit => edit.op !== '-').length;
    const oldStart = oldCount ? slice[0].a + 1 : slice[0].a;
    const newStart = newCount ? slice[0].b + 1 : slice[0].b;
    hunks.push(
      `@@ -${oldStart},${oldCount} +${newStart},${newCount} @@\n` +
        slice.map(edit => `${edit.op}${edit.line}\n`).join('')
    );
    index = stop;
  }
  const from = created ? '/dev/null' : `a/${path}`;
  return `--- ${from}\n+++ b/${path}\n${hunks.join('')}`;
}

/** A harness's edit, drawn. */
export type AcpDiff = {
  /** The path the harness said. */
  path: string;
  /** The path shown: the workspace's relative one. */
  displayPath: string;
  /** Whether the file is new. */
  created: boolean;
  /** The unified diff. */
  unified: string;
  /** Lines added. */
  added: number;
  /** Lines removed. */
  removed: number;
};

/** A permission option, as the harness offered it. */
export type AcpOption = { optionId: string; name: string; kind: string };

/** One row of the panel's transcript. */
export type AcpRow =
  | { kind: 'user'; id: string; text: string }
  | { kind: 'agent'; id: string; text: string }
  | { kind: 'thought'; id: string; text: string }
  | {
      kind: 'tool';
      id: string;
      toolCallId: string;
      title: string;
      toolKind: string;
      status: string;
      diffs: AcpDiff[];
      texts: string[];
      terminals: string[];
    }
  | {
      kind: 'permission';
      id: string;
      /** The JSON-RPC id of the route's request: the answer carries it. */
      requestId: string | number;
      title: string;
      toolKind: string;
      /** The command, when the harness said one. */
      command: string;
      /** The Shield's sentence: which Rule asked, and why. */
      sentence: string;
      options: AcpOption[];
      /** The option chosen, `null` once cancelled; absent while open. */
      answer?: string | null;
    }
  | {
      kind: 'plan';
      id: string;
      entries: { content: string; status: string; priority: string }[];
    }
  | { kind: 'said'; id: string; tone: 'info' | 'error'; text: string };

/** Where the conversation stands. */
export type AcpPhase =
  | 'connecting'
  | 'initializing'
  | 'authenticating'
  | 'opening'
  | 'ready'
  | 'working'
  | 'closed';

/** The panel's state: its rows and its session. */
export type AcpState = {
  phase: AcpPhase;
  rows: AcpRow[];
  sessionId?: string;
  /** The runtime's workspace, where the harness's paths are. */
  workspace?: string;
  /** The agent's name, as `initialize` said it. */
  agentName?: string;
  /** The last turn's stop reason. */
  stopReason?: string;
};

/** The state before anything is sent. */
export const initialAcpState = (): AcpState => ({
  phase: 'connecting',
  rows: []
});

/** The words the panel says. */
export const ACP_WORDS = {
  mode: 'Agent over ACP',
  modeDescription:
    "A shielded harness on this runtime, over ACP: its edits in the runtime's workspace, its questions here.",
  approve: 'Approve',
  reject: 'Reject',
  workspace: "Editing the runtime's workspace",
  stopped: (reason: string) =>
    reason === 'end_turn'
      ? ''
      : reason === 'refusal'
        ? 'The turn ended refused: the Shield said why above.'
        : reason === 'cancelled'
          ? 'The turn was cancelled.'
          : `The turn ended: ${reason}.`,
  closed: 'The connection to the runtime closed.',
  noToken:
    'Sign in to Datalayer first: the runtime is told who you are in a message.'
};

/**
 * The option an Approve or a Reject answers with.
 *
 * @param options - The harness's options.
 * @param choice - `approve` (allow once, else always) or `reject` (reject once, else always).
 *
 * @returns The option's id, or `undefined` when the harness offered none of that kind.
 */
export function optionFor(
  options: AcpOption[],
  choice: 'approve' | 'reject'
): string | undefined {
  const kinds =
    choice === 'approve'
      ? ['allow_once', 'allow_always']
      : ['reject_once', 'reject_always'];
  for (const kind of kinds) {
    const found = options.find(option => option.kind === kind);
    if (found) {
      return found.optionId;
    }
  }
  return undefined;
}

/**
 * A tool call's content as the panel draws it.
 *
 * @param content - ACP's tool call content.
 * @param workspace - The runtime's workspace.
 *
 * @returns Its diffs, texts and terminals.
 */
function contentOf(
  content: unknown,
  workspace?: string
): { diffs: AcpDiff[]; texts: string[]; terminals: string[] } {
  const diffs: AcpDiff[] = [];
  const texts: string[] = [];
  const terminals: string[] = [];
  for (const item of Array.isArray(content) ? content : []) {
    const part = record(item);
    if (part.type === 'diff') {
      const path = text(part.path);
      const displayPath = displayPathOf(path, workspace);
      const oldText =
        part.oldText === null || part.oldText === undefined
          ? null
          : text(part.oldText);
      const unified = unifiedDiff(displayPath, oldText, text(part.newText));
      const lines = unified.split('\n');
      diffs.push({
        path,
        displayPath,
        created: oldText === null,
        unified,
        added: lines.filter(l => l.startsWith('+') && !l.startsWith('+++'))
          .length,
        removed: lines.filter(l => l.startsWith('-') && !l.startsWith('---'))
          .length
      });
    } else if (part.type === 'content') {
      const block = record(part.content);
      if (block.type === 'text' && text(block.text)) {
        texts.push(text(block.text));
      }
    } else if (part.type === 'terminal') {
      terminals.push(text(part.terminalId));
    }
  }
  return { diffs, texts, terminals };
}

/**
 * The state after one `session/update`.
 *
 * @param state - The state.
 * @param update - The update's `update`.
 *
 * @returns The next state.
 */
export function withUpdate(state: AcpState, update: unknown): AcpState {
  const said = record(update);
  const kind = text(said.sessionUpdate);
  const rows = [...state.rows];
  const last = rows[rows.length - 1];
  switch (kind) {
    case 'agent_message_chunk':
    case 'agent_thought_chunk':
    case 'user_message_chunk': {
      const block = record(said.content);
      const chunk = block.type === 'text' ? text(block.text) : '';
      if (!chunk) {
        return state;
      }
      const rowKind =
        kind === 'agent_message_chunk'
          ? 'agent'
          : kind === 'agent_thought_chunk'
            ? 'thought'
            : 'user';
      // Chunks of the same speaker, one after the other, are one row.
      if (last && last.kind === rowKind) {
        rows[rows.length - 1] = { ...last, text: last.text + chunk };
      } else {
        rows.push({ kind: rowKind, id: `r${rows.length}`, text: chunk });
      }
      return { ...state, rows };
    }
    case 'tool_call':
    case 'tool_call_update': {
      const toolCallId = text(said.toolCallId);
      const index = rows.findIndex(
        row => row.kind === 'tool' && row.toolCallId === toolCallId
      );
      const content = contentOf(said.content, state.workspace);
      if (index < 0) {
        rows.push({
          kind: 'tool',
          id: `r${rows.length}`,
          toolCallId,
          title: text(said.title) || toolCallId,
          toolKind: text(said.kind) || 'other',
          status: text(said.status) || 'pending',
          ...content
        });
        return { ...state, rows };
      }
      const known = rows[index] as Extract<AcpRow, { kind: 'tool' }>;
      // An update replaces the content it carries, and keeps what it does not say.
      rows[index] = {
        ...known,
        title: text(said.title) || known.title,
        toolKind: text(said.kind) || known.toolKind,
        status: text(said.status) || known.status,
        ...(Array.isArray(said.content) ? content : {})
      };
      return { ...state, rows };
    }
    case 'plan': {
      const entries = (Array.isArray(said.entries) ? said.entries : []).map(
        entry => {
          const item = record(entry);
          return {
            content: text(item.content),
            status: text(item.status),
            priority: text(item.priority)
          };
        }
      );
      const index = rows.findIndex(row => row.kind === 'plan');
      if (index >= 0) {
        rows[index] = {
          ...(rows[index] as Extract<AcpRow, { kind: 'plan' }>),
          entries
        };
      } else {
        rows.push({ kind: 'plan', id: `r${rows.length}`, entries });
      }
      return { ...state, rows };
    }
    default:
      // available_commands_update, current_mode_update and the rest: nothing drawn.
      return state;
  }
}

/** A frame the panel sends. */
export type AcpFrame = Record<string, unknown>;

/**
 * The panel's side of one ACP connection: frames in, frames out, the state
 * drawn. The socket is the view's: `send` writes a frame to it and
 * {@link AcpConversation.receive} is handed each frame read.
 */
export class AcpConversation {
  private counter = 0;
  private readonly pending = new Map<number, string>();
  state: AcpState = initialAcpState();

  /**
   * @param send - Writes one JSON-RPC frame on the socket.
   * @param token - The person's Datalayer token, said in `authenticate`.
   * @param cwd - The notebook's folder, sent as `session/new`'s cwd (the
   *   runtime answers with its own workspace).
   * @param onChange - Told each new state.
   */
  constructor(
    private readonly send: (frame: AcpFrame) => void,
    private readonly token: string,
    private readonly cwd: string,
    private readonly onChange: (state: AcpState) => void = () => undefined
  ) {}

  private set(next: AcpState): void {
    this.state = next;
    this.onChange(next);
  }

  private say(tone: 'info' | 'error', said: string): void {
    this.set({
      ...this.state,
      rows: [
        ...this.state.rows,
        { kind: 'said', id: `r${this.state.rows.length}`, tone, text: said }
      ]
    });
  }

  private request(method: string, params: Record<string, unknown>): number {
    this.counter += 1;
    this.pending.set(this.counter, method);
    this.send({ jsonrpc: '2.0', id: this.counter, method, params });
    return this.counter;
  }

  /** The socket opened: `initialize` sent. */
  open(): void {
    if (!this.token) {
      this.say('error', ACP_WORDS.noToken);
      this.set({ ...this.state, phase: 'closed' });
      return;
    }
    this.set({ ...this.state, phase: 'initializing' });
    this.request('initialize', {
      protocolVersion: ACP_PROTOCOL_VERSION,
      // The panel lends no filesystem and no terminal: the harness's are the
      // runtime's (SHIELD decision 6).
      clientCapabilities: {
        fs: { readTextFile: false, writeTextFile: false },
        terminal: false
      },
      clientInfo: { name: 'jupyter-ai-agents', version: '1' }
    });
  }

  /**
   * A prompt sent, said as the person's row.
   *
   * @param prompt - What the person wrote.
   *
   * @returns Whether it was sent (a session open and no turn running).
   */
  prompt(prompt: string): boolean {
    const said = prompt.trim();
    if (!said || this.state.phase !== 'ready' || !this.state.sessionId) {
      return false;
    }
    this.set({
      ...this.state,
      phase: 'working',
      stopReason: undefined,
      rows: [
        ...this.state.rows,
        { kind: 'user', id: `r${this.state.rows.length}`, text: said }
      ]
    });
    this.request('session/prompt', {
      sessionId: this.state.sessionId,
      prompt: [{ type: 'text', text: said }]
    });
    return true;
  }

  /** The running turn cancelled (`session/cancel`, a notification). */
  cancel(): void {
    if (this.state.phase === 'working' && this.state.sessionId) {
      this.send({
        jsonrpc: '2.0',
        method: 'session/cancel',
        params: { sessionId: this.state.sessionId }
      });
    }
  }

  /**
   * A permission answered with the option the person chose.
   *
   * @param requestId - The route's request id.
   * @param optionId - The option chosen; `null` answers *cancelled*.
   */
  decide(requestId: string | number, optionId: string | null): void {
    const index = this.state.rows.findIndex(
      row =>
        row.kind === 'permission' &&
        row.requestId === requestId &&
        row.answer === undefined
    );
    if (index < 0) {
      return;
    }
    const row = this.state.rows[index] as Extract<
      AcpRow,
      { kind: 'permission' }
    >;
    if (optionId !== null && !row.options.some(o => o.optionId === optionId)) {
      return;
    }
    this.send({
      jsonrpc: '2.0',
      id: requestId,
      result: {
        outcome:
          optionId === null
            ? { outcome: 'cancelled' }
            : { outcome: 'selected', optionId }
      }
    });
    const rows = [...this.state.rows];
    rows[index] = { ...row, answer: optionId };
    this.set({ ...this.state, rows });
  }

  /** The socket closed: open permissions are no longer answerable. */
  closed(): void {
    if (this.state.phase !== 'closed') {
      this.say('info', ACP_WORDS.closed);
      this.set({ ...this.state, phase: 'closed' });
    }
  }

  /**
   * One frame read from the socket.
   *
   * @param raw - The frame's text.
   */
  receive(raw: string): void {
    let message: Record<string, unknown>;
    try {
      message = record(JSON.parse(raw));
    } catch {
      this.say('error', 'The runtime sent a frame that is not JSON.');
      return;
    }
    const method = text(message.method);
    if (method === 'session/update') {
      this.set(withUpdate(this.state, record(message.params).update));
      return;
    }
    if (method === 'session/request_permission') {
      const params = record(message.params);
      const call = record(params.toolCall);
      const options = (Array.isArray(params.options) ? params.options : []).map(
        option => {
          const item = record(option);
          return {
            optionId: text(item.optionId),
            name: text(item.name),
            kind: text(item.kind)
          };
        }
      );
      const requestId = message.id as string | number;
      this.set({
        ...this.state,
        rows: [
          ...this.state.rows,
          {
            kind: 'permission',
            id: `r${this.state.rows.length}`,
            requestId,
            title: text(call.title) || text(call.toolCallId),
            toolKind: text(call.kind) || 'other',
            command: text(record(call.rawInput).command),
            sentence: contentOf(call.content).texts.join('\n'),
            options
          }
        ]
      });
      return;
    }
    if (method) {
      // A request the panel does not serve (fs/*, terminal/*: the runtime's).
      if (message.id !== undefined) {
        this.send({
          jsonrpc: '2.0',
          id: message.id,
          error: {
            code: -32601,
            message: `The panel does not serve ${method}.`
          }
        });
      }
      return;
    }
    // An answer to one of the panel's own requests.
    const id = Number(message.id);
    const asked = this.pending.get(id);
    if (asked === undefined) {
      const error = record(message.error);
      if (text(error.message)) {
        this.say('error', text(error.message));
      }
      return;
    }
    this.pending.delete(id);
    const error = record(message.error);
    if (message.error) {
      this.say('error', text(error.message) || `${asked} failed.`);
      this.set({
        ...this.state,
        phase: asked === 'session/prompt' ? 'ready' : 'closed'
      });
      return;
    }
    const result = record(message.result);
    if (asked === 'initialize') {
      const agent = record(record(result.agentCapabilities).agent);
      const agentName = text(agent.name) || undefined;
      const methods = Array.isArray(result.authMethods)
        ? result.authMethods
        : [];
      if (methods.some(m => record(m).id === ACP_AUTH_METHOD)) {
        this.set({ ...this.state, agentName, phase: 'authenticating' });
        this.request('authenticate', {
          methodId: ACP_AUTH_METHOD,
          _meta: { token: this.token }
        });
      } else {
        this.say(
          'error',
          `The runtime does not take a token in a message (no ${ACP_AUTH_METHOD} method): it needs a newer agent-runtimes.`
        );
        this.set({ ...this.state, agentName, phase: 'closed' });
      }
    } else if (asked === 'authenticate') {
      this.set({ ...this.state, phase: 'opening' });
      this.request('session/new', { cwd: this.cwd, mcpServers: [] });
    } else if (asked === 'session/new') {
      const workspace =
        text(record(record(result._meta).datalayer).workspace) || undefined;
      this.set({
        ...this.state,
        phase: 'ready',
        sessionId: text(result.sessionId),
        workspace
      });
    } else if (asked === 'session/prompt') {
      const stopReason = text(result.stopReason) || 'end_turn';
      // A question the turn ended without answering is no longer answerable.
      const rows = this.state.rows.map(row =>
        row.kind === 'permission' && row.answer === undefined
          ? { ...row, answer: null }
          : row
      );
      this.set({ ...this.state, rows, phase: 'ready', stopReason });
      const sentence = ACP_WORDS.stopped(stopReason);
      if (sentence) {
        this.say(stopReason === 'refusal' ? 'error' : 'info', sentence);
      }
    }
  }
}
