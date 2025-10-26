/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

/*
 * Copyright (c) 2023-2024 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import { type ReactNode } from 'react';
import { CodeIcon, GlobeIcon, ImagePlusIcon, WrenchIcon } from 'lucide-react';

export function getToolIcon(toolId: string, className = 'size-4') {
  const iconMap: Record<string, ReactNode> = {
    web_search: <GlobeIcon className={className} />,
    code_execution: <CodeIcon className={className} />,
    image_generation: <ImagePlusIcon className={className} />,
  }
  return iconMap[toolId] ?? <WrenchIcon className={className} />
}
