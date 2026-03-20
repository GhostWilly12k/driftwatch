/* ═══════════════════════════════════════
   COGNITIONTRADE — CHARTS MODULE
   charts.js — loaded on pages that need charts
═══════════════════════════════════════ */

const CT_Charts = (() => {
  const instances = {};

  function colors() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      grid: dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.06)',
      tick: dark ? '#4a5568' : '#8892a0',
    };
  }

  function make(id, config) {
    if (instances[id]) { try { instances[id].destroy(); } catch(e){} delete instances[id]; }
    const el = document.getElementById(id);
    if (!el || !el.offsetParent) return;
    instances[id] = new Chart(el, config);
  }

  function equity() {
    const c = colors();
    const labels = ['Feb 1','','','','10','','','','20','','','','Mar 1','','','','10','','','Mar 20'];
    const data   = [0,0.8,1.6,0.4,1.8,2.6,1.4,3.2,2.8,4.1,3.5,5.2,4.8,6.4,5.6,7.1,6.3,8.0,7.2,8.9];
    make('equityChart', {
      type: 'line',
      data: { labels, datasets: [{ data, borderColor:'#00d4aa', borderWidth:2, fill:true, backgroundColor:'rgba(0,212,170,0.06)', pointRadius:0, tension:0.4 }] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales: { x:{grid:{color:c.grid},ticks:{color:c.tick,font:{size:11,family:'DM Mono'}}}, y:{grid:{color:c.grid},ticks:{color:c.tick,font:{size:11,family:'DM Mono'},callback:v=>v+'R'}} } }
    });
  }

  function monthly() {
    const c = colors();
    make('monthlyChart', {
      type: 'bar',
      data: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
        datasets: [{ data:[4.2,-1.8,6.5,3.1,-0.4,7.8,2.3,5.6,-2.1,8.4,1.9,3.7], backgroundColor: ctx => ctx.raw >= 0 ? 'rgba(0,212,170,0.7)' : 'rgba(255,71,87,0.7)', borderRadius:4 }]
      },
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales: { x:{grid:{display:false},ticks:{color:c.tick,font:{size:11}}}, y:{grid:{color:c.grid},ticks:{color:c.tick,font:{size:11},callback:v=>v+'R'}} } }
    });
  }

  function maeMfe() {
    const c = colors();
    make('maeMfeChart', {
      type: 'scatter',
      data: { datasets: [
        { label:'Max Risk Hit',      data:[{x:0.3,y:1},{x:0.8,y:2},{x:1.1,y:3},{x:0.4,y:4},{x:1.8,y:5},{x:0.6,y:6},{x:1.2,y:7}], backgroundColor:'rgba(255,71,87,0.65)',  pointRadius:7 },
        { label:'Max Gain Available',data:[{x:2.1,y:1},{x:1.4,y:2},{x:2.8,y:3},{x:1.9,y:4},{x:0.3,y:5},{x:2.4,y:6},{x:1.6,y:7}], backgroundColor:'rgba(0,212,170,0.65)', pointRadius:7 },
      ]},
      options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
        scales: { x:{grid:{color:c.grid},ticks:{color:c.tick,font:{size:11},callback:v=>v+'R'},min:0,max:3.5}, y:{display:false} } }
    });
  }

  function sentiment() {
    make('sentimentChart', {
      type: 'doughnut',
      data: { labels:['Bearish','Bullish','Neutral'], datasets:[{ data:[52,28,20], backgroundColor:['#ff4757','#00d4aa','#4a5568'], borderWidth:0 }] },
      options: { responsive:true, maintainAspectRatio:false, cutout:'72%', plugins:{legend:{display:false}} }
    });
  }

  function refreshAll() {
    Object.keys(instances).forEach(k => { try { instances[k].destroy(); } catch(e){} delete instances[k]; });
    // Re-init whichever canvases exist on this page
    if (document.getElementById('equityChart'))   equity();
    if (document.getElementById('monthlyChart'))  monthly();
    if (document.getElementById('maeMfeChart'))   maeMfe();
    if (document.getElementById('sentimentChart'))sentiment();
  }

  function initPage() {
    setTimeout(() => {
      equity(); monthly(); maeMfe(); sentiment();
    }, 80);
  }

  return { equity, monthly, maeMfe, sentiment, refreshAll, initPage };
})();

document.addEventListener('DOMContentLoaded', CT_Charts.initPage);
