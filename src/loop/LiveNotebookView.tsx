/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/*
 * Copyright (c) 2023-2026 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The notebook view, in JupyterLab.
 *
 * The workspace's notebook plugin renders an ephemeral notebook because in a
 * browser page there is nothing else. In JupyterLab the notebook is already
 * open in the main area, at full width, with the user's cursor in it — so this
 * view does not render one. It names the notebook the agent is pointed at and
 * offers the specialists that act on it.
 *
 * Same contribution shape, different implementation. That is the whole payoff
 * of the extension point being an interface rather than a component.
 *
 * @module loop/LiveNotebookView
 */

import type { JSX } from 'react';
import { useEffect, useState } from 'react';
import { Box, Text } from '@primer/react';
import type { INotebookTracker } from '@jupyterlab/notebook';
import type { LoopViewProps } from '@datalayer/agent-runtimes';

let tracker: INotebookTracker | null = null;

/** Told once, at activation, so the view can be a plain component. */
export function setNotebookTracker(value: INotebookTracker): void {
  tracker = value;
}

type Target = { path: string; cells: number } | null;

function readTarget(): Target {
  const panel = tracker?.currentWidget;
  if (!panel) {
    return null;
  }
  return {
    path: panel.context.path,
    cells: panel.content.widgets.length,
  };
}

export default function LiveNotebookView({
  workspace,
}: LoopViewProps): JSX.Element {
  const [target, setTarget] = useState<Target>(readTarget);

  useEffect(() => {
    if (!tracker) {
      return undefined;
    }
    const update = () => setTarget(readTarget());
    tracker.currentChanged.connect(update);
    update();
    return () => {
      tracker?.currentChanged.disconnect(update);
    };
  }, []);

  if (!target) {
    return (
      <Box sx={{ p: 3, color: 'fg.muted', fontSize: 1 }}>
        <Text>
          No notebook is open. The agent acts on whichever notebook is in front
          of you.
        </Text>
      </Box>
    );
  }

  const ask = (prompt: string) => () => {
    workspace.prompts.submit(prompt);
  };

  return (
    <Box sx={{ p: 3, display: 'grid', gap: 3 }}>
      <Box>
        <Text sx={{ fontSize: 0, color: 'fg.muted' }}>Acting on</Text>
        <Text sx={{ display: 'block', fontFamily: 'mono', fontSize: 1 }}>
          {target.path}
        </Text>
        <Text sx={{ fontSize: 0, color: 'fg.muted' }}>
          {target.cells} cells
        </Text>
      </Box>

      <Box sx={{ display: 'grid', gap: 2 }}>
        {[
          {
            label: 'Compact it',
            hint: 'Shorten without changing what it computes',
            prompt:
              '@NotebookCompactor compact this notebook without changing what it computes.',
          },
          {
            label: 'Check reproducibility',
            hint: 'Run it on a fresh sandbox and report what breaks',
            prompt:
              '@NotebookReproducer run this notebook top to bottom on a fresh sandbox and report what does not reproduce.',
          },
        ].map(action => (
          <Box
            as="button"
            key={action.label}
            onClick={ask(action.prompt)}
            sx={{
              textAlign: 'left',
              p: 2,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'border.default',
              bg: 'canvas.subtle',
              cursor: 'pointer',
            }}
          >
            <Text sx={{ display: 'block', fontSize: 1 }}>{action.label}</Text>
            <Text sx={{ display: 'block', fontSize: 0, color: 'fg.muted' }}>
              {action.hint}
            </Text>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
