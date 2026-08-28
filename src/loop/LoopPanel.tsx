/*
 * Copyright (c) 2023-2026 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The LOOP workspace in a JupyterLab side panel.
 *
 * The third front-end, and the one that tests whether the extension points are
 * interfaces or wishful thinking: the same shell, the same plugins, a different
 * host — with only two things replaced, both of them implementations of
 * contracts the workspace already had.
 *
 * JupyterLab owns the providers here, as every host does (§3.5), so this file
 * mounts a theme and hands the workspace a reactor. It asks for the `panel`
 * layout because a side panel is a column, not a page.
 *
 * @module loop/LoopPanel
 */

import { useEffect, useMemo } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import type { JupyterFrontEnd } from '@jupyterlab/application';
import type { INotebookTracker } from '@jupyterlab/notebook';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { JupyterReactTheme } from '@datalayer/jupyter-react';
import { useReactor } from '@datalayer/reactor/react';
import {
  A2uiExtension,
  AgentsExtension,
  ChatExtension,
  CODE_SANDBOX_EXTENSION_NAME,
  LoopWorkspace,
  ModelsExtension,
  buildLoopReactor,
  type CodeSandboxOutput,
} from '@datalayer/agent-runtimes';
import { jupyterLabExtensions } from './plugin';

const queryClient = new QueryClient();

function LoopPanelContent({
  app,
  notebookTracker,
  serverUrl,
}: {
  app: JupyterFrontEnd;
  notebookTracker: INotebookTracker;
  serverUrl: string;
}): JSX.Element {
  const reactor = useMemo(
    () =>
      buildLoopReactor([
        ChatExtension,
        AgentsExtension,
        ModelsExtension,
        A2uiExtension,
        ...jupyterLabExtensions(app, notebookTracker, serverUrl),
      ]),
    [app, notebookTracker, serverUrl],
  );
  useReactor(reactor);

  useEffect(() => {
    const sandbox = reactor.getOutput<CodeSandboxOutput>(
      CODE_SANDBOX_EXTENSION_NAME,
    )?.sandbox;
    // JupyterLab's services are already running, so this connects immediately
    // rather than booting anything.
    return sandbox?.connect();
  }, [reactor]);

  return (
    <QueryClientProvider client={queryClient}>
      <LoopWorkspace
        serverUrl={serverUrl}
        agentId="default"
        reactor={reactor}
        manageReactor={false}
        layout="panel"
        placeholder="Ask about this notebook, or type / for commands"
      />
    </QueryClientProvider>
  );
}

/** The side-panel widget. */
export class LoopWidget extends ReactWidget {
  constructor(
    private readonly app: JupyterFrontEnd,
    private readonly notebookTracker: INotebookTracker,
    private readonly serverUrl: string,
  ) {
    super();
    this.addClass('jp-loop-container');
    this.id = 'jupyter-loop';
    this.title.caption = 'Loop';
    this.title.closable = true;
  }

  render(): JSX.Element {
    return (
      <JupyterReactTheme>
        <LoopPanelContent
          app={this.app}
          notebookTracker={this.notebookTracker}
          serverUrl={this.serverUrl}
        />
      </JupyterReactTheme>
    );
  }
}

export default LoopWidget;
