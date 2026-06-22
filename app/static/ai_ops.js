// ---------------------------------------------------------------------------
// Tab navigation
// ---------------------------------------------------------------------------

const TAB_ORDER = ["ao-status", "ao-inbox", "ao-questions", "ao-feed"];

const tabs = document.querySelectorAll(".cc-tab");
const sections = {
  "ao-status":    document.getElementById("cc-ao-status"),
  "ao-inbox":     document.getElementById("cc-ao-inbox"),
  "ao-questions": document.getElementById("cc-ao-questions"),
  "ao-feed":      document.getElementById("cc-ao-feed"),
};

function activateTab(tabId) {
  tabs.forEach((btn) => {
    const active = btn.dataset.tab === tabId;
    btn.classList.toggle("cc-tab-active", active);
    btn.setAttribute("aria-selected", active ? "true" : "false");
  });
  Object.entries(sections).forEach(([id, el]) => {
    if (!el) return;
    el.classList.toggle("hidden", id !== tabId);
  });
  history.replaceState(null, "", `#${tabId}`);
}

tabs.forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

const initialTab = TAB_ORDER.includes(location.hash.slice(1))
  ? location.hash.slice(1)
  : "ao-status";
activateTab(initialTab);

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function postForm(url, formData) {
  const response = await fetch(url, { method: "POST", body: formData });
  const payload = await response.json();
  return { ok: response.ok, ...payload };
}

// ---------------------------------------------------------------------------
// Automation loop status + manual run
// ---------------------------------------------------------------------------

const automationCard = document.querySelector(".automation-card");
const automationRunNow = document.getElementById("automation-run-now");
const automationRunStatus = document.getElementById("automation-run-status");

function renderAutomationState(automation) {
  if (!automation) return;

  const enabledBadge = document.getElementById("automation-enabled-badge");
  const lastRunEl = document.getElementById("automation-last-run");
  const summaryEl = document.getElementById("automation-summary");
  const errorEl = document.getElementById("automation-error");
  const pendingEl = document.getElementById("automation-pending-approvals");
  const pendingExecutionEl = document.getElementById("automation-pending-execution");

  if (enabledBadge) {
    enabledBadge.className = `ao-status-badge ${automation.enabled ? "ao-badge-scheduled" : "ao-badge-error"}`;
    enabledBadge.textContent = automation.enabled ? "Enabled" : "Disabled";
  }
  if (lastRunEl) {
    lastRunEl.textContent = `Last run: ${automation.last_run ? automation.last_run.slice(0, 16).replace("T", " ") : "Not yet run"}`;
  }
  if (summaryEl) {
    summaryEl.textContent = `Summary: ${automation.last_summary || automation.last_result || "No summary yet."}`;
  }
  if (errorEl) {
    errorEl.textContent = automation.last_error ? `Error: ${automation.last_error}` : "";
  }
  if (pendingEl) {
    pendingEl.textContent = `Pending approvals: ${automation.pending_approvals ?? 0}`;
  }
  if (pendingExecutionEl) {
    pendingExecutionEl.textContent = `Approved waiting to execute: ${automation.approved_pending_execution ?? 0}`;
  }
  if (automationRunNow) {
    automationRunNow.disabled = Boolean(automation.is_running);
    automationRunNow.textContent = automation.is_running ? "Cycle running..." : "Run cycle now";
  }
}

if (automationRunNow) {
  automationRunNow.addEventListener("click", async () => {
    automationRunNow.disabled = true;
    if (automationRunStatus) automationRunStatus.textContent = "Running automation cycle...";

    const response = await fetch("/api/automation/run", { method: "POST" });
    const payload = await response.json();

    if (!response.ok && response.status !== 409) {
      if (automationRunStatus) automationRunStatus.textContent = payload.detail || "Unable to run automation.";
      automationRunNow.disabled = false;
      automationRunNow.textContent = "Run cycle now";
      return;
    }

    renderAutomationState(payload.automation);
    if (automationRunStatus) {
      automationRunStatus.textContent = response.status === 409
        ? (payload.detail || "Automation is already running.")
        : "Automation cycle completed.";
    }
  });
}

if (automationCard) {
  const refreshMinutes = parseInt(automationCard.dataset.refreshMinutes || "15", 10) || 15;
  const scheduleRefresh = (delayMs) => {
    window.setTimeout(() => {
      const activeTag = document.activeElement?.tagName;
      const isEditing = activeTag === "INPUT" || activeTag === "TEXTAREA" || activeTag === "SELECT";
      if (isEditing) {
        scheduleRefresh(60 * 1000);
        return;
      }
      window.location.reload();
    }, delayMs);
  };
  scheduleRefresh(refreshMinutes * 60 * 1000);
}

// ---------------------------------------------------------------------------
// Agent Status — register agent form
// ---------------------------------------------------------------------------

const registerToggle = document.getElementById("ao-register-toggle");
const registerFormWrap = document.getElementById("ao-register-form-wrap");
const registerForm = document.getElementById("ao-register-form");
const registerStatus = document.getElementById("ao-register-status");

if (registerToggle && registerFormWrap) {
  registerToggle.addEventListener("click", () => {
    const hidden = registerFormWrap.classList.toggle("hidden");
    registerToggle.textContent = hidden ? "+ Register agent" : "Cancel";
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    registerStatus.textContent = "Saving...";
    const formData = new FormData(registerForm);
    const response = await postForm("/api/aiops/agents", formData);
    if (!response.ok) {
      registerStatus.textContent = response.detail || "Unable to register agent.";
      return;
    }
    registerStatus.textContent = "Agent registered.";
    registerForm.reset();
    registerFormWrap.classList.add("hidden");
    registerToggle.textContent = "+ Register agent";
    appendAgentCard(response.agent);
  });
}

