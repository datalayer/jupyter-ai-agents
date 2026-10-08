/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * Talking to a deployed application's agent from JupyterLab (STUDIO A-19).
 *
 * The person signed in to Datalayer picks one of their deployments in the
 * AI Agents panel and talks to it as its hosted page does: over the
 * runtime's session API, an AG-UI run on
 * `<runtime>/api/v1/apps/agents/<agent>/ag-ui/` whose thread is the session
 * (LOOP R-04, STUDIO R-02), on the runtime the deployment is kept on
 * (`kept.url`, `kept.agent_id`, R-33), with the person's own token. Its
 * approvals (R-05) are the Tool Approvals of ai-agents, answered in the
 * panel; its tool calls are said as the transcript's lines (A-06); the
 * notebook open beside the panel is what JupyterLab passes as the host's
 * `page` (D-10) — its path and its selected cell, the cell's source and its
 * outputs as text — and only when the application's Appspec names it under
 * `deployment.embedded.host.context` and a rule lets `host_context` run.
 * An application that takes only a user
 * its host's server signed (D-21) is opened with a user token ai-agents
 * signs for the person signed in (`fetchUserToken`), sent with each run;
 * the deployed version's Appspec decides, never another's.
 *
 * The same logic, and the same sentences with the surface's name, as the
 * VS Code extension's `src/chat/appChat.ts` (A-18): the two repositories
 * share no code, so it is copied, not imported.
 *
 * Pure: no JupyterLab, no React, no network. Imported by the panel
 * (`Chat.tsx`, which lists the deployments) and by `AppChat.tsx`.
 *
 * @module appChat
 */

/** A deployment of the person's that can be talked to now. */
export type AppChatHandle = {
  /** The deployment's uid. */
  uid: string;
  /** The application's uid (its Spacer item). */
  appUid: string;
  /** The application's name, as ai-agents keeps it. */
  name: string;
  /** The version the deployment runs. */
  version: number;
  /** `hosted`, `embedded` or `preview`. */
  target: string;
  /** Its address, for a hosted one. */
  slug: string;
  /** The runtime it is kept on (`kept.url`), without a trailing slash. */
  url: string;
  /** The agent the runtime made for it (`kept.agent_id`). */
  agentId: string;
};

/** A deployment as the picker offers it: talked to, or why not. */
export type AppChatChoice =
  | { kind: 'talk'; handle: AppChatHandle }
  | { kind: 'closed'; uid: string; name: string; why: string };

/** A notebook cell as JupyterLab hands it over (nbformat outputs). */
export type NotebookCellRead = {
  /** Its index in the notebook. */
  index: number;
  /** `code`, `markdown` or `raw`. */
  type: string;
  /** Its source. */
  source: string;
  /** Its outputs, as nbformat writes them; none for a markdown cell. */
  outputs?: Iterable<unknown>;
};

/** The notebook open beside the panel, as JupyterLab passes it for the host's `page`. */
export type NotebookContext = {
  /** The notebook's path, relative to the server's root. */
  path: string;
  /** How many cells it has. */
  cells: number;
  /** The selected cell, when one is. */
  cell?: {
    index: number;
    type: string;
    /** Its source, cut so that source and outputs hold within the limit. */
    source: string;
    /** Its outputs as text: streams, `text/plain`, errors. */
    outputs: string;
  };
  /** Whether the source or the outputs were cut. */
  truncated: boolean;
};

/** What an application's Appspec says its host passes and who its user is. */
export type AppHost = {
  /** The application's name, from its Appspec. */
  name: string;
  /** The version its Spacer item is now (`state.revision`). */
  revision: number;
  /** The names its agent reads with `host_context`. */
  context: string[];
  /** `signed` when it takes only a user its host's server signed (D-21). */
  user: 'claimed' | 'signed';
  /** The functions of the host it may call, by name. */
  functions: string[];
  /** Its rules, as `{appliesTo, behaviour}`. */
  rules: { appliesTo: string[]; behaviour: string }[];
  /** Its connections, as `{server, tools}`, for the transcript's lines. */
  connections: { server: string; tools: string[] }[];
};

/** A pending approval, as `<Chat>`'s `pendingApprovals` takes it. */
export type AppChatApproval = {
  /** The approval's id at ai-agents. */
  id: string;
  /** The tool waiting on it. */
  toolName: string;
  /** Its note, when it has one. */
  toolDescription?: string;
  /** The tool's arguments. */
  args: Record<string, unknown>;
  /** The agent waiting on it. */
  agentId: string;
  /** When it was asked. */
  requestedAt: string;
};

