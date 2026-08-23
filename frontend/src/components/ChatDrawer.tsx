import React, { useEffect, useRef, useState } from 'react';
import { ChatMessage } from '../types';
import { api } from '../services/api';

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [prompt, setPrompt] = useState('');
  const [audience, setAudience] = useState<'technical' | 'business' | 'auto-detect'>('auto-detect');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const loadHistory = async () => {
    try {
      const data = await api.getChatHistory('main');
      setMessages(data.items);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isStreaming) return;

    const userMessageText = prompt.trim();
    setPrompt('');

    // Append user message immediately
    const tempUserMsg: ChatMessage = {
      id: Date.now().toString(),
      org_id: '',
      session_id: 'main',
      role: 'user',
      content: userMessageText,
      created_at: new Date().toISOString(),
    };

    const tempAssistantMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      org_id: '',
      session_id: 'main',
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg, tempAssistantMsg]);
    setIsStreaming(true);

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'main',
          message: userMessageText,
          audience: audience,
        }),
      });

      if (!response.body) throw new Error('ReadableStream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.substring(6));
              if (payload.token) {
                accumulatedText += payload.token;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                    updated[lastIdx] = { ...updated[lastIdx], content: accumulatedText };
                  }
                  return updated;
                });
              }
            } catch {
              // Partial JSON chunk parsing
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsStreaming(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/40">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse" />
            <h3 className="font-semibold text-sm text-slate-100">AI Risk Assistant & RAG Q&A</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-xs px-2.5 py-1 rounded bg-slate-800"
          >
            Close
          </button>
        </div>

        {/* Audience Mode Selector */}
        <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <span className="text-[11px] text-slate-400 font-mono">Audience Mode:</span>
          <div className="flex space-x-1 bg-slate-800 p-0.5 rounded-lg border border-slate-700">
            {(['auto-detect', 'technical', 'business'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setAudience(mode)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                  audience === mode
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode === 'auto-detect' ? 'Auto' : mode === 'technical' ? 'Tech (SRE)' : 'Business (Exec)'}
              </button>
            ))}
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400">
              Ask questions about deployment risks, architectural impacts, or incident notes...
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={m.id || idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center space-x-1.5 mb-1">
                  <span className="text-[10px] font-mono text-slate-500">
                    {m.role === 'user' ? 'You' : 'AI Assistant'}
                  </span>
                </div>
                <div
                  className={`max-w-[88%] p-3 rounded-xl text-xs leading-relaxed whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-cyan-600/30 border border-cyan-500/40 text-cyan-50 rounded-br-none'
                      : 'bg-slate-800/90 border border-slate-700 text-slate-200 rounded-bl-none shadow-md'
                  }`}
                >
                  {m.content || (isStreaming && idx === messages.length - 1 ? 'Thinking...' : '')}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer */}
        <form onSubmit={handleSend} className="p-3 border-t border-slate-800 bg-slate-950/60 flex space-x-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask AI risk assistant..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !prompt.trim()}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition-all"
          >
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
};
