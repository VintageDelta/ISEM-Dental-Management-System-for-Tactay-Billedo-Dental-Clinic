// ===== Appointment Modals & Utility =====
document.addEventListener("DOMContentLoaded", () => {
  const createBtn = document.getElementById("create-appointment-btn");
  const appointmentModal = document.getElementById("appointment-modal");
  const closeAppointmentBtn = document.getElementById("close-appointment-btn");

  // Open / Close
  createBtn?.addEventListener("click", () => openModal("appointment-modal"));
  closeAppointmentBtn?.addEventListener("click", () => closeModal("appointment-modal"));
  appointmentModal?.addEventListener("click", e => {
    if (e.target === appointmentModal) closeModal("appointment-modal");
  });

  // Followup / Reschedule
  document.getElementById("close-followup-btn")?.addEventListener("click", () => closeModal("followup-modal"));
  document.getElementById("close-reschedule-btn")?.addEventListener("click", () => closeModal("reschedule-modal"));

  // Initialize
  initTimeValidation();
});

// ===== Modal Helpers =====
function openModal(id) {
  const modal = document.getElementById(id);
  const content = modal.querySelector("div");
  if (!modal || !content) return;

  modal.classList.remove("hidden");
  modal.classList.add("flex");

  setTimeout(() => {
    content.classList.remove("opacity-0", "scale-95");
    content.classList.add("opacity-100", "scale-100");
  }, 10);
}

function closeModal(id) {
  const modal = document.getElementById(id);
  const content = modal.querySelector("div");
  if (!modal || !content) return;

  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");

  setTimeout(() => modal.classList.add("hidden"), 200);
}

// ===== Fetch Booked Times =====
async function fetchBookedTimes(dentistId, date, location) {
  if (!dentistId || !date || !location) return [];
  try {
    const res = await fetch(`/dashboard/appointment/get-booked-times/?dentist=${dentistId}&date=${date}&location=${location}`);
    const data = await res.json();
    return data.booked || [];
  } catch (err) {
    console.error("Error fetching booked times:", err);
    return [];
  }
}

// ===== 24-hour converter =====
function to24Hour(hour, ampm) {
  hour = parseInt(hour);
  if (ampm === "PM" && hour < 12) return hour + 12;
  if (ampm === "AM" && hour === 12) return 0;
  return hour;
}

// ===== Time Validation =====
function initTimeValidation() {
  const dentistSelect = document.getElementById("dentist_name");
  const dateInput = document.getElementById("date");
  const locationSelect = document.getElementById("location");
  const hourSelect = document.getElementById("hour");
  const minuteSelect = document.getElementById("minute");
  const ampmSelect = document.getElementById("ampm");
  const timeError = document.getElementById("time-error");
  const timeHidden = document.getElementById("time_hidden");

  async function toggleTimeInputs() {
    const ready = dentistSelect.value && dateInput.value && locationSelect.value;

    // Enable/disable selects
    hourSelect.disabled = !ready;
    minuteSelect.disabled = !ready;
    ampmSelect.disabled = !ready;

    timeError.textContent = ready ? "" : "Please select dentist, location, and date first.";

    if (ready) {
      const booked = await fetchBookedTimes(dentistSelect.value, dateInput.value, locationSelect.value);

      // Reset hour options
      Array.from(hourSelect.options).forEach(o => {
        o.disabled = false;
        o.textContent = o.textContent.replace(" (Booked)", "");
      });

      // Disable booked hours
      booked.forEach(slot => {
        const [sh] = slot.start.split(":").map(Number);
        const [eh] = slot.end.split(":").map(Number);

        for (let h = sh; h <= eh; h++) {
          const hour12 = (h % 12) || 12;
          const opt = hourSelect.querySelector(`option[value="${hour12}"]`);
          if (opt) {
            opt.disabled = true;
            if (!opt.textContent.includes("Booked")) opt.textContent += " (Booked)";
          }
        }
      });
    }
  }

  dentistSelect.addEventListener("change", toggleTimeInputs);
  dateInput.addEventListener("change", toggleTimeInputs);
  locationSelect.addEventListener("change", toggleTimeInputs);

  // Update hidden time input when user selects custom time
  [hourSelect, minuteSelect, ampmSelect].forEach(el => {
    el.addEventListener("change", () => {
      const h = hourSelect.value;
      const m = minuteSelect.value;
      const ampm = ampmSelect.value;
      if (!h || !m || !ampm) return;
      timeHidden.value = `${String(to24Hour(h, ampm)).padStart(2, "0")}:${m}`;
    });
  });

  toggleTimeInputs(); // initial
}

document.getElementById("ampm").addEventListener("change", function () {
    const ampm = this.value;
    const hour = document.getElementById("hour");
    
    // Reset hour dropdown
    hour.innerHTML = `<option value="">Hour</option>`;

    if (ampm === "AM") {
        // 7 AM to 11 AM
        const hours = ["7", "8", "9", "10", "11"];
        hours.forEach(h => {
            hour.innerHTML += `<option value="${h}">${h}</option>`;
        });
    }

    if (ampm === "PM") {
        // 12 PM to 5 PM
        const hours = ["12", "1", "2", "3", "4", "5"];
        hours.forEach(h => {
            hour.innerHTML += `<option value="${h}">${h}</option>`;
        });
    }
});

// ===== Success Modal =====
const successModal = document.getElementById("success-modal");
const closeSuccessBtn = document.getElementById("close-success-btn");

function showSuccessModal() {
  if (!successModal) return;

  successModal.classList.remove("hidden");
  setTimeout(() => {
    successModal.querySelector("div").classList.remove("opacity-0", "scale-95");
    successModal.querySelector("div").classList.add("opacity-100", "scale-100");
  }, 10);
}

function closeSuccessModal() {
  if (!successModal) return;

  const content = successModal.querySelector("div");
  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");

  setTimeout(() => successModal.classList.add("hidden"), 200);
}

// Close on button click
closeSuccessBtn?.addEventListener("click", closeSuccessModal);

// Optional: close when clicking outside content
successModal?.addEventListener("click", e => {
  if (e.target === successModal) closeSuccessModal();
});

