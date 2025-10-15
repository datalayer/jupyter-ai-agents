/*
 * Copyright (c) 2023-2025 Datalayer, Inc.
 * Distributed under the terms of the Modified BSD License.
 */

const path = require('path');

module.exports = {
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './lib')
    }
  },
  module: {
    rules: [
      {
        test: /(?<!\.raw)\.css$/,
        use: [
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  require('@tailwindcss/postcss'),
                  require('autoprefixer'),
                ],
              },
            },
          },
        ],
      },
    ],
  },
};



