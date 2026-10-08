/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The plugin's `agentChatEnabled` setting (STUDIO A-19): on only when it is
 * exactly `true` (its schema default, off, is held by
 * `jupyter_ai_agents/tests/test_schema.py`).
 */

import { appChatEnabledOf } from '../appChat';

describe('agentChatEnabled', () => {
  it('is off without settings, and when set to anything but true', () => {
    expect(appChatEnabledOf(undefined)).toBe(false);
    expect(appChatEnabledOf(null)).toBe(false);
    expect(appChatEnabledOf({})).toBe(false);
    expect(appChatEnabledOf({ agentChatEnabled: false })).toBe(false);
    expect(appChatEnabledOf({ agentChatEnabled: 'true' })).toBe(false);
    expect(appChatEnabledOf({ agentChatEnabled: 1 })).toBe(false);
  });

  it('is on when set to true', () => {
    expect(appChatEnabledOf({ agentChatEnabled: true })).toBe(true);
  });
});
