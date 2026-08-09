import React from 'react';

export default function ProgressBar({ currentTurn = 1, maxEstimatedTurns = 10 }) {
  const percentage = Math.min(Math.round((currentTurn / maxEstimatedTurns) * 100), 100);

  return (
    <div className="w-full space-y-1.5 font-sans">
      <div className="flex items-center justify-between text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
        <span>Interview Progress</span>
        <span className="font-semibold" style={{ color: 'var(--color-text)' }}>Question ~{currentTurn} of ~{maxEstimatedTurns}</span>
      </div>
      <div className="w-full h-2.5 rounded-full overflow-hidden p-0.5 shadow-inner" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}>
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${percentage}%`,
            background: 'linear-gradient(90deg, rgb(var(--accent-dark)), rgb(var(--accent)))',
            boxShadow: '0 0 8px var(--color-accent-shadow)',
          }}
        />
      </div>
    </div>
  );
}
