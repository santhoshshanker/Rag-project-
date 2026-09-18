/**
 * Dental Assistant Copilot - Chairside Clinical AI Chatbot
 * Interactive conversational logic, multi-session management,
 * Web Speech API dictation & TTS, RAG grounding & patient cross-checks.
 */

// Application State
const state = {
  user: null,
  patient: {
    name: "John Doe",
    age: 42,
    gender: "Male",
    treatment_type: "Oral Surgery & Implant",
    medical_alerts: ["Penicillin Allergy (Severe)", "Hypertension (Controlled)"],
    chief_complaint: "Severe throbbing lower left jaw pain, fractured tooth #19 on olive pit."
  },
  documents: [],
  docStats: {},
  sessions: [],
  activeSessionId: null,
  config: {
    provider: "builtin",
    temperature: 0.2
  },
  activeModalChunk: null,
  isGenerating: false,
  isRecordingVoice: false,
  speechRecognition: null,
  speechSynthesisUtterance: null,
  currentlySpeakingBtn: null
};

// DOM Elements
const el = {
  // Sidebar
  sidebarPanel: document.getElementById("sidebar-panel"),
  sidebarBackdrop: document.getElementById("sidebar-backdrop"),
  toggleSidebarBtn: document.getElementById("toggle-sidebar-btn"),
  closeSidebarBtn: document.getElementById("close-sidebar-btn"),
  newChatBtn: document.getElementById("new-chat-btn"),
  navTabs: document.querySelectorAll(".nav-tab"),
  viewContents: document.querySelectorAll(".sidebar-view-content"),
  sessionsListContainer: document.getElementById("sessions-list-container"),

  // Sidebar Patient Context
  presetSelect: document.getElementById("patient-preset-select"),
  sidebarPatientName: document.getElementById("sidebar-patient-name"),
  sidebarPatientAge: document.getElementById("sidebar-patient-age"),
  sidebarPatientTreatment: document.getElementById("sidebar-patient-treatment"),
  sidebarPatientComplaint: document.getElementById("sidebar-patient-complaint"),
  patientAlertsTags: document.getElementById("patient-alerts-tags"),
  editPatientBtn: document.getElementById("edit-patient-btn"),

  // Sidebar Documents
  docsCountBadge: document.getElementById("docs-count-badge"),
  dropZone: document.getElementById("document-drop-zone"),
  fileInput: document.getElementById("document-file-input"),
  uploadProgressBar: document.getElementById("upload-progress-bar"),
  documentListContainer: document.getElementById("document-list-container"),
  refreshDocsBtn: document.getElementById("refresh-docs-btn"),

  // Sidebar User & Theme
  userProfileBtn: document.getElementById("user-profile-btn"),
  userDisplayName: document.getElementById("user-display-name"),
  userDisplayRole: document.getElementById("user-display-role"),
  userAvatarInitials: document.getElementById("user-avatar-initials"),
  themeToggleBtn: document.getElementById("theme-toggle-btn"),
  themeIcon: document.getElementById("theme-icon"),
  sidebarSettingsBtn: document.getElementById("sidebar-settings-btn"),

  // Chat Topbar
  currentChatTitle: document.getElementById("current-chat-title"),
  topbarPatientPill: document.getElementById("topbar-patient-pill"),
  topbarPatientName: document.getElementById("topbar-patient-name"),
  topbarPatientSub: document.getElementById("topbar-patient-sub"),
  engineBadge: document.getElementById("engine-status-badge"),
  engineNameHeader: document.getElementById("header-engine-name"),
  exportNotesBtn: document.getElementById("export-notes-btn"),
  clearChatBtn: document.getElementById("clear-chat-btn"),
  disclaimerBanner: document.querySelector(".clinical-disclaimer-banner"),
  dismissDisclaimerBtn: document.getElementById("dismiss-disclaimer-btn"),

  // Chat Feed
  chatFeed: document.getElementById("chat-feed"),
  welcomeHero: document.getElementById("welcome-hero"),
  categoryCards: document.querySelectorAll(".category-card"),
  scrollBottomBtn: document.getElementById("scroll-bottom-btn"),

  // Chat Input Dock
  inputPatientBar: document.getElementById("input-patient-bar"),
  inputPatientName: document.getElementById("input-patient-name"),
  inputPatientTags: document.getElementById("input-patient-tags"),
  changePatientBtn: document.getElementById("change-patient-btn"),
  voiceDictationBanner: document.getElementById("voice-dictation-banner"),
  cancelVoiceBtn: document.getElementById("cancel-voice-btn"),
  chatForm: document.getElementById("chat-form"),
  attachFileBtn: document.getElementById("attach-file-btn"),
  inlineFileInput: document.getElementById("inline-file-input"),
  queryInput: document.getElementById("query-input"),
  voiceDictationBtn: document.getElementById("voice-dictation-btn"),
  sendBtn: document.getElementById("send-btn"),

  // Source Modal
  sourceModal: document.getElementById("source-modal"),
  modalSourceTitle: document.getElementById("modal-source-title"),
  modalSourceMeta: document.getElementById("modal-source-meta"),
  modalMatchFill: document.getElementById("modal-match-fill"),
  modalMatchText: document.getElementById("modal-match-text"),
  modalChunkText: document.getElementById("modal-chunk-text"),
  copyChunkBtn: document.getElementById("copy-chunk-btn"),
  closeSourceModalBtn: document.getElementById("close-source-modal-btn"),
  closeSourceModalBtn2: document.getElementById("close-source-modal-btn2"),

  // Document Preview Modal
  docPreviewModal: document.getElementById("doc-preview-modal"),
  previewDocTitle: document.getElementById("preview-doc-title"),
  previewDocMeta: document.getElementById("preview-doc-meta"),
  previewChunksContainer: document.getElementById("preview-chunks-container"),
  closeDocModalBtn: document.getElementById("close-doc-modal-btn"),
  closeDocModalBtn2: document.getElementById("close-doc-modal-btn2"),

  // Patient Edit Modal
  patientModal: document.getElementById("patient-modal"),
  patientEditForm: document.getElementById("patient-edit-form"),
  modalPatientName: document.getElementById("modal-patient-name"),
  modalPatientAge: document.getElementById("modal-patient-age"),
  modalPatientGender: document.getElementById("modal-patient-gender"),
  modalPatientTreatment: document.getElementById("modal-patient-treatment"),
  modalAlertsTags: document.getElementById("modal-alerts-tags"),
  modalNewAlertInput: document.getElementById("modal-new-alert-input"),
  modalAddAlertBtn: document.getElementById("modal-add-alert-btn"),
  modalPatientComplaint: document.getElementById("modal-patient-complaint"),
  closePatientModalBtn: document.getElementById("close-patient-modal-btn"),
  cancelPatientModalBtn: document.getElementById("cancel-patient-modal-btn"),

  // Settings Modal
  settingsModal: document.getElementById("settings-modal"),
  settingsForm: document.getElementById("settings-form"),
  providerSelect: document.getElementById("provider-select"),
  geminiGroup: document.getElementById("gemini-config-group"),
  openaiGroup: document.getElementById("openai-config-group"),
  geminiKeyInput: document.getElementById("gemini-api-key"),
  openaiKeyInput: document.getElementById("openai-api-key"),
  tempSlider: document.getElementById("temperature-slider"),
  tempValDisplay: document.getElementById("temp-val"),
  closeSettingsBtn: document.getElementById("close-settings-btn"),
  cancelSettingsBtn: document.getElementById("cancel-settings-btn"),

  // Auth Modal
  authModal: document.getElementById("auth-modal"),
  authForm: document.getElementById("auth-form"),
  authUsernameInput: document.getElementById("auth-username"),
  authPasswordInput: document.getElementById("auth-password"),
  authErrorMsg: document.getElementById("auth-error-msg"),
  demoUserBtns: document.querySelectorAll(".demo-user-btn"),

  // Toast
  toast: document.getElementById("toast"),
  toastMsg: document.getElementById("toast-msg")
};

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  initAuth();
  initSidebarNavigation();
  initTextareaAutoResize();
  initVoiceDictation();
  initChatSessions();
  await loadConfig();
  await loadPatientPresets();
  await loadCurrentPatient();
  await loadDocuments();
  attachEventListeners();
});

