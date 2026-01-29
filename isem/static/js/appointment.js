let currentPatientId = null;
// Global refs for main create-appointment form/button
let addForm = null;
let addSaveBtn = null;
let reschedAppointmentId = null;
let doneOdontogramHandlerAttached = false;

let reschedHandlerAttached = false;

// ===== Appointment Modals & Utility =====
document.addEventListener("DOMContentLoaded", () => {
  const createBtn = document.getElementById("create-appointment-btn");
  
  const appointmentModal = document.getElementById("appointment-modal");
  const closeAppointmentBtn = document.getElementById("close-appointment-btn");

  // Open / Close
  createBtn?.addEventListener("click", () => openAppointmentModal("appointment-modal"));
  closeAppointmentBtn?.addEventListener("click", () => closeAppointmentModal("appointment-modal"));
  appointmentModal?.addEventListener("click", e => {
    if (e.target === appointmentModal) closeAppointmentModal("appointment-modal");
  });

  // Cancel confirmation wiring
  const statusCancelBtn = document.getElementById("status-cancel-btn");
  console.log("statusCancelBtn found?", statusCancelBtn); 
  const confirmYes = document.getElementById("cancel-confirm-yes");
  const confirmNo = document.getElementById("cancel-confirm-no");

  let pendingCancelEventId = null;

  // updates the total price live (Step 1 only; Step 2 is handled in initDoneStepsModal)
  const doneServicesContainer = document.getElementById("done-services-checkboxes");
  if (doneServicesContainer) {
    doneServicesContainer.addEventListener("change", () => {
      computeDoneMedicalTotal();
    });
  }


  // === Original appointment modal instance ===
  initServiceSearchAndTags({
    searchInput: document.getElementById("service-search"),
    servicesContainer: document.getElementById("services-checkboxes"),
    checkboxSelector: "input.service-checkbox",
    selectedTagsContainer: document.getElementById("selected-services-tags"),
    selectedEmptyText: document.getElementById("selected-services-empty"),
  });

  // === Done Steps modal instance (Step 1) ===
  window.refreshDoneStep1Tags = initServiceSearchAndTags({
    searchInput: document.getElementById("done-service-search"),
    servicesContainer: document.getElementById("done-services-checkboxes"),
    checkboxSelector: "input.done-service-checkbox",
    selectedTagsContainer: document.getElementById("done-selected-services-tags"),
    selectedEmptyText: document.getElementById("done-selected-services-empty"),
  });

  // === Done-odontogram Step 3 instance ===
  window.refreshDoneStep3Tags = initServiceSearchAndTags({
    searchInput: document.getElementById("done-odontogram-service-search-0"),
    servicesContainer: document.getElementById("done-odontogram-services-checkboxes-0"),
    checkboxSelector: "input.done-odontogram-service-checkbox",
    selectedTagsContainer: document.getElementById("done-odontogram-selected-services-tags-0"),
    selectedEmptyText: document.getElementById("done-odontogram-selected-services-empty-0"),
  });


  statusCancelBtn?.addEventListener("click", () => {
    console.log("Cancel button clicked");    // TEMP DEBUG
    if (!window.currentEventId) return;     // calendar.js sets currentEventId
    pendingCancelEventId = window.currentEventId;
    openAppointmentModal("cancel-confirm-modal");
  });

  confirmNo?.addEventListener("click", () => {
    pendingCancelEventId = null;
    closeAppointmentModal("cancel-confirm-modal");
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

      closeAppointmentModal("cancel-confirm-modal");
      closeAppointmentModal("status-modal");
    });

  pendingCancelEventId = null;
});


  // Status / Followup / Reschedule
  document.getElementById("close-status-btn")?.addEventListener("click", () => closeAppointmentModal("status-modal"));
  document.getElementById("close-followup-btn")?.addEventListener("click", () => closeAppointmentModal("followup-modal"));
  document.getElementById("close-reschedule-btn")?.addEventListener("click", () => closeAppointmentModal("reschedule-modal"));

  // ===== Service search + selected tags =====
  function initServiceSearchAndTags({
    searchInput,
    servicesContainer,
    checkboxSelector,
    selectedTagsContainer,
    selectedEmptyText,
  }) {
    if (!servicesContainer || !selectedTagsContainer || !selectedEmptyText) return;

    const serviceCheckboxes = servicesContainer.querySelectorAll(checkboxSelector);

    function refreshSelectedServiceTags() {
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
    if (searchInput && servicesContainer) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.toLowerCase();

        servicesContainer.querySelectorAll("label").forEach(label => {
          const nameEl = label.querySelector("span");
          const name = nameEl ? nameEl.textContent.toLowerCase() : "";
          label.style.display = name.includes(q) ? "" : "none";
        });
      });
    }

    // Initial state
    refreshSelectedServiceTags();

    // NEW: return refresher so callers can re-run after programmatic changes
    return refreshSelectedServiceTags;
  }



  // Odontogram "Check All" functionality
  function wireDoneOdontogramCheckAll(recordEl) {
    const checkAllBox = recordEl.querySelector(".tooth-check-all");
    const toothCheckboxes = recordEl.querySelectorAll(".done-tooth-checkbox");

    if (!checkAllBox || !toothCheckboxes.length) return;

    // Remove existing listeners by cloning
    const newCheckAll = checkAllBox.cloneNode(true);
    checkAllBox.parentNode.replaceChild(newCheckAll, checkAllBox);

    newCheckAll.addEventListener("change", () => {
      toothCheckboxes.forEach((cb) => {
        cb.checked = newCheckAll.checked;
      });
    });
  }

  // Odontogram "Add More" functionality
  document.getElementById("done-add-more-odontogram")?.addEventListener("click", () => {
    const recordsWrapper = document.getElementById("done-odontogram-records");
    if (!recordsWrapper) return;

    const firstRecord = recordsWrapper.querySelector(".odontogram-record");
    if (!firstRecord) return;

    const newRecord = firstRecord.cloneNode(true);
    
    // Find the highest index
    let maxIndex = 0;
    recordsWrapper.querySelectorAll(".odontogram-record").forEach(record => {
      const inputs = record.querySelectorAll("input[name^='date_'], select[name^='dentist_'], input[name^='status_']");
      inputs.forEach(input => {
        const match = input.name.match(/_(\d+)$/);
        if (match) {
          const idx = parseInt(match[1]);
          if (idx > maxIndex) maxIndex = idx;
        }
      });
    });
    
    const newIndex = maxIndex + 1;
    
    // Update all input names in the new record
    newRecord.querySelectorAll("input, select").forEach(el => {
      if (el.name) {
        el.name = el.name.replace(/_\d+$/, `_${newIndex}`);
        el.id = el.id ? el.id.replace(/_\d+$/, `_${newIndex}`) : el.name;
        
        // Reset values
        if (el.type === "checkbox" || el.type === "radio") {
          el.checked = false;
        } else {
          el.value = "";
        }
      }
    });

    // Show remove button for new record
    const removeBtn = newRecord.querySelector(".remove-record");
    if (removeBtn) {
      removeBtn.classList.remove("hidden");
      removeBtn.addEventListener("click", () => {
        newRecord.remove();
      });
    }

    // Wire check all for new record
    wireDoneOdontogramCheckAll(newRecord);

    recordsWrapper.appendChild(newRecord);
  });

  // Wire check all for initial odontogram record
  const doneOdontogramRecords = document.getElementById("done-odontogram-records");
  if (doneOdontogramRecords) {
    const initialRecord = doneOdontogramRecords.querySelector(".odontogram-record");
    if (initialRecord) {
      wireDoneOdontogramCheckAll(initialRecord);
    }
  }

  // Close modal when clicking outside
  const doneStepsModal = document.getElementById("done-steps-modal");
  doneStepsModal?.addEventListener("click", (e) => {
    if (e.target === doneStepsModal) {
      closeAppointmentModal("done-steps-modal");
    }
  });

    // Notify Patient modal wiring
  const notifyPatientBtn = document.getElementById("notify-patient-btn");
  const closeNotifyBtn = document.getElementById("close-notify-btn");
  const notifySmsBtn = document.getElementById("notify-sms-btn");
  const notifyEmailBtn = document.getElementById("notify-email-btn");
  const notifyEmailModal = document.getElementById("notify-email-modal");
  const notifyEmailMessage = document.getElementById("notify-email-message");
  const closeNotifyEmailModalBtn = document.getElementById("close-notify-email-modal");

  closeNotifyEmailModalBtn?.addEventListener("click", () => {
  closeAppointmentModal("notify-email-modal");
  });
  notifyEmailModal?.addEventListener("click", e => {
    if (e.target === notifyEmailModal) closeAppointmentModal("notify-email-modal");
  });

  notifyPatientBtn?.addEventListener("click", () => {
    if (!window.currentEventId) return; // set by calendar.js when opening status modal
    openAppointmentModal("notify-modal");
  });

  closeNotifyBtn?.addEventListener("click", () => {
    closeAppointmentModal("notify-modal");
  });

  // Optional: clicking on the backdrop closes the notify modal as well
  const notifyModal = document.getElementById("notify-modal");
  notifyModal?.addEventListener("click", (e) => {
    if (e.target === notifyModal) closeAppointmentModal("notify-modal");
  });

  // For now, just close after click; you can replace with real API calls later
  notifySmsBtn?.addEventListener("click", () => {
    console.log("Send SMS to patient for event", window.currentEventId);
    // TODO: call your SMS endpoint here
    closeAppointmentModal("notify-modal");
  });

  // Email notif block
  notifyEmailBtn?.addEventListener("click", () => {
    if (!window.currentEventId) return;

    const idStr = String(window.currentEventId);

    notifyEmailBtn.disabled = true;
    notifyEmailBtn.classList.add("opacity-50", "cursor-not-allowed");

    fetch(`/dashboard/appointment/notify-email/${idStr}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(res => res.json())
      .then(data => {
        notifyEmailBtn.disabled = false;
        notifyEmailBtn.classList.remove("opacity-50", "cursor-not-allowed");

        if (!data.success) {
          console.error("Notify email failed:", data.error);
          notifyEmailMessage.textContent =
            data.error || "Failed to send email notification.";
          closeAppointmentModal("notify-modal");
          openAppointmentModal("notify-email-modal");
          return;
        }

        // Success UX: show notify-email modal
        notifyEmailMessage.textContent = "Email notification sent to the patient.";
        closeAppointmentModal("notify-modal");
        openAppointmentModal("notify-email-modal");
      })
      .catch(err => {
        notifyEmailBtn.disabled = false;
        notifyEmailBtn.classList.remove("opacity-50", "cursor-not-allowed");
        console.error("Notify email error:", err);
        notifyEmailMessage.textContent = "Network error while sending email.";
        closeAppointmentModal("notify-modal");
        openAppointmentModal("notify-email-modal");
      });
  });



  // --- Two-step create appointment flow (loading + confirm) ---
  addForm = document.querySelector("#appointment-modal form");
  addSaveBtn = addForm ? addForm.querySelector('button[type="submit"]') : null;

  const overlay = document.getElementById("appointment-loading-overlay");
  const loadingStep = document.getElementById("appointment-loading-step");
  const confirmStep = document.getElementById("appointment-confirm-step");
  const confirmDateEl = document.getElementById("confirm-picked-date");
  const confirmTimeEl = document.getElementById("confirm-picked-time");
  const confirmSaveBtn = document.getElementById("confirm-save-btn");
  const confirmReschedBtn = document.getElementById("confirm-reschedule-btn");

  let pendingSubmitTimeout = null;

  if (addForm && overlay && loadingStep && confirmStep) {
    // Intercept the normal submit
    addForm.addEventListener("submit", (e) => {
      e.preventDefault(); // stop immediate POST

      // If form invalid by our existing validation, do nothing
      if (addSaveBtn && addSaveBtn.disabled) return;

      // Prepare overlay: show loading step, hide confirm step
      loadingStep.classList.remove("hidden");
      confirmStep.classList.add("hidden");
      overlay.classList.remove("hidden");
      overlay.classList.add("flex");

      const content = overlay.querySelector(":scope > div");
      if (content) {
        content.classList.remove("opacity-100", "scale-100");
        content.classList.add("opacity-0", "scale-95");
        requestAnimationFrame(() => {
          content.classList.remove("opacity-0", "scale-95");
          content.classList.add("opacity-100", "scale-100");
        });
      }

      // After ~5 seconds, switch to confirmation step
      if (pendingSubmitTimeout) clearTimeout(pendingSubmitTimeout);
      
        pendingSubmitTimeout = setTimeout(() => {
          // Build form data to send to precompute API
          const formData = new FormData(addForm);

          fetch("/dashboard/appointment/precompute-slot/", {
            method: "POST",
            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: formData,
          })
            .then(res => res.json())
            .then(data => {
              if (!data.success) {
                // If API fails, you can show an error and close overlay
                confirmDateEl.textContent = "N/A";
                confirmTimeEl.textContent = "No available slot";
              } else {
                // Use the actual scheduled slot from the server
                const dateVal = data.date;               // "YYYY-MM-DD"
                const start = data.start_time;           // "HH:MM" 24h
                const end = data.end_time;               // "HH:MM" 24h

                confirmDateEl.textContent = dateVal || "N/A";

                if (start && end) {
                  // Convert to AM/PM for display if you want
                  const format12 = (t) => {
                    const [h, m] = t.split(":");
                    let hour = parseInt(h, 10);
                    const ampm = hour >= 12 ? "PM" : "AM";
                    hour = hour % 12;
                    if (hour === 0) hour = 12;
                    return `${hour.toString().padStart(2, "0")}:${m} ${ampm}`;
                  };

                  confirmTimeEl.textContent =
                    `${format12(start)} – ${format12(end)}`;
                } else {
                  confirmTimeEl.textContent = "N/A";
                }
              }

              loadingStep.classList.add("hidden");
              confirmStep.classList.remove("hidden");
            })
            .catch(() => {
              confirmDateEl.textContent = "N/A";
              confirmTimeEl.textContent = "Error computing slot";
              loadingStep.classList.add("hidden");
              confirmStep.classList.remove("hidden");
            });
        }, 5000);
    });

    // User confirms: actually submit form to Django
    confirmSaveBtn?.addEventListener("click", () => {
      if (pendingSubmitTimeout) clearTimeout(pendingSubmitTimeout);
      // Close overlay
      overlay.classList.add("hidden");
      overlay.classList.remove("flex");
      // Now allow the real submit
      addForm.submit();
    });

    // User wants to change schedule: close overlay, keep modal & inputs as-is
    confirmReschedBtn?.addEventListener("click", () => {
      if (pendingSubmitTimeout) clearTimeout(pendingSubmitTimeout);
      overlay.classList.add("hidden");
      overlay.classList.remove("flex");
      // Do NOT reset the form; all inputs stay the same
    });
  }

  // Initialize
  initTimeValidation();
  initRescheduleForm();
  initFollowupForm();
});

//helper mdecial
function computeDoneMedicalTotal() {
  const container = document.getElementById("done-services-checkboxes");
  const amountInput = document.getElementById("done-medical-amount");
  if (!container || !amountInput) return;

  let total = 0;
  container.querySelectorAll("input.done-service-checkbox").forEach(cb => {
    if (cb.checked) {
      const price = parseFloat(cb.dataset.price || "0");
      if (!isNaN(price)) total += price;
    }
  });

  amountInput.value = total.toFixed(2);
}

// ===== Modal Helpers (simple, robust) =====
function openAppointmentModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  modal.classList.remove("hidden");
  modal.classList.add("flex");

  const content =
    modal.querySelector(".modal-content") ||
    modal.querySelector(".bg-white.rounded-2xl") ||
    modal.querySelector(".bg-white.rounded-lg");

  if (content) {
    content.classList.remove("opacity-0", "scale-95");
    content.classList.add("opacity-100", "scale-100");
  }
}

function closeAppointmentModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;

  const content =
    modal.querySelector(".modal-content") ||
    modal.querySelector(".bg-white.rounded-2xl") ||
    modal.querySelector(".bg-white.rounded-lg");

  if (content) {
    content.classList.remove("opacity-100", "scale-100");
    content.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }, 200);
  } else {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
  }
}


// Return a map: { hour24: Set(blockedMinutes) }
function buildBlockedMinuteMap(booked) {
  const blocked = {};

  booked.forEach(slot => {
    if (!slot.start || !slot.end) return;

    const [sh, sm] = slot.start.split(":").map(Number);
    const [eh, em] = slot.end.split(":").map(Number);

    let startMinutes = sh * 60 + sm;
    let endMinutes = eh * 60 + em;

    // Treat [start, end) so an appointment 08:00-08:30 blocks 00,05,...,25 but not 30+
    for (let m = startMinutes; m < endMinutes; m += 5) {
      const h = Math.floor(m / 60);
      const mm = m % 60;
      if (!blocked[h]) blocked[h] = new Set();
      blocked[h].add(mm);
    }
  });

  return blocked;
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

  hourSelect.disabled = !ready;
  minuteSelect.disabled = !ready;
  ampmSelect.disabled = !ready;

  timeError.textContent = ready
    ? ""
    : "Please select dentist, location, and date first.";

  if (!ready) return;

  const booked = await fetchBookedTimes(
    dentistSelect.value,
    dateInput.value,
    locationSelect.value
  );

  const blockedMap = buildBlockedMinuteMap(booked);

  // 1) Hour-level disabling: disable an hour only if all minutes 0–59 are blocked
  Array.from(hourSelect.options).forEach(opt => {
    if (!opt.value || opt.disabled && opt.value === "") return; // skip placeholder
    const hour12 = parseInt(opt.value, 10);

    // convert 12h + current AM/PM to 24h
    const ampm = ampmSelect.value;
    if (!ampm) {
      opt.disabled = false;
      return;
    }

    let h24 = hour12;
    if (ampm === "AM" && hour12 === 12) h24 = 0;
    if (ampm === "PM" && hour12 !== 12) h24 = hour12 + 12;

    const blockedMinutes = blockedMap[h24] || new Set();
    // check if ANY minute in this hour is free
    let hasFree = false;
    for (let mm = 0; mm < 60; mm += 5) {
      if (!blockedMinutes.has(mm)) {
        hasFree = true;
        break;
      }
    }
    opt.disabled = !hasFree;
  });

  // 2) Minute-level disabling: whenever hour or ampm changes, disable only blocked minutes
  function updateMinuteOptions() {
    const hourStr = hourSelect.value;
    const ampm = ampmSelect.value;

    // re-enable all minutes first
    Array.from(minuteSelect.options).forEach(opt => {
      if (!opt.value) return;
      opt.disabled = false;
    });

    if (!hourStr || !ampm) return;

    const hour12 = parseInt(hourStr, 10);
    let h24 = hour12;
    if (ampm === "AM" && hour12 === 12) h24 = 0;
    if (ampm === "PM" && hour12 !== 12) h24 = hour12 + 12;

    const blockedMinutes = blockedMap[h24] || new Set();

    Array.from(minuteSelect.options).forEach(opt => {
      if (!opt.value) return;
      const mm = parseInt(opt.value, 10);
      if (blockedMinutes.has(mm)) {
        opt.disabled = true;
      }
    });
  }

  // hook the minute update; ensure you don't add multiple listeners
  hourSelect.removeEventListener("change", updateMinuteOptions);
  ampmSelect.removeEventListener("change", updateMinuteOptions);
  minuteSelect.removeEventListener("change", updateMinuteOptions);

  hourSelect.addEventListener("change", updateMinuteOptions);
  ampmSelect.addEventListener("change", updateMinuteOptions);
  minuteSelect.addEventListener("change", updateMinuteOptions);

  // run once for current selection
  updateMinuteOptions();
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

// ===== Status Updated Modal =====
const statusUpdatedModal = document.getElementById("status-updated-modal");
const statusUpdatedMessage = document.getElementById("status-updated-message");
const closeStatusUpdatedBtn = document.getElementById("close-status-updated-modal");

closeStatusUpdatedBtn?.addEventListener("click", () => {
  closeAppointmentModal("status-updated-modal");
});

statusUpdatedModal?.addEventListener("click", e => {
  if (e.target === statusUpdatedModal) closeAppointmentModal("status-updated-modal");
});

// ===== Success Modal =====
const successModal = document.getElementById("success-modal");
const closeSuccessBtn = document.getElementById("close-success-btn");

function showSuccessModal() {
  openAppointmentModal("success-modal");
}

function closeSuccessModal() {
  closeAppointmentModal("success-modal");
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
  openAppointmentModal("failed-modal");
}

function closeFailedModal() {
  closeAppointmentModal("failed-modal");
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

    async function toggleReschedTimeInputs() {
    const dentist = document.getElementById("resched-dentist")?.value || "";
    const date = document.getElementById("resched-date")?.value || "";
    const location = document.getElementById("resched-location")?.value || "";

    const ready = dentist && date && location;

    // enable/disable selects
    hourSelect.disabled = !ready;
    minuteSelect.disabled = !ready;
    ampmSelect.disabled = !ready;

    if (!ready) return;

    const booked = await fetchBookedTimes(dentist, date, location);

    // reset hour options disabled state
    Array.from(hourSelect.options).forEach(o => {
      o.disabled = false;
    });

    // disable booked hours (same idea as create)
    booked.forEach(slot => {
      const [sh] = slot.start.split(":").map(Number);
      const [eh] = slot.end.split(":").map(Number);

      for (let h = sh; h <= eh; h++) {
        const hour12 = (h % 12) || 12;
        const opt = hourSelect.querySelector(`option[value="${hour12}"]`);
        if (opt) opt.disabled = true;
      }
    });
  }

    // when resched dentist/date/location change, refetch and apply booked times
  [
    document.getElementById("resched-dentist"),
    document.getElementById("resched-location"),
    document.getElementById("resched-date"),
  ].forEach(el => {
    el && el.addEventListener("change", toggleReschedTimeInputs);
  });

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

    toggleReschedTimeInputs();
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

  // --- Reschedule form validation: enable Save Changes only when complete ---
  const reschedForm = document.getElementById("reschedule-form");
  const reschedSaveBtn = reschedForm ? reschedForm.querySelector('button[type="submit"]') : null;

    const reschedLoadingRow = document.getElementById("resched-loading-row");

  // Attach submit handler only once
  if (reschedForm && reschedSaveBtn && !reschedHandlerAttached) {
    reschedHandlerAttached = true;

    reschedForm.addEventListener("submit", (e) => {
      e.preventDefault();
      if (reschedSaveBtn.disabled) return;
      if (!window.reschedAppointmentId) return;

      // show small loader in modal, disable button
      reschedLoadingRow?.classList.remove("hidden");
      reschedSaveBtn.disabled = true;
      reschedSaveBtn.classList.add("opacity-50", "cursor-not-allowed");

      const formData = new FormData(reschedForm);

      setTimeout(() => {
        fetch(`/dashboard/appointment/reschedule_appointment/${window.reschedAppointmentId}/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            reschedLoadingRow?.classList.add("hidden");
            reschedSaveBtn.disabled = false;
            reschedSaveBtn.classList.remove("opacity-50", "cursor-not-allowed");

            if (!data.success) {
              showFailedModal(data.error || "Failed to reschedule appointment.");
              return;
            }

            closeAppointmentModal("reschedule-modal");

            if (window.timelineCalendar) window.timelineCalendar.refetchEvents();
            if (window.mainCalendar) window.mainCalendar.refetchEvents();
            setTimeout(() => {
              if (typeof window.renderTodaysAppointments === "function") {
                window.renderTodaysAppointments();
              }
            }, 250);

            showSuccessModal();
          });
      }, 5000); // 5-second delay to match your UX
    });
  }


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
  toggleReschedTimeInputs();

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

