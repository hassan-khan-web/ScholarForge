(function () {
  let currentSessionId = null;
  let hasMessages = false;
  let attachedFiles = [];

  document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const sessId = params.get('session_id');
    if (sessId) {
      window.loadSession(sessId);
      window.history.replaceState({}, document.title, "/chat");
    }

    initFileUpload();
    initChatForm();
  });

  function initFileUpload() {
    const fileInput = document.getElementById('file-upload');
    const previewArea = document.getElementById('file-preview-area');

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        files.forEach(file => {
          if (!attachedFiles.find(f => f.name === file.name)) {
            attachedFiles.push(file);
            addFilePreview(file, previewArea);
          }
        });
        fileInput.value = '';
      });
    }
  }

  function addFilePreview(file, container) {
    const chip = document.createElement('div');
    chip.className = 'file-chip flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-panel)] border border-[var(--border-color)] rounded-lg text-xs text-[var(--text-main)]';
    chip.innerHTML = `
      <svg class="w-3 h-3 text-[var(--accent-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
      </svg>
      <span class="max-w-[120px] truncate">${file.name}</span>
      <button type="button" class="remove-file p-0.5 hover:text-red-500 transition-colors">
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;

    chip.querySelector('.remove-file').addEventListener('click', () => {
      attachedFiles = attachedFiles.filter(f => f.name !== file.name);
      chip.remove();
    });

    container.appendChild(chip);
  }

  function initChatForm() {
    const form = document.getElementById('chat-form');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
      e.preventDefault();

      if (!currentSessionId) {
        window.showToast('Please select or create a chat session first');
        return;
      }

      const input = document.getElementById('chat-input');
      const message = (input?.value || '').trim();
      if (!message) return;

      const model = document.getElementById('model-select')?.value || 'default';
      const mode = document.getElementById('chat-mode')?.value || 'normal';

      input.value = '';
      input.disabled = true;
      document.getElementById('send-btn').disabled = true;

      renderUserMessage(message, attachedFiles.map(f => f.name));

      if (!hasMessages) {
        transitionInputToBottom();
        hasMessages = true;
      }

      showTypingIndicator();

      try {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('session_id', currentSessionId);
        formData.append('model', model);
        formData.append('mode', mode);

        attachedFiles.forEach(file => {
          formData.append('files', file);
        });

        const response = await fetch('/chat', {
          method: 'POST',
          body: formData
        });

        const data = await response.json();
        hideTypingIndicator();

        if (data.error) {
          renderAssistantMessage('Error: ' + data.error);
        } else {
          renderAssistantMessage(data.response);
        }

        attachedFiles = [];
        document.getElementById('file-preview-area').innerHTML = '';

      } catch (err) {
        hideTypingIndicator();
        renderAssistantMessage('Connection error. Please try again.');
        console.error('Chat error:', err);
      } finally {
        input.disabled = false;
        document.getElementById('send-btn').disabled = false;
        input.focus();
      }
    });
  }

  function renderUserMessage(text, fileNames = []) {
    const container = document.getElementById('messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';

    let filesHtml = '';
    if (fileNames.length > 0) {
      filesHtml = `<div class="text-xs text-blue-300 mt-2 flex flex-wrap gap-1">
        ${fileNames.map(n => `<span class="bg-blue-500/20 px-2 py-0.5 rounded">📎 ${n}</span>`).join('')}
      </div>`;
    }

    msgDiv.innerHTML = `
      <div class="message-bubble">
        <p class="message-text">${escapeHtml(text)}</p>
        ${filesHtml}
      </div>
    `;
    container.appendChild(msgDiv);
    scrollToBottom();
  }

  function renderAssistantMessage(text) {
    const container = document.getElementById('messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant-message';

    const formattedText = formatMarkdown(text);

    msgDiv.innerHTML = `
      <div class="message-bubble">
        <div class="message-text prose">${formattedText}</div>
      </div>
    `;
    container.appendChild(msgDiv);
    scrollToBottom();
  }

  function showTypingIndicator() {
    const container = document.getElementById('messages-container');
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
      <div class="typing-bubble">
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;
    container.appendChild(indicator);
    scrollToBottom();
  }

  function hideTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
  }

  function transitionInputToBottom() {
    const unitMsg = document.getElementById('unit-msg');
    if (unitMsg) {
      unitMsg.classList.remove('unit-msg-centered');
      unitMsg.classList.add('unit-msg-docked');
    }
  }

  function resetInputToCenter() {
    const unitMsg = document.getElementById('unit-msg');
    if (unitMsg) {
      unitMsg.classList.remove('unit-msg-docked');
      unitMsg.classList.add('unit-msg-centered');
    }
  }

  function scrollToBottom() {
    const container = document.getElementById('messages-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/^### (.+)$/gm, '<h3 class="font-bold text-base mt-3 mb-1">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="font-bold text-lg mt-4 mb-2">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="font-bold text-xl mt-4 mb-2">$1</h1>');
    html = html.replace(/^\* (.+)$/gm, '<li class="ml-4">$1</li>');
    html = html.replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>');
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  async function loadSessionMessages(sessionId) {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/messages`);
      const messages = await response.json();

      const container = document.getElementById('messages-container');
      container.innerHTML = '';

      if (messages.length > 0) {
        hasMessages = true;
        transitionInputToBottom();

        messages.forEach(msg => {
          if (msg.role === 'user') {
            renderUserMessage(msg.content);
          } else {
            renderAssistantMessage(msg.content);
          }
        });
      } else {
        hasMessages = false;
        resetInputToCenter();
      }
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  }

  window.loadSession = function (id) {
    currentSessionId = id;

    const w = document.getElementById('welcome-state');
    if (w) w.classList.add('hidden');

    const c = document.getElementById('chat-interface');
    if (c) {
      c.classList.remove('hidden');
    }
    document.getElementById('active-indicator')?.classList.remove('hidden');

    const titleEl = document.getElementById('active-session-title');
    if (titleEl) titleEl.textContent = "Chat Session " + id;

    loadSessionMessages(id);
  };

  function handleHookButtonClick() {
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString().trim() : '';

    if (selectedText) {
      saveHook(selectedText);
    } else {
      window.openMergePanel?.();
    }
  }
  window.handleHookButtonClick = handleHookButtonClick;

  async function saveHook(content) {
    try {
      const response = await fetch(window.ADD_HOOK_URL || '/add-hook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
      });

      const data = await response.json();
      if (data.status === 'success') {
        window.showToast('Hook saved successfully!');
        window.getSelection()?.removeAllRanges();
      } else {
        window.showToast('Failed to save hook');
      }
    } catch (err) {
      console.error('Hook save error:', err);
      window.showToast('Error saving hook');
    }
  }

  window.attemptNewChat = function () {
    window.showToast('Select a folder from sidebar to create new chat');
  };

  window.toggleChatModelSelect = function (id) {
    const opt = document.getElementById(id + '-options');
    if (opt) opt.classList.toggle('show');
  };

  window.selectCustomOption = function (value, text, inputId, changeCb) {
    const hidden = document.getElementById(inputId);
    const trigger = document.getElementById(inputId + '-trigger-text');
    if (hidden) hidden.value = value;
    if (trigger) trigger.textContent = text;
    const opts = document.getElementById(inputId + '-options');
    if (opts) opts.classList.remove('show');
    if (changeCb && typeof window[changeCb] === 'function') window[changeCb](value);
  };

  window.setMode = function (mode) {
    const indicator = document.getElementById('mode-indicator');
    const btnNormal = document.getElementById('mode-normal');
    const btnDeep = document.getElementById('mode-deep');
    const hiddenInput = document.getElementById('chat-mode');

    if (hiddenInput) hiddenInput.value = mode;

    if (mode === 'normal') {
      if (indicator) {
        indicator.style.left = '0.125rem';
        indicator.classList.remove('left-1/2');
      }
      btnNormal?.classList.add('text-white');
      btnNormal?.classList.remove('text-[var(--text-muted)]');
      btnDeep?.classList.add('text-[var(--text-muted)]');
      btnDeep?.classList.remove('text-white');
    } else if (mode === 'deep_dive') {
      if (indicator) {
        indicator.style.left = '50%';
        indicator.classList.remove('left-0.5');
      }
      btnNormal?.classList.remove('text-white');
      btnNormal?.classList.add('text-[var(--text-muted)]');
      btnDeep?.classList.remove('text-[var(--text-muted)]');
      btnDeep?.classList.add('text-white');
    }
  };

  window.toggleRecording = function () {
    window.showToast('Voice recording coming soon');
  };

})();
