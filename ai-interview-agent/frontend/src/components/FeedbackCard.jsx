import React from 'react';
import { CheckCircle2, AlertTriangle, ArrowRightCircle, FileText, BarChart3, PenLine } from 'lucide-react';

function ScoreRing({ percentage, size = 130, strokeWidth = 10 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color =
    percentage >= 80 ? 'var(--color-success)' :
    percentage >= 60 ? 'var(--color-warning)' :
    'var(--color-error)';

  return (
    <div className="relative flex items-center justify-center font-sans" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
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
        <span className="text-3xl font-extrabold font-display" style={{ color: 'var(--color-text-heading)' }}>{percentage}%</span>
        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-accent-text)' }}>Overall</span>
      </div>
    </div>
  );
}

function CategoryBar({ label, value }) {
  const color =
    value >= 80 ? 'from-emerald-500 to-emerald-400' :
    value >= 60 ? 'from-amber-500 to-amber-400' :
    'from-rose-500 to-rose-400';

  const displayLabel = label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="space-y-1.5 font-sans">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold" style={{ color: 'var(--color-text)' }}>{displayLabel}</span>
        <span className="font-mono font-medium" style={{ color: 'var(--color-text-secondary)' }}>{value}%</span>
      </div>
      <div className="w-full h-2.5 rounded-full overflow-hidden p-0.5" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}>
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
    <div className="space-y-6 max-w-4xl mx-auto font-sans">
      {/* Overall Score + Category Breakdown Section */}
      {(hasScores || hasBreakdown) && (
        <div className="rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl pointer-events-none" style={{ background: 'var(--color-glow)' }} />

          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', color: 'var(--color-accent-text)' }}>
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>Technical Performance Score</h3>
              <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>Averaged across all evaluated questions</p>
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
              <div className="flex-1 w-full space-y-3.5">
                {Object.entries(category_breakdown).map(([key, val]) => (
                  <CategoryBar key={key} label={key} value={val} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Executive Summary Card */}
      <div className="rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl pointer-events-none" style={{ background: 'var(--color-glow)' }} />
        
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', color: 'var(--color-accent-text)' }}>
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>Executive Evaluation Summary</h3>
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>AI Cohort Technical Performance Review</p>
          </div>
        </div>

        <p className="text-sm md:text-base leading-relaxed font-normal" style={{ color: 'var(--color-text)' }}>
          {summary || 'Candidate evaluation complete.'}
        </p>
      </div>

      {/* 3 Labeled Section Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Key Strengths List */}
        <div className="rounded-2xl p-5 md:p-6 shadow-xl backdrop-blur-md flex flex-col justify-between" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-success-border)' }}>
          <div>
            <div className="flex items-center gap-2.5 font-bold font-display text-base mb-4 pb-3" style={{ color: 'var(--color-success)', borderBottom: '1px solid var(--color-border-light)' }}>
              <CheckCircle2 className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--color-success)' }} />
              <span>Key Strengths</span>
            </div>

            <ul className="space-y-3">
              {strengths.length > 0 ? (
                strengths.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs md:text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                    <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: 'var(--color-success)' }} />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs italic" style={{ color: 'var(--color-text-tertiary)' }}>No specific strengths recorded.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Technical Gaps List */}
        <div className="rounded-2xl p-5 md:p-6 shadow-xl backdrop-blur-md flex flex-col justify-between" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-warning-border)' }}>
          <div>
            <div className="flex items-center gap-2.5 font-bold font-display text-base mb-4 pb-3" style={{ color: 'var(--color-warning-text)', borderBottom: '1px solid var(--color-border-light)' }}>
              <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--color-warning)' }} />
              <span>Growth Areas &amp; Gaps</span>
            </div>

            <ul className="space-y-3">
              {gaps.length > 0 ? (
                gaps.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs md:text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                    <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: 'var(--color-warning)' }} />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs italic" style={{ color: 'var(--color-text-tertiary)' }}>No technical gaps identified.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Recommended Next Steps List */}
        <div className="rounded-2xl p-5 md:p-6 shadow-xl backdrop-blur-md flex flex-col justify-between" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-accent-border)' }}>
          <div>
            <div className="flex items-center gap-2.5 font-bold font-display text-base mb-4 pb-3" style={{ color: 'var(--color-accent-text)', borderBottom: '1px solid var(--color-border-light)' }}>
              <ArrowRightCircle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--color-accent-text)' }} />
              <span>Actionable Next Steps</span>
            </div>

            <ul className="space-y-3">
              {next.length > 0 ? (
                next.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs md:text-sm leading-relaxed" style={{ color: 'var(--color-text)' }}>
                    <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: 'var(--color-accent-text)' }} />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs italic" style={{ color: 'var(--color-text-tertiary)' }}>No next steps provided.</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Communication & Writing Clarity — Separate Section */}
      {hasFluency && (
        <div className="rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-md relative overflow-hidden" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-info-border)' }}>
          <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full blur-3xl pointer-events-none" style={{ background: 'var(--color-glow-alt)' }} />

          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-info-bg)', border: '1px solid var(--color-info-border)', color: 'var(--color-info)' }}>
              <PenLine className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>Communication &amp; Writing Clarity</h3>
              <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>Grammatical correctness and expression quality — separate from technical score</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            {/* Fluency Score Badge */}
            <div className="flex-shrink-0 flex flex-col items-center gap-1">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-extrabold font-display border"
                style={{
                  background: fluency_score >= 80 ? 'var(--color-success-bg)' : fluency_score >= 60 ? 'var(--color-warning-bg)' : 'var(--color-error-bg)',
                  borderColor: fluency_score >= 80 ? 'var(--color-success-border)' : fluency_score >= 60 ? 'var(--color-warning-border)' : 'var(--color-error-border)',
                  color: fluency_score >= 80 ? 'var(--color-success)' : fluency_score >= 60 ? 'var(--color-warning-text)' : 'var(--color-error-text)',
                }}
              >
                {fluency_score}
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-accent-text)' }}>Fluency</span>
            </div>

            {/* Fluency Notes */}
            {fluency_notes && (
              <p className="text-sm leading-relaxed italic flex-1" style={{ color: 'var(--color-text)' }}>
                "{fluency_notes}"
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
