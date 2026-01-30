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

    window.toggleHistory = function () { const p = byId('history-panel'); if (!p) return; if (p.style.display === 'block' || p.style.transform === 'translateX(0%)') { p.style.transform = 'translateX(100%)'; p.style.display = 'none'; } else { p.style.display = 'block'; p.style.transform = 'translateX(0%)'; } };

    window.toggleHookPanel = function () { const p = byId('hook-panel'); if (!p) return; if (p.style.transform === 'translateX(0%)') { p.style.transform = 'translateX(100%)'; } else { p.style.transform = 'translateX(0%)'; } };

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

})();
