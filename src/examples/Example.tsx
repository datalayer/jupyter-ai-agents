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

/// <reference types="webpack-env" />

import { createRoot } from 'react-dom/client';
import { ExampleJupyterLab } from './ExampleJupyterLab';

const div = document.createElement('div');
document.body.appendChild(div);
const root = createRoot(div);

root.render(<ExampleJupyterLab />);
