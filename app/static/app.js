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

    statusText.textContent = "Update saved. Refresh to see it in the recent list.";
    form.reset();
  });
}
