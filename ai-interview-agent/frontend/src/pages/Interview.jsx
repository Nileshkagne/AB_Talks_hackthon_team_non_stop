import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterview } from '../context/InterviewContext';
import InterviewHeader from '../components/InterviewHeader';
import QuestionCard from '../components/QuestionCard';
import AnswerInput from '../components/AnswerInput';
import { postInterviewTurn } from '../services/api';
import Toast from '../components/Toast';
import { User, AlertCircle, RefreshCw } from 'lucide-react';

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

  const messagesEndRef = useRef(null);

  // Redirect to home if accessed without an active session
  useEffect(() => {
    if (!sessionId || !candidate) {
      navigate('/');
    }
  }, [sessionId, candidate, navigate]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSubmitting]);

  if (!sessionId || !candidate) {
    return null;
  }

  // Count interviewer questions asked so far to derive current turn count for header
  const questionCount = messages.filter((m) => m.sender === 'interviewer').length;

  const handleSubmit = async () => {
    const textToSend = answerText.trim();
    if (!textToSend || isSubmitting) return;

    setTurnError(null);
    setIsSubmitting(true);

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Append candidate message immediately to transcript
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

      // Clear input on successful server round-trip
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
        setTimeout(() => {
          navigate('/results');
        }, 1200);
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <InterviewHeader
        candidate={candidate}
        currentTurn={questionCount}
        onExit={handleExit}
      />

      {/* Main Conversation Canvas */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 md:p-8 flex flex-col justify-between space-y-6">
        {/* AI Warning Banner */}
        {aiWarning && (
          <Toast
            message={aiWarning}
            onDismiss={() => setAiWarning(null)}
          />
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
                className="flex justify-end gap-3 md:gap-4 max-w-4xl w-full ml-auto animate-fade-in"
              >
                <div className="flex-1 space-y-1 text-right">
                  <div className="flex items-center justify-end gap-2 text-xs font-semibold text-slate-400">
                    {msg.timestamp && <span>{msg.timestamp} &bull;</span>}
                    <span className="text-slate-200">{candidate?.member?.name || 'You'}</span>
                  </div>

                  <div className="bg-indigo-600/90 border border-indigo-500/80 text-white rounded-2xl rounded-tr-sm p-4 md:p-5 font-normal leading-relaxed text-sm md:text-base inline-block text-left shadow-lg">
                    {msg.text}
                  </div>
                </div>

                <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 flex-shrink-0 shadow-md">
                  <User className="w-5 h-5" />
                </div>
              </div>
            );
          })}

          {/* Animated Thinking Indicator */}
          {isSubmitting && (
            <div className="flex gap-3 md:gap-4 max-w-4xl w-full animate-fade-in">
              <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-indigo-500/30 to-cyan-500/30 border border-indigo-500/40 flex items-center justify-center flex-shrink-0 shadow-md animate-pulse">
                <span className="text-lg">🤖</span>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl rounded-tl-sm p-4 md:p-5 shadow-lg">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>AI is thinking</span>
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                    <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                    <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Turn Error Banner */}
        {turnError && (
          <div className="max-w-4xl mx-auto w-full p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-semibold">Submission failed</p>
                <p className="text-xs opacity-90">{turnError}</p>
              </div>
            </div>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-bold border border-rose-500/40 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Submit
            </button>
          </div>
        )}

        {/* Sticky Bottom Input Bar */}
        <div className="pt-4 border-t border-slate-900 bg-slate-950/80 backdrop-blur-md sticky bottom-0">
          <AnswerInput
            value={answerText}
            onChange={setAnswerText}
            onSubmit={handleSubmit}
            disabled={isSubmitting}
          />
        </div>
      </main>
    </div>
  );
}
