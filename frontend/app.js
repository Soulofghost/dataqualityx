const API_BASE = '/api';

let currentDatasets = [];

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initModal();
  initDriftEvaluation();
  loadStats();
  loadDatasets();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const target = tab.dataset.tab === 'profiles' ? 'paneProfiles' :
                     tab.dataset.tab === 'assertions' ? 'paneAssertions' : 'paneDrift';
      document.getElementById(target)?.classList.add('active');
    });
  });
}

function initModal() {
  const modal = document.getElementById('uploadModal');
  const openBtn = document.getElementById('openUploadModal');
  const closeBtn = document.getElementById('closeUploadBtn');
  const cancelBtn = document.getElementById('cancelUploadBtn');
  const form = document.getElementById('uploadForm');

  openBtn?.addEventListener('click', () => modal.classList.add('active'));
  closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
  cancelBtn?.addEventListener('click', () => modal.classList.remove('active'));

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('dsName').value.trim();
    const description = document.getElementById('dsDesc').value.trim();

    try {
      const res = await fetch(`${API_BASE}/datasets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description })
      });

      if (!res.ok) throw new Error('Failed to profile dataset');
      const data = await res.json();
      modal.classList.remove('active');
      form.reset();
      await loadStats();
      await loadDatasets();
      document.getElementById('datasetSelect').value = data.id;
      renderDatasetDetail(data);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  });
}

function initDriftEvaluation() {
  const btn = document.getElementById('checkDriftBtn');
  btn?.addEventListener('click', async () => {
    const select = document.getElementById('datasetSelect');
    const dataset_name = select.options[select.selectedIndex]?.text.split(' (')[0] || 'Production User Stream';
    const rawJson = document.getElementById('schemaJsonInput').value.trim();

    let current_schema = {};
    try {
      current_schema = JSON.parse(rawJson);
    } catch (e) {
      alert('Invalid JSON in schema input.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/schema/drift`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_name, current_schema })
      });

      if (!res.ok) throw new Error('Drift assessment failed');
      const data = await res.json();
      renderDriftReport(data);
    } catch (err) {
      alert(err.message);
    }
  });
}

function renderDriftReport(data) {
  const badge = document.getElementById('driftBadge');
  const container = document.getElementById('driftResults');

  if (data.has_drift) {
    badge.innerText = 'DRIFT DETECTED';
    badge.className = 'badge badge-drift';

    let html = '<div style="color: var(--accent-red); margin-bottom: 1rem;">⚠️ Schema inconsistency identified against golden baseline.</div>';

    if (data.missing_columns && data.missing_columns.length > 0) {
      html += `<div><strong>Missing Expected Columns:</strong> <code class="text-mono">${data.missing_columns.join(', ')}</code></div>`;
    }
    if (data.unexpected_columns && data.unexpected_columns.length > 0) {
      html += `<div style="margin-top:0.5rem;"><strong>Unexpected New Columns:</strong> <code class="text-mono" style="color:var(--accent-amber);">${data.unexpected_columns.join(', ')}</code></div>`;
    }
    if (data.type_mismatches && data.type_mismatches.length > 0) {
      html += `<div style="margin-top:0.5rem;"><strong>Type Drift:</strong> ${data.type_mismatches.map(m => `<code>${m.column} (Expected: ${m.expected_type}, Actual: ${m.actual_type})</code>`).join(', ')}</div>`;
    }

    container.innerHTML = html;
  } else {
    badge.innerText = 'SCHEMA COMPLIANT';
    badge.className = 'badge badge-clean';
    container.innerHTML = `<div style="color: var(--accent-emerald);">✅ All columns match golden baseline types and definitions perfectly.</div>`;
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    document.getElementById('statDatasets').innerText = data.totalDatasets;
    document.getElementById('statHealthScore').innerText = `${data.averageHealthScore}%`;
    document.getElementById('statOutliers').innerText = data.columnsWithOutliers;
    document.getElementById('statFails').innerText = data.failedAssertionsCount;
  } catch (err) {
    console.warn('Failed to load stats', err);
  }
}

async function loadDatasets() {
  const select = document.getElementById('datasetSelect');
  try {
    const res = await fetch(`${API_BASE}/datasets`);
    const list = await res.json();
    currentDatasets = list || [];

    if (currentDatasets.length === 0) {
      const seed = await fetch(`${API_BASE}/datasets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Production User Stream', description: 'Seeded e-commerce transaction batch' })
      });
      if (seed.ok) return loadDatasets();
    }

    select.innerHTML = currentDatasets.map(d => `<option value="${d.id}">${escapeHtml(d.name)} (${d.row_count} rows, ${d.column_count} cols)</option>`).join('');

    select.onchange = () => loadDatasetDetail(select.value);
    if (currentDatasets.length > 0) {
      loadDatasetDetail(currentDatasets[0].id);
    }
  } catch (err) {
    select.innerHTML = `<option value="">Error loading datasets</option>`;
  }
}

async function loadDatasetDetail(id) {
  if (!id) return;
  try {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    const data = await res.json();
    renderDatasetDetail(data);
  } catch (err) {
    console.warn(err);
  }
}

function renderDatasetDetail(data) {
  document.getElementById('colCountBadge').innerText = `${data.column_count} Columns (${data.row_count} Rows)`;
  const healthBadge = document.getElementById('healthBadge');
  healthBadge.innerText = `HEALTH: ${data.health_score}%`;
  healthBadge.className = 'badge ' + (data.health_score >= 80 ? 'badge-pass' : 'badge-fail');

  const pBody = document.getElementById('profilesTableBody');
  pBody.innerHTML = data.profiles.map(p => `
    <tr>
      <td class="text-mono"><strong>${escapeHtml(p.column_name)}</strong></td>
      <td><span class="badge badge-info">${p.inferred_type}</span></td>
      <td><strong style="color: ${p.completeness_pct === 100 ? 'var(--accent-emerald)' : 'var(--accent-amber)'}">${p.completeness_pct}%</strong></td>
      <td>${p.null_count}</td>
      <td>${p.distinct_count}</td>
      <td class="text-mono">${p.min_val !== null ? escapeHtml(String(p.min_val)) : '--'}</td>
      <td class="text-mono">${p.max_val !== null ? escapeHtml(String(p.max_val)) : '--'}</td>
      <td>
        ${p.mean_val !== null ? `Mean: ${p.mean_val}` : '--'}
        ${p.outliers_count > 0 ? `<br><span class="badge badge-fail">${p.outliers_count} Outlier(s)</span>` : ''}
      </td>
    </tr>
  `).join('');

  const aBody = document.getElementById('assertionsTableBody');
  aBody.innerHTML = data.assertions.map(a => `
    <tr>
      <td><span class="badge ${a.passed ? 'badge-pass' : 'badge-fail'}">${a.passed ? 'PASSED' : 'FAILED'}</span></td>
      <td class="text-mono"><strong>${escapeHtml(a.assertion_type)}</strong></td>
      <td><code>${escapeHtml(a.column_name)}</code></td>
      <td class="text-mono" style="font-size:0.75rem;">${escapeHtml(a.parameters)}</td>
      <td style="color: ${a.passed ? 'var(--text-secondary)' : 'var(--accent-red)'}">${escapeHtml(a.message)}</td>
    </tr>
  `).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
