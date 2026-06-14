/* ── Collectorly Numismatics — Web UI JS ──────────────────────────────────── */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────

let _lastIdentification = null;
let _lastCertData       = null;  // most recent cert lookup result
let _pcgsPriceChart     = null;  // Chart.js instance for PCGS price tab
let _cmpPopChart        = null;  // Chart.js instance for compare tab
let _mktPriceChart      = null;  // Chart.js instance for market tab

// ── Tab routing ───────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-tabs .nav-link').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-tabs .nav-link').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const id = 'tab-' + btn.dataset.tab;
    document.getElementById(id)?.classList.add('active');
    if (btn.dataset.tab === 'collection') loadCollection();
  });
});

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(msg, type = 'info') {
  const el   = document.getElementById('main-toast');
  const body = document.getElementById('toast-msg');
  el.className = `toast align-items-center text-bg-${
    type === 'error' ? 'danger' : type === 'success' ? 'success' : 'secondary'} border-0`;
  body.textContent = msg;
  bootstrap.Toast.getOrCreateInstance(el, { delay: 3500 }).show();
}

// ── Metal prices ──────────────────────────────────────────────────────────────

async function refreshPrices() {
  const container = document.getElementById('metal-prices');
  container.innerHTML = '<span class="text-muted small">Loading...</span>';
  try {
    const res  = await fetch('/api/metal-prices');
    const data = await res.json();
    if (data.error && !Object.keys(data.prices || {}).length) {
      container.innerHTML = `<span class="text-warning small">${escHtml(data.error)}</span>`;
      return;
    }
    const labels = { gold: 'Gold', silver: 'Silver', platinum: 'Platinum', palladium: 'Palladium' };
    const html = Object.entries(data.prices || {}).map(([metal, val]) => `
      <div class="price-chip">
        <span class="metal-name">${escHtml(labels[metal] || metal)}</span>
        <span class="metal-val">$${Number(val).toLocaleString('en-US',
          {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
      </div>
    `).join('');
    container.innerHTML = html || '<span class="text-muted small">No price data</span>';
  } catch (e) {
    container.innerHTML = '<span class="text-warning small">Price fetch failed</span>';
  }
}

// ── Image upload & identify ───────────────────────────────────────────────────

const dropZone   = document.getElementById('drop-zone');
const fileInput  = document.getElementById('coin-file');
const previewImg = document.getElementById('preview-img');
const dropHint   = document.getElementById('drop-hint');

dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setPreview(file);
});
fileInput.addEventListener('change', () => { if (fileInput.files[0]) setPreview(fileInput.files[0]); });

function setPreview(file) {
  const reader = new FileReader();
  reader.onload = ev => {
    previewImg.src = ev.target.result;
    previewImg.classList.remove('d-none');
    dropHint.classList.add('d-none');
  };
  reader.readAsDataURL(file);
  document.getElementById('btn-identify').disabled = false;
  _lastIdentification = null;
  document.getElementById('identify-results').classList.add('d-none');
  document.getElementById('identify-placeholder').classList.remove('d-none');
}

function clearIdentify() {
  previewImg.src = '';
  previewImg.classList.add('d-none');
  dropHint.classList.remove('d-none');
  fileInput.value = '';
  document.getElementById('btn-identify').disabled = true;
  document.getElementById('identify-results').classList.add('d-none');
  document.getElementById('identify-placeholder').classList.remove('d-none');
  _lastIdentification = null;
}

async function identifyCoin() {
  const file = fileInput.files[0];
  if (!file) { showToast('No image selected', 'error'); return; }

  document.getElementById('identify-placeholder').classList.add('d-none');
  document.getElementById('identify-results').classList.add('d-none');
  document.getElementById('identify-loading').classList.remove('d-none');
  document.getElementById('btn-identify').disabled = true;

  const form = new FormData();
  form.append('image', file);

  try {
    const res  = await fetch('/api/identify', { method: 'POST', body: form });
    const data = await res.json();
    document.getElementById('identify-loading').classList.add('d-none');
    document.getElementById('btn-identify').disabled = false;
    if (!res.ok || data.error) {
      showToast(data.error || 'Identification failed', 'error');
      document.getElementById('identify-placeholder').classList.remove('d-none');
      return;
    }
    _lastIdentification = data.identification;
    renderIdentification(data.identification, data.catalog_matches || []);
  } catch (e) {
    document.getElementById('identify-loading').classList.add('d-none');
    document.getElementById('btn-identify').disabled = false;
    showToast('Network error: ' + e.message, 'error');
    document.getElementById('identify-placeholder').classList.remove('d-none');
  }
}