// ============================================================
// THEME MANAGEMENT (Dark / Light Mode)
// ============================================================
function initTheme() {
  const savedTheme = localStorage.getItem("denta_theme") || "light";
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    el.themeIcon.textContent = "☀️";
  } else {
    document.body.classList.remove("dark-mode");
    el.themeIcon.textContent = "🌙";
  }

  el.themeToggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("denta_theme", isDark ? "dark" : "light");
    el.themeIcon.textContent = isDark ? "☀️" : "🌙";
    showToast(`Switched to ${isDark ? "Dark" : "Light"} theme`);
  });
}

// ============================================================
// AUTHENTICATION
// ============================================================
function initAuth() {
  const savedUser = localStorage.getItem("denta_user");
  if (savedUser) {
    try {
      state.user = JSON.parse(savedUser);
      renderUserUI();
    } catch (e) {
      promptLogin();
    }
  } else {
    // Default demo session for immediate chairside testing
    state.user = {
      username: "drsarah",
      name: "Dr. Sarah Lin, DDS",
      role: "Lead Dental Surgeon",
      license: "DDS-CA-88419"
    };
    localStorage.setItem("denta_user", JSON.stringify(state.user));
    renderUserUI();
  }
}

function promptLogin() {
  el.authModal.classList.remove("hidden");
  el.authErrorMsg.classList.add("hidden");
}

