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

  // Done Steps Modal - Step navigation
  let currentStep = 1;
  const totalSteps = 3;
  let currentAppointmentData = null;
  // let currentPatientId = null;

  function updateDoneStepsDisplay() {
    // Update all steps
    for (let i = 1; i <= totalSteps; i++) {
      const stepEl = document.getElementById(`step-${i}`);
      const stepCircle = stepEl?.querySelector('.step-circle');
      const icon = stepCircle?.querySelector('i');
      
      if (!stepEl || !stepCircle) continue;

      if (i < currentStep) {
        // Completed step
        stepEl.classList.remove("opacity-50");
        stepEl.classList.remove("border-gray-200", "border-blue-500", "bg-blue-50");
        stepEl.classList.add("border-emerald-500", "bg-emerald-50");
        stepCircle.classList.remove("border-gray-300", "bg-white", "border-blue-500");
        stepCircle.classList.add("border-emerald-500", "bg-emerald-500");
        if (icon) {
          icon.classList.remove("text-gray-400", "text-blue-500");
          icon.classList.add("text-white");
        }
      } else if (i === currentStep) {
        // Current step
        stepEl.classList.remove("opacity-50");
        stepEl.classList.remove("border-gray-200", "border-emerald-500", "bg-emerald-50");
        stepEl.classList.add("border-blue-500", "bg-blue-50");
        stepCircle.classList.remove("border-gray-300", "bg-white", "border-emerald-500", "bg-emerald-500");
        stepCircle.classList.add("border-blue-500", "bg-white");
        if (icon) {
          icon.classList.remove("text-white", "text-gray-400");
          icon.classList.add("text-blue-500");
        }
      } else {
        // Future step
        stepEl.classList.add("opacity-50");
        stepEl.classList.remove("border-blue-500", "bg-blue-50", "border-emerald-500", "bg-emerald-50");
        stepEl.classList.add("border-gray-200");
        stepCircle.classList.remove("border-blue-500", "border-emerald-500", "bg-emerald-500");
        stepCircle.classList.add("border-gray-300", "bg-white");
        if (icon) {
          icon.classList.remove("text-blue-500", "text-white");
          icon.classList.add("text-gray-400");
        }
      }
    }

    // Show/hide forms based on current step
    document.querySelectorAll('.step-form').forEach(form => {
      const formStep = parseInt(form.dataset.step);
      if (formStep === currentStep) {
        form.classList.remove('hidden');
        // Update submit button form attribute
        const submitBtn = document.getElementById("done-steps-submit-btn");
        if (submitBtn) {
          submitBtn.setAttribute("form", form.id);
        }
      } else {
        form.classList.add('hidden');
      }
    });

    // Update buttons
    const backBtn = document.getElementById("done-steps-back-btn");
    const nextBtn = document.getElementById("done-steps-next-btn");
    const submitBtn = document.getElementById("done-steps-submit-btn");

    if (backBtn) {
      backBtn.disabled = currentStep === 1;
    }

    if (nextBtn) {
      if (currentStep === totalSteps) {
        nextBtn.classList.add("hidden");
        if (submitBtn) submitBtn.classList.remove("hidden");
      } else {
        nextBtn.classList.remove("hidden");
        if (submitBtn) submitBtn.classList.add("hidden");
      }
    }
  }

  function prefillForms(appointmentData, patientData, userRole) {
    if (!appointmentData) return;

    // Pre-fill Medical History Form (Step 1)
    const medicalPatientName = document.getElementById("done-medical-patient-name");
    const medicalDate = document.getElementById("done-medical-date");
    const medicalDentist = document.getElementById("done-medical-dentist");
    const medicalService = document.getElementById("done-medical-service");
    const medicalReason = document.getElementById("done-medical-reason");
    
    // Conditionally pre-fill patient name only if user is NOT admin/staff
    if (medicalPatientName && patientData && patientData.name) {
      if (userRole && !userRole.is_admin_or_staff) {
        // Auto-fill patient name for non-admin/staff users
        medicalPatientName.value = patientData.name;
        medicalPatientName.readOnly = true;
        medicalPatientName.classList.add("bg-gray-100");
        medicalPatientName.classList.remove("bg-white");
      } else {
        // For admin/staff, leave empty and make editable
        medicalPatientName.value = "";
        medicalPatientName.readOnly = false;
        medicalPatientName.classList.remove("bg-gray-100");
        medicalPatientName.classList.add("bg-white");
      }
    }
    
    if (medicalDate && appointmentData.date) medicalDate.value = appointmentData.date;
    if (medicalDentist && appointmentData.dentist) {
      // Set dentist name as text (field is text input)
      medicalDentist.value = appointmentData.dentist;
    }
    if (medicalService && appointmentData.services) {
      // Set service names as text (field is text input)
      medicalService.value = appointmentData.services;
    }
    if (medicalReason) {
      medicalReason.value = `Appointment - ${appointmentData.services || "Treatment"}`;
    }

    // Pre-fill Financial History Form (Step 2)
    const financialDate = document.getElementById("done-financial-date");
    const financialTime = document.getElementById("done-financial-time");
    const financialDescription = document.getElementById("done-financial-description");
    
    if (financialDate && appointmentData.date) financialDate.value = appointmentData.date;
    if (financialTime && appointmentData.time) {
      // Convert 12-hour format to 24-hour format for time input
      const time24 = appointmentData.time.includes(":") ? appointmentData.time : appointmentData.preferred_time || "";
      if (time24) {
        const timeMatch = time24.match(/(\d{1,2}):(\d{2})/);
        if (timeMatch) {
          let hours = parseInt(timeMatch[1]);
          const minutes = timeMatch[2];
          if (time24.includes("PM") && hours < 12) hours += 12;
          if (time24.includes("AM") && hours === 12) hours = 0;
          financialTime.value = `${String(hours).padStart(2, "0")}:${minutes}`;
        }
      }
    }
    if (financialDescription && appointmentData.services) {
      financialDescription.value = `Treatment: ${appointmentData.services}`;
    }

    // Pre-fill Odontogram Form (Step 3)
    const odontogramDate = document.getElementById("done-odontogram-date-0");
    const odontogramDentist = document.getElementById("done-odontogram-dentist-0");
    
    if (odontogramDate && appointmentData.date) odontogramDate.value = appointmentData.date;
    if (odontogramDentist && appointmentData.dentist_id) {
      odontogramDentist.value = appointmentData.dentist_id;
    }

    // Pre-check services in odontogram form
    if (appointmentData.service_ids && appointmentData.service_ids.length > 0) {
      const serviceCheckboxes = document.querySelectorAll('#done-odontogram-form input[name="services_0"]');
      serviceCheckboxes.forEach(cb => {
        if (appointmentData.service_ids.includes(parseInt(cb.value))) {
          cb.checked = true;
        }
      });
    }
  }

  // Expose update function globally
  window.updateDoneStepsDisplay = updateDoneStepsDisplay;

  // Back button
  document.getElementById("done-steps-back-btn")?.addEventListener("click", () => {
    if (currentStep > 1) {
      currentStep--;
      updateDoneStepsDisplay();
    }
  });

  // Next button
  document.getElementById("done-steps-next-btn")?.addEventListener("click", () => {
    if (currentStep < totalSteps) {
      currentStep++;
      updateDoneStepsDisplay();
    }
  });

  // Close button
  document.getElementById("done-steps-close-btn")?.addEventListener("click", () => {
    closeModal("done-steps-modal");
  });

  // Form submissions
  document.getElementById("done-medical-form")?.addEventListener("submit", function(e) {
    e.preventDefault();
    //DEBUG DEBUG
    console.log("=== MEDICAL FORM SUBMIT DEBUG ===");
    console.log("typeof currentPatientId:", typeof currentPatientId);
    console.log("currentPatientId value:", currentPatientId);
    console.log("window.currentPatientId:", window.currentPatientId);
    if (!currentPatientId) {
      alert("Patient ID not found. Please try again.");
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
        // Success - move to next step
        currentStep++;
        updateDoneStepsDisplay();
      } else {
        alert(data.error || "Error saving medical history. Please try again.");
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("Error saving medical history. Please try again.");
    });
  });

  document.getElementById("done-financial-form")?.addEventListener("submit", function(e) {
    e.preventDefault();
    if (!currentPatientId) {
      alert("Patient ID not found. Please try again.");
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
        // Success - move to next step
        currentStep++;
        updateDoneStepsDisplay();
      } else {
        alert(data.error || "Error saving financial history. Please try again.");
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("Error saving financial history. Please try again.");
    });
  });

  document.getElementById("done-odontogram-form")?.addEventListener("submit", function(e) {
    e.preventDefault();
    if (!currentPatientId) {
      alert("Patient ID not found. Please try again.");
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
        // Success - update appointment status to "done" and close modal
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
          .then(data => {
            if (data.success) {
              if (window.timelineCalendar) window.timelineCalendar.refetchEvents();
              if (window.mainCalendar) window.mainCalendar.refetchEvents();
              setTimeout(() => {
                if (typeof window.renderTodaysAppointments === "function") {
                  window.renderTodaysAppointments();
                }
              }, 250);

              // NEW: go to this patient's history page so you see all 3 records
              if (window.currentPatientId) {
                window.location.href = `/dashboard/patient/${window.currentPatientId}/`;
                // or `/dashboard/patient/${window.currentPatientId}/medical_history/` if that is your URL
              } else {
                closeModal("done-steps-modal");
                closeModal("status-modal");
              }
            }
          });
        } else {
          closeModal("done-steps-modal");
        }
      } else {
        alert(data.error || "Error saving odontogram. Please try again.");
      }
    })
    .catch(err => {
      console.error("Error:", err);
      alert("Error saving odontogram. Please try again.");
    });
  });

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
      closeModal("done-steps-modal");
    }
  });

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
        // Compute the picked date / time from the form
        const dateVal = document.getElementById("date")?.value || "";
        const hourVal = document.getElementById("hour")?.value || "";
        const minuteVal = document.getElementById("minute")?.value || "";
        const ampmVal = document.getElementById("ampm")?.value || "";

        // Format date as YYYY-MM-DD (as stored)
        confirmDateEl.textContent = dateVal || "N/A";

        // Format time into something like "09:30 AM"
        if (hourVal && minuteVal && ampmVal) {
          const hourStr = hourVal.toString().padStart(2, "0");
          confirmTimeEl.textContent = `${hourStr}:${minuteVal} ${ampmVal}`;
        } else {
          confirmTimeEl.textContent = "N/A";
        }

        loadingStep.classList.add("hidden");
        confirmStep.classList.remove("hidden");
      }, 5000); // 5 seconds
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

            closeModal("reschedule-modal");

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
  openModal("done-steps-modal");

  // Show step 1 immediately
  showDoneStep(1);

  // Fetch appointment + patient data
  fetch(`/dashboard/appointment/get-appointment-details/${appointmentId}/`)
    .then(res => res.json())
    .then(data => {
      console.log("Got appointment data:", data);
      
      if (!data.success) {
        alert("Failed to load appointment details");
        closeModal("done-steps-modal");
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
      if (document.getElementById("done-medical-patient-name")) 
        document.getElementById("done-medical-patient-name").value = patientData.name || "";
      if (document.getElementById("done-medical-date")) 
        document.getElementById("done-medical-date").value = apptData.date || "";
      if (document.getElementById("done-medical-dentist")) 
        document.getElementById("done-medical-dentist").value = apptData.dentist || "";
      if (document.getElementById("done-medical-service")) 
        document.getElementById("done-medical-service").value = apptData.services || "";
      if (document.getElementById("done-financial-date")) 
        document.getElementById("done-financial-date").value = apptData.date || "";
      if (document.getElementById("done-financial-time")) 
        document.getElementById("done-financial-time").value = apptData.time || "";
      if (document.getElementById("done-odontogram-date-0")) 
        document.getElementById("done-odontogram-date-0").value = apptData.date || "";
      
      const odontoDentistSelect = document.getElementById("done-odontogram-dentist-0");
      if (odontoDentistSelect && apptData.dentist_id) {
        odontoDentistSelect.value = apptData.dentist_id;
      }

      // === Financial step: Total Due, Amount, Balance ===
      const totalDueInput = document.getElementById("done-financial-total-due");
      const amountInput   = document.getElementById("done-financial-amount");
      const balanceInput  = document.getElementById("done-financial-balance");

      // Use total_price from backend (sum of service prices)
      let totalDue = 0;
      if (apptData.total_price !== undefined && apptData.total_price !== null) {
        totalDue = parseFloat(apptData.total_price) || 0;
      }

      if (totalDueInput) {
        totalDueInput.value = totalDue.toFixed(2);
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
      closeModal("done-steps-modal");
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
    nextBtn.addEventListener("click", function() {
      console.log("=== NEXT BUTTON CLICKED ===");
      console.log("Current step:", window.doneStepsCurrentStep);

      const currentStep = window.doneStepsCurrentStep;
      const form = document.querySelector(`.step-form[data-step="${currentStep}"]`);
      
      if (!form) {
        console.error("Form not found for step:", currentStep);
        alert("Form not found");
        return;
      }

      const action = form.action;
      console.log("Form action:", action);

      if (!action || action.includes("/patient/0/") || action.includes("/patient//")) {
        console.error("Invalid action URL:", action);
        alert("Form action not set correctly");
        return;
      }

      const formData = new FormData(form);
      console.log("Submitting form data to:", action);

      fetch(action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: formData,
      })
      .then(res => {
        console.log("Response status:", res.status);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log("Response data:", data);
        if (data.success) {
          console.log(`Step ${currentStep} saved!`);
          if (currentStep < 3) {
            showDoneStep(currentStep + 1);
          }
        } else {
          alert(data.error || "Failed to save");
        }
      })
      .catch(err => {
        console.error("Error:", err);
        alert("Network error: " + err.message);
      });
    });
  }

  // Close button
  const closeBtn = document.getElementById("done-steps-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", function() {
      closeModal("done-steps-modal");
      closeModal("status-modal");
    });
  }
});



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