function renderIdentification(id, catalogMatches) {
  const fields = [
    ['Coin Name',     id.coin_name],
    ['Country',       id.country],
    ['Year',          id.year],
    ['Mint',          id.mint],
    ['Denomination',  id.denomination],
    ['KM#',           id.km_number],
    ['Metal',         id.metal],
    ['Grade (est.)',  id.grade_estimate],
    ['Obverse',       id.obverse_desc],
    ['Reverse',       id.reverse_desc],
    ['Notes',         id.notes],
  ].filter(([, v]) => v && String(v).trim());

  document.getElementById('id-fields').innerHTML = fields.map(([label, val]) => `
    <div class="col-6 col-md-4">
      <div class="id-field">
        <div class="label">${escHtml(label)}</div>
        <div class="value">${escHtml(String(val))}</div>
      </div>
    </div>
  `).join('');

  const conf  = parseFloat(id.confidence) || 0;
  const pct   = Math.round(conf * 100);
  const cls   = conf >= 0.75 ? 'badge-high' : conf >= 0.5 ? 'badge-medium' : 'badge-low';
  const badge = document.getElementById('confidence-badge');
  badge.textContent = `${pct}% confidence`;
  badge.className   = `badge ${cls}`;

  if (id.key_features?.length) {
    document.getElementById('id-fields').insertAdjacentHTML('beforeend', `
      <div class="col-12">
        <div class="id-field">
          <div class="label">Key Features</div>
          <div class="value">${id.key_features.map(f =>
            `<span class="badge bg-light text-dark me-1 mb-1">${escHtml(f)}</span>`).join('')}</div>
        </div>
      </div>
    `);
  }

  const catCard = document.getElementById('catalog-card');
  const catBody = document.getElementById('catalog-body');
  if (catalogMatches.length) {
    catBody.innerHTML = `<table class="data-table"><thead><tr>
      <th>Catalog</th><th>Country</th><th>KM#</th><th>Denomination</th><th>Metal</th><th>Page</th>
    </tr></thead><tbody>` +
      catalogMatches.map(m => `<tr>
        <td>${escHtml(m.catalog || '—')}</td>
        <td>${escHtml(m.country || '—')}</td>
        <td>${escHtml(m.km_number || '—')}</td>
        <td>${escHtml(m.denomination || '—')}</td>
        <td>${escHtml(m.metal || '—')}</td>
        <td>${m.page_number ? m.page_number : '—'}</td>
      </tr>`).join('') +
    `</tbody></table>`;
    catCard.classList.remove('d-none');
  } else {
    catCard.classList.add('d-none');
  }

  document.getElementById('identify-results').classList.remove('d-none');
  document.getElementById('identify-placeholder').classList.add('d-none');
}

// ── Quick lookup from identified coin ────────────────────────────────────────

function _quickParams() {
  if (!_lastIdentification) { showToast('No coin identified yet', 'error'); return null; }
  return {
    name: _lastIdentification.coin_name || '',
    year: _lastIdentification.year || '',
    mint: _lastIdentification.mint || '',
  };
}

async function quickNGC() {
  const p = _quickParams(); if (!p) return;
  openQuickModal('NGC Census — ' + [p.year, p.mint, p.name].filter(Boolean).join(' '));
  await _doQuickFetch('/api/ngc-census', p, renderNGCData);
}
async function quickPCGSPrice() {
  const p = _quickParams(); if (!p) return;
  openQuickModal('PCGS Prices — ' + [p.year, p.mint, p.name].filter(Boolean).join(' '));
  await _doQuickFetch('/api/pcgs-prices', p, renderPCGSPriceData);
}
async function quickPCGSPop() {
  const p = _quickParams(); if (!p) return;
  openQuickModal('PCGS Population — ' + [p.year, p.mint, p.name].filter(Boolean).join(' '));
  await _doQuickFetch('/api/pcgs-pop', p, renderPCGSPopData);
}
function quickCompare() {
  const p = _quickParams(); if (!p) return;
  // Pre-fill the compare tab and switch to it
  document.getElementById('cmp-name').value = p.name;
  document.getElementById('cmp-year').value = p.year;
  document.getElementById('cmp-mint').value = p.mint;
  document.querySelector('[data-tab="compare"]').click();
  fetchCompare();
}

