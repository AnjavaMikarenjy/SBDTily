let backend = null;

/** Chargement de tout les styles css */
function loadCSS(file) {
    // supprimer ancien css de page
    document.querySelectorAll("link[data-page]").forEach(link => link.remove());

    // ajouter nouveau css
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `css/${file}`;
    link.setAttribute("data-page", "true");

    document.head.appendChild(link);
}



/**Navigation  **/
function navigate(page, btn = null) {

    document.getElementById("page-title").innerText =
        page.charAt(0).toUpperCase() + page.slice(1);

    // gestion bouton actif
    document.querySelectorAll("#sidebar button").forEach(b =>
        b.classList.remove("active")
    );

    if (btn) {
        btn.classList.add("active");
    }

    switch (page) {
        case "dashboard":
            loadCSS("dashboard.css");
            loadDashboard();
            break;

        case "membres":
            loadCSS("membres.css");
            loadMembres();
            break;

        case "analyse":
            loadCSS("analyse.css");
            loadAnalyse();
            break;

        case "parametres":
            loadCSS("parametres.css");
            loadParametres();
            break;
    }
}


/**Chargement de tableau de bord au demarage **/
window.onload = () => {
    const dashboardBtn = document.querySelector(
        "#sidebar button"
    );
    navigate("dashboard", dashboardBtn);
};

// Variable globale pour stocker les membres
// Variable globale pour stocker les membres
let allMembres = [];

new QWebChannel(qt.webChannelTransport, function (channel) {
    window.backend = channel.objects.backend;
    
    // ACTION : On charge les données IMMÉDIATEMENT au démarrage
    initApp();
});

function initApp() {
    window.backend.charger_membres(function(data) {
        allMembres = data;
        filteredMembres = data;
        
        // Si vous avez une fonction pour mettre à jour les chiffres du Dashboard
        updateDashboard(data); 
        
        // Si vous êtes sur la page des membres, on affiche
        if (typeof renderMembresDisplay === "function") {
            renderMembresDisplay();
        }
    });
}

function updateDashboard(data) {
    const totalElement = document.getElementById("total-membres");
    if (totalElement) {
        totalElement.innerText = data.length;
    }
    
    // Exemple : Compter les Mpiandraikitra
    const mpiandraikitraCount = data.filter(m => m.type === 'Mpiandraikitra').length;
    const mpiandraikitraElement = document.getElementById("count-mpiandraikitra");
    if (mpiandraikitraElement) {
        mpiandraikitraElement.innerText = mpiandraikitraCount;
    }
}

