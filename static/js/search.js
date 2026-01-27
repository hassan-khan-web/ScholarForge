(function(){
    const body = document.body;
    const THEME_KEY = 'sf_theme';
    function byId(id){ return document.getElementById(id); }
    function initTheme(){ const saved = localStorage.getItem(THEME_KEY) || 'default'; applyTheme(saved); }
    function applyTheme(name){ body.classList.remove('theme-dark','theme-tokyo'); if(name === 'dark') body.classList.add('theme-dark'); else if(name === 'light') {} else { body.classList.add('theme-tokyo'); } localStorage.setItem(THEME_KEY, name); }
    window.setTheme = function(name){ applyTheme(name); showToast('Theme set to ' + name); };
    window.toggleDropdown = function(id){ const el = byId(id); if(!el) return; closeAllDropdowns(); el.classList.toggle('show'); };
    window.closeAllDropdowns = function(){ document.querySelectorAll('.dropdown-menu.show').forEach(d=>d.classList.remove('show')); };
    function showModal(id){ const m = byId(id); if(m){ m.classList.add('active'); }}
    function hideModal(id){ const m = byId(id); if(m){ m.classList.remove('active'); }}
    window.openFolderModal = function(){ showModal('folder-modal'); }
    window.closeFolderModal = function(){ hideModal('folder-modal'); }
    window.openSettingsModal = function(){ showModal('settings-modal'); }
    window.closeSettingsModal = function(){ hideModal('settings-modal'); }
    let _confirmCb = null;
    function showConfirm(title, msg, cb){ const t = byId('confirm-title'); const m = byId('confirm-msg'); t && (t.textContent = title || 'Are you sure?'); m && (m.textContent = msg || 'This action cannot be undone.'); _confirmCb = cb; showModal('confirm-modal'); }
    byId('btn-cancel-confirm')?.addEventListener('click', ()=>{ hideModal('confirm-modal'); _confirmCb = null; });
    byId('btn-do-confirm')?.addEventListener('click', ()=>{ hideModal('confirm-modal'); if(typeof _confirmCb === 'function') _confirmCb(); _confirmCb = null; });
    window.toggleSelectMode = function(){ showToast('Toggled select mode'); };
    window.selectAllReports = function(){ showToast('Selected all reports'); };
    window.deleteSelectedReports = function(){ showConfirm('Delete reports','Delete selected reports?', ()=> showToast('Deleted selected reports')); };
    window.openMergePanel = function(){ showModal('merge-panel'); };
    window.closeMergePanel = function(){ hideModal('merge-panel'); };
    window.saveEditedReport = function(){ showToast('Saved edited report'); };
    window.smartPushHooks = function(){ showToast('Pushed hooks into report'); };
    window.deleteAllHooks = function(){ showConfirm('Delete hooks','Delete all hooks?', ()=> showToast('All hooks deleted')); };
    let toastTimer = null;
    window.showToast = function(msg, timeout=2500){ const t = byId('toast-notification'); const m = byId('toast-message'); if(!t || !m) return console.log('Toast:', msg); m.textContent = msg; t.classList.remove('translate-y-full'); t.style.transform = 'translateY(0)'; clearTimeout(toastTimer); toastTimer = setTimeout(()=>{ hideToast(); }, timeout); };
    window.hideToast = function(){ const t = byId('toast-notification'); if(t){ t.style.transform = 'translateY(100%)'; }};
    window.resetDatabase = function(){ showConfirm('Reset Database','This will reset local database. Continue?', ()=> showToast('Database reset (stub)')); };
    window.triggerGlobalDownload = function(fmt){ const form = byId('dl-helper-form'); if(!form){ showToast('Download form not found'); return; } byId('hlp-format').value = fmt; byId('hlp-content').value = (document.querySelector('#merge-report-content')||{value:''}).value; form.submit(); showToast('Preparing download: '+fmt); hideGlobalMenu(); };
    window.hideGlobalMenu = function(){ const g = byId('global-download-menu'); if(g) g.classList.add('hidden'); };
    document.addEventListener('click', (e)=>{ if(!e.target.closest('.dropdown-menu') && !e.target.closest('[onclick*="toggleDropdown"]')) closeAllDropdowns(); });
    document.addEventListener('keydown', (e)=>{ if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k'){ e.preventDefault(); const btn = byId('sidebar-search-btn'); if(btn) btn.click(); } if(e.key === 'Escape') { closeAllDropdowns(); hideModal('settings-modal'); hideModal('folder-modal'); } });
    document.addEventListener('DOMContentLoaded', ()=>{ initTheme(); });
})();

let searchData = { reports: [], chats: [] };
let currentSearchTab = 'all';
let selectedSearchIndex = -1;
let filteredResults = [];

document.addEventListener('DOMContentLoaded', loadSearchData);

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        window.history.back();
    }
});

