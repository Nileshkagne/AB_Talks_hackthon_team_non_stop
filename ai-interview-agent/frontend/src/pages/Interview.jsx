import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterview } from '../context/InterviewContext';
import InterviewHeader from '../components/InterviewHeader';
import QuestionCard from '../components/QuestionCard';
import AnswerInput from '../components/AnswerInput';
import { postInterviewTurn } from '../services/api';
import CompletionModal from '../components/CompletionModal';
import { User, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';

export default function Interview() {
  const navigate = useNavigate();
  const {
    sessionId,
    candidate,
    messages,
    addMessage,
    setDone,
    setFeedback,
    resetSession,
  } = useInterview();

  const [answerText, setAnswerText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [turnError, setTurnError] = useState(null);
  const [aiWarning, setAiWarning] = useState(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [closingMessage, setClosingMessage] = useState('');

  const messagesEndRef = useRef(null);

  // Redirect to home if accessed without an active session
  useEffect(() => {
    if (!sessionId || !candidate) {
      navigate('/');
    }
  }, [sessionId, candidate, navigate]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages, isSubmitting]);

  if (!sessionId || !candidate) {
    return null;
  }

  const questionCount = messages.filter((m) => m.sender === 'interviewer').length;

  const handleSubmit = async () => {
    const textToSend = answerText.trim();
    if (!textToSend || isSubmitting) return;

    setTurnError(null);
    setIsSubmitting(true);

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const candMsg = {
      id: `cand-${Date.now()}`,
      sender: 'candidate',
      text: textToSend,
      timestamp,
    };

    addMessage(candMsg);

    try {
      const res = await postInterviewTurn({
        sessionId,
        message: textToSend,
      });

      setAnswerText('');

      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: 'interviewer',
        text: res.reply || 'Thank you.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      addMessage(botMsg);

      if (res.warning === 'ai_temporarily_unavailable') {
        setAiWarning('AI service is temporarily busy — this response may be a generic fallback rather than a tailored one.');
      } else {
        setAiWarning(null);
      }

      if (res.done) {
        setDone(true);
        if (res.feedback) {
          setFeedback(res.feedback);
        }
        setClosingMessage(res.reply || res.feedback?.closing_message || 'Thank you for completing your interview session!');
        setShowCompletionModal(true);
      }
    } catch (err) {
      const msg = err.message || 'Failed to submit response. Please check server connection.';
      setTurnError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExit = () => {
    if (window.confirm('Are you sure you want to end this interview session?')) {
      resetSession();
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between font-sans">
      {/* Header */}
      <InterviewHeader
        candidate={candidate}
        currentTurn={questionCount}
        onExit={handleExit}
      />

      {/* Main Conversation Canvas */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 md:p-8 flex flex-col justify-between space-y-6">
        {/* AI Warning Banner */}
        {aiWarning && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start justify-between gap-3 animate-bubble-enter">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm font-medium">{aiWarning}</p>
            </div>
            <button
              onClick={() => setAiWarning(null)}
              className="text-xs text-amber-400 hover:text-amber-200 underline font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Messages Stream */}
        <div className="space-y-6 flex-1">
          {messages.map((msg, idx) => {
            const isLatest = idx === messages.length - 1;
            if (msg.sender === 'interviewer') {
              return (
                <QuestionCard
                  key={msg.id || idx}
                  text={msg.text}
                  timestamp={msg.timestamp}
                  isLatest={isLatest}
                />
              );
            }

            // Candidate Message Bubble
            return (
              <div
                key={msg.id || idx}
                className="flex justify-end gap-3 md:gap-4 max-w-4xl w-full ml-auto animate-bubble-enter"
              >
                <div className="flex-1 space-y-1 text-right">
                  <div className="flex items-center justify-end gap-2 text-xs font-semibold text-slate-400">
                    {msg.timestamp && <span>{msg.timestamp} &bull;</span>}
                    <span className="text-slate-200 font-bold">{candidate?.member?.name || 'You'}</span>
                  </div>

                  <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 border border-indigo-500/80 text-white rounded-2xl rounded-tr-sm p-4 md:p-5 font-normal leading-relaxed text-sm md:text-base inline-block text-left shadow-lg shadow-indigo-600/20">
                    {msg.text}
                  </div>
                </div>

                <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 shadow-md">
                  <User className="w-5 h-5" />
                </div>
              </div>
            );
          })}

          {/* Thinking Indicator */}
          {isSubmitting && (
            <div className="flex gap-3 md:gap-4 max-w-4xl w-full animate-bubble-enter">
              <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0 shadow-md animate-shimmer-pulse">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl rounded-tl-sm p-4 md:p-5 shadow-xl backdrop-blur-sm">
                <div className="flex items-center gap-2.5 text-sm text-slate-300 font-medium">
                  <span>AI Interviewer is evaluating...</span>
                  <span className="flex gap-1.5 items-center">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Turn Error Banner */}
        {turnError && (
          <div className="max-w-4xl mx-auto w-full p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between gap-3 animate-bubble-enter">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-bold">Submission failed</p>
                <p className="text-xs opacity-90">{turnError}</p>
              </div>
            </div>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-bold border border-rose-500/40 flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Submit
            </button>
          </div>
        )}

        {/* Sticky Bottom Input Bar */}
        <div className="pt-4 border-t border-slate-900 bg-slate-950/90 backdrop-blur-md sticky bottom-0 z-10">
          <AnswerInput
            value={answerText}
            onChange={setAnswerText}
            onSubmit={handleSubmit}
            disabled={isSubmitting}
          />
        </div>
      </main>

      {/* Completion Modal Popup */}
      {showCompletionModal && (
        <CompletionModal
          candidateName={candidate?.member?.name || candidate?.name}
          closingMessage={closingMessage}
          onViewResults={() => navigate('/results')}
        />
      )}
    </div>
  );
}
