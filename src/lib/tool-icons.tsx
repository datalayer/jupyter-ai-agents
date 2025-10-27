/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import { type ReactNode } from 'react';
import { CodeIcon, GlobeIcon, ImagePlusIcon, WrenchIcon } from 'lucide-react';

export function getToolIcon(toolId: string, size: number = 16) {
  const iconMap: Record<string, ReactNode> = {
    web_search: <GlobeIcon size={size} />,
    code_execution: <CodeIcon size={size} />,
    image_generation: <ImagePlusIcon size={size} />,
  }
  return iconMap[toolId] ?? <WrenchIcon size={size} />
}