// ===== Done Steps Modal =====
window.initDoneStepsModal = function(appointmentId) {
  console.log("=== INIT DONE STEPS MODAL CALLED ===");
  console.log("appointmentId:", appointmentId);
  if (!appointmentId) return;

  // Initialize step to 1 FIRST
  window.doneStepsCurrentStep = 1;
  console.log("Set doneStepsCurrentStep to:", window.doneStepsCurrentStep);

  // Open modal first
  openAppointmentModal("done-steps-modal");

  // Show step 1 immediately
  showDoneStep(1);

  // Fetch appointment + patient data
  fetch(`/dashboard/appointment/get-appointment-details/${appointmentId}/`)
    .then(res => res.json())
    .then(data => {
      console.log("Got appointment data:", data);
      
      if (!data.success) {
        alert("Failed to load appointment details");
        closeAppointmentModal("done-steps-modal");
        return;
      }

      const apptData = data.appointment;
      const patientData = data.patient;
      window.currentPatientId = patientData.id;

      console.log("Setting form actions with patient ID:", patientData.id);

      // Set form actions
      const medicalForm = document.getElementById("done-medical-form");
      const financialForm = document.getElementById("done-financial-form");
      const odontogramForm = document.getElementById("done-odontogram-form");

      if (medicalForm) {
        medicalForm.action = `/dashboard/patient/${patientData.id}/add_history/`;
        console.log("Medical form action:", medicalForm.action);
      }
      if (financialForm) {
        financialForm.action = `/dashboard/patient/${patientData.id}/add_financial_history/`;
        console.log("Financial form action:", financialForm.action);
      }
      if (odontogramForm) {
        odontogramForm.action = `/dashboard/patient/${patientData.id}/add_odontogram/`;
        console.log("Odontogram form action:", odontogramForm.action);
      }

      // Prefill forms
      if (document.getElementById("done-medical-date")) 
        document.getElementById("done-medical-date").value = apptData.date || "";
      if (document.getElementById("done-medical-dentist")) 
        document.getElementById("done-medical-dentist").value = apptData.dentist || "";
      // Prefill Step‑1 services as checkboxes in Done Steps modal
      if (Array.isArray(apptData.service_ids)) {
        const doneServicesContainer = document.getElementById("done-services-checkboxes");
        if (doneServicesContainer) {
          const idSet = new Set(apptData.service_ids.map(String));  // normalize to strings
          doneServicesContainer
            .querySelectorAll("input.done-service-checkbox")
            .forEach(cb => {
              if (idSet.has(cb.value)) {
                cb.checked = true;
              }
            });
        }

        // Refresh selected-services tags box after programmatically checking
        if (typeof window.refreshDoneStep1Tags === "function") {
          window.refreshDoneStep1Tags();
        }
      }


      // Prefill Step‑3 odontogram services to match appointment services
      if (Array.isArray(apptData.service_ids)) {
        const odontoServicesContainer = document.getElementById("done-odontogram-services-checkboxes-0");
        if (odontoServicesContainer) {
          const idSet = new Set(apptData.service_ids.map(String));
          odontoServicesContainer
            .querySelectorAll("input.done-odontogram-service-checkbox")
            .forEach(cb => {
              if (idSet.has(cb.value)) {
                cb.checked = true;
              }
            });
        }

        // Refresh Step 3 selected-services tags after programmatic checking
        if (typeof window.refreshDoneStep3Tags === "function") {
          window.refreshDoneStep3Tags();
        }
      }

    
      if (document.getElementById("done-financial-date")) 
        document.getElementById("done-financial-date").value = apptData.date || "";
      // If you want a default bill_type and payment_mode:
      const billTypeSelect = document.getElementById("done-financial-bill-type");
      if (billTypeSelect) billTypeSelect.value = "Services";
      const paymentModeSelect = document.getElementById("done-financial-payment-mode");
      if (paymentModeSelect) paymentModeSelect.value = "Cash";
      if (document.getElementById("done-odontogram-date-0")) 
        document.getElementById("done-odontogram-date-0").value = apptData.date || "";

      const odontoDentistSelect = document.getElementById("done-odontogram-dentist-0");
      if (odontoDentistSelect && apptData.dentist_id) {
        odontoDentistSelect.value = apptData.dentist_id;
      }
      

      // 1) compute total price into done-medical-amount (initial)
      computeDoneMedicalTotal();
      const doneAmountInput = document.getElementById("done-medical-amount");

      // === Financial step: Total Due, Amount, Balance ===
      const totalDueInput = document.getElementById("done-financial-total-due");
      const amountInput   = document.getElementById("done-financial-amount");
      const balanceInput  = document.getElementById("done-financial-balance");

      // Use Step 1 total for Step 2 Total Due (initial)
      if (totalDueInput && doneAmountInput) {
        totalDueInput.value = doneAmountInput.value || "0.00";
      }

      // Keep Step 2 Total Due in sync when Step 1 services change during this modal session
      const doneServicesContainerModal = document.getElementById("done-services-checkboxes");
      if (doneServicesContainerModal && totalDueInput && doneAmountInput) {
        doneServicesContainerModal.addEventListener("change", () => {
          computeDoneMedicalTotal();
          totalDueInput.value = doneAmountInput.value || "0.00";
          // optional: recompute balance if user already typed Amount
          if (typeof recomputeBalance === "function") {
            recomputeBalance();
          }
        });
      }


      // Helper to recompute balance
      function recomputeBalance() {
        if (!totalDueInput || !amountInput || !balanceInput) return;
        const t = parseFloat(totalDueInput.value) || 0;
        const a = parseFloat(amountInput.value) || 0;
        const bal = t - a;
        balanceInput.value = bal.toFixed(2);
      }

      // Recompute when user types amount (payment)
      if (amountInput) {
        amountInput.addEventListener("input", recomputeBalance);
      }

      // Recompute if staff/admin edits total_due (field is editable only for them in template)
      if (totalDueInput) {
        totalDueInput.addEventListener("input", recomputeBalance);
      }

      // Initial balance = totalDue (before any payment)
      recomputeBalance();

      console.log("Forms prefilled successfully");
    })
    .catch(err => {
      console.error("Error:", err);
      alert("Failed to load appointment details");
      closeAppointmentModal("done-steps-modal");
    });
};

