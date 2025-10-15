import { useChat } from '@ai-sdk/react';
import { useCallback, useMemo } from 'react';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';

export interface IUseJupyterChatOptions {
  apiUrl?: string;
  initialMessages?: any[];
}

/**
 * Hook to manage chat state with JupyterLab backend.
 * Adapts Vercel AI SDK's useChat for Jupyter context.
 */
export function useJupyterChat(_options: IUseJupyterChatOptions = {}) {
  // Build the full API URL for the chat endpoint
  const settings = ServerConnection.makeSettings();
  const chatEndpoint = URLExt.join(settings.baseUrl, 'jupyter-ai-agents', 'chat');
  
  const { messages, sendMessage, status, setMessages, regenerate } = useChat({
    // @ts-expect-error - api property exists but may not be in types for this version
    api: chatEndpoint,
    credentials: 'same-origin' as RequestCredentials,
    headers: {
      'X-XSRFToken': settings.token || ''
    }
  });

  // Clear chat history
  const clearChat = useCallback(() => {
    setMessages([]);
  }, [setMessages]);

  return useMemo(
    () => ({
      messages,
      sendMessage,
      status,
      setMessages,
      regenerate,
      clearChat
    }),
    [messages, sendMessage, status, setMessages, regenerate, clearChat]
  );
}
