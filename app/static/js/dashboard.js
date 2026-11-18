/**
 * MESSMIND - Simple Daily Mess Meal Logging Portal
 * Summary Chart: dashboard.js
 */

document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("consumptionChart");
    if (!ctx) return;

    fetch("/api/chart-data")
        .then((response) => response.json())
        .then((data) => {
            if (!data || !data.dates || data.dates.length === 0) {
                const parent = ctx.parentElement;
                if (parent) {
                    parent.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px 0;">No completed meal records available yet to display.</div>';
                }
                return;
            }

            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: "Meals prepared",
                            data: data.prepared,
                            backgroundColor: "rgba(2, 136, 209, 0.75)",
                            borderColor: "#0288d1",
                            borderWidth: 1,
                            borderRadius: 4,
                        },
                        {
                            label: "Meals served",
                            data: data.consumed || data.served,
                            backgroundColor: "rgba(46, 125, 50, 0.85)",
                            borderColor: "#2e7d32",
                            borderWidth: 1,
                            borderRadius: 4,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "top",
                            labels: {
                                font: { size: 13, weight: "bold" },
                                padding: 16
                            },
                        },
                        tooltip: {
                            callbacks: {
                                afterLabel: function (context) {
                                    const index = context.dataIndex;
                                    const prep = data.prepared[index];
                                    const served = (data.consumed || data.served)[index];
                                    const leftover = prep - served;
                                    return `Meals left over: ${leftover} portions (${data.waste_percentages[index]}%)`;
                                },
                            },
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: "#f1f5f9" },
                            title: {
                                display: true,
                                text: "Number of Portions / Plates",
                                font: { size: 12 }
                            },
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 11 } }
                        },
                    },
                },
            });
        })
        .catch((error) => {
            console.error("Could not load summary chart:", error);
        });
});