function showDoneStep(step) {
  console.log("showDoneStep called with step:", step);
  
  // Hide all forms
  document.querySelectorAll(".step-form").forEach(f => f.classList.add("hidden"));
  
  // Reset all step containers
  document.querySelectorAll(".step-container").forEach(s => {
    s.classList.add("opacity-50");
    s.classList.remove("border-blue-500");
  });

  // Show current form and highlight step
  const form = document.querySelector(`.step-form[data-step="${step}"]`);
  const container = document.getElementById(`step-${step}`);
  
  console.log("Form for step", step, ":", form);
  console.log("Container for step", step, ":", container);
  
  if (form) form.classList.remove("hidden");
  if (container) {
    container.classList.remove("opacity-50");
    container.classList.add("border-blue-500");
  }

  // Update buttons
  const backBtn = document.getElementById("done-steps-back-btn");
  const nextBtn = document.getElementById("done-steps-next-btn");
  const submitBtn = document.getElementById("done-steps-submit-btn");

  if (backBtn) backBtn.disabled = (step === 1);
  if (nextBtn) nextBtn.classList.toggle("hidden", step === 3);
  if (submitBtn) {
    submitBtn.classList.toggle("hidden", step !== 3);
    if (form) submitBtn.setAttribute("form", form.id);
  }

  window.doneStepsCurrentStep = step;
  console.log("doneStepsCurrentStep set to:", window.doneStepsCurrentStep);
}


