import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import candidatesData from '../data/candidates.json';
import { useInterview } from '../context/InterviewContext';
import { User, BookOpen, Clock, AlertCircle, Loader2, Sparkles, ChevronRight, BarChart2, CheckCircle2 } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

export default function Home() {
  const candidatesList = candidatesData.candidates || [];
  const [selectedId, setSelectedId] = useState(candidatesList[0]?.member?.id || '');
  const { startInterview, loading, error, setError } = useInterview();
  const navigate = useNavigate();

  const selectedCandidate = candidatesList.find(
    (c) => c.member.id === selectedId
  ) || candidatesList[0];

  const handleStart = async () => {
    if (!selectedCandidate) return;
    try {
      await startInterview(selectedCandidate);
      navigate('/interview');
    } catch (err) {
      // Error state handled in context, UI renders retry button
    }
  };

  const member = selectedCandidate?.member || {};
  const signals = selectedCandidate?.signals || {};
  const missions = selectedCandidate?.missions || [];

  const firstTryMissions = missions.filter((m) => m.passed && m.attempts === 1).length;

  return (
    <div className="min-h-screen flex flex-col justify-between p-4 sm:p-6 md:p-8 relative overflow-hidden font-sans" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}>
      {/* Ambient Background Decorative Gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none" style={{ backgroundColor: 'var(--color-glow)' }} />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none" style={{ backgroundColor: 'var(--color-glow-alt)' }} />

      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 mb-6 md:mb-8" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', boxShadow: `0 4px 12px ${`var(--color-accent-shadow)`}` }}>
            <Sparkles className="w-5 h-5" style={{ color: 'var(--color-accent-text)' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-display tracking-tight" style={{ color: 'var(--color-text-heading)' }}>
              AI Technical Evaluation Agent
            </h1>
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>Enterprise Candidate Review Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <span className="text-xs font-semibold px-3.5 py-1.5 rounded-full" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-accent-text)' }}>
            Cohort Evaluator v1.0
          </span>
        </div>
      </header>

      {/* Main Content Grid */}
      <main className="max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8 my-auto">
        {/* Left Column: Candidate Selector */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold font-display tracking-tight mb-2" style={{ color: 'var(--color-text-heading)' }}>
              Select Candidate Profile
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
              Choose a cohort candidate to initiate a personalized, adaptive technical evaluation session.
            </p>
          </div>

          {/* Select Dropdown (Mobile-Friendly Shortcut) */}
          <div className="space-y-1.5 lg:hidden">
            <label className="block text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--color-accent-text)' }}>
              Select Candidate
            </label>
            <div className="relative">
              <select
                value={selectedId}
                onChange={(e) => {
                  setSelectedId(e.target.value);
                  if (error) setError(null);
                }}
                className="w-full rounded-xl px-4 py-3 font-medium focus:outline-none transition-all appearance-none cursor-pointer text-sm"
                style={{ background: 'var(--color-surface-solid)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
              >
                {candidatesList.map((c) => (
                  <option key={c.member.id} value={c.member.id}>
                    {c.member.name} — {c.member.jobRole}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-secondary)' }}>
                <ChevronRight className="w-4 h-4 rotate-90" />
              </div>
            </div>
          </div>

          {/* Candidates List Preview Cards */}
          <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
            {candidatesList.map((c) => {
              const isSelected = c.member.id === selectedId;
              return (
                <button
                  key={c.member.id}
                  onClick={() => {
                    setSelectedId(c.member.id);
                    if (error) setError(null);
                  }}
                  className="w-full text-left p-3.5 rounded-xl transition-all flex items-center justify-between cursor-pointer"
                  style={{
                    background: isSelected ? 'var(--color-accent-bg)' : 'var(--color-surface)',
                    border: isSelected ? '1px solid var(--color-accent-border)' : '1px solid var(--color-border)',
                    color: isSelected ? 'var(--color-text)' : 'var(--color-text-secondary)',
                    boxShadow: isSelected ? '0 4px 16px var(--color-accent-shadow)' : 'none',
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm transition-all"
                      style={{
                        background: isSelected ? 'var(--color-accent-btn)' : 'var(--color-surface-alt)',
                        color: isSelected ? '#ffffff' : 'var(--color-text-secondary)',
                      }}
                    >
                      {c.member.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-bold text-sm font-display" style={{ color: 'var(--color-text)' }}>{c.member.name}</div>
                      <div className="text-xs font-medium" style={{ color: 'var(--color-accent-text)', opacity: 0.8 }}>{c.member.jobRole}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>{c.member.yearsExperience} yrs exp</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Candidate Details & Action Card */}
        <div className="lg:col-span-7 rounded-2xl p-6 sm:p-8 backdrop-blur-md flex flex-col justify-between shadow-2xl relative" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div>
            {/* Header Badge */}
            <div className="flex items-center justify-between mb-6 pb-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-md" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', color: 'var(--color-accent-text)' }}>
                  <User className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>{member.name}</h3>
                  <p className="text-sm font-semibold" style={{ color: 'var(--color-accent-text)' }}>{member.jobRole}</p>
                </div>
              </div>
              <span className="text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider flex items-center gap-1.5" style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success-border)', color: 'var(--color-success)' }}>
                <CheckCircle2 className="w-3.5 h-3.5" />
                {member.status || 'READY'}
              </span>
            </div>

            {/* Profile Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
                <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                  <Clock className="w-3.5 h-3.5" style={{ color: 'var(--color-accent-text)' }} />
                  Experience
                </div>
                <div className="text-lg font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>
                  {member.yearsExperience} {member.yearsExperience === 1 ? 'Year' : 'Years'}
                </div>
              </div>

              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
                <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                  <BookOpen className="w-3.5 h-3.5" style={{ color: 'var(--color-accent-text)' }} />
                  Education
                </div>
                <div className="text-sm font-semibold truncate" title={member.education} style={{ color: 'var(--color-text-heading)' }}>
                  {member.education || 'N/A'}
                </div>
              </div>
            </div>

            {/* Signal Metrics */}
            <div className="space-y-3 mb-6">
              <h4 className="text-[11px] font-bold uppercase tracking-wider flex items-center gap-2" style={{ color: 'var(--color-accent-text)' }}>
                <BarChart2 className="w-4 h-4" />
                Cohort Learning Performance
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl text-center" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
                  <div className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>Commit Days</div>
                  <div className="text-base font-bold font-display mt-1" style={{ color: 'var(--color-text-heading)' }}>{signals.commitDays || 0} / 31</div>
                </div>
                <div className="p-3.5 rounded-xl text-center" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
                  <div className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>Missions Done</div>
                  <div className="text-base font-bold font-display mt-1" style={{ color: 'var(--color-success)' }}>{signals.missionsCompleted || 0}</div>
                </div>
                <div className="p-3.5 rounded-xl text-center" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border-light)' }}>
                  <div className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>First-Try Passes</div>
                  <div className="text-base font-bold font-display mt-1" style={{ color: 'var(--color-accent-text)' }}>{firstTryMissions}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 rounded-xl flex items-start gap-3" style={{ background: 'var(--color-error-bg)', border: '1px solid var(--color-error-border)', color: 'var(--color-error-text)' }}>
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--color-error)' }} />
              <div className="flex-1 text-sm">
                <p className="font-bold">Failed to start interview session</p>
                <p className="text-xs opacity-90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Start Interview Action Bar */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4" style={{ borderTop: '1px solid var(--color-border)' }}>
            <div className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
              Session ID generated via <code className="font-mono" style={{ color: 'var(--color-accent-text)' }}>crypto.randomUUID()</code>
            </div>
            <button
              onClick={handleStart}
              disabled={loading}
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl text-white font-bold text-sm active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 cursor-pointer"
              style={{
                background: 'var(--color-accent-btn)',
                boxShadow: `0 4px 16px var(--color-accent-shadow)`,
              }}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  Initiating Session...
                </>
              ) : error ? (
                <>
                  <Sparkles className="w-4 h-4" />
                  Retry Start Interview
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Start Interview
                </>
              )}
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-6xl w-full mx-auto text-center text-xs pt-8 mt-8 font-medium" style={{ color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border-light)' }}>
        AI Technical Evaluation Agent &bull; Powered by Gemini LLM &amp; LangGraph State Machine
      </footer>
    </div>
  );
}
