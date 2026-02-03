document.addEventListener("DOMContentLoaded", function () {
  function applyStatusModalMobileStyles() {
    const isMobile = window.innerWidth < 768;
    const statusModal = document.getElementById("status-modal");
    if (!statusModal) return;
    const content = statusModal.querySelector(".modal-content");
    if (!content) return;

    if (isMobile) {
      content.style.maxWidth = "20rem";
      content.style.transform = "scale(0.9)";
    } else {
      content.style.maxWidth = "";
      content.style.transform = "";
    }

    const header = content.querySelector(".bg-slate-800");
    if (header) header.style.padding = isMobile ? "0.5rem 0.75rem" : "";

    const title = content.querySelector("h2");
    if (title) title.style.fontSize = isMobile ? "0.9rem" : "";

    const desc = content.querySelector("p");
    if (desc) desc.style.fontSize = isMobile ? "0.68rem" : "";

    const body = content.querySelector(".px-4.py-4");
    if (body) body.style.padding = isMobile ? "0.75rem" : "";

    const statusButtons = statusModal.querySelectorAll(".grid button");
    statusButtons.forEach(btn => {
      if (isMobile) {
        btn.style.padding = "0.35rem 0.5rem";
        btn.style.fontSize = "0.68rem";
      } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
      }
    });

    const cancelBtn = document.getElementById("status-cancel-btn");
    const closeBtn = document.getElementById("close-status-btn");
    [cancelBtn, closeBtn].forEach(btn => {
      if (!btn) return;
      if (isMobile) {
        btn.style.padding = "0.4rem 0.75rem";
        btn.style.fontSize = "0.75rem";
      } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
      }
    });
  }

  function applyFollowupModalMobileStyles() {
    const isMobile = window.innerWidth < 768;
    const followupModal = document.getElementById("followup-modal");
    if (!followupModal) return;
    const content = followupModal.querySelector(".modal-content");
    if (!content) return;

    if (isMobile) {
      content.style.maxWidth = "20rem";
      content.style.transform = "scale(0.9)";
      content.style.padding = "0.75rem 0.9rem";
    } else {
      content.style.maxWidth = "";
      content.style.transform = "";
      content.style.padding = "";
    }

    const title = content.querySelector("h2");
    if (title) {
      title.style.fontSize = isMobile ? "1rem" : "";
      title.style.marginBottom = isMobile ? "0.5rem" : "";
    }

    const labels = followupModal.querySelectorAll("label, .text-sm.font-medium");
    labels.forEach(lab => {
      lab.style.fontSize = isMobile ? "0.8rem" : "";
    });

    const selects = followupModal.querySelectorAll("select, input[type='date']");
    selects.forEach(sel => {
      if (isMobile) {
        sel.style.padding = "0.35rem 0.5rem";
        sel.style.fontSize = "0.75rem";
      } else {
        sel.style.padding = "";
        sel.style.fontSize = "";
      }
    });

    const closeBtn = document.getElementById("close-followup-btn");
    const saveBtn = followupModal.querySelector("button[type='submit']");
    [closeBtn, saveBtn].forEach(btn => {
      if (!btn) return;
      if (isMobile) {
        btn.style.padding = "0.4rem 0.75rem";
        btn.style.fontSize = "0.75rem";
      } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
      }
    });
  }

    function applyRescheduleModalMobileStyles() {
    const isMobile = window.innerWidth < 768;
    const reschedModal = document.getElementById("reschedule-modal");
    if (!reschedModal) return;
    const content = reschedModal.querySelector(".modal-content");
    if (!content) return;

    if (isMobile) {
        content.style.maxWidth = "20rem";
        content.style.transform = "scale(0.9)";
        content.style.padding = "0.75rem 0.9rem";

        // allow scrolling inside the reschedule box
        content.style.maxHeight = "90vh";
        content.style.overflowY = "auto";
    } else {
        content.style.maxWidth = "";
        content.style.transform = "";
        content.style.padding = "";
        content.style.maxHeight = "";
        content.style.overflowY = "";
    }

    const title = content.querySelector("h2");
    if (title) {
        title.style.fontSize = isMobile ? "1rem" : "";
        title.style.marginBottom = isMobile ? "0.5rem" : "";
    }

    const selects = reschedModal.querySelectorAll("select, input[type='date'], input[type='email']");
    selects.forEach(sel => {
        if (isMobile) {
        sel.style.padding = "0.35rem 0.5rem";
        sel.style.fontSize = "0.75rem";
        } else {
        sel.style.padding = "";
        sel.style.fontSize = "";
        }
    });

    const labels = reschedModal.querySelectorAll("label, p, .font-semibold");
    labels.forEach(lab => {
        lab.style.fontSize = isMobile ? "0.8rem" : "";
    });

    const cancelBtn = document.getElementById("close-reschedule-btn");
    const saveBtn = reschedModal.querySelector("button[type='submit']");
    [cancelBtn, saveBtn].forEach(btn => {
        if (!btn) return;
        if (isMobile) {
        btn.style.padding = "0.4rem 0.75rem";
        btn.style.fontSize = "0.75rem";
        } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
        }
    });
    }


