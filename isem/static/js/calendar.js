

let currentEventId = null;
window.currentEventId = null;
let mainCalendar = null;
let timelineCalendar = null;

document.addEventListener('DOMContentLoaded', function () {
  const mainCalendarEl = document.getElementById('calendar');
  const timelineCalendarEl = document.getElementById('timeline-calendar');
  const timelineControlsEl = document.getElementById('timeline-controls');
  const listEl = document.getElementById('todays-appointments-list');
  const statusButtons = document.querySelectorAll(
  "#status-modal .border .grid button"
  );
  const branchFilterEl = document.getElementById("branch-filter");
  const eventsUrl = "/dashboard/appointment/events/";

  branchFilterEl.addEventListener("change", function () {
    if (mainCalendar) mainCalendar.refetchEvents();
    if (timelineCalendar) timelineCalendar.refetchEvents();

    setTimeout(() => {
      if (typeof window.renderTodaysAppointments === "function") {
        window.renderTodaysAppointments();
      }
    }, 300);
  });

  document.getElementById("branch-filter").addEventListener("change", function() {
    console.log("Selected branch:", this.value);
});

  function fetchEvents(info, successCallback, failureCallback) {
    const branch = branchFilterEl.value;
    let url = eventsUrl;
    if (branch) url += `?branch=${branch}`;

    console.log("FETCHING:", url);   // ← ADD THIS LINE

    fetch(url)
      .then(res => res.json())
      .then(events => {
        console.log("RECEIVED EVENTS:", events); // ← ADD THIS TOO
        successCallback(events)
      })
      .catch(err => failureCallback(err));
  }

  // Colormaps for Status
  const colorMap = {
    not_arrived: "#9CA3AF",  
    arrived:    "#3B82F6",   
    ongoing:    "#F59E0B",   
    done:       "#10B981",   
    cancelled:  "#EF4444"    
  };

  // Status button handling
  statusButtons.forEach(btn => {
    btn.addEventListener("click", function () {
      if (!currentEventId) return;

      const statusMap = {
        "Not Yet Arrived": "not_arrived",
        "Arrived": "arrived",
        "On Going": "ongoing",
        "Done": "done"
      };

      const chosen = statusMap[btn.textContent.trim()];
      if (!chosen) {
        closeModal("status-modal");
        return;
      }

      // Special handling for "Done" button - open steps modal
      if (chosen === "done") {
        // Initialize the steps modal with appointment ID
        if (typeof window.initDoneStepsModal === "function") {
          window.initDoneStepsModal(currentEventId);
        }
        openModal("done-steps-modal");
        return;
      }

      // For other statuses, update immediately as before
      fetch(`/dashboard/appointment/update-status/${currentEventId}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ status: chosen })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if (timelineCalendar) timelineCalendar.refetchEvents();
          if (mainCalendar) mainCalendar.refetchEvents();

          setTimeout(() => {
            if (typeof window.renderTodaysAppointments === "function") {
              window.renderTodaysAppointments();
            }
          }, 250);


          closeModal("status-modal");
        }
      });
    });
  });

  if (mainCalendarEl && timelineCalendarEl && listEl) {

    // Ensure only one selected day in main calendar
    // dateInput can be a Date or a YYYY-MM-DD string
    function setMainSelectedDate(dateInput) {
      const calendarEl = document.getElementById("calendar");
      if (!calendarEl) return;

      // 1) Normalize to YYYY-MM-DD
      let dateStr;
      if (dateInput instanceof Date) {
        dateStr = dateInput.toISOString().split("T")[0]; // YYYY-MM-DD
      } else {
        // assume it's already a YYYY-MM-DD string (e.g. info.dateStr)
        dateStr = dateInput;
      }

      // 2) Clear ALL previously selected cells
      calendarEl
        .querySelectorAll('.fc-daygrid-day[data-selected="true"]')
        .forEach((el) => {
          el.style.backgroundColor = "";
          el.style.borderRadius = "";
          el.style.boxShadow = "";
          el.dataset.selected = "false";
        });

      // 3) Find the cell for the given date and apply styles
      const cell = calendarEl.querySelector(`.fc-daygrid-day[data-date="${dateStr}"]`);
      if (cell) {
        cell.style.backgroundColor = "#e5e7eb";   // Tailwind gray-200
        cell.style.borderRadius = "0.375rem";     // rounded-md
        cell.style.boxShadow = "inset 0 0 0 2px #9ca3af"; // like ring-2 ring-gray-400
        cell.dataset.selected = "true";
      }
    }

    // Main monthly calendar
    mainCalendar = new FullCalendar.Calendar(mainCalendarEl, {
      initialView: 'dayGridMonth',
      height: "auto",
      aspectRatio: window.innerWidth < 768 ? 1.0 : 1.4, // Smaller aspect ratio on mobile
      expandRows: true,
      handleWindowResize: true,
      customButtons: {
      myToday: {
        text: 'Today',
        click: function() {
          const today = new Date();

          // 1) Move month view to today
          mainCalendar.today();

          // 2) Also move timeline to today's day view
          if (window.timelineCalendar) {
            timelineCalendar.changeView("timeGridDay", today);
          }

          // 3) Ensure only today is selected in main calendar
          setMainSelectedDate(today);
        }
      }
    },
    headerToolbar: { left: "prev myToday", center: "title", right: "next" },



      events: fetchEvents,

      events: fetchEvents,

      eventContent: function(info) {
        // Only customize in month view
        if (info.view.type !== "dayGridMonth") {
          return {}; // default rendering in other views (if any)
        }

        const calendar = info.view.calendar;
        const allEvents = calendar.getEvents();
        const dateStr = info.event.startStr.split("T")[0];

        // All events that start on this same day
        const sameDayEvents = allEvents.filter(ev => ev.startStr.startsWith(dateStr));
        const count = sameDayEvents.length;

        // Only render for the earliest event of that day
        sameDayEvents.sort((a, b) => a.start - b.start);
        if (sameDayEvents[0].id !== info.event.id) {
          return { domNodes: [] }; // hide this event row
        }

        // Create a small badge like "3 appointments"
        const badge = document.createElement("div");
        badge.style.display = "inline-block";
        badge.style.padding = "2px 6px";
        badge.style.borderRadius = "9999px";
        badge.style.fontSize = "0.7rem";
        badge.style.fontWeight = "600";
        badge.style.backgroundColor = "#3B82F6"; // blue
        badge.style.color = "white";
        badge.textContent = `${count} Appt${count > 1 ? "s" : ""}`;

        return { domNodes: [badge] };
      },

      titleFormat: { year: 'numeric', month: 'short' },

      dateClick: function(info) {
        // 1) Use the exact YYYY-MM-DD string from FullCalendar
        setMainSelectedDate(info.dateStr);

        // 2) Sync timeline view (still using Date)
        const current = timelineCalendar.view.currentStart.toISOString().split("T")[0];
        const clicked = info.date.toISOString().split("T")[0];

        if (current !== clicked) {
          timelineCalendar.changeView("timeGridDay", info.date);
        }
      }

    });
    mainCalendar.render();
    


    // Timeline calendar
    timelineCalendar = new FullCalendar.Calendar(timelineCalendarEl, {
      initialView: 'timeGridDay',
      height: window.innerWidth < 768 ? 400 : "auto", // Fixed height on mobile
      expandRows: true,
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "timeGridDay,timeGridWeek"
      },
      buttonText: { today: 'Today', day: 'Day', week: 'Week' },
      slotMinTime: "08:00:00",
      slotMaxTime: "18:00:00",
      slotDuration: "00:15:00",
      slotLabelInterval: "01:00:00",
      slotEventOverlap: false,
      allDaySlot: false,
      events: fetchEvents,
      titleFormat: { year: 'numeric', month: 'short', day: 'numeric' },

      //added
      eventMinHeight: 40,

      eventDidMount: function(info) {
        info.el.style.backgroundColor = "transparent";
        info.el.style.border = "none";
        info.el.style.boxShadow = "none";
        info.el.style.padding = "0";
      },

      //displaying of cards and buttons
        eventContent: function(info) {
        const status = info.event.extendedProps && info.event.extendedProps.status
          ? info.event.extendedProps.status
          : "not_arrived";
        const base = colorMap[status] || "#9CA3AF";
        const tinted = hexToRgba(base, 0.3);

        // Outer card
        const wrapper = document.createElement("div");
        wrapper.style.display = "flex";
        wrapper.style.alignItems = "stretch";
        wrapper.style.width = "100%";
        wrapper.style.height = "100%";
        wrapper.style.boxSizing = "border-box";
        wrapper.style.padding = "6px 8px";
        wrapper.style.borderRadius = "8px";
        wrapper.style.overflow = "hidden";
        wrapper.style.backgroundColor = tinted;
        wrapper.style.minHeight = "40px";
        wrapper.style.cursor = "pointer";

        const props = info.event.extendedProps || {};
        const isCancelled = props.status === "cancelled";
        const canManage = !!props.can_manage;

        console.log("EVENT PROPS", info.event.id, props);

        // if cancelled and user cannot manage, disable pointer/interactions
        if (isCancelled && !canManage) {
          wrapper.style.cursor = "default";
          wrapper.style.opacity = "0.6";
        }

        const stripe = document.createElement("div");
        stripe.style.width = "6px";
        stripe.style.height = "100%";
        stripe.style.flex = "0 0 6px";
        stripe.style.borderRadius = "6px 0 0 6px";
        stripe.style.marginRight = "8px";
        stripe.style.backgroundColor = base;
        stripe.style.pointerEvents = "none";

        // Main content: vertical (title on top, time+buttons at bottom)
        const content = document.createElement("div");
        content.style.flex = "1";
        content.style.minWidth = "0";
        content.style.color = "#0f172a";
        content.style.display = "flex";
        content.style.flexDirection = "column";
        content.style.alignItems = "flex-start";
        content.style.justifyContent = "space-between";

        // Title (top-left)
        const title = document.createElement("div");
        title.textContent = info.event.title || "";
        title.style.whiteSpace = "nowrap";
        title.style.overflow = "hidden";
        title.style.textOverflow = "ellipsis";
        title.style.fontSize = "0.9rem";
        title.style.fontWeight = "600";
        title.style.marginBottom = "0px"; //was 2

        // Bottom row: time (left) + buttons (right)
        const bottomRow = document.createElement("div");
        bottomRow.style.display = "flex";
        bottomRow.style.alignItems = "center";
        bottomRow.style.justifyContent = "space-between";
        bottomRow.style.width = "100%";
        bottomRow.style.gap = "4px"; //was 8

        // Time (bottom-left)
        const startTime = info.event.start
          ? info.event.start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : "";
        const endTime = info.event.end
          ? info.event.end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : "";
        const time = document.createElement("div");
        time.textContent = endTime ? `${startTime} - ${endTime}` : startTime;
        time.style.fontSize = "0.75rem";
        time.style.color = "#475569";

        // Buttons (bottom-right)
        const btnRow = document.createElement("div");
        btnRow.style.display = "flex";
        btnRow.style.flexShrink = "0";
        btnRow.style.gap = "2px"; //was 4
        btnRow.style.flexWrap = "wrap";
        btnRow.style.justifyContent = "flex-end";

      if (info.view && info.view.type === "timeGridDay") {
        const followBtn = document.createElement("button");
        followBtn.textContent = "Follow up";
        followBtn.style.padding = "4px 8px";
        followBtn.style.fontSize = "0.7rem";
        followBtn.style.borderRadius = "6px";
        followBtn.style.background = "#16a34a";
        followBtn.style.color = "#fff";

        const rescheduleBtn = document.createElement("button");
        rescheduleBtn.textContent = "Reschedule";
        rescheduleBtn.style.padding = "4px 8px";
        rescheduleBtn.style.fontSize = "0.7rem";
        rescheduleBtn.style.borderRadius = "6px";
        rescheduleBtn.style.background = "#2563eb";
        rescheduleBtn.style.color = "#fff";

        if (!isCancelled || canManage) {
          followBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            currentEventId = info.event.id;
            const propsInner = info.event.extendedProps || {};

            const origInput = document.getElementById("followup-original-id");
            if (origInput) origInput.value = currentEventId;

            const followDate = document.getElementById("followup-date");
            if (followDate && propsInner.preferred_date) {
              followDate.value = propsInner.preferred_date;
            }

            openModal("followup-modal");
          });

          rescheduleBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          currentEventId = info.event.id;
          window.reschedAppointmentId = info.event.id; 

          const propsInner = info.event.extendedProps || {};

          // Basic fields
          document.getElementById("resched-dentist").value  = propsInner.dentist_id || "";
          document.getElementById("resched-location").value = propsInner.location || "";
          document.getElementById("resched-date").value     = propsInner.preferred_date || propsInner.date || "";
          document.getElementById("resched-email").value    = propsInner.email || "";

          // ----- Time prefill (preferred_time or time) -----
          const rawTime = propsInner.preferred_time || propsInner.time || ""; // e.g. "09:30 AM"
          const reschedAmpm  = document.getElementById("resched-ampm");
          const reschedHour  = document.getElementById("resched-hour");
          const reschedMin   = document.getElementById("resched-minute");
          const reschedHidden = document.getElementById("resched-time-hidden");

          if (rawTime && reschedAmpm && reschedHour && reschedMin) {
            const [timePart, ampmPart] = rawTime.split(" ");
            const [hStr, mStr] = timePart.split(":");

            // Set AM/PM first to rebuild hour options
            reschedAmpm.value = ampmPart;
            reschedAmpm.dispatchEvent(new Event("change"));

            // Now set hour + minute
            reschedHour.value = String(parseInt(hStr, 10)); // "09" -> "9"
            reschedMin.value  = mStr;

            // Update hidden 24h field (matches initRescheduleForm logic)
            if (typeof to24Hour === "function") {
              reschedHidden.value = `${String(to24Hour(reschedHour.value, ampmPart)).padStart(2, "0")}:${mStr}`;
            } else {
              reschedHidden.value = ""; // fallback
            }
          }

          // ----- Services pre-check -----
          const serviceIds = propsInner.service_ids || [];   // from views: extendedProps.service_ids
          const allServiceCbs = document.querySelectorAll("#resched-services-checkboxes input.resched-service-checkbox");
          allServiceCbs.forEach(cb => {
            cb.checked = serviceIds.includes(parseInt(cb.value, 10));
          });

          // Refresh selected-service tags in reschedule modal
          if (typeof window.refreshReschedSelectedServiceTags === "function") {
            window.refreshReschedSelectedServiceTags();
          }

          // ----- Current schedule display -----
          const currentScheduleEl = document.getElementById("resched-current-time");
          if (currentScheduleEl) {
            const dateLabel = propsInner.preferred_date || propsInner.date || "";
            const timeLabel = propsInner.preferred_time || propsInner.time || "";
            currentScheduleEl.textContent = dateLabel && timeLabel
              ? `${dateLabel} at ${timeLabel}`
              : "";
          }

          openModal("reschedule-modal");
        });

        } else {
          // visually show disabled buttons for non-admin cancelled
          followBtn.disabled = true;
          rescheduleBtn.disabled = true;
          followBtn.style.opacity = "0.5";
          rescheduleBtn.style.opacity = "0.5";
          followBtn.style.cursor = "default";
          rescheduleBtn.style.cursor = "default";
        }

        btnRow.appendChild(followBtn);
        btnRow.appendChild(rescheduleBtn);
      }


        bottomRow.appendChild(time);
        bottomRow.appendChild(btnRow);

        content.appendChild(title);
        content.appendChild(bottomRow);

        wrapper.appendChild(stripe);
        wrapper.appendChild(content);

        // Make whole card open Status modal only if allowed
        if (!isCancelled || canManage) {
          wrapper.addEventListener("click", () => {
            currentEventId = info.event.id;
            window.reschedAppointmentId = info.event.id;
            window.currentEventId = currentEventId; 
            const props2 = info.event.extendedProps || {};
            document.getElementById("detail-dentist").textContent = props2.dentist || "N/A";
            document.getElementById("detail-location").textContent = props2.location || "N/A";
            document.getElementById("detail-date").textContent = props2.preferred_date || props2.date || "N/A";
            document.getElementById("detail-time").textContent = props2.preferred_time || props2.time || "N/A";
            document.getElementById("detail-service").textContent = props2.service || "N/A";
            openModal("status-modal");
          });
        }

        return { domNodes: [wrapper] };
      }


    });

    //renders the calendar
    timelineCalendar.render();

    // EXPOSE THEM GLOBALLY so appointment.js can use them
    window.mainCalendar = mainCalendar;
    window.timelineCalendar = timelineCalendar;

    // --- Extra timeline controls (Day/Week/Today) ---
    function makeBtn(label, onClick) {
      const btn = document.createElement("button");
      btn.textContent = label;
      btn.className =
        "px-3 py-1.5 text-sm font-medium border border-gray-300 rounded-md " +
        "bg-white/80 text-gray-600 hover:bg-gray-100 transition " +
        "focus:outline-none focus:ring-2 focus:ring-blue-500";
      btn.onclick = onClick;
      return btn;
    }

    
    timelineControlsEl.appendChild(makeBtn("Week", () => timelineCalendar.changeView("timeGridWeek")));
    timelineControlsEl.appendChild(makeBtn("Day", () => timelineCalendar.changeView("timeGridDay")));
    timelineControlsEl.appendChild(
    makeBtn("Today", () => {
      const today = new Date();

      // 1) Move the timeline to today (existing behavior)
      timelineCalendar.today();

      // 2) Move the main month view so today is in view
      if (window.mainCalendar) {
        mainCalendar.gotoDate(today); // ensure month is correct
      }

      // 3) Ensure only today is selected in main calendar
      setMainSelectedDate(today);
    })
  );


    // --- Render today's appointments in the side list ---
    window.renderTodaysAppointments = function() {
      listEl.innerHTML = "";
      const today = new Date().toISOString().split("T")[0];
      const todaysEvents = timelineCalendar.getEvents().filter(ev => ev.startStr.startsWith(today));

      if (todaysEvents.length === 0) {
        listEl.innerHTML = `<li class="text-gray-500 text-sm">No appointments today.</li>`;
      } else {
        todaysEvents.forEach(ev => {
          const base = colorMap[ev.extendedProps.status] || "#9CA3AF";
          const tinted = base + "33";

          const li = document.createElement("li");
          li.className = "relative rounded-lg p-3 shadow-sm mb-2 flex items-start";
          li.style.backgroundColor = tinted;

          const stripe = document.createElement("div");
          stripe.className = "rounded-l-lg";
          stripe.style.width = "6px";
          stripe.style.height = "100%";
          stripe.style.background = base;
          stripe.style.flex = "0 0 6px";
          stripe.style.marginRight = "8px";

          const content = document.createElement("div");
          content.className = "pl-3";
          content.innerHTML = `
            <p class="text-sm text-gray-600">${ev.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
            <p class="font-medium text-gray-900">${ev.title}</p>
          `;

          li.appendChild(stripe);
          li.appendChild(content);

          // cancelled / permission logic for side list item
          const isCancelled = ev.extendedProps.status === "cancelled";
          const canManage = !!ev.extendedProps.can_manage;

          if (!isCancelled || canManage) {
            li.addEventListener("click", () => {
              currentEventId = ev.id;
              window.currentEventId = currentEventId;
              document.getElementById("detail-dentist").textContent = ev.extendedProps.dentist || "N/A";
              document.getElementById("detail-location").textContent = ev.extendedProps.location || "N/A";
              document.getElementById("detail-date").textContent = ev.extendedProps.preferred_date || "N/A";
              document.getElementById("detail-time").textContent = ev.extendedProps.preferred_time || "N/A";
              document.getElementById("detail-service").textContent = ev.extendedProps.service || "N/A";
              openModal("status-modal");
            });
          } else {
            li.style.cursor = "default";
            li.style.opacity = "0.6";
          }

          listEl.appendChild(li);
        });
      }
    }

    window.renderTodaysAppointments();
    timelineCalendar.on("eventAdd", window.renderTodaysAppointments);
    timelineCalendar.on("eventRemove", window.renderTodaysAppointments);
    timelineCalendar.on("eventChange", window.renderTodaysAppointments);
  }
});

function hexToRgba(hex, alpha) {
  hex = hex.replace("#", "");
  if (hex.length === 3) {
    hex = hex.split("").map(ch => ch + ch).join("");
  }
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Helper to get CSRF token from cookies ---
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function convertTo24Hour(timeStr) {
  const [time, modifier] = timeStr.split(" ");
  let [hours, minutes] = time.split(":");
  if (modifier === "PM" && hours !== "12") hours = parseInt(hours, 10) + 12;
  if (modifier === "AM" && hours === "12") hours = "00";
  return `${hours}:${minutes}`;
}





