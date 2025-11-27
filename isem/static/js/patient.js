document.addEventListener("DOMContentLoaded", function () {
  const searchBar = document.getElementById("search-bar");
  const tableBody = document.getElementById("patient-table-body");

  if (searchBar && tableBody) {
    // Search filter
    searchBar.addEventListener("keyup", () => {
      const query = searchBar.value.toLowerCase();
      const rows = tableBody.getElementsByTagName("tr");

      Array.from(rows).forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  }

  // ==== DELETE BUTTON ====
  const deleteModal = document.getElementById("delete-modal");
  const deleteContent = document.getElementById("delete-modal-content");
  const cancelDelete = document.getElementById("cancel-delete");
  const confirmDelete = document.getElementById("confirm-delete");
  let patientToDelete = null;

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      patientToDelete = btn.dataset.id;
      openModal(deleteModal, deleteContent);
    });
  });

  if (cancelDelete) {
    cancelDelete.addEventListener("click", () =>
      closeModal(deleteModal, deleteContent)
    );
  }

  if (deleteModal) {
    deleteModal.addEventListener("click", (e) => {
      if (e.target === deleteModal) closeModal(deleteModal, deleteContent);
    });
  }

  if (confirmDelete) {
    confirmDelete.addEventListener("click", () => {
      console.log("Delete patient ID:", patientToDelete);

      fetch(`/dashboard/patient/delete/${patientToDelete}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      }).then((response) => {
        if (response.ok) {
          window.location.reload();
        } else {
          console.error("Delete failed");
        }
      });
    });
  }

  // ==== CHOOSE TYPE MODAL ====
  const chooseModal = document.getElementById("choose-type-modal");
  const chooseContent = document.getElementById("choose-type-content");
  const addModalBtn = document.getElementById("add-modal-btn");
  const popupModal = document.getElementById("modal-popup");
  const popupContent = document.getElementById("popup-content");
  //const cancelChoose = document.getElementById("cancel-choose");
  //const btnRegistered = document.getElementById("choose-registered");
  const btnGuest = document.getElementById("choose-guest");
  const closeBtn = document.getElementById("close-popup-btn");

  if (addModalBtn) {
    addModalBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      closeAllModals();
      openModal(popupModal, popupContent);
    });
  }

  // if (btnRegistered) {
  //   btnRegistered.addEventListener("click", () => {
  //     closeModal(chooseModal, chooseContent);
  //     setTimeout(() => openModal(popupModal, popupContent), 250);
  //   });
  // }

  // if (btnGuest) {
  //   btnGuest.addEventListener("click", () => {
  //     closeModal(chooseModal, chooseContent);
  //     setTimeout(() => openModal(popupModal, popupContent), 250);
  //   });
  // }

  // if (cancelChoose) {
  //   cancelChoose.addEventListener("click", () =>
  //     closeModal(chooseModal, chooseContent)
  //   );
  // }

  // ==== EDIT BUTTON ====
  const editModal = document.getElementById("edit-modal");
  const editContent = document.getElementById("edit-modal-content");
  const cancelEdit = document.getElementById("cancel-edit");

  document.querySelectorAll(".uil-edit").forEach((icon) => {
    icon.parentElement.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const btn = icon.parentElement;

      closeAllModals();

      document.getElementById("edit-id").value = btn.dataset.id;
      document.getElementById("edit-name").value =
        btn.closest("tr").children[2].innerText;
      document.getElementById("edit-email").value =
        btn.closest("tr").children[3].innerText;
      document.getElementById("edit-address").value =
        btn.closest("tr").children[4].innerText;
      document.getElementById("edit-telephone").value =
        btn.closest("tr").children[5].innerText;
      document.getElementById("edit-age").value =
        btn.closest("tr").children[6].innerText;
      document.getElementById("edit-occupation").value =
        btn.closest("tr").children[7].innerText;

      openModal(editModal, editContent);
    });
  });

  if (cancelEdit) {
    cancelEdit.addEventListener("click", () =>
      closeModal(editModal, editContent)
    );
  }

  if (editModal) {
    editModal.addEventListener("click", (e) => {
      if (e.target === editModal) closeModal(editModal, editContent);
    });
  }

  // ===== Helper Functions =====
  function openModal(modal, content) {
    if (!modal || !content) return;
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    requestAnimationFrame(() => {
      content.classList.remove("opacity-0", "scale-95");
      content.classList.add("opacity-100", "scale-100");
    });
  }

  function closeModal(modal, content) {
    if (!modal || !content) return;
    content.classList.remove("opacity-100", "scale-100");
    content.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      modal.classList.remove("flex");
      modal.classList.add("hidden");
    }, 200);
  }

  function closeAllModals() {
    const allModals = [
      { modal: deleteModal, content: deleteContent },
      { modal: chooseModal, content: chooseContent },
      { modal: popupModal, content: popupContent },
      { modal: editModal, content: editContent },
    ];
    allModals.forEach(({ modal, content }) => {
      if (modal && content && modal.classList.contains("flex")) {
        closeModal(modal, content);
      }
    });
  }

  // ==== CLOSE POPUP ====
  const closePopup = () => {
    popupContent.classList.remove("opacity-100", "scale-100");
    popupContent.classList.add("opacity-0", "scale-95");
    setTimeout(() => {
      popupModal.classList.remove("flex");
      popupModal.classList.add("hidden");
    }, 200);
  };

  if (closeBtn) {
    closeBtn.addEventListener("click", closePopup);
  }
  popupModal.addEventListener("click", (e) => {
    if (e.target === popupModal) closePopup();
  });

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
});
