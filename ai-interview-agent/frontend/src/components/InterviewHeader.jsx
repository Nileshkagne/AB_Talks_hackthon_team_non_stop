import React from 'react';
import { User, LogOut } from 'lucide-react';
import ProgressBar from './ProgressBar';

export default function InterviewHeader({ candidate, currentTurn = 1, onExit }) {
  const member = candidate?.member || {};

  return (
    <header className="bg-slate-900/90 border-b border-slate-800/90 backdrop-blur-md sticky top-0 z-20 px-4 md:px-8 py-3.5 font-sans">
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3 md:gap-4">
        {/* Left: Candidate Info */}
        <div className="flex items-center justify-between w-full md:w-auto">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shadow-md">
              <User className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-base font-bold font-display text-white leading-snug">
                {member.name || 'Candidate'}
              </h2>
              <p className="text-xs text-indigo-300 font-medium">
                {member.jobRole || 'AI Cohort Evaluator'}
              </p>
            </div>
          </div>

          {/* Mobile Exit Button */}
          {onExit && (
            <button
              onClick={onExit}
              className="md:hidden text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950/60 active:scale-95 transition-all"
              title="Exit Interview"
            >
              <LogOut className="w-3.5 h-3.5" />
              Exit
            </button>
          )}
        </div>

        {/* Center: Progress Bar */}
        <div className="w-full md:w-72">
          <ProgressBar currentTurn={currentTurn} maxEstimatedTurns={10} />
        </div>

        {/* Right: Exit / Session Status */}
        <div className="hidden md:flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live Session
          </span>
          {onExit && (
            <button
              onClick={onExit}
              className="text-xs font-semibold text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-rose-900/50 bg-slate-950/40 cursor-pointer active:scale-95"
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
