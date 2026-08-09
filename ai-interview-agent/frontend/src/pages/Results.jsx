import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInterview } from '../context/InterviewContext';
import FeedbackCard from '../components/FeedbackCard';
import ThemeToggle from '../components/ThemeToggle';
import { fetchInterviewReport } from '../services/api';
import { User, Award, RotateCcw, Sparkles, Download, Loader2, AlertCircle } from 'lucide-react';
import { jsPDF } from 'jspdf';

function generateCleanPDF(report) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  const contentWidth = pageWidth - margin * 2;
  let y = 48;

  const checkPage = (needed = 15) => {
    if (y + needed > pageHeight - 16) {
      doc.addPage();
      y = 20;
    }
  };

  const wrapText = (text, maxWidth, fontSize = 9.5) => {
    doc.setFontSize(fontSize);
    return doc.splitTextToSize(text || '', maxWidth);
  };

  const candidateName = report.candidate?.name || 'Candidate';
  const candidateRole = report.candidate?.role || 'AI Engineer';
  const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  const fb = report.feedback || {};

  // ── Header Banner ──
  // Top brand bar
  doc.setFillColor(79, 70, 229); // indigo-600
  doc.rect(0, 0, pageWidth, 3.5, 'F');

  // Dark header block
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(0, 3.5, pageWidth, 38, 'F');

  // Title
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(255, 255, 255);
  doc.text('AI TECHNICAL INTERVIEW EVALUATION REPORT', margin, 17);

  // Candidate Subtitle
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9.5);
  doc.setTextColor(148, 163, 184); // slate-400
  doc.text(`${candidateName}   |   ${candidateRole}   |   ${dateStr}`, margin, 25);

  // Header Divider Line
  doc.setDrawColor(51, 65, 85); // slate-700
  doc.setLineWidth(0.4);
  doc.line(margin, 32, margin + contentWidth - 42, 32);

  // Header Subtext
  doc.setFontSize(8);
  doc.setTextColor(129, 140, 248); // indigo-400
  doc.text('ABTalks AI Engineering Cohort  •  Adaptive Evaluation Agent', margin, 37);

  // Overall Score Badge (Top Right of Banner)
  if (fb.overall_percentage != null) {
    const scoreVal = fb.overall_percentage;
    const badgeColor =
      scoreVal >= 80 ? [16, 185, 129] : // emerald-500
      scoreVal >= 60 ? [245, 158, 11] : // amber-500
      [239, 68, 68]; // rose-500

    const badgeX = pageWidth - margin - 36;
    doc.setFillColor(...badgeColor);
    doc.roundedRect(badgeX, 9, 36, 27, 3, 3, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(16);
    doc.setTextColor(255, 255, 255);
    doc.text(`${scoreVal}%`, badgeX + 18, 22, { align: 'center' });

    doc.setFontSize(7);
    doc.text('OVERALL', badgeX + 18, 29, { align: 'center' });
  }

  y = 48;

  // ── Technical Performance Score & Category Breakdown ──
  if (fb.category_breakdown && Object.keys(fb.category_breakdown).length > 0) {
    checkPage(48);

    // Section title
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59); // slate-800
    doc.text('TECHNICAL PERFORMANCE BREAKDOWN', margin, y);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139); // slate-500
    doc.text('Averaged across all evaluated question criteria', margin + 85, y);
    y += 5;

    const entries = Object.entries(fb.category_breakdown);
    const cardHeight = entries.length * 8.5 + 8;

    doc.setFillColor(248, 250, 252); // slate-50
    doc.setDrawColor(226, 232, 240); // slate-200
    doc.setLineWidth(0.4);
    doc.roundedRect(margin, y, contentWidth, cardHeight, 2, 2, 'FD');

    let barY = y + 7;
    for (const [cat, val] of entries) {
      const label = cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const scorePct = Math.min(100, Math.max(0, Number(val) || 0));

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.setTextColor(51, 65, 85); // slate-700
      doc.text(label, margin + 5, barY + 1);

      doc.setFontSize(9);
      doc.setTextColor(30, 41, 59);
      doc.text(`${scorePct}%`, margin + 62, barY + 1);

      // Progress bar track
      const barX = margin + 74;
      const barWidth = 96;
      doc.setFillColor(226, 232, 240);
      doc.roundedRect(barX, barY - 2.5, barWidth, 4.5, 1.5, 1.5, 'F');

      // Progress bar fill
      const barFillColor =
        scorePct >= 80 ? [16, 185, 129] :
        scorePct >= 60 ? [245, 158, 11] :
        [239, 68, 68];

      doc.setFillColor(...barFillColor);
      doc.roundedRect(barX, barY - 2.5, Math.max(2, (barWidth * scorePct) / 100), 4.5, 1.5, 1.5, 'F');

      barY += 8.5;
    }
    y += cardHeight + 8;
  }

  // ── Communication & Writing Clarity (Fluency) ──
  if (fb.fluency_score != null) {
    checkPage(30);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(109, 40, 217); // violet-700
    doc.text('COMMUNICATION & WRITING CLARITY', margin, y);
    y += 5;

    const notesLines = wrapText(fb.fluency_notes ? `"${fb.fluency_notes}"` : '', contentWidth - 36, 8.5);
    const cardH = Math.max(18, notesLines.length * 4.2 + 8);

    doc.setFillColor(245, 243, 255); // violet-50
    doc.setDrawColor(221, 214, 254); // violet-200
    doc.setLineWidth(0.4);
    doc.roundedRect(margin, y, contentWidth, cardH, 2, 2, 'FD');

    // Fluency Score Badge
    const fScore = fb.fluency_score;
    const fColor =
      fScore >= 80 ? [16, 185, 129] :
      fScore >= 60 ? [245, 158, 11] :
      [239, 68, 68];

    doc.setFillColor(...fColor);
    doc.roundedRect(margin + 4, y + 4, 24, 11, 2, 2, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.text(`${fScore}/100`, margin + 16, y + 11, { align: 'center' });

    // Notes
    if (fb.fluency_notes) {
      doc.setFont('helvetica', 'italic');
      doc.setFontSize(8.5);
      doc.setTextColor(71, 85, 105); // slate-600
      let lineY = y + 7;
      notesLines.forEach(line => {
        doc.text(line, margin + 32, lineY);
        lineY += 4.2;
      });
    }

    y += cardH + 8;
  }

  // ── Executive Summary ──
  if (fb.summary) {
    const sumLines = wrapText(fb.summary, contentWidth - 8, 9.5);
    const cardH = sumLines.length * 4.8 + 12;

    checkPage(cardH + 10);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59);
    doc.text('EXECUTIVE EVALUATION SUMMARY', margin, y);
    y += 5;

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.4);
    doc.roundedRect(margin, y, contentWidth, cardH, 2, 2, 'FD');

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9.5);
    doc.setTextColor(51, 65, 85);
    let sY = y + 7;
    sumLines.forEach(line => {
      doc.text(line, margin + 4, sY);
      sY += 4.8;
    });

    y += cardH + 8;
  }

  // ── Key Strengths, Growth Areas, Actionable Next Steps ──
  const drawListSection = (title, items, headerColor, boxFill, boxBorder, bulletColor) => {
    if (!items || items.length === 0) return;

    checkPage(24);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...headerColor);
    doc.text(title, margin, y);
    y += 5;

    // Calculate height
    let totalItemLines = 0;
    const formattedItems = items.map(item => {
      const lines = wrapText(item, contentWidth - 12, 9);
      totalItemLines += lines.length;
      return lines;
    });

    const cardH = totalItemLines * 4.5 + items.length * 3 + 6;

    checkPage(cardH + 4);

    doc.setFillColor(...boxFill);
    doc.setDrawColor(...boxBorder);
    doc.setLineWidth(0.4);
    doc.roundedRect(margin, y, contentWidth, cardH, 2, 2, 'FD');

    let itemY = y + 6;
    formattedItems.forEach(lines => {
      // Bullet dot
      doc.setFillColor(...bulletColor);
      doc.circle(margin + 5, itemY - 1.2, 1.2, 'F');

      lines.forEach(line => {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(30, 41, 59);
        doc.text(line, margin + 9, itemY);
        itemY += 4.5;
      });
      itemY += 2;
    });

    y += cardH + 8;
  };

  drawListSection(
    'KEY STRENGTHS',
    fb.strengths,
    [4, 120, 87], // emerald-700
    [236, 253, 245], // emerald-50
    [167, 243, 208], // emerald-200
    [16, 185, 129] // emerald-500
  );

  drawListSection(
    'GROWTH AREAS & GAPS',
    fb.gaps,
    [180, 83, 9], // amber-700
    [255, 251, 235], // amber-50
    [253, 230, 138], // amber-200
    [245, 158, 11] // amber-500
  );

  drawListSection(
    'ACTIONABLE NEXT STEPS',
    fb.next,
    [67, 56, 202], // indigo-700
    [238, 242, 255], // indigo-50
    [199, 210, 254], // indigo-200
    [79, 70, 229] // indigo-600
  );

  // ── Detailed Question Evaluations & Transcript ──
  const transcript = report.transcript || [];
  if (transcript.length > 0) {
    checkPage(20);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59);
    doc.text('DETAILED QUESTION EVALUATIONS & TRANSCRIPT', margin, y);
    y += 7;

    // Group transcript into Q&A pairs (deduplicated by question_number)
    const qaPairs = [];
    let currentPair = null;

    for (const entry of transcript) {
      if (entry.role === 'interviewer') {
        if (currentPair) {
          qaPairs.push(currentPair);
        }
        currentPair = {
          qnum: entry.question_number,
          topic: entry.topic,
          question: entry.content,
          answer: null,
          evaluation: null,
        };
      } else if (entry.role === 'candidate' && currentPair) {
        currentPair.answer = entry.content;
        currentPair.evaluation = entry.evaluation || null;
      }
    }
    if (currentPair) {
      qaPairs.push(currentPair);
    }

    // Render each Q&A Pair cleanly
    qaPairs.forEach(pair => {
      const qNumStr = pair.qnum ? `Q${pair.qnum}` : 'Question';
      const topicStr = pair.topic ? `  [Day Topic: ${pair.topic}]` : '';

      const qLines = wrapText(pair.question || '', contentWidth - 10, 9);
      const aLines = pair.answer ? wrapText(pair.answer, contentWidth - 10, 9) : [];
      const ev = pair.evaluation || {};
      const sumLines = ev.evaluation_summary ? wrapText(ev.evaluation_summary, contentWidth - 10, 8.5) : [];

      // Calculate total block height
      const qBoxH = qLines.length * 4.3 + 9;
      const aBoxH = aLines.length > 0 ? aLines.length * 4.2 + 9 : 0;
      const evBoxH = ev.overall_score != null ? (sumLines.length * 4.0 + 14) : 0;
      const totalCardH = qBoxH + aBoxH + evBoxH + 4;

      checkPage(totalCardH + 6);

      // Question Box Container
      doc.setFillColor(241, 245, 249); // slate-100
      doc.setDrawColor(226, 232, 240); // slate-200
      doc.setLineWidth(0.4);
      doc.roundedRect(margin, y, contentWidth, qBoxH, 2, 2, 'FD');

      // Left Accent Strip on Question Box
      doc.setFillColor(79, 70, 229); // indigo-600
      doc.rect(margin, y, 1.8, qBoxH, 'F');

      // Question Header
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9.5);
      doc.setTextColor(67, 56, 202); // indigo-700
      doc.text(`${qNumStr}${topicStr}`, margin + 5, y + 6);

      // Question Text
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(30, 41, 59);
      let qY = y + 11;
      qLines.forEach(line => {
        doc.text(line, margin + 5, qY);
        qY += 4.3;
      });

      y += qBoxH + 2;

      // Candidate Answer Box
      if (aLines.length > 0) {
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(226, 232, 240);
        doc.setLineWidth(0.3);
        doc.roundedRect(margin, y, contentWidth, aBoxH, 2, 2, 'FD');

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8.5);
        doc.setTextColor(5, 150, 105); // emerald-600
        doc.text('Candidate Answer:', margin + 5, y + 5.5);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(51, 65, 85);
        let aY = y + 10;
        aLines.forEach(line => {
          doc.text(line, margin + 5, aY);
          aY += 4.2;
        });

        y += aBoxH + 2;
      }

      // Per-Question Evaluation & Sub-Scores Box
      if (ev.overall_score != null) {
        doc.setFillColor(248, 250, 252);
        doc.setDrawColor(226, 232, 240);
        doc.setLineWidth(0.3);
        doc.roundedRect(margin, y, contentWidth, evBoxH, 2, 2, 'FD');

        // Score Badge Box
        const qScore = Number(ev.overall_score) || 0;
        const qBadgeColor =
          qScore >= 8.0 ? [16, 185, 129] :
          qScore >= 6.0 ? [245, 158, 11] :
          [239, 68, 68];

        doc.setFillColor(...qBadgeColor);
        doc.roundedRect(margin + 4, y + 3, 24, 6.5, 1.5, 1.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(255, 255, 255);
        doc.text(`Score: ${qScore}/10`, margin + 16, y + 7.5, { align: 'center' });

        // Sub-scores horizontal pills
        const subParts = [];
        if (ev.correctness != null) subParts.push(`Corr: ${ev.correctness}`);
        if (ev.technical_depth != null) subParts.push(`Depth: ${ev.technical_depth}`);
        if (ev.reasoning != null) subParts.push(`Reason: ${ev.reasoning}`);
        if (ev.practicality != null) subParts.push(`Pract: ${ev.practicality}`);
        if (ev.communication != null) subParts.push(`Comm: ${ev.communication}`);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(71, 85, 105);
        doc.text(subParts.join('   |   '), margin + 32, y + 7.5);

        // Evaluation Summary
        if (ev.evaluation_summary) {
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(8.5);
          doc.setTextColor(51, 65, 85);
          let sumY = y + 13;
          sumLines.forEach(line => {
            doc.text(line, margin + 5, sumY);
            sumY += 4.0;
          });
        }

        y += evBoxH + 4;
      } else {
        y += 2;
      }
    });
  }

  // ── Footer on Every Page ──
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.3);
    doc.line(margin, pageHeight - 12, margin + contentWidth, pageHeight - 12);

    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(148, 163, 184); // slate-400
    doc.text(
      `AI Technical Evaluation Agent  •  ${candidateName} (${candidateRole})`,
      margin, pageHeight - 6.5
    );

    doc.setFont('helvetica', 'bold');
    doc.text(
      `Page ${i} of ${totalPages}`,
      margin + contentWidth, pageHeight - 6.5,
      { align: 'right' }
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
    <div className="min-h-screen flex flex-col justify-between p-4 sm:p-6 md:p-8 relative overflow-hidden font-sans" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}>
      {/* Ambient Decorative Gradients */}
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none" style={{ backgroundColor: 'var(--color-glow)' }} />
      <div className="absolute bottom-0 right-1/3 w-[500px] h-[500px] rounded-full blur-3xl pointer-events-none" style={{ backgroundColor: 'var(--color-glow-alt)' }} />

      {/* Header */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 mb-6 md:mb-8" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', boxShadow: `0 4px 12px var(--color-accent-shadow)` }}>
            <Award className="w-5 h-5" style={{ color: 'var(--color-accent-text)' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-display tracking-tight" style={{ color: 'var(--color-text-heading)' }}>
              Evaluation Results
            </h1>
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>AI Cohort Technical Review</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <span className="text-xs font-bold px-3.5 py-1.5 rounded-full flex items-center gap-1.5 uppercase tracking-wider" style={{ background: 'var(--color-success-bg)', border: '1px solid var(--color-success-border)', color: 'var(--color-success)' }}>
            <Sparkles className="w-3.5 h-3.5" />
            Completed
          </span>
        </div>
      </header>

      {/* Main Results Body */}
      <main className="max-w-4xl w-full mx-auto my-auto space-y-6 md:space-y-8">
        {/* Candidate Profile Summary Header */}
        <div className="rounded-2xl p-6 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-md" style={{ background: 'var(--color-accent-bg)', border: '1px solid var(--color-accent-border)', color: 'var(--color-accent-text)' }}>
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-display" style={{ color: 'var(--color-text-heading)' }}>{member.name || 'Cohort Candidate'}</h2>
              <p className="text-sm font-semibold" style={{ color: 'var(--color-accent-text)' }}>{member.jobRole || 'AI Engineer'}</p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
            {/* Download Report Button */}
            <button
              id="download-report-btn"
              onClick={handleDownloadReport}
              disabled={reportLoading}
              className="w-full sm:w-auto px-5 py-3 rounded-xl text-sm font-bold shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: reportLoading ? 'var(--color-surface-alt)' : 'var(--color-accent-btn)',
                color: reportLoading ? 'var(--color-text-secondary)' : '#ffffff',
                border: reportLoading ? '1px solid var(--color-border)' : 'none',
                boxShadow: reportLoading ? 'none' : '0 4px 16px var(--color-accent-shadow)',
              }}
            >
              {reportLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
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
              className="w-full sm:w-auto px-5 py-3 rounded-xl font-bold text-sm shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
              style={{ background: 'var(--color-surface-alt)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
            >
              <RotateCcw className="w-4 h-4" />
              Start New Interview
            </button>
          </div>
        </div>

        {/* Report Error Message */}
        {reportError && (
          <div className="rounded-xl p-4 flex items-start gap-3 animate-bubble-enter" style={{ background: 'var(--color-error-bg)', border: '1px solid var(--color-error-border)' }}>
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--color-error)' }} />
            <div className="flex-1">
              <p className="text-sm font-bold" style={{ color: 'var(--color-error-text)' }}>{reportError}</p>
              <button
                onClick={handleDownloadReport}
                className="mt-2 text-xs underline transition-colors font-semibold cursor-pointer"
                style={{ color: 'var(--color-error)' }}
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
      <footer className="max-w-6xl w-full mx-auto text-center text-xs pt-8 mt-8 font-medium" style={{ color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border-light)' }}>
        AI Technical Evaluation Agent &bull; Final Assessment Report
      </footer>
    </div>
  );
}
