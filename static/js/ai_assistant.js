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
    } else {
      // Restore last session from localStorage
      const savedSessionId = localStorage.getItem('currentChatSessionId');
      if (savedSessionId) {
        window.loadSession(savedSessionId);
      }
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
    const msgId = 'user-msg-' + Date.now();

    let filesHtml = '';
    if (fileNames.length > 0) {
      filesHtml = `<div class="text-xs text-blue-300 mt-2 flex flex-wrap gap-1">
        ${fileNames.map(n => `<span class="bg-blue-500/20 px-2 py-0.5 rounded">📎 ${n}</span>`).join('')}
      </div>`;
    }

    msgDiv.innerHTML = `
      <div class="user-msg-wrapper">
        <div class="message-bubble" id="${msgId}" data-raw-text="${escapeHtml(text).replace(/"/g, '&quot;')}">
          <p class="message-text">${escapeHtml(text)}</p>
          ${filesHtml}
        </div>
        <div class="message-actions user-actions">
          <button class="action-btn" onclick="copyMessageText('${msgId}')" title="Copy">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
          </button>
          <button class="action-btn" onclick="editUserMessage('${msgId}')" title="Edit">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
          </button>
        </div>
      </div>
    `;
    container.appendChild(msgDiv);
    scrollToBottom();
  }

  function renderAssistantMessage(text, msgId = null) {
    const container = document.getElementById('messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant-message';
    const id = msgId || ('asst-msg-' + Date.now());

    const formattedText = formatMarkdown(text);

    msgDiv.innerHTML = `
      <div class="message-bubble" id="${id}" data-raw-text="${escapeHtml(text).replace(/"/g, '&quot;')}">
        <div class="message-text prose">${formattedText}</div>
        <div class="message-actions assistant-actions">
          <button class="action-btn" onclick="copyMessageText('${id}')" title="Copy">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
          </button>
          <button class="action-btn like-btn" onclick="likeMessage('${id}')" title="Like">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"></path>
            </svg>
          </button>
          <button class="action-btn dislike-btn" onclick="dislikeMessage('${id}')" title="Dislike">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"></path>
            </svg>
          </button>
          <div class="redo-container">
            <button class="action-btn redo-btn" onclick="toggleRedoMenu('${id}')" title="Redo with different model">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
            <div class="redo-menu" id="redo-menu-${id}">
              <div class="redo-menu-title">Regenerate with:</div>
              <button class="redo-option" onclick="redoWithModel('${id}', 'default')">nvidia/Nemotron</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'qwen-80b')">Qwen 2.5 72B</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'mistral')">Mistral Small</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'gemini')">Gemini 2.0 Flash</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'gpt-oss')">GPT-4o (OSS)</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'gemma')">Gemma 2 27B</button>
              <button class="redo-option" onclick="redoWithModel('${id}', 'deepseek')">DeepSeek R1</button>
            </div>
          </div>
        </div>
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

    // Save to localStorage for persistence across reloads
    localStorage.setItem('currentChatSessionId', id);

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

  window.attemptNewChat = async function () {
    if (!currentSessionId) {
      window.showToast('No active session. Please select a folder first.');
      return;
    }

    try {
      // Fetch current session info to get folder_id
      const response = await fetch(`/api/sessions/${currentSessionId}/info`);
      if (!response.ok) {
        window.showToast('Could not find current session info');
        return;
      }
      const sessionInfo = await response.json();
      const folderId = sessionInfo.folder_id;

      if (folderId) {
        // Create new session in the same folder
        await window.createSession(folderId, 'New Chat', true);
      } else {
        window.showToast('Could not determine folder for new chat');
      }
    } catch (err) {
      console.error('Error creating new chat:', err);
      window.showToast('Error creating new chat');
    }
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

  // ============================================
  // MESSAGE ACTION HANDLERS
  // ============================================

  window.copyMessageText = function (msgId) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    // Get raw text from data attribute and decode HTML entities
    let rawText = msgEl.dataset.rawText || '';
    if (rawText) {
      const textarea = document.createElement('textarea');
      textarea.innerHTML = rawText;
      rawText = textarea.value;
    } else {
      rawText = msgEl.querySelector('.message-text')?.innerText || '';
    }

    navigator.clipboard.writeText(rawText).then(() => {
      window.showToast('Copied to clipboard');
    }).catch(() => {
      window.showToast('Failed to copy');
    });
  };

  window.editUserMessage = function (msgId) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl || msgEl.classList.contains('editing')) return;

    const textEl = msgEl.querySelector('.message-text');
    if (!textEl) return;

    let rawText = msgEl.dataset.rawText || textEl.innerText;
    const textarea = document.createElement('textarea');
    textarea.innerHTML = rawText;
    rawText = textarea.value;

    msgEl.dataset.originalText = rawText;
    msgEl.classList.add('editing');
    textEl.contentEditable = 'true';
    textEl.textContent = rawText;
    textEl.focus();

    const range = document.createRange();
    range.selectNodeContents(textEl);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);

    const actionsEl = msgEl.closest('.user-msg-wrapper')?.querySelector('.message-actions');
    if (actionsEl) {
      actionsEl.dataset.originalHtml = actionsEl.innerHTML;
      actionsEl.innerHTML = `
        <button class="action-btn" onclick="saveUserMessage('${msgId}')" title="Save" style="color: #22c55e;">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </button>
        <button class="action-btn" onclick="cancelEditUserMessage('${msgId}')" title="Cancel" style="color: #ef4444;">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      `;
      actionsEl.style.opacity = '1';
    }

    textEl.onkeydown = function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window.saveUserMessage(msgId);
      } else if (e.key === 'Escape') {
        window.cancelEditUserMessage(msgId);
      }
    };
  };

  window.saveUserMessage = function (msgId) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;
    const textEl = msgEl.querySelector('.message-text');
    if (!textEl) return;

    const newText = textEl.textContent.trim();
    msgEl.dataset.rawText = escapeHtml(newText).replace(/"/g, '&quot;');
    textEl.contentEditable = 'false';
    textEl.onkeydown = null;
    msgEl.classList.remove('editing');

    const actionsEl = msgEl.closest('.user-msg-wrapper')?.querySelector('.message-actions');
    if (actionsEl && actionsEl.dataset.originalHtml) {
      actionsEl.innerHTML = actionsEl.dataset.originalHtml;
      actionsEl.style.opacity = '';
      delete actionsEl.dataset.originalHtml;
    }
    delete msgEl.dataset.originalText;
    window.showToast('Message updated');
  };

  window.cancelEditUserMessage = function (msgId) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;
    const textEl = msgEl.querySelector('.message-text');
    if (!textEl) return;

    textEl.textContent = msgEl.dataset.originalText || '';
    textEl.contentEditable = 'false';
    textEl.onkeydown = null;
    msgEl.classList.remove('editing');

    const actionsEl = msgEl.closest('.user-msg-wrapper')?.querySelector('.message-actions');
    if (actionsEl && actionsEl.dataset.originalHtml) {
      actionsEl.innerHTML = actionsEl.dataset.originalHtml;
      actionsEl.style.opacity = '';
      delete actionsEl.dataset.originalHtml;
    }
    delete msgEl.dataset.originalText;
  };

  window.likeMessage = function (msgId) {
    const btn = document.querySelector(`#${msgId} .like-btn`);
    if (btn) {
      btn.classList.toggle('active');
      document.querySelector(`#${msgId} .dislike-btn`)?.classList.remove('active');
    }
    window.showToast('Feedback recorded');
  };

  window.dislikeMessage = function (msgId) {
    const btn = document.querySelector(`#${msgId} .dislike-btn`);
    if (btn) {
      btn.classList.toggle('active');
      document.querySelector(`#${msgId} .like-btn`)?.classList.remove('active');
    }
    window.showToast('Feedback recorded');
  };

  window.toggleRedoMenu = function (msgId) {
    // Close other redo menus
    document.querySelectorAll('.redo-menu.show').forEach(menu => {
      if (menu.id !== `redo-menu-${msgId}`) {
        menu.classList.remove('show');
      }
    });
    const menu = document.getElementById(`redo-menu-${msgId}`);
    if (menu) menu.classList.toggle('show');
  };

  window.redoWithModel = async function (msgId, model) {
    const menu = document.getElementById(`redo-menu-${msgId}`);
    if (menu) menu.classList.remove('show');

    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    // Find the previous user message
    const msgContainer = msgEl.closest('.message');
    let prevUserMsg = msgContainer?.previousElementSibling;
    while (prevUserMsg && !prevUserMsg.classList.contains('user-message')) {
      prevUserMsg = prevUserMsg.previousElementSibling;
    }

    if (!prevUserMsg) {
      window.showToast('Could not find original query');
      return;
    }

    const userText = prevUserMsg.querySelector('.message-text')?.innerText || '';
    if (!userText) {
      window.showToast('Could not find original query');
      return;
    }

    // Show loading state
    const textEl = msgEl.querySelector('.message-text');
    const originalContent = textEl?.innerHTML;
    if (textEl) {
      textEl.innerHTML = '<div class="typing-dots inline-flex gap-1"><span></span><span></span><span></span></div> Regenerating...';
    }

    try {
      const mode = document.getElementById('chat-mode')?.value || 'normal';
      const formData = new FormData();
      formData.append('message', userText);
      formData.append('session_id', currentSessionId);
      formData.append('model', model);
      formData.append('mode', mode);

      const response = await fetch('/chat', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.error) {
        if (textEl) textEl.innerHTML = originalContent;
        window.showToast('Error: ' + data.error);
      } else {
        if (textEl) {
          textEl.innerHTML = formatMarkdown(data.response);
          msgEl.dataset.rawText = escapeHtml(data.response).replace(/"/g, '&quot;');
        }
        window.showToast('Response regenerated');
      }
    } catch (err) {
      if (textEl) textEl.innerHTML = originalContent;
      window.showToast('Failed to regenerate');
      console.error('Redo error:', err);
    }
  };

  // Close redo menus when clicking outside
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.redo-container')) {
      document.querySelectorAll('.redo-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    }
  });

})();
