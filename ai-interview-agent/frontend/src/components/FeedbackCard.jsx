import React from 'react';
import { CheckCircle2, AlertTriangle, ArrowRightCircle, FileText } from 'lucide-react';

export default function FeedbackCard({ feedback }) {
  if (!feedback) return null;

  const { summary, strengths = [], gaps = [], next = [] } = feedback;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Executive Summary Card */}
      <div className="bg-gradient-to-br from-slate-900/90 to-slate-900/60 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Executive Evaluation Summary</h3>
            <p className="text-xs text-slate-400">AI Cohort Technical Performance Review</p>
          </div>
        </div>

        <p className="text-slate-200 text-sm md:text-base leading-relaxed font-normal">
          {summary || 'Candidate evaluation complete.'}
        </p>
      </div>

      {/* 3 Labeled Section Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Strengths List */}
        <div className="bg-slate-900/60 border border-emerald-500/30 rounded-2xl p-5 md:p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 text-emerald-400 font-bold text-base mb-4 pb-3 border-b border-slate-800">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <span>Key Strengths</span>
            </div>

            <ul className="space-y-3">
              {strengths.length > 0 ? (
                strengths.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs md:text-sm text-slate-200 leading-normal">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-500 italic">No specific strengths recorded.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Technical Gaps List */}
        <div className="bg-slate-900/60 border border-amber-500/30 rounded-2xl p-5 md:p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 text-amber-400 font-bold text-base mb-4 pb-3 border-b border-slate-800">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <span>Growth Areas & Gaps</span>
            </div>

            <ul className="space-y-3">
              {gaps.length > 0 ? (
                gaps.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs md:text-sm text-slate-200 leading-normal">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-500 italic">No technical gaps identified.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Recommended Next Steps List */}
        <div className="bg-slate-900/60 border border-indigo-500/30 rounded-2xl p-5 md:p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 text-indigo-400 font-bold text-base mb-4 pb-3 border-b border-slate-800">
              <ArrowRightCircle className="w-5 h-5 text-indigo-400 flex-shrink-0" />
              <span>Actionable Next Steps</span>
            </div>

            <ul className="space-y-3">
              {next.length > 0 ? (
                next.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs md:text-sm text-slate-200 leading-normal">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-500 italic">No next steps provided.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