function applyDoneStepsModalMobileStyles() {
  const isMobile = window.innerWidth < 768;
  const doneModal = document.getElementById("done-steps-modal");
  if (!doneModal) return;
  const content = doneModal.querySelector(".modal-content");
  if (!content) return;

  // main container
  if (isMobile) {
    content.style.maxWidth = "100%";
    content.style.transform = "scale(0.9)";
    content.style.maxHeight = "90vh";

    // prevent double scroll: let inner flex section scroll, outer no extra overflow
    content.style.overflow = "hidden";
  } else {
    content.style.maxWidth = "";
    content.style.transform = "";
    content.style.maxHeight = "";
    content.style.overflow = "";
  }

  // header
  const header = content.querySelector("div.border-b");
  if (header) {
    header.style.padding = isMobile ? "0.75rem 0.9rem" : "";
  }

  const title = header ? header.querySelector("h2") : null;
  if (title) {
    title.style.fontSize = isMobile ? "1rem" : "";
    title.style.marginBottom = isMobile ? "0.25rem" : "";
  }

  const subtitle = header ? header.querySelector("p") : null;
  if (subtitle) {
    subtitle.style.fontSize = isMobile ? "0.75rem" : "";
  }

  // left steps column padding / text
  const stepsCol = doneModal.querySelector("div.w-full.md\\:w-64");
  if (stepsCol) {
    stepsCol.style.padding = isMobile ? "0.5rem" : "";
    // on mobile, avoid its own scroll to reduce double scrolling feeling
    stepsCol.style.maxHeight = isMobile ? "none" : "";
    stepsCol.style.overflowY = isMobile ? "visible" : "";
  }

  // step cards + circles
  const stepCards = doneModal.querySelectorAll(".step-container");
  stepCards.forEach(card => {
    if (isMobile) {
      card.style.padding = "0.4rem 0.5rem";
      card.style.gap = "0.4rem";
    } else {
      card.style.padding = "";
      card.style.gap = "";
    }
  });

  const stepCircles = doneModal.querySelectorAll(".step-circle");
  stepCircles.forEach(circle => {
    if (isMobile) {
      circle.style.width = "2rem";   // smaller than w-10 (2.5rem)
      circle.style.height = "2rem";
    } else {
      circle.style.width = "";
      circle.style.height = "";
    }
  });

  const stepTexts = stepsCol ? stepsCol.querySelectorAll("p") : [];
  stepTexts.forEach(p => {
    p.style.fontSize = isMobile ? "0.78rem" : "";
  });

  // right forms padding and inputs
  const formsCol = doneModal.querySelector("div.flex-1.overflow-y-auto");
  if (formsCol) {
    formsCol.style.padding = isMobile ? "0.75rem" : "";
    // let this be the only scrolling area inside the modal
    formsCol.style.maxHeight = isMobile ? "calc(90vh - 120px)" : "";
  }

  const inputs = doneModal.querySelectorAll("input, select");
  inputs.forEach(el => {
    if (isMobile) {
      el.style.padding = "0.35rem 0.5rem";
      el.style.fontSize = "0.75rem";
    } else {
      el.style.padding = "";
      el.style.fontSize = "";
    }
  });

  const labels = doneModal.querySelectorAll("label, .font-semibold, .text-sm, .text-xs");
  labels.forEach(lab => {
    if (isMobile) {
      lab.style.fontSize = "0.78rem";
    } else {
      lab.style.fontSize = "";
    }
  });

  // footer buttons
  const footer = doneModal.querySelector("div.border-t");
  if (footer) {
    footer.style.padding = isMobile ? "0.6rem 0.9rem" : "";
  }

  const footerBtns = footer ? footer.querySelectorAll("button") : [];
  footerBtns.forEach(btn => {
    if (isMobile) {
      btn.style.padding = "0.4rem 0.8rem";
      btn.style.fontSize = "0.78rem";
    } else {
      btn.style.padding = "";
      btn.style.fontSize = "";
    }
  });
}


  function applyAppointmentModalMobileStyles() {
    const isMobile = window.innerWidth < 768;
    const appModal = document.getElementById("appointment-modal");
    if (!appModal) return;

    const content = document.getElementById("appointment-modal-content");
    if (!content) return;

    if (isMobile) {
      content.style.maxWidth = "20rem";          // narrower on mobile
      content.style.transform = "scale(0.9)";    // slightly smaller
      content.style.padding = "0.75rem 0.9rem";
    } else {
      content.style.maxWidth = "";
      content.style.transform = "";
      content.style.padding = "";
    }

    // Title
    const title = content.querySelector("h2");
    if (title) {
      title.style.fontSize = isMobile ? "1rem" : "";
      title.style.marginBottom = isMobile ? "0.5rem" : "";
    }

    // Inputs/selects
    const fields = appModal.querySelectorAll("select, input[type='date'], input[type='email']");
    fields.forEach(el => {
      if (isMobile) {
        el.style.padding = "0.35rem 0.5rem";
        el.style.fontSize = "0.75rem";
      } else {
        el.style.padding = "";
        el.style.fontSize = "";
      }
    });

    // Labels/section titles
    const labels = appModal.querySelectorAll("label, .font-semibold, .text-sm");
    labels.forEach(lab => {
      if (isMobile) {
        lab.style.fontSize = "0.8rem";
      } else {
        lab.style.fontSize = "";
      }
    });

    // Footer buttons
    const cancelBtn = document.getElementById("close-appointment-btn");
    const saveBtn = appModal.querySelector("button[type='submit']");
    [cancelBtn, saveBtn].forEach(btn => {
      if (!btn) return;
      if (isMobile) {
        btn.style.padding = "0.4rem 0.75rem";
        btn.style.fontSize = "0.75rem";
      } else {
        btn.style.padding = "";
        btn.style.fontSize = "";
      }
    });
  }

  function applyAllModalMobileStyles() {
    applyStatusModalMobileStyles();
    applyFollowupModalMobileStyles();
    applyRescheduleModalMobileStyles();
    applyDoneStepsModalMobileStyles();
    applyAppointmentModalMobileStyles();
  }

  applyAllModalMobileStyles();
  window.addEventListener("resize", applyAllModalMobileStyles);
});
