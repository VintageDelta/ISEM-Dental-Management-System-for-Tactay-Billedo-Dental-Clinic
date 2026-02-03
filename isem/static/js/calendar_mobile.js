document.addEventListener("DOMContentLoaded", function () {
  function applyTimelineMobileStyles() {
    const isMobile = window.innerWidth < 768;
    const timeline = document.getElementById("timeline-calendar");
    const mainCal = document.getElementById("calendar");

    // ---------- MAIN CALENDAR TOOLBAR ----------
    if (mainCal) {
      // target buttons inside toolbar chunks (prev/next/today etc.)
      const mainButtons = mainCal.querySelectorAll(
        ".fc-toolbar-chunk .fc-button"
      );
      mainButtons.forEach(btn => {
        if (isMobile) {
          btn.style.padding = "2px 4px";
          btn.style.fontSize = "0.65rem";
        } else {
          btn.style.padding = "";
          btn.style.fontSize = "";
        }
      });

      const mainTitle = mainCal.querySelector(".fc-toolbar-title");
      if (mainTitle) {
        mainTitle.style.fontSize = isMobile ? "0.8rem" : "";
      }
    }

    // ---------- TIMELINE CALENDAR ----------
    if (!timeline) return;

    // 1) Time label cells (8am, 9am, ...)
    const labelEls = timeline.querySelectorAll(".fc-timegrid-slot-label");
    labelEls.forEach(el => {
      if (isMobile) {
        el.style.fontSize = "0.65rem";
        el.style.padding = "0 2px";
      } else {
        el.style.fontSize = "";
        el.style.padding = "";
      }
    });

    // 2) Time slot rows (height)
    const slotEls = timeline.querySelectorAll(".fc-timegrid-slot");
    slotEls.forEach(el => {
      if (isMobile) {
        el.style.height = "1.5rem";
      } else {
        el.style.height = "";
      }
    });

    // 3) Timeline toolbar buttons
    const toolbarButtons = timeline.querySelectorAll(
      ".fc-toolbar-chunk .fc-button"
    );
    toolbarButtons.forEach(btn => {
      if (isMobile) {
        btn.style.padding = "2px 4px";
        btn.style.fontSize = "0.65rem";
      } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
      }
    });

    const tlTitle = timeline.querySelector(".fc-toolbar-title");
    if (tlTitle) {
      tlTitle.style.fontSize = isMobile ? "0.8rem" : "";
    }

    // 4) Timeline event cards and buttons
    const eventCards = timeline.querySelectorAll(".fc-timegrid-event div");
    eventCards.forEach(card => {
      if (isMobile) {
        card.style.padding = "4px 6px";
      } else {
        card.style.padding = "";
      }
    });

    const titleEls = timeline.querySelectorAll(".fc-timegrid-event div > div:first-child");
    titleEls.forEach(el => {
      if (isMobile) {
        el.style.fontSize = "0.7rem";
      } else {
        el.style.fontSize = "";
      }
    });

    const followBtns = timeline.querySelectorAll("button");
    followBtns.forEach(btn => {
      const label = btn.textContent.trim();
      if (label === "Follow up" || label === "Reschedule") {
        if (isMobile) {
          btn.style.padding = "2px 4px";
          btn.style.fontSize = "0.6rem";
        } else {
          btn.style.padding = "";
          btn.style.fontSize = "";
        }
      }
    });

    // 5) Status legend under the timeline
    const legend = timeline.closest(".bg-white")?.querySelector(
      ".flex.flex-wrap.items-center.justify-center.gap-4"
    );
    if (legend) {
      const legendItems = legend.querySelectorAll("span");
      legendItems.forEach(span => {
        if (isMobile) {
          span.style.fontSize = "0.7rem";
          span.style.gap = "0.25rem";
        } else {
          span.style.fontSize = "";
          span.style.gap = "";
        }
      });

      const dots = legend.querySelectorAll("span > span");
      dots.forEach(dot => {
        if (isMobile) {
          dot.style.width = "0.5rem";
          dot.style.height = "0.5rem";
        } else {
          dot.style.width = "";
          dot.style.height = "";
        }
      });
    }
  }

  // Run once after DOM is ready (calendars are created in calendar.js)
  applyTimelineMobileStyles();

  // Re-apply on resize
  window.addEventListener("resize", applyTimelineMobileStyles);

  // Also re-apply whenever FullCalendar changes view/dates
  if (window.timelineCalendar) {
    window.timelineCalendar.on("datesSet", applyTimelineMobileStyles);
    window.timelineCalendar.on("viewDidMount", applyTimelineMobileStyles);
  }
  if (window.mainCalendar) {
    window.mainCalendar.on("datesSet", applyTimelineMobileStyles);
  }
});
