import React from 'react';
import { Trophy, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';

export default function CompletionModal({ candidateName, closingMessage, onViewResults }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md animate-modal-backdrop"
      style={{ background: 'var(--color-modal-backdrop)' }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="completion-modal-title"
    >
      <div
        className="rounded-2xl max-w-lg w-full p-6 md:p-8 shadow-2xl space-y-6 relative overflow-hidden text-center transform transition-all animate-modal-content font-sans"
        style={{ background: 'var(--color-surface-solid)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
      >
        {/* Ambient Gradient Background Effect */}
        <div className="absolute -top-24 -left-24 w-56 h-56 rounded-full blur-3xl pointer-events-none" style={{ background: 'var(--color-glow)' }} />
        <div className="absolute -bottom-24 -right-24 w-56 h-56 rounded-full blur-3xl pointer-events-none" style={{ background: 'var(--color-glow-alt)' }} />

        {/* Top Trophy & Success Badge */}
        <div className="flex justify-center">
          <div className="relative">
            <div
              className="w-16 h-16 md:w-20 md:h-20 rounded-2xl flex items-center justify-center shadow-xl"
              style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)' }}
            >
              <Trophy className="w-8 h-8 md:w-10 md:h-10" style={{ color: 'var(--color-warning)' }} />
            </div>
            <div
              className="absolute -bottom-1 -right-1 rounded-full p-1 border-2"
              style={{ background: 'var(--color-success)', color: '#ffffff', borderColor: 'var(--color-surface-solid)' }}
            >
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Title & Congratulations */}
        <div className="space-y-2">
          <div
            className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
            style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', color: 'var(--color-accent-text)' }}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interview Complete</span>
          </div>
          <h2
            id="completion-modal-title"
            className="text-2xl md:text-3xl font-extrabold font-display tracking-tight"
            style={{ color: 'var(--color-text-heading)' }}
          >
            Great job{candidateName ? `, ${candidateName}` : ''}!
          </h2>
        </div>

        {/* Closing Message from Interviewer */}
        <div className="rounded-xl p-4 md:p-5 text-left space-y-1.5" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
          <div className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-accent-text)' }}>
            Interviewer Closing Note
          </div>
          <p className="text-sm md:text-base leading-relaxed font-normal italic" style={{ color: 'var(--color-text)' }}>
            "{closingMessage || "Thank you for completing your technical interview session! We have compiled your performance analysis and personalized feedback."}"
          </p>
        </div>

        {/* Explicit Navigation Button */}
        <div className="pt-2">
          <button
            id="view-results-btn"
            onClick={onViewResults}
            className="w-full py-4 px-6 rounded-xl text-white font-bold text-base shadow-lg flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
            style={{
              background: 'var(--color-accent-btn)',
              boxShadow: '0 4px 16px var(--color-accent-shadow)',
            }}
          >
            <span>View My Results</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
