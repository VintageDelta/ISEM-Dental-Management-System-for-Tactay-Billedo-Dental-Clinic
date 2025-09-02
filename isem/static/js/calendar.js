document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');

  if (calendarEl) {
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      height: '650px',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      // Add Tailwind classes to the toolbar
      eventDidMount: function(info) {
        info.el.classList.add(
          'bg-blue-500', 'text-white', 'text-sm', 'font-medium', 
          'px-2', 'py-1', 'rounded', 'truncate'
        );
      },
      dayCellDidMount: function(info) {
        // Add Tailwind styling to day numbers
        info.el.querySelector('.fc-daygrid-day-number')?.classList.add(
          'text-gray-700', 'font-semibold'
        );
      },
      events: [
        { title: 'Dental Check-up', start: '2025-08-25' },
        { title: 'Follow-up Appointment', start: '2025-08-28' },
        { title: 'Appointment with John', start: '2025-08-30' }
      ],
      // Optional: Tailwind styling for selected day
      dateClick: function(info) {
        info.dayEl.classList.add('bg-green-100', 'rounded');
      }
    });

    calendar.render();
  }
});