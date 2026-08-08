import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function Toast({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mb-4 animate-fade-in">
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 flex items-center justify-between gap-3 shadow-lg backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
          <div className="text-sm font-medium leading-snug">
            {message}
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded-lg hover:bg-amber-500/20 text-amber-400 transition-colors flex-shrink-0"
            title="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
