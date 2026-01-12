/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import { ReactWidget } from '@jupyterlab/ui-components';
import { LabIcon } from '@jupyterlab/ui-components';
import { Chat } from './Chat';

import sparklesSvgstr from '../style/icons/sparkles.svg';

const sparklesIcon = new LabIcon({
  name: 'ai-chat:sparkles',
  svgstr: sparklesSvgstr
});

/**
 * Chat widget with React Query provider
 */
export class ChatWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.icon = sparklesIcon;
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <Chat/>
  }
}

export default ChatWidget;