/** The most of a notebook's selected cell passed to an application, source and outputs together. */
export const NOTEBOOK_TEXT_LIMIT = 20_000;

/** The tool an application's agent reads what its host passes with (D-10). */
export const HOST_CONTEXT_TOOL = 'host_context';

/** The surface, as the sentences and the transcript's lines name it. */
export const SURFACE = 'JupyterLab';

/** How a value of the host is named (as agent-runtimes' `HOST_NAME`). */
const HOST_NAME = /^[a-z][a-z0-9_]{0,62}$/;

/** The format of an application's Spacer item (`loop.app.item/v1`). */
const APP_ITEM_FORMAT = 'loop.app.item/v1';

/** The four behaviours a rule may say. */
const BEHAVIOURS = ['do_it', 'if_asked', 'ask_first', 'leave_to_me'];

/** The words the panel says, in one place. */
export const APP_CHAT_WORDS = {
  pickerGroup: 'Your applications',
  closedGroup: 'Not available here',
  listFailed: 'Your applications could not be listed',
  runtimesGroup: 'Cloud Agents',
  reading: 'Reading the application...',
  transcript: 'What it did',
  noLines: 'Nothing yet.',
  passesNotebook:
    'It reads the open notebook’s selected cell when it asks for it (host_context: page).'
} as const;

/**
 * Trims the trailing slashes of a base URL.
 *
 * @param url - A base URL.
 *
 * @returns The URL without trailing slashes.
 */
const base = (url: string): string => url.replace(/\/+$/, '');

/**
 * The person's deployments at ai-agents (`GET /apps/deployments`).
 *
 * @param aiAgentsUrl - The ai-agents service's base URL.
 *
 * @returns The listing's URL.
 */
export function deploymentsUrl(aiAgentsUrl: string): string {
  return `${base(aiAgentsUrl)}/api/ai-agents/v1/apps/deployments`;
}

/**
 * The application's Spacer item, which holds its Appspec.
 *
 * @param spacerUrl - The Spacer service's base URL.
 * @param appUid - The application's uid.
 *
 * @returns Where Spacer answers the application's item.
 */
export function appItemUrl(spacerUrl: string, appUid: string): string {
  return `${base(spacerUrl)}/api/spacer/v1/lexicals/${encodeURIComponent(appUid)}`;
}

/**
 * The session API's AG-UI route of a deployment's agent: each thread a session.
 *
 * @param handle - The deployment talked to.
 *
 * @returns The endpoint `<Chat protocol="ag-ui">` posts its runs to.
 */
export function agUiEndpoint(
  handle: Pick<AppChatHandle, 'url' | 'agentId'>
): string {
  return `${base(handle.url)}/api/v1/apps/agents/${encodeURIComponent(handle.agentId)}/ag-ui/`;
}

/**
 * The pending Tool Approvals of one agent, at ai-agents.
 *
 * @param aiAgentsUrl - The ai-agents service's base URL.
 * @param agentId - The deployment's agent.
 *
 * @returns The listing's URL.
 */
export function pendingApprovalsUrl(
  aiAgentsUrl: string,
  agentId: string
): string {
  return `${base(aiAgentsUrl)}/api/ai-agents/v1/tool-approvals?agent_id=${encodeURIComponent(agentId)}&status=pending`;
}

/**
 * Where an approval is decided: the one way the Tool Approvals page, a
 * Slack thread and VS Code decide it (`decide_tool_approval`).
 *
 * @param aiAgentsUrl - The ai-agents service's base URL.
 * @param approvalId - The approval decided, by its id at ai-agents.
 * @param approved - Approve, or decline.
 *
 * @returns The route's URL.
 */
export function decideApprovalUrl(
  aiAgentsUrl: string,
  approvalId: string,
  approved: boolean
): string {
  return `${base(aiAgentsUrl)}/api/ai-agents/v1/tool-approvals/${encodeURIComponent(approvalId)}/${approved ? 'approve' : 'reject'}`;
}

/**
 * Reads a record field as a string.
 *
 * @param value - Anything.
 *
 * @returns The string, or `""`.
 */
const text = (value: unknown): string =>
  typeof value === 'string' ? value : '';

/**
 * Reads a value as a record.
 *
 * @param value - Anything.
 *
 * @returns The record, or an empty one.
 */
const record = (value: unknown): Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};

