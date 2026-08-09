import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { InterviewProvider } from './context/InterviewContext';
import Home from './pages/Home';
import Interview from './pages/Interview';
import Results from './pages/Results';

export default function App() {
  return (
    <ThemeProvider>
      <InterviewProvider>
        <Router>
          <div className="min-h-screen font-sans" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/interview" element={<Interview />} />
              <Route path="/results" element={<Results />} />
            </Routes>
          </div>
        </Router>
      </InterviewProvider>
    </ThemeProvider>
  );
}
