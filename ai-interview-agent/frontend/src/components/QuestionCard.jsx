import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export default function QuestionCard({ text, timestamp, isLatest = true }) {
  return (
    <div className={`flex gap-3 md:gap-4 max-w-4xl w-full ${isLatest ? 'animate-bubble-enter' : ''}`}>
      {/* Avatar */}
      <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0 shadow-md">
        <Bot className="w-5 h-5" />
      </div>

      {/* Bubble Container */}
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span className="text-indigo-400 font-bold flex items-center gap-1 font-display">
            <Sparkles className="w-3 h-3" />
            AI Interviewer
          </span>
          {timestamp && <span className="text-slate-500">&bull; {timestamp}</span>}
        </div>

        <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl rounded-tl-sm p-4 md:p-5 text-slate-100 font-normal leading-relaxed text-sm md:text-base shadow-xl backdrop-blur-sm">
          {text}
        </div>
      </div>
    </div>
  );
}
