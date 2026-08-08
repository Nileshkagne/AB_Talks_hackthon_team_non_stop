import React from 'react';

export default function ProgressBar({ currentTurn = 1, maxEstimatedTurns = 10 }) {
  const percentage = Math.min(Math.round((currentTurn / maxEstimatedTurns) * 100), 100);

  return (
    <div className="w-full space-y-1.5">
      <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
        <span>Interview Progress</span>
        <span>Question ~{currentTurn} of ~{maxEstimatedTurns}</span>
      </div>
      <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800/80 p-0.5">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500 ease-out shadow-sm shadow-indigo-500/50"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