function renderUserUI() {
  if (!state.user) return;
  el.userDisplayName.textContent = state.user.name;
  el.userDisplayRole.textContent = state.user.role;
  const initials = state.user.name
    .replace(/^Dr\.\s*/, '')
    .split(' ')
    .map(n => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();
  el.userAvatarInitials.textContent = initials || "DR";
}

// ============================================================
// CHAT SESSION STATE MANAGEMENT
// ============================================================
function initChatSessions() {
  const savedSessions = localStorage.getItem("denta_chat_sessions");
  if (savedSessions) {
    try {
      state.sessions = JSON.parse(savedSessions);
    } catch (e) {
      state.sessions = [];
    }
  }

  if (!state.sessions || state.sessions.length === 0) {
    // Create initial default consultation
    createNewSession("Clinical Consultation");
  } else {
    const lastActiveId = localStorage.getItem("denta_active_session");
    const active = state.sessions.find(s => s.id === lastActiveId) || state.sessions[0];
    switchSession(active.id);
  }
}

function saveSessionsToStorage() {
  localStorage.setItem("denta_chat_sessions", JSON.stringify(state.sessions));
  localStorage.setItem("denta_active_session", state.activeSessionId);
  renderSessionsList();
}

function createNewSession(customTitle = null) {
  const newId = "sess_" + Date.now();
  const session = {
    id: newId,
    title: customTitle || "New Consultation",
    createdAt: new Date().toISOString(),
    messages: []
  };
  state.sessions.unshift(session);
  switchSession(newId);
  showToast("Started a new clinical consultation");
}

function switchSession(sessionId) {
  const session = state.sessions.find(s => s.id === sessionId);
  if (!session) return;

  state.activeSessionId = sessionId;
  localStorage.setItem("denta_active_session", sessionId);
  el.currentChatTitle.textContent = session.title;

  // Render messages
  renderSessionMessages(session);
  saveSessionsToStorage();

  // Close sidebar on mobile
  if (window.innerWidth <= 900) {
    closeSidebar();
  }
}

function deleteSession(sessionId, event) {
  if (event) event.stopPropagation();
  if (state.sessions.length <= 1) {
    // Clear the only session instead of deleting
    const session = state.sessions[0];
    session.title = "New Consultation";
    session.messages = [];
    saveSessionsToStorage();
    renderSessionMessages(session);
    showToast("Consultation cleared");
    return;
  }

  state.sessions = state.sessions.filter(s => s.id !== sessionId);
  if (state.activeSessionId === sessionId) {
    state.activeSessionId = state.sessions[0].id;
  }
  switchSession(state.activeSessionId);
  showToast("Conversation deleted");
}

function renderSessionsList() {
  el.sessionsListContainer.innerHTML = "";
  state.sessions.forEach(sess => {
    const item = document.createElement("div");
    item.className = `session-item ${sess.id === state.activeSessionId ? 'active' : ''}`;
    item.innerHTML = `
      <div class="session-title-wrap">
        <span>💬</span>
        <span class="session-title-text" title="${escapeHTML(sess.title)}">${escapeHTML(sess.title)}</span>
      </div>
      <button class="delete-session-btn" title="Delete consultation">×</button>
    `;

    item.addEventListener("click", () => switchSession(sess.id));
    item.querySelector(".delete-session-btn").addEventListener("click", (e) => deleteSession(sess.id, e));

    el.sessionsListContainer.appendChild(item);
  });
}

function renderSessionMessages(session) {
  // Clear feed
  el.chatFeed.innerHTML = "";

  if (!session.messages || session.messages.length === 0) {
    // Show welcome hero
    el.welcomeHero.classList.remove("hidden");
    el.chatFeed.appendChild(el.welcomeHero);
  } else {
    el.welcomeHero.classList.add("hidden");
    session.messages.forEach(msg => {
      if (msg.role === "user") {
        appendUserMessageToDOM(msg.content, msg.time);
      } else if (msg.role === "assistant") {
        appendAssistantMessageToDOM(msg.content, msg.sources, msg.provider, msg.time, msg.followups, false);
      }
    });
  }
  scrollToBottom();
}

// ============================================================
// SIDEBAR & DRAWER NAVIGATION
// ============================================================
function initSidebarNavigation() {
  // Tabs switcher (Chats / Patient / Docs)
  el.navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetViewId = tab.dataset.view;
      el.navTabs.forEach(t => t.classList.remove("active"));
      el.viewContents.forEach(v => v.classList.remove("active"));

      tab.classList.add("active");
      const targetView = document.getElementById(targetViewId);
      if (targetView) targetView.classList.add("active");
    });
  });

  // Mobile sidebar toggles
  el.toggleSidebarBtn.addEventListener("click", openSidebar);
  el.closeSidebarBtn.addEventListener("click", closeSidebar);
  el.sidebarBackdrop.addEventListener("click", closeSidebar);

  // New chat button
  el.newChatBtn.addEventListener("click", () => createNewSession());

  // Topbar patient pill opens patient tab in sidebar
  el.topbarPatientPill.addEventListener("click", () => {
    openSidebar();
    document.querySelector('.nav-tab[data-view="view-patient"]').click();
  });

  el.changePatientBtn.addEventListener("click", () => {
    openSidebar();
    document.querySelector('.nav-tab[data-view="view-patient"]').click();
  });
}

function openSidebar() {
  el.sidebarPanel.classList.add("open");
  el.sidebarBackdrop.classList.remove("hidden");
}

function closeSidebar() {
  el.sidebarPanel.classList.remove("open");
  el.sidebarBackdrop.classList.add("hidden");
}

function initTextareaAutoResize() {
  const textarea = el.queryInput;
  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 140) + "px";
  });
}

// ============================================================
// CHAIRSIDE VOICE DICTATION (Web Speech API)
// ============================================================
function initVoiceDictation() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    el.voiceDictationBtn.title = "Voice dictation not supported in this browser.";
    el.voiceDictationBtn.style.opacity = "0.4";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    state.isRecordingVoice = true;
    el.voiceDictationBanner.classList.remove("hidden");
    el.voiceDictationBtn.classList.add("speaking");
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    el.queryInput.value = transcript;
    el.queryInput.dispatchEvent(new Event("input"));
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    stopVoiceDictation();
    showToast("Voice dictation error: " + event.error);
  };

  recognition.onend = () => {
    stopVoiceDictation();
    // If text was captured, highlight input
    if (el.queryInput.value.trim().length > 3) {
      showToast("Voice recorded! Press Send or add more details.");
    }
  };

  state.speechRecognition = recognition;

  el.voiceDictationBtn.addEventListener("click", () => {
    if (state.isRecordingVoice) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (e) {
        console.error(e);
      }
    }
  });

  el.cancelVoiceBtn.addEventListener("click", () => {
    if (recognition) recognition.abort();
    stopVoiceDictation();
  });
}

function stopVoiceDictation() {
  state.isRecordingVoice = false;
  el.voiceDictationBanner.classList.add("hidden");
  el.voiceDictationBtn.classList.remove("speaking");
}

