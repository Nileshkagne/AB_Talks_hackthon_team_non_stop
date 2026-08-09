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
      <div className="relative bg-slate-900/90 border border-slate-800 rounded-2xl p-3 md:p-4 focus-within:border-indigo-500/80 focus-within:ring-2 focus-within:ring-indigo-500/30 transition-all shadow-xl backdrop-blur-md">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type your technical response here... (Ctrl+Enter to submit)"
          rows={4}
          maxLength={maxLength}
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm md:text-base focus:outline-none resize-none disabled:opacity-50 font-normal leading-relaxed"
        />

        <div className="flex items-center justify-between pt-3 border-t border-slate-800/80">
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1 hidden sm:inline-flex font-medium">
              <CornerDownLeft className="w-3.5 h-3.5 text-slate-400" />
              Press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px]">Ctrl+Enter</kbd> to send
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`text-xs font-mono font-medium ${
                isOverLimit
                  ? 'text-rose-400 font-bold'
                  : value.length > maxLength * 0.9
                  ? 'text-amber-400'
                  : 'text-slate-500'
              }`}
            >
              {value.length} / {maxLength}
            </span>

            <button
              onClick={onSubmit}
              disabled={disabled || !value.trim() || isOverLimit}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
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
