// Show/hide modals for Appointments
document.addEventListener("DOMContentLoaded", function () {
  // ==========================
  // Elements
  // ==========================
  const createBtn = document.getElementById("create-appointment-btn");

  // Choose Patient Type Modal
  const chooseModal = document.getElementById("choose-type-modal");
  const chooseContent = document.getElementById("choose-type-content");
  const registeredBtn = document.getElementById("choose-registered");
  const guestBtn = document.getElementById("choose-guest");
  const cancelChooseBtn = document.getElementById("cancel-choose");

  // Appointment Modal
  const appointmentModal = document.getElementById("appointment-modal");
  const appointmentContent = appointmentModal.querySelector("div"); 
  const closeAppointmentBtn = document.getElementById("close-appointment-btn");

  // ==========================
  // Open Choose Modal first
  // ==========================
  createBtn.addEventListener("click", () => {
    chooseModal.classList.remove("hidden");
    chooseModal.classList.add("flex");

    setTimeout(() => {
      chooseContent.classList.remove("opacity-0", "scale-95");
      chooseContent.classList.add("opacity-100", "scale-100");
    }, 10);
  });

  // ==========================
  // Choose Registered → Show Appointment Modal

  registeredBtn.addEventListener("click", () => {
    // Close choose modal
    chooseContent.classList.remove("opacity-100", "scale-100");
    chooseContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      chooseModal.classList.add("hidden");
    }, 200);

    // Open appointment modal
    appointmentModal.classList.remove("hidden");
    appointmentModal.classList.add("flex");
    setTimeout(() => {
      appointmentContent.classList.remove("opacity-0", "scale-95");
      appointmentContent.classList.add("opacity-100", "scale-100");
    }, 10);
  });

  // ==========================
  // Choose Guest → Same for now
  // ==========================
  guestBtn.addEventListener("click", () => {
    chooseContent.classList.remove("opacity-100", "scale-100");
    chooseContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      chooseModal.classList.add("hidden");
    }, 200);

    appointmentModal.classList.remove("hidden");
    appointmentModal.classList.add("flex");
    setTimeout(() => {
      appointmentContent.classList.remove("opacity-0", "scale-95");
      appointmentContent.classList.add("opacity-100", "scale-100");
    }, 10);
  });

  // ==========================
  // Cancel Choose Modal
  // ==========================
  cancelChooseBtn.addEventListener("click", () => {
    chooseContent.classList.remove("opacity-100", "scale-100");
    chooseContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      chooseModal.classList.add("hidden");
    }, 200);
  });

  // ==========================
  // Close Appointment Modal
  // ==========================
  closeAppointmentBtn.addEventListener("click", () => {
    appointmentContent.classList.remove("opacity-100", "scale-100");
    appointmentContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      appointmentModal.classList.add("hidden");
    }, 200);
  });

  // Optional: close appointment modal if clicking backdrop
  appointmentModal.addEventListener("click", (e) => {
    if (e.target === appointmentModal) {
      appointmentContent.classList.remove("opacity-100", "scale-100");
      appointmentContent.classList.add("opacity-0", "scale-95");
      setTimeout(() => appointmentModal.classList.add("hidden"), 200);
    }
  });

  document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("close-followup-btn")
    .addEventListener("click", () => closeModal("followup-modal"));

  document.getElementById("close-reschedule-btn")
    .addEventListener("click", () => closeModal("reschedule-modal"));
  });

});

// ========== Modal Utility ==========
function openModal(id) {
  const modal = document.getElementById(id);
  const content = modal.querySelector("div");

  modal.classList.remove("hidden");
  modal.classList.add("flex");

  setTimeout(() => {
    content.classList.remove("opacity-0", "scale-95");
    content.classList.add("opacity-100", "scale-100");
  }, 10);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal(id);
  });
}

function closeModal(id) {
  const modal = document.getElementById(id);
  const content = modal.querySelector("div");

  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");

  setTimeout(() => modal.classList.add("hidden"), 200);
}

// ========== Attach close button listeners safely ==========
document.addEventListener("DOMContentLoaded", () => {
  const followBtn = document.getElementById("close-followup-btn");
  if (followBtn) {
    followBtn.addEventListener("click", () => closeModal("followup-modal"));
  }

  const reschedBtn = document.getElementById("close-reschedule-btn");
  if (reschedBtn) {
    reschedBtn.addEventListener("click", () => closeModal("reschedule-modal"));
  }
});
