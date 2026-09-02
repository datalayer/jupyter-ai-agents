/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/*
 * Copyright (c) 2023-2026 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The LOOP plugins that only make sense inside JupyterLab.
 *
 * Two of them, and both are second implementations of interfaces the workspace
 * already had:
 *
 * - the **sandbox** is JupyterLab's own `ServiceManager`, so the agent runs in
 *   the kernel the user is already looking at rather than a second one beside
 *   it;
 * - the **notebook view** points at the open notebook instead of rendering an
 *   ephemeral one, because there is already a notebook on screen.
 *
 * Nothing in the workspace changed to allow either.
 *
 * @module loop/plugin
 */

import type { JupyterFrontEnd } from '@jupyterlab/application';
import type { INotebookTracker } from '@jupyterlab/notebook';
import { contribution, definePlugin, configurePlugin } from '@datalayer/reactor';
import {
  ChatPlugin,
  AgentsPlugin,
  LoopCommand,
  LoopViewType,
  suppliedSource,
} from '@datalayer/agent-runtimes';
import { setNotebookTracker } from './LiveNotebookView';

export const LIVE_NOTEBOOK_EXTENSION_NAME =
  '@datalayer/jupyter-ai-agents:loop-notebook';

/** The notebook the user has open, not one the workspace invented. */
export const LiveNotebookPlugin = definePlugin({
  name: LIVE_NOTEBOOK_EXTENSION_NAME,
  dependencies: [AgentsPlugin],
  contributes: [
    contribution(
      LoopViewType,
      {
        viewType: 'notebook',
        title: 'Notebook',
        order: 10,
        // No sandbox gate: in JupyterLab the notebook exists whether or not a
        // kernel is attached, and saying "needs a running sandbox" about a
        // notebook the user is looking at would be nonsense.
        load: () => import('./LiveNotebookView'),
      },
      { id: 'notebook', order: 10 },
    ),
    contribution(
      LoopCommand,
      {
        name: 'notebook',
        description: 'Point the agent at the open notebook',
        group: 'Open',
        run: async ({ workspace }) => {
          workspace.setActiveViewType('notebook');
        },
      },
      { id: 'notebook' },
    ),
  ],
});

/**
 * The plugins to mount in JupyterLab.
 *
 * The sandbox is configured with the application's services, so there is one
 * kernel: the one the user can see.
 */
export function jupyterLabPlugins(
  app: JupyterFrontEnd,
  notebookTracker: INotebookTracker,
  serverUrl: string,
) {
  setNotebookTracker(notebookTracker);

  return [
    configurePlugin(AgentsPlugin, {
      serverUrl,
      target: 'browser',
      kernelSource: suppliedSource(
        app.serviceManager as never,
        'jupyter-server',
      ),
    }),
    // The prompt belongs to the chat plugin, so the words in it are set on
    // the chat plugin — this panel sits beside a notebook, and saying so is
    // the difference between a useful placeholder and a generic one.
    configurePlugin(ChatPlugin, {
      placeholder: 'Ask about this notebook, or type / for commands',
    }),
    LiveNotebookPlugin,
  ];
}
