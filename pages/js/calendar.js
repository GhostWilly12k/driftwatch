/* ═══════════════════════════════════════
   COGNITIONTRADE — CALENDAR MODULE
   calendar.js — loaded on trades.html
═══════════════════════════════════════ */

const CT_Calendar = (() => {
  let curYear = 2026, curMonth = 2, selDate = null; // March = index 2

  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const DAYS   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const PSY_CLASS = { Focused:'psy-focused', Impulsive:'psy-fomo', 'In the Zone':'psy-focused', Hesitant:'psy-hesitant', Revenge:'psy-revenge', Confident:'psy-focused' };

  function changeMonth(dir) {
    curMonth += dir;
    if (curMonth > 11) { curMonth = 0; curYear++; }
    if (curMonth < 0)  { curMonth = 11; curYear--; }
    selDate = null;
    closeDayDetail();
    render();
  }

  function render() {
    document.getElementById('calMonthLabel').textContent = `${MONTHS[curMonth]} ${curYear}`;
    const firstDay = new Date(curYear, curMonth, 1).getDay();
    const dim      = new Date(curYear, curMonth + 1, 0).getDate();
    const today    = new Date();

    // Month summary stats
    let mT = 0, mD = 0, mR = 0, mW = 0, best = -Infinity, bestS = null;
    for (let d = 1; d <= dim; d++) {
      const ds = dateStr(d);
      const s  = getDayStats(ds);
      if (s) { mT += s.count; mD++; mR += parseFloat(s.totalR); mW += s.wins; if (parseFloat(s.totalR) > best) { best = parseFloat(s.totalR); bestS = s.totalR; } }
    }
    document.getElementById('stripTrades').textContent = mT || '—';
    document.getElementById('stripDays').textContent   = mD || '—';
    const pe = document.getElementById('stripPnl');
    pe.textContent = mD ? (mR >= 0 ? '+' : '') + mR.toFixed(1) + 'R' : '—';
    pe.style.color = mR >= 0 ? 'var(--green)' : 'var(--red)';
    document.getElementById('stripWin').textContent  = mT ? Math.round(mW / mT * 100) + '%' : '—';
    document.getElementById('stripBest').textContent = bestS !== null ? (parseFloat(bestS) >= 0 ? '+' : '') + bestS + 'R' : '—';

    // Build grid
    const container = document.getElementById('calDays');
    container.innerHTML = '';

    // Empty offset cells
    for (let i = 0; i < firstDay; i++) {
      const e = document.createElement('div'); e.className = 'cal-day empty'; container.appendChild(e);
    }

    for (let d = 1; d <= dim; d++) {
      const ds    = dateStr(d);
      const stats = getDayStats(ds);
      const isToday = today.getFullYear() === curYear && today.getMonth() === curMonth && today.getDate() === d;
      const dow     = new Date(curYear, curMonth, d).getDay();
      const isWeekend = dow === 0 || dow === 6;

      const cell = document.createElement('div');
      cell.className = 'cal-day' + (isToday ? ' today' : '') + (selDate === ds ? ' selected' : '');

      if (stats) {
        const r = parseFloat(stats.totalR);
        cell.classList.add(r > 0.05 ? 'profit' : r < -0.05 ? 'loss' : 'flat');
        cell.innerHTML = `
          <div class="cal-day-num">${d}</div>
          <div class="cal-day-count">${stats.count} trade${stats.count > 1 ? 's' : ''}</div>
          <div class="cal-day-dots">${stats.trades.map(t => `<div class="cal-dot" style="background:${parseFloat(t.outcome.replace('+','')) > 0 ? 'var(--green)' : 'var(--red)'}"></div>`).join('')}</div>
          <div class="cal-day-pnl">${r >= 0 ? '+' : ''}${stats.totalR}R</div>
          <div class="cal-day-bar"></div>`;
        cell.addEventListener('click', () => selectDay(ds, d, cell));
      } else {
        cell.classList.add('no-trades');
        cell.style.opacity = isWeekend ? '0.18' : '0.35';
        cell.innerHTML = `<div class="cal-day-num" style="color:var(--text3)">${d}</div>`;
      }
      container.appendChild(cell);
    }
  }

  function dateStr(d) {
    return `${curYear}-${String(curMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  }

  function selectDay(ds, dayNum, cellEl) {
    selDate = ds;
    document.querySelectorAll('.cal-day').forEach(c => c.classList.remove('selected'));
    cellEl.classList.add('selected');
    showDayDetail(ds, dayNum);
  }

  function showDayDetail(ds, dayNum) {
    const stats = getDayStats(ds);
    if (!stats) return;
    const dow = new Date(curYear, curMonth, dayNum).getDay();
    document.getElementById('dayDetailTitle').textContent = `${DAYS[dow]}, ${MONTHS[curMonth]} ${dayNum}`;
    const r = parseFloat(stats.totalR);
    document.getElementById('dayDetailMeta').innerHTML =
      `<span class="day-stat-pill">${stats.count} trades</span>
       <span class="day-stat-pill" style="color:${r >= 0 ? 'var(--green)' : 'var(--red)'}">${r >= 0 ? '+' : ''}${stats.totalR}R total</span>
       <span class="day-stat-pill">${stats.wins}W / ${stats.losses}L</span>`;

    document.getElementById('dayDetailBody').innerHTML = stats.trades.map(t => {
      const rn = parseFloat(t.outcome.replace('+', ''));
      return `<tr>
        <td style="font-family:var(--mono);font-size:12px;color:var(--text2)">${t.time}</td>
        <td><span class="symbol">${t.stock}</span></td>
        <td><span style="color:${t.dir === 'Long' ? 'var(--green)' : 'var(--red)'};font-family:var(--mono);font-size:12px">${t.dir}</span></td>
        <td><span class="setup-tag">${t.strategy}</span></td>
        <td style="font-family:var(--mono);font-size:12px">${t.entry}</td>
        <td style="font-family:var(--mono);font-size:12px">${t.exit}</td>
        <td><span class="r-val ${rn >= 0 ? 'c-green' : 'c-red'}">${t.outcome}</span></td>
        <td style="font-family:var(--mono);font-size:12px;color:var(--red)">${t.mae}</td>
        <td style="font-family:var(--mono);font-size:12px;color:var(--green)">${t.mfe}</td>
        <td><span class="psy-tag ${PSY_CLASS[t.mindset] || 'psy-focused'}">${t.mindset}</span></td>
      </tr>`;
    }).join('');

    const det = document.getElementById('dayDetail');
    det.classList.remove('hidden');
    setTimeout(() => det.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
  }

  function closeDayDetail() {
    document.getElementById('dayDetail').classList.add('hidden');
    selDate = null;
    document.querySelectorAll('.cal-day').forEach(c => c.classList.remove('selected'));
  }

  // Public API
  return { render, changeMonth, closeDayDetail };
})();

// Expose to HTML onclick attributes
function calChangeMonth(dir) { CT_Calendar.changeMonth(dir); }
function closeDayDetail()     { CT_Calendar.closeDayDetail(); }

document.addEventListener('DOMContentLoaded', CT_Calendar.render);
