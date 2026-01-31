(function () {
    const body = document.body;
    const THEME_KEY = 'sf_theme';
    let _confirmCb = null;  // For custom confirm modal

    function byId(id) { return document.getElementById(id); }

    function initTheme() {
        const saved = localStorage.getItem(THEME_KEY) || 'default';
        applyTheme(saved);
    }

    function applyTheme(name) {
        body.classList.remove('theme-dark', 'theme-tokyo');
        if (name === 'dark') body.classList.add('theme-dark');
        else if (name === 'light') { }
        else { body.classList.add('theme-tokyo'); }
        localStorage.setItem(THEME_KEY, name);
    }

    window.setTheme = function (name) { applyTheme(name); showToast('Theme set to ' + name); };

    window.toggleDropdown = function (id) {
        const el = byId(id);
        if (!el) return;
        const key = el.classList.contains('show');
        closeAllDropdowns();
        if (!key) el.classList.add('show');
    };
    window.closeAllDropdowns = function () { document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show')); };

    window.toggleHistory = function () { const p = byId('history-panel'); if (!p) return; p.classList.toggle('-translate-x-full'); };

    window.toggleHookPanel = function () { const p = byId('hook-panel'); if (!p) return; if (p.style.transform === 'translateX(0%)') { p.style.transform = 'translateX(100%)'; } else { p.style.transform = 'translateX(0%)'; if (window.fetchHooks) window.fetchHooks(); } };

    function showModal(id) { const m = byId(id); if (m) { m.classList.add('active'); if (id === 'folder-modal') setTimeout(() => byId('fm-input')?.focus(), 100); } }
    function hideModal(id) { const m = byId(id); if (m) { m.classList.remove('active'); } }
    window.openFolderModal = function () { showModal('folder-modal'); }
    window.closeFolderModal = function () { hideModal('folder-modal'); }
    window.openSettingsModal = function () { showModal('settings-modal'); }
    window.closeSettingsModal = function () { hideModal('settings-modal'); }

    let toastTimer = null;
    window.showToast = function (msg, timeout = 2500) {
        console.log('Toast suppressed:', msg);
    };
    window.hideToast = function () { };

    let currentFolders = [];

    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        fetchFolders();

        // Attach confirm modal event listeners
        byId('btn-cancel-confirm')?.addEventListener('click', () => {
            hideModal('confirm-modal');
            _confirmCb = null;
        });

        byId('btn-do-confirm')?.addEventListener('click', () => {
            hideModal('confirm-modal');
            if (typeof _confirmCb === 'function') _confirmCb();
            _confirmCb = null;
        });
    });

    window.submitFolderCreation = async function () {
        const input = byId('fm-input');
        const name = (input?.value || '').trim();
        if (!name) { showToast('Please enter a folder name'); return; }

        try {
            const res = await fetch('/api/folders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast('Created project: ' + name);
                closeFolderModal();
                input.value = '';
                await createSession(data.folder.id, "New Research", true);
            } else {
                showToast(data.error || 'Failed to create folder');
            }
        } catch (e) {
            console.error(e);
            showToast('Error creating folder');
        }
    };

    async function fetchFolders() {
        try {
            const res = await fetch('/api/folders');
            currentFolders = await res.json();
            renderFolderTree();

            // Check if we need to reset to welcome state (only on chat page)
            if (window.resetToWelcomeState && typeof window.resetToWelcomeState === 'function') {
                const currentSessionId = localStorage.getItem('currentChatSessionId');
                if (currentSessionId) {
                    let sessionExists = false;
                    // Deep search for session in folders
                    for (const folder of currentFolders) {
                        if (folder.sessions && folder.sessions.some(s => s.id.toString() === currentSessionId.toString())) {
                            sessionExists = true;
                            break;
                        }
                    }

                    if (!sessionExists) {
                        window.resetToWelcomeState();
                        showToast('Session closed or deleted');
                    }
                } else {
                    // No session selected, ensure we are in welcome state
                    // This handles the case where user manually cleared storage or landed on page fresh
                    const welcome = document.getElementById('welcome-state');
                    if (welcome && welcome.classList.contains('hidden')) {
                        window.resetToWelcomeState();
                    }
                }
            }
        } catch (e) { console.error('Error fetching folders:', e); }
    }
    window.refreshFolders = fetchFolders;

    function renderFolderTree() {
        const container = byId('folder-tree-container');
        if (!container) return;

        container.classList.remove('hidden');
        container.innerHTML = '';

        if (currentFolders.length === 0) return;

        currentFolders.forEach(folder => {
            const folderEl = document.createElement('div');
            folderEl.className = 'mb-1';

            const header = document.createElement('div');
            header.className = 'group flex items-center justify-between px-3 py-2 hover:bg-[var(--hover-bg)] rounded-lg cursor-pointer transition-colors';

            header.onclick = (e) => {
                if (!e.target.closest('.folder-action')) toggleFolder(folder.id);
            };

            header.innerHTML = `
                <div class="flex items-center gap-2 overflow-hidden">
                    <svg id="arrow-${folder.id}" class="w-3 h-3 text-[var(--text-muted)] transition-transform duration-200 transform -rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                    <span class="text-sm font-medium text-[var(--text-main)] whitespace-nowrap overflow-hidden text-ellipsis">${folder.name}</span>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="createSession(${folder.id}, 'New Chat')" class="folder-action p-1 hover:bg-blue-100 text-[var(--text-muted)] hover:text-blue-600 rounded" title="New Chat">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    </button>
                    <button onclick="showFolderOptions(event, ${folder.id}, '${folder.name}')" class="folder-action p-1 hover:bg-gray-200 text-[var(--text-muted)] rounded" title="Options">
                         <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path></svg>
                    </button>
                </div>
            `;

            const children = document.createElement('div');
            children.id = `folder-content-${folder.id}`;
            children.className = 'hidden ml-3 border-l border-[var(--border-color)] mt-1 space-y-0.5';

            folder.sessions.forEach(session => {
                const sessEl = document.createElement('div');
                sessEl.className = 'group flex items-center justify-between px-3 py-1.5 hover:bg-[var(--hover-bg)] rounded-r-lg cursor-pointer text-xs text-[var(--text-muted)] hover:text-[var(--text-main)]';
                sessEl.onclick = (e) => {
                    if (!e.target.closest('.sess-action')) loadSessionGlobal(session.id);
                };

                sessEl.innerHTML = `
                    <span class="truncate pr-2">${session.title}</span>
                    <button onclick="showSessionOptions(event, ${session.id}, '${session.title}')" class="sess-action opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-200 rounded">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path></svg>
                    </button>
                `;
                children.appendChild(sessEl);
            });

            folderEl.appendChild(header);
            folderEl.appendChild(children);
            container.appendChild(folderEl);
        });
    }

    window.toggleFolder = function (id) {
        const content = byId(`folder-content-${id}`);
        const arrow = byId(`arrow-${id}`);
        if (content.classList.contains('hidden')) {
            content.classList.remove('hidden');
            arrow.classList.remove('-rotate-90');
        } else {
            content.classList.add('hidden');
            arrow.classList.add('-rotate-90');
        }
    };

    window.createSession = async function (folderId, title = "New Chat", redirect = false) {
        try {
            const res = await fetch('/api/sessions', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_id: folderId, title: title })
            });
            const data = await res.json();
            if (data.status === 'success') {
                await fetchFolders();
                if (redirect || window.location.pathname === '/chat') {
                    if (window.loadSession) window.loadSession(data.session.id);
                    else window.location.href = '/chat?session_id=' + data.session.id;
                } else {
                    window.location.href = '/chat';
                }

                setTimeout(() => {
                    const content = byId(`folder-content-${folderId}`);
                    if (content && content.classList.contains('hidden')) toggleFolder(folderId);
                }, 100);
            }
        } catch (e) { console.error(e); }
    };

    window.loadSessionGlobal = function (id) {
        if (window.location.pathname.includes('/chat')) {
            if (window.loadSession) window.loadSession(id);
        } else {
            window.location.href = '/chat?session_id=' + id;
        }
    };

    window.showFolderOptions = function (e, id, name) {
        e.stopPropagation();
        showContextMenu(e.clientX, e.clientY, [
            { label: 'Rename', action: () => promptRenameFolder(id, name) },
            { label: 'Delete', action: () => confirmDeleteFolder(id) }
        ]);
    };

    window.showSessionOptions = function (e, id, name) {
        e.stopPropagation();
        showContextMenu(e.clientX, e.clientY, [
            { label: 'Rename', action: () => promptRenameSession(id, name) },
            { label: 'Delete', action: () => confirmDeleteSession(id) }
        ]);
    };

    function showContextMenu(x, y, options) {
        const existing = document.getElementById('custom-context-menu');
        if (existing) existing.remove();

        const menu = document.createElement('div');
        menu.id = 'custom-context-menu';
        menu.className = 'fixed bg-[var(--bg-panel)] border border-[var(--border-color)] shadow-xl rounded-lg z-[1000] py-1 w-32';
        menu.style.left = x + 'px';
        menu.style.top = y + 'px';

        options.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'px-4 py-2 text-xs text-[var(--text-main)] hover:bg-[var(--hover-bg)] cursor-pointer';
            item.textContent = opt.label;
            item.onclick = () => { opt.action(); menu.remove(); };
            menu.appendChild(item);
        });

        document.body.appendChild(menu);
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 10);
    }

    // Custom themed confirm dialog
    function showConfirm(title, msg, cb) {
        const t = byId('confirm-title');
        const m = byId('confirm-msg');
        if (t) t.textContent = title || 'Are you sure?';
        if (m) m.textContent = msg || 'This action cannot be undone.';
        _confirmCb = cb;
        showModal('confirm-modal');
    }

    function promptRenameFolder(id, oldName) {
        const n = prompt("Rename Folder", oldName);
        if (n && n !== oldName) {
            fetch(`/api/folders/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_name: n }) })
                .then(fetchFolders);
        }
    }
    function confirmDeleteFolder(id) {
        showConfirm("Delete Project", "Delete this folder and all its chats? This cannot be undone.", () => {
            fetch(`/api/folders/${id}`, { method: 'DELETE' }).then(fetchFolders);
        });
    }
    function promptRenameSession(id, oldName) {
        const n = prompt("Rename Chat", oldName);
        if (n && n !== oldName) {
            fetch(`/api/sessions/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_name: n }) })
                .then(fetchFolders);
        }
    }
    function confirmDeleteSession(id) {
        showConfirm("Delete Chat", "Delete this chat? This cannot be undone.", () => {
            fetch(`/api/sessions/${id}`, { method: 'DELETE' }).then(fetchFolders);
        });
    }

    // ============================================
    // MERGE PANEL FUNCTIONS
    // ============================================

    let currentMergeReportId = null;

    window.openMergePanel = function () {
        showModal('merge-panel');
        loadMergeReports();
        loadMergeHooks();
    };

    window.closeMergePanel = function () {
        hideModal('merge-panel');
        currentMergeReportId = null;
        byId('merge-report-content').value = '';
        byId('merge-report-title').textContent = '';
    };

    async function loadMergeReports() {
        const container = byId('merge-report-list');
        if (!container) return;

        try {
            const res = await fetch('/api/history');
            const reports = await res.json();

            if (!reports || reports.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-6">
                        <svg class="w-8 h-8 mx-auto text-[var(--text-muted)] opacity-50 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <p class="text-xs text-[var(--text-muted)]">No reports</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = reports.map(report => `
                <button onclick="selectMergeReport(${report.id}, '${escapeAttr(report.topic)}')" 
                    class="merge-report-item w-full text-left p-2 rounded-lg text-xs hover:bg-[var(--hover-bg)] transition-colors truncate ${currentMergeReportId === report.id ? 'bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]' : 'text-[var(--text-main)]'}"
                    title="${escapeAttr(report.topic)}">
                    ${escapeHtml(report.topic)}
                </button>
            `).join('');
        } catch (e) {
            console.error('Failed to load merge reports', e);
            container.innerHTML = '<div class="text-xs text-red-400 p-2">Failed to load</div>';
        }
    }

    window.selectMergeReport = async function (id, topic) {
        currentMergeReportId = id;
        byId('merge-report-title').textContent = topic;

        // Highlight selected report
        document.querySelectorAll('.merge-report-item').forEach(el => {
            el.classList.remove('bg-[var(--accent-primary)]/10', 'text-[var(--accent-primary)]');
            el.classList.add('text-[var(--text-main)]');
        });
        const selectedBtn = document.querySelector(`.merge-report-item[onclick*="selectMergeReport(${id}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('bg-[var(--accent-primary)]/10', 'text-[var(--accent-primary)]');
            selectedBtn.classList.remove('text-[var(--text-main)]');
        }

        // Load report content
        const contentArea = byId('merge-report-content');
        contentArea.value = 'Loading...';

        try {
            const res = await fetch(`/api/report/${id}`);
            const data = await res.json();
            contentArea.value = data.content || '';
        } catch (e) {
            console.error('Failed to load report content', e);
            contentArea.value = 'Failed to load report content';
        }
    };

    async function loadMergeHooks() {
        const container = byId('merge-hooks-list');
        if (!container) return;

        try {
            const res = await fetch('/api/hooks');
            const hooks = await res.json();

            if (!hooks || hooks.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8">
                        <svg class="w-10 h-10 mx-auto text-[var(--text-muted)] opacity-50 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                        </svg>
                        <p class="text-sm text-[var(--text-muted)]">No hooks saved</p>
                        <p class="text-xs text-[var(--text-muted)] mt-1">Select text in chat and click Hook</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = hooks.map(hook => `
                <div class="hook-merge-item group bg-[var(--bg-panel)] border border-[var(--border-color)] rounded-lg p-3 hover:border-[var(--accent-primary)] transition-colors">
                    <p class="text-sm text-[var(--text-main)] mb-3 line-clamp-4">${escapeHtml(hook.content)}</p>
                    <div class="flex items-center justify-between">
                        <span class="text-xs text-[var(--text-muted)]">${hook.date || ''}</span>
                        <button onclick="smartPushHook(${hook.id}, \`${escapeAttr(hook.content)}\`)" 
                            class="px-3 py-1.5 text-xs font-medium bg-gradient-to-r from-purple-500 to-indigo-500 hover:opacity-90 text-white rounded-lg shadow-sm transition-all flex items-center gap-1.5"
                            title="Smart Push: AI will intelligently merge this hook into the report">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                            Smart Push
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Failed to load merge hooks', e);
            container.innerHTML = '<div class="text-xs text-red-400 p-2">Failed to load hooks</div>';
        }
    }

    window.saveMergeReport = async function () {
        if (!currentMergeReportId) {
            showToast('Please select a report first');
            return;
        }

        const content = byId('merge-report-content').value;

        try {
            const res = await fetch(`/api/report/${currentMergeReportId}/content`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            });

            if (res.ok) {
                showToast('Report saved successfully');
            } else {
                showToast('Failed to save report');
            }
        } catch (e) {
            console.error('Failed to save report', e);
            showToast('Error saving report');
        }
    };

    window.smartPushHook = async function (hookId, hookContent) {
        if (!currentMergeReportId) {
            showToast('Please select a report first');
            return;
        }

        const contentArea = byId('merge-report-content');
        const reportContent = contentArea.value;

        if (!reportContent || reportContent === 'Loading...') {
            showToast('Please wait for report to load');
            return;
        }

        // Show loading state
        const originalContent = contentArea.value;
        contentArea.value = 'AI is merging the hook into your report...';
        contentArea.disabled = true;

        try {
            const res = await fetch('/api/merge-hook', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_content: reportContent,
                    hook_content: hookContent
                })
            });

            const data = await res.json();

            if (data.status === 'success' && data.merged_content) {
                contentArea.value = data.merged_content;
                showToast('Hook merged successfully! Don\'t forget to save.');
            } else {
                contentArea.value = originalContent;
                showToast(data.error || 'Failed to merge hook');
            }
        } catch (e) {
            console.error('Smart push error:', e);
            contentArea.value = originalContent;
            showToast('Error merging hook');
        } finally {
            contentArea.disabled = false;
        }
    };

    // Helper functions
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        if (!text) return '';
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/`/g, '\\`');
    }

    // Add Escape key handler
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllDropdowns();
            hideModal('settings-modal');
            hideModal('folder-modal');
            hideModal('merge-panel');
            hideModal('confirm-modal');
        }
    });

})();
