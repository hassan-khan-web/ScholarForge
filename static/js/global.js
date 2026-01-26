// Global JS for Sidebar, Modals, and Folder Logic
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

    // Dropdowns (Global close)
    window.toggleDropdown = function (id) {
        const el = byId(id);
        if (!el) return;
        const key = el.classList.contains('show');
        closeAllDropdowns();
        if (!key) el.classList.add('show');
    };
    window.closeAllDropdowns = function () { document.querySelectorAll('.dropdown-menu.show').forEach(d => d.classList.remove('show')); };

    // History panel (Legacy)
    window.toggleHistory = function () { const p = byId('history-panel'); if (!p) return; if (p.style.display === 'block' || p.style.transform === 'translateX(0%)') { p.style.transform = 'translateX(100%)'; p.style.display = 'none'; } else { p.style.display = 'block'; p.style.transform = 'translateX(0%)'; } };

    // Hook panel
    window.toggleHookPanel = function () { const p = byId('hook-panel'); if (!p) return; if (p.style.transform === 'translateX(0%)') { p.style.transform = 'translateX(100%)'; } else { p.style.transform = 'translateX(0%)'; } };

    // Modals
    function showModal(id) { const m = byId(id); if (m) { m.classList.add('active'); if (id === 'folder-modal') setTimeout(() => byId('fm-input')?.focus(), 100); } }
    function hideModal(id) { const m = byId(id); if (m) { m.classList.remove('active'); } }
    window.openFolderModal = function () { showModal('folder-modal'); }
    window.closeFolderModal = function () { hideModal('folder-modal'); }
    window.openSettingsModal = function () { showModal('settings-modal'); }
    window.closeSettingsModal = function () { hideModal('settings-modal'); }

    // Toast
    let toastTimer = null;
    window.showToast = function (msg, timeout = 2500) { const t = byId('toast-notification'); const m = byId('toast-message'); if (!t || !m) return console.log('Toast:', msg); m.textContent = msg; t.classList.remove('translate-y-full'); t.style.transform = 'translateY(0)'; clearTimeout(toastTimer); toastTimer = setTimeout(() => { hideToast(); }, timeout); };
    window.hideToast = function () { const t = byId('toast-notification'); if (t) { t.style.transform = 'translateY(100%)'; } };

    // FOLDER AND SESSION LOGIC
    let currentFolders = [];

    // Init Logic
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        fetchFolders(); // Load sidebar tree
    });

    // 1. Create Folder
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
                // Auto-create initial session
                await createSession(data.folder.id, "New Research", true);
                // Refresh tree is handled by createSession's success
            } else {
                showToast(data.error || 'Failed to create folder');
            }
        } catch (e) {
            console.error(e);
            showToast('Error creating folder');
        }
    };

    // 2. Fetch & Render Tree
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

            // Folder Header
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
        // If state is saved in localstorage, we can use that. For now default closed.
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
                    // If on chat page, load session
                    if (window.loadSession) window.loadSession(data.session.id);
                    else window.location.href = '/chat?session=' + data.session.id; // Or just /chat
                } else {
                    // Redirect to chat
                    window.location.href = '/chat';
                }

                // Auto-expand folder
                setTimeout(() => {
                    const content = byId(`folder-content-${folderId}`);
                    if (content && content.classList.contains('hidden')) toggleFolder(folderId);
                }, 100);
            }
        } catch (e) { console.error(e); }
    };

    // Global loadSession - if on another page, redirect. If on chat page, custom logic handles it.
    window.loadSessionGlobal = function (id) {
        if (window.location.pathname.includes('/chat')) {
            if (window.loadSession) window.loadSession(id);
        } else {
            // Store session ID to load? 
            // Simplified: Go to chat page. Chat page should default to latest or empty?
            // Let's pass query param
            window.location.href = '/chat?session_id=' + id;
        }
    };

    // Options Logic
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

    function promptRenameFolder(id, oldName) {
        const n = prompt("Rename Folder", oldName);
        if (n && n !== oldName) {
            fetch(`/api/folders/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_name: n }) })
                .then(fetchFolders);
        }
    }
    function confirmDeleteFolder(id) {
        if (confirm("Delete folder and all chats?")) {
            fetch(`/api/folders/${id}`, { method: 'DELETE' }).then(fetchFolders);
        }
    }
    function promptRenameSession(id, oldName) {
        const n = prompt("Rename Chat", oldName);
        if (n && n !== oldName) {
            fetch(`/api/sessions/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_name: n }) })
                .then(fetchFolders);
        }
    }
    function confirmDeleteSession(id) {
        if (confirm("Delete chat?")) {
            fetch(`/api/sessions/${id}`, { method: 'DELETE' }).then(fetchFolders);
        }
    }

})();
