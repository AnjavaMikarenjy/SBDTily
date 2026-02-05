let myDonutChart = null;
let myBarChart = null;

function loadDashboard() {
    // Vérification de sécurité si membresData n'est pas encore chargé
    const data = typeof membresData !== 'undefined' ? membresData : [];

    const counts = {
        filoha: data.filter(m => m.type === "Filoha").length,
        tonia: data.filter(m => m.type === "Tonia").length,
        mpiandraikitra: data.filter(m => m.type === "Mpiandraikitra").length,
        beazina: data.filter(m => m.type === "Beazina").length,
        total: data.length
    };

    const content = document.getElementById("content");
    
    content.innerHTML = `
        <div class="dashboard-dark">
            <div class="kpi-grid four-cols">
                <div class="kpi-card purple"><h3>${counts.filoha}</h3><p>Filoha</p></div>
                <div class="kpi-card blue"><h3>${counts.tonia}</h3><p>Tonia</p></div>
                <div class="kpi-card green"><h3>${counts.mpiandraikitra}</h3><p>Mpiandraikitra</p></div>
                <div class="kpi-card orange"><h3>${counts.beazina}</h3><p>Beazina</p></div>
            </div>

            <div class="charts-row">
                <div class="chart-container">
                    <h4>Mpikambana</h4>
                    <canvas id="donutChart"></canvas>
                </div>
                <div class="chart-container">
                    <h4>Volume Comparatif</h4>
                    <canvas id="barChart"></canvas>
                </div>
            </div>
            
            </div>
    `;

    // Utilisation d'un seul déclencheur fiable pour le rendu
    setTimeout(() => {
        initDashboardCharts(counts);
    }, 150); // Un délai légèrement plus long pour laisser le temps au CSS de s'appliquer

}

function initDashboardCharts(data) {
    const elDonut = document.getElementById('donutChart');
    const elBar = document.getElementById('barChart');

    if (!elDonut || !elBar) return;

    // Récupération explicite du contexte 2D
    const ctxDonut = elDonut.getContext('2d');
    const ctxBar = elBar.getContext('2d');

    if (myDonutChart) myDonutChart.destroy();
    if (myBarChart) myBarChart.destroy();

    myDonutChart = new Chart(ctxDonut, {
        type: 'doughnut',
        data: {
            labels: ['Filoha', 'Tonia', 'Mpiandraikitra', 'Beazina'],
            datasets: [{
                data: [data.filoha, data.tonia, data.mpiandraikitra, data.beazina],
                backgroundColor: ['#7b1fa2', '#1976d2', '#388e3c', '#f57c00'],
                borderColor: '#1e1e1e',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 30, // Un peu d'espace pour ne pas coller au bord
                    top: 10,
                    bottom: 10
                }
            },
            plugins: {
                legend: {
                    position: 'right', // Place la légende à droite du graphique
                    align: 'center',    // Centre la liste verticalement
                    labels: {
                        color: '#ffffff', // Légende en blanc bien visible
                        font: {
                            size: 13,
                            weight: 'bold'
                        },
                        padding: 25,      // Espace vertical entre chaque ligne de la légende
                        usePointStyle: true, // Utilise des cercles au lieu de carrés
                        pointStyle: 'circle'
                    }
                }
            },
            cutout: '70%'
        }
    });

    // Configuration du graphique à Barres
    myBarChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Filoha', 'Tonia', 'Mpiandraikitra', 'Beazina'],
            datasets: [{
                label: 'Effectifs',
                data: [data.filoha, data.tonia, data.mpiandraikitra, data.beazina],
                backgroundColor: ['#7b1fa2', '#1976d2', '#388e3c', '#f57c00'],
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { 
                    beginAtZero: true, 
                    ticks: { 
                        color: '#ffffff', // Texte des chiffres en blanc pur
                        
                    }, 
                    grid: { 
                        color: 'rgba(255, 255, 255, 0.2)', // Lignes horizontales blanches semi-transparentes
                        lineWidth: 1
                    },
                    border: { color: '#ffffff', width: 1 } // Ligne de l'axe vertical
                },
                x: { 
                    ticks: { 
                        color: '#ffffff', // Texte des catégories en blanc pur
                        
                    }, 
                    grid: { 
                        display: false // On cache souvent les lignes verticales pour plus de clarté
                    },
                    border: { color: '#ffffff', width: 1 } // Ligne de l'axe horizontal
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}