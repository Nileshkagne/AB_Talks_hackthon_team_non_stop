import React from 'react';
import { Trophy, ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';

export default function CompletionModal({ candidateName, closingMessage, onViewResults }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="completion-modal-title"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 md:p-8 shadow-2xl space-y-6 relative overflow-hidden text-center transform transition-all animate-modal-content font-sans">
        {/* Ambient Gradient Background Effect */}
        <div className="absolute -top-24 -left-24 w-56 h-56 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-56 h-56 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Trophy & Success Badge */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-xl">
              <Trophy className="w-8 h-8 md:w-10 md:h-10 text-amber-400" />
            </div>
            <div className="absolute -bottom-1 -right-1 bg-emerald-500 text-slate-950 rounded-full p-1 border-2 border-slate-900">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Title & Congratulations */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interview Complete</span>
          </div>
          <h2
            id="completion-modal-title"
            className="text-2xl md:text-3xl font-extrabold font-display text-white tracking-tight"
          >
            Great job{candidateName ? `, ${candidateName}` : ''}!
          </h2>
        </div>

        {/* Closing Message from Interviewer */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 md:p-5 text-left space-y-1.5">
          <div className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
            Interviewer Closing Note
          </div>
          <p className="text-sm md:text-base text-slate-200 leading-relaxed font-normal italic">
            "{closingMessage || "Thank you for completing your technical interview session! We have compiled your performance analysis and personalized feedback."}"
          </p>
        </div>

        {/* Explicit Navigation Button */}
        <div className="pt-2">
          <button
            id="view-results-btn"
            onClick={onViewResults}
            className="w-full py-4 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-base shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
          >
            <span>View My Results</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
