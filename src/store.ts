/*
 * Copyright (c) 2024-2026 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The shared state of the AI Agents sidebar.
 *
 * A code sandbox of the platform is equipped with an agent, so whatever
 * creates or terminates one changes what the sidebar should list. This store
 * is the doorbell: the sidebar reloads its agents whenever `refreshSeq`
 * moves, and any plugin — the Datalayer UI among them — rings it with
 * `refreshAgents()` after it created or removed a sandbox.
 *
 * Imported from `@datalayer/jupyter-ai-agents/lib/store` (or the package
 * root), and deliberately free of side effects: consumers ringing the bell
 * must not pull the widget, its styles, or the plugins into their bundle.
 *
 * @module store
 */

import { create } from 'zustand';

export interface IAIAgentsStore {
  /**
   * How many times a refresh was asked for. The sidebar watches this and
   * reloads its agents on every change; the number itself means nothing.
   */
  refreshSeq: number;
  /** Ask the AI Agents sidebar to reload its agents. */
  refreshAgents: () => void;
}

export const useAIAgentsStore = create<IAIAgentsStore>(set => ({
  refreshSeq: 0,
  refreshAgents: () => set(state => ({ refreshSeq: state.refreshSeq + 1 }))
}));

export default useAIAgentsStore;
