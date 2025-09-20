document.addEventListener("DOMContentLoaded", () => {
  const popup = document.getElementById("modal-popup");
  const popupContent = document.getElementById("popup-content");
  const addBtn = document.getElementById("add-modal-btn");
  const closeBtn = document.getElementById("close-popup-btn");
  const addMedBtn = document.getElementById("add-medical-btn");
  const addFinBtn = document.getElementById("add-financial-btn");
  const medicalTab = document.getElementById("medicalTab");
  const financialTab = document.getElementById("financialTab");
  const medicalForm = document.getElementById("medicalForm");
  const financialForm = document.getElementById("financialForm");

  function showForm(type) {
    if (!medicalForm || !financialForm) return;
    if (type === "medical") {
      medicalForm.classList.remove("hidden");
      financialForm.classList.add("hidden");
    } else if (type === "financial") {
      financialForm.classList.remove("hidden");
      medicalForm.classList.add("hidden");
    }
  }

  const openPopup = (url, type) => {
    if (type) showForm(type);
    popup.classList.remove("hidden");
    popup.classList.add("flex");


    requestAnimationFrame(() => {
      popupContent.classList.remove("opacity-0", "scale-95");
      popupContent.classList.add("opacity-100", "scale-100");
    });
  };

  if (addBtn) addBtn.addEventListener("click", openPopup);
  if (addMedBtn)
    addMedBtn.addEventListener("click", () => openPopup(medicalUrl, "medical"));
  if (addFinBtn)
    addFinBtn.addEventListener("click", () =>
      openPopup(financialUrl, "financial")
    );


  const closePopup = () => {
    popupContent.classList.remove("opacity-100", "scale-100");
    popupContent.classList.add("opacity-0", "scale-95");


    setTimeout(() => {
      popup.classList.remove("flex");
      popup.classList.add("hidden");
    }, 200);
  };


  closeBtn.addEventListener("click", closePopup);
  popup.addEventListener("click", (e) => {
    if (e.target === popup) closePopup();
  });

  medicalTab.addEventListener("click", () => {
    document.getElementById("medicalContent").classList.remove("hidden");
    document.getElementById("financialContent").classList.add("hidden");
    addMedBtn.classList.remove("hidden");
    addFinBtn.classList.add("hidden");
  });

  financialTab.addEventListener("click", () => {
    document.getElementById("financialContent").classList.remove("hidden");
    document.getElementById("medicalContent").classList.add("hidden");
    addFinBtn.classList.remove("hidden");
    addMedBtn.classList.add("hidden");
  });
});