function openQuickModal(title) {
  document.getElementById('quick-modal-title').textContent = title;
  document.getElementById('quick-body').innerHTML = '';
  document.getElementById('quick-loading').classList.remove('d-none');
  bootstrap.Modal.getOrCreateInstance(document.getElementById('quickModal')).show();
}
async function _doQuickFetch(url, body, renderer) {
  try {
    const res  = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    document.getElementById('quick-loading').classList.add('d-none');
    document.getElementById('quick-body').innerHTML = renderer(data);
  } catch (e) {
    document.getElementById('quick-loading').classList.add('d-none');
    document.getElementById('quick-body').innerHTML =
      `<div class="alert alert-danger">${escHtml(e.message)}</div>`;
  }
}

// ── NGC Census tab ────────────────────────────────────────────────────────────

async function fetchNGC() {
  const name = document.getElementById('ngc-name').value.trim();
  const year = document.getElementById('ngc-year').value.trim();
  const mint = document.getElementById('ngc-mint').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }
  document.getElementById('ngc-results').classList.add('d-none');
  document.getElementById('ngc-loading').classList.remove('d-none');
  try {
    const res  = await fetch('/api/ngc-census', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, year, mint }),
    });
    const data = await res.json();
    document.getElementById('ngc-loading').classList.add('d-none');
    document.getElementById('ngc-body').innerHTML = renderNGCData(data);
    const link = document.getElementById('ngc-link');
    link.href = data.url || '#';
    link.style.display = data.url ? '' : 'none';
    document.getElementById('ngc-results').classList.remove('d-none');
  } catch (e) {
    document.getElementById('ngc-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
  }
}

function renderNGCData(data) {
  if (data.error && !Object.keys(data.populations || {}).length)
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  const pops = data.populations || {};
  if (!Object.keys(pops).length) return '<p class="text-muted mb-0">No population data found.</p>';
  return `<div class="table-scroll"><table class="data-table">
    <thead><tr><th>Grade</th><th>Population</th></tr></thead>
    <tbody>${Object.entries(pops).map(([g, p]) =>
      `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}
    </tbody></table></div>` +
    (data.error ? `<p class="text-muted small mt-2 mb-0">${escHtml(data.error)}</p>` : '');
}

// ── PCGS tab ──────────────────────────────────────────────────────────────────

async function fetchPCGSPrice() {
  const name = document.getElementById('pcgs-name').value.trim();
  const year = document.getElementById('pcgs-year').value.trim();
  const mint = document.getElementById('pcgs-mint').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }
  document.getElementById('pcgs-results').classList.add('d-none');
  document.getElementById('pcgs-chart-wrap').classList.add('d-none');
  document.getElementById('pcgs-loading').classList.remove('d-none');
  document.getElementById('pcgs-result-title').textContent = 'PCGS Price Guide';
  try {
    const res  = await fetch('/api/pcgs-prices', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, year, mint }),
    });
    const data = await res.json();
    document.getElementById('pcgs-loading').classList.add('d-none');
    document.getElementById('pcgs-body').innerHTML = renderPCGSPriceData(data);
    const link = document.getElementById('pcgs-link');
    link.href = data.url || '#';
    link.style.display = data.url ? '' : 'none';
    document.getElementById('pcgs-results').classList.remove('d-none');
    _renderPriceChart(data.prices || {});
  } catch (e) {
    document.getElementById('pcgs-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
  }
}

function _renderPriceChart(prices) {
  const clean = { ...prices };
  delete clean.__coin__;
  const entries = Object.entries(clean)
    .map(([g, v]) => [g, parseFloat(String(v).replace(/[$,]/g, '')) || 0])
    .filter(([, v]) => v > 0);
  if (!entries.length) return;

  document.getElementById('pcgs-chart-wrap').classList.remove('d-none');
  if (_pcgsPriceChart) { _pcgsPriceChart.destroy(); _pcgsPriceChart = null; }

  const ctx = document.getElementById('pcgs-price-chart').getContext('2d');
  _pcgsPriceChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: entries.map(([g]) => g),
      datasets: [{
        label: 'Price ($)',
        data: entries.map(([, v]) => v),
        backgroundColor: 'rgba(201,162,39,0.7)',
        borderColor: '#a07d10',
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString() } },
      },
    },
  });
}

function renderPCGSPriceData(data) {
  if (data.error && !Object.keys(data.prices || {}).length)
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  const prices   = { ...data.prices };
  const coinName = prices.__coin__ || '';
  delete prices.__coin__;
  if (!Object.keys(prices).length) return '<p class="text-muted mb-0">No price data found.</p>';
  return (coinName ? `<p class="fw-semibold mb-2">${escHtml(coinName)}</p>` : '') +
    `<div class="table-scroll"><table class="data-table">
      <thead><tr><th>Grade</th><th>Price</th></tr></thead>
      <tbody>${Object.entries(prices).map(([g, p]) =>
        `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}
      </tbody></table></div>`;
}

async function fetchPCGSPop() {
  const name = document.getElementById('pcgs-name').value.trim();
  const year = document.getElementById('pcgs-year').value.trim();
  const mint = document.getElementById('pcgs-mint').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }
  document.getElementById('pcgs-results').classList.add('d-none');
  document.getElementById('pcgs-loading').classList.remove('d-none');
  document.getElementById('pcgs-result-title').textContent = 'PCGS Population Report';
  try {
    const res  = await fetch('/api/pcgs-pop', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, year, mint }),
    });
    const data = await res.json();
    document.getElementById('pcgs-loading').classList.add('d-none');
    document.getElementById('pcgs-body').innerHTML = renderPCGSPopData(data);
    document.getElementById('pcgs-results').classList.remove('d-none');
  } catch (e) {
    document.getElementById('pcgs-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
  }
}

