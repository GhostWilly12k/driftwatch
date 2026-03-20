/* ═══════════════════════════════════════
   COGNITIONTRADE — SHARED JS
   app.js — loaded on every page
═══════════════════════════════════════ */

/* ── THEME ── */
const CT = {

  // ── Init (call on every page load)
  init() {
    const saved = localStorage.getItem('ct-theme') || 'dark';
    CT.setTheme(saved, false);
    CT.auth.checkRedirect();
  },

  setTheme(t, save = true) {
    document.documentElement.setAttribute('data-theme', t);
    if (save) localStorage.setItem('ct-theme', t);
    // Sync all theme option buttons if present
    document.querySelectorAll('[data-theme-opt]').forEach(el => {
      el.classList.toggle('selected', el.dataset.themeOpt === t);
    });
    // Refresh charts if any exist
    if (window.CT_Charts) CT_Charts.refreshAll();
  },

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    CT.setTheme(current === 'dark' ? 'light' : 'dark');
  },

  // ── AUTH (mock — replace with real JWT/Supabase calls)
  auth: {
    SESSION_KEY: 'ct-session',

    isLoggedIn() {
      return !!localStorage.getItem(CT.auth.SESSION_KEY);
    },

    login(email, password) {
      // TODO: replace with real API call
      // POST /api/auth/login  →  { token, user }
      if (email && password) {
        const fakeSession = { email, name: 'Jordan Dex', plan: 'Pro', avatar: 'JD' };
        localStorage.setItem(CT.auth.SESSION_KEY, JSON.stringify(fakeSession));
        return true;
      }
      return false;
    },

    logout() {
      localStorage.removeItem(CT.auth.SESSION_KEY);
      window.location.href = 'login.html';
    },

    getUser() {
      const s = localStorage.getItem(CT.auth.SESSION_KEY);
      return s ? JSON.parse(s) : null;
    },

    // Redirect if not logged in (call on protected pages)
    requireAuth() {
      if (!CT.auth.isLoggedIn()) {
        window.location.href = 'login.html';
      }
    },

    // Redirect logged-in users away from login/landing
    checkRedirect() {
      const publicPages = ['index.html', 'login.html', ''];
      const page = window.location.pathname.split('/').pop();
      // If already logged in and on a public page, redirect to dashboard
      if (CT.auth.isLoggedIn() && publicPages.includes(page)) {
        // Uncomment to auto-redirect:
        // window.location.href = 'dashboard.html';
      }
    },
  },

  // ── NAV helpers
  nav: {
    setActive(viewId) {
      document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.view === viewId);
      });
      const titleMap = {
        dashboard: 'Dashboard',
        journal: 'Log a Trade',
        trades: 'Trade History',
        performance: 'My Performance',
        strategy: 'Execution Review',
        researcher: 'Market Briefing',
        chat: 'Ask My AI Coach',
        settings: 'Settings',
      };
      const el = document.getElementById('page-title');
      if (el) el.textContent = titleMap[viewId] || viewId;
    },
  },

  // ── User display helpers
  ui: {
    populateUser() {
      const user = CT.auth.getUser();
      if (!user) return;
      document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = user.name);
      document.querySelectorAll('[data-user-email]').forEach(el => el.textContent = user.email);
      document.querySelectorAll('[data-user-plan]').forEach(el => el.textContent = `${user.plan} · 342 trades`);
      document.querySelectorAll('[data-user-avatar]').forEach(el => el.textContent = user.avatar || 'JD');
    },
  },
};

// ── Run on every page
document.addEventListener('DOMContentLoaded', () => {
  CT.init();
  CT.ui.populateUser();

  // Wire theme toggles
  document.querySelectorAll('[data-action="toggle-theme"]').forEach(el => {
    el.addEventListener('click', CT.toggleTheme);
  });

  // Wire logout buttons
  document.querySelectorAll('[data-action="logout"]').forEach(el => {
    el.addEventListener('click', CT.auth.logout);
  });

  // Wire emotion chips
  document.querySelectorAll('.emotion-chip').forEach(c => {
    c.addEventListener('click', () => c.classList.toggle('sel'));
  });

  // Wire color swatches
  document.querySelectorAll('.color-swatch').forEach(s => {
    s.addEventListener('click', function () {
      document.querySelectorAll('.color-swatch').forEach(x => x.classList.remove('selected'));
      this.classList.add('selected');
    });
  });
});


