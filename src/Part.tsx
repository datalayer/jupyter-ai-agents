import { Message, MessageContent } from '@/components/ai-elements/message'

import { Actions, Action } from '@/components/ai-elements/actions'
import { Response } from '@/components/ai-elements/response'
import { CopyIcon, RefreshCcwIcon } from 'lucide-react'
import type { UIDataTypes, UIMessagePart, UITools, UIMessage } from 'ai'
import { Reasoning, ReasoningContent, ReasoningTrigger } from '@/components/ai-elements/reasoning'
import { Tool, ToolHeader, ToolInput, ToolOutput, ToolContent } from '@/components/ai-elements/tool'
import { CodeBlock } from '@/components/ai-elements/code-block'

interface PartProps {
  part: UIMessagePart<UIDataTypes, UITools>
  message: UIMessage
  status: string
  regen: (id: string) => void
  index: number
  lastMessage: boolean
}

export function Part({ part, message, status, regen, index, lastMessage }: PartProps) {
  function copy(text: string) {
    navigator.clipboard.writeText(text).catch((error: unknown) => {
      console.error('Error copying text:', error)
    })
  }

  if (part.type === 'text') {
    return (
      <div className="py-4">
        <Message from={message.role}>
          <MessageContent>
            <Response>{part.text}</Response>
          </MessageContent>
        </Message>
        {message.role === 'assistant' && index === message.parts.length - 1 && (
          <Actions className="mt-1">
            <Action
              onClick={() => {
                regen(message.id)
              }}
              label="Retry"
            >
              <RefreshCcwIcon className="size-3" />
            </Action>
            <Action
              onClick={() => {
                copy(part.text)
              }}
              label="Copy"
            >
              <CopyIcon className="size-3" />
            </Action>
          </Actions>
        )}
      </div>
    )
  } else if (part.type === 'reasoning') {
    return (
      <Reasoning
        className="w-full"
        isStreaming={status === 'streaming' && index === message.parts.length - 1 && lastMessage}
      >
        <ReasoningTrigger />
        <ReasoningContent>{part.text}</ReasoningContent>
      </Reasoning>
    )
  } else if (part.type === 'dynamic-tool') {
    return <>Dynamic Tool, TODO {JSON.stringify(part)}</>
  } else if ('toolCallId' in part) {
    // return <div>{JSON.stringify(part)}</div>
    return (
      <Tool>
        <ToolHeader type={part.type} state={part.state} />
        <ToolContent>
          <ToolInput input={part.input} />
          {part.state === 'output-available' && (
            <ToolOutput
              errorText=""
              output={<CodeBlock code={JSON.stringify(part.output, null, 2)} language="json" />}
            />
          )}
        </ToolContent>
      </Tool>
    )
  }
}
