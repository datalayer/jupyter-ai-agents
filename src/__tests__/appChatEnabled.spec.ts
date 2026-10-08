/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * The plugin's `agentChatEnabled` setting (STUDIO A-19): off by default in
 * the schema, and on only when it is exactly `true`.
 */

import { readFileSync } from 'fs';
import { join } from 'path';

import { APP_CHAT_SETTING, appChatEnabledOf } from '../appChat';

describe('agentChatEnabled', () => {
  it('is in the schema, a boolean off by default', () => {
    const schema = JSON.parse(
      readFileSync(join(__dirname, '..', '..', 'schema', 'plugin.json'), 'utf8')
    ) as {
      properties: Record<string, { type: string; default: unknown }>;
      additionalProperties: boolean;
    };
    expect(schema.properties[APP_CHAT_SETTING]).toEqual(
      expect.objectContaining({ type: 'boolean', default: false })
    );
  });

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
