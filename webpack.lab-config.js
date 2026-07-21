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

/*
 * Provide a local (bundled) fallback for Jupyter-ecosystem shared modules.
 *
 * `@jupyter/builder` forces every core JupyterLab package (its `core.package.json`
 * dependencies plus every `singletonPackages` entry) to be shared with
 * `import: false`, i.e. "the host must provide this, there is no bundled
 * fallback". When this extension is loaded into a host that does not expose a
 * matching version of one of those packages (common when the host lab and this
 * rspack-built extension disagree on versions), the module-federation runtime
 * throws:
 *
 *   Error: The getter for the shared module is not a function. This may be
 *   caused by setting "shared.import: false" without the host providing the
 *   corresponding lib. #RUNTIME-012
 *
 * Rather than enumerating every affected `@jupyterlab/*` / `@jupyter/*` package
 * in `sharedPackages` (a never-ending game of whack-a-mole), we patch rspack's
 * `ModuleFederationPlugin` to re-enable the bundled fallback (delete
 * `import: false`) for any Jupyter-ecosystem share that is actually installed in
 * this extension's `node_modules`. The package stays a `singleton`, so when the
 * host does provide a compatible version that copy still wins; the local
 * fallback is only used when the host has nothing satisfying to offer.
 */
function patchModuleFederationSharedFallback() {
  // Scopes whose packages jupyter-react (and friends) bundle and that a host
  // lab may fail to share at a compatible version. `react`/`react-dom` are bare
  // (unscoped) names and are intentionally excluded so they stay host
  // singletons per the explicit `sharedPackages` config.
  const SCOPE_PATTERN = /^@(jupyterlab|jupyter|jupyter-notebook|jupyter-widgets|lumino)\//;

  let rspack;
  try {
    rspack = require('@rspack/core');
  } catch (error) {
    return;
  }

  const ModuleFederationPlugin = rspack?.container?.ModuleFederationPlugin;
  const prototype = ModuleFederationPlugin?.prototype;
  if (!prototype || typeof prototype.apply !== 'function') {
    return;
  }
  if (prototype.__datalayerSharedFallbackPatched) {
    return;
  }

  const originalApply = prototype.apply;

  prototype.apply = function applyWithSharedFallback(compiler) {
    const shared = this?._options?.shared;
    if (shared && typeof shared === 'object' && !Array.isArray(shared)) {
      for (const key of Object.keys(shared)) {
        const config = shared[key];
        if (!config || typeof config !== 'object') {
          continue;
        }
        // Only touch host-only shares within the Jupyter ecosystem.
        if (config.import !== false || !SCOPE_PATTERN.test(key)) {
          continue;
        }
        // Only enable a fallback for packages we can actually resolve locally,
        // so we never try to bundle something that is not installed.
        try {
          require.resolve(key, { paths: [__dirname] });
        } catch (error) {
          continue;
        }
        // Deleting `import` lets module federation bundle the local copy as a
        // fallback while keeping the package a shared singleton.
        delete config.import;
      }
    }
    return originalApply.call(this, compiler);
  };

  prototype.__datalayerSharedFallbackPatched = true;
}

patchModuleFederationSharedFallback();

module.exports = {
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './lib')
    },
    fallback: {
      "fs": false,
      "module": false,
      // Optional Next.js modules referenced by @datalayer/core's navigation
      // adapter behind a runtime `window.__NEXT_DATA__` guard. They are never
      // present in a JupyterLab (non-Next.js) bundle, so resolve them to empty
      // instead of failing the build when `next` is not installed.
      "next/navigation": false,
      "next/router": false,
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
  // Workaround for an rspack panic during the production build:
  // "RealContentHashPlugin: circular hash dependency". Disabling the real
  // content hash pass avoids the circular hash computation while still
  // producing content-hashed asset filenames.
  optimization: {
    realContentHash: false,
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
      {
        test: /\.wasm$/,
        type: 'webassembly/async',
      },
    ],
  },
};