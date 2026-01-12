/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const example = process.env.EXAMPLE || 'Example';
const IS_PRODUCTION = process.argv.indexOf('--mode=production') > -1;

const mode = IS_PRODUCTION ? 'production' : 'development';
// inline-source-map | eval-source-map | source-map | inline-cheap-source-map
const devtool = IS_PRODUCTION ? false : 'eval-source-map';
const minimize = IS_PRODUCTION ? true : false;

module.exports = {
  entry: path.resolve(__dirname, `./src/examples/${example}.tsx`),
  output: {
    path: path.resolve(__dirname, './dist'),
    filename: IS_PRODUCTION ? '[name].[contenthash].js' : 'bundle.js',
    publicPath: '/'
  },
  mode,
  devServer: {
    port: 8080,
    client: { overlay: false },
    historyApiFallback: true,
    hot: !IS_PRODUCTION,
    allowedHosts: 'all'
  },
  watchOptions: {
    aggregateTimeout: 300,
    poll: 2000,
    ignored: '/node_modules/'
  },
  devtool,
  optimization: {
    minimize
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, './lib'),
      path: 'path-browserify',
      stream: 'stream-browserify'
    },
    extensionAlias: {
      '.js': ['.js', '.ts', '.tsx'],
      '.jsx': ['.jsx', '.tsx']
    }
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: 'babel-loader',
        options: {
          plugins: [
            '@babel/plugin-proposal-class-properties'
          ],
          presets: [
            ['@babel/preset-react', {
              runtime: 'automatic',
              importSource: 'react'
            }],
            '@babel/preset-typescript'
          ],
          cacheDirectory: true
        },
        exclude: /node_modules/
      },
      {
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false
        }
      },
      {
        test: /\.jsx?$/,
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-react'],
          cacheDirectory: true
        }
      },
      {
        test: /\.js$/,
        enforce: 'pre',
        use: ['source-map-loader']
      },
      {
        test: /\.css$/,
        exclude: /node_modules/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      },
      {
        test: /\.css$/,
        include: /node_modules/,
        use: ['style-loader', 'css-loader']
      },
      {
        // In .css files, svg is loaded as a data URI
        test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
        issuer: /\.css$/,
        type: 'asset/inline'
      },
      {
        // SVG imports from TypeScript/JavaScript files use raw-loader for LabIcon
        test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
        issuer: /\.(ts|tsx|js)$/,
        use: {
          loader: 'raw-loader'
        }
      },
      {
        test: /\.(png|jpg|jpeg|gif|ttf|woff|woff2|eot|mp4|webp)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        use: [{ loader: 'url-loader', options: { limit: 10000 } }]
      },
      // Ship the JupyterLite service worker.
      {
        resourceQuery: /text/,
        type: 'asset/resource',
        generator: {
          filename: '[name][ext]',
        },
      },
      // Rule for pyodide kernel
      {
        test: /pypi\/.*/,
        type: 'asset/resource',
        generator: {
          filename: 'pypi/[name][ext][query]',
        },
      },
      {
        test: /pyodide-kernel-extension\/schema\/.*/,
        type: 'asset/resource',
        generator: {
          filename: 'schema/[name][ext][query]',
        },
      }
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      process: 'process/browser'
    }),
    new HtmlWebpackPlugin({
      template: 'public/index.html',
      title: 'Jupyter AI Agents'
    })
  ]
};
