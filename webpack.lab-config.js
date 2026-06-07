/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/*
 * Copyright (c) 2021-2024 Datalayer, Inc.
 *
 * Datalayer License
 */

const path = require('path');

function patchLicenseWebpackPluginIterator() {
  const candidatePaths = [
    './node_modules/@jupyterlab/builder/node_modules/license-webpack-plugin/dist/WebpackInnerModuleIterator',
    'license-webpack-plugin/dist/WebpackInnerModuleIterator',
  ];

  for (const candidatePath of candidatePaths) {
    try {
      const iteratorModule = require(candidatePath);
      const IteratorClass = iteratorModule?.WebpackInnerModuleIterator;
      const prototype = IteratorClass?.prototype;

      if (!prototype || typeof prototype.getActualFilename !== 'function') {
        continue;
      }
      if (prototype.__datalayerProvideModuleGuardPatched) {
        return;
      }

      const originalGetActualFilename = prototype.getActualFilename;

      prototype.getActualFilename = function getActualFilenamePatched(filename) {
        if (typeof filename !== 'string') {
          return null;
        }

        if (filename.indexOf('provide module') === 0) {
          const parts = filename.split('=');
          if (parts.length < 2) {
            return null;
          }
          const resolved = parts.slice(1).join('=').trim();
          return resolved || null;
        }

        return originalGetActualFilename.call(this, filename);
      };

      prototype.__datalayerProvideModuleGuardPatched = true;
      return;
    } catch (error) {
      // Try the next candidate path.
    }
  }
}

patchLicenseWebpackPluginIterator();

module.exports = {
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './lib')
    },
    fallback: {
      "fs": false,
      "path": require.resolve("path-browserify"),
      "stream": require.resolve("stream-browserify"),
      "crypto": require.resolve("crypto-browserify"),
      "buffer": require.resolve("buffer"),
      "util": require.resolve("util"),
      "assert": require.resolve("assert"),
      "url": require.resolve("url"),
      "querystring": require.resolve("querystring-es3"),
      "os": require.resolve("os-browserify/browser"),
      "zlib": require.resolve("browserify-zlib"),
      "process": require.resolve("process/browser"),
    },
  },
  experiments: {
    asyncWebAssembly: true,
    syncWebAssembly: true,
  },
  module: {
    rules: [
      {
        test: /\.jsx$/,
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-react'],
          cacheDirectory: true
        }
      },
      {
        test: /\.s[ac]ss$/i,
        use: [ "style-loader", "css-loader", "sass-loader" ],
      },
      // Rule to deal with the service-worker.ts file
      // It will include the transpiled file as a text file named `[name][ext]`
      // That file is available from the static folder of this extension. That
      // requires to overwrite the `workerUrl` in '@datalayer/jupyter-kernels:browser-service-worker'
      // see https://github.com/jupyterlite/jupyterlite/blob/1a1bbcaab83f3c56fde6747a8c9b83d3c2a9eb97/packages/server/src/tokens.ts#L5
      {
        resourceQuery: /text/,
        type: 'asset/resource',
        generator: {
          filename: 'lite-[name][ext]',
        },
      },
      // Rules for pyodide kernel assets
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
      },
    ],
  },
};