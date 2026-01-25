// Combined main.js + page-specific JS for report_generator.html (standalone)
(function () {
  const body = document.body;
  const THEME_KEY = 'sf_theme';

  function byId(id) { return document.getElementById(id); }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || 'default';
    applyTheme(saved);
  }

  function applyTheme(name) {
    body.classList.remove('theme-dark', 'theme-tokyo');
    if (name === 'dark') body.classList.add('theme-dark');
    else if (name === 'light') { /* default root variables are light */ }
    else { /* default -> tokyo */ body.classList.add('theme-tokyo'); }
    localStorage.setItem(THEME_KEY, name);
  }

  window.setTheme = function (name) { applyTheme(name); showToast('Theme set to ' + name); };

  // Dropdowns
  window.toggleDropdown = function (id) { const el = byId(id); if (!el) return; closeAllDropdowns(); el.classList.toggle('show'); };
  window.closeAllDropdowns = function () { document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show')); };

  // History panel
  // History panel
  window.toggleHistory = function () { const p = byId('history-panel'); if (!p) return; p.classList.toggle('-translate-x-full'); };

  // Hook panel
  window.toggleHookPanel = function () { const p = byId('hook-panel'); if (!p) return; if (p.style.transform === 'translateX(0%)') p.style.transform = 'translateX(100%)'; else p.style.transform = 'translateX(0%)'; };

  // Modals
  function showModal(id) { const m = byId(id); if (m) { m.classList.add('active'); } }
  function hideModal(id) { const m = byId(id); if (m) { m.classList.remove('active'); } }
  window.openFolderModal = function () { showModal('folder-modal'); }
  window.closeFolderModal = function () { hideModal('folder-modal'); }
  window.openSettingsModal = function () { showModal('settings-modal'); }
  window.closeSettingsModal = function () { hideModal('settings-modal'); }

  window.submitFolderCreation = function () { const val = (byId('fm-input') || { value: '' }).value.trim(); if (!val) { showToast('Please enter a folder name'); return; } showToast('Created folder: ' + val); closeFolderModal(); };

  // Confirm helper
  let _confirmCb = null;
  function showConfirm(title, msg, cb) { const t = byId('confirm-title'); const m = byId('confirm-msg'); t && (t.textContent = title || 'Are you sure?'); m && (m.textContent = msg || 'This action cannot be undone.'); _confirmCb = cb; showModal('confirm-modal'); }
  byId('btn-cancel-confirm')?.addEventListener('click', () => { hideModal('confirm-modal'); _confirmCb = null; });
  byId('btn-do-confirm')?.addEventListener('click', () => { hideModal('confirm-modal'); if (typeof _confirmCb === 'function') _confirmCb(); _confirmCb = null; });

  // History actions
  window.toggleSelectMode = function () { showToast('Toggled select mode'); };
  window.selectAllReports = function () { showToast('Selected all reports'); };
  window.deleteSelectedReports = function () { showConfirm('Delete reports', 'Delete selected reports?', () => showToast('Deleted selected reports')); };

  // Merge panel
  window.openMergePanel = function () { showModal('merge-panel'); };
  window.closeMergePanel = function () { hideModal('merge-panel'); };
  window.saveEditedReport = function () { showToast('Saved edited report'); };
  window.smartPushHooks = function () { showToast('Pushed hooks into report'); };
  window.deleteAllHooks = function () { showConfirm('Delete hooks', 'Delete all hooks?', () => showToast('All hooks deleted')); };

  // Toast
  let toastTimer = null;
  window.showToast = function (msg, timeout = 2500) { const t = byId('toast-notification'); const m = byId('toast-message'); if (!t || !m) return console.log('Toast:', msg); m.textContent = msg; t.classList.remove('translate-y-full'); t.style.transform = 'translateY(0)'; clearTimeout(toastTimer); toastTimer = setTimeout(() => { hideToast(); }, timeout); };
  window.hideToast = function () { const t = byId('toast-notification'); if (t) { t.style.transform = 'translateY(100%)'; } };

  // Danger action
  window.resetDatabase = function () { showConfirm('Reset Database', 'This will reset local database. Continue?', () => showToast('Database reset (stub)')); };

  // Global download
  window.triggerGlobalDownload = function (fmt) { const form = byId('dl-helper-form'); if (!form) { showToast('Download form not found'); return; } byId('hlp-format').value = fmt; byId('hlp-content').value = (document.querySelector('#merge-report-content') || { value: '' }).value; form.submit(); showToast('Preparing download: ' + fmt); hideGlobalMenu(); };
  window.hideGlobalMenu = function () { const g = byId('global-download-menu'); if (g) g.classList.add('hidden'); };

  // Misc
  document.addEventListener('click', (e) => { if (!e.target.closest('.dropdown-menu') && !e.target.closest('[onclick*="toggleDropdown"]')) closeAllDropdowns(); });
  document.addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); const btn = byId('sidebar-search-btn'); if (btn) btn.click(); } if (e.key === 'Escape') { closeAllDropdowns(); hideModal('settings-modal'); hideModal('folder-modal'); } });

  // Init
  document.addEventListener('DOMContentLoaded', () => { initTheme(); });

  // report page specific
  window.toggleCustomSelect = function (id) {
    const opts = document.getElementById(id + '-options');
    if (opts) opts.classList.toggle('hidden');
  };

  window.selectCustomOption = function (value, text, inputId, changeCb) {
    const hidden = document.getElementById(inputId);
    const trigger = document.getElementById(inputId + '-trigger-text');
    if (hidden) hidden.value = value;
    if (trigger) trigger.textContent = text;
    document.getElementById(inputId + '-options')?.classList.add('hidden');
    if (changeCb && typeof window[changeCb] === 'function') window[changeCb](value);
    else if (changeCb === 'handleFormatChange' && typeof handleFormatChange === 'function') handleFormatChange(value); // explicit check
  };

  window.handleFormatChange = function (val) {
    const el = document.getElementById('custom-format-container');
    if (val === 'custom') el?.classList.remove('hidden');
    else el?.classList.add('hidden');
  };

  window.updateFileName = function (el) {
    const fname = (el.files && el.files.length > 0) ? el.files[0].name : 'Upload Knowledge Base';
    const display = document.getElementById('file-name');
    if (display) display.textContent = fname;
  };

  window.copyToClipboard = function () { const text = document.getElementById('report-output')?.innerText || ''; navigator.clipboard?.writeText(text).then(() => showToast('Copied to clipboard')); };

  window.downloadFile = function (fmt) { showToast('Downloading ' + fmt + ' (stub)'); };

  window.resetView = function () {
    document.getElementById('report-output').innerHTML = '';
    document.getElementById('results-container')?.classList.add('hidden');
    document.getElementById('input-section')?.classList.remove('hidden');
    // Reset progress
    byId('progress-section')?.classList.add('hidden');
    document.querySelectorAll('.progress-step').forEach(el => { el.style.opacity = '0'; el.classList.remove('scale-100'); el.classList.add('scale-95'); });
    byId('progress-line-fill').style.height = '0';
    showToast('Ready for new report');
  };

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('report-form');
    form?.addEventListener('submit', function (e) {
      e.preventDefault();
      startResearchSequence();
    });

    // Click outside to close custom selects
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.relative.group')) {
        document.querySelectorAll('[id$="-options"]').forEach(el => el.classList.add('hidden'));
      }
    });
  });

  function startResearchSequence() {
    const form = document.getElementById('report-form');
    if (!form) return;

    const inputSec = document.getElementById('input-section');
    const progSec = document.getElementById('progress-section');
    const submitBtn = document.getElementById('submit-btn');

    if (!inputSec || !progSec) return showToast('Error: UI sections missing');

    // Lock UI
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.7'; }

    const formData = new FormData(form);

    // 1. Hide Input / Show Progress
    inputSec.classList.add('hidden');
    progSec.classList.remove('hidden');

    // Start initial animation
    document.getElementById('progress-line-fill').style.height = '10%';
    animateStep(1);

    // 2. Submit API
    fetch(window.START_REPORT_URL, {
      method: 'POST',
      body: formData
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) throw new Error(data.error);
        if (data.task_id) {
          pollTaskStatus(data.task_id);
        } else {
          throw new Error('No task ID returned');
        }
      })
      .catch(e => {
        console.error(e);
        showToast('Failed to start: ' + e.message);
        setTimeout(resetView, 2000);
      });
  }

  function animateStep(num) {
    // Reset all steps to low opacity first if needed, or just highlight current
    // Logic: Mark 1..num as active.
    const line = document.getElementById('progress-line-fill');
    if (line) line.style.height = (num * 25) + '%';

    for (let i = 1; i <= 4; i++) {
      const el = document.getElementById('step-' + i);
      if (!el) continue;

      const iconBox = el.querySelector('div');
      const txt = document.getElementById('step-' + i + '-text');

      if (i === num) {
        el.style.opacity = '1';
        el.classList.add('scale-100');
        el.classList.remove('scale-95');

        if (iconBox) {
          iconBox.classList.remove('bg-[var(--bg-panel)]', 'border-[var(--border-color)]');
          iconBox.classList.add('bg-blue-600', 'border-blue-600', 'text-white');
          const svg = iconBox.querySelector('svg');
          if (svg) svg.classList.remove('text-[var(--text-muted)]');
        }
        if (txt) txt.textContent = "Processing...";
      } else if (i < num) {
        // Completed steps
        el.style.opacity = '0.6';
        if (iconBox) {
          iconBox.classList.remove('bg-blue-600', 'border-blue-600', 'text-white');
          iconBox.classList.add('bg-green-600', 'border-green-600', 'text-white');
        }
        if (txt) txt.textContent = "Completed";
      }
    }
  }

  function pollTaskStatus(taskId) {
    const url = window.REPORT_STATUS_URL_TEMPLATE.replace('TASK_ID_PLACEHOLDER', taskId);

    fetch(url)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'SUCCESS') {
          animateStep(4);
          setTimeout(() => displayResults(data), 1000);
        } else if (data.status === 'FAILURE') {
          showToast('Error: ' + (data.error || 'Unknown error'));
          setTimeout(resetView, 3000);
        } else {
          // Parse status message to update step UI
          // Message usually formatted like "Step X/7: ..."
          const msg = data.message || '';
          if (msg.includes('Step 1') || msg.includes('Step 2')) animateStep(1);
          else if (msg.includes('Step 3') || msg.includes('Search')) animateStep(1); // Analysis
          else if (msg.includes('Step 4') || msg.includes('Visuals')) animateStep(2); // Planning/Visuals
          else if (msg.includes('Step 5') || msg.includes('Structure')) animateStep(2);
          else if (msg.includes('Step 6') || msg.includes('Writing')) animateStep(3); // Drafting
          else if (msg.includes('Step 7')) animateStep(4); // Finalizing

          // Correct active text
          const activeStep = document.querySelector('.scale-100.opacity-100 p.text-xs');
          if (activeStep) activeStep.textContent = msg.length > 50 ? msg.substring(0, 47) + '...' : msg;

          setTimeout(() => pollTaskStatus(taskId), 2000);
        }
      })
      .catch(e => {
        console.error(e);
        // Don't fail immediately on network blip
        setTimeout(() => pollTaskStatus(taskId), 3000);
      });
  }

  function displayResults(data) {
    const progSec = document.getElementById('progress-section');
    const resSec = document.getElementById('results-container');

    progSec.classList.add('hidden');
    if (resSec) {
      resSec.classList.remove('hidden');
      resSec.style.opacity = '0';
      setTimeout(() => resSec.style.opacity = '1', 50);

      let content = data.report_content || '';

      // Basic Markdown formatting
      // 1. Headers
      content = content.replace(/^# (.*$)/gim, '<h1>$1</h1>');
      content = content.replace(/^## (.*$)/gim, '<h2>$1</h2>');
      content = content.replace(/^### (.*$)/gim, '<h3>$1</h3>');
      // 2. Bold
      content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // 3. Lists
      content = content.replace(/^\* (.*$)/gim, '<ul><li>$1</li></ul>');
      content = content.replace(/<\/ul>\s*<ul>/g, ''); // Fix adjacent lists
      // 4. Newlines
      content = content.replace(/\n\n/g, '<br><br>');

      // Inject Chart if exists
      if (data.chart_path) {
        content = `<div class="mb-8 p-4 bg-white/5 rounded-xl border border-white/10 flex justify-center"><img src="/${data.chart_path}" class="max-w-full rounded-lg shadow-lg" alt="Analysis Chart"></div>` + content;
      }

      document.getElementById('report-output').innerHTML = content;
      document.getElementById('result-topic-display').textContent = document.getElementById('query').value;

      // Populate Hidden Form for Downloads
      document.getElementById('dl-content').value = data.report_content;
      document.getElementById('dl-topic').value = document.getElementById('query').value;
      document.getElementById('dl-format').value = document.getElementById('format-select').value; // fallback
      document.getElementById('dl-chart-path').value = data.chart_path || '';
    }
  }

  window.downloadFile = function (fmt) {
    const form = document.getElementById('download-form');
    if (form) {
      document.getElementById('dl-format').value = fmt;
      form.submit();
      showToast('Downloading ' + fmt.toUpperCase() + '...');
    }
  };

})();
