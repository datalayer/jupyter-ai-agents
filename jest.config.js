/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/**
 * Jest for the labextension's pure modules (`src/__tests__/*.spec.ts`):
 * TypeScript through Babel, in Node. A module tested here imports neither
 * JupyterLab nor React, so nothing ESM-only has to be transformed.
 */
module.exports = {
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.spec.ts'],
  testEnvironment: 'node',
  transform: {
    '^.+\\.[jt]sx?$': [
      'babel-jest',
      {
        presets: [
          ['@babel/preset-env', { targets: { node: 'current' } }],
          '@babel/preset-typescript'
        ]
      }
    ]
  }
};
