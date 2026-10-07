/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import type { JSX } from 'react';
import React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import type { INotebookTracker } from '@jupyterlab/notebook';
import AiAgentIconJupyterLab from '@datalayer/icons-react/data1/AiAgentIconJupyterLab';
import { Chat } from './Chat';

const WidgetContent: React.FC<{ notebookTracker?: INotebookTracker }> = ({
  notebookTracker
}) => {
  return (
    <>
      <Chat notebookTracker={notebookTracker} />
    </>
  );
};

/**
 * Chat widget with React Query provider
 */
export class ChatWidget extends ReactWidget {
  /**
   * @param notebookTracker - JupyterLab's notebooks: an application's agent
   *   may read the open one's selected cell when it allows it (STUDIO A-19).
   */
  constructor(private readonly notebookTracker?: INotebookTracker) {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.icon = AiAgentIconJupyterLab;
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <WidgetContent notebookTracker={this.notebookTracker} />;
  }
}

export default ChatWidget;
