import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export default function QuestionCard({
  text,
  timestamp,
  isLatest = true,
  showAvatar = true,
}) {
  return (
    <div
      className={`flex gap-3 md:gap-4 max-w-3xl w-full ${
        isLatest ? 'animate-msg-left' : ''
      }`}
    >
      {/* Avatar — only on first message in a consecutive interviewer block */}
      {showAvatar ? (
        <div
          className="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md mt-1"
          style={{
            background: 'var(--color-accent-bg)',
            border: '1px solid var(--color-accent-border)',
          }}
        >
          <Bot className="w-5 h-5" style={{ color: 'var(--color-accent-text)' }} />
        </div>
      ) : (
        <div className="w-9 md:w-10 flex-shrink-0" />
      )}

      {/* Bubble Container */}
      <div className="flex-1 space-y-1.5 min-w-0">
        {/* Label row — only with avatar */}
        {showAvatar && (
          <div className="flex items-center gap-2 text-xs font-semibold pl-0.5" style={{ color: 'var(--color-text-secondary)' }}>
            <span
              className="font-bold flex items-center gap-1 font-display"
              style={{ color: 'var(--color-accent-text)' }}
            >
              <Sparkles className="w-3 h-3" />
              AI Interviewer
            </span>
            {isLatest && timestamp && (
              <span style={{ color: 'var(--color-text-tertiary)' }}>&bull; {timestamp}</span>
            )}
          </div>
        )}

        {/* Message bubble */}
        <div
          className="rounded-2xl rounded-tl-sm p-4 md:p-5 font-normal leading-relaxed text-sm md:text-base backdrop-blur-sm"
          style={{
            background: 'var(--color-interviewer-bg)',
            color: 'var(--color-text)',
            borderLeft: '3px solid var(--color-interviewer-border-left)',
            borderTop: '1px solid var(--color-interviewer-border)',
            borderRight: '1px solid var(--color-interviewer-border)',
            borderBottom: '1px solid var(--color-interviewer-border)',
            boxShadow: '0 4px 24px -4px rgba(0,0,0,0.1)',
          }}
        >
          {text}
        </div>
      </div>
    </div>
  );
}
