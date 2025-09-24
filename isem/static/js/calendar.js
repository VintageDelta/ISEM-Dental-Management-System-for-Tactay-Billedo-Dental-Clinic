let currentEventId = null;
let mainCalendar = null;
let timelineCalendar = null;

document.addEventListener('DOMContentLoaded', function () {
  const mainCalendarEl = document.getElementById('calendar');
  const timelineCalendarEl = document.getElementById('timeline-calendar');
  const timelineControlsEl = document.getElementById('timeline-controls');
  const listEl = document.getElementById('todays-appointments-list');
  const statusButtons = document.querySelectorAll("#followup-modal button");

  // --- Status button handling ---
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

      // --- Send update request for appointment status ---
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
          // --- Refresh both calendars after update ---
          if (timelineCalendar) timelineCalendar.refetchEvents();
          if (mainCalendar) mainCalendar.refetchEvents();

          // --- Re-render today’s list after small delay ---
          setTimeout(() => {
            if (typeof renderTodaysAppointments === "function") {
              renderTodaysAppointments();
            }
          }, 250);

          // --- Close modal once status is updated ---
          closeModal("followup-modal");
        }
      });
    });
  });

  if (mainCalendarEl && timelineCalendarEl && listEl) {
    // --- Main monthly calendar ---
    mainCalendar = new FullCalendar.Calendar(mainCalendarEl, {
      initialView: 'dayGridMonth',
      height: "auto",
      aspectRatio: 1.4,
      expandRows: true,
      handleWindowResize: true,
      headerToolbar: { left: "prev today", center: "title", right: "next" },
      buttonText: { today: 'Today' },
      events: eventsUrl,
      eventDidMount: function (info) {
        info.el.classList.add(
          'bg-blue-500', 'text-white', 'text-xs', 'font-medium',
          'px-2', 'py-1', 'rounded-lg', 'shadow-sm', 'truncate'
        );
      },
      titleFormat: { year: 'numeric', month: 'short' },
      dateClick: function(info) {
        // --- Switch timeline calendar when clicking a date ---
        timelineCalendar.changeView("timeGridDay", info.date);
      }
    });
    mainCalendar.render();

    // --- Timeline (daily/weekly) calendar ---
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
      slotDuration: "00:20:00",
      slotLabelInterval: "01:00:00",
      slotEventOverlap: false,
      allDaySlot: false,
      events: eventsUrl,
      titleFormat: { year: 'numeric', month: 'short', day: 'numeric' },

      eventContent: function(arg) {
        const title = document.createElement("div");
        title.textContent = arg.event.title;
        title.className = "truncate text-sm font-semibold text-white-800";

        const startTime = arg.event.start
          ? arg.event.start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : "";
        const endTime = arg.event.end
          ? arg.event.end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          : "";

        const time = document.createElement("div");
        time.textContent = endTime ? `${startTime} - ${endTime}` : startTime;
        time.className = "text-sm text-white-500";

        if (arg.view.type === "timeGridDay") {
          const btnContainer = document.createElement("div");
          btnContainer.className = "mt-1 flex gap-1";
          
          // --- Follow-up button inside event card ---
          const followBtn = document.createElement("button");
          followBtn.textContent = "Follow up";
          followBtn.className = "px-2 py-0.5 text-xs bg-green-500 text-white rounded hover:bg-green-600";
          followBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            currentEventId = arg.event.id;
            document.getElementById("detail-dentist").textContent = arg.event.extendedProps.dentist || "N/A";
            document.getElementById("detail-location").textContent = arg.event.extendedProps.location || "N/A";
            document.getElementById("detail-date").textContent = arg.event.extendedProps.preferred_date || "N/A";
            document.getElementById("detail-time").textContent = arg.event.extendedProps.preferred_time || "N/A";
            document.getElementById("detail-service").textContent = arg.event.extendedProps.service || "N/A";
            document.getElementById("detail-reason").textContent = arg.event.extendedProps.reason || "N/A";
            openModal("followup-modal");
          });

          // --- Reschedule button inside event card ---
          const rescheduleBtn = document.createElement("button");
          rescheduleBtn.textContent = "Reschedule";
          rescheduleBtn.className = "px-2 py-0.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600";
          rescheduleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const start = arg.event.start;
            const dateOptions = { weekday: "long", month: "short", day: "numeric" };
            const formattedDate = start.toLocaleDateString("en-US", dateOptions).toUpperCase();
            const timeOptions = { hour: "numeric", minute: "2-digit" };
            const formattedTime = start.toLocaleTimeString("en-US", timeOptions);

            // --- Fill reschedule modal with current appointment date/time ---
            document.getElementById("reschedule-date-display").innerHTML = `
              <div class="px-4 py-2 bg-blue-100 text-blue-800 font-semibold rounded-full w-fit">${formattedDate}</div>
              <div class="px-4 py-2 bg-green-100 text-green-800 font-medium rounded-full w-fit">${formattedTime}</div>
            `;
            openModal("reschedule-modal");
          });

          btnContainer.appendChild(followBtn);
          btnContainer.appendChild(rescheduleBtn);

          const container = document.createElement("div");
          container.className = "flex flex-col overflow-visible";
          container.appendChild(title);
          container.appendChild(time);
          container.appendChild(btnContainer);

          return { domNodes: [container] };
        }

        const container = document.createElement("div");
        container.className = "flex flex-col overflow-visible";
        container.appendChild(title);
        container.appendChild(time);
        return { domNodes: [container] };
      }
    });

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
          const li = document.createElement("li");
          li.className = "relative";
          li.innerHTML = `
            <div class="absolute -left-2 top-1 w-3 h-3 rounded-full bg-blue-500"></div>
            <p class="text-sm text-gray-500">
              ${ev.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </p>
            <p class="font-medium text-gray-800">${ev.title}</p>
          `;
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