function renderPCGSPopData(data) {
  if (data.error && !Object.keys(data.populations || {}).length)
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  const pops = data.populations || {};
  if (!Object.keys(pops).length) return '<p class="text-muted mb-0">No population data found.</p>';
  return `<div class="table-scroll"><table class="data-table">
    <thead><tr><th>Grade</th><th>Population</th></tr></thead>
    <tbody>${Object.entries(pops).map(([g, p]) =>
      `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}
    </tbody></table></div>`;
}

// ── Cert lookup ───────────────────────────────────────────────────────────────

async function fetchNGCCert() { await _doCertFetch('/api/ngc-cert', 'NGC Certificate', 'NGC'); }
async function fetchPCGSCert() { await _doCertFetch('/api/pcgs-cert', 'PCGS Certificate', 'PCGS'); }

async function _doCertFetch(url, title, source) {
  const cert = document.getElementById('cert-number').value.trim();
  if (!cert) { showToast('Cert number required', 'error'); return; }
  document.getElementById('cert-results').classList.add('d-none');
  document.getElementById('cert-loading').classList.remove('d-none');
  document.getElementById('cert-result-title').textContent = title + ' — ' + cert;
  try {
    const res  = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cert }),
    });
    const data = await res.json();
    document.getElementById('cert-loading').classList.add('d-none');
    document.getElementById('cert-body').innerHTML = renderCertData(data);
    document.getElementById('cert-results').classList.remove('d-none');
    // Store for "Add to Collection"
    _lastCertData = { ...data, source, cert_number: cert };
  } catch (e) {
    document.getElementById('cert-loading').classList.add('d-none');
    showToast('Network error: ' + e.message, 'error');
  }
}

function renderCertData(data) {
  const fields  = data.data   || {};
  const images  = data.images || [];
  const hasData = Object.keys(fields).length > 0;

  if (data.error && !hasData)
    return `<div class="alert alert-warning mb-0"><i class="bi bi-exclamation-triangle me-2"></i>${escHtml(data.error)}</div>`;

  let html = '';

  // Coin images — proxied to bypass CDN hotlink blocks
  if (images.length) {
    html += '<div class="d-flex gap-2 mb-3 flex-wrap" id="cert-images-row">';
    images.forEach((src, i) => {
      const proxied = '/api/image-proxy?url=' + encodeURIComponent(src);
      const label   = i === 0 ? 'Obverse' : 'Reverse';
      html += `<img src="${proxied}" alt="${label}"
                    class="cert-coin-img rounded" title="${label}"
                    onerror="this.style.display='none'">`;
    });
    html += '</div>';
  }

  if (data.url) {
    html += `<a href="${escHtml(data.url)}" target="_blank"
               class="btn btn-sm btn-outline-secondary mb-3">
               <i class="bi bi-box-arrow-up-right me-1"></i>View on site</a> `;
  }
  if (data.error && hasData)
    html += `<div class="alert alert-warning py-1 small mb-2">${escHtml(data.error)}</div>`;

  const highlights = ['Coin','Grade','Year','Mint','Designation','Variety',
                      'Pop at Grade','Pop Finer','Price Guide'];
  const chips = highlights.filter(k => fields[k]);
  if (chips.length) {
    html += '<div class="d-flex gap-2 flex-wrap mb-3">';
    chips.forEach(k => {
      html += `<div class="id-field"><div class="label">${escHtml(k)}</div>
                <div class="value">${escHtml(fields[k])}</div></div>`;
    });
    html += '</div>';
  }

  if (hasData) {
    const rest = Object.entries(fields).filter(([k]) => !chips.includes(k));
    if (rest.length) {
      html += `<table class="data-table"><tbody>${
        rest.map(([k, v]) =>
          `<tr><td class="fw-semibold" style="width:38%">${escHtml(k)}</td>
               <td>${escHtml(String(v))}</td></tr>`).join('')
      }</tbody></table>`;
    }
  } else {
    html += '<p class="text-muted mb-0">No details returned.</p>';
  }
  return html;
}

function openAddToCollection() {
  if (_lastCertData) {
    const f = _lastCertData.data || {};
    document.getElementById('add-coin-name').value  = f['Coin'] || f['Description'] || '';
    document.getElementById('add-source').value     = _lastCertData.source || 'NGC';
    document.getElementById('add-cert').value       = _lastCertData.cert_number || '';
    document.getElementById('add-grade').value      = f['Grade'] || '';
    document.getElementById('add-year').value       = f['Year'] || '';
    document.getElementById('add-mint').value       = f['Mint'] || '';
    document.getElementById('add-designation').value = f['Designation'] || '';
  }
  openAddModal();
}

// ── NGC vs PCGS Compare tab ───────────────────────────────────────────────────

async function fetchCompare() {
  const name = document.getElementById('cmp-name').value.trim();
  const year = document.getElementById('cmp-year').value.trim();
  const mint = document.getElementById('cmp-mint').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }

  document.getElementById('cmp-results').classList.add('d-none');
  document.getElementById('cmp-placeholder').classList.add('d-none');
  document.getElementById('cmp-loading').classList.remove('d-none');

  try {
    const res  = await fetch('/api/ngc-vs-pcgs', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, year, mint }),
    });
    const data = await res.json();
    document.getElementById('cmp-loading').classList.add('d-none');
    _renderCompare(data);
  } catch (e) {
    document.getElementById('cmp-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
    document.getElementById('cmp-placeholder').classList.remove('d-none');
  }
}

function _renderCompare(data) {
  const ngcPop  = data.ngc?.populations  || {};
  const pcgsPop = data.pcgs?.populations || {};
  const pcgsPrices = data.pcgs?.prices   || {};

  function _popTable(pops) {
    if (!Object.keys(pops).length) return '<p class="text-muted small mb-0">No data</p>';
    const total = Object.values(pops).reduce((s, v) => s + (parseInt(v) || 0), 0);
    return `<p class="small text-muted mb-1">Total graded: <strong>${total.toLocaleString()}</strong></p>
    <div class="table-scroll" style="max-height:200px"><table class="data-table">
      <thead><tr><th>Grade</th><th>Pop</th></tr></thead>
      <tbody>${Object.entries(pops).slice(0, 20).map(([g, p]) =>
        `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}
      </tbody></table></div>`;
  }

  document.getElementById('cmp-ngc-body').innerHTML  = _popTable(ngcPop);
  document.getElementById('cmp-pcgs-body').innerHTML = _popTable(pcgsPop) +
    (Object.keys(pcgsPrices).length
      ? `<hr class="my-2"><p class="small fw-semibold mb-1">Price Guide</p>
         <table class="data-table"><tbody>${
           Object.entries(pcgsPrices).filter(([k]) => k !== '__coin__').slice(0, 10)
             .map(([g, p]) => `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`)
             .join('')
         }</tbody></table>`
      : '');

  // Population comparison chart
  const allGrades = [...new Set([...Object.keys(ngcPop), ...Object.keys(pcgsPop)])].slice(0, 16);
  if (allGrades.length) {
    if (_cmpPopChart) { _cmpPopChart.destroy(); _cmpPopChart = null; }
    const ctx = document.getElementById('cmp-pop-chart').getContext('2d');
    _cmpPopChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: allGrades,
        datasets: [
          {
            label: 'NGC',
            data: allGrades.map(g => parseInt(ngcPop[g]) || 0),
            backgroundColor: 'rgba(13,110,253,0.7)',
            borderColor: '#0d6efd',
            borderWidth: 1,
            borderRadius: 3,
          },
          {
            label: 'PCGS',
            data: allGrades.map(g => parseInt(pcgsPop[g]) || 0),
            backgroundColor: 'rgba(25,135,84,0.7)',
            borderColor: '#198754',
            borderWidth: 1,
            borderRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'top' } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  document.getElementById('cmp-results').classList.remove('d-none');
}

// ── Market Feed tab ───────────────────────────────────────────────────────────

async function fetchMarket() {
  const name  = document.getElementById('mkt-name').value.trim();
  const year  = document.getElementById('mkt-year').value.trim();
  const mint  = document.getElementById('mkt-mint').value.trim();
  const grade = document.getElementById('mkt-grade').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }

  document.getElementById('mkt-results').classList.add('d-none');
  document.getElementById('mkt-placeholder').classList.add('d-none');
  document.getElementById('mkt-loading').classList.remove('d-none');

  try {
    const res  = await fetch('/api/market-feed', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, year, mint, grade }),
    });
    const data = await res.json();
    document.getElementById('mkt-loading').classList.add('d-none');
    _renderMarketFeed(data);
  } catch (e) {
    document.getElementById('mkt-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
    document.getElementById('mkt-placeholder').classList.remove('d-none');
  }
}

