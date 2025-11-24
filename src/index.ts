/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ILabShell } from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { setupPrimerPortals } from '@datalayer/primer-addons';
import { ChatWidget } from './widget';
// import { requestAPI } from './handler';

import '../style/index.css';

setupPrimerPortals();

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
    const chatWidget = new ChatWidget();
    labShell.add(chatWidget, 'right', { rank: 1000 });

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
    /*
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
    */
  }
};

export default plugin;