/**
 * The setting of `@datalayer/jupyter-ai-agents:plugin` that turns talking to
 * a deployed application's agent on (`schema/plugin.json`, off by default
 * until it has had one pass against a deployment kept always on).
 */
export const APP_CHAT_SETTING = 'agentChatEnabled';

/**
 * Whether talking to a deployed application's agent is on. Off, the panel
 * lists no deployment, asks ai-agents nothing and never mounts `AppChat`;
 * its runtimes are as before.
 *
 * @param composite - The plugin's settings (`settings.composite`), or
 *   nothing when the setting registry is not there.
 *
 * @returns True only when the setting is exactly `true`.
 */
export function appChatEnabledOf(composite: unknown): boolean {
  return record(composite)[APP_CHAT_SETTING] === true;
}

/**
 * Reads a value as a list of strings.
 *
 * @param value - Anything.
 *
 * @returns Its strings.
 */
const texts = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : [];

/**
 * A deployment as ai-agents answers it, offered in the picker: one live
 * (`state` exactly `live`), saying the version it runs, kept always on, on
 * a running runtime is talked to; any other says why not, in a sentence —
 * nothing is guessed, a version least of all (what the deployed version
 * lets its host pass is read from it).
 *
 * @param raw - One of the deployments `GET /apps/deployments` answers.
 *
 * @returns The choice, or `undefined` for what is not a deployment.
 */
export function deploymentChoiceOf(raw: unknown): AppChatChoice | undefined {
  const deployment = record(raw);
  const uid = text(deployment.uid);
  if (!uid) {
    return undefined;
  }
  const name = text(deployment.app_name) || 'This application';
  const kept = record(deployment.kept);
  const closed = (why: string): AppChatChoice => ({
    kind: 'closed',
    uid,
    name,
    why
  });
  const state = text(deployment.state);
  if (state === 'paused') {
    return closed(`${name} is paused.`);
  }
  if (state !== 'live') {
    return closed(
      `${name} is not live${state ? ` (${state})` : ''}, so it is not offered here.`
    );
  }
  const version = deployment.version;
  if (
    typeof version !== 'number' ||
    !Number.isInteger(version) ||
    version < 1
  ) {
    return closed(
      `${name} does not say which version it runs, so what it lets ${SURFACE} do is not known: it is not offered here.`
    );
  }
  if (deployment.always_on !== true) {
    return closed(
      `${name} is not kept always on, so no runtime holds its agent: turn on Always on in its Ship tab to talk to it here.`
    );
  }
  const url = text(kept.url);
  const agentId = text(kept.agent_id);
  if (kept.state !== 'running' || !url || !agentId) {
    const why = text(kept.why);
    return closed(
      `${name} is kept always on, but its runtime is not running${why ? `: ${why}` : '.'}`
    );
  }
  return {
    kind: 'talk',
    handle: {
      uid,
      appUid: text(deployment.app_uid),
      name,
      version,
      target: text(deployment.target) || 'hosted',
      slug: text(deployment.slug),
      url: base(url),
      agentId
    }
  };
}

/**
 * The picker's choices, from what ai-agents answers.
 *
 * @param body - The answer of `GET /apps/deployments`.
 *
 * @returns Every deployment, the ones talked to first.
 */
export function deploymentChoicesOf(body: unknown): AppChatChoice[] {
  const listed = record(body).deployments;
  const choices = (Array.isArray(listed) ? listed : [])
    .map(deploymentChoiceOf)
    .filter((choice): choice is AppChatChoice => choice !== undefined);
  return [
    ...choices.filter(choice => choice.kind === 'talk'),
    ...choices.filter(choice => choice.kind === 'closed')
  ];
}

/**
 * What the picker says when none of the person's applications can be talked
 * to: none deployed, or each closed for its own reason — paused, not live,
 * not kept always on, its runtime not running — said beside it.
 *
 * @param choices - The picker's choices.
 *
 * @returns The sentence, or `""` when one can be talked to.
 */
export function noneTalkableSentence(
  choices: readonly AppChatChoice[]
): string {
  if (choices.some(choice => choice.kind === 'talk')) {
    return '';
  }
  return choices.length === 0
    ? "You have no deployed applications: ship one from the Studio's Ship tab to talk to it here."
    : 'None of your applications can be talked to here now: each one says why — paused, not kept always on, or its runtime not running.';
}

/**
 * A key of the deployments talked to — each one's uid, version, runtime and
 * agent — so that a refresh answering the same ones changes nothing: the
 * view memoizes on it, and the conversation open survives.
 *
 * @param choices - The picker's choices.
 *
 * @returns One line per deployment talked to: uid, version, runtime, agent.
 */