function appendAgentCard(agent) {
  const list = document.getElementById("ao-agent-list");
  if (!list) return;
  const emptyMsg = list.querySelector(".cc-empty");
  if (emptyMsg) emptyMsg.remove();

  const card = document.createElement("div");
  card.className = "ao-agent-card card";
  card.id = `ao-agent-${agent.id}`;
  card.dataset.id = agent.id;
  card.innerHTML = `
    <div class="ao-agent-head">
      <div class="ao-agent-name-wrap">
        <span class="ao-status-dot ao-dot-${escapeHtml(agent.status)}"></span>
        <p class="ao-agent-name">${escapeHtml(agent.name)}</p>
        <span class="ao-agent-type-label">${escapeHtml(agent.agent_type || "")}</span>
      </div>
      <span class="ao-status-badge ao-badge-${escapeHtml(agent.status)}">${escapeHtml(agent.status.charAt(0).toUpperCase() + agent.status.slice(1))}</span>
    </div>
    ${agent.description ? `<p class="ao-agent-desc">${escapeHtml(agent.description)}</p>` : ""}
    <p class="ao-last-result">Not yet run.</p>
  `;
  list.appendChild(card);
}

// ---------------------------------------------------------------------------
// Agent Status — Run now buttons
// ---------------------------------------------------------------------------

document.querySelectorAll(".ao-run-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const agentId = btn.dataset.agentId;
    const statusEl = document.getElementById(`ao-run-status-${agentId}`);
    const badgeEl = document.getElementById(`ao-badge-${agentId}`);

    btn.disabled = true;
    btn.textContent = "Running…";
    if (badgeEl) {
      badgeEl.className = "ao-status-badge ao-badge-running";
      badgeEl.textContent = "Running";
    }
    if (statusEl) statusEl.textContent = "Dispatching to OpenJarvis…";

    const response = await fetch(`/api/aiops/agents/${agentId}/run`, { method: "POST" });
    const payload = await response.json();

    if (!response.ok) {
      btn.disabled = false;
      btn.textContent = "Run now";
      if (badgeEl) {
        badgeEl.className = "ao-status-badge ao-badge-error";
        badgeEl.textContent = "Error";
      }
      if (statusEl) statusEl.textContent = payload.detail || "Failed to start agent.";
      return;
    }

    if (statusEl) statusEl.textContent = "Agent started — results will appear in Inbox when complete.";
  });
});

// ---------------------------------------------------------------------------
// Agent Inbox — action / dismiss buttons
// ---------------------------------------------------------------------------

document.querySelectorAll(".ao-action-btn, .ao-dismiss-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const inboxId = btn.dataset.inboxId;
    const action = btn.dataset.action;
    const feedback = document.getElementById(`inbox-feedback-${inboxId}`);
    if (feedback) feedback.textContent = "Saving...";

    const formData = new FormData();
    formData.append("status", action);
    const response = await postForm(`/api/aiops/inbox/${inboxId}`, formData);
    if (!response.ok) {
      if (feedback) feedback.textContent = response.detail || "Unable to update.";
      return;
    }

    const card = document.getElementById(`ao-inbox-${inboxId}`);
    if (card) {
      card.classList.remove("ao-unread");
      const unreadDot = card.querySelector(".ao-unread-dot");
      if (unreadDot) unreadDot.remove();
      const actionsEl = card.querySelector(".ao-inbox-actions");
      if (actionsEl) {
        const label = action === "actioned" ? "Actioned" : "Dismissed";
        actionsEl.outerHTML = `<p class="cc-answered-at ao-inbox-done">${escapeHtml(label)}</p>`;
      }
    }

    // Decrement unread badge
    const badge = document.querySelector('.cc-tab[data-tab="ao-inbox"] .cc-badge-warn');
    if (badge) {
      const count = parseInt(badge.textContent, 10) || 0;
      const next = count - 1;
      if (next <= 0) badge.remove();
      else badge.textContent = next;
    }
  });
});

// ---------------------------------------------------------------------------
// Agent Questions — answer forms
// ---------------------------------------------------------------------------

document.querySelectorAll(".ao-answer-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const qId = form.dataset.qId;
    const statusEl = document.getElementById(`aoq-status-${qId}`);
    if (statusEl) statusEl.textContent = "Saving answer...";

    const formData = new FormData(form);
    const response = await postForm(`/api/cc/questions/${qId}/answer`, formData);
    if (!response.ok) {
      if (statusEl) statusEl.textContent = response.detail || "Unable to save answer.";
      return;
    }

    const card = document.getElementById(`aoq-${qId}`);
    if (card) {
      card.classList.add("cc-answered");
      const badge = card.querySelector(".cc-q-status-badge");
      if (badge) {
        badge.className = "cc-q-status-badge q-answered";
        badge.textContent = "Answered";
      }
      const answerText = escapeHtml(response.question.answer || "");
      const answeredAt = (response.question.answered_at || "").slice(0, 10);
      const formWrap = card.querySelector(".ao-answer-form");
      if (formWrap) {
        formWrap.outerHTML = `
          <div class="cc-answer-display">
            <p class="section-label">Your answer</p>
            <p>${answerText}</p>
            <p class="cc-answered-at">Answered ${escapeHtml(answeredAt)}</p>
          </div>`;
      }
    }

    const qBadge = document.querySelector('.cc-tab[data-tab="ao-questions"] .cc-badge');
    if (qBadge) {
      const count = parseInt(qBadge.textContent, 10) || 0;
      const next = count - 1;
      if (next <= 0) qBadge.remove();
      else qBadge.textContent = next;
    }
  });
});
