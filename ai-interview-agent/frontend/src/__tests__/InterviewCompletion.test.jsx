import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Interview from '../pages/Interview';
import { InterviewProvider, useInterview } from '../context/InterviewContext';
import * as api from '../services/api';

vi.spyOn(api, 'postInterviewTurn');

const mockFeedback = {
  closing_message: "Thank you so much for your time, Sarah! That concludes our technical interview.",
  summary: "Great overall performance across FastAPI and system design topics.",
  strengths: ["Chunk overlap explanation in RAG"],
  gaps: ["HNSW vector indexing trade-offs"],
  next: ["Practice FAISS vector store indexing"]
};

function TestApp() {
  const { setSessionId, setCandidate } = useInterview();

  React.useEffect(() => {
    setSessionId('test-session-123');
    setCandidate({
      id: 'CAND-001',
      member: { name: 'Sarah', track: 'AI Engineering' }
    });
  }, [setSessionId, setCandidate]);

  return (
    <Routes>
      <Route path="/" element={<Interview />} />
      <Route path="/results" element={<ResultsPage />} />
    </Routes>
  );
}

function ResultsPage() {
  const { feedback } = useInterview();
  return (
    <div data-testid="results-page">
      <h1>Results Page</h1>
      <p data-testid="results-summary">{feedback?.summary}</p>
      <p data-testid="results-closing">{feedback?.closing_message}</p>
    </div>
  );
}

describe('Interview Completion Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders CompletionModal in the DOM when done:true is returned BEFORE navigation, and navigates to /results on button click', async () => {
    api.postInterviewTurn.mockResolvedValueOnce({
      reply: mockFeedback.closing_message,
      done: true,
      feedback: mockFeedback
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <InterviewProvider>
          <TestApp />
        </InterviewProvider>
      </MemoryRouter>
    );

    // 1. Submit an answer
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'Here is my final answer.' } });

    const submitBtn = screen.getByRole('button', { name: /submit answer/i });
    fireEvent.click(submitBtn);

    // 2. Verify modal is present in DOM before navigation occurs
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    expect(screen.getByText(/Interview Complete/i)).toBeInTheDocument();
    expect(screen.getByText(/Great job, Sarah!/i)).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(mockFeedback.closing_message, 'i')).length).toBeGreaterThanOrEqual(2);

    // Confirm results page is NOT rendered yet
    expect(screen.queryByTestId('results-page')).not.toBeInTheDocument();

    // 3. Click "View My Results" button
    const viewResultsBtn = screen.getByRole('button', { name: /View My Results/i });
    fireEvent.click(viewResultsBtn);

    // 4. Confirm navigation to /results and feedback available
    await waitFor(() => {
      expect(screen.getByTestId('results-page')).toBeInTheDocument();
    });

    expect(screen.getByTestId('results-summary')).toHaveTextContent(mockFeedback.summary);
    expect(screen.getByTestId('results-closing')).toHaveTextContent(mockFeedback.closing_message);
  });
});
