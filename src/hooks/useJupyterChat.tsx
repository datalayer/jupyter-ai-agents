import { useChat } from '@ai-sdk/react';
import { useCallback, useMemo } from 'react';

export interface IUseJupyterChatOptions {
  apiUrl?: string;
  initialMessages?: any[];
}

/**
 * Hook to manage chat state with JupyterLab backend.
 * Adapts Vercel AI SDK's useChat for Jupyter context.
 */
export function useJupyterChat(_options: IUseJupyterChatOptions = {}) {
  const { messages, sendMessage, status, setMessages, regenerate } = useChat();

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
