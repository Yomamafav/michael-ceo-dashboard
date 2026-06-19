const form = document.getElementById("mobile-update-form");
const statusText = document.getElementById("form-status");
const quickFillButtons = document.querySelectorAll(".quick-fill");
const updateTypeSelect = document.getElementById("update_type");

if (quickFillButtons.length && updateTypeSelect) {
  quickFillButtons.forEach((button) => {
    button.addEventListener("click", () => {
      updateTypeSelect.value = button.dataset.value;
    });
  });
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusText.textContent = "Saving update...";

    const formData = new FormData(form);
    const response = await fetch("/api/mobile/update", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      statusText.textContent = payload.detail || "Unable to save update.";
      return;
    }

    statusText.textContent = "Update saved. It now appears in the update log below.";
    prependRecentUpdate(payload.entry);
    form.reset();
  });
}

function prependRecentUpdate(entry) {
  const updatesCard = document.getElementById("recent-updates-card");
  if (!updatesCard || !entry) {
    return;
  }

  const emptyState = updatesCard.querySelector(".empty-state");
  if (emptyState) {
    emptyState.remove();
  }

  const wrapper = document.createElement("details");
  wrapper.className = "detail-item";
  wrapper.open = true;
  wrapper.innerHTML = `
    <summary class="item-row interactive-row">
      <div>
        <p>${escapeHtml(entry.update_type || "")}</p>
        <span>${escapeHtml(entry.subject || "")}</span>
      </div>
    </summary>
    <div class="detail-panel">
      <p><strong>Subject:</strong> ${escapeHtml(entry.subject || "")}</p>
      <p><strong>Details:</strong> ${escapeHtml(entry.details || "")}</p>
      <p><strong>Saved:</strong> ${escapeHtml(entry.timestamp || "")}</p>
      <p><strong>Source:</strong> ${escapeHtml(entry.source || "mobile")}</p>
    </div>
  `;

  const cardHead = updatesCard.querySelector(".card-head");
  updatesCard.insertBefore(wrapper, cardHead.nextSibling);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// ---------------------------------------------------------------------------
// Item detail modal
// ---------------------------------------------------------------------------

const CATEGORY_LABELS = {
  schedule: "Schedule item",
  follow_ups: "Follow-up",
  payments: "Payment",
  bills: "Bill",
  construction_jobs: "Construction job",
  printing_jobs: "Printing job",
};

const itemModal = document.getElementById("item-modal");
const modalCloseButton = document.getElementById("modal-close");
const modalCategoryLabel = document.getElementById("modal-category-label");
const modalTitle = document.getElementById("modal-title");
const modalFields = document.getElementById("modal-fields");
const modalActions = document.getElementById("modal-actions");
const modalNoteInput = document.getElementById("modal-note-input");
const modalNoteSubmit = document.getElementById("modal-note-submit");
const modalStatus = document.getElementById("modal-status");
const modalHistoryList = document.getElementById("modal-history-list");

let modalDirty = false;
let currentCategory = null;
let currentItem = null;

document.addEventListener("click", (event) => {
  const trigger = event.target.closest(".clickable-item");
  if (trigger) {
    openItemModal(trigger.dataset.category, trigger.dataset.id);
  }
});

if (modalCloseButton) {
  modalCloseButton.addEventListener("click", closeItemModal);
}

if (itemModal) {
  itemModal.addEventListener("click", (event) => {
    if (event.target === itemModal) {
      closeItemModal();
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && itemModal && !itemModal.classList.contains("hidden")) {
    closeItemModal();
  }
});

if (modalNoteSubmit) {
  modalNoteSubmit.addEventListener("click", async () => {
    const note = modalNoteInput.value.trim();
    if (!note || !currentCategory || !currentItem) {
      return;
    }
    modalStatus.textContent = "Saving note...";
    const formData = new FormData();
    formData.append("note", note);
    const response = await postForm(`/api/items/${currentCategory}/${currentItem.id}/note`, formData);
    if (!response.ok) {
      modalStatus.textContent = response.detail || "Unable to save note.";
      return;
    }
    modalNoteInput.value = "";
    modalStatus.textContent = "Note added.";
    modalDirty = true;
    renderItem(currentCategory, response.item);
  });
}

async function openItemModal(category, itemId) {
  if (!itemModal || !category || !itemId) {
    return;
  }
  modalStatus.textContent = "Loading...";
  itemModal.classList.remove("hidden");
  itemModal.setAttribute("aria-hidden", "false");

  const response = await getJson(`/api/items/${category}/${itemId}`);
  if (!response.ok) {
    modalStatus.textContent = response.detail || "Unable to load item.";
    return;
  }
  modalStatus.textContent = "";
  renderItem(category, response.item);
}

function closeItemModal() {
  if (!itemModal) {
    return;
  }
  itemModal.classList.add("hidden");
  itemModal.setAttribute("aria-hidden", "true");
  currentCategory = null;
  currentItem = null;
  if (modalDirty) {
    modalDirty = false;
    window.location.reload();
  }
}

function renderItem(category, item) {
  currentCategory = category;
  currentItem = item;

  modalCategoryLabel.textContent = CATEGORY_LABELS[category] || category;
  modalTitle.textContent = item.name || item.job || "Detail";

  const rows = [
    ["Customer / Name", item.name],
    ["Phone", item.phone],
    ["Email", item.email],
    ["Job / Project", item.job],
    ["Amount", item.amount],
    ["Status", item.status],
    ["Due / Deadline", item.due],
    ["Notes", item.notes],
    ["Next action", item.next_action],
  ];

  modalFields.innerHTML = rows
    .filter(([, value]) => value)
    .map(([label, value]) => `<p><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</p>`)
    .join("");

  renderActions(category, item);
  renderHistory(item.update_history || []);
}

function renderHistory(history) {
  if (!history.length) {
    modalHistoryList.innerHTML = "<li>No updates yet.</li>";
    return;
  }
  modalHistoryList.innerHTML = history
    .map((entry) => `<li><strong>${escapeHtml(entry.timestamp || "")}</strong> &mdash; ${escapeHtml(entry.text || "")}</li>`)
    .join("");
}

function renderActions(category, item) {
  modalActions.innerHTML = "";

  if (category === "payments") {
    if ((item.payment_type || "").toLowerCase() === "deposit" && item.status !== "Paid") {
      modalActions.appendChild(makeActionButton("Mark deposit paid", () => runAction(`/api/items/payments/${item.id}/deposit-paid`)));
    } else if (item.status !== "Received") {
      modalActions.appendChild(makeActionButton("Mark payment received", () => runAction(`/api/items/payments/${item.id}/payment-received`)));
    }
  } else {
    const completeLabel = category === "bills" ? "Mark paid" : "Mark complete";
    modalActions.appendChild(makeActionButton(completeLabel, () => runAction(`/api/items/${category}/${item.id}/complete`)));
  }

  if (["follow_ups", "construction_jobs", "printing_jobs"].includes(category)) {
    modalActions.appendChild(makeActionButton("Copy text message", copyTextMessage));
  }
}

function makeActionButton(label, handler) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}

async function runAction(url) {
  modalStatus.textContent = "Saving...";
  const response = await postForm(url, new FormData());
  if (!response.ok) {
    modalStatus.textContent = response.detail || "Unable to complete action.";
    return;
  }
  modalStatus.textContent = "Saved.";
  modalDirty = true;
  renderItem(currentCategory, response.item);
}

function copyTextMessage() {
  if (!currentItem) {
    return;
  }
  const name = currentItem.name || "there";
  const topic = currentItem.job || "your project";
  const nextAction = currentItem.next_action ? ` ${currentItem.next_action}` : "";
  const message = `Hi ${name}, this is Michael following up about ${topic}.${nextAction}`.trim();

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(message)
      .then(() => {
        modalStatus.textContent = "Message copied to clipboard.";
      })
      .catch(() => {
        modalStatus.textContent = message;
      });
  } else {
    modalStatus.textContent = message;
  }
}