// ============================================================
// TEXT-TO-SPEECH AUDIO DICTATION (SpeechSynthesis)
// ============================================================
function speakMessage(text, buttonEl) {
  if (!('speechSynthesis' in window)) {
    showToast("Text-to-speech audio not supported in this browser.");
    return;
  }

  // If already speaking this button, stop
  if (window.speechSynthesis.speaking && state.currentlySpeakingBtn === buttonEl) {
    window.speechSynthesis.cancel();
    resetSpeechBtn(buttonEl);
    return;
  }

  window.speechSynthesis.cancel();
  if (state.currentlySpeakingBtn) {
    resetSpeechBtn(state.currentlySpeakingBtn);
  }

  // Clean markdown tags for natural spoken medical reading
  const cleanSpokenText = text
    .replace(/###\s+/g, '')
    .replace(/####\s+/g, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/>\s*⚠️\s*/g, 'Clinical Warning: ')
    .replace(/>\s*/g, '')
    .replace(/\[Source:.*?\]/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/http[s]?:\/\/\S+/g, '');

  const utterance = new SpeechSynthesisUtterance(cleanSpokenText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  utterance.onstart = () => {
    state.currentlySpeakingBtn = buttonEl;
    buttonEl.classList.add("speaking");
    buttonEl.innerHTML = `<span>⏹️</span> Stop`;
  };

  utterance.onend = () => {
    resetSpeechBtn(buttonEl);
  };

  utterance.onerror = () => {
    resetSpeechBtn(buttonEl);
  };

  window.speechSynthesis.speak(utterance);
}

function resetSpeechBtn(buttonEl) {
  if (buttonEl) {
    buttonEl.classList.remove("speaking");
    buttonEl.innerHTML = `<span>🔊</span> Listen`;
  }
  state.currentlySpeakingBtn = null;
}

// ============================================================
// PATIENT CONTEXT & CRUD
// ============================================================
async function loadPatientPresets() {
  try {
    const res = await fetch("/api/patient/presets");
    if (res.ok) {
      const presets = await res.json();
      el.presetSelect.innerHTML = presets
        .map(p => `<option value="${p.id}">${p.name} (${p.age}y • ${p.treatment_type})</option>`)
        .join('');
    }
  } catch (err) {
    console.error("Failed to load presets:", err);
  }
}

async function loadCurrentPatient() {
  try {
    const res = await fetch("/api/patient/current");
    if (res.ok) {
      state.patient = await res.json();
      renderPatientUI();
    }
  } catch (err) {
    console.error("Failed to load current patient:", err);
    renderPatientUI();
  }
}

function renderPatientUI() {
  const p = state.patient;
  // Topbar
  el.topbarPatientName.textContent = p.name;
  const primaryAlert = (p.medical_alerts && p.medical_alerts.length > 0) ? p.medical_alerts[0] : p.treatment_type;
  el.topbarPatientSub.textContent = `${p.age}y • ${primaryAlert}`;

  // Sidebar
  el.sidebarPatientName.textContent = p.name;
  el.sidebarPatientAge.textContent = `${p.age}y • ${p.gender}`;
  el.sidebarPatientTreatment.textContent = p.treatment_type;
  el.sidebarPatientComplaint.textContent = p.chief_complaint;

  // Bottom Input Reminder
  el.inputPatientName.textContent = p.name;
  el.inputPatientTags.textContent = `(Age ${p.age} • ${p.medical_alerts.join(', ') || 'No Alerts'})`;

  // Render Tags
  el.patientAlertsTags.innerHTML = "";
  (p.medical_alerts || []).forEach(alertText => {
    const tag = document.createElement("span");
    const isPenicillin = alertText.toLowerCase().includes("penicillin");
    tag.className = `alert-tag ${isPenicillin ? '' : 'warning-type'}`;
    tag.textContent = alertText;
    el.patientAlertsTags.appendChild(tag);
  });
}

// ============================================================
// KNOWLEDGE BASE DOCUMENTS
// ============================================================
async function loadDocuments() {
  try {
    const res = await fetch("/api/documents");
    if (res.ok) {
      const data = await res.json();
      state.documents = data.documents;
      state.docStats = data.stats;
      renderDocumentsUI();
    }
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}

function renderDocumentsUI() {
  el.docsCountBadge.textContent = state.documents.length;

  if (state.documents.length === 0) {
    el.documentListContainer.innerHTML = `
      <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.78rem;">
        No dental documents uploaded. Upload guidelines above.
      </div>
    `;
    return;
  }

  el.documentListContainer.innerHTML = state.documents.map(doc => {
    const badgeClass = doc.file_type === 'pdf' ? 'pdf' : 'txt';
    return `
      <div class="doc-card" data-id="${doc.doc_id}">
        <div class="doc-info">
          <span class="file-badge ${badgeClass}">${doc.file_type}</span>
          <div class="doc-text-meta">
            <span class="doc-title" title="${doc.filename}">${doc.filename}</span>
            <span class="doc-meta-sub">${doc.chunk_count} chunks • ${Math.round(doc.char_count / 1024 * 10) / 10} KB</span>
          </div>
        </div>
        <div style="display: flex; gap: 4px;">
          <button class="icon-btn-sm view-doc-btn" data-id="${doc.doc_id}" title="Inspect chunks">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="icon-btn-sm danger-hover delete-doc-btn" data-id="${doc.doc_id}" title="Delete document">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Attach card triggers
  el.documentListContainer.querySelectorAll(".view-doc-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openDocPreview(btn.dataset.id);
    });
  });

  el.documentListContainer.querySelectorAll(".delete-doc-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await deleteDocument(btn.dataset.id);
    });
  });
}

async function handleFileUpload(files) {
  el.uploadProgressBar.classList.remove("hidden");
  let successCount = 0;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        successCount++;
      } else {
        const errData = await res.json();
        alert(`Failed to upload ${file.name}: ${errData.detail || 'Server error'}`);
      }
    } catch (err) {
      alert(`Error uploading ${file.name}: ${err.message}`);
    }
  }

  el.uploadProgressBar.classList.add("hidden");
  el.fileInput.value = "";
  el.inlineFileInput.value = "";
  if (successCount > 0) {
    showToast(`Successfully indexed ${successCount} document(s) into RAG memory!`);
    await loadDocuments();
  }
}

async function deleteDocument(docId) {
  if (!confirm("Are you sure you want to remove this document from the vector store?")) return;

  try {
    const res = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Document deleted from RAG knowledge base");
      await loadDocuments();
    }
  } catch (err) {
    alert("Failed to delete document: " + err.message);
  }
}

async function openDocPreview(docId) {
  try {
    const doc = state.documents.find(d => d.doc_id === docId);
    if (!doc) return;

    el.previewDocTitle.textContent = doc.filename;
    el.previewDocMeta.textContent = `${doc.chunk_count} Chunks • ${doc.file_type.toUpperCase()}`;
    el.previewChunksContainer.innerHTML = `<div style="text-align: center; padding: 1rem; color: var(--text-muted);">Loading chunks...</div>`;
    el.docPreviewModal.classList.remove("hidden");

    const res = await fetch(`/api/documents/${docId}/chunks`);
    if (res.ok) {
      const data = await res.json();
      el.previewChunksContainer.innerHTML = data.chunks.map((c, i) => `
        <div style="background: var(--bg-surface-alt); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.85rem; margin-bottom: 0.65rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.74rem; font-weight: 700; color: var(--primary);">
            <span>Chunk #${i+1} • ${c.section || 'General'}</span>
            <span style="color: var(--text-muted);">${c.char_count} chars</span>
          </div>
          <p style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; white-space: pre-wrap;">${escapeHTML(c.text)}</p>
        </div>
      `).join('');
    }
  } catch (err) {
    el.previewChunksContainer.innerHTML = `<p style="color: red;">Failed to load chunks: ${err.message}</p>`;
  }
}

// ============================================================
// CHAT EXECUTION & PROGRESSIVE WORD STREAMING
// ============================================================
async function submitQuery(queryText) {
  if (!queryText.trim() || state.isGenerating) return;

  // Clear query input
  el.queryInput.value = "";
  el.queryInput.style.height = "auto";

  // Hide welcome hero on first message
  el.welcomeHero.classList.add("hidden");

  // Get active session
  let session = state.sessions.find(s => s.id === state.activeSessionId);
  if (!session) {
    createNewSession();
    session = state.sessions[0];
  }

  // If first user message, update session title
  if (session.messages.length === 0) {
    session.title = queryText.length > 32 ? queryText.substring(0, 32) + "..." : queryText;
    el.currentChatTitle.textContent = session.title;
    saveSessionsToStorage();
  }

  const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Add user message to session & DOM
  session.messages.push({ role: "user", content: queryText, time: nowStr });
  appendUserMessageToDOM(queryText, nowStr);
  scrollToBottom();

  // Typing indicator
  const typingId = "typing-" + Date.now();
  appendTypingIndicator(typingId);
  scrollToBottom();

  state.isGenerating = true;
  el.sendBtn.disabled = true;

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: queryText,
        patient_info: state.patient,
        top_k: 3,
        chat_history: session.messages.slice(-6).map(m => ({ role: m.role, content: m.content }))
      })
    });

    removeTypingIndicator(typingId);

    if (res.ok) {
      const data = await res.json();
      const assistantTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      // Save to session
      session.messages.push({
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        provider: data.provider_used,
        time: assistantTime,
        followups: data.suggested_followups || []
      });
      saveSessionsToStorage();

      // Render with typewriter effect
      appendAssistantMessageToDOM(
        data.answer,
        data.sources,
        data.provider_used,
        assistantTime,
        data.suggested_followups || [],
        true // animate streaming
      );
    } else {
      const err = await res.json();
      appendErrorMessage(err.detail || "Error generating grounded answer from clinical documents.");
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendErrorMessage("Network error: Could not reach Dental Assistant server. " + err.message);
  } finally {
    state.isGenerating = false;
    el.sendBtn.disabled = false;
    scrollToBottom();
  }
}

// ============================================================
// DOM MESSAGE RENDERING
// ============================================================
function appendUserMessageToDOM(text, timeStr) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message user-message";
  msgDiv.innerHTML = `
    <div class="message-avatar">
      <div class="user-avatar-small">${el.userAvatarInitials.textContent || 'MD'}</div>
    </div>
    <div class="message-body">
      <div class="message-header">
        <strong class="user-name">${state.user ? state.user.name : 'Clinician'}</strong>
        <span class="message-time">${timeStr}</span>
      </div>
      <div class="message-content">
        <p>${escapeHTML(text)}</p>
      </div>
    </div>
  `;
  el.chatFeed.appendChild(msgDiv);
}

function appendAssistantMessageToDOM(markdownText, sources, provider, timeStr, followups = [], animate = false) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message assistant-message";

  // Build Sources HTML
  let sourcesHTML = "";
  if (sources && sources.length > 0) {
    const pills = sources.map((s, idx) => `
      <button class="source-pill-btn" data-idx="${idx}" title="Inspect source excerpt">
        <span>📄 ${escapeHTML(s.doc_name)}</span>
        <span class="source-match-score">${s.match_percentage}%</span>
      </button>
    `).join('');

    sourcesHTML = `
      <div class="sources-card">
        <div class="sources-header">
          <span>📚 Evidence Citations (${sources.length} Documents)</span>
          <span style="font-size: 0.68rem; color: var(--primary);">Click to verify chunk</span>
        </div>
        <div class="sources-list">${pills}</div>
      </div>
    `;
  }

  // Build Followups HTML
  let followupsHTML = "";
  if (followups && followups.length > 0) {
    const chips = followups.map(f => `
      <button class="followup-chip" data-query="${escapeHTML(f)}">
        <span>💡</span> ${escapeHTML(f)}
      </button>
    `).join('');

    followupsHTML = `
      <div class="followups-container">
        <span class="followups-label">Suggested Follow-up Questions:</span>
        <div class="followup-chips-wrap">${chips}</div>
      </div>
    `;
  }

  msgDiv.innerHTML = `
    <div class="message-avatar">
      <div class="assistant-avatar-wrap">🦷</div>
    </div>
    <div class="message-body">
      <div class="message-header">
        <strong class="assistant-name">Dental Assistant Copilot</strong>
        <span class="message-time">${timeStr}</span>
        <span class="badge-rag" title="Engine: ${escapeHTML(provider)}">${escapeHTML(provider)}</span>
      </div>
      <div class="message-content" id="content-${Date.now()}">
        ${animate ? '' : formatMarkdown(markdownText)}
      </div>
      ${sourcesHTML}
      <div class="message-actions-bar">
        <button class="msg-action-btn copy-msg-btn" title="Copy response">
          <span>📋</span> Copy
        </button>
        <button class="msg-action-btn speak-msg-btn" title="Listen aloud (Hands-Free)">
          <span>🔊</span> Listen
        </button>
        <button class="msg-action-btn regen-msg-btn" title="Regenerate clinical answer">
          <span>🔄</span> Regenerate
        </button>
      </div>
      ${followupsHTML}
    </div>
  `;

  // Attach event listeners to source pills
  if (sources && sources.length > 0) {
    msgDiv.querySelectorAll(".source-pill-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.idx);
        openSourceModal(sources[idx]);
      });
    });
  }

  // Attach event listeners to message action buttons
  const copyBtn = msgDiv.querySelector(".copy-msg-btn");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(markdownText);
    copyBtn.innerHTML = `<span>✓</span> Copied!`;
    setTimeout(() => { copyBtn.innerHTML = `<span>📋</span> Copy`; }, 2000);
    showToast("Clinical response copied to clipboard");
  });

  const speakBtn = msgDiv.querySelector(".speak-msg-btn");
  speakBtn.addEventListener("click", () => {
    speakMessage(markdownText, speakBtn);
  });

  const regenBtn = msgDiv.querySelector(".regen-msg-btn");
  regenBtn.addEventListener("click", () => {
    const session = state.sessions.find(s => s.id === state.activeSessionId);
    if (session && session.messages.length > 1) {
      // Find last user question
      for (let i = session.messages.length - 1; i >= 0; i--) {
        if (session.messages[i].role === "user") {
          submitQuery(session.messages[i].content);
          break;
        }
      }
    }
  });

  // Attach event listeners to follow-up suggestion chips
  msgDiv.querySelectorAll(".followup-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      el.queryInput.value = q;
      submitQuery(q);
    });
  });

  el.chatFeed.appendChild(msgDiv);

  // Streaming typewriter animation
  if (animate) {
    const contentEl = msgDiv.querySelector(".message-content");
    streamWordsIntoElement(contentEl, markdownText);
  }
}

function streamWordsIntoElement(targetEl, fullMarkdown) {
  const words = fullMarkdown.split(" ");
  let i = 0;
  let accumulated = "";

  const interval = setInterval(() => {
    if (i < words.length) {
      accumulated += (i === 0 ? "" : " ") + words[i];
      targetEl.innerHTML = formatMarkdown(accumulated);
      scrollToBottom();
      i++;
    } else {
      clearInterval(interval);
      targetEl.innerHTML = formatMarkdown(fullMarkdown);
      scrollToBottom();
    }
  }, 16);
}

function appendTypingIndicator(id) {
  const div = document.createElement("div");
  div.id = id;
  div.className = "chat-message assistant-message";
  div.innerHTML = `
    <div class="message-avatar">
      <div class="assistant-avatar-wrap">🦷</div>
    </div>
    <div class="message-body">
      <div class="message-header">
        <strong class="assistant-name">Dental Assistant Copilot</strong>
        <span class="message-time">Synthesizing clinical evidence...</span>
      </div>
      <div class="message-content" style="padding: 0.75rem 1rem;">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  el.chatFeed.appendChild(div);
}

function removeTypingIndicator(id) {
  const item = document.getElementById(id);
  if (item) item.remove();
}

function appendErrorMessage(errorText) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-message assistant-message";
  msgDiv.innerHTML = `
    <div class="message-avatar">
      <div class="assistant-avatar-wrap" style="background: var(--alert-red);">⚠️</div>
    </div>
    <div class="message-body">
      <div class="message-header">
        <strong class="assistant-name" style="color: var(--alert-red);">Notice</strong>
      </div>
      <div class="message-content" style="background: var(--alert-red-light); border-color: var(--alert-red-border); color: #991b1b;">
        <p>${escapeHTML(errorText)}</p>
      </div>
    </div>
  `;
  el.chatFeed.appendChild(msgDiv);
}

function scrollToBottom() {
  el.chatFeed.scrollTop = el.chatFeed.scrollHeight;
}

// ============================================================
// MODALS LOGIC
// ============================================================
function openSourceModal(chunk) {
  el.modalSourceTitle.textContent = chunk.doc_name;
  el.modalSourceMeta.textContent = `${chunk.section || 'Clinical Section'} • Chunk ID: ${chunk.chunk_id}`;
  const matchPct = chunk.match_percentage || 85;
  el.modalMatchFill.style.width = `${matchPct}%`;
  el.modalMatchText.textContent = `${matchPct}% Match`;
  el.modalChunkText.textContent = chunk.text_snippet || chunk.text || "No excerpt text available.";
  el.sourceModal.classList.remove("hidden");
}

// ============================================================
// CONFIG & SETTINGS
// ============================================================
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (res.ok) {
      state.config = await res.json();
      renderConfigUI();
    }
  } catch (err) {
    console.error("Failed to load config:", err);
  }
}

function renderConfigUI() {
  const provider = state.config.provider || "builtin";
  el.providerSelect.value = provider;
  el.tempSlider.value = state.config.temperature || 0.2;
  el.tempValDisplay.textContent = state.config.temperature || 0.2;

  let providerLabel = "Built-in Dental Engine";
  if (provider === "gemini") providerLabel = "Google Gemini (1.5 Flash)";
  if (provider === "openai") providerLabel = "OpenAI (GPT-4o Mini)";
  el.engineNameHeader.textContent = providerLabel;

  if (provider === "gemini") {
    el.geminiGroup.classList.remove("hidden");
    el.openaiGroup.classList.add("hidden");
  } else if (provider === "openai") {
    el.openaiGroup.classList.remove("hidden");
    el.geminiGroup.classList.add("hidden");
  } else {
    el.geminiGroup.classList.add("hidden");
    el.openaiGroup.classList.add("hidden");
  }
}

// ============================================================
// EVENT LISTENERS BINDING
// ============================================================
function attachEventListeners() {
  // Disclaimer Banner
  el.dismissDisclaimerBtn.addEventListener("click", () => {
    el.disclaimerBanner.style.display = "none";
  });

  // Welcome Category Prompts
  el.categoryCards.forEach(card => {
    card.addEventListener("click", () => {
      const prompt = card.dataset.prompt;
      el.queryInput.value = prompt;
      submitQuery(prompt);
    });
  });

  // Chat Form Submit (IME Safe)
  el.chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = el.queryInput.value.trim();
    if (q) submitQuery(q);
  });

  el.queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      if (e.isComposing || e.keyCode === 229) return;
      e.preventDefault();
      el.chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Scroll to Bottom Button
  el.chatFeed.addEventListener("scroll", () => {
    const fromBottom = el.chatFeed.scrollHeight - el.chatFeed.scrollTop - el.chatFeed.clientHeight;
    if (fromBottom > 150) {
      el.scrollBottomBtn.classList.remove("hidden");
    } else {
      el.scrollBottomBtn.classList.add("hidden");
    }
  });

  el.scrollBottomBtn.addEventListener("click", () => {
    scrollToBottom();
  });

  // Clear Chat Button in Header
  el.clearChatBtn.addEventListener("click", () => {
    const session = state.sessions.find(s => s.id === state.activeSessionId);
    if (session) {
      session.messages = [];
      saveSessionsToStorage();
      renderSessionMessages(session);
      showToast("Conversation cleared");
    }
  });

  // Export Notes
  el.exportNotesBtn.addEventListener("click", exportConsultationNotes);

  // File Upload Attachments (Chat Inline Paperclip & Dropzone)
  el.attachFileBtn.addEventListener("click", () => el.inlineFileInput.click());
  el.inlineFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) handleFileUpload(e.target.files);
  });

  el.fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) handleFileUpload(e.target.files);
  });

  el.dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    el.dropZone.classList.add("dragover");
  });
  el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("dragover"));
  el.dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    el.dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files);
  });

  el.refreshDocsBtn.addEventListener("click", () => {
    loadDocuments();
    showToast("Knowledge library refreshed");
  });

  // Patient Preset Selector
  el.presetSelect.addEventListener("change", (e) => {
    const selectedId = e.target.value;
    const presetMap = {
      "p1": {
        name: "John Doe", age: 42, gender: "Male", treatment_type: "Oral Surgery & Implant",
        medical_alerts: ["Penicillin Allergy (Severe)", "Hypertension (Controlled)"],
        chief_complaint: "Severe throbbing lower left jaw pain, fractured tooth #19 on olive pit."
      },
      "p2": {
        name: "Emma Watson", age: 8, gender: "Female", treatment_type: "Pediatric Trauma",
        medical_alerts: ["Asthma (Albuterol PRN)", "Latex Sensitivity"],
        chief_complaint: "Bicycle fall 40 minutes ago; tooth #8 avulsed, transported in cold milk."
      },
      "p3": {
        name: "Robert Vance", age: 67, gender: "Male", treatment_type: "Periodontics & Extractions",
        medical_alerts: ["Atrial Fibrillation on Warfarin (Coumadin)", "Type 2 Diabetes (HbA1c 6.8%)"],
        chief_complaint: "Bleeding gums on brushing, tooth #30 mobility degree 2, planned extraction."
      },
      "p4": {
        name: "Maria Garcia", age: 29, gender: "Female", treatment_type: "Endodontics",
        medical_alerts: ["No Known Drug Allergies (NKDA)"],
        chief_complaint: "Spontaneous lingering thermal sensitivity on upper right first molar (#3)."
      }
    };

    if (presetMap[selectedId]) {
      state.patient = { ...presetMap[selectedId] };
      renderPatientUI();
      savePatientToBackend();
      showToast(`Switched active patient scenario to ${state.patient.name}`);
    }
  });

  // Patient Edit Modal
  el.editPatientBtn.addEventListener("click", openPatientEditModal);
  el.closePatientModalBtn.addEventListener("click", () => el.patientModal.classList.add("hidden"));
  el.cancelPatientModalBtn.addEventListener("click", () => el.patientModal.classList.add("hidden"));

  el.modalAddAlertBtn.addEventListener("click", () => {
    const txt = el.modalNewAlertInput.value.trim();
    if (txt) {
      state.patient.medical_alerts.push(txt);
      el.modalNewAlertInput.value = "";
      renderModalAlertTags();
    }
  });

  el.patientEditForm.addEventListener("submit", (e) => {
    e.preventDefault();
    state.patient.name = el.modalPatientName.value.trim();
    state.patient.age = parseInt(el.modalPatientAge.value) || 35;
    state.patient.gender = el.modalPatientGender.value;
    state.patient.treatment_type = el.modalPatientTreatment.value;
    state.patient.chief_complaint = el.modalPatientComplaint.value.trim();

    renderPatientUI();
    savePatientToBackend();
    el.patientModal.classList.add("hidden");
    showToast("Patient clinical profile updated!");
  });

  // Settings Modal Triggers
  el.sidebarSettingsBtn.addEventListener("click", () => el.settingsModal.classList.remove("hidden"));
  el.closeSettingsBtn.addEventListener("click", () => el.settingsModal.classList.add("hidden"));
  el.cancelSettingsBtn.addEventListener("click", () => el.settingsModal.classList.add("hidden"));

  el.providerSelect.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "gemini") {
      el.geminiGroup.classList.remove("hidden");
      el.openaiGroup.classList.add("hidden");
    } else if (val === "openai") {
      el.openaiGroup.classList.remove("hidden");
      el.geminiGroup.classList.add("hidden");
    } else {
      el.geminiGroup.classList.add("hidden");
      el.openaiGroup.classList.add("hidden");
    }
  });

  el.tempSlider.addEventListener("input", (e) => {
    el.tempValDisplay.textContent = e.target.value;
  });

  el.settingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const provider = el.providerSelect.value;
    const temp = parseFloat(el.tempSlider.value);
    const payload = { provider, temperature: temp };

    if (provider === "gemini" && el.geminiKeyInput.value.trim()) {
      payload.gemini_api_key = el.geminiKeyInput.value.trim();
    }
    if (provider === "openai" && el.openaiKeyInput.value.trim()) {
      payload.openai_api_key = el.openaiKeyInput.value.trim();
    }

    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        state.config = { ...state.config, ...payload };
        renderConfigUI();
        el.settingsModal.classList.add("hidden");
        showToast("AI engine configuration saved!");
      }
    } catch (err) {
      alert("Failed to save config: " + err.message);
    }
  });

  // Source & Doc Modals Close
  el.closeSourceModalBtn.addEventListener("click", () => el.sourceModal.classList.add("hidden"));
  el.closeSourceModalBtn2.addEventListener("click", () => el.sourceModal.classList.add("hidden"));
  el.closeDocModalBtn.addEventListener("click", () => el.docPreviewModal.classList.add("hidden"));
  el.closeDocModalBtn2.addEventListener("click", () => el.docPreviewModal.classList.add("hidden"));

  el.copyChunkBtn.addEventListener("click", () => {
    if (el.modalChunkText.textContent) {
      navigator.clipboard.writeText(el.modalChunkText.textContent);
      showToast("Source text excerpt copied!");
    }
  });

  // Auth Quick Demo Logins
  el.demoUserBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      el.authUsernameInput.value = btn.dataset.user;
      el.authPasswordInput.value = btn.dataset.pass;
      el.authForm.dispatchEvent(new Event("submit"));
    });
  });

  el.authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = el.authUsernameInput.value.trim();
    const password = el.authPasswordInput.value.trim();

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        state.user = data.user;
        localStorage.setItem("denta_user", JSON.stringify(data.user));
        renderUserUI();
        el.authModal.classList.add("hidden");
        showToast(`Welcome back, ${data.user.name}`);
      } else {
        el.authErrorMsg.textContent = data.detail || "Invalid credentials.";
        el.authErrorMsg.classList.remove("hidden");
      }
    } catch (err) {
      el.authErrorMsg.textContent = "Sign-in error: " + err.message;
      el.authErrorMsg.classList.remove("hidden");
    }
  });

  el.userProfileBtn.addEventListener("click", () => {
    if (confirm("Sign out of current staff account?")) {
      localStorage.removeItem("denta_user");
      state.user = null;
      promptLogin();
    }
  });
}

