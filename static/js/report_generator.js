// Combined main.js + page-specific JS for report_generator.html (standalone)
(function () {
  const body = document.body;
  const THEME_KEY = 'sf_theme';

  function byId(id){ return document.getElementById(id); }

  function initTheme(){
    const saved = localStorage.getItem(THEME_KEY) || 'default';
    applyTheme(saved);
  }

  function applyTheme(name){
    body.classList.remove('theme-dark','theme-tokyo');
    if(name === 'dark') body.classList.add('theme-dark');
    else if(name === 'light') { /* default root variables are light */ }
    else { /* default -> tokyo */ body.classList.add('theme-tokyo'); }
    localStorage.setItem(THEME_KEY, name);
  }

  window.setTheme = function(name){ applyTheme(name); showToast('Theme set to ' + name); };

  // Dropdowns
  window.toggleDropdown = function(id){ const el = byId(id); if(!el) return; closeAllDropdowns(); el.classList.toggle('show'); };
  window.closeAllDropdowns = function(){ document.querySelectorAll('.dropdown-menu.show').forEach(d=>d.classList.remove('show')); };

  // History panel
  window.toggleHistory = function(){ const p = byId('history-panel'); if(!p) return; if(p.style.display === 'block' || p.style.transform === 'translateX(0%)'){ p.style.transform = 'translateX(100%)'; p.style.display = 'none'; } else { p.style.display = 'block'; p.style.transform = 'translateX(0%)'; } };

  // Hook panel
  window.toggleHookPanel = function(){ const p = byId('hook-panel'); if(!p) return; if(p.style.transform === 'translateX(0%)') p.style.transform = 'translateX(100%)'; else p.style.transform = 'translateX(0%)'; };

  // Modals
  function showModal(id){ const m = byId(id); if(m){ m.classList.add('active'); }}
  function hideModal(id){ const m = byId(id); if(m){ m.classList.remove('active'); }}
  window.openFolderModal = function(){ showModal('folder-modal'); }
  window.closeFolderModal = function(){ hideModal('folder-modal'); }
  window.openSettingsModal = function(){ showModal('settings-modal'); }
  window.closeSettingsModal = function(){ hideModal('settings-modal'); }

  window.submitFolderCreation = function(){ const val = (byId('fm-input')||{value:''}).value.trim(); if(!val){ showToast('Please enter a folder name'); return; } showToast('Created folder: '+val); closeFolderModal(); };

  // Confirm helper
  let _confirmCb = null;
  function showConfirm(title, msg, cb){ const t = byId('confirm-title'); const m = byId('confirm-msg'); t && (t.textContent = title || 'Are you sure?'); m && (m.textContent = msg || 'This action cannot be undone.'); _confirmCb = cb; showModal('confirm-modal'); }
  byId('btn-cancel-confirm')?.addEventListener('click', ()=>{ hideModal('confirm-modal'); _confirmCb = null; });
  byId('btn-do-confirm')?.addEventListener('click', ()=>{ hideModal('confirm-modal'); if(typeof _confirmCb === 'function') _confirmCb(); _confirmCb = null; });

  // History actions
  window.toggleSelectMode = function(){ showToast('Toggled select mode'); };
  window.selectAllReports = function(){ showToast('Selected all reports'); };
  window.deleteSelectedReports = function(){ showConfirm('Delete reports','Delete selected reports?', ()=> showToast('Deleted selected reports')); };

  // Merge panel
  window.openMergePanel = function(){ showModal('merge-panel'); };
  window.closeMergePanel = function(){ hideModal('merge-panel'); };
  window.saveEditedReport = function(){ showToast('Saved edited report'); };
  window.smartPushHooks = function(){ showToast('Pushed hooks into report'); };
  window.deleteAllHooks = function(){ showConfirm('Delete hooks','Delete all hooks?', ()=> showToast('All hooks deleted')); };

  // Toast
  let toastTimer = null;
  window.showToast = function(msg, timeout=2500){ const t = byId('toast-notification'); const m = byId('toast-message'); if(!t || !m) return console.log('Toast:', msg); m.textContent = msg; t.classList.remove('translate-y-full'); t.style.transform = 'translateY(0)'; clearTimeout(toastTimer); toastTimer = setTimeout(()=>{ hideToast(); }, timeout); };
  window.hideToast = function(){ const t = byId('toast-notification'); if(t){ t.style.transform = 'translateY(100%)'; }};

  // Danger action
  window.resetDatabase = function(){ showConfirm('Reset Database','This will reset local database. Continue?', ()=> showToast('Database reset (stub)')); };

  // Global download
  window.triggerGlobalDownload = function(fmt){ const form = byId('dl-helper-form'); if(!form){ showToast('Download form not found'); return; } byId('hlp-format').value = fmt; byId('hlp-content').value = (document.querySelector('#merge-report-content')||{value:''}).value; form.submit(); showToast('Preparing download: '+fmt); hideGlobalMenu(); };
  window.hideGlobalMenu = function(){ const g = byId('global-download-menu'); if(g) g.classList.add('hidden'); };

  // Misc
  document.addEventListener('click', (e)=>{ if(!e.target.closest('.dropdown-menu') && !e.target.closest('[onclick*="toggleDropdown"]')) closeAllDropdowns(); });
  document.addEventListener('keydown', (e)=>{ if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k'){ e.preventDefault(); const btn = byId('sidebar-search-btn'); if(btn) btn.click(); } if(e.key === 'Escape') { closeAllDropdowns(); hideModal('settings-modal'); hideModal('folder-modal'); } });

  // Init
  document.addEventListener('DOMContentLoaded', ()=>{ initTheme(); });

  // report page specific
  window.toggleCustomSelect = function(id){ document.getElementById(id + '-options')?.classList.toggle('show'); };

  window.selectCustomOption = function(value, text, inputId, changeCb){ const hidden = document.getElementById(inputId); const trigger = document.getElementById(inputId + '-trigger-text'); if(hidden) hidden.value = value; if(trigger) trigger.textContent = text; document.getElementById(inputId + '-options')?.classList.remove('show'); if(changeCb && typeof window[changeCb] === 'function') window[changeCb](value); };

  window.updateFileName = function(el){ const fname = (el.files && el.files.length>0) ? el.files[0].name : 'Upload PDFs'; const display = document.getElementById('file-name'); if(display) display.textContent = fname; };

  window.copyToClipboard = function(){ const text = document.getElementById('report-output')?.innerText || ''; navigator.clipboard?.writeText(text).then(()=> showToast('Copied to clipboard')); };

  window.downloadFile = function(fmt){ showToast('Downloading '+fmt+' (stub)'); };

  window.resetView = function(){ document.getElementById('report-output').innerHTML = ''; showToast('Ready for new report'); };

  document.addEventListener('DOMContentLoaded', ()=>{ const form = document.getElementById('report-form'); form?.addEventListener('submit', function(e){ e.preventDefault(); showToast('Running report sequence (stub)'); }); });

})();
