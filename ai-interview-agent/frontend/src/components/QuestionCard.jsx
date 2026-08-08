import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export default function QuestionCard({ text, timestamp, isLatest = true }) {
  return (
    <div className={`flex gap-3 md:gap-4 max-w-4xl w-full ${isLatest ? 'animate-fade-in' : ''}`}>
      {/* Avatar */}
      <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white flex-shrink-0 shadow-lg shadow-indigo-600/20">
        <Bot className="w-5 h-5" />
      </div>

      {/* Bubble Container */}
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span className="text-indigo-400 font-bold flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            AI Interviewer
          </span>
          {timestamp && <span>&bull; {timestamp}</span>}
        </div>

        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl rounded-tl-sm p-4 md:p-5 text-slate-100 font-normal leading-relaxed text-sm md:text-base shadow-xl backdrop-blur-sm">
          {text}
        </div>
      </div>
    </div>
  );
}
