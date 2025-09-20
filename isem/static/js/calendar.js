document.addEventListener('DOMContentLoaded', function () {
  const mainCalendarEl = document.getElementById('calendar');
  const timelineCalendarEl = document.getElementById('timeline-calendar');
  const timelineControlsEl = document.getElementById('timeline-controls');
  const listEl = document.getElementById('todays-appointments-list');

  if (mainCalendarEl && timelineCalendarEl && listEl) {
    // Main Calendar
    const mainCalendar = new FullCalendar.Calendar(mainCalendarEl, {
      initialView: 'dayGridMonth',
      height: "auto",
      aspectRatio: 1.4,
      expandRows: true,
      handleWindowResize: true,
      headerToolbar: { 
        left: "prev today", 
        center: "title", 
        right: "next" 
      },
      buttonText: {
        today: 'Today',
      },
      events: eventsUrl,
      eventDidMount: function (info) {
        info.el.classList.add(
          'bg-blue-500', 'text-white', 'text-xs', 'font-medium',
          'px-2', 'py-1', 'rounded-lg', 'shadow-sm', 'truncate'
        );
      },
      titleFormat: { year: 'numeric', month: 'short' },

      // updates the timeline with the clidked date
      dateClick: function(info) {
        timelineCalendar.changeView("timeGridDay", info.date); // jump to date
      }
    });
    mainCalendar.render();

    // Timeline Calendar
    const timelineCalendar = new FullCalendar.Calendar(timelineCalendarEl, {
      initialView: 'timeGridDay',
      height: "auto",
      expandRows: true,
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "timeGridDay,timeGridWeek"
      },
      buttonText: {
        today: 'Today',
        day: 'Day',
        week: 'Week',
      },
      slotMinTime: "07:00:00",
      slotMaxTime: "20:00:00",
      slotDuration: "00:15:00",
      slotLabelInterval: "01:00:00",
      slotEventOverlap: false,
      allDaySlot: false,
      events: eventsUrl,
      titleFormat: { year: 'numeric', month: 'short', day: 'numeric' }, // smaller title
      eventContent: function(arg) {
      const title = document.createElement("div");
      title.textContent = arg.event.title;
      title.className = "truncate text-sm font-semibold text-gray-800";

      if (arg.view.type === "timeGridDay") {
        const btnContainer = document.createElement("div");
        btnContainer.className = "mt-2 flex gap-2";

        // Follow up button
        const followBtn = document.createElement("button");
        followBtn.textContent = "Follow up";
        followBtn.className =
          "px-3 py-1 text-sm bg-green-500 text-white rounded-md hover:bg-green-600";
        followBtn.addEventListener("click", (e) => {
          e.stopPropagation();

          // Fill modal fields from extendedProps
          document.getElementById("detail-dentist").textContent = arg.event.extendedProps.dentist || "N/A";
          document.getElementById("detail-location").textContent = arg.event.extendedProps.location || "N/A";
          document.getElementById("detail-date").textContent = arg.event.extendedProps.date || "N/A";
          document.getElementById("detail-time").textContent = arg.event.extendedProps.time || "N/A";
          document.getElementById("detail-service").textContent = arg.event.extendedProps.service || "N/A";
          document.getElementById("detail-reason").textContent = arg.event.extendedProps.reason || "N/A";

          openModal("followup-modal");
        });

        // Reschedule button
        const rescheduleBtn = document.createElement("button");
        rescheduleBtn.textContent = "Reschedule";
        rescheduleBtn.className =
          "px-3 py-1 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600";
        rescheduleBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          openModal("reschedule-modal");
        });

        btnContainer.appendChild(followBtn);
        btnContainer.appendChild(rescheduleBtn);

        const container = document.createElement("div");
        container.className = "flex flex-col";
        container.appendChild(title);
        container.appendChild(btnContainer);

        return { domNodes: [container] };
      }

      return { domNodes: [title] };
    }
    });
    timelineCalendar.render();

    // External controls (Week, Day, Today)
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

    // Today's appointments list
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
          `
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

