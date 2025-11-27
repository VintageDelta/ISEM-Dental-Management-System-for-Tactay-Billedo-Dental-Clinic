

let currentEventId = null;
let mainCalendar = null;
let timelineCalendar = null;

document.addEventListener('DOMContentLoaded', function () {
  const mainCalendarEl = document.getElementById('calendar');
  const timelineCalendarEl = document.getElementById('timeline-calendar');
  const timelineControlsEl = document.getElementById('timeline-controls');
  const listEl = document.getElementById('todays-appointments-list');
  const statusButtons = document.querySelectorAll("#followup-modal button");
  const branchFilterEl = document.getElementById("branch-filter");
  const eventsUrl = "/dashboard/appointment/events/";
  


  branchFilterEl.addEventListener("change", function () {
    if (mainCalendar) mainCalendar.refetchEvents();
    if (timelineCalendar) timelineCalendar.refetchEvents();

    setTimeout(() => {
      if (typeof renderTodaysAppointments === "function") {
        renderTodaysAppointments();
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
        "Done": "done",
        "Cancel Appointment": "cancelled"
      };

      const chosen = statusMap[btn.textContent.trim()];
      if (!chosen) {
        closeModal("followup-modal");
        return;
      }

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
            if (typeof renderTodaysAppointments === "function") {
              renderTodaysAppointments();
            }
          }, 250);

          closeModal("followup-modal");
        }
      });
    });
  });

  if (mainCalendarEl && timelineCalendarEl && listEl) {
    // Main monthly calendar
    mainCalendar = new FullCalendar.Calendar(mainCalendarEl, {
      initialView: 'dayGridMonth',
      height: "auto",
      aspectRatio: 1.4,
      expandRows: true,
      handleWindowResize: true,
      headerToolbar: { left: "prev today", center: "title", right: "next" },
      buttonText: { today: 'Today' },
      events: fetchEvents,

      eventDidMount: function (info) {
        info.el.classList.add(
          'bg-blue-500', 'text-white', 'text-xs', 'font-medium',
          'px-2', 'py-1', 'rounded-lg', 'shadow-sm', 'truncate'
        );
      },
      titleFormat: { year: 'numeric', month: 'short' },
      dateClick: function(info) {
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
      height: "auto",
      expandRows: true,
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "timeGridDay,timeGridWeek"
      },
      buttonText: { today: 'Today', day: 'Day', week: 'Week' },
      slotMinTime: "07:00:00",
      slotMaxTime: "18:00:00",
      slotDuration: "00:15:00",
      slotLabelInterval: "01:00:00",
      slotEventOverlap: false,
      allDaySlot: false,
      events: fetchEvents,
      titleFormat: { year: 'numeric', month: 'short', day: 'numeric' },

      // We DON'T rely on FullCalendars default styling 
      eventDidMount: function(info) {
        try {
          // debug (open console to see)
          // console.log("eventDidMount:", info.event.id, info.event.extendedProps.status);

          const status = info.event.extendedProps && info.event.extendedProps.status
            ? info.event.extendedProps.status
            : "not_arrived";
          const base = colorMap[status] || "#9CA3AF";
          const tinted = base + "33";

          // CARD deets css here cuz why not?
          const wrapper = document.createElement("div");
          wrapper.style.display = "flex";
          wrapper.style.alignItems = "flex-start";
          wrapper.style.width = "100%";
          wrapper.style.height = "100%";
          wrapper.style.boxSizing = "border-box";
          wrapper.style.padding = "6px 8px";
          wrapper.style.borderRadius = "8px";
          wrapper.style.overflow = "hidden";
          wrapper.style.backgroundColor = tinted;
          wrapper.style.minHeight = "60px"; // height of the Card
          wrapper.style.cursor = "pointer";

          const stripe = document.createElement("div");
          stripe.style.width = "6px";
          stripe.style.height = "100%";
          stripe.style.flex = "0 0 6px";
          stripe.style.borderRadius = "6px 0 0 6px";
          stripe.style.marginRight = "8px";
          stripe.style.backgroundColor = base;
          stripe.style.pointerEvents = "none";

          const content = document.createElement("div");
          content.style.flex = "1";
          content.style.minWidth = "0"; 
          content.style.color = "#0f172a";

          const title = document.createElement("div");
          title.textContent = info.event.title || "";
          title.style.whiteSpace = "nowrap";
          title.style.overflow = "hidden";
          title.style.textOverflow = "ellipsis";
          title.style.fontSize = "0.9rem";
          title.style.fontWeight = "600";
          title.style.marginBottom = "2px";

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
          time.style.marginBottom = "4px";

          content.appendChild(title);
          content.appendChild(time);

          // Add buttons if in day view
          if (info.view && info.view.type === "timeGridDay") {
            const btnContainer = document.createElement("div");
            btnContainer.style.marginTop = "6px";
            btnContainer.style.display = "flex";
            btnContainer.style.gap = "6px";

            const followBtn = document.createElement("button");
            followBtn.textContent = "Follow up";
            followBtn.style.padding = "4px 8px";
            followBtn.style.fontSize = "0.7rem";
            followBtn.style.borderRadius = "6px";
            followBtn.style.background = "#16a34a";
            followBtn.style.color = "#fff";
            followBtn.addEventListener("click", (e) => {
              e.stopPropagation();
              currentEventId = info.event.id;
              document.getElementById("detail-dentist").textContent = info.event.extendedProps.dentist || "N/A";
              document.getElementById("detail-location").textContent = info.event.extendedProps.location || "N/A";
              document.getElementById("detail-date").textContent = info.event.extendedProps.preferred_date || "N/A";
              document.getElementById("detail-time").textContent = info.event.extendedProps.preferred_time || "N/A";
              document.getElementById("detail-service").textContent = info.event.extendedProps.service || "N/A";
              document.getElementById("detail-reason").textContent = info.event.extendedProps.reason || "N/A";
              openModal("followup-modal");
            });

            const rescheduleBtn = document.createElement("button");
            rescheduleBtn.textContent = "Reschedule";
            rescheduleBtn.style.padding = "4px 8px";
            rescheduleBtn.style.fontSize = "0.7rem";
            rescheduleBtn.style.borderRadius = "6px";
            rescheduleBtn.style.background = "#2563eb";
            rescheduleBtn.style.color = "#fff";

            //resched btn handler
            rescheduleBtn.addEventListener("click", (e) => {
              e.stopPropagation();
              currentEventId = info.event.id;

              // Prefill form fields
              document.getElementById("resched-dentist").value = info.event.extendedProps.dentist_id || "";
              document.getElementById("resched-location").value = info.event.extendedProps.location || "";
              document.getElementById("resched-date").value = info.event.extendedProps.preferred_date || "";
              document.getElementById("resched-time").value = info.event.extendedProps.preferred_time
                ? convertTo24Hour(info.event.extendedProps.preferred_time)
                : "";
              const selectedServices = info.event.extendedProps.service_ids || [];
              document.querySelectorAll('#resched-services-checkboxes input[type="checkbox"]').forEach(cb => {
                  cb.checked = selectedServices.includes(parseInt(cb.value));
              });
              document.getElementById("resched-reason").value = info.event.extendedProps.reason || "";

              // Show current scheduled time
              const start = info.event.start;
              const formatted = start.toLocaleString("en-US", { 
                weekday: "long", month: "short", day: "numeric", 
                hour: "numeric", minute: "2-digit" 
              });
              document.getElementById("resched-current-time").textContent = formatted;

              openModal("reschedule-modal");
            });


            btnContainer.appendChild(followBtn);
            btnContainer.appendChild(rescheduleBtn);
            content.appendChild(btnContainer);
          }

          wrapper.appendChild(stripe);
          wrapper.appendChild(content);

          // Replace inner content of the FC-generated node with our card
          info.el.innerHTML = "";
          // remove FC default backgrounds that might override
          info.el.style.background = "transparent";
          info.el.style.border = "none";
          info.el.style.padding = "0";
          info.el.style.boxShadow = "none";
          // make the outer container allow our card to stretch
          info.el.style.display = "flex";
          info.el.style.alignItems = "stretch";

          info.el.appendChild(wrapper);
        } catch (err) {
          console.error("eventDidMount error:", err);
        }
      }
    });

    //renders the calendar
    timelineCalendar.render();


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
    timelineControlsEl.appendChild(makeBtn("Today", () => timelineCalendar.today()));

    // --- Render today's appointments in the side list ---
    function renderTodaysAppointments() {
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

          li.addEventListener("click", () => {
            currentEventId = ev.id;
            document.getElementById("detail-dentist").textContent = ev.extendedProps.dentist || "N/A";
            document.getElementById("detail-location").textContent = ev.extendedProps.location || "N/A";
            document.getElementById("detail-date").textContent = ev.extendedProps.preferred_date || "N/A";
            document.getElementById("detail-time").textContent = ev.extendedProps.preferred_time || "N/A";
            document.getElementById("detail-service").textContent = ev.extendedProps.service || "N/A";
            document.getElementById("detail-reason").textContent = ev.extendedProps.reason || "N/A";
            openModal("followup-modal");
          });

          listEl.appendChild(li);
        });
      }
    }

    renderTodaysAppointments();
    timelineCalendar.on("eventAdd", renderTodaysAppointments);
    timelineCalendar.on("eventRemove", renderTodaysAppointments);
    timelineCalendar.on("eventChange", renderTodaysAppointments);
  }
});


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





