// ---------------------------------------------------------------------------
// Tab navigation
// ---------------------------------------------------------------------------

const TAB_ORDER = ["inbox", "questions", "status", "changes", "approvals"];

const tabs = document.querySelectorAll(".cc-tab");
const sections = {
  inbox: document.getElementById("cc-inbox"),
  questions: document.getElementById("cc-questions"),
  status: document.getElementById("cc-status"),
  changes: document.getElementById("cc-changes"),
  approvals: document.getElementById("cc-approvals"),
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

// Restore tab from URL hash on page load
const initialTab = TAB_ORDER.includes(location.hash.slice(1))
  ? location.hash.slice(1)
  : "inbox";
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
// Command Inbox — new task form
// ---------------------------------------------------------------------------

const newTaskToggle = document.getElementById("new-task-toggle");
const newTaskFormWrap = document.getElementById("new-task-form-wrap");
const newTaskForm = document.getElementById("new-task-form");
const newTaskStatus = document.getElementById("new-task-status");

if (newTaskToggle && newTaskFormWrap) {
  newTaskToggle.addEventListener("click", () => {
    const hidden = newTaskFormWrap.classList.toggle("hidden");
    newTaskToggle.textContent = hidden ? "+ New task" : "Cancel";
  });
}

if (newTaskForm) {
  newTaskForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    newTaskStatus.textContent = "Saving...";
    const formData = new FormData(newTaskForm);
    const response = await postForm("/api/cc/tasks", formData);
    if (!response.ok) {
      newTaskStatus.textContent = response.detail || "Unable to save task.";
      return;
    }
    newTaskStatus.textContent = "Task saved.";
    newTaskForm.reset();
    newTaskFormWrap.classList.add("hidden");
    newTaskToggle.textContent = "+ New task";
    prependTaskCard(response.task);
  });
}

function prependTaskCard(task) {
  const taskList = document.getElementById("task-list");
  if (!taskList) return;

  const emptyMsg = taskList.querySelector(".cc-empty");
  if (emptyMsg) emptyMsg.remove();

  const priorityClass = `priority-${(task.priority || "medium").toLowerCase()}`;
  const statusClass = `status-${(task.status || "new").toLowerCase().replaceAll(" ", "-")}`;

  const card = document.createElement("div");
  card.className = "cc-task-card card";
  card.id = `task-${task.id}`;
  card.dataset.id = task.id;
  card.innerHTML = `
    <div class="cc-task-head">
      <div class="cc-task-meta">
        <span class="cc-priority-badge ${escapeHtml(priorityClass)}">${escapeHtml(task.priority || "")}</span>
        <span class="cc-status-badge ${escapeHtml(statusClass)}">${escapeHtml(task.status || "New")}</span>
      </div>
      <span class="cc-task-assignee">${escapeHtml(task.assigned_to || "")}</span>
    </div>
    <p class="cc-task-title">${escapeHtml(task.title || "")}</p>
    ${task.description ? `<p class="cc-task-desc">${escapeHtml(task.description)}</p>` : ""}
    <div class="cc-task-actions">
      <select class="cc-status-select" data-task-id="${escapeHtml(task.id)}" aria-label="Change status">
        ${["New", "In Progress", "Blocked", "Waiting for Michael", "Complete"]
          .map((s) => `<option value="${escapeHtml(s)}"${s === task.status ? " selected" : ""}>${escapeHtml(s)}</option>`)
          .join("")}
      </select>
      <span class="status-text cc-task-feedback" id="task-feedback-${escapeHtml(task.id)}"></span>
    </div>
  `;
  taskList.prepend(card);
  bindStatusSelect(card.querySelector(".cc-status-select"));
}

// ---------------------------------------------------------------------------
// Command Inbox — status select (works for server-rendered AND newly added cards)
// ---------------------------------------------------------------------------