export function talkableKeyOf(choices: readonly AppChatChoice[]): string {
  return choices
    .flatMap(choice =>
      choice.kind === 'talk'
        ? [
            [
              choice.handle.uid,
              choice.handle.version,
              choice.handle.url,
              choice.handle.agentId
            ].join(' ')
          ]
        : []
    )
    .join('\n');
}

/**
 * The deployment picked, as the newest listing has it: its runtime, agent
 * or version may have changed since it was picked; `null` when it can no
 * longer be talked to.
 *
 * @param choices - The newest listing.
 * @param pickedUid - The deployment picked.
 *
 * @returns Its newest handle, or `null`.
 */
export function pickedHandleOf(
  choices: readonly AppChatChoice[],
  pickedUid: string | null | undefined
): AppChatHandle | null {
  if (!pickedUid) {
    return null;
  }
  for (const choice of choices) {
    if (choice.kind === 'talk' && choice.handle.uid === pickedUid) {
      return choice.handle;
    }
  }
  return null;
}

/**
 * What an application's Appspec says of its host, from its Spacer item.
 *
 * @param body - The answer of `GET /api/spacer/v1/lexicals/<app uid>`.
 *
 * @returns Its host's terms.
 *
 * @throws When the item holds no Appspec that can be read.
 */
export function appHostOf(body: unknown): AppHost {
  const document = record(record(body).document);
  let stored: Record<string, unknown> = {};
  try {
    stored = record(JSON.parse(text(document.model_s) || 'null'));
  } catch {
    stored = {};
  }
  if (stored.format !== APP_ITEM_FORMAT || !record(stored.spec).schema) {
    throw new Error(
      'The application holds no Appspec that can be read: open it in the Studio and save it.'
    );
  }
  const spec = record(stored.spec);
  const host = record(record(record(spec.deployment).embedded).host);
  const revision = Number(record(stored.state).revision);
  return {
    name: text(spec.name) || text(document.name_t),
    revision: Number.isFinite(revision) ? Math.trunc(revision) : 0,
    context: texts(host.context).filter(name => HOST_NAME.test(name)),
    user: host.user === 'signed' ? 'signed' : 'claimed',
    functions: (Array.isArray(host.functions) ? host.functions : [])
      .map(fn => text(record(fn).name))
      .filter(name => HOST_NAME.test(name)),
    rules: (Array.isArray(spec.rules) ? spec.rules : []).map(rule => ({
      appliesTo:
        typeof record(rule).applies_to === 'string'
          ? [text(record(rule).applies_to)]
          : texts(record(rule).applies_to),
      behaviour: text(record(rule).behaviour)
    })),
    connections: (Array.isArray(spec.connections) ? spec.connections : [])
      .map(connection => ({
        server:
          text(record(connection).server) || text(record(connection).name),
        tools: [
          ...texts(record(connection).tools),
          ...texts(record(connection).only)
        ]
      }))
      .filter(connection => connection.server)
  };
}

/**
 * Why a deployment is not opened here, when the Appspec read is not the
 * version it runs: who its user is (D-21) and what its host may pass (D-10)
 * are the deployed version's, and nothing is decided on another's — closed,
 * rather than guessed.
 *
 * @param handle - The deployment talked to.
 * @param host - What the Appspec read says of its host.
 *
 * @returns The refusal, or `""` when the Appspec read is the version deployed.
 */
export function revisionRefusal(
  handle: Pick<AppChatHandle, 'name' | 'version'>,
  host: AppHost
): string {
  return host.revision === handle.version
    ? ''
    : `${handle.name} runs version ${handle.version}, and its Appspec read is version ${host.revision}: what the version it runs says of its host and its user is not known, so it is not opened here. Deploy the version you are at to talk to it here.`;
}

/**
 * Whether the deployed application takes only a signed user (D-21): then
 * Datalayer signs the person signed in for it (`fetchUserToken`), and the
 * token goes with each run as `forwardedProps.loop.user_token`.
 *
 * @param host - What its Appspec says of its host.
 *
 * @returns Whether a user token is fetched.
 */
export function takesSignedUser(host: Pick<AppHost, 'user'>): boolean {
  return host.user === 'signed';
}

/**
 * Why a signed application is not opened: Datalayer did not sign the
 * person for it, with ai-agents' sentence.
 *
 * @param name - The application's name.
 * @param why - What ai-agents said.
 *
 * @returns The sentence said in the chat's place.
 */
