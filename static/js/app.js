/* ── Collectorly Numismatics — Web UI JS ──────────────────────────────────── */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────

let _lastIdentification = null;  // stores last AI result for quick lookups

// ── Tab routing ───────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-tabs .nav-link').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-tabs .nav-link').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const id = 'tab-' + btn.dataset.tab;
    document.getElementById(id)?.classList.add('active');
  });
});

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(msg, type = 'info') {
  const el = document.getElementById('main-toast');
  const body = document.getElementById('toast-msg');
  el.className = `toast align-items-center text-bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'secondary'} border-0`;
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
        <span class="metal-val">$${Number(val).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
      </div>
    `).join('');
    container.innerHTML = html || '<span class="text-muted small">No price data</span>';
  } catch (e) {
    container.innerHTML = '<span class="text-warning small">Price fetch failed</span>';
  }
}

// ── Image upload & identify ───────────────────────────────────────────────────

const dropZone  = document.getElementById('drop-zone');
const fileInput = document.getElementById('coin-file');
const previewImg = document.getElementById('preview-img');
const dropHint  = document.getElementById('drop-hint');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setPreview(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setPreview(fileInput.files[0]);
});

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
  // Reset results
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

  // Confidence badge
  const conf = parseFloat(id.confidence) || 0;
  const pct  = Math.round(conf * 100);
  const cls  = conf >= 0.75 ? 'badge-high' : conf >= 0.5 ? 'badge-medium' : 'badge-low';
  const badge = document.getElementById('confidence-badge');
  badge.textContent = `${pct}% confidence`;
  badge.className = `badge ${cls}`;

  // Key features
  if (id.key_features?.length) {
    document.getElementById('id-fields').insertAdjacentHTML('beforeend', `
      <div class="col-12">
        <div class="id-field">
          <div class="label">Key Features</div>
          <div class="value">${id.key_features.map(f => `<span class="badge bg-light text-dark me-1 mb-1">${escHtml(f)}</span>`).join('')}</div>
        </div>
      </div>
    `);
  }

  // Catalog matches
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

function openQuickModal(title) {
  document.getElementById('quick-modal-title').textContent = title;
  document.getElementById('quick-body').innerHTML = '';
  document.getElementById('quick-loading').classList.remove('d-none');
  bootstrap.Modal.getOrCreateInstance(document.getElementById('quickModal')).show();
}

async function _doQuickFetch(url, body, renderer) {
  try {
    const res  = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    document.getElementById('quick-loading').classList.add('d-none');
    document.getElementById('quick-body').innerHTML = renderer(data);
  } catch (e) {
    document.getElementById('quick-loading').classList.add('d-none');
    document.getElementById('quick-body').innerHTML = `<div class="alert alert-danger">${escHtml(e.message)}</div>`;
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
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
  if (data.error && !Object.keys(data.populations || {}).length) {
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  }
  const pops = data.populations || {};
  if (!Object.keys(pops).length) {
    return '<p class="text-muted mb-0">No population data found.</p>';
  }
  return `<div class="table-scroll"><table class="data-table">
    <thead><tr><th>Grade</th><th>Population</th></tr></thead>
    <tbody>${Object.entries(pops).map(([g, p]) => `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}</tbody>
  </table></div>` + (data.error ? `<p class="text-muted small mt-2 mb-0">${escHtml(data.error)}</p>` : '');
}

// ── PCGS tab ──────────────────────────────────────────────────────────────────

async function fetchPCGSPrice() {
  const name = document.getElementById('pcgs-name').value.trim();
  const year = document.getElementById('pcgs-year').value.trim();
  const mint = document.getElementById('pcgs-mint').value.trim();
  if (!name) { showToast('Coin name required', 'error'); return; }
  document.getElementById('pcgs-results').classList.add('d-none');
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
  } catch (e) {
    document.getElementById('pcgs-loading').classList.add('d-none');
    showToast('Error: ' + e.message, 'error');
  }
}

function renderPCGSPriceData(data) {
  if (data.error && !Object.keys(data.prices || {}).length) {
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  }
  const prices = { ...data.prices };
  const coinName = prices.__coin__ || '';
  delete prices.__coin__;
  if (!Object.keys(prices).length) {
    return '<p class="text-muted mb-0">No price data found.</p>';
  }
  return (coinName ? `<p class="fw-semibold mb-2">${escHtml(coinName)}</p>` : '') +
    `<div class="table-scroll"><table class="data-table">
      <thead><tr><th>Grade</th><th>Price</th></tr></thead>
      <tbody>${Object.entries(prices).map(([g, p]) => `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}</tbody>
    </table></div>`;
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
  if (data.error && !Object.keys(data.populations || {}).length) {
    return `<div class="alert alert-warning mb-0">${escHtml(data.error)}</div>`;
  }
  const pops = data.populations || {};
  if (!Object.keys(pops).length) {
    return '<p class="text-muted mb-0">No population data found.</p>';
  }
  return `<div class="table-scroll"><table class="data-table">
    <thead><tr><th>Grade</th><th>Population</th></tr></thead>
    <tbody>${Object.entries(pops).map(([g, p]) => `<tr><td>${escHtml(g)}</td><td>${escHtml(String(p))}</td></tr>`).join('')}</tbody>
  </table></div>`;
}

// ── Cert lookup ───────────────────────────────────────────────────────────────

async function fetchNGCCert() {
  await _doCertFetch('/api/ngc-cert', 'NGC Certificate');
}

async function fetchPCGSCert() {
  await _doCertFetch('/api/pcgs-cert', 'PCGS Certificate');
}

async function _doCertFetch(url, title) {
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
  } catch (e) {
    document.getElementById('cert-loading').classList.add('d-none');
    showToast('Network error: ' + e.message, 'error');
  }
}

function renderCertData(data) {
  const fields  = data.data   || {};
  const images  = data.images || [];
  const hasData = Object.keys(fields).length > 0;

  // Error with no data
  if (data.error && !hasData) {
    return `<div class="alert alert-warning mb-0"><i class="bi bi-exclamation-triangle me-2"></i>${escHtml(data.error)}</div>`;
  }

  let html = '';

  // Coin images (obverse / reverse) — proxied server-side to bypass CDN hotlink blocks
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

  // "View on site" link
  if (data.url) {
    html += `<a href="${escHtml(data.url)}" target="_blank"
               class="btn btn-sm btn-outline-secondary mb-3">
               <i class="bi bi-box-arrow-up-right me-1"></i>View on site</a> `;
  }

  // Soft error (partial data returned)
  if (data.error && hasData) {
    html += `<div class="alert alert-warning py-1 small mb-2">${escHtml(data.error)}</div>`;
  }

  // Highlight key fields in chips
  const highlights = ['Coin','Grade','Year','Mint','Designation','Variety','Pop at Grade','Pop Finer','Price Guide'];
  const chips = highlights.filter(k => fields[k]);
  if (chips.length) {
    html += '<div class="d-flex gap-2 flex-wrap mb-3">';
    chips.forEach(k => {
      html += `<div class="id-field"><div class="label">${escHtml(k)}</div>
                <div class="value">${escHtml(fields[k])}</div></div>`;
    });
    html += '</div>';
  }

  // Full data table
  if (hasData) {
    const rest = Object.entries(fields).filter(([k]) => !chips.includes(k));
    if (rest.length) {
      html += `<table class="data-table"><tbody>${
        rest.map(([k, v]) =>
          `<tr><td class="fw-semibold" style="width:38%">${escHtml(k)}</td>
               <td>${escHtml(String(v))}</td></tr>`
        ).join('')
      }</tbody></table>`;
    }
  } else {
    html += '<p class="text-muted mb-0">No details returned.</p>';
  }

  return html;
}

// ── Credentials modal ─────────────────────────────────────────────────────────

function openCredentials() {
  document.getElementById('cred-user').value = '';
  document.getElementById('cred-pass').value = '';
  const msg = document.getElementById('cred-msg');
  msg.classList.add('d-none');
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
  const msg      = document.getElementById('cred-msg');

  if (!password) { showCredMsg('Password / API Key is required.', 'danger'); return; }

  try {
    const res  = await fetch('/api/credentials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    if (res.ok) {
      showCredMsg('Deleted.', 'success');
    } else {
      showCredMsg(data.error || 'Delete failed.', 'danger');
    }
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
