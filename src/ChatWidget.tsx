/*
 * Copyright (c) 2024-2025 Datalayer, Inc.
 *
 * BSD 3-Clause License
 */

import React, {
  useState,
  useEffect,
  useMemo,
  useRef
} from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton
} from './components/ai-elements/conversation';
import { Loader } from './components/ai-elements/loader';
import {
  PromptInput,
  PromptInputButton,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools
} from './components/ai-elements/prompt-input';
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger
} from './components/ai-elements/sources';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger
} from './components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from './components/ui/tooltip';
import { Switch } from './components/ui/switch';
import { Part } from './Part';
import { useJupyterChat } from './hooks/useJupyterChat';
import { useQuery } from '@tanstack/react-query';
import { requestAPI } from './handler';
import { Settings2Icon } from 'lucide-react';

interface IModelConfig {
  id: string;
  name: string;
  builtinTools?: string[];  // Support both naming conventions
}

interface IBuiltinTool {
  name: string;
  id: string;
}

interface IRemoteConfig {
  models: IModelConfig[];
  builtinTools: IBuiltinTool[];
}

async function getModels() {
  return await requestAPI<IRemoteConfig>('configure');
}

/**
 * Main Chat component for JupyterLab sidebar
 */
export const ChatComponent: React.FC = () => {
  const [model, setModel] = useState<string>('');
  const [enabledTools, setEnabledTools] = useState<string[]>([]);
  const { messages, sendMessage, status, regenerate } = useJupyterChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const configQuery = useQuery({
    queryFn: getModels,
    queryKey: ['models']
  });

  useEffect(() => {
    if (configQuery.data) {
      setModel(configQuery.data.models[0].id);
      
      // Enable all builtin tools by default
      const allToolIds = configQuery.data.builtinTools?.map(tool => tool.id) || [];
      setEnabledTools(allToolIds);
      console.log('[ChatWidget] Enabled all tools by default:', allToolIds);
    }
  }, [configQuery.data]);

  const handleSubmit = (message: PromptInputMessage) => {
    if (message.text?.trim()) {
      sendMessage(
        { text: message.text },
        {
          body: { model, builtinTools: enabledTools }
        }
      ).catch((error: unknown) => {
        console.error('Error sending message:', error);
      });
    }
  };

  const regen = (id: string) => {
    regenerate({ messageId: id }).catch((error: unknown) => {
      console.error('Error regenerating message:', error);
    });
  };

  const availableTools = useMemo(() => {
    if (!configQuery.data) {
      console.log('[ChatWidget] availableTools: no config data');
      return [];
    }
    const selectedModel = configQuery.data.models.find(entry => entry.id === model);

    const enabledToolIds = selectedModel?.builtinTools ?? [];
    
    // If model doesn't specify tools, show all builtin tools
    const tools = enabledToolIds.length > 0
      ? (configQuery.data.builtinTools?.filter(tool =>
          enabledToolIds.includes(tool.id)
        ) ?? [])
      : (configQuery.data.builtinTools ?? []);
    
    console.log('[ChatWidget] availableTools calculated:', {
      model,
      selectedModel,
      enabledToolIds,
      builtinTools: configQuery.data.builtinTools,
      filteredTools: tools
    });
    
    return tools;
  }, [configQuery.data, model]);

  return (
    <>
      <Conversation className="h-full">
        <ConversationContent>
          {messages.map(message => (
            <div key={message.id}>
              {message.role === 'assistant' &&
                message.parts.filter(part => part.type === 'source-url')
                  .length > 0 && (
                  <Sources>
                    <SourcesTrigger
                      count={
                        message.parts.filter(part => part.type === 'source-url')
                          .length
                      }
                    />
                    {message.parts
                      .filter(part => part.type === 'source-url')
                      .map((part, i) => (
                        <SourcesContent key={`${message.id}-${i}`}>
                          <Source
                            key={`${message.id}-${i}`}
                            href={part.url}
                            title={part.url}
                          />
                        </SourcesContent>
                      ))}
                  </Sources>
                )}
              {message.parts.map((part, index) => (
                <Part
                  key={`${message.id}-${index}`}
                  part={part}
                  message={message}
                  status={status}
                  index={index}
                  regen={regen}
                  lastMessage={message.id === messages.at(-1)?.id}
                />
              ))}
            </div>
          ))}
          {status === 'submitted' && <Loader />}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="sticky bottom-0 p-3">
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputTextarea
            ref={textareaRef}
            placeholder="Ask me anything..."
            autoFocus={true}
          />
          <PromptInputFooter>
            <PromptInputTools>
              {availableTools.length > 0 && (
                <DropdownMenu>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <DropdownMenuTrigger asChild>
                        <PromptInputButton variant="outline">
                          <Settings2Icon size={16} />
                        </PromptInputButton>
                      </DropdownMenuTrigger>
                    </TooltipTrigger>
                    <TooltipContent side="top">Tools</TooltipContent>
                  </Tooltip>
                  <DropdownMenuContent align="start" side="top">
                    {availableTools.map(tool => (
                      <div
                        key={tool.id}
                        className="flex items-center justify-between gap-3 px-2 py-1.5 rounded-sm"
                      >
                        <span className="text-sm" title={tool.name}>
                          {tool.name.length > 20 ? tool.name.substring(0, 20) + '...' : tool.name}
                        </span>
                        <Switch
                          checked={true}
                          disabled={true}
                        />
                      </div>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
              {configQuery.data && model && (
                <PromptInputModelSelect
                  onValueChange={value => {
                    setModel(value);
                  }}
                  value={model}
                >
                  <PromptInputModelSelectTrigger>
                    <PromptInputModelSelectValue />
                  </PromptInputModelSelectTrigger>
                  <PromptInputModelSelectContent>
                    {configQuery.data.models.map(modelItem => (
                      <PromptInputModelSelectItem
                        key={modelItem.id}
                        value={modelItem.id}
                      >
                        {modelItem.name}
                      </PromptInputModelSelectItem>
                    ))}
                  </PromptInputModelSelectContent>
                </PromptInputModelSelect>
              )}
            </PromptInputTools>
            <PromptInputSubmit status={status} />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </>
  );
};

/**
 * JupyterLab ReactWidget wrapper for the Chat component
 */
export class ChatWidget extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-ai-chat-container');
    this.id = 'jupyter-ai-chat';
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <ChatComponent />;
  }
}
