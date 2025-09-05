document.addEventListener('DOMContentLoaded', function () {
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
  // ==== DELETE BUTTON ====
  const deleteModal = document.getElementById("delete-modal");
  const deleteContent = document.getElementById("delete-modal-content");
  const cancelDelete = document.getElementById("cancel-delete");
  const confirmDelete = document.getElementById("confirm-delete");
  let patientToDelete = null;

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      patientToDelete = btn.dataset.id;
      openModal(deleteModal, deleteContent);
    });
  });

  cancelDelete.addEventListener("click", () => closeModal(deleteModal, deleteContent));
  deleteModal.addEventListener("click", (e) => {
    if (e.target === deleteModal) closeModal(deleteModal, deleteContent);
  });

  confirmDelete.addEventListener("click", () => {
  console.log("Delete patient ID:", patientToDelete);

  // Send delete request to Django
fetch(`/dashboard/patient/delete/${patientToDelete}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
}).then((response) => {
    if (response.ok) {
      window.location.reload(); // reload to update table
    } else {
      console.error("Delete failed");
    }
    });       
});
  // ==== EDIT BUTTON ====
  const editModal = document.getElementById("edit-modal");
  const editContent = document.getElementById("edit-modal-content");
  const cancelEdit = document.getElementById("cancel-edit");

  document.querySelectorAll(".uil-edit").forEach((icon) => {
    icon.parentElement.addEventListener("click", (e) => {
      e.preventDefault();

      const btn = icon.parentElement;

      // Fill edit form
      document.getElementById("edit-id").value = btn.dataset.id;
      document.getElementById("edit-name").value = btn.closest("tr").children[1].innerText;
      document.getElementById("edit-address").value = btn.closest("tr").children[2].innerText;
      document.getElementById("edit-telephone").value = btn.closest("tr").children[3].innerText;
      document.getElementById("edit-age").value = btn.closest("tr").children[4].innerText;
      document.getElementById("edit-occupation").value = btn.closest("tr").children[5].innerText;
      document.getElementById("edit-status").value = btn.closest("tr").children[6].innerText;
      document.getElementById("edit-complaint").value = btn.closest("tr").children[7].innerText;

      openModal(editModal, editContent);
    });
  });

  cancelEdit.addEventListener("click", () => closeModal(editModal, editContent));
  editModal.addEventListener("click", (e) => {
    if (e.target === editModal) closeModal(editModal, editContent);
  });
});

// ===== Helpers =====
function openModal(modal, content) {
  modal.classList.remove("hidden");
  modal.classList.add("flex");
  requestAnimationFrame(() => {
    content.classList.remove("opacity-0", "scale-95");
    content.classList.add("opacity-100", "scale-100");
  });
}

function closeModal(modal, content) {
  content.classList.remove("opacity-100", "scale-100");
  content.classList.add("opacity-0", "scale-95");
  setTimeout(() => {
    modal.classList.remove("flex");
    modal.classList.add("hidden");
  }, 200);
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}