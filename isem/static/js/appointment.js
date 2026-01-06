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

  // Cancel confirmation wiring
  const statusCancelBtn = document.getElementById("status-cancel-btn");
  console.log("statusCancelBtn found?", statusCancelBtn); 
  const confirmYes = document.getElementById("cancel-confirm-yes");
  const confirmNo = document.getElementById("cancel-confirm-no");

  let pendingCancelEventId = null;

  statusCancelBtn?.addEventListener("click", () => {
    console.log("Cancel button clicked");    // TEMP DEBUG
    if (!window.currentEventId) return;     // calendar.js sets currentEventId
    pendingCancelEventId = window.currentEventId;
    openModal("cancel-confirm-modal");
  });

  confirmNo?.addEventListener("click", () => {
    pendingCancelEventId = null;
    closeModal("cancel-confirm-modal");
  });

confirmYes?.addEventListener("click", () => {
  if (!pendingCancelEventId) return;

  const idStr = String(pendingCancelEventId);

  fetch(`/dashboard/appointment/update-status/${pendingCancelEventId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ status: "cancelled" })
  })
    .then(res => res.json())
    .then(data => {
      if (!data.success) return;

      // 1) Update the event object in the timeline immediately
      if (window.timelineCalendar) {
        const ev = window.timelineCalendar.getEventById(idStr);
        if (ev) {
          ev.setExtendedProp("status", "cancelled"); // rerenders this event [web:234][web:263]
        }
      }

      // 2) Refetch from the server so everything stays in sync
      if (window.timelineCalendar) window.timelineCalendar.refetchEvents();
      if (window.mainCalendar) window.mainCalendar.refetchEvents();

      // 3) Rebuild today's side list after refetch
      setTimeout(() => {
        if (typeof window.renderTodaysAppointments === "function") {
          window.renderTodaysAppointments();
        }
      }, 300);

      closeModal("cancel-confirm-modal");
      closeModal("status-modal");
    });

  pendingCancelEventId = null;
});


  // Status / Followup / Reschedule
  document.getElementById("close-status-btn")?.addEventListener("click", () => closeModal("status-modal"));
  document.getElementById("close-followup-btn")?.addEventListener("click", () => closeModal("followup-modal"));
  document.getElementById("close-reschedule-btn")?.addEventListener("click", () => closeModal("reschedule-modal"));

    // Notify Patient modal wiring
  const notifyPatientBtn = document.getElementById("notify-patient-btn");
  const closeNotifyBtn = document.getElementById("close-notify-btn");
  const notifySmsBtn = document.getElementById("notify-sms-btn");
  const notifyEmailBtn = document.getElementById("notify-email-btn");

  notifyPatientBtn?.addEventListener("click", () => {
    if (!window.currentEventId) return; // set by calendar.js when opening status modal
    openModal("notify-modal");
  });

  closeNotifyBtn?.addEventListener("click", () => {
    closeModal("notify-modal");
  });

  // Optional: clicking on the backdrop closes the notify modal as well
  const notifyModal = document.getElementById("notify-modal");
  notifyModal?.addEventListener("click", (e) => {
    if (e.target === notifyModal) closeModal("notify-modal");
  });

  // For now, just close after click; you can replace with real API calls later
  notifySmsBtn?.addEventListener("click", () => {
    console.log("Send SMS to patient for event", window.currentEventId);
    // TODO: call your SMS endpoint here
    closeModal("notify-modal");
  });

  notifyEmailBtn?.addEventListener("click", () => {
    console.log("Send EMAIL to patient for event", window.currentEventId);
    // TODO: call your Email endpoint here
    closeModal("notify-modal");
  });

  
  // Initialize
  initTimeValidation();
  initRescheduleForm();
  initFollowupForm();
});

// ===== Modal Helpers =====
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  // find the first direct child div (the white box)
  const content = modal.querySelector(":scope > div");
  if (!content) return;

  modal.classList.remove("hidden");
  modal.classList.add("flex");

  // start from transparent & slightly scaled down
  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");

  // animate to visible on next frame
  requestAnimationFrame(() => {
    content.classList.remove("opacity-0", "scale-95");
    content.classList.add("opacity-100", "scale-100");
  });
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  const content = modal.querySelector(":scope > div");
  if (!content) return;

  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");

  // duration-200 = 200ms
  setTimeout(() => {
    modal.classList.add("hidden");
  }, 200);
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
      const booked = await fetchBookedTimes(
        dentistSelect.value,
        dateInput.value,
        locationSelect.value
      );

      // Reset hour options (if they exist)
      Array.from(hourSelect.options).forEach(o => {
        o.disabled = false;
      });

      // Disable booked hours
      booked.forEach(slot => {
        const [sh] = slot.start.split(":").map(Number);
        const [eh] = slot.end.split(":").map(Number);

        for (let h = sh; h <= eh; h++) {
          const hour12 = (h % 12) || 12;
          const opt = hourSelect.querySelector(`option[value="${hour12}"]`);
          if (opt) {
            opt.disabled = true; // browser will gray it out
          }
        }
      });
    }
  }

  // When dentist/date/location change, (re)fetch and apply booked times
  dentistSelect.addEventListener("change", toggleTimeInputs);
  dateInput.addEventListener("change", toggleTimeInputs);
  locationSelect.addEventListener("change", toggleTimeInputs);

  // When AM/PM changes, rebuild hours AND then reapply booked-time disabling
  ampmSelect.addEventListener("change", function () {
    const ampm = this.value;

    // Reset hour dropdown
    hourSelect.innerHTML = `<option value="">Hour</option>`;

    if (ampm === "AM") {
      // 8 AM to 11 AM
      const hours = ["8", "9", "10", "11"];
      hours.forEach(h => {
        hourSelect.innerHTML += `<option value="${h}">${h}</option>`;
      });
    }

    if (ampm === "PM") {
      // 12 PM to 5 PM
      const hours = ["12", "1", "2", "3", "4", "5"];
      hours.forEach(h => {
        hourSelect.innerHTML += `<option value="${h}">${h}</option>`;
      });
    }

    // After regenerating hour options, apply booked/disabled state
    toggleTimeInputs();
  });

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

    // ===== Service search + selected tags =====
  const serviceSearchInput = document.getElementById("service-search");
  const servicesContainer = document.getElementById("services-checkboxes");
  const serviceCheckboxes = servicesContainer
    ? servicesContainer.querySelectorAll('input.service-checkbox')
    : [];
  const selectedTagsContainer = document.getElementById("selected-services-tags");
  const selectedEmptyText = document.getElementById("selected-services-empty");

  function refreshSelectedServiceTags() {
    if (!selectedTagsContainer || !selectedEmptyText) return;

    selectedTagsContainer.innerHTML = "";

    const checked = Array.from(serviceCheckboxes).filter(cb => cb.checked);

    if (checked.length === 0) {
      selectedEmptyText.classList.remove("hidden");
      return;
    }

    selectedEmptyText.classList.add("hidden");

    checked.forEach(cb => {
      const label = cb.closest("label");
      const nameEl = label ? label.querySelector("span") : null;
      const name = nameEl ? nameEl.textContent.trim() : `Service ${cb.value}`;

      // Create a pill/tag
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className =
        "flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 " +
        "rounded-full text-xs hover:bg-blue-200";

      const text = document.createElement("span");
      text.textContent = name;

      const close = document.createElement("span");
      close.textContent = "✕";
      close.className = "text-[10px]";

      pill.appendChild(text);
      pill.appendChild(close);

      // Clicking the pill unchecks the checkbox and refreshes
      pill.addEventListener("click", () => {
        cb.checked = false;
        refreshSelectedServiceTags();
      });

      selectedTagsContainer.appendChild(pill);
    });
  }

  // Hook checkboxes to refresh tags
  Array.from(serviceCheckboxes).forEach(cb => {
    cb.addEventListener("change", refreshSelectedServiceTags);
  });

  // Live search filter on services
  if (serviceSearchInput && servicesContainer) {
    serviceSearchInput.addEventListener("input", () => {
      const q = serviceSearchInput.value.toLowerCase();

      servicesContainer.querySelectorAll("label").forEach(label => {
        const nameEl = label.querySelector("span");
        const name = nameEl ? nameEl.textContent.toLowerCase() : "";
        label.style.display = name.includes(q) ? "" : "none";
      });
    });
  }

  // Initial state
  refreshSelectedServiceTags();
    // --- Form-level validation: enable Save only when all required fields are filled ---
  const addForm = document.querySelector("#appointment-modal form");
  const addSaveBtn = addForm ? addForm.querySelector('button[type="submit"]') : null;

  function validateAddForm() {
    if (!addForm || !addSaveBtn) return;

    const dentist = dentistSelect.value;
    const location = locationSelect.value;
    const date = dateInput.value;
    const ampm = ampmSelect.value;
    const hour = hourSelect.value;
    const minute = minuteSelect.value;
    const email = document.getElementById("email")?.value || "";

    const anyServiceChecked = Array.from(
      document.querySelectorAll("#services-checkboxes input.service-checkbox")
    ).some(cb => cb.checked);

    const timeOk = ampm && hour && minute;
    const basicOk = dentist && location && date && email && anyServiceChecked && timeOk;

    addSaveBtn.disabled = !basicOk;
    addSaveBtn.classList.toggle("opacity-50", !basicOk);
    addSaveBtn.classList.toggle("cursor-not-allowed", !basicOk);
  }

  // Revalidate whenever relevant fields change
  [
    dentistSelect,
    locationSelect,
    dateInput,
    ampmSelect,
    hourSelect,
    minuteSelect,
    document.getElementById("email"),
    ...Array.from(document.querySelectorAll("#services-checkboxes input.service-checkbox"))
  ].forEach(el => {
    el && el.addEventListener("change", validateAddForm);
    el && el.addEventListener("input", validateAddForm);
  });

  // Initial state
  validateAddForm();

}


// ===== Success Modal =====
const successModal = document.getElementById("success-modal");
const closeSuccessBtn = document.getElementById("close-success-btn");

function showSuccessModal() {
  openModal("success-modal");
}

function closeSuccessModal() {
  closeModal("success-modal");
}

closeSuccessBtn?.addEventListener("click", closeSuccessModal);
successModal?.addEventListener("click", e => {
  if (e.target === successModal) closeSuccessModal();
});

// Close on button click
closeSuccessBtn?.addEventListener("click", closeSuccessModal);

// Optional: close when clicking outside content
successModal?.addEventListener("click", e => {
  if (e.target === successModal) closeSuccessModal();
});


// ===== Failed Modal =====
const failedModal = document.getElementById("failed-modal");
const closeFailedBtn = document.getElementById("close-failed-btn");
const failedMessageText = document.getElementById("failed-message-text");

function showFailedModal(message) {
  if (!failedModal || !failedMessageText) return;
  failedMessageText.textContent = message || "Something went wrong.";
  openModal("failed-modal");
}

function closeFailedModal() {
  closeModal("failed-modal");
}

closeFailedBtn?.addEventListener("click", closeFailedModal);
failedModal?.addEventListener("click", e => {
  if (e.target === failedModal) closeFailedModal();
});

function to24Hour(hour, ampm) {
  hour = parseInt(hour);
  if (ampm === "PM" && hour < 12) return hour + 12;
  if (ampm === "AM" && hour === 12) return 0;
  return hour;
}


//reshed form
function initRescheduleForm() {
  const hourSelect = document.getElementById("resched-hour");
  const minuteSelect = document.getElementById("resched-minute");
  const ampmSelect = document.getElementById("resched-ampm");
  const timeHidden = document.getElementById("resched-time-hidden");

  // Rebuild hours when AM/PM changes
  ampmSelect?.addEventListener("change", function() {
    const ampm = this.value;
    hourSelect.innerHTML = '<option value="" selected disabled >hour</option>';

    if (ampm === "AM") {
      ["7", "8", "9", "10", "11"].forEach(h => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        hourSelect.appendChild(opt);
      });
    } else if (ampm === "PM") {
      ["12", "1", "2", "3", "4", "5"].forEach(h => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        hourSelect.appendChild(opt);
      });
    }
  });

  // Update hidden 24h time
  [hourSelect, minuteSelect, ampmSelect].forEach(el => {
    el?.addEventListener("change", () => {
      const h = hourSelect.value;
      const m = minuteSelect.value;
      const ampm = ampmSelect.value;
      if (!h || !m || !ampm) return;
      timeHidden.value = `${String(to24Hour(h, ampm)).padStart(2, "0")}:${m}`;
    });
  });

  // ===== Service search + selected tags for reschedule =====
  const serviceSearchInput = document.getElementById("resched-service-search");
  const servicesContainer = document.getElementById("resched-services-checkboxes");
  const serviceCheckboxes = servicesContainer
    ? servicesContainer.querySelectorAll('input.resched-service-checkbox')
    : [];
  const selectedTagsContainer = document.getElementById("resched-selected-services-tags");
  const selectedEmptyText = document.getElementById("resched-selected-services-empty");

  window.refreshReschedSelectedServiceTags = function() {
    if (!selectedTagsContainer || !selectedEmptyText) return;

    selectedTagsContainer.innerHTML = "";

    const checked = Array.from(serviceCheckboxes).filter(cb => cb.checked);

    if (checked.length === 0) {
      selectedEmptyText.classList.remove("hidden");
      return;
    }

    selectedEmptyText.classList.add("hidden");

    checked.forEach(cb => {
      const label = cb.closest("label");
      const nameEl = label ? label.querySelector("span") : null;
      const name = nameEl ? nameEl.textContent.trim() : `Service ${cb.value}`;

      const pill = document.createElement("button");
      pill.type = "button";
      pill.className =
        "flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 " +
        "rounded-full text-xs hover:bg-blue-200";

      const text = document.createElement("span");
      text.textContent = name;

      const close = document.createElement("span");
      close.textContent = "✕";
      close.className = "text-[10px]";

      pill.appendChild(text);
      pill.appendChild(close);

      pill.addEventListener("click", () => {
        cb.checked = false;
        refreshReschedSelectedServiceTags();
      });

      selectedTagsContainer.appendChild(pill);
    });
  };

  Array.from(serviceCheckboxes).forEach(cb => {
    cb.addEventListener("change", refreshReschedSelectedServiceTags);
  });

  if (serviceSearchInput && servicesContainer) {
    serviceSearchInput.addEventListener("input", () => {
      const q = serviceSearchInput.value.toLowerCase();
      servicesContainer.querySelectorAll("label").forEach(label => {
        const nameEl = label.querySelector("span");
        const name = nameEl ? nameEl.textContent.toLowerCase() : "";
        label.style.display = name.includes(q) ? "" : "none";
      });
    });
  }

  refreshReschedSelectedServiceTags();

    // --- Reschedule form validation: enable Save Changes only when complete ---
  const reschedForm = document.getElementById("reschedule-form");
  const reschedSaveBtn = reschedForm ? reschedForm.querySelector('button[type="submit"]') : null;

  function validateReschedForm() {
    if (!reschedForm || !reschedSaveBtn) return;

    const dentist = document.getElementById("resched-dentist")?.value || "";
    const location = document.getElementById("resched-location")?.value || "";
    const date = document.getElementById("resched-date")?.value || "";
    const ampm = ampmSelect.value;
    const hour = hourSelect.value;
    const minute = minuteSelect.value;
    const email = document.getElementById("resched-email")?.value || "";

    const anyServiceChecked = Array.from(
      document.querySelectorAll("#resched-services-checkboxes input.resched-service-checkbox")
    ).some(cb => cb.checked);

    const timeOk = ampm && hour && minute;
    const basicOk = dentist && location && date && email && anyServiceChecked && timeOk;

    reschedSaveBtn.disabled = !basicOk;
    reschedSaveBtn.classList.toggle("opacity-50", !basicOk);
    reschedSaveBtn.classList.toggle("cursor-not-allowed", !basicOk);
  }

  [
    document.getElementById("resched-dentist"),
    document.getElementById("resched-location"),
    document.getElementById("resched-date"),
    ampmSelect,
    hourSelect,
    minuteSelect,
    document.getElementById("resched-email"),
    ...Array.from(document.querySelectorAll("#resched-services-checkboxes input.resched-service-checkbox"))
  ].forEach(el => {
    el && el.addEventListener("change", validateReschedForm);
    el && el.addEventListener("input", validateReschedForm);
  });

  validateReschedForm();

}

// ===== Follow-up form (acts like create appointment, but linked to original) =====
function initFollowupForm() {
  const dateInput = document.getElementById("followup-date");
  const hourSelect = document.getElementById("followup-hour");
  const minuteSelect = document.getElementById("followup-minute");
  const ampmSelect = document.getElementById("followup-ampm");
  const timeHidden = document.getElementById("followup-time-hidden");
  const followupForm = document.getElementById("followup-form");
  const followupSaveBtn = followupForm
    ? followupForm.querySelector('button[type="submit"]')
    : null;

  if (!followupForm) return;

  // Build hours when AM/PM changes (similar to reschedule)
  ampmSelect?.addEventListener("change", function () {
    const ampm = this.value;
    hourSelect.innerHTML = '<option value="" selected disabled>Hour</option>';

    if (ampm === "AM") {
      ["7", "8", "9", "10", "11"].forEach((h) => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        hourSelect.appendChild(opt);
      });
    } else if (ampm === "PM") {
      ["12", "1", "2", "3", "4", "5"].forEach((h) => {
        const opt = document.createElement("option");
        opt.value = h;
        opt.textContent = h;
        hourSelect.appendChild(opt);
      });
    }
  });

  // Update hidden 24h time
  [hourSelect, minuteSelect, ampmSelect].forEach((el) => {
    el?.addEventListener("change", () => {
      const h = hourSelect.value;
      const m = minuteSelect.value;
      const ampm = ampmSelect.value;
      if (!h || !m || !ampm) return;
      timeHidden.value = `${String(to24Hour(h, ampm)).padStart(2, "0")}:${m}`;
    });
  });

  // Basic validation: require date + full time
  function validateFollowupForm() {
    if (!followupSaveBtn) return;

    const date = dateInput?.value || "";
    const ampm = ampmSelect?.value || "";
    const hour = hourSelect?.value || "";
    const minute = minuteSelect?.value || "";

    const timeOk = ampm && hour && minute;
    const basicOk = date && timeOk;

    followupSaveBtn.disabled = !basicOk;
    followupSaveBtn.classList.toggle("opacity-50", !basicOk);
    followupSaveBtn.classList.toggle("cursor-not-allowed", !basicOk);
  }

  [dateInput, ampmSelect, hourSelect, minuteSelect].forEach((el) => {
    el && el.addEventListener("change", validateFollowupForm);
    el && el.addEventListener("input", validateFollowupForm);
  });

  validateFollowupForm();
}
