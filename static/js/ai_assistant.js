// Page-specific JS for ai_assistant.html
(function () {
  // Check if there is a session_id in URL to load
  document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const sessId = params.get('session_id');
    if (sessId) {
      window.loadSession(sessId);
      // Remove param to clean URL
      window.history.replaceState({}, document.title, "/chat");
    }
  });

  window.loadSession = function (id) {
    // Switch to chat view
    const w = document.getElementById('welcome-state');
    if (w) w.classList.add('hidden');

    const c = document.getElementById('chat-interface');
    if (c) {
      c.classList.remove('hidden');
      setTimeout(() => c.classList.remove('opacity-0'), 50);
    }

    document.getElementById('active-session-title').textContent = "Chat Session " + id;
    document.getElementById('messages-container').innerHTML = ''; // Start fresh or fetch details
    // fetch(`/api/sessions/${id}/messages`) ...
  };

  function handleHookButtonClick() { window.openMergePanel?.(); }
  window.handleHookButtonClick = handleHookButtonClick;

  window.attemptNewChat = function () {
    // Logic for top-right "New Chat" button
    // Should create in active folder or prompt? Default to first available folder?
    // We can access currentFolders from global scope? No, encapsulated.
    // We can expose currentFolders or just make a new session in "New Research" folder if needed.
    // For now, simple toast.
    window.showToast('Select a folder from sidebar to create new chat');
  };

  window.toggleChatModelSelect = function (id) { const opt = document.getElementById(id + '-options'); if (opt) opt.classList.toggle('show'); };
  window.selectCustomOption = function (value, text, inputId, changeCb) { const hidden = document.getElementById(inputId); const trigger = document.getElementById(inputId + '-trigger-text'); if (hidden) hidden.value = value; if (trigger) trigger.textContent = text; const opts = document.getElementById(inputId + '-options'); if (opts) opts.classList.remove('show'); if (changeCb && typeof window[changeCb] === 'function') window[changeCb](value); };
  window.setMode = function (mode) { document.getElementById('mode-normal')?.classList.toggle('text-white', mode === 'normal'); document.getElementById('mode-deep')?.classList.toggle('text-white', mode === 'deep_dive'); showToast('Mode: ' + mode); };
  window.toggleRecording = function () { showToast('Toggle recording (stub)'); };

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    form?.addEventListener('submit', function (e) {
      e.preventDefault();
      window.showToast('Message sent (stub)');
    });
  });

})();