function bindStatusSelect(select) {
  if (!select) return;
  select.addEventListener("change", async () => {
    const taskId = select.dataset.taskId;
    const feedback = document.getElementById(`task-feedback-${taskId}`);
    if (feedback) feedback.textContent = "Saving...";
    const formData = new FormData();
    formData.append("status", select.value);
    const response = await postForm(`/api/cc/tasks/${taskId}`, formData);
    if (!response.ok) {
      if (feedback) feedback.textContent = response.detail || "Unable to update.";
      return;
    }
    if (feedback) feedback.textContent = "Saved.";
    // Update status badge in the card
    const card = document.getElementById(`task-${taskId}`);
    if (card) {
      const badge = card.querySelector(".cc-status-badge");
      if (badge) {
        badge.className = `cc-status-badge status-${response.task.status.toLowerCase().replaceAll(" ", "-")}`;
        badge.textContent = response.task.status;
      }
    }
    setTimeout(() => { if (feedback) feedback.textContent = ""; }, 2500);
  });
}

document.querySelectorAll(".cc-status-select").forEach(bindStatusSelect);

// ---------------------------------------------------------------------------
// Agent Questions — answer forms
// ---------------------------------------------------------------------------

document.querySelectorAll(".cc-answer-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const qId = form.dataset.qId;
    const statusEl = document.getElementById(`q-status-${qId}`);
    const textarea = form.querySelector("textarea");
    if (statusEl) statusEl.textContent = "Saving answer...";

    const formData = new FormData(form);
    const response = await postForm(`/api/cc/questions/${qId}/answer`, formData);
    if (!response.ok) {
      if (statusEl) statusEl.textContent = response.detail || "Unable to save answer.";
      return;
    }

    // Replace form with a static answer display
    const card = document.getElementById(`q-${qId}`);
    if (card) {
      card.classList.add("cc-answered");
      const badge = card.querySelector(".cc-q-status-badge");
      if (badge) {
        badge.className = "cc-q-status-badge q-answered";
        badge.textContent = "Answered";
      }
      const answerText = escapeHtml(response.question.answer || "");
      const answeredAt = (response.question.answered_at || "").slice(0, 10);
      const formWrap = card.querySelector(".cc-answer-form");
      if (formWrap) {
        formWrap.outerHTML = `
          <div class="cc-answer-display">
            <p class="section-label">Michael's answer</p>
            <p>${answerText}</p>
            <p class="cc-answered-at">Answered ${escapeHtml(answeredAt)}</p>
          </div>`;
      }
    }
  });
});

// ---------------------------------------------------------------------------
// Approval Queue — decision buttons
// ---------------------------------------------------------------------------

document.querySelectorAll(".cc-approve-btn, .cc-changes-btn, .cc-reject-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const apId = btn.dataset.apId;
    const decision = btn.dataset.decision;
    const statusEl = document.getElementById(`ap-status-${apId}`);
    const form = btn.closest(".cc-approval-form");
    const feedbackEl = form ? form.querySelector("textarea") : null;
    const feedback = feedbackEl ? feedbackEl.value : "";

    if (statusEl) statusEl.textContent = "Saving decision...";

    const formData = new FormData();
    formData.append("decision", decision);
    formData.append("feedback", feedback);

    const response = await postForm(`/api/cc/approvals/${apId}/decide`, formData);
    if (!response.ok) {
      if (statusEl) statusEl.textContent = response.detail || "Unable to record decision.";
      return;
    }

    const card = document.getElementById(`ap-${apId}`);
    if (card) {
      const badge = card.querySelector(".cc-ap-status-badge");
      const labelMap = { approved: "Approved", rejected: "Rejected", needs_changes: "Needs Changes" };
      if (badge) {
        badge.className = `cc-ap-status-badge ap-${decision}`;
        badge.textContent = labelMap[decision] || decision;
      }
      if (form) {
        const decidedAt = (response.approval.decided_at || "").slice(0, 10);
        form.outerHTML = `
          <div class="cc-ap-decision-display">
            ${feedback ? `<p class="cc-agent-notes">Feedback: ${escapeHtml(feedback)}</p>` : ""}
            <p class="cc-answered-at">Decided ${escapeHtml(decidedAt)}</p>
          </div>`;
      }
    }

    // Update the pending count badge in the Approval Queue tab button
    const tabBtn = document.querySelector('.cc-tab[data-tab="approvals"] .cc-badge-warn');
    if (tabBtn) {
      const currentCount = parseInt(tabBtn.textContent, 10) || 0;
      const newCount = currentCount - 1;
      if (newCount <= 0) {
        tabBtn.remove();
      } else {
        tabBtn.textContent = newCount;
      }
    }
  });
});
