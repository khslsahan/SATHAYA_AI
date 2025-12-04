import { DocumentTextIcon } from '@heroicons/react/24/outline'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Array<{ type: string; full_text: string }>
  timestamp: Date
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] rounded-lg p-4 ${
              message.role === 'user'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            <div className="whitespace-pre-wrap">{message.content}</div>
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-300">
                <div className="flex items-center space-x-2 text-sm font-semibold mb-2">
                  <DocumentTextIcon className="h-4 w-4" />
                  <span>Citations:</span>
                </div>
                <ul className="space-y-1 text-sm">
                  {message.citations.map((citation, idx) => (
                    <li key={idx} className="text-primary-600 hover:underline">
                      {citation.full_text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

