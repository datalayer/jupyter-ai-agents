/*
 * Copyright (c) 2023-2025 Datalayer, Inc.
 * Distributed under the terms of the Modified BSD License.
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ILabShell } from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { ReactWidget } from '@jupyterlab/ui-components';
import { LabIcon } from '@jupyterlab/ui-components';
import React from 'react';
import { requestAPI } from './handler';
import { ChatRoot } from './ChatRoot';

import sparklesSvgstr from '../style/icons/sparkles.svg';

// Import styles
import '../style/index.js';

const sparklesIcon = new LabIcon({
  name: 'ai-chat:sparkles',
  svgstr: sparklesSvgstr
});

/**
 * Chat widget with React Query provider
 */
class ChatWidgetWithProvider extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.icon = sparklesIcon;
    this.title.closable = true;
  }

  render(): JSX.Element {
    return React.createElement(ChatRoot);
  }
}

/**
 * Initialization data for the @datalayer/jupyter-ai-agents extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@datalayer/jupyter-ai-agents:plugin',
  description: 'Jupyter AI Agents.',
  autoStart: true,
  optional: [ISettingRegistry],
  requires: [ILabShell, INotebookTracker],
  activate: (
    app: JupyterFrontEnd,
    labShell: ILabShell,
    notebookTracker: INotebookTracker,
    settingRegistry: ISettingRegistry | null
  ) => {
    console.log(
      'JupyterLab extension @datalayer/jupyter-ai-agents is activated!'
    );

    // Create and add chat widget to left sidebar
    const chatWidget = new ChatWidgetWithProvider();
    labShell.add(chatWidget, 'left', { rank: 1000 });

    if (settingRegistry) {
      settingRegistry
        .load(plugin.id)
        .then(settings => {
          console.log(
            '@datalayer/jupyter-ai-agents settings loaded:',
            settings.composite
          );
        })
        .catch(reason => {
          console.error(
            'Failed to load settings for @datalayer/jupyter-ai-agents.',
            reason
          );
        });
    }

    // Test connection to backend by fetching configuration
    requestAPI<any>('configure')
      .then(data => {
        console.log('AI Chat backend connected:', data);
      })
      .catch(reason => {
        console.error(
          `The jupyter-ai-agents server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
