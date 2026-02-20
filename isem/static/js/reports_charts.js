// Function to helper to get data from element
function getChartData(id) {
    const el = document.getElementById(id);
    return {
        labels: JSON.parse(el.getAttribute('data-labels')),
        values: JSON.parse(el.getAttribute('data-values'))
    };
}

// Initialize Appointment Chart
const appt = getChartData("appointmentChart");
createLineChart("appointmentChart", appt.labels, appt.values, "Appointments", "#10b981");

// Initialize Patient Chart
const pat = getChartData("patientChart");
createLineChart("patientChart", pat.labels, pat.values, "New Patients", "#6366f1");

// Initialize Revenue Chart
const rev = getChartData("revenueChart");
createLineChart("revenueChart", rev.labels, rev.values, "Revenue", "#2563eb");

// Initialize Inventory (Bar) Chart
const inv = getChartData("inventoryChart");
createBarChart("inventoryChart", inv.labels, inv.values, "Items");

function createLineChart(id, labels, data, label, color) {
    new Chart(document.getElementById(id), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + "33",
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function createBarChart(id, labels, data, label) {
    new Chart(document.getElementById(id), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}