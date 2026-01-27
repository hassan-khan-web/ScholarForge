// Combined main.js + minimal layout JS (standalone)
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

    window.toggleDropdown = function (id) { const el = byId(id); if (!el) return; closeAllDropdowns(); el.classList.toggle('show'); };
    window.closeAllDropdowns = function () { document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show')); };

    function showModal(id) { const m = byId(id); if (m) { m.classList.add('active'); } }
    function hideModal(id) { const m = byId(id); if (m) { m.classList.remove('active'); } }
    window.openFolderModal = function () { showModal('folder-modal'); }
    window.closeFolderModal = function () { hideModal('folder-modal'); }
    window.openSettingsModal = function () { showModal('settings-modal'); }
    window.closeSettingsModal = function () { hideModal('settings-modal'); }

    let _confirmCb = null;
    function showConfirm(title, msg, cb) { const t = byId('confirm-title'); const m = byId('confirm-msg'); t && (t.textContent = title || 'Are you sure?'); m && (m.textContent = msg || 'This action cannot be undone.'); _confirmCb = cb; showModal('confirm-modal'); }
    byId('btn-cancel-confirm')?.addEventListener('click', () => { hideModal('confirm-modal'); _confirmCb = null; });
    byId('btn-do-confirm')?.addEventListener('click', () => { hideModal('confirm-modal'); if (typeof _confirmCb === 'function') _confirmCb(); _confirmCb = null; });

    window.toggleSelectMode = function () { showToast('Toggled select mode'); };
    window.selectAllReports = function () { showToast('Selected all reports'); };
    window.deleteSelectedReports = function () { showConfirm('Delete reports', 'Delete selected reports?', () => showToast('Deleted selected reports')); };

    window.openMergePanel = function () { showModal('merge-panel'); };
    window.closeMergePanel = function () { hideModal('merge-panel'); };
    window.saveEditedReport = function () { showToast('Saved edited report'); };
    window.smartPushHooks = function () { showToast('Pushed hooks into report'); };
    window.deleteAllHooks = function () { showConfirm('Delete hooks', 'Delete all hooks?', () => showToast('All hooks deleted')); };

    let toastTimer = null;
    window.showToast = function (msg, timeout = 2500) {
        console.log('Toast suppressed (layout.js):', msg);
    };
    window.hideToast = function () { };

    window.resetDatabase = function () { showConfirm('Reset Database', 'This will reset local database. Continue?', () => showToast('Database reset (stub)')); };

    window.triggerGlobalDownload = function (fmt) { const form = byId('dl-helper-form'); if (!form) { showToast('Download form not found'); return; } byId('hlp-format').value = fmt; byId('hlp-content').value = (document.querySelector('#merge-report-content') || { value: '' }).value; form.submit(); showToast('Preparing download: ' + fmt); hideGlobalMenu(); };
    window.hideGlobalMenu = function () { const g = byId('global-download-menu'); if (g) g.classList.add('hidden'); };

    document.addEventListener('click', (e) => { if (!e.target.closest('.dropdown-menu') && !e.target.closest('[onclick*="toggleDropdown"]')) closeAllDropdowns(); });
    document.addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); const btn = byId('sidebar-search-btn'); if (btn) btn.click(); } if (e.key === 'Escape') { closeAllDropdowns(); hideModal('settings-modal'); hideModal('folder-modal'); } });

    // Folder & Chat Logic
    async function loadFolders() {
        const container = byId('folder-tree-container');
        if (!container) return;
        try {
            const res = await fetch('/api/folders');
            const folders = await res.json();
            renderFolders(folders);
        } catch (e) {
            console.error('Failed to load folders', e);
            container.innerHTML = '<div class="text-xs text-red-400 pl-5">Failed to load folders</div>';
        }
    }

    function renderFolders(folders) {
        const container = byId('folder-tree-container');
        if (!container) return;
        container.innerHTML = '';

        folders.forEach(folder => {
            // Folder Item
            const folderEl = document.createElement('div');
            folderEl.className = 'flex flex-col';

            const header = document.createElement('div');
            header.className = 'nav-item justify-between group';
            header.onclick = () => toggleFolder(folder.id);
            header.innerHTML = `
            <div class="flex items-center gap-2 overflow-hidden">
                <svg class="w-4 h-4 text-[var(--text-muted)] shrink-0 transition-transform ${folder.isOpen ? 'rotate-90' : ''}" id="arrow-${folder.id}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                <svg class="w-4 h-4 text-[var(--accent-primary)] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path></svg>
                <span class="nav-text text-sm truncate">${folder.name}</span>
            </div>
            <div class="opacity-0 group-hover:opacity-100 flex items-center gap-1 nav-text">
                <button onclick="event.stopPropagation(); createSession(${folder.id}, '${folder.name}')" class="p-1 hover:text-[var(--accent-primary)]" title="New Chat">+</button>
            </div>
          `;

            container.appendChild(header);

            // Sessions Container
            const sessContainer = document.createElement('div');
            sessContainer.id = `folder-content-${folder.id}`;
            sessContainer.className = `ml-6 flex flex-col border-l border-[var(--border-color)] pl-2 ${folder.isOpen ? '' : 'hidden'}`;

            if (folder.sessions && folder.sessions.length > 0) {
                folder.sessions.forEach(session => {
                    const sessEl = document.createElement('a');
                    sessEl.href = `/chat?session_id=${session.id}`;
                    sessEl.className = 'nav-item py-1.5 text-xs nav-text truncate block';
                    sessEl.innerText = session.title || 'Untitled Chat';
                    // Highlight active session if needed
                    const urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.get('session_id') == session.id) sessEl.classList.add('text-[var(--accent-primary)]', 'font-semibold');

                    sessContainer.appendChild(sessEl);
                });
            } else {
                sessContainer.innerHTML = '<div class="text-[10px] text-[var(--text-muted)] py-1 italic nav-text">No chats</div>';
            }
            container.appendChild(sessContainer);
        });
    }

    window.toggleFolder = function (id) {
        const content = byId(`folder-content-${id}`);
        const arrow = byId(`arrow-${id}`);
        if (content) content.classList.toggle('hidden');
        if (arrow) arrow.classList.toggle('rotate-90');
    }

    window.createSession = async function (folderId, folderName) {
        try {
            const title = prompt(`New chat in ${folderName}:`, "New Chat");
            if (!title) return;

            const res = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_id: folderId, title: title })
            });
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'success') {
                    window.location.href = `/chat?session_id=${data.session.id}`;
                }
            }
        } catch (e) { console.error(e); showToast('Failed to create session'); }
    }

    window.submitFolderCreation = async function () {
        const input = byId('fm-input');
        const val = (input || { value: '' }).value.trim();
        if (!val) { showToast('Please enter a folder name'); return; }

        try {
            const res = await fetch('/api/folders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: val })
            });
            if (res.ok) {
                showToast('Created folder: ' + val);
                closeFolderModal();
                input.value = '';
                loadFolders(); // Reload list
            } else {
                showToast('Failed to create folder');
            }
        } catch (e) {
            console.error(e);
            showToast('Error creating folder');
        }
    };

    window.loadFolders = loadFolders; // Export for external usage if needed

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        loadFolders();
        // Only attach if not using inline onclick, but we are using inline onclick for toggle
    });

})();
