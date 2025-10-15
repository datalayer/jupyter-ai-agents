import React, { useState, useEffect, type FormEvent } from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton
} from './components/ai-elements/conversation';
import { Loader } from './components/ai-elements/loader';
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea
} from './components/ai-elements/prompt-input';
import { Part } from './Part';
import { useJupyterChat } from './hooks/useJupyterChat';
import { useQuery } from '@tanstack/react-query';

interface IModelConfig {
  id: string;
  name: string;
  builtin_tools: string[];
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
  const res = await fetch('/api/configure');
  return (await res.json()) as IRemoteConfig;
}

/**
 * Main Chat component for JupyterLab sidebar
 */
export const ChatComponent: React.FC = () => {
  const [input, setInput] = useState('');
  const [model, setModel] = useState<string>('');
  const [enabledTools] = useState<string[]>([]);
  const { messages, sendMessage, status, regenerate } = useJupyterChat();

  const configQuery = useQuery({
    queryFn: getModels,
    queryKey: ['models']
  });

  useEffect(() => {
    if (configQuery.data) {
      setModel(configQuery.data.models[0].id);
    }
  }, [configQuery.data]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(
        { text: input },
        {
          body: { model, builtinTools: enabledTools }
        }
      ).catch((error: unknown) => {
        console.error('Error sending message:', error);
      });
      setInput('');
    }
  };

  const regen = (id: string) => {
    regenerate({ messageId: id }).catch((error: unknown) => {
      console.error('Error regenerating message:', error);
    });
  };

  return (
    <div className="jp-ai-chat-widget">
      <Conversation className="h-full">
        <ConversationContent>
          {messages.map(message => (
            <div key={message.id}>
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

      <PromptInput onSubmit={handleSubmit}>
        <PromptInputTextarea
          value={input}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
            setInput(e.target.value);
          }}
          placeholder="Ask me anything..."
        />
        <PromptInputSubmit disabled={status === 'submitted' || !input.trim()} />
      </PromptInput>
    </div>
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
    this.title.label = 'AI Chat';
    this.title.closable = true;
  }

  render(): JSX.Element {
    return <ChatComponent />;
  }
}
