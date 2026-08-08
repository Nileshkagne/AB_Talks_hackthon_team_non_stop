import React, { createContext, useContext, useState } from 'react';
import { postInterviewTurn } from '../services/api';

const InterviewContext = createContext(null);

export function InterviewProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [candidate, setCandidate] = useState(null);
  const [messages, setMessages] = useState([]);
  const [done, setDone] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startInterview = async (candidateObj) => {
    setLoading(true);
    setError(null);
    try {
      const newSessionId = crypto.randomUUID();
      const res = await postInterviewTurn({
        sessionId: newSessionId,
        candidate: candidateObj,
      });

      setSessionId(newSessionId);
      setCandidate(candidateObj);
      setMessages([
        {
          id: '1',
          sender: 'interviewer',
          text: res.reply || "Welcome. Let's begin your interview.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
      setDone(false);
      setFeedback(null);
      setLoading(false);
      return res;
    } catch (err) {
      setLoading(false);
      const msg = err.message || 'Failed to start interview. Please check server connection.';
      setError(msg);
      throw err;
    }
  };

  const addMessage = (msgObj) => {
    setMessages((prev) => [...prev, msgObj]);
  };

  const resetSession = () => {
    setSessionId(null);
    setCandidate(null);
    setMessages([]);
    setDone(false);
    setFeedback(null);
    setError(null);
  };

  return (
    <InterviewContext.Provider
      value={{
        sessionId,
        candidate,
        messages,
        done,
        feedback,
        loading,
        error,
        startInterview,
        addMessage,
        setMessages,
        setDone,
        setFeedback,
        resetSession,
        setError,
      }}
    >
      {children}
    </InterviewContext.Provider>
  );
}

export function useInterview() {
  const ctx = useContext(InterviewContext);
  if (!ctx) {
    throw new Error('useInterview must be used within an InterviewProvider');
  }
  return ctx;
}