async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  return { ok: response.ok, ...payload };
}

async function postForm(url, formData) {
  const response = await fetch(url, { method: "POST", body: formData });
  const payload = await response.json();
  return { ok: response.ok, ...payload };
}

// ---------------------------------------------------------------------------
// Add follow-up modal
// ---------------------------------------------------------------------------

const addFollowUpButton = document.getElementById("add-follow-up-button");
const followUpModal = document.getElementById("followup-modal");
const followUpModalClose = document.getElementById("followup-modal-close");
const followUpForm = document.getElementById("followup-form");
const followUpStatus = document.getElementById("followup-status");

if (addFollowUpButton && followUpModal) {
  addFollowUpButton.addEventListener("click", () => {
    followUpModal.classList.remove("hidden");
    followUpModal.setAttribute("aria-hidden", "false");
  });
}

if (followUpModalClose && followUpModal) {
  followUpModalClose.addEventListener("click", () => {
    followUpModal.classList.add("hidden");
    followUpModal.setAttribute("aria-hidden", "true");
  });
  followUpModal.addEventListener("click", (event) => {
    if (event.target === followUpModal) {
      followUpModal.classList.add("hidden");
      followUpModal.setAttribute("aria-hidden", "true");
    }
  });
}

if (followUpForm) {
  followUpForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    followUpStatus.textContent = "Saving...";
    const formData = new FormData(followUpForm);
    const response = await postForm("/api/follow-ups", formData);
    if (!response.ok) {
      followUpStatus.textContent = response.detail || "Unable to save follow-up.";
      return;
    }
    followUpStatus.textContent = "Follow-up added.";
    window.location.reload();
  });
}