/* ═══════════════════════════════════════
   MOCK TRADE DATA  (replace with API)
═══════════════════════════════════════ */
const TRADES_BY_DATE = {
  '2026-03-02': [
    { time:'09:31', stock:'SPY',  dir:'Long',  strategy:'Open Breakout', entry:'518.20', exit:'521.40', outcome:'+1.6R', mae:'0.3R', mfe:'1.9R', mindset:'Focused' },
    { time:'10:45', stock:'AAPL', dir:'Long',  strategy:'Bull Flag',     entry:'194.10', exit:'195.80', outcome:'+0.9R', mae:'0.2R', mfe:'1.2R', mindset:'Focused' },
  ],
  '2026-03-03': [
    { time:'09:45', stock:'NVDA', dir:'Short', strategy:'VWAP Fade',     entry:'888.00', exit:'882.50', outcome:'+2.2R', mae:'0.4R', mfe:'2.6R', mindset:'In the Zone' },
    { time:'11:10', stock:'TSLA', dir:'Long',  strategy:'Bull Flag',     entry:'246.00', exit:'243.20', outcome:'-1.0R', mae:'1.4R', mfe:'0.3R', mindset:'Impulsive' },
    { time:'13:30', stock:'QQQ',  dir:'Long',  strategy:'Trend Follow',  entry:'442.00', exit:'444.80', outcome:'+1.4R', mae:'0.3R', mfe:'1.7R', mindset:'Focused' },
  ],
  '2026-03-04': [
    { time:'10:00', stock:'META', dir:'Long',  strategy:'Trend Follow',  entry:'590.00', exit:'586.50', outcome:'-0.7R', mae:'1.1R', mfe:'0.5R', mindset:'Hesitant' },
    { time:'14:00', stock:'MSFT', dir:'Short', strategy:'VWAP Fade',     entry:'415.30', exit:'413.00', outcome:'+0.8R', mae:'0.4R', mfe:'1.0R', mindset:'Focused' },
  ],
  '2026-03-05': [
    { time:'09:32', stock:'AAPL', dir:'Long',  strategy:'Open Breakout', entry:'195.00', exit:'199.20', outcome:'+2.8R', mae:'0.2R', mfe:'3.1R', mindset:'In the Zone' },
    { time:'10:20', stock:'SPY',  dir:'Long',  strategy:'Bull Flag',     entry:'520.10', exit:'523.80', outcome:'+2.1R', mae:'0.3R', mfe:'2.4R', mindset:'Focused' },
    { time:'13:00', stock:'NVDA', dir:'Long',  strategy:'Trend Follow',  entry:'885.00', exit:'892.00', outcome:'+1.8R', mae:'0.4R', mfe:'2.0R', mindset:'Confident' },
  ],
  '2026-03-06': [
    { time:'10:15', stock:'TSLA', dir:'Short', strategy:'VWAP Fade',     entry:'250.00', exit:'252.80', outcome:'-1.4R', mae:'1.8R', mfe:'0.2R', mindset:'Revenge' },
    { time:'11:30', stock:'QQQ',  dir:'Short', strategy:'VWAP Fade',     entry:'445.00', exit:'441.50', outcome:'+1.9R', mae:'0.5R', mfe:'2.2R', mindset:'Focused' },
  ],
  '2026-03-09': [
    { time:'09:35', stock:'SPY',  dir:'Long',  strategy:'Open Breakout', entry:'521.00', exit:'524.60', outcome:'+2.0R', mae:'0.2R', mfe:'2.4R', mindset:'Focused' },
  ],
  '2026-03-10': [
    { time:'09:45', stock:'AAPL', dir:'Long',  strategy:'Bull Flag',     entry:'196.50', exit:'194.20', outcome:'-1.2R', mae:'1.5R', mfe:'0.3R', mindset:'Impulsive' },
    { time:'11:00', stock:'META', dir:'Long',  strategy:'Trend Follow',  entry:'593.00', exit:'598.40', outcome:'+1.5R', mae:'0.4R', mfe:'1.8R', mindset:'Focused' },
  ],
  '2026-03-11': [
    { time:'10:30', stock:'NVDA', dir:'Short', strategy:'VWAP Fade',     entry:'892.00', exit:'885.00', outcome:'+2.4R', mae:'0.3R', mfe:'2.7R', mindset:'In the Zone' },
    { time:'13:15', stock:'MSFT', dir:'Long',  strategy:'Bull Flag',     entry:'416.00', exit:'419.80', outcome:'+1.3R', mae:'0.4R', mfe:'1.6R', mindset:'Focused' },
    { time:'14:30', stock:'TSLA', dir:'Long',  strategy:'Open Breakout', entry:'248.00', exit:'252.40', outcome:'+1.8R', mae:'0.3R', mfe:'2.1R', mindset:'Confident' },
  ],
  '2026-03-12': [
    { time:'09:32', stock:'QQQ',  dir:'Short', strategy:'VWAP Fade',     entry:'447.00', exit:'450.60', outcome:'-1.8R', mae:'2.0R', mfe:'0.4R', mindset:'Revenge' },
    { time:'10:50', stock:'SPY',  dir:'Long',  strategy:'Bull Flag',     entry:'522.00', exit:'520.10', outcome:'-0.9R', mae:'1.2R', mfe:'0.3R', mindset:'Hesitant' },
  ],
  '2026-03-13': [
    { time:'09:40', stock:'AAPL', dir:'Long',  strategy:'Open Breakout', entry:'197.00', exit:'201.40', outcome:'+3.2R', mae:'0.2R', mfe:'3.5R', mindset:'In the Zone' },
    { time:'11:20', stock:'NVDA', dir:'Long',  strategy:'Bull Flag',     entry:'887.00', exit:'895.00', outcome:'+2.5R', mae:'0.3R', mfe:'2.8R', mindset:'Focused' },
  ],
  '2026-03-16': [
    { time:'09:50', stock:'META', dir:'Short', strategy:'VWAP Fade',     entry:'596.00', exit:'591.20', outcome:'+1.7R', mae:'0.4R', mfe:'2.0R', mindset:'Focused' },
  ],
  '2026-03-17': [
    { time:'10:00', stock:'TSLA', dir:'Long',  strategy:'Trend Follow',  entry:'249.00', exit:'247.10', outcome:'-0.8R', mae:'1.1R', mfe:'0.6R', mindset:'Hesitant' },
    { time:'11:45', stock:'QQQ',  dir:'Long',  strategy:'Bull Flag',     entry:'448.00', exit:'451.80', outcome:'+2.0R', mae:'0.3R', mfe:'2.3R', mindset:'Focused' },
    { time:'13:30', stock:'SPY',  dir:'Long',  strategy:'Open Breakout', entry:'523.50', exit:'525.80', outcome:'+1.1R', mae:'0.2R', mfe:'1.4R', mindset:'Confident' },
  ],
  '2026-03-18': [
    { time:'09:35', stock:'AAPL', dir:'Short', strategy:'VWAP Fade',     entry:'198.00', exit:'200.20', outcome:'-1.1R', mae:'1.4R', mfe:'0.3R', mindset:'Impulsive' },
    { time:'14:00', stock:'MSFT', dir:'Long',  strategy:'Trend Follow',  entry:'418.00', exit:'420.90', outcome:'+1.0R', mae:'0.5R', mfe:'1.3R', mindset:'Focused' },
  ],
  '2026-03-19': [
    { time:'09:45', stock:'TSLA', dir:'Long',  strategy:'Bull Flag',     entry:'248.10', exit:'244.30', outcome:'-0.8R', mae:'1.1R', mfe:'0.6R', mindset:'Revenge' },
    { time:'11:00', stock:'META', dir:'Long',  strategy:'Trend Follow',  entry:'592.40', exit:'596.00', outcome:'+1.1R', mae:'0.3R', mfe:'1.9R', mindset:'Hesitant' },
    { time:'13:00', stock:'QQQ',  dir:'Short', strategy:'VWAP Fade',     entry:'444.20', exit:'440.50', outcome:'+2.1R', mae:'0.5R', mfe:'2.4R', mindset:'In the Zone' },
  ],
  '2026-03-20': [
    { time:'09:32', stock:'AAPL', dir:'Long',  strategy:'Bull Flag',     entry:'195.40', exit:'198.28', outcome:'+1.8R', mae:'0.4R', mfe:'2.1R', mindset:'Focused' },
    { time:'09:47', stock:'NVDA', dir:'Short', strategy:'VWAP Fade',     entry:'891.20', exit:'897.80', outcome:'-1.2R', mae:'1.8R', mfe:'0.3R', mindset:'Impulsive' },
    { time:'10:15', stock:'SPY',  dir:'Long',  strategy:'Open Breakout', entry:'519.80', exit:'524.60', outcome:'+2.4R', mae:'0.2R', mfe:'2.8R', mindset:'Focused' },
    { time:'11:02', stock:'TSLA', dir:'Long',  strategy:'Bull Flag',     entry:'248.10', exit:'244.30', outcome:'-0.8R', mae:'1.1R', mfe:'0.6R', mindset:'Revenge' },
    { time:'13:45', stock:'META', dir:'Long',  strategy:'Trend Follow',  entry:'592.40', exit:'596.00', outcome:'+1.1R', mae:'0.3R', mfe:'1.9R', mindset:'Hesitant' },
  ],
};

function getDayStats(dateStr) {
  const trades = TRADES_BY_DATE[dateStr] || [];
  if (!trades.length) return null;
  let wins = 0, totalR = 0;
  trades.forEach(t => {
    const r = parseFloat(t.outcome.replace('+', ''));
    totalR += r;
    if (r > 0) wins++;
  });
  return { trades, count: trades.length, totalR: totalR.toFixed(1), wins, losses: trades.length - wins };
}
