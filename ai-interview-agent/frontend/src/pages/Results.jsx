import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterview } from '../context/InterviewContext';
import FeedbackCard from '../components/FeedbackCard';
import { fetchInterviewReport } from '../services/api';
import { User, Award, RotateCcw, Sparkles, Download, Loader2, AlertCircle } from 'lucide-react';
import { jsPDF } from 'jspdf';

function generateCleanPDF(report) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 18;
  const contentWidth = pageWidth - margin * 2;
  let y = 20;

  const checkPage = (needed = 12) => {
    if (y + needed > pageHeight - 15) {
      doc.addPage();
      y = 20;
    }
  };

  const drawSectionHeader = (title) => {
    checkPage(16);
    y += 4;
    doc.setDrawColor(99, 102, 241); // indigo-500
    doc.setLineWidth(0.5);
    doc.line(margin, y, margin + contentWidth, y);
    y += 6;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(55, 65, 81); // gray-700
    doc.text(title, margin, y);
    y += 8;
  };

  const wrapText = (text, maxWidth, fontSize = 10) => {
    doc.setFontSize(fontSize);
    return doc.splitTextToSize(text || '', maxWidth);
  };

  const candidateName = report.candidate?.name || 'Candidate';
  const candidateRole = report.candidate?.role || 'AI Engineer';
  const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  // ── Header ──
  doc.setFillColor(248, 250, 252); // slate-50
  doc.rect(0, 0, pageWidth, 36, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(15, 23, 42); // slate-900
  doc.text('AI Technical Interview Report', margin, 16);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139); // slate-500
  doc.text(`${candidateName}  •  ${candidateRole}  •  ${dateStr}`, margin, 24);
  doc.setDrawColor(99, 102, 241);
  doc.setLineWidth(0.8);
  doc.line(margin, 30, margin + contentWidth, 30);
  y = 42;

  const fb = report.feedback || {};

  // ── Overall Score ──
  if (fb.overall_percentage != null) {
    drawSectionHeader('OVERALL PERFORMANCE SCORE');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(24);
    doc.setTextColor(22, 163, 74); // green-600
    doc.text(`${fb.overall_percentage}%`, margin, y + 4);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(107, 114, 128); // gray-500
    doc.text('averaged across all evaluated questions', margin + 26, y + 2);
    y += 14;
  }

  // ── Category Breakdown ──
  if (fb.category_breakdown && Object.keys(fb.category_breakdown).length > 0) {
    drawSectionHeader('CATEGORY BREAKDOWN');
    doc.setFontSize(10);
    for (const [cat, val] of Object.entries(fb.category_breakdown)) {
      checkPage(8);
      const label = cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(55, 65, 81);
      doc.text(label, margin, y);
      doc.setFont('helvetica', 'bold');
      doc.text(`${val}%`, margin + 48, y);
      // Bar bg
      doc.setFillColor(229, 231, 235); // gray-200
      doc.roundedRect(margin + 58, y - 3, 90, 4, 1, 1, 'F');
      // Bar fill
      const barColor = val >= 80 ? [22, 163, 74] : val >= 60 ? [202, 138, 4] : [234, 88, 12];
      doc.setFillColor(...barColor);
      doc.roundedRect(margin + 58, y - 3, Math.max(1, 90 * val / 100), 4, 1, 1, 'F');
      y += 8;
    }
    y += 2;
  }

  // ── Fluency ──
  if (fb.fluency_score != null) {
    drawSectionHeader('COMMUNICATION & WRITING CLARITY');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(109, 40, 217); // violet-700
    doc.text(`Fluency Score: ${fb.fluency_score}/100`, margin, y);
    y += 7;
    if (fb.fluency_notes) {
      doc.setFont('helvetica', 'italic');
      doc.setFontSize(9);
      doc.setTextColor(75, 85, 99); // gray-600
      const lines = wrapText(`"${fb.fluency_notes}"`, contentWidth, 9);
      lines.forEach(line => {
        checkPage(5);
        doc.text(line, margin, y);
        y += 4.5;
      });
    }
    y += 4;
  }

  // ── Transcript ──
  const transcript = report.transcript || [];
  if (transcript.length > 0) {
    drawSectionHeader('INTERVIEW TRANSCRIPT');

    for (const entry of transcript) {
      if (entry.role === 'interviewer') {
        checkPage(12);
        const qLabel = entry.question_number ? `Q${entry.question_number}` : 'Q';
        const topicLabel = entry.topic ? ` [${entry.topic}]` : '';
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(67, 56, 202); // indigo-700
        doc.text(`${qLabel}${topicLabel}`, margin, y);
        y += 5;
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(31, 41, 55); // gray-800
        const qLines = wrapText(entry.content, contentWidth);
        qLines.forEach(line => {
          checkPage(5);
          doc.text(line, margin, y);
          y += 4.5;
        });
        y += 2;
      } else if (entry.role === 'candidate') {
        checkPage(10);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(5, 150, 105); // emerald-600
        doc.text('Answer:', margin + 3, y);
        y += 4.5;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(55, 65, 81);
        const aLines = wrapText(entry.content, contentWidth - 6, 9);
        aLines.forEach(line => {
          checkPage(5);
          doc.text(line, margin + 3, y);
          y += 4.2;
        });

        if (entry.evaluation) {
          checkPage(8);
          y += 1;
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(8);
          doc.setTextColor(107, 114, 128);
          const ev = entry.evaluation;
          const parts = [];
          if (ev.overall_score != null) parts.push(`Score: ${ev.overall_score}/10`);
          if (ev.correctness != null) parts.push(`Corr: ${ev.correctness}`);
          if (ev.technical_depth != null) parts.push(`Depth: ${ev.technical_depth}`);
          if (ev.reasoning != null) parts.push(`Reason: ${ev.reasoning}`);
          if (ev.practicality != null) parts.push(`Pract: ${ev.practicality}`);
          if (ev.communication != null) parts.push(`Comm: ${ev.communication}`);
          doc.text(parts.join('  |  '), margin + 3, y);
          y += 4;
          if (ev.evaluation_summary) {
            const sumLines = wrapText(ev.evaluation_summary, contentWidth - 6, 8);
            sumLines.forEach(line => {
              checkPage(4);
              doc.text(line, margin + 3, y);
              y += 3.8;
            });
          }
        }
        y += 5;
      }
    }
  }

  // ── Executive Summary ──
  if (fb.summary) {
    drawSectionHeader('EXECUTIVE SUMMARY');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(31, 41, 55);
    const lines = wrapText(fb.summary, contentWidth);
    lines.forEach(line => {
      checkPage(5);
      doc.text(line, margin, y);
      y += 5;
    });
    y += 3;
  }

  // ── Strengths ──
  if (fb.strengths?.length) {
    drawSectionHeader('KEY STRENGTHS');
    doc.setFontSize(9);
    fb.strengths.forEach((s, i) => {
      const lines = wrapText(`${i + 1}. ${s}`, contentWidth, 9);
      lines.forEach(line => {
        checkPage(5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(5, 150, 105);
        doc.text(line, margin, y);
        y += 4.5;
      });
      y += 2;
    });
  }

  // ── Gaps ──
  if (fb.gaps?.length) {
    drawSectionHeader('GROWTH AREAS & GAPS');
    doc.setFontSize(9);
    fb.gaps.forEach((g, i) => {
      const lines = wrapText(`${i + 1}. ${g}`, contentWidth, 9);
      lines.forEach(line => {
        checkPage(5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(180, 83, 9); // amber-700
        doc.text(line, margin, y);
        y += 4.5;
      });
      y += 2;
    });
  }

  // ── Next Steps ──
  if (fb.next?.length) {
    drawSectionHeader('ACTIONABLE NEXT STEPS');
    doc.setFontSize(9);
    fb.next.forEach((n, i) => {
      const lines = wrapText(`${i + 1}. ${n}`, contentWidth, 9);
      lines.forEach(line => {
        checkPage(5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(67, 56, 202);
        doc.text(line, margin, y);
        y += 4.5;
      });
      y += 2;
    });
  }

  // ── Footer on every page ──
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(156, 163, 175); // gray-400
    doc.text(
      `AI Technical Interview Report  •  ${candidateName}  •  Page ${i}/${totalPages}`,
      margin, pageHeight - 8,
    );
  }

  const safeName = candidateName.replace(/[^a-zA-Z0-9]/g, '_');
  const safeDate = new Date().toISOString().slice(0, 10);
  doc.save(`InterviewReport_${safeName}_${safeDate}.pdf`);
}

export default function Results() {
  const navigate = useNavigate();
  const { feedback, candidate, sessionId, resetSession } = useInterview();

  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState(null);

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

  const handleDownloadReport = async () => {
    if (reportLoading) return;
    setReportLoading(true);
    setReportError(null);

    try {
      const report = await fetchInterviewReport(sessionId);
      generateCleanPDF(report);
    } catch (err) {
      setReportError(err.message || 'Failed to generate report. Please try again.');
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 sm:p-6 md:p-8 relative overflow-hidden font-sans">
      {/* Ambient Decorative Gradients */}
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/3 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-slate-800/80 mb-6 md:mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shadow-lg shadow-indigo-600/20">
            <Award className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-display tracking-tight text-white">
              Evaluation Results
            </h1>
            <p className="text-xs text-slate-400 font-medium">AI Cohort Technical Review</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-bold px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            Completed
          </span>
        </div>
      </header>

      {/* Main Results Body */}
      <main className="max-w-4xl w-full mx-auto my-auto space-y-6 md:space-y-8">
        {/* Candidate Profile Summary Header */}
        <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-md">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-display text-white">{member.name || 'Cohort Candidate'}</h2>
              <p className="text-sm text-indigo-300 font-semibold">{member.jobRole || 'AI Engineer'}</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
            {/* Download Report Button */}
            <button
              id="download-report-btn"
              onClick={handleDownloadReport}
              disabled={reportLoading}
              className={`w-full sm:w-auto px-5 py-3 rounded-xl text-sm font-bold shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer ${
                reportLoading
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30 active:scale-95'
              }`}
            >
              {reportLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Download Report
                </>
              )}
            </button>

            <button
              onClick={handleStartNew}
              className="w-full sm:w-auto px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-sm shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              Start New Interview
            </button>
          </div>
        </div>

        {/* Report Error Message */}
        {reportError && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start gap-3 animate-bubble-enter">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-rose-300 font-bold">{reportError}</p>
              <button
                onClick={handleDownloadReport}
                className="mt-2 text-xs text-rose-400 underline hover:text-rose-300 transition-colors font-semibold cursor-pointer"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Feedback Card Display */}
        <FeedbackCard feedback={feedback} />
      </main>

      {/* Footer */}
      <footer className="max-w-6xl w-full mx-auto text-center text-xs text-slate-400 pt-8 border-t border-slate-900 mt-8 font-medium">
        AI Technical Evaluation Agent &bull; Final Assessment Report
      </footer>
    </div>
  );
}