function _renderMarketFeed(data) {
  const results = data.results || [];
  document.getElementById('mkt-count').textContent =
    results.length ? `${results.length} results` : 'No results';

  if (!results.length) {
    document.getElementById('mkt-body').innerHTML =
      '<p class="text-muted p-3 mb-0">No recent sales found. Try a broader search.</p>';
    document.getElementById('mkt-results').classList.remove('d-none');
    return;
  }

  const rows = results.map(r => `
    <div class="mkt-row d-flex align-items-start gap-3 p-3 border-bottom">
      <span class="badge bg-${r.source === 'GreatCollections' ? 'primary' : 'secondary'} flex-shrink-0">
        ${escHtml(r.source === 'GreatCollections' ? 'GC' : 'Heritage')}
      </span>
      <div class="flex-grow-1 min-width-0">
        <div class="small fw-semibold text-truncate">${escHtml(r.description || '—')}</div>
        <div class="d-flex gap-3 mt-1 flex-wrap">
          ${r.grade ? `<span class="small text-muted">Grade: <strong>${escHtml(r.grade)}</strong></span>` : ''}
          ${r.date  ? `<span class="small text-muted">${escHtml(r.date)}</span>` : ''}
        </div>
      </div>
      <div class="text-end flex-shrink-0">
        <span class="fw-bold text-success">$${r.price ? Number(r.price).toLocaleString('en-US',
          {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '—'}</span>
        ${r.url ? `<br><a href="${escHtml(r.url)}" target="_blank" class="small text-muted">View</a>` : ''}
      </div>
    </div>
  `).join('');
  document.getElementById('mkt-body').innerHTML = rows;

  // Realized price chart (prices over result order as proxy for time)
  const priced = results.filter(r => r.price > 0);
  if (priced.length >= 2) {
    if (_mktPriceChart) { _mktPriceChart.destroy(); _mktPriceChart = null; }
    const ctx = document.getElementById('mkt-price-chart').getContext('2d');
    _mktPriceChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: priced.map((r, i) => r.date || `#${i + 1}`),
        datasets: [{
          label: 'Realized Price ($)',
          data: priced.map(r => r.price),
          borderColor: '#c9a227',
          backgroundColor: 'rgba(201,162,39,0.12)',
          fill: true,
          tension: 0.3,
          pointRadius: 4,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: false, ticks: { callback: v => '$' + v.toLocaleString() } } },
      },
    });
  }

  if (data.error) showToast(data.error, 'error');
  document.getElementById('mkt-results').classList.remove('d-none');
}

