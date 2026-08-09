import React from 'react';
import { CheckCircle2, AlertTriangle, ArrowRightCircle, FileText, BarChart3, PenLine } from 'lucide-react';

function ScoreRing({ percentage, size = 120, strokeWidth = 10 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color =
    percentage >= 80 ? '#22c55e' :
    percentage >= 60 ? '#eab308' :
    percentage >= 40 ? '#f97316' : '#ef4444';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-800"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-extrabold text-white">{percentage}%</span>
        <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Overall</span>
      </div>
    </div>
  );
}

function CategoryBar({ label, value }) {
  const color =
    value >= 80 ? 'from-emerald-500 to-emerald-400' :
    value >= 60 ? 'from-yellow-500 to-yellow-400' :
    value >= 40 ? 'from-orange-500 to-orange-400' : 'from-rose-500 to-rose-400';

  const displayLabel = label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-300 font-medium">{displayLabel}</span>
        <span className="text-slate-400 font-mono">{value}%</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export default function FeedbackCard({ feedback }) {
  if (!feedback) return null;

  const {
    summary,
    strengths = [],
    gaps = [],
    next = [],
    overall_percentage,
    category_breakdown,
    fluency_score,
    fluency_notes,
  } = feedback;

  const hasScores = overall_percentage != null;
  const hasBreakdown = category_breakdown && Object.keys(category_breakdown).length > 0;
  const hasFluency = fluency_score != null;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Overall Score + Category Breakdown Section */}
      {(hasScores || hasBreakdown) && (
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-900/60 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Technical Performance Score</h3>
              <p className="text-xs text-slate-400">Averaged across all evaluated questions</p>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center gap-8">
            {/* Score Ring */}
            {hasScores && (
              <div className="flex-shrink-0">
                <ScoreRing percentage={overall_percentage} />
              </div>
            )}

            {/* Category Breakdown Bars */}
            {hasBreakdown && (
              <div className="flex-1 w-full space-y-3">
                {Object.entries(category_breakdown).map(([key, val]) => (
                  <CategoryBar key={key} label={key} value={val} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

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

      {/* Communication & Writing Clarity — Separate Section */}
      {hasFluency && (
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-900/60 border border-violet-500/30 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden">
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-violet-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <PenLine className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Communication & Writing Clarity</h3>
              <p className="text-xs text-slate-400">Grammatical correctness and expression quality — separate from technical score</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            {/* Fluency Score Badge */}
            <div className="flex-shrink-0 flex flex-col items-center gap-1">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-extrabold border ${
                fluency_score >= 80 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                fluency_score >= 60 ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400' :
                'bg-orange-500/10 border-orange-500/30 text-orange-400'
              }`}>
                {fluency_score}
              </div>
              <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Fluency</span>
            </div>

            {/* Fluency Notes */}
            {fluency_notes && (
              <p className="text-sm text-slate-200 leading-relaxed italic flex-1">
                "{fluency_notes}"
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
