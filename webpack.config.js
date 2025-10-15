/*
 * Copyright (c) 2023-2025 Datalayer, Inc.
 * Distributed under the terms of the Modified BSD License.
 */

const path = require('path');

module.exports = {
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './lib')
    },
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json']
  }
};
