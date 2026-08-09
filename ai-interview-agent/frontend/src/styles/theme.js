/**
 * Application Design System & Theme Tokens
 *
 * Establishes a cohesive dark, professional aesthetic:
 * - Primary Background: Deep Slate/Navy (#030712 / #0f172a)
 * - Primary Accent: Indigo / Violet family for buttons, focus rings, progress bars
 * - Functional Accents: Emerald (success/completion), Amber (warning/gaps), Rose (error), Violet (fluency)
 * - Typography: Plus Jakarta Sans (body) & Outfit (headings)
 */

export const theme = {
  fonts: {
    sans: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
    display: "'Outfit', 'Plus Jakarta Sans', system-ui, sans-serif",
  },
  colors: {
    bg: {
      page: 'bg-slate-950',
      card: 'bg-slate-900/80',
      cardBorder: 'border-slate-800/80',
      cardInner: 'bg-slate-950/60',
      input: 'bg-slate-900/90',
    },
    accent: {
      primary: 'indigo',
      gradient: 'from-indigo-600 to-indigo-700',
      gradientHover: 'hover:from-indigo-500 hover:to-indigo-600',
      button: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25',
      badge: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300',
      text: 'text-indigo-400',
      ring: 'focus:ring-indigo-500/30 focus:border-indigo-500/80',
    },
    status: {
      success: {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        text: 'text-emerald-400',
      },
      warning: {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        text: 'text-amber-400',
      },
      error: {
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/30',
        text: 'text-rose-400',
      },
      fluency: {
        bg: 'bg-violet-500/10',
        border: 'border-violet-500/30',
        text: 'text-violet-400',
      },
    },
  },
  radii: {
    card: 'rounded-2xl',
    innerCard: 'rounded-xl',
    button: 'rounded-xl',
    badge: 'rounded-full',
  },
  animationDuration: '200ms',
};

export default theme;
