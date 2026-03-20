/* ═══════════════════════════════════════
   COGNITIONTRADE — SIDEBAR RENDERER
   sidebar.js — injects shared sidebar HTML
═══════════════════════════════════════ */

(function injectSidebar() {
  // Determine active page
  const page = window.location.pathname.split('/').pop().replace('.html', '');

  const navItems = [
    { id: 'dashboard',   label: 'Dashboard',        badge: '',    group: 'Overview', icon: '<rect x="1" y="1" width="6" height="6" rx="1.5"/><rect x="9" y="1" width="6" height="6" rx="1.5"/><rect x="1" y="9" width="6" height="6" rx="1.5"/><rect x="9" y="9" width="6" height="6" rx="1.5"/>' },
    { id: 'journal',     label: 'Log a Trade',       badge: 'New', group: null,       icon: '<path d="M3 2h8a1 1 0 011 1v11l-3-2-3 2V3a1 1 0 011-1z"/>' },
    { id: 'trades',      label: 'Trade History',     badge: '',    group: null,       icon: '<rect x="2" y="2" width="12" height="3" rx="1"/><rect x="2" y="7" width="12" height="3" rx="1"/><rect x="2" y="12" width="8" height="3" rx="1"/>' },
    { id: 'performance', label: 'My Performance',    badge: '',    group: 'AI Agents',icon: '<path d="M2 12l4-4 3 3 5-7"/>' },
    { id: 'strategy',    label: 'Execution Review',  badge: '2r',  group: null,       icon: '<path d="M8 2L2 14h12L8 2z"/><path d="M8 10v2M8 7v1.5"/>' },
    { id: 'researcher',  label: 'Market Briefing',   badge: '',    group: null,       icon: '<circle cx="6" cy="6" r="4"/><path d="M9.5 9.5l4 4"/>' },
    { id: 'chat',        label: 'Ask My AI Coach',   badge: '',    group: null,       icon: '<path d="M14 10a2 2 0 01-2 2H5l-3 3V4a2 2 0 012-2h8a2 2 0 012 2v6z"/>' },
    { id: 'settings',    label: 'Settings',          badge: '',    group: 'Account',  icon: '<circle cx="8" cy="8" r="2.5"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"/>' },
  ];

  let lastGroup = null;
  let navHTML = '';

  navItems.forEach(item => {
    if (item.group && item.group !== lastGroup) {
      navHTML += `<div class="nav-section"><div class="nav-label">${item.group}</div>`;
      lastGroup = item.group;
    } else if (!item.group && lastGroup !== '__none') {
      // continuation of previous section — no extra div needed
    }

    const isActive = page === item.id;
    const badgeClass = item.badge === '2r' ? 'badge badge-red' : 'badge';
    const badgeLabel = item.badge === '2r' ? '2' : item.badge;
    const badgeHTML  = badgeLabel ? `<span class="${badgeClass}">${badgeLabel}</span>` : '';

    navHTML += `
      <a href="${item.id}.html" class="nav-item${isActive ? ' active' : ''}" data-view="${item.id}">
        <svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">${item.icon}</svg>
        ${item.label}${badgeHTML}
      </a>`;

    if (item.group) navHTML += `</div>`;
  });

  const html = `
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">CT</div>
        <div>
          <div class="logo-text">CognitionTrade</div>
          <div class="logo-sub">AI Journal</div>
        </div>
      </div>
      <nav class="nav">${navHTML}</nav>
      <div class="sidebar-footer">
        <div class="avatar" data-user-avatar>JD</div>
        <div style="flex:1;min-width:0;">
          <div class="user-name" data-user-name>Jordan Dex</div>
          <div class="user-plan" data-user-plan>Pro · 342 trades</div>
        </div>
        <div class="theme-toggle" data-action="toggle-theme" title="Toggle theme"><div class="theme-toggle-thumb"></div></div>
      </div>
    </aside>`;

  document.getElementById('sidebar-mount').innerHTML = html;
})();