async function loadSearchData() {
    try {
        const container = document.getElementById('search-results');
        container.innerHTML = `
            <div class="text-center text-[var(--text-muted)] py-16">
                <div class="animate-pulse">
                    <div class="w-12 h-12 mx-auto mb-4 rounded-full bg-[var(--hover-bg)]"></div>
                    <p class="text-sm">Loading your data...</p>
                </div>
            </div>`;

        const reportsRes = await fetch('/api/history');
        const reports = await reportsRes.json();
        searchData.reports = reports.map(r => ({ id: r.id, type: 'report', title: r.topic || 'Untitled Report', date: r.date }));

        const contentPromises = searchData.reports.map(async (r) => {
            try {
                const contentRes = await fetch(`/api/report/${r.id}`);
                const content = await contentRes.json();
                r.preview = content.content ? content.content.substring(0, 150).replace(/[#*_`]/g, '') + '...' : '';
            } catch (e) { r.preview = ''; }
        });
        await Promise.all(contentPromises);

        const foldersRes = await fetch('/api/folders');
        const folders = await foldersRes.json();
        searchData.chats = [];
        folders.forEach(f => {
            if (f.sessions && f.sessions.length > 0) {
                f.sessions.forEach(s => {
                    searchData.chats.push({ id: s.id, type: 'chat', title: s.title || 'Untitled Chat', folder: f.name, date: s.created_at || null });
                });
            }
        });

        container.innerHTML = `
            <div class="text-center text-[var(--text-muted)] py-16">
                <svg class="w-16 h-16 mx-auto mb-4 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <h2 class="text-xl font-semibold text-[var(--text-main)] mb-2">Search ScholarForge</h2>
                <p class="text-sm">Find your reports and chat sessions quickly</p>
                <p class="text-xs mt-3 text-[var(--accent-primary)]">
                    ${searchData.reports.length} reports • ${searchData.chats.length} chats loaded
                </p>
            </div>`;

    } catch (err) {
        console.error('Failed to load search data:', err);
        document.getElementById('search-results').innerHTML = `<div class="text-center text-red-400 py-16"><p class="text-sm">Failed to load data. Please try refreshing.</p></div>`;
    }
}

function performSearch(query) {
    const q = query.trim().toLowerCase();
    let results = [];
    if (!q) {
        if (currentSearchTab === 'reports') results = [...searchData.reports];
        else if (currentSearchTab === 'chats') results = [...searchData.chats];
        else { renderSearchResults([]); return; }
    } else {
        if (currentSearchTab === 'all' || currentSearchTab === 'reports') {
            searchData.reports.forEach(r => { if (r.title.toLowerCase().includes(q) || (r.preview && r.preview.toLowerCase().includes(q))) results.push(r); });
        }
        if (currentSearchTab === 'all' || currentSearchTab === 'chats') {
            searchData.chats.forEach(c => { if (c.title.toLowerCase().includes(q) || (c.folder && c.folder.toLowerCase().includes(q))) results.push(c); });
        }
    }

    filteredResults = results;
    selectedSearchIndex = results.length > 0 ? 0 : -1;
    renderSearchResults(results, !q && currentSearchTab !== 'all');
}

function switchSearchTab(tab) {
    currentSearchTab = tab;
    document.querySelectorAll('.search-tab').forEach(t => { t.classList.remove('text-[var(--accent-primary)]','border-[var(--accent-primary)]'); t.classList.add('text-[var(--text-muted)]','border-transparent'); });
    const activeTab = document.getElementById(`search-tab-${tab}`);
    activeTab.classList.remove('text-[var(--text-muted)]','border-transparent');
    activeTab.classList.add('text-[var(--accent-primary)]','border-[var(--accent-primary)]');
    performSearch(document.getElementById('search-input').value);
}

function renderSearchResults(results, showAllMode = false) {
    const container = document.getElementById('search-results');
    if (results.length === 0) {
        const query = document.getElementById('search-input').value;
        if (query.trim()) {
            container.innerHTML = `<div class="text-center text-[var(--text-muted)] py-16"><svg class="w-12 h-12 mx-auto mb-4 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg><p class="text-lg font-medium text-[var(--text-main)]">No results found</p><p class="text-sm">Try different keywords or check another tab</p></div>`;
        } else if (showAllMode) {
            const categoryName = currentSearchTab === 'reports' ? 'reports' : 'chat sessions';
            container.innerHTML = `<div class="text-center text-[var(--text-muted)] py-16"><svg class="w-12 h-12 mx-auto mb-4 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg><p class="text-lg font-medium text-[var(--text-main)]">No ${categoryName} yet</p><p class="text-sm mt-1">Your ${categoryName} will appear here</p></div>`;
        } else {
            container.innerHTML = `<div class="text-center text-[var(--text-muted)] py-16"><svg class="w-16 h-16 mx-auto mb-4 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><h2 class="text-xl font-semibold text-[var(--text-main)] mb-2">Search ScholarForge</h2><p class="text-sm">Find your reports and chat sessions quickly</p></div>`;
        }
        return;
    }

    let headerText = `${results.length} result${results.length !== 1 ? 's' : ''} found`;
    if (showAllMode) {
        if (currentSearchTab === 'reports') headerText = `📄 All Reports (${results.length})`;
        else if (currentSearchTab === 'chats') headerText = `💬 All Chat Sessions (${results.length})`;
    }

    container.innerHTML = `<div class="text-sm font-medium text-[var(--text-main)] mb-4">${headerText}</div><div class="space-y-2">${results.map((r, idx) => `
        <div class="search-result-item ${idx === selectedSearchIndex ? 'selected' : ''}" onclick="selectSearchResult(${idx})" data-index="${idx}">
            <div class="flex items-start gap-4">
                <div class="mt-1 p-2 rounded-lg bg-[var(--hover-bg)]">${r.type === 'report' ? `<svg class="w-5 h-5 text-[var(--accent-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>` : `<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>`}</div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1"><span class="font-medium text-[var(--text-main)]">${r.title}</span><span class="text-xs px-2 py-0.5 rounded-full bg-[var(--hover-bg)] text-[var(--text-muted)]">${r.type === 'report' ? 'Report' : 'Chat'}</span></div>
                    ${r.preview ? `<p class="text-sm text-[var(--text-muted)] line-clamp-2">${r.preview}</p>` : ''}
                    ${r.folder ? `<p class="text-xs text-[var(--text-muted)] mt-1">📁 ${r.folder}</p>` : ''}
                    ${r.date ? `<p class="text-xs text-[var(--text-muted)] mt-1">${r.date}</p>` : ''}
                </div>
                <div class="text-[var(--text-muted)]"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg></div>
            </div>
        </div>
    `).join('')}</div>`;
}

function selectSearchResult(index) {
    const result = filteredResults[index]; if (!result) return;
    if (result.type === 'report') window.location.href = '/?show_report=' + result.id;
    else if (result.type === 'chat') window.location.href = `/chat?session_id=${result.id}`;
}

function handleSearchKeydown(e) {
    const items = document.querySelectorAll('.search-result-item'); if (items.length === 0) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); selectedSearchIndex = Math.min(selectedSearchIndex + 1, filteredResults.length - 1); updateSearchSelection(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); selectedSearchIndex = Math.max(selectedSearchIndex - 1, 0); updateSearchSelection(); }
    else if (e.key === 'Enter' && selectedSearchIndex >= 0) { e.preventDefault(); selectSearchResult(selectedSearchIndex); }
}

function updateSearchSelection() { document.querySelectorAll('.search-result-item').forEach((item, idx) => { item.classList.toggle('selected', idx === selectedSearchIndex); if (idx === selectedSearchIndex) item.scrollIntoView({ block: 'nearest' }); }); }
