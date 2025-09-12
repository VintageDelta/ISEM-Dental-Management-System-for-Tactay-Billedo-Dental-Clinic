document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const controlsEl = document.getElementById('calendar-controls');
  const listEl = document.getElementById('todays-appointments-list');

  if (calendarEl && controlsEl && listEl) {
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      height: "auto",
      aspectRatio: 1.4,
      expandRows: true,
      handleWindowResize: true,
      headerToolbar: false, // disable default header

      eventDidMount: function (info) {
        info.el.classList.add(
          'bg-blue-500', 'text-white', 'text-xs', 'font-medium',
          'px-2', 'py-1', 'rounded-lg', 'shadow-sm', 'truncate'
        );
      },
      dayCellDidMount: function (info) {
        const dayNum = info.el.querySelector('.fc-daygrid-day-number');
        if (dayNum) {
          dayNum.classList.add('text-gray-700', 'font-semibold');
        }
        info.el.classList.add('rounded-lg', 'hover:bg-gray-50', 'transition');
      },
      events: [
        { title: 'Dental Check-up - John Doe', start: '2025-09-12T09:00:00' },
        { title: 'Follow-up - Jane Smith', start: '2025-09-12T11:00:00' },
        { title: 'Consultation - Mark Lee', start: '2025-09-12T14:00:00' }
      ],
      dateClick: function (info) {
        info.dayEl.classList.add('bg-green-100', 'rounded-lg');
      }
    });

    calendar.render();

    // --- Render toolbar into external container ---
    const toolbar = document.createElement("div");
    toolbar.className = "fc-header-toolbar flex items-center justify-between mb-4";

    // Left side (navigation)
    const leftControls = document.createElement("div");
    leftControls.className = "flex items-center gap-2";

    // Title (fixed space so buttons don’t move)
    const titleWrapper = document.createElement("div");
    titleWrapper.className = "flex-1 text-center"; // takes full space in middle

    const titleSpan = document.createElement("span");
    titleSpan.className = "font-semibold text-gray-800 text-lg inline-block min-w-[180px]"; 
    titleSpan.textContent = calendar.view.title;

    titleWrapper.appendChild(titleSpan);

    // Right side (view buttons)
    const rightControls = document.createElement("div");
    rightControls.className = "flex items-center gap-2";

    // Reusable button factory
    function makeBtn(label, onClick) {
      const btn = document.createElement("button");
      btn.textContent = label;
      btn.className =
        "px-3 py-1.5 text-sm font-medium border border-gray-300 rounded-md " +
        "bg-transparent text-gray-700 hover:bg-gray-100 transition " +
        "focus:outline-none focus:ring-2 focus:ring-blue-500";
      btn.onclick = onClick;
      return btn;
    }

    // Navigation
    const prevBtn = makeBtn("Prev", () => calendar.prev());
    const nextBtn = makeBtn("Next", () => calendar.next());
    const todayBtn = makeBtn("Today", () => calendar.today());

    // Views
    const monthBtn = makeBtn("Month", () => calendar.changeView("dayGridMonth"));
    const weekBtn = makeBtn("Week", () => calendar.changeView("timeGridWeek"));
    const dayBtn = makeBtn("Day", () => calendar.changeView("timeGridDay"));

    // Assemble
    leftControls.appendChild(prevBtn);
    leftControls.appendChild(nextBtn);
    leftControls.appendChild(todayBtn);

    rightControls.appendChild(monthBtn);
    rightControls.appendChild(weekBtn);
    rightControls.appendChild(dayBtn);

    toolbar.appendChild(leftControls);
    toolbar.appendChild(titleWrapper);
    toolbar.appendChild(rightControls);
    controlsEl.appendChild(toolbar);

    // Keep title updated
    calendar.on("datesSet", function () {
      titleSpan.textContent = calendar.view.title;
});


    // --- Render today's appointments ---
    function renderTodaysAppointments() {
      listEl.innerHTML = ""; // clear
      const today = new Date().toISOString().split("T")[0]; // YYYY-MM-DD

      const todaysEvents = calendar.getEvents().filter(ev => {
        return ev.startStr.startsWith(today);
      });

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

    // Run once & hook events
    renderTodaysAppointments();
    calendar.on("eventAdd", renderTodaysAppointments);
    calendar.on("eventRemove", renderTodaysAppointments);
    calendar.on("eventChange", renderTodaysAppointments);
  }
});