// Attach handlers when DOM loads - ONCE
document.addEventListener("DOMContentLoaded", function() {
  console.log("Attaching Done Steps handlers");

  // Back button
  const backBtn = document.getElementById("done-steps-back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", function() {
      console.log("Back clicked, current step:", window.doneStepsCurrentStep);
      showDoneStep(Math.max(1, window.doneStepsCurrentStep - 1));
    });
  }

  // Next button
  const nextBtn = document.getElementById("done-steps-next-btn");
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      const currentStep = window.doneStepsCurrentStep || 1;

      // Optional: basic validation before moving on
      const form = document.querySelector(`.step-form[data-step="${currentStep}"]`);
      if (form && !form.checkValidity()) {
        form.reportValidity();
        return;
      }

      const nextStep = Math.min(3, currentStep + 1);
      showDoneStep(nextStep);
    });
  }

  // NEW: Submit button - save all 3 steps at once
  const submitBtn = document.getElementById("done-steps-submit-btn");
  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      window.doneStepsCurrentStep = 3;
      const forms = [
        document.getElementById("done-medical-form"),
        document.getElementById("done-financial-form"),
        document.getElementById("done-odontogram-form"),
      ].filter(Boolean);

      // Basic HTML5 validation first
      for (const f of forms) {
        if (!f.checkValidity()) {
          f.reportValidity();
          return;
        }
      }

      // Helper to POST one form and return a promise
      const postForm = (form) => {
        const action = form.action;
        if (!action || action.includes("patient/0")) {
          alert("Form action not set correctly.");
          return Promise.reject("bad action");
        }
        const formData = new FormData(form);
        return fetch(action, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: formData,
        }).then(res => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return res.json();
        });
      };

      // Post all three forms in sequence
      postForm(forms[0])
        .then(data1 => {
          if (!data1.success) throw new Error(data1.error || "Failed to save step 1");
          return postForm(forms[1]);
        })
        .then(data2 => {
          if (!data2.success) throw new Error(data2.error || "Failed to save step 2");
          return postForm(forms[2]);
        })
        .then(data3 => {
          if (!data3.success) throw new Error(data3.error || "Failed to save step 3");

          // After all succeed, mark appointment as done and redirect
          if (window.currentEventId) {
            return fetch(`/dashboard/appointment/update-status/${window.currentEventId}/`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
              },
              body: JSON.stringify({ status: "done" }),
            }).then(res => res.json());
          }
        })
        .then(statusData => {
          if (statusData && !statusData.success) {
            alert("Failed to update appointment status.");
            return;
          }
          // Refresh calendars and redirect to patient page
          if (window.timelineCalendar) window.timelineCalendar.refetchEvents();
          if (window.mainCalendar) window.mainCalendar.refetchEvents();
          if (window.currentPatientId) {
            window.location.href = `/dashboard/patient/${window.currentPatientId}/`;
          } else {
            closeAppointmentModal("done-steps-modal");
          }
        })
        .catch(err => {
          console.error(err);
          alert(err.message || "Network error while saving done steps.");
        });
    });
  }

  // Close button
  const closeBtn = document.getElementById("done-steps-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", function() {
      closeAppointmentModal("done-steps-modal");
      closeAppointmentModal("status-modal");
    });
  }
});

