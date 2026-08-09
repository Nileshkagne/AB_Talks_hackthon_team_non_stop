import React from 'react';
import { User, LogOut } from 'lucide-react';
import ProgressBar from './ProgressBar';
import ThemeToggle from './ThemeToggle';

export default function InterviewHeader({ candidate, currentTurn = 1, onExit }) {
  const member = candidate?.member || {};

  return (
    <header className="backdrop-blur-md sticky top-0 z-20 px-4 md:px-8 py-3.5 font-sans" style={{ background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)' }}>
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4">
        {/* Left: Candidate Info */}
        <div className="flex items-center justify-between w-full md:w-auto">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shadow-md"
              style={{
                background: 'var(--color-accent-bg)',
                border: '1px solid var(--color-accent-border)',
              }}
            >
              <User className="w-5 h-5" style={{ color: 'var(--color-accent-text)' }} />
            </div>
            <div>
              <h2 className="text-base font-bold font-display leading-snug" style={{ color: 'var(--color-text-heading)' }}>
                {member.name || 'Candidate'}
              </h2>
              <p className="text-xs font-medium" style={{ color: 'var(--color-accent-text)' }}>
                {member.jobRole || 'AI Cohort Evaluator'}
              </p>
            </div>
          </div>

          {/* Mobile Right Controls: ThemeToggle + Exit */}
          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            {onExit && (
              <button
                onClick={onExit}
                className="text-xs font-semibold flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer"
                style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}
                title="Exit Interview"
              >
                <LogOut className="w-3.5 h-3.5" />
                Exit
              </button>
            )}
          </div>
        </div>

        {/* Center: Progress Bar */}
        <div className="w-full md:w-72">
          <ProgressBar currentTurn={currentTurn} maxEstimatedTurns={10} />
        </div>

        {/* Right: ThemeToggle + Exit / Session Status */}
        <div className="hidden md:flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider" style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success-border)', color: 'var(--color-success)' }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--color-success)' }} />
            Live Session
          </span>
          <ThemeToggle />
          {onExit && (
            <button
              onClick={onExit}
              className="text-xs font-semibold transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg cursor-pointer active:scale-95"
              style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}
            >
              <LogOut className="w-3.5 h-3.5" />
              End Session
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
