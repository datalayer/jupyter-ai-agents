/*
 * Copyright (c) 2021-2024 Datalayer, Inc.
 *
 * Datalayer License
 */

import { Jupyter, JupyterLabApp } from '@datalayer/jupyter-react';
import { setupPrimerPortals } from '@datalayer/primer-addons';

import * as lightThemePlugins from '@jupyterlab/theme-light-extension';
import * as darkThemePlugins from '@jupyterlab/theme-dark-extension';
import * as iPyWidgetsPlugins from '@jupyter-widgets/jupyterlab-manager';

import * as collaborationDocProviderPlugins from '@jupyter/docprovider-extension';
import * as collaborationPlugins from '@jupyter/collaboration-extension';

import * as jupyterAIAgentsPlugins from '../index';

import '@datalayer/agent-runtimes/style/index.css';

setupPrimerPortals();

const JupyterAIAgentsApp = () => {
  return (
    <JupyterLabApp
//      serverless
      plugins={[
        lightThemePlugins,
        darkThemePlugins,
        iPyWidgetsPlugins,
        jupyterAIAgentsPlugins,
        collaborationDocProviderPlugins,
        collaborationPlugins,
      ]}
      disabledPlugins={[
        '@jupyterlab/apputils-extension:announcements',
      ]}
      position="absolute"
      height="100vh"
    />
  );
}

export const ExampleJupyterLab = () => (
  <Jupyter startDefaultKernel collaborative>
    <JupyterAIAgentsApp />
  </Jupyter>
);

export default ExampleJupyterLab;
