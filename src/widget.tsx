/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import AiAgentIconJupyterLab from '@datalayer/icons-react/data1/AiAgentIconJupyterLab';
import { Chat } from './Chat';

const WidgetContent: React.FC = () => {
  return (
    <>
      <Chat />
    </>
  );
};

/**
 * Chat widget with React Query provider
 */
export class ChatWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.icon = AiAgentIconJupyterLab;
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <WidgetContent />;
  }
}

export default ChatWidget;