export function userTokenRefusal(name: string, why: string): string {
  return `${name} takes only a signed user (deployment.embedded.host.user: signed), and Datalayer did not sign you for it: ${why}`;
}

/**
 * Where ai-agents signs the person signed in for a deployment that takes
 * only a signed user (`POST …/deployments/{uid}/user-token`, D-21).
 *
 * @param aiAgentsUrl - The ai-agents service's base URL.
 * @param deploymentUid - The uid of the deployment talked to.
 *
 * @returns The route's URL.
 */
export function userTokenUrl(
  aiAgentsUrl: string,
  deploymentUid: string
): string {
  return `${base(aiAgentsUrl)}/api/ai-agents/v1/apps/deployments/${encodeURIComponent(deploymentUid)}/user-token`;
}

/** A user token ai-agents signed, and when it ends (seconds since the epoch). */
export type SignedUser = { token: string; exp: number };

/**
 * The user token of ai-agents' answer.
 *
 * @param body - The answer of `POST …/user-token`.
 *
 * @returns The token and when it ends.
 *
 * @throws When the answer holds none.
 */
export function signedUserOf(body: unknown): SignedUser {
  const answered = record(body);
  const token = text(answered.user_token);
  const exp = Number(answered.exp);
  if (!token || !Number.isFinite(exp)) {
    throw new Error('ai-agents answered no user token.');
  }
  return { token, exp };
}

/**
 * Whether a user token still has a minute to live: the runtime reads it as
 * a session opens, and a new conversation after it ends asks for another.
 *
 * @param signed - The token, or none.
 * @param nowSeconds - Now, in seconds since the epoch.
 *
 * @returns Whether it is sent as it is.
 */
export function signedUserFresh(
  signed: SignedUser | null | undefined,
  nowSeconds: number
): boolean {
  return Boolean(signed && signed.exp - 60 > nowSeconds);
}

/**
 * Asks ai-agents to sign the person signed in for a deployment (D-21),
 * with their own token: the same in the VS Code extension, Jupyter AI
 * Agents and Datalayer Desktop (agent-runtimes' `fetchUserToken`).
 *
 * @param aiAgentsUrl - The ai-agents service's base URL.
 * @param deploymentUid - The uid of the deployment talked to.
 * @param token - The person's Datalayer token.
 * @param fetcher - What asks; `fetch` unless given.
 *
 * @returns The user token and when it ends.
 *
 * @throws With ai-agents' sentence when it refuses.
 */
