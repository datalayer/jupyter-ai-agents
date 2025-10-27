/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

declare module '*.css' {
  const content: string;
  export default content;
}

declare module '!!css-loader?importLoaders=1&exportType=string!postcss-loader!*' {
  const content: string;
  export default content;
}
