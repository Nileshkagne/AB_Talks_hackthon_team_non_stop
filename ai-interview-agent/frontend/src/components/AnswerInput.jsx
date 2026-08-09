import React from 'react';
import { Send, Loader2, CornerDownLeft } from 'lucide-react';

export default function AnswerInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  maxLength = 4000,
}) {
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (value.trim() && !disabled) {
        onSubmit();
      }
    }
  };

  const isOverLimit = value.length > maxLength;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-2 font-sans">
      <div
        className="relative rounded-2xl p-3 md:p-4 transition-all backdrop-blur-md"
        style={{
          background: 'var(--color-input-bg)',
          border: '1px solid var(--color-input-border)',
          boxShadow: '0 4px 24px -4px rgba(0,0,0,0.1)',
        }}
      >
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type your technical response here... (Ctrl+Enter to submit)"
          rows={4}
          maxLength={maxLength}
          className="w-full bg-transparent text-sm md:text-base focus:outline-none resize-none disabled:opacity-50 font-normal leading-relaxed"
          style={{ color: 'var(--color-text)' }}
          onFocus={(e) => {
            e.target.parentElement.style.borderColor = 'var(--color-accent-border)';
            e.target.parentElement.style.boxShadow = '0 4px 24px -4px rgba(0,0,0,0.1), 0 0 0 2px var(--color-accent-bg)';
          }}
          onBlur={(e) => {
            e.target.parentElement.style.borderColor = 'var(--color-input-border)';
            e.target.parentElement.style.boxShadow = '0 4px 24px -4px rgba(0,0,0,0.1)';
          }}
        />

        <div className="flex items-center justify-between pt-3" style={{ borderTop: '1px solid var(--color-border-light)' }}>
          <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
            <span className="flex items-center gap-1 hidden sm:inline-flex font-medium">
              <CornerDownLeft className="w-3.5 h-3.5" style={{ color: 'var(--color-text-secondary)' }} />
              Press <kbd className="px-1.5 py-0.5 rounded font-mono text-[10px]" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>Ctrl+Enter</kbd> to send
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`text-xs font-mono font-medium ${
                isOverLimit
                  ? 'font-bold'
                  : ''
              }`}
              style={{
                color: isOverLimit
                  ? 'var(--color-error)'
                  : value.length > maxLength * 0.9
                  ? 'var(--color-warning-text)'
                  : 'var(--color-text-tertiary)',
              }}
            >
              {value.length} / {maxLength}
            </span>

            <button
              onClick={onSubmit}
              disabled={disabled || !value.trim() || isOverLimit}
              className="px-5 py-2.5 rounded-xl active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 text-white font-bold text-sm transition-all flex items-center gap-2 cursor-pointer"
              style={{
                background: 'var(--color-accent-btn)',
                boxShadow: '0 4px 16px -4px var(--color-accent-shadow)',
              }}
            >
              {disabled ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  Evaluating...
                </>
              ) : (
                <>
                  <span>Submit Answer</span>
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