export async function fetchUserToken(
  aiAgentsUrl: string,
  deploymentUid: string,
  token: string,
  fetcher: (url: string, init: RequestInit) => Promise<Response> = fetch
): Promise<SignedUser> {
  const response = await fetcher(userTokenUrl(aiAgentsUrl, deploymentUid), {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    let detail = '';
    try {
      detail = text(record(await response.json()).detail);
    } catch {
      // The status says it.
    }
    throw new Error(
      detail || `ai-agents refused to sign you (${response.status}).`
    );
  }
  return signedUserOf(await response.json());
}

/**
 * A run's body with the user token in it, as `forwardedProps.loop.user_token`
 * — what the runtime verifies as the session opens. A body that is not a
 * JSON object goes as it was.
 *
 * @param body - The run's body, as `<Chat>` sent it.
 * @param token - What ai-agents signed for the person.
 *
 * @returns The body to send.
 */
export function withUserToken(body: string, token: string): string {
  let run: unknown;
  try {
    run = JSON.parse(body);
  } catch {
    return body;
  }
  if (run === null || typeof run !== 'object' || Array.isArray(run)) {
    return body;
  }
  const given = record((run as Record<string, unknown>).forwardedProps);
  return JSON.stringify({
    ...(run as Record<string, unknown>),
    forwardedProps: {
      ...given,
      loop: { ...record(given.loop), user_token: token }
    }
  });
}

/**
 * Whether a request is a run of the deployment's agent — a `POST` to its
 * session API's AG-UI route — which the user token goes with.
 *
 * @param url - Where the request goes.
 * @param method - Its method.
 * @param handle - The deployment talked to.
 *
 * @returns Whether the token goes in its body.
 */
export function isRunOf(
  url: string,
  method: string | undefined,
  handle: Pick<AppChatHandle, 'url' | 'agentId'>
): boolean {
  if ((method ?? 'GET').toUpperCase() !== 'POST') {
    return false;
  }
  try {
    const target = new URL(url);
    const endpoint = new URL(agUiEndpoint(handle));
    return (
      target.origin === endpoint.origin &&
      target.pathname.replace(/\/+$/, '/') === endpoint.pathname
    );
  } catch {
    return false;
  }
}

/**
 * A fetch that puts the user token in each run of the deployment's agent
 * (D-21) and leaves every other request as it was: the token asked for
 * when the run goes, so that a conversation begun after the last one ended
 * is sent a new one.
 *
 * @param fetcher - The fetch it wraps.
 * @param handle - The deployment talked to.
 * @param userToken - The user token now.
 *
 * @returns A fetch with the same signature.
 */
export function signedRunFetch(
  fetcher: typeof fetch,
  handle: Pick<AppChatHandle, 'url' | 'agentId'>,
  userToken: () => Promise<string>
): typeof fetch {
  return async (input, init) => {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    const method =
      init?.method ??
      (typeof input === 'object' && 'method' in input ? input.method : 'GET');
    const body = init?.body;
    if (!isRunOf(url, method, handle) || typeof body !== 'string') {
      return fetcher(input, init);
    }
    return fetcher(input, {
      ...init,
      body: withUserToken(body, await userToken())
    });
  };
}

/**
 * Whether the open notebook is passed, and why not (D-10): only when the
 * Appspec names `page` among what its host passes, and only when the
 * Appspec read is the version the deployment runs — another version may say
 * otherwise, and nothing is passed on a guess.
 *
 * @param handle - The deployment talked to.
 * @param host - What its Appspec says of its host.
 *
 * @returns `""` when the open notebook is passed, else the sentence why not.
 */
export function notebookContextRefusal(
  handle: Pick<AppChatHandle, 'name' | 'version'>,
  host: AppHost
): string {
  if (!host.context.includes('page')) {
    return `${handle.name} does not let its host pass the page (deployment.embedded.host.context), so your notebook is not read.`;
  }
  if (host.revision !== handle.version) {
    return `${handle.name} runs version ${handle.version}, and its Appspec read is version ${host.revision}: what the deployed version lets its host pass is not known, so your notebook is not read.`;
  }
  return '';
}

/**
 * The behaviour of the rule that applies to a tool: the rule naming it,
 * else the rule of the class `read` (what `host_context` does).
 *
 * @param host - What its Appspec says.
 * @param tool - The name of the tool called.
 *
 * @returns The behaviour, or `undefined` when no rule applies.
 */
export function behaviourOf(host: AppHost, tool: string): string | undefined {
  const named = host.rules.find(rule => rule.appliesTo.includes(tool));
  const read = host.rules.find(rule => rule.appliesTo.includes('read'));
  const behaviour = (named ?? read)?.behaviour;
  return behaviour && BEHAVIOURS.includes(behaviour) ? behaviour : undefined;
}

/**
 * Up to `room` characters of nbformat's multiline string (a string, or a
 * list of lines), joined no further than that.
 *
 * @param value - A multiline string.
 * @param room - The most characters wanted.
 *
 * @returns The text, at most `room + 1` characters (one more says it was cut).
 */
function multilineUpTo(value: unknown, room: number): string {
  if (typeof value === 'string') {
    return value.slice(0, room + 1);
  }
  let joined = '';
  for (const line of texts(value)) {
    joined += line;
    if (joined.length > room) {
      break;
    }
  }
  return joined.slice(0, room + 1);
}

/**
 * A cell's outputs as text, read one output at a time and no further than
 * `budget`: a stream's text, a result's or a display's `text/plain` (else
 * the kinds it holds, in brackets), an error's name and value — not its
 * traceback, which is the kernel's colours. Nothing is serialized beyond
 * what is passed.
 *
 * @param outputs - The outputs, as nbformat writes them, read in order.
 * @param budget - The most characters passed.
 *
 * @returns The text, and whether anything was left out.
 */
export function outputsText(
  outputs: Iterable<unknown>,
  budget: number = NOTEBOOK_TEXT_LIMIT
): { text: string; cut: boolean } {
  let said = '';
  for (const raw of outputs) {
    const room = budget - said.length - (said ? 1 : 0);
    if (room <= 0) {
      return { text: said, cut: true };
    }
    const output = record(raw);
    let piece = '';
    switch (output.output_type) {
      case 'stream':
        piece = multilineUpTo(output.text, room);
        break;
      case 'execute_result':
      case 'display_data': {
        const data = record(output.data);
        piece =
          multilineUpTo(data['text/plain'], room) ||
          `[${Object.keys(data).join(', ')}]`;
        break;
      }
      case 'error':
        piece = `${text(output.ename)}: ${text(output.evalue)}`;
        break;
      default:
        piece = '';
    }
    piece = piece.replace(/\n+$/, '');
    if (!piece) {
      continue;
    }
    if (piece.length > room) {
      return {
        text: `${said}${said ? '\n' : ''}${piece.slice(0, room)}`,
        cut: true
      };
    }
    said = `${said}${said ? '\n' : ''}${piece}`;
  }
  return { text: said, cut: false };
}

/**
 * The open notebook as an application is passed it: its path, how many
 * cells, and its selected cell — the source first, then the outputs as
 * text, cut together at `limit` characters, the outputs read only as far as
 * the room the source leaves.
 *
 * @param notebook - The notebook: its path, its cell count, its selected cell.
 * @param limit - The most characters of source and outputs passed.
 *
 * @returns The value passed as the host's `page`.
 */
export function notebookContextOf(
  notebook: { path: string; cells: number; cell?: NotebookCellRead },
  limit: number = NOTEBOOK_TEXT_LIMIT
): NotebookContext {
  const read = notebook.cell;
  if (!read) {
    return { path: notebook.path, cells: notebook.cells, truncated: false };
  }
  const source = read.source.slice(0, limit);
  const outputs = outputsText(
    read.outputs ?? [],
    Math.max(0, limit - source.length)
  );
  return {
    path: notebook.path,
    cells: notebook.cells,
    cell: { index: read.index, type: read.type, source, outputs: outputs.text },
    truncated: source.length < read.source.length || outputs.cut
  };
}

/**
 * A notebook model's outputs, one at a time, as nbformat writes each: read
 * lazily by {@link outputsText}, which stops at its budget.
 *
 * @param outputs - The cell's output area model (`length`, `get(i).toJSON()`).
 *
 * @returns The outputs, in order.
 */
export function* outputsOfModel(
  outputs:
    | { readonly length: number; get(index: number): { toJSON(): unknown } }
    | undefined
): Generator<unknown> {
  for (let index = 0; index < (outputs?.length ?? 0); index++) {
    yield outputs!.get(index).toJSON();
  }
}

/** A frontend tool, as `<Chat frontendTools>` takes it. */
export type AppChatFrontendTool = {
  /** Its name. */
  name: string;
  /** What it is, for the model. */
  description: string;
  /** Its arguments, as a JSON Schema object. */
  parameters: Record<string, unknown>;
  /** Run in the panel. */
  location: 'frontend';
  /** What answers it. */
  handler: (args: Record<string, unknown>) => Promise<unknown>;
};

/**
 * The `host_context` tool JupyterLab answers (D-10): `page` the open
 * notebook, `user` the person signed in (a claim, as a page's is), any
 * other name unsaid. Refused, in a sentence, when no rule lets it run or
 * one leaves it to the person.
 *
 * @param host - What the Appspec says of its host.
 * @param read - Reads the open notebook now; `undefined` when none is open.
 * @param user - The person signed in.
 *
 * @returns The tool, or `undefined` when the Appspec names nothing passed.
 */
export function hostContextTool(
  host: AppHost,
  read: () => Promise<NotebookContext | undefined>,
  user: { handle: string } | null
): AppChatFrontendTool | undefined {
  if (host.context.length === 0) {
    return undefined;
  }
  return {
    name: HOST_CONTEXT_TOOL,
    description: `What ${SURFACE}, where you are talked to, says of the person and of the notebook open beside you: ${host.context.join(', ')}. Read it before answering what depends on them.`,
    parameters: { type: 'object', properties: {} },
    location: 'frontend',
    handler: async () => {
      const behaviour = behaviourOf(host, HOST_CONTEXT_TOOL);
      if (!behaviour || behaviour === 'leave_to_me') {
        return {
          error: `No rule of this application lets ${HOST_CONTEXT_TOOL} run: it is left to the person, and ${SURFACE} passed nothing.`
        };
      }
      const values: Record<string, unknown> = {};
      const unsaid: string[] = [];
      for (const name of host.context) {
        if (name === 'page') {
          const page = await read();
          if (page) {
            values.page = page;
          } else {
            unsaid.push(name);
          }
        } else if (name === 'user' && user) {
          values.user = { handle: user.handle, signed: false };
        } else {
          unsaid.push(name);
        }
      }
      return { values, ...(unsaid.length > 0 ? { unsaid } : {}) };
    }
  };
}

/**
 * The transcript's line of a tool call (A-06): *Desk → Odoo: tool*, the
 * server of the connection the tool is of, *its runtime* for a tool of
 * none, *JupyterLab* for `host_context` — as ai-agents' Slack thread and
 * VS Code say it.
 *
 * @param appName - The application's name.
 * @param tool - The tool called.
 * @param host - What its Appspec says, for its connections.
 *
 * @returns The line, as the transcript says it.
 */
export function toolLineOf(
  appName: string,
  tool: string,
  host: Pick<AppHost, 'connections'> | undefined
): string {
  if (tool === HOST_CONTEXT_TOOL) {
    return `${appName} → ${SURFACE}: ${tool}`;
  }
  const connection = (host?.connections ?? []).find(
    ({ server, tools }) =>
      tools.includes(tool) || tool.startsWith(`${server.replace(/-/g, '_')}_`)
  );
  return `${appName} → ${connection?.server || 'its runtime'}: ${tool}`;
}

/**
 * The approvals one agent waits on, from ai-agents' listing.
 *
 * @param body - The answer of `GET /tool-approvals`.
 * @param agentId - The deployment's agent.
 *
 * @returns Its pending approvals, oldest first.
 */
export function pendingApprovalsOf(
  body: unknown,
  agentId: string
): AppChatApproval[] {
  const listed = record(body).approvals;
  return (Array.isArray(listed) ? listed : [])
    .map(record)
    .filter(
      approval =>
        approval.status === 'pending' &&
        text(approval.agent_id) === agentId &&
        text(approval.id)
    )
    .map(approval => ({
      id: text(approval.id),
      toolName: text(approval.tool_name),
      ...(text(approval.note) ? { toolDescription: text(approval.note) } : {}),
      args: record(approval.tool_args),
      agentId,
      requestedAt: text(approval.created_at)
    }))
    .sort((a, b) => a.requestedAt.localeCompare(b.requestedAt));
}

/**
 * The URL prefixes the panel signs with the person's token: the runtimes
 * the person's deployments are kept on, ai-agents' Tool Approvals, and
 * Spacer's items. Nothing else of an application's chat is given the token.
 *
 * @param handles - The deployments talked to.
 * @param services - The ai-agents and Spacer base URLs.
 * @param services.aiAgentsUrl - The ai-agents service's base URL.
 * @param services.spacerUrl - The Spacer service's base URL.
 *
 * @returns The prefixes, each ending with `/` (or `?` for a listing).
 */
export function signedPrefixesOf(
  handles: readonly Pick<AppChatHandle, 'url'>[],
  services: { aiAgentsUrl: string; spacerUrl: string }
): string[] {
  return [
    ...handles.map(handle => `${base(handle.url)}/`),
    `${base(services.aiAgentsUrl)}/api/ai-agents/v1/tool-approvals/`,
    `${base(services.aiAgentsUrl)}/api/ai-agents/v1/tool-approvals?`,
    `${base(services.spacerUrl)}/api/spacer/v1/lexicals/`
  ];
}

/**
 * Whether a request of the chat is signed with the person's token: an
 * HTTPS URL under one of the prefixes, its origin the prefix's own.
 *
 * @param url - Where the request goes.
 * @param prefixes - What {@link signedPrefixesOf} gave.
 *
 * @returns Whether the token goes with it.
 */
export function signsRequest(
  url: string,
  prefixes: readonly string[]
): boolean {
  let target: URL;
  try {
    target = new URL(url);
  } catch {
    return false;
  }
  if (target.protocol !== 'https:' || target.username || target.password) {
    return false;
  }
  const href = target.href;
  return prefixes.some(prefix => {
    try {
      return (
        new URL(prefix).origin === target.origin &&
        href.startsWith(new URL(prefix).href)
      );
    } catch {
      return false;
    }
  });
}

/**
 * The headers a request of the chat carries: the person's token only when
 * {@link signsRequest} says so — JupyterLab holds the token in the page, so
 * where it goes is decided here, request by request.
 *
 * @param url - Where the request goes.
 * @param token - The person's Datalayer token.
 * @param prefixes - What {@link signedPrefixesOf} gave.
 * @param headers - The request's other headers.
 *
 * @returns The headers to send.
 */
export function signedHeaders(
  url: string,
  token: string | undefined,
  prefixes: readonly string[],
  headers: Record<string, string> = {}
): Record<string, string> {
  return token && signsRequest(url, prefixes)
    ? { ...headers, Authorization: `Bearer ${token}` }
    : { ...headers };
}
