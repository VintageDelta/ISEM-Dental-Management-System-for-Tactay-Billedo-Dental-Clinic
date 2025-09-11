// Show/hide appointment modal
document.addEventListener("DOMContentLoaded", function () {
  const createBtn = document.getElementById("create-appointment-btn");
  const modal = document.getElementById("appointment-modal");
  const modalContent = modal.querySelector("div"); // inner content
  const closeBtn = document.getElementById("close-appointment-btn");

  createBtn.addEventListener("click", () => {
    modal.classList.remove("hidden");
    // Trigger Tailwind transition
    setTimeout(() => {
      modalContent.classList.remove("opacity-0", "scale-95");
      modalContent.classList.add("opacity-100", "scale-100");
    }, 10);
  });

  closeBtn.addEventListener("click", () => {
    modalContent.classList.remove("opacity-100", "scale-100");
    modalContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => modal.classList.add("hidden"), 200);
  });

  // Optional: close modal if user clicks outside content
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modalContent.classList.remove("opacity-100", "scale-100");
      modalContent.classList.add("opacity-0", "scale-95");
      setTimeout(() => modal.classList.add("hidden"), 200);
    }
  });
});
