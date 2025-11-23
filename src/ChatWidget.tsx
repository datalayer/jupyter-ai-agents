/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import { ReactWidget } from "@jupyterlab/ui-components";
import { ChatComponent } from "@datalayer/core";

/**
 * JupyterLab ReactWidget wrapper for the Chat component
 */
export class ChatWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <ChatComponent />;
  }
}
