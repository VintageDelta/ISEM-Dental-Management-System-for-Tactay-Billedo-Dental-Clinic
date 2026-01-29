document.addEventListener("DOMContentLoaded", () => {
  const popup = document.getElementById("modal-popup");
  if (!popup) return;
  const popupContent = document.getElementById("popup-content");
  const addBtn = document.getElementById("add-modal-btn");
  const closeBtn = document.querySelectorAll(".close-popup-btn");
  const addMedBtn = document.getElementById("add-medical-btn");
  const addFinBtn = document.getElementById("add-financial-btn");
  const addOdontogramBtn = document.getElementById("add-odontogram-btn");

  const medicalTab = document.getElementById("medicalTab");
  const financialTab = document.getElementById("financialTab");
  const odontogramTab = document.getElementById("odontogramTab");

  const medicalForm = document.getElementById("medicalForm");
  const financialForm = document.getElementById("financialForm");
  const odontogramForm = document.getElementById("odontogramForm");

  function showForm(type) {
    if (!medicalForm || !financialForm || !odontogramForm) return;
    if (type === "medical") {
      medicalForm.classList.remove("hidden");
      financialForm.classList.add("hidden");
      odontogramForm.classList.add("hidden");
    } else if (type === "financial") {
      financialForm.classList.remove("hidden");
      medicalForm.classList.add("hidden");
      odontogramForm.classList.add("hidden");
    } else if (type === "odontogram") {
      odontogramForm.classList.remove("hidden");
      medicalForm.classList.add("hidden");
      financialForm.classList.add("hidden");
    }
  }

  const openPopup = (url, type) => {
    if (!popup || !popupContent) return;
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
  if (addOdontogramBtn)
    addOdontogramBtn.addEventListener("click", () =>
      openPopup(odontogramUrl, "odontogram")
    );


  const closePopup = () => {
    if (!popup || !popupContent) return;
    popupContent.classList.remove("opacity-100", "scale-100");
    popupContent.classList.add("opacity-0", "scale-95");


    setTimeout(() => {
      popup.classList.remove("flex");
      popup.classList.add("hidden");
    }, 200);
  };

  // Loop through all close buttons and add event listener
  closeBtn.forEach(button => {
    button.addEventListener("click", closePopup);
  });

  // Optional: Close when clicking outside the modal
  popup.addEventListener("click", (e) => {
    if (e.target === popup) closePopup();
  });

  // closeBtn.addEventListener("click", closePopup);
  // popup.addEventListener("click", (e) => {
  //   if (e.target === popup) closePopup();
  // });
if (medicalTab && financialTab && odontogramTab) {
  medicalTab.addEventListener("click", () => {
    document.getElementById("medicalContent").classList.remove("hidden");
    document.getElementById("financialContent").classList.add("hidden");
    document.getElementById("odontogramContent").classList.add("hidden");
    addMedBtn.classList.remove("hidden");
    addFinBtn.classList.add("hidden");
    addOdontogramBtn.classList.add("hidden");
  });

  financialTab.addEventListener("click", () => {
    document.getElementById("financialContent").classList.remove("hidden");
    document.getElementById("medicalContent").classList.add("hidden");
    document.getElementById("odontogramContent").classList.add("hidden");
    addFinBtn.classList.remove("hidden");
    addMedBtn.classList.add("hidden");
    addOdontogramBtn.classList.add("hidden");
  });

  odontogramTab.addEventListener("click", () => {
    document.getElementById("odontogramContent").classList.remove("hidden");
    document.getElementById("medicalContent").classList.add("hidden");
    document.getElementById("financialContent").classList.add("hidden");
    addFinBtn.classList.add("hidden");
    addMedBtn.classList.add("hidden");
    addOdontogramBtn.classList.remove("hidden");
  });
}});