import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterview } from '../context/InterviewContext';
import FeedbackCard from '../components/FeedbackCard';
import { User, Award, RotateCcw, Sparkles } from 'lucide-react';

export default function Results() {
  const navigate = useNavigate();
  const { feedback, candidate, resetSession } = useInterview();

  // Page Refresh / Direct Navigation Safeguard
  useEffect(() => {
    if (!feedback) {
      navigate('/');
    }
  }, [feedback, navigate]);

  if (!feedback) {
    return null;
  }

  const member = candidate?.member || {};

  const handleStartNew = () => {
    resetSession();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 md:p-8 relative overflow-hidden">
      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-slate-800/80 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Award className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Evaluation Results
            </h1>
            <p className="text-xs text-slate-400">AI Cohort Technical Review</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Completed
          </span>
        </div>
      </header>

      {/* Main Results Body */}
      <main className="max-w-4xl w-full mx-auto my-auto space-y-8">
        {/* Candidate Profile Summary Header */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{member.name || 'Cohort Candidate'}</h2>
              <p className="text-sm text-indigo-300 font-medium">{member.jobRole || 'AI Engineer'}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleStartNew}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/25 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Start New Interview
            </button>
          </div>
        </div>

        {/* Feedback Card Display */}
        <FeedbackCard feedback={feedback} />
      </main>

      {/* Footer */}
      <footer className="max-w-6xl w-full mx-auto text-center text-xs text-slate-400 pt-8 border-t border-slate-900 mt-8">
        AI Technical Evaluation Agent &bull; Final Assessment Report
      </footer>
    </div>
  );
}
