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
  const roomRef = useRef(null);

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

  // Compute avatar visibility: show avatar only on first message in a consecutive sender block
  const shouldShowAvatar = (idx) => {
    if (idx === 0) return true;
    return messages[idx].sender !== messages[idx - 1].sender;
  };

  const candidateName = candidate?.member?.name || 'You';

  return (
    <div className="min-h-screen flex flex-col justify-between font-sans" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}>
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
          <div className="p-4 rounded-xl flex items-start justify-between gap-3 animate-bubble-enter" style={{ background: 'var(--color-warning-bg)', border: '1px solid var(--color-warning-border)', color: 'var(--color-warning-text)' }}>
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--color-warning)' }} />
              <p className="text-sm font-medium">{aiWarning}</p>
            </div>
            <button
              onClick={() => setAiWarning(null)}
              className="text-xs hover:opacity-80 underline font-semibold"
              style={{ color: 'var(--color-warning)' }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Interview Room Container */}
        <div
          ref={roomRef}
          className="interview-room flex-1 overflow-y-auto p-4 sm:p-5 md:p-6 space-y-5"
          style={{ maxHeight: 'calc(100vh - 260px)' }}
        >
          {messages.map((msg, idx) => {
            const isLatest = idx === messages.length - 1;
            const showAvatar = shouldShowAvatar(idx);

            if (msg.sender === 'interviewer') {
              return (
                <QuestionCard
                  key={msg.id || idx}
                  text={msg.text}
                  timestamp={msg.timestamp}
                  isLatest={isLatest}
                  showAvatar={showAvatar}
                />
              );
            }

            // ── Candidate Message Bubble ──
            return (
              <div
                key={msg.id || idx}
                className={`flex justify-end gap-3 md:gap-4 max-w-3xl w-full ml-auto ${
                  isLatest ? 'animate-msg-right' : ''
                }`}
              >
                <div className="flex-1 space-y-1.5 text-right min-w-0">
                  {/* Label row — only with avatar */}
                  {showAvatar && (
                    <div className="flex items-center justify-end gap-2 text-xs font-semibold pr-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                      {isLatest && msg.timestamp && (
                        <span>{msg.timestamp} &bull;</span>
                      )}
                      <span className="font-bold" style={{ color: 'var(--color-text)' }}>{candidateName}</span>
                    </div>
                  )}

                  {/* Bubble */}
                  <div
                    className="rounded-2xl rounded-tr-sm p-4 md:p-5 font-normal leading-relaxed text-sm md:text-base inline-block text-left"
                    style={{
                      background: 'var(--color-candidate-bubble)',
                      color: 'var(--color-candidate-bubble-text)',
                      boxShadow: `0 4px 24px -4px var(--color-accent-shadow)`,
                    }}
                  >
                    {msg.text}
                  </div>
                </div>

                {/* Avatar — only first in block */}
                {showAvatar ? (
                  <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md mt-1" style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
                    <User className="w-5 h-5" />
                  </div>
                ) : (
                  <div className="w-9 md:w-10 flex-shrink-0" />
                )}
              </div>
            );
          })}

          {/* Thinking Indicator */}
          {isSubmitting && (
            <div className="flex gap-3 md:gap-4 max-w-3xl w-full animate-msg-left">
              <div
                className="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md animate-shimmer-pulse"
                style={{
                  background: 'var(--color-accent-bg)',
                  border: '1px solid var(--color-accent-border)',
                }}
              >
                <Sparkles className="w-5 h-5" style={{ color: `rgb(var(--accent-glow))` }} />
              </div>
              <div
                className="rounded-2xl rounded-tl-sm p-4 md:p-5 backdrop-blur-sm"
                style={{
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  boxShadow: '0 4px 24px -4px rgba(0,0,0,0.15)',
                }}
              >
                <div className="flex items-center gap-2.5 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
                  <span>AI Interviewer is evaluating...</span>
                  <span className="flex gap-1.5 items-center">
                    <span
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: `rgb(var(--accent-glow))`, animationDelay: '0ms' }}
                    />
                    <span
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: `rgb(var(--accent-glow))`, animationDelay: '150ms' }}
                    />
                    <span
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ background: `rgb(var(--accent-glow))`, animationDelay: '300ms' }}
                    />
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Turn Error Banner */}
        {turnError && (
          <div className="max-w-4xl mx-auto w-full p-4 rounded-xl flex items-center justify-between gap-3 animate-bubble-enter" style={{ background: 'var(--color-error-bg)', border: '1px solid var(--color-error-border)', color: 'var(--color-error-text)' }}>
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--color-error)' }} />
              <div className="text-sm">
                <p className="font-bold">Submission failed</p>
                <p className="text-xs opacity-90">{turnError}</p>
              </div>
            </div>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 cursor-pointer"
              style={{ background: 'var(--color-error-bg)', border: '1px solid var(--color-error-border)', color: 'var(--color-error-text)' }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Submit
            </button>
          </div>
        )}

        {/* Sticky Bottom Input Bar */}
        <div className="pt-4 backdrop-blur-md sticky bottom-0 z-10" style={{ borderTop: '1px solid var(--color-border-light)', backgroundColor: 'var(--color-bg)' }}>
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