// ============================================================
// PATIENT EDIT MODAL LOGIC
// ============================================================
function openPatientEditModal() {
  const p = state.patient;
  el.modalPatientName.value = p.name;
  el.modalPatientAge.value = p.age;
  el.modalPatientGender.value = p.gender;
  el.modalPatientTreatment.value = p.treatment_type;
  el.modalPatientComplaint.value = p.chief_complaint;
  renderModalAlertTags();
  el.patientModal.classList.remove("hidden");
}

function renderModalAlertTags() {
  el.modalAlertsTags.innerHTML = "";
  state.patient.medical_alerts.forEach((alertText, idx) => {
    const tag = document.createElement("span");
    const isPenicillin = alertText.toLowerCase().includes("penicillin");
    tag.className = `alert-tag ${isPenicillin ? '' : 'warning-type'}`;
    tag.innerHTML = `
      <span>${escapeHTML(alertText)}</span>
      <button type="button" class="remove-tag-btn" data-idx="${idx}" style="background:none; border:none; color:inherit; font-weight:bold; cursor:pointer; margin-left:4px;">×</button>
    `;
    tag.querySelector(".remove-tag-btn").addEventListener("click", () => {
      state.patient.medical_alerts.splice(idx, 1);
      renderModalAlertTags();
    });
    el.modalAlertsTags.appendChild(tag);
  });
}

