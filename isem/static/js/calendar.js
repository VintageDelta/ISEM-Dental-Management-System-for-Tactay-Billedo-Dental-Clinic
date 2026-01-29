

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

  // NEW: sync timeline height with main calendar (desktop only)
  function syncTimelineHeight() {
    const wrapper = document.getElementById("timeline-scroll");
    if (!wrapper || !mainCalendarEl) return;

    const isMobile = window.innerWidth < 768; // same as Tailwind md breakpoint

    if (isMobile) {
      // On mobile/stacked: make timeline tall enough and scrollable
      wrapper.style.height = "500px";       // increase from 400px so cards + buttons fit
      wrapper.style.maxHeight = "500px";
      wrapper.style.overflowY = "auto";
    } else {
      // On desktop/side-by-side: match main calendar height
      const calHeight = mainCalendarEl.offsetHeight;
      if (calHeight > 0) {
        wrapper.style.height = calHeight + "px";
        wrapper.style.maxHeight = calHeight + "px";
        wrapper.style.overflowY = "auto";
      }
    }
  }
  
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

    console.log("FETCHING:", url);

    fetch(url)
      .then(res => res.json())
      .then(events => {
        console.log("RECEIVED EVENTS:", events);
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
        closeAppointmentModal("status-modal");
        return;
      }

      // Special handling for "Done" button - open steps modal
      if (chosen === "done") {
        if (typeof window.initDoneStepsModal === "function") {
          window.initDoneStepsModal(currentEventId);
        }
        openAppointmentModal("done-steps-modal");
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

            // NEW: show status-updated modal with the label
            const msgEl = document.getElementById("status-updated-message");
            if (msgEl) {
              const label = btn.textContent.trim();
              msgEl.textContent = `Status has been changed to "${label}".`;
            }
            openAppointmentModal("status-updated-modal");

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
      aspectRatio: window.innerWidth < 768 ? 0.8 : 1.4, // Smaller aspect ratio on mobile
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
  if (info.view.type !== "dayGridMonth") {
    return {};
  }

  const calendar = info.view.calendar;
  const allEvents = calendar.getEvents();
  const dateStr = info.event.startStr.split("T")[0];

  const sameDayEvents = allEvents.filter(ev => ev.startStr.startsWith(dateStr));

  sameDayEvents.sort((a, b) => a.start - b.start);
  if (sameDayEvents[0].id !== info.event.id) {
    return { domNodes: [] };
  }

  const counts = {
    not_arrived: 0,
    arrived: 0,
    ongoing: 0,
    done: 0,
    cancelled: 0,
  };

  sameDayEvents.forEach(ev => {
    const status = ev.extendedProps && ev.extendedProps.status;
    if (status && counts.hasOwnProperty(status)) {
      counts[status]++;
    }
  });

  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (!total) {
    return { domNodes: [] };
  }

  const statusColors = {
    not_arrived: "#9CA3AF",
    arrived: "#3B82F6",
    ongoing: "#F59E0B",
    done: "#10B981",
    cancelled: "#EF4444",
  };

  const statusOrder = ["done", "ongoing", "arrived", "not_arrived", "cancelled"];

  // Outer container
  const container = document.createElement("div");
  container.style.display = "flex";
  container.style.flexWrap = "wrap";          // allow multiple lines
  container.style.alignItems = "center";
  container.style.gap = "4px";
  container.style.fontSize = "0.7rem";
  container.style.fontWeight = "600";
  container.style.maxWidth = "100%";          // stay inside the cell
  container.style.pointerEvents = "none";     // do NOT block clicks on the day cell
  container.style.overflow = "hidden";        // avoid overflow into next day

  function makePill(count, colorHex) {
    const wrapper = document.createElement("div");
    wrapper.style.display = "flex";
    wrapper.style.alignItems = "center";
    wrapper.style.gap = "3px";
    wrapper.style.flexShrink = "0";
    wrapper.style.maxWidth = "100%";

    const num = document.createElement("span");
    num.textContent = count;
    num.style.color = "#111827";

    const dot = document.createElement("span");
    dot.style.display = "inline-block";
    dot.style.width = "8px";
    dot.style.height = "8px";
    dot.style.borderRadius = "9999px";
    dot.style.backgroundColor = colorHex;

    wrapper.appendChild(num);
    wrapper.appendChild(dot);
    return wrapper;
  }

  statusOrder.forEach(key => {
    if (counts[key] > 0) {
      container.appendChild(makePill(counts[key], statusColors[key]));
    }
  });

  return { domNodes: [container] };
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
      height: "100%",
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
        eventContent: function(info) {const status = info.event.extendedProps && info.event.extendedProps.status
    ? info.event.extendedProps.status
    : "not_arrived";
      const base = colorMap[status] || "#9CA3AF";
      const tinted = hexToRgba(base, 0.3);

      // Outer card
      const wrapper = document.createElement("div");
      wrapper.style.display = "flex";
      wrapper.style.position = "relative";  // ← ADD THIS
      wrapper.style.width = "100%";
      wrapper.style.height = "100%";
      wrapper.style.boxSizing = "border-box";
      wrapper.style.padding = "8px";
      wrapper.style.borderRadius = "8px";
      wrapper.style.backgroundColor = tinted;
      wrapper.style.minHeight = "40px";
      wrapper.style.cursor = "pointer";

      const props = info.event.extendedProps || {};
      const isCancelled = props.status === "cancelled";
      const canManage = !!props.can_manage;

      if (isCancelled && !canManage) {
        wrapper.style.cursor = "default";
        wrapper.style.opacity = "0.6";
      }

      // Stripe
      const stripe = document.createElement("div");
      stripe.style.width = "4px";
      stripe.style.alignSelf = "stretch";
      stripe.style.borderRadius = "4px";
      stripe.style.marginRight = "8px";
      stripe.style.backgroundColor = base;

      // Content container (for text + buttons)
      const content = document.createElement("div");
      content.style.flex = "1";
      content.style.paddingRight = "8px";
      const isMobile = window.innerWidth < 768;

      // DAY vs WEEK text
      if (info.view && info.view.type === "timeGridDay" ) {
        const titleDiv = document.createElement("div");
        titleDiv.textContent = info.event.title || "";
        titleDiv.style.fontSize = isMobile ? "0.7rem" : "0.875rem";
        titleDiv.style.fontWeight = "600";
        titleDiv.style.color = "#1f2937";
        titleDiv.style.overflow = "hidden";
        titleDiv.style.textOverflow = "ellipsis";
        titleDiv.style.whiteSpace = "nowrap";
        content.appendChild(titleDiv);
      } else if (info.view && info.view.type === "timeGridWeek") {
        // Week view: show only time text
        const timeDiv = document.createElement("div");
        const start = info.event.start;
        const timeLabel = start
          ? start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : "";
        timeDiv.textContent = timeLabel;
        timeDiv.style.fontSize = "0.75rem";
        timeDiv.style.fontWeight = "600";
        timeDiv.style.color = "#1f2937";
        content.appendChild(timeDiv);
      }

      // Buttons container - ABSOLUTE POSITION (DAY VIEW ONLY)
      const btnRow = document.createElement("div");
      btnRow.style.position = "absolute";
      btnRow.style.bottom = "8px";
      btnRow.style.right = "8px";
      btnRow.style.display = "flex";
      btnRow.style.gap = "4px";
      btnRow.style.flexShrink = "0";
      

      if (info.view && info.view.type === "timeGridDay") {
        const followBtn = document.createElement("button");
        followBtn.textContent = "Follow up";
        followBtn.style.padding = isMobile ? "2px 4px" : "4px 8px";
        followBtn.style.fontSize = isMobile ? "0.6rem" : "0.7rem";
        followBtn.style.borderRadius = "6px";
        followBtn.style.background = "#16a34a";
        followBtn.style.color = "#fff";
        followBtn.style.border = "none";
        followBtn.style.cursor = "pointer";

        const rescheduleBtn = document.createElement("button");
        rescheduleBtn.textContent = "Reschedule";
        rescheduleBtn.style.padding = isMobile ? "2px 4px" : "4px 8px";
        rescheduleBtn.style.fontSize = isMobile ? "0.6rem" : "0.7rem";
        rescheduleBtn.style.borderRadius = "6px";
        rescheduleBtn.style.background = "#2563eb";
        rescheduleBtn.style.color = "#fff";
        rescheduleBtn.style.border = "none";
        rescheduleBtn.style.cursor = "pointer";

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
            openAppointmentModal("followup-modal");
          });

          rescheduleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            currentEventId = info.event.id;
            window.reschedAppointmentId = info.event.id;
            const propsInner = info.event.extendedProps || {};

            const rDentist  = document.getElementById("resched-dentist");
            const rLocation = document.getElementById("resched-location");
            const rDate     = document.getElementById("resched-date");
            const rEmail    = document.getElementById("resched-email");

            if (rDentist)  rDentist.value  = propsInner.dentist_id || "";
            if (rLocation) rLocation.value = propsInner.location || "";
            if (rDate)     rDate.value     = propsInner.preferred_date || propsInner.date || "";
            if (rEmail)    rEmail.value    = propsInner.email || "";

            const rawTime      = propsInner.preferred_time || propsInner.time || "";
            const reschedAmpm  = document.getElementById("resched-ampm");
            const reschedHour  = document.getElementById("resched-hour");
            const reschedMin   = document.getElementById("resched-minute");
            const reschedHidden= document.getElementById("resched-time-hidden");

            if (rawTime && reschedAmpm && reschedHour && reschedMin) {
              const [timePart, ampmPart] = rawTime.split(" ");
              const [hStr, mStr] = timePart.split(":");
              reschedAmpm.value = ampmPart;
              reschedAmpm.dispatchEvent(new Event("change"));
              reschedHour.value = String(parseInt(hStr, 10));
              reschedMin.value  = mStr;
              if (typeof to24Hour === "function" && reschedHidden) {
                reschedHidden.value = `${String(to24Hour(reschedHour.value, ampmPart)).padStart(2, "0")}:${mStr}`;
              }
            }

            const serviceIds = propsInner.service_ids || [];
            const allServiceCbs = document.querySelectorAll("#resched-services-checkboxes input.resched-service-checkbox");
            allServiceCbs.forEach(cb => {
              cb.checked = serviceIds.includes(parseInt(cb.value, 10));
            });

            if (typeof window.refreshReschedSelectedServiceTags === "function") {
              window.refreshReschedSelectedServiceTags();
            }

            const currentScheduleEl = document.getElementById("resched-current-time");
            if (currentScheduleEl) {
              const dateLabel = propsInner.preferred_date || propsInner.date || "";
              const timeLabel2 = propsInner.preferred_time || propsInner.time || "";
              currentScheduleEl.textContent = dateLabel && timeLabel2 ? `${dateLabel} at ${timeLabel2}` : "";
            }
            openAppointmentModal("reschedule-modal");
          });

        } else {
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

      // In week view there are no buttons, but we still append the (empty) btnRow
      content.appendChild(btnRow);
      wrapper.appendChild(stripe);
      wrapper.appendChild(content);


      if (!isCancelled || canManage) {
        wrapper.addEventListener("click", () => {
          console.log("timeline card clicked", info.event.id);
          console.log("opening status modal"); 

          currentEventId = info.event.id;
          window.reschedAppointmentId = info.event.id;
          window.currentEventId = currentEventId;
          const props2 = info.event.extendedProps || {};

          const dDentist  = document.getElementById("detail-dentist");
          const dLocation = document.getElementById("detail-location");
          const dDate     = document.getElementById("detail-date");
          const dTime     = document.getElementById("detail-time");
          const dService  = document.getElementById("detail-service");

          if (dDentist)  dDentist.textContent  = props2.dentist || "N/A";
          if (dLocation) dLocation.textContent = props2.location || "N/A";
          if (dDate)     dDate.textContent     = props2.preferred_date || props2.date || "N/A";
          if (dTime)     dTime.textContent     = props2.time || props2.preferred_time || "N/A";
          if (dService)  dService.textContent  = props2.service || "N/A";

          const cancelBtn = document.getElementById("status-cancel-btn");
          if (cancelBtn) {
            const status    = props2.status;
            const canManage = !!props2.can_manage;

            if (status === "done" && !canManage) {
              cancelBtn.disabled = true;
              cancelBtn.classList.add("opacity-50", "cursor-not-allowed");
            } else {
              cancelBtn.disabled = false;
              cancelBtn.classList.remove("opacity-50", "cursor-not-allowed");
            }
          }

          openAppointmentModal("status-modal");
        });

      }
      return { domNodes: [wrapper] };
    }
    });

    //renders the calendar
    timelineCalendar.render();

    syncTimelineHeight();
    window.addEventListener("resize", syncTimelineHeight);

    // EXPOSE THEM GLOBALLY so appointment.js can use them
    window.mainCalendar = mainCalendar;
    window.timelineCalendar = timelineCalendar;

    // --- Extra timeline controls (Day/Week/Today) ---
    function makeBtn(label, onClick) {
      const btn = document.createElement("button");
      btn.textContent = label;
      btn.className =
        "px-1.5 py-0.5 text-[0.65rem] md:px-3 md:py-1.5 md:text-sm font-medium " +
        "border border-gray-300 rounded-md " +
        "bg-white/80 text-gray-600 hover:bg-gray-100 transition " +
        "focus:outline-none focus:ring-2 focus:ring-blue-500";
      btn.onclick = onClick;
      return btn;
    }


    if (timelineControlsEl) {
      timelineControlsEl.appendChild(
        makeBtn("Week", () => timelineCalendar.changeView("timeGridWeek"))
      );
      timelineControlsEl.appendChild(
        makeBtn("Day", () => timelineCalendar.changeView("timeGridDay"))
      );
      timelineControlsEl.appendChild(
        makeBtn("Today", () => {
          const today = new Date();

          timelineCalendar.today();
          if (window.mainCalendar) {
            mainCalendar.gotoDate(today);
          }
          setMainSelectedDate(today);
        })
      );
    }



    // --- Render today's appointments in the side list ---
    window.renderTodaysAppointments = function() {
      listEl.innerHTML = "";
      const today = new Date().toISOString().split("T")[0];
      const todaysEvents = timelineCalendar.getEvents().filter(ev => ev.startStr.startsWith(today));

      // If none, show nothing (just leave the list empty)
      if (todaysEvents.length === 0) {
        return;
      }

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

                    const dDentist  = document.getElementById("detail-dentist");
                    const dLocation = document.getElementById("detail-location");
                    const dDate     = document.getElementById("detail-date");
                    const dTime     = document.getElementById("detail-time");
                    const dService  = document.getElementById("detail-service");

                    if (dDentist)  dDentist.textContent  = ev.extendedProps.dentist || "N/A";
                    if (dLocation) dLocation.textContent = ev.extendedProps.location || "N/A";
                    if (dDate)     dDate.textContent     = ev.extendedProps.preferred_date || ev.extendedProps.date || "N/A";
                    if (dTime)     dTime.textContent     = ev.extendedProps.time || ev.extendedProps.preferred_time || "N/A";
                    if (dService)  dService.textContent  = ev.extendedProps.service || "N/A";

                    // existing cancelBtn logic...
                    // NEW: toggle Cancel button based on status + can_manage
                    const cancelBtn = document.getElementById("status-cancel-btn");
                    if (cancelBtn) {
                      const status = ev.extendedProps.status;          // "done", etc.
                      const canManageUser = !!ev.extendedProps.can_manage;

                      if (status === "done" && !canManageUser) {
                        cancelBtn.disabled = true;
                        cancelBtn.classList.add("opacity-50", "cursor-not-allowed");
                      } else {
                        cancelBtn.disabled = false;
                        cancelBtn.classList.remove("opacity-50", "cursor-not-allowed");
                      }
                    }

                    openAppointmentModal("status-modal");
                  });
                } else {
                  li.style.cursor = "default";
                  li.style.opacity = "0.6";
                }


          listEl.appendChild(li);
      });
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





