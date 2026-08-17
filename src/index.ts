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
import { ILauncher } from '@jupyterlab/launcher';
import { INotebookTracker } from '@jupyterlab/notebook';
import RobotIconJupyterLab from '@datalayer/icons-react/data2/RobotIconJupyterLab';
import { setupPrimerPortals } from '@datalayer/primer-addons';
import { ChatWidget } from './widget';
import { useAIAgentsStore } from './store';
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

    /*
     * Double the width the right panel opens at while the chat is the
     * visible panel.
     *
     * JupyterLab offers no official way to size a side panel. Lumino reads
     * the CSS minimum of the split panel's direct child — `#jp-right-stack`
     * — when it fits the layout, so the floor is written there, and only
     * while the chat is showing: the file browser and the other panels keep
     * their usual width. `fit()` makes the shell re-read the constraint at
     * the moment it changes.
     */
    const RIGHT_STACK_MIN_WIDTH_PX = 600;
    const syncRightPanelWidth = () => {
      const stack = document.getElementById('jp-right-stack');
      if (!stack) {
        return;
      }
      const visible = chatWidget.isVisible;
      const wanted = visible ? `${RIGHT_STACK_MIN_WIDTH_PX}px` : '';
      const split = (labShell as any)._hsplitPanel;
      if (stack.style.minWidth !== wanted) {
        stack.style.minWidth = wanted;
        /*
         * The split panel holding the stack must refit to read the new
         * minimum: a fit on the shell stops at the shell's own layout —
         * Lumino propagates fit-requests upward, not down. The panel is
         * private, so a window resize — on which JupyterLab refits every
         * layout — stands in when it is not where it used to be.
         */
        if (split?.fit) {
          split.fit();
        } else {
          window.dispatchEvent(new Event('resize'));
        }
      }
      /*
       * The floor alone is not enough on a workspace that was saved with a
       * narrower panel: the restored layout states explicit sizes, and on
       * some paths the split keeps them instead of re-reading the CSS
       * minimum. Stating the sizes wins over whatever was restored. The
       * handler re-runs on the layoutModified this triggers and finds
       * nothing left to change, so it settles rather than loops — and a
       * user dragging the panel wider than the target is left alone.
       */
      if (visible && split?.relativeSizes && split?.setRelativeSizes) {
        const total = split.node?.getBoundingClientRect().width ?? 0;
        if (total > 0) {
          const sizes: number[] = split.relativeSizes();
          const rightIndex = sizes.length - 1;
          // Never take more than 60% of the window from the main area.
          const target = Math.min(0.6, RIGHT_STACK_MIN_WIDTH_PX / total);
          if (sizes[rightIndex] < target - 0.005) {
            const remainder = 1 - target;
            const currentRemainder = 1 - sizes[rightIndex];
            const next = sizes.map((size, index) =>
              index === rightIndex
                ? target
                : currentRemainder > 0
                  ? (size * remainder) / currentRemainder
                  : remainder / Math.max(1, rightIndex)
            );
            split.setRelativeSizes(next);
          }
        }
      }
    };
    labShell.layoutModified.connect(syncRightPanelWidth);
    void app.restored.then(syncRightPanelWidth);

    /*
     * Tell the chat which Datalayer editor is in front of the user.
     *
     * Both Datalayer editors — the notebook and the `.dlex` document — are
     * document widgets whose content wears the `dla-Container` class, and
     * both register in their stores under the path of the document. The
     * default editors of JupyterLab are deliberately not published: the
     * frontend tools read the Datalayer stores, which know nothing of them.
     */
    const publishActiveEditor = (widget: unknown) => {
      /*
       * Only the main area speaks for the selection.
       *
       * `currentChanged` also fires when a sidebar takes focus — this chat
       * itself, the file browser — and clearing the selection then would
       * drop the notebook's tools at the very moment the user clicks into
       * the chat to use them. A sidebar focus keeps the previous choice; a
       * main-area widget that is not a Datalayer editor clears it.
       */
      const inMainArea = Array.from(labShell.widgets('main')).some(
        candidate => candidate === widget
      );
      if (!widget || !inMainArea) {
        return;
      }
      const path: string | undefined = (widget as any)?.context?.path;
      const isDatalayer = !!(widget as any)?.content?.hasClass?.(
        'dla-Container'
      );
      let activeEditor;
      if (path && isDatalayer) {
        if (path.endsWith('.ipynb')) {
          activeEditor = { kind: 'notebook' as const, id: path };
        } else if (path.endsWith('.dlex')) {
          activeEditor = { kind: 'document' as const, id: path };
        }
      }
      useAIAgentsStore.getState().setActiveEditor(activeEditor);
    };
    publishActiveEditor(labShell.currentWidget);
    labShell.currentChanged.connect((_, args) => {
      publishActiveEditor(args.newValue);
    });

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

/**
 * The AI Agents card of the launcher, in the Datalayer section.
 *
 * A separate plugin: the launcher is optional — a host without one, the
 * Datalayer web application among them, still gets the chat of the main
 * plugin — and a card that only reveals a sidebar has no reason to hold the
 * chat hostage to it.
 */
const launcherPlugin: JupyterFrontEndPlugin<void> = {
  id: '@datalayer/jupyter-ai-agents:launcher',
  description: 'The AI Agents card of the JupyterLab launcher.',
  autoStart: true,
  requires: [ILabShell],
  optional: [ILauncher],
  activate: (
    app: JupyterFrontEnd,
    labShell: ILabShell,
    launcher: ILauncher | null
  ) => {
    const command = '@datalayer/jupyter-ai-agents:open-chat';
    app.commands.addCommand(command, {
      label: 'AI Agents',
      caption: 'Chat with the AI Agents of Datalayer',
      icon: RobotIconJupyterLab,
      execute: () => {
        // The widget of the main plugin, brought into view.
        labShell.activateById('jupyter-ai-chat');
      }
    });
    launcher?.add({
      command,
      category: 'Datalayer',
      // After the cards of the Datalayer UI, which take the first ranks.
      rank: 10
    });
  }
};

export { useAIAgentsStore } from './store';
export type { IAIAgentsStore } from './store';

export default [plugin, launcherPlugin];