// Sync Step 1 total -> Step 2 total
const step1ServicesContainer = document.getElementById("done-services-checkboxes");
const doneAmountInput = document.getElementById("done-medical-amount");
const financialTotalDueInput = document.getElementById("done-financial-total-due");

if (step1ServicesContainer && doneAmountInput) {
  step1ServicesContainer.addEventListener("change", () => {
    let total = 0;
    step1ServicesContainer
      .querySelectorAll("input.done-service-checkbox")
      .forEach(cb => {
        if (cb.checked) {
          const price = parseFloat(cb.dataset.price || "0");
          total += isNaN(price) ? 0 : price;
        }
      });

    const totalStr = total.toFixed(2);
    doneAmountInput.value = totalStr;

    if (financialTotalDueInput) {
      financialTotalDueInput.value = totalStr;
    }
  });
}


// Odontogram final step submit (attach only once)
const doneOdontoForm = document.getElementById("done-odontogram-form");
if (doneOdontoForm && !doneOdontogramHandlerAttached) {
  doneOdontogramHandlerAttached = true;
  
  doneOdontoForm.addEventListener("submit", function(e) {
    e.preventDefault();
    if (!window.currentPatientId) {
      // alert("Patient ID not found");
      return;
    }

    const formData = new FormData(this);
    fetch(this.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // Mark appointment as done
        if (window.currentEventId) {
          fetch(`/dashboard/appointment/update-status/${window.currentEventId}/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ status: "done" })
          })
          .then(res => res.json())
          .then(statusData => {
            if (statusData.success) {
              if (window.timelineCalendar) window.timelineCalendar.refetchEvents();
              if (window.mainCalendar) window.mainCalendar.refetchEvents();
              
              // Redirect to patient page so you see all 3 records
              window.location.href = `/dashboard/patient/${window.currentPatientId}/`;
            }
          });
        }
      } else {
        alert(data.error || "Failed to save odontogram");
      }
    })
    .catch(err => {
      console.error(err);
      alert("Network error");
    });
  });
}

