import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function Toast({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mb-4 animate-fade-in">
      <div
        className="p-4 rounded-xl flex items-center justify-between gap-3 shadow-lg backdrop-blur-sm"
        style={{
          background: 'var(--color-warning-bg)',
          border: '1px solid var(--color-warning-border)',
          color: 'var(--color-warning-text)',
        }}
      >
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--color-warning)' }} />
          <div className="text-sm font-medium leading-snug">
            {message}
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded-lg transition-colors flex-shrink-0 cursor-pointer"
            style={{ color: 'var(--color-warning)' }}
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
