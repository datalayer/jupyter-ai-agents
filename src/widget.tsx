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

const WidgetContent: React.FC<{
  notebookTracker?: INotebookTracker;
  appChatEnabled: boolean;
  acpEnabled: boolean;
}> = ({ notebookTracker, appChatEnabled, acpEnabled }) => {
  return (
    <>
      <Chat
        notebookTracker={notebookTracker}
        appChatEnabled={appChatEnabled}
        acpEnabled={acpEnabled}
      />
    </>
  );
};

/**
 * Chat widget with React Query provider
 */
export class ChatWidget extends ReactWidget {
  /** Off until the setting says otherwise (STUDIO A-19). */
  private appChatEnabled = false;
  /** Off until the setting says otherwise (SHIELD SH-49). */
  private acpEnabled = false;

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

  /**
   * Turns talking to deployed applications on or off (the plugin's
   * `agentChatEnabled` setting, off by default).
   *
   * @param enabled - Whether it is on.
   */
  setAppChatEnabled(enabled: boolean): void {
    if (this.appChatEnabled !== enabled) {
      this.appChatEnabled = enabled;
      this.update();
    }
  }

  /**
   * Turns the agent over ACP on or off (the plugin's `acpAgentEnabled`
   * setting, off by default).
   *
   * @param enabled - Whether it is on.
   */
  setAcpEnabled(enabled: boolean): void {
    if (this.acpEnabled !== enabled) {
      this.acpEnabled = enabled;
      this.update();
    }
  }

  render(): JSX.Element {
    return (
      <WidgetContent
        notebookTracker={this.notebookTracker}
        appChatEnabled={this.appChatEnabled}
        acpEnabled={this.acpEnabled}
      />
    );
  }
}

export default ChatWidget;