async function savePatientToBackend() {
  try {
    await fetch("/api/patient/current", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.patient)
    });
  } catch (err) {
    console.warn("Could not sync patient to backend:", err);
  }
}

// ============================================================
// MARKDOWN FORMATTER
// ============================================================
function formatMarkdown(text) {
  if (!text) return "";

  let html = text;

  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="source-code-view">$1</pre>');

  // Headings
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');

  // Blockquotes (Callouts)
  html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Lists
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*?<\/li>(\s*<li>.*?<\/li>)*)/g, '<ul>$1</ul>');

  // Paragraphs
  const paragraphs = html.split(/\n{2,}/);
  html = paragraphs.map(p => {
    p = p.trim();
    if (!p) return "";
    if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<block') || p.startsWith('<pre')) {
      return p;
    }
    return `<p>${p.replace(/\n/g, '<br/>')}</p>`;
  }).join('');

  return html;
}

function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ============================================================
// CONSULTATION NOTES EXPORT
// ============================================================
function exportConsultationNotes() {
  const p = state.patient;
  const session = state.sessions.find(s => s.id === state.activeSessionId);

  let doc = `========================================================\n`;
  doc += `CLINICAL DENTAL CONSULTATION & AI COPILOT SUMMARY\n`;
  doc += `Date: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}\n`;
  doc += `Clinician: ${state.user ? state.user.name : 'Dentist'} (${state.user ? state.user.license : 'N/A'})\n`;
  doc += `Session: ${session ? session.title : 'General Consultation'}\n`;
  doc += `========================================================\n\n`;

  doc += `[PATIENT PROFILE]\n`;
  doc += `Name: ${p.name}\n`;
  doc += `Age: ${p.age} | Sex: ${p.gender}\n`;
  doc += `Treatment: ${p.treatment_type}\n`;
  doc += `Medical Alerts / Allergies: ${(p.medical_alerts || []).join(', ') || 'None recorded'}\n`;
  doc += `Chief Complaint: ${p.chief_complaint}\n\n`;

  doc += `[CONSULTATION DIALOGUE]\n`;
  if (!session || session.messages.length === 0) {
    doc += `No clinical queries recorded in this session.\n\n`;
  } else {
    session.messages.forEach(m => {
      const role = m.role === 'user' ? 'CLINICIAN' : 'DENTAL COPILOT (RAG GROUNDED)';
      doc += `--------------------------------------------------------\n`;
      doc += `[${m.time || ''}] ${role}:\n${m.content.replace(/<[^>]+>/g, '')}\n\n`;
    });
  }

  doc += `========================================================\n`;
  doc += `DISCLAIMER: This output is decision-support evidence retrieved by Dental Assistant Copilot.\n`;
  doc += `It does not supersede the clinical judgment of the licensed attending dentist.\n`;

  navigator.clipboard.writeText(doc).then(() => {
    showToast("Consultation notes copied to clipboard!");
  }).catch(() => {
    alert("Could not copy notes to clipboard.");
  });
}

// Toast Notification Helper
let toastTimeout;
function showToast(message) {
  clearTimeout(toastTimeout);
  el.toastMsg.textContent = message;
  el.toast.classList.remove("hidden");
  toastTimeout = setTimeout(() => {
    el.toast.classList.add("hidden");
  }, 3500);
}