// ── My Collection tab ─────────────────────────────────────────────────────────

async function loadCollection() {
  document.getElementById('coll-loading').classList.remove('d-none');
  document.getElementById('coll-empty').classList.add('d-none');
  document.getElementById('coll-grid').innerHTML = '';
  try {
    const res  = await fetch('/api/collection');
    const rows = await res.json();
    document.getElementById('coll-loading').classList.add('d-none');
    if (!rows.length) {
      document.getElementById('coll-empty').classList.remove('d-none');
      document.getElementById('coll-stats').textContent = '';
      return;
    }
    _renderCollection(rows);
  } catch (e) {
    document.getElementById('coll-loading').classList.add('d-none');
    showToast('Error loading collection: ' + e.message, 'error');
  }
}

function _renderCollection(rows) {
  const totalCost  = rows.reduce((s, r) => s + (r.purchase_price || 0), 0);
  const totalValue = rows.reduce((s, r) => s + (r.current_value  || 0), 0);
  const gain       = totalValue - totalCost;
  const gainPct    = totalCost > 0 ? ((gain / totalCost) * 100).toFixed(1) : null;
  const gainCls    = gain >= 0 ? 'text-success' : 'text-danger';
  const gainSign   = gain >= 0 ? '+' : '';

  document.getElementById('coll-stats').innerHTML =
    `${rows.length} coin${rows.length !== 1 ? 's' : ''} &nbsp;·&nbsp;
     Cost: <strong>$${totalCost.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong>
     &nbsp;·&nbsp; Value: <strong>$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong>` +
    (gainPct !== null
      ? ` &nbsp;·&nbsp; <span class="${gainCls}">${gainSign}$${Math.abs(gain).toLocaleString('en-US',
          {minimumFractionDigits: 2, maximumFractionDigits: 2})} (${gainSign}${gainPct}%)</span>`
      : '');

  const grid = document.getElementById('coll-grid');
  grid.innerHTML = rows.map(r => {
    const imgHtml = r.image_url
      ? `<div class="coll-card-img">
           <img src="/api/image-proxy?url=${encodeURIComponent(r.image_url)}"
                alt="coin" onerror="this.parentElement.style.display='none'">
         </div>`
      : `<div class="coll-card-img coll-card-img--placeholder">
           <i class="bi bi-coin display-4 text-muted"></i>
         </div>`;
    const val      = r.current_value || r.purchase_price || 0;
    const srcBadge = r.source
      ? `<span class="badge bg-${r.source === 'NGC' ? 'primary' : r.source === 'PCGS' ? 'success' : 'secondary'} mb-2">
           ${escHtml(r.source)}</span>`
      : '';
    return `
    <div class="col-sm-6 col-md-4 col-xl-3">
      <div class="card coll-card h-100">
        ${imgHtml}
        <div class="card-body d-flex flex-column">
          ${srcBadge}
          <div class="fw-semibold small mb-1">${escHtml(r.coin_name || '—')}</div>
          <div class="d-flex gap-2 flex-wrap mb-2">
            ${r.grade ? `<span class="badge bg-light text-dark border">${escHtml(r.grade)}</span>` : ''}
            ${r.year  ? `<span class="small text-muted">${escHtml(r.year)}${r.mint ? '-' + r.mint : ''}</span>` : ''}
          </div>
          ${r.cert_number ? `<div class="small text-muted mb-1">Cert: ${escHtml(r.cert_number)}</div>` : ''}
          ${val > 0 ? `<div class="mt-auto fw-bold">$${val.toLocaleString('en-US',
              {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>` : ''}
          <div class="d-flex gap-1 mt-2">
            <button class="btn btn-xs btn-outline-secondary flex-grow-1" onclick="editCollItem(${r.id})">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-xs btn-outline-danger" onclick="deleteCollItem(${r.id})">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

function openAddModal() {
  document.getElementById('add-msg').classList.add('d-none');
  bootstrap.Modal.getOrCreateInstance(document.getElementById('addCollModal')).show();
}

async function saveToCollection() {
  const payload = {
    coin_name:      document.getElementById('add-coin-name').value.trim(),
    source:         document.getElementById('add-source').value,
    cert_number:    document.getElementById('add-cert').value.trim(),
    grade:          document.getElementById('add-grade').value.trim(),
    year:           document.getElementById('add-year').value.trim(),
    mint:           document.getElementById('add-mint').value.trim(),
    designation:    document.getElementById('add-designation').value.trim(),
    purchase_price: parseFloat(document.getElementById('add-purchase-price').value) || null,
    current_value:  parseFloat(document.getElementById('add-current-value').value)  || null,
    purchase_date:  document.getElementById('add-purchase-date').value || null,
    notes:          document.getElementById('add-notes').value.trim(),
    image_url:      _lastCertData?.images?.[0] || null,
    cert_data:      _lastCertData?.data || {},
  };
  try {
    const res  = await fetch('/api/collection', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      bootstrap.Modal.getInstance(document.getElementById('addCollModal'))?.hide();
      showToast('Added to collection!', 'success');
      // Clear fields
      ['add-coin-name','add-cert','add-grade','add-year','add-mint',
       'add-designation','add-notes'].forEach(id => document.getElementById(id).value = '');
      document.getElementById('add-purchase-price').value = '';
      document.getElementById('add-current-value').value = '';
      document.getElementById('add-purchase-date').value = '';
    } else {
      const msg = document.getElementById('add-msg');
      msg.className = 'alert alert-danger mt-3';
      msg.textContent = data.error || 'Save failed.';
      msg.classList.remove('d-none');
    }
  } catch (e) {
    showToast('Network error.', 'error');
  }
}

function editCollItem(id) {
  fetch('/api/collection').then(r => r.json()).then(rows => {
    const item = rows.find(r => r.id === id);
    if (!item) return;
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-purchase-price').value = item.purchase_price || '';
    document.getElementById('edit-current-value').value  = item.current_value  || '';
    document.getElementById('edit-purchase-date').value  = item.purchase_date  || '';
    document.getElementById('edit-notes').value          = item.notes          || '';
    document.getElementById('edit-msg').classList.add('d-none');
    bootstrap.Modal.getOrCreateInstance(document.getElementById('editCollModal')).show();
  });
}

async function updateCollItem() {
  const id = parseInt(document.getElementById('edit-id').value);
  const payload = {
    purchase_price: parseFloat(document.getElementById('edit-purchase-price').value) || null,
    current_value:  parseFloat(document.getElementById('edit-current-value').value)  || null,
    purchase_date:  document.getElementById('edit-purchase-date').value || null,
    notes:          document.getElementById('edit-notes').value.trim(),
  };
  try {
    const res  = await fetch(`/api/collection/${id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      bootstrap.Modal.getInstance(document.getElementById('editCollModal'))?.hide();
      showToast('Updated!', 'success');
      loadCollection();
    } else {
      const msg = document.getElementById('edit-msg');
      msg.className = 'alert alert-danger';
      msg.textContent = data.error || 'Update failed.';
      msg.classList.remove('d-none');
    }
  } catch (e) {
    showToast('Network error.', 'error');
  }
}

async function deleteCollItem(id) {
  if (!confirm('Remove this coin from your collection?')) return;
  try {
    await fetch(`/api/collection/${id}`, { method: 'DELETE' });
    showToast('Removed.', 'success');
    loadCollection();
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

function exportCSV() {
  window.location.href = '/api/collection/export-csv';
}

// ── Credentials modal ─────────────────────────────────────────────────────────

function openCredentials() {
  document.getElementById('cred-user').value = '';
  document.getElementById('cred-pass').value = '';
  document.getElementById('cred-msg').classList.add('d-none');
  bootstrap.Modal.getOrCreateInstance(document.getElementById('credModal')).show();
}
function togglePassVis() {
  const inp = document.getElementById('cred-pass');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}
async function saveCredentials() {
  const site     = document.getElementById('cred-site').value;
  const username = document.getElementById('cred-user').value.trim();
  const password = document.getElementById('cred-pass').value;
  if (!password) { showCredMsg('Password / API Key is required.', 'danger'); return; }
  try {
    const res  = await fetch('/api/credentials', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ site, username, password }),
    });
    const data = await res.json();
    if (res.ok) {
      showCredMsg('Saved securely.', 'success');
      document.getElementById('cred-pass').value = '';
      setTimeout(() => bootstrap.Modal.getInstance(document.getElementById('credModal'))?.hide(), 1200);
    } else {
      showCredMsg(data.error || 'Save failed.', 'danger');
    }
  } catch (e) {
    showCredMsg('Network error.', 'danger');
  }
}
async function deleteCredentials() {
  const site = document.getElementById('cred-site').value;
  if (!confirm(`Delete credentials for ${site}?`)) return;
  try {
    const res  = await fetch(`/api/credentials/${encodeURIComponent(site)}`, { method: 'DELETE' });
    const data = await res.json();
    showCredMsg(res.ok ? 'Deleted.' : (data.error || 'Delete failed.'), res.ok ? 'success' : 'danger');
  } catch (e) {
    showCredMsg('Network error.', 'danger');
  }
}
function showCredMsg(msg, type) {
  const el = document.getElementById('cred-msg');
  el.className = `alert alert-${type}`;
  el.textContent = msg;
  el.classList.remove('d-none');
}

// ── Utility ───────────────────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  refreshPrices();
});
