document.addEventListener("DOMContentLoaded", () => {
  const popup = document.getElementById("modal-popup");
  const popupContent = document.getElementById("popup-content");
  const addBtn = document.getElementById("add-modal-btn");
  const closeBtn = document.getElementById("close-popup-btn");

  // Open popup
  addBtn.addEventListener("click", () => {
    popup.classList.remove("hidden");
    popup.classList.add("flex");

    // Allow rendering before transition
    requestAnimationFrame(() => {
      popupContent.classList.remove("opacity-0", "scale-95");
      popupContent.classList.add("opacity-100", "scale-100");
    });
  });

  // Close popup function
  const closePopup = () => {
    popupContent.classList.remove("opacity-100", "scale-100");
    popupContent.classList.add("opacity-0", "scale-95");

    // Wait for animation to finish before hiding backdrop
    setTimeout(() => {
      popup.classList.remove("flex");
      popup.classList.add("hidden");
    }, 200); // duration matches Tailwind's `duration-200`
  };

  // Close popup (button & outside click)
  closeBtn.addEventListener("click", closePopup);
  popup.addEventListener("click", (e) => {
    if (e.target === popup) closePopup();
  });
});
