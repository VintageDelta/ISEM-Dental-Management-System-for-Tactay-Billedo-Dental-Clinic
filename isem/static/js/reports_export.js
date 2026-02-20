function setExportFormat(format) {
    const btn = document.getElementById("exportBtn");
    const baseUrl = "{% url 'reports:export' %}";
    btn.href = `${baseUrl}?range={{ range_type }}&format=${format}`;

    // Close dropdown
    document.getElementById('exportDropdown').classList.add('hidden');
}

// pdf export
async function handlePdfExport(url) {
    const chartIds = ['appointmentChart', 'patientChart', 'revenueChart', 'inventoryChart'];
    const formData = new FormData();
    
    // Add CSRF token for the POST request
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    formData.append('csrfmiddlewaretoken', csrfToken);

    chartIds.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = id;
            // Convert Chart.js canvas to base64 PNG
            const base64Image = canvas.toDataURL('image/png');
            formData.append(id, base64Image);
        }
    });

    // Create a temporary form to submit the data
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    
    for (const [key, value] of formData.entries()) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}