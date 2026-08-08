import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import candidatesData from '../data/candidates.json';
import { useInterview } from '../context/InterviewContext';
import { User, BookOpen, Clock, AlertCircle, Loader2, Sparkles, ChevronRight, BarChart2 } from 'lucide-react';

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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 md:p-8 relative overflow-hidden">
      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-slate-800/80 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              AI Interview Agent
            </h1>
            <p className="text-xs text-slate-400">Enterprise Candidate Evaluator</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-indigo-300">
          Cohort Evaluator v1.0
        </span>
      </header>

      {/* Main Content Container */}
      <main className="max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 my-auto">
        {/* Left Column: Selector */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight mb-2">
              Select Candidate Profile
            </h2>
            <p className="text-sm text-slate-400">
              Choose a cohort candidate to initiate a personalized, adaptive technical evaluation session.
            </p>
          </div>

          {/* Select Dropdown */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Candidate Selector
            </label>
            <div className="relative">
              <select
                value={selectedId}
                onChange={(e) => {
                  setSelectedId(e.target.value);
                  if (error) setError(null);
                }}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-3.5 text-slate-100 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-inner appearance-none cursor-pointer"
              >
                {candidatesList.map((c) => (
                  <option key={c.member.id} value={c.member.id} className="bg-slate-900 text-slate-100">
                    {c.member.name} — {c.member.jobRole}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                <ChevronRight className="w-5 h-5 rotate-90" />
              </div>
            </div>
          </div>

          {/* Candidates List Preview Cards */}
          <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
            {candidatesList.map((c) => {
              const isSelected = c.member.id === selectedId;
              return (
                <button
                  key={c.member.id}
                  onClick={() => {
                    setSelectedId(c.member.id);
                    if (error) setError(null);
                  }}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 text-white shadow-md shadow-indigo-950/50'
                      : 'bg-slate-900/40 border-slate-800/60 text-slate-300 hover:bg-slate-900/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {c.member.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-semibold text-sm">{c.member.name}</div>
                      <div className="text-xs text-slate-400">{c.member.jobRole}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">{c.member.yearsExperience} yrs exp</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Candidate Details & Action */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 md:p-8 backdrop-blur-sm flex flex-col justify-between shadow-2xl relative">
          <div>
            {/* Header Badge */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800/80">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <User className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{member.name}</h3>
                  <p className="text-sm font-medium text-indigo-400">{member.jobRole}</p>
                </div>
              </div>
              <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 uppercase tracking-wider">
                {member.status || 'READY'}
              </span>
            </div>

            {/* Profile Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-slate-950/60 border border-slate-800/70 p-4 rounded-xl">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  <Clock className="w-4 h-4 text-indigo-400" />
                  Experience
                </div>
                <div className="text-lg font-bold text-white">
                  {member.yearsExperience} {member.yearsExperience === 1 ? 'Year' : 'Years'}
                </div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800/70 p-4 rounded-xl">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  <BookOpen className="w-4 h-4 text-cyan-400" />
                  Education
                </div>
                <div className="text-sm font-semibold text-white truncate" title={member.education}>
                  {member.education || 'N/A'}
                </div>
              </div>
            </div>

            {/* Signal Metrics */}
            <div className="space-y-3 mb-6">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-indigo-400" />
                Cohort Learning Performance
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-950/40 border border-slate-800/60 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-400">Commit Days</div>
                  <div className="text-base font-bold text-white mt-1">{signals.commitDays || 0} / 31</div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/60 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-400">Missions Done</div>
                  <div className="text-base font-bold text-emerald-400 mt-1">{signals.missionsCompleted || 0}</div>
                </div>
                <div className="bg-slate-950/40 border border-slate-800/60 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-400">First-Try Passes</div>
                  <div className="text-base font-bold text-indigo-400 mt-1">{firstTryMissions}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm">
                <p className="font-semibold">Failed to start interview session</p>
                <p className="text-xs opacity-90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Start Interview Action */}
          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
            <div className="text-xs text-slate-400">
              Session ID generated via <code className="text-indigo-300">crypto.randomUUID()</code>
            </div>
            <button
              onClick={handleStart}
              disabled={loading}
              className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/25 hover:shadow-indigo-600/40 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
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
      <footer className="max-w-6xl w-full mx-auto text-center text-xs text-slate-400 pt-8 border-t border-slate-900 mt-8">
        AI Technical Evaluation Agent &bull; Powered by Gemini LLM & LangGraph State Machine
      </footer>
    </div>
  );
}
