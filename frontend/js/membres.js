/// ---------------------------
// VARIABLES GLOBALES
// ---------------------------
let membresData = [];
let filteredMembres = [];
let currentView = "cards"; 
let selectedType = "Tous"; 
let currentOpenIndex = null;

// ---------------------------
// CHARGEMENT DEPUIS SQLITE
// ---------------------------
function loadMembresFromDB() {
    if (window.backend) {
        window.backend.charger_membres((data) => {
            membresData = data;
            searchMembres(document.querySelector(".combo-input")?.value || ""); 
        });
    }
}
// ---------------------------
// CHARGEMENT DE LA PAGE
// ---------------------------
function loadMembres() {
    const content = document.getElementById("content");
    if (!content) return;

    content.innerHTML = `
    <div class="membres-page">
        <div id="membres-view">    
            <div class="membres-header">
                <div class="search-combo">
                    <div class="combo-type" onclick="toggleTypeList()">
                        <span id="currentType">${selectedType}</span>
                        <i class="fa-solid fa-chevron-down"></i>
                    </div>
                    <input type="text" class="combo-input" placeholder="Rechercher un membre..." onkeyup="searchMembres(this.value)">
                    <div class="combo-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
                    
                    <div class="type-dropdown" id="typeDropdown">
                        <div onclick="selectType('Tous')">Tous</div>
                        <div onclick="selectType('Filoha')">Filoha</div>
                        <div onclick="selectType('Tonia')">Tonia</div>
                        <div onclick="selectType('Mpiandraikitra')">Mpiandraikitra</div>
                        <div onclick="selectType('Beazina')">Beazina</div>
                    </div>
                </div>

                <div class="header-buttons">
                    <button class="btn-primary" onclick="showMemberForm()">
                        <i class="fa-solid fa-user-plus"></i> Ajouter
                    </button>
                    <select id="view-select" class="view-select">
                        <option value="cards" ${currentView === 'cards' ? 'selected' : ''}>Cartes</option>
                        <option value="table" ${currentView === 'table' ? 'selected' : ''}>Tableau</option>
                    </select>
                </div>
            </div>

            <div id="membres-display"></div>
        </div>
        <div id="cv-view" class="hidden"></div>
    </div>
    `;

    document.getElementById("view-select").onchange = function() {
        currentView = this.value;
        renderMembresDisplay();
    };

    renderMembresDisplay();
}

// ---------------------------
// FILTRAGE ET RECHERCHE
// ---------------------------
function toggleTypeList() {
    const dropdown = document.getElementById("typeDropdown");
    dropdown.style.display = (dropdown.style.display === "block") ? "none" : "block";
}

function selectType(type) {
    selectedType = type;
    document.getElementById("currentType").innerText = type;
    document.getElementById("typeDropdown").style.display = "none";
    searchMembres(document.querySelector(".combo-input").value);
}

function searchMembres(query) {
    const q = query.toLowerCase();
    filteredMembres = membresData.filter(m => {
        // Correction : utiliser les champs exacts de la DB
        const nom = (m.nom || "").toLowerCase();
        const prenom = (m.prenom || "").toLowerCase();
        const matchesText = nom.includes(q) || prenom.includes(q);
        const matchesType = (selectedType === "Tous" || m.type === selectedType);
        return matchesText && matchesType;
    });
    renderMembresDisplay();
}
// ---------------------------
// RENDU DES CARTES (MODERNES)
// ---------------------------
function renderMembresDisplay() {
    const container = document.getElementById("membres-display");
    
    if (!container) return;

    if (filteredMembres.length === 0) {
        container.innerHTML = `<div class="no-result">Aucun membre trouvé</div>`;
        return;
    }

    if (currentView === "cards") {
        container.innerHTML = `<div class="cards-container">
            ${filteredMembres.map((m, index) => {
                // Si m.photo est "uploads/img_xxx.jpg", on s'assure qu'il est bien lu
                // On ajoute un ?t=... pour éviter les problèmes de cache
                const imageSrc = m.photo ? `../${m.photo}` : "";
                
                return `
                <div class="modern-card">
                    <div class="shape-top"></div>
                    <div class="shape-bottom"></div>
                    
                    <button class="modern-btn-cv" onclick="openCV(${index})">
                        <i class="fa-solid fa-id-card"></i> CV
                    </button>

                    <div class="modern-card-content">
                        <div class="modern-photo-wrapper">
                            <div class="photo-circle">
                                ${m.photo 
                                    ? `<img src="${imageSrc}" 
                                            style="width:100%; height:100%; object-fit:cover;" 
                                            onerror="this.src='../assets/default-user.png'; this.onerror=null;">` 
                                    : `<i class="fa-solid fa-user"></i>`
                                }
                            </div>
                        </div>
                        <div class="modern-info">
                            <h3 class="member-name">${m.nom} ${m.prenom}</h3>
                            <p class="member-title">${m.type || 'Membre'}</p>
                            
                            <div class="details-list">
                                <div class="detail-item">
                                    <i class="fa-solid fa-phone"></i>
                                    <span>${m.telephone || 'Non renseigné'}</span>
                                </div>
                                <div class="detail-item">
                                    <i class="fa-solid fa-layer-group"></i>
                                    <span>${m.sampana || '---'}</span>
                                </div>
                                <div class="detail-item">
                                    <i class="fa-solid fa-location-dot"></i>
                                    <span>${m.nom_faritra || 'DIANA'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-actions-footer" style="display: flex; justify-content: space-around; padding: 10px; border-top: 1px solid #eee;">
                         <button onclick="editMembre(${index})" style="border:none; background:none; color:#007bff; cursor:pointer; font-weight:bold;">
                            <i class="fa-solid fa-pen"></i> Modifier
                         </button>
                    </div>
                </div>
            `}).join("")}
        </div>`;
    } else {
        renderTable(container);
    }
}

// ---------------------------
// RENDU DU TABLEAU
// ---------------------------
function renderTable(container) {
    container.innerHTML = `
        <div class="table-container">
            <table class="membres-table">
                <thead>
                    <tr>
                        <th>Photo</th>
                        <th onclick="sortTable('nom')">Nom <i class="fa-solid fa-sort"></i></th>
                        <th onclick="sortTable('prenom')">Prénom <i class="fa-solid fa-sort"></i></th>
                        <th>Téléphone</th>
                        <th>Type</th>
                        <th class="no-print">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredMembres.map((m, index) => `
                        <tr>
                            <td>
                                <div class="table-photo">
                                    ${m.photo ? `<img src="${m.photo}">` : `<i class="fa-solid fa-user"></i>`}
                                </div>
                            </td>
                            <td class="bold">${m.nom}</td>
                            <td>${m.prenom}</td>
                            <td>${m.telephone}</td>
                            <td><span class="badge-type">${m.type}</span></td>
                            <td class="no-print">
                                <div class="table-actions">
                                    <button class="action-btn view" onclick="openCV(${index})" title="Voir CV">
                                        <i class="fa-solid fa-eye"></i>
                                    </button>
                                    <button class="action-btn edit" onclick="currentOpenIndex=${index}; showMemberForm(membresData[${index}])" title="Modifier">
                                        <i class="fa-solid fa-pen"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
        
        <button class="csv-btn no-print" onclick="exportCSV()" title="Exporter en CSV">
            <i class="fa-solid fa-file-csv"></i>
        </button>
    `;
}

// Fonction de tri simple pour le tableau
function sortTable(key) {
    filteredMembres.sort((a, b) => {
        return a[key].localeCompare(b[key]);
    });
    renderMembresDisplay();
}
// ---------------------------
// FORMULAIRE (AJOUT / EDIT)
// ---------------------------
// --- FONCTION PRINCIPALE DU FORMULAIRE ---
// Fonction pour prévisualiser l'image choisie
function previewImage(input) {
    const preview = document.getElementById('photoPreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" id="img-preview">`;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Fonction pour ajouter des lignes dynamiques
function addRow(containerId, type) {
    const container = document.getElementById(containerId);
    const div = document.createElement('div');
    div.className = "dynamic-row";

    let fields = '';
    if (type === 'langue') {
        fields = `
            <input type="text" class="lg-nom" placeholder="Langue" style="flex:2">
            <select class="lg-niveau" style="flex:1">
                <option value="Mahay kely">Mahay kely</option>
                <option value="Afaka iasana">Afaka iasana</option>
                <option value="Mahafehy">Mahafehy</option>
            </select>`;
    } else if (type === 'formation') {
        fields = `
            <input type="text" class="of-nom" placeholder="Diplôme/Formation" style="flex:2">
            <input type="text" class="of-date" placeholder="Année" style="flex:1">
            <input type="text" class="of-lieu" placeholder="Lieu" style="flex:1">`;
    } else if (type === 'trakefa') {
        fields = `
            <input type="text" class="tr-poste" placeholder="Poste" style="flex:1">
            <input type="text" class="tr-lieu" placeholder="Entreprise" style="flex:1">
            <input type="text" class="tr-debut" placeholder="Début" style="flex:0.5">
            <input type="text" class="tr-fin" placeholder="Fin" style="flex:0.5">`;
    } else if (type === 'dingana') {
        fields = `
            <select class="di-etape" style="flex:1">
                <option value="Fanomanana">Fanomanana</option>
                <option value="Fananterana">Fananterana</option>
                <option value="Ravinala">Ravinala</option>
                <option value="Fanolorana Tp2">Fanolorana Tp2</option>
                <option value="Fiofanana Tp3">Fiofanana Tp3</option>
                <option value="Fiofanana Tp4">Fiofanana Tp4</option>
            </select>
            <input type="text" class="di-date" placeholder="Date" style="flex:1">
            <input type="text" class="di-lieu" placeholder="Lieu" style="flex:1">`;
    }

    div.innerHTML = fields + `<button type="button" class="btn-del" onclick="this.parentElement.remove()">×</button>`;
    container.appendChild(div);
}

// LE FORMULAIRE COMPLET
function showMemberForm(data = null) {
    const isEditing = !!data;
    const content = document.getElementById("content");

    content.innerHTML = `
    <div class="form-container">
        <div class="form-header">
            <button class="btn-back" onclick="loadMembres()"><i class="fa-solid fa-arrow-left"></i></button>
            <h2>${isEditing ? "Modifier le profil" : "Nouveau Membre Scout"}</h2>
        </div>
        
        <form id="member-form">
            <div class="form-section">
                <h3><i class="fa-solid fa-camera"></i> Identité & Photo</h3>
                <div class="photo-upload-container" style="text-align:center;">
                    <div id="photoPreview" class="photo-preview-circle">
                        ${data?.photo ? `<img src="${data.photo}">` : '<i class="fa-solid fa-user fa-3x" style="color:#cbd5e1"></i>'}
                    </div>
                    <input type="file" id="photoInput" hidden accept="image/*" onchange="previewImage(this)">
                    <button type="button" class="btn-back" onclick="document.getElementById('photoInput').click()">
                        <i class="fa-solid fa-image"></i> Sélectionner une photo
                    </button>
                </div>
                <br>
                <div class="form-grid">
                    <input type="text" id="nom" placeholder="NOM (Matraicule)" value="${data?.nom || ''}" required>
                    <input type="text" id="prenom" placeholder="Prénom" value="${data?.prenom || ''}">
                    <input type="text" id="surnom" placeholder="Surnom / Fiantso" value="${data?.surnom || ''}">
                    <select id="type">
                        <option value="Beazina" ${data?.type==='Beazina'?'selected':''}>Beazina</option>
                        <option value="Mpiandraikitra" ${data?.type==='Mpiandraikitra'?'selected':''}>Mpiandraikitra</option>
                        <option value="Tonia" ${data?.type==='Tonia'?'selected':''}>Tonia</option>
                        <option value="Filoha" ${data?.type==='Filoha'?'selected':''}>Filoha</option>
                    </select>
                    <select id="selectFaritra">
                        <option value="Diego">Diego</option>
                        <option value="Anivorano">Anivorano</option>
                        <option value="Ambilobe">Ambilobe</option>
                        <option value="Ambanja">Ambanja</option>
                        <option value="Nosy Be">Nosy Be</option>
                    </select>
                </div>
            </div>

            <div class="form-section">
                <h3><i class="fa-solid fa-shield-halved"></i> Détails Scout & Contact</h3>
                <div class="form-grid">
                    <select id="sampana">
                        <option value="Mavo" ${data?.sampana==='Mavo'?'selected':''}>Mavo (Louveteau)</option>
                        <option value="Maitso" ${data?.sampana==='Maitso'?'selected':''}>Maitso (Éclaireur)</option>
                        <option value="Mena" ${data?.sampana==='Mena'?'selected':''}>Mena (Routier)</option>
                        <option value="Menafify" ${data?.sampana==='Menafify'?'selected':''}>Menafify</option>
                    </select>
                    <input type="text" id="fafy" placeholder="Fafy" value="${data?.fafy || ''}">
                    <input type="text" id="andraikitra" placeholder="Andraikitra" value="${data?.andraikitra || ''}">
                    <input type="text" id="telephone" placeholder="Téléphone" value="${data?.telephone || ''}">
                    <input type="email" id="email" placeholder="Email" value="${data?.email || ''}">
                    <input type="text" id="fiangonana" placeholder="Fiangonana" value="${data?.fiangonana || ''}">
                    <input type="text" id="vady" placeholder="Nom du conjoint" value="${data?.vady || ''}">
                    <input type="number" id="zanaka" placeholder="Nombre d'enfants" value="${data?.nombre_zanaka || 0}">
                </div>
            </div>

            <div class="form-section">
                <div class="section-header-flex" style="display:flex; justify-content:space-between; align-items:center;">
                    <h3><i class="fa-solid fa-language"></i> Langues</h3>
                    <button type="button" class="btn-add-row" onclick="addRow('langues-list', 'langue')">+</button>
                </div>
                <div id="langues-list"></div>
            </div>

            <div class="form-section">
                <div class="section-header-flex" style="display:flex; justify-content:space-between; align-items:center;">
                    <h3><i class="fa-solid fa-graduation-cap"></i> Formations</h3>
                    <button type="button" class="btn-add-row" onclick="addRow('formations-list', 'formation')">+</button>
                </div>
                <div id="formations-list"></div>
            </div>

            <div class="form-section">
                <div class="section-header-flex" style="display:flex; justify-content:space-between; align-items:center;">
                    <h3><i class="fa-solid fa-medal"></i> Parcours Scout (Dingana)</h3>
                    <button type="button" class="btn-add-row" onclick="addRow('dingana-list', 'dingana')">+</button>
                </div>
                <div id="dingana-list"></div>
            </div>

            <button type="submit" class="btn-submit-global">
                <i class="fa-solid fa-floppy-disk"></i> ENREGISTRER LE MEMBRE
            </button>
        </form>
    </div>
    `;

    document.getElementById("member-form").onsubmit = function(e) {
        e.preventDefault();
        collecterEtSauvegarderTout();
    };
}

// --- COLLECTE ET ENVOI AU BACKEND ---
function collecterEtSauvegarderTout() {
    if (!window.backend) {
        alert("Erreur : Backend non connecté");
        return;
    }

    // 1. Gestion du chemin de la photo
    const input = document.getElementById("photoInput");
    let photoPath = "";
    // Note : Dans un environnement type Electron ou PyQt, .path permet de récupérer le chemin local réel
    if (input.files && input.files[0]) {
        photoPath = input.files[0].path || ""; 
    }

    // 2. Construction de l'objet global
    const data = {
        // Table principale : mpikambana
        perso: {
            nom: document.getElementById("nom").value.trim().toUpperCase(),
            prenom: document.getElementById("prenom").value.trim(),
            surnom: document.getElementById("surnom").value.trim(),
            type: document.getElementById("type").value,
            faritra: document.getElementById("selectFaritra").value,
            fafy: document.getElementById("fafy").value.trim(),
            sampana: document.getElementById("sampana").value.trim(),
            andraikitra: document.getElementById("andraikitra").value.trim(),
            telephone: document.getElementById("telephone").value.trim(),
            email: document.getElementById("email").value.trim(),
            fiangonana: document.getElementById("fiangonana").value.trim(),
            vady: document.getElementById("vady").value.trim() || "Tsisy",
            zanaka: parseInt(document.getElementById("zanaka").value) || 0,
            photo: photoPath // On envoie le chemin local pour traitement Python
        },

        // Table : fiteny (Langues)
        langues: Array.from(document.querySelectorAll("#langues-list .dynamic-row")).map(row => ({
            nom: row.querySelector(".lg-nom")?.value.trim(),
            niveau: row.querySelector(".lg-niveau")?.value
        })).filter(l => l.nom !== ""), // On ne garde que les lignes remplies

        // Table : ofana (Formations)
        formations: Array.from(document.querySelectorAll("#formations-list .dynamic-row")).map(row => ({
            nom: row.querySelector(".of-nom")?.value.trim(),
            date: row.querySelector(".of-date")?.value.trim(),
            lieu: row.querySelector(".of-lieu")?.value.trim()
        })).filter(f => f.nom !== ""),

        // Table : trakefa (Expériences professionnelles)
        trakefa: Array.from(document.querySelectorAll("#trakefa-list .dynamic-row")).map(row => ({
            poste: row.querySelector(".tr-poste")?.value.trim(),
            lieu: row.querySelector(".tr-lieu")?.value.trim(),
            debut: row.querySelector(".tr-debut")?.value.trim(),
            fin: row.querySelector(".tr-fin")?.value.trim()
        })).filter(t => t.poste !== ""),

        // Table : dingampiofanana (Parcours Scout)
        dingana: Array.from(document.querySelectorAll("#dingana-list .dynamic-row")).map(row => ({
            etape: row.querySelector(".di-etape")?.value.trim(),
            date: row.querySelector(".di-date")?.value.trim(),
            lieu: row.querySelector(".di-lieu")?.value.trim()
        })).filter(d => d.etape !== "")
    };

    // 3. Envoi au Backend Python
    console.log("Données envoyées au backend :", data);
    const success = window.backend.sauvegarder_tout_sql(data);

    if (success) {
        alert("Membre et tous ses détails enregistrés avec succès ✅");
        // Recharger les données et revenir à la vue liste
        if (typeof loadMembresFromDB === "function") loadMembresFromDB();
        if (typeof loadMembres === "function") loadMembres();
    } else {
        alert("Erreur lors de l'enregistrement dans la base de données ❌. Vérifiez la console Python.");
    }
}


function saveMemberData(isEdit) {
    const photoImg = document.getElementById("photoPreview").querySelector("img");
    const newMember = {
        nom: document.getElementById("nom").value.toUpperCase(),
        prenom: document.getElementById("prenom").value,
        telephone: document.getElementById("telephone").value,
        type: document.getElementById("type").value,
        sexe: "M", // À ajouter dans le form si besoin
        photo: photoImg ? photoImg.src : ""
    };

    if (isEdit) {
        membresData[currentOpenIndex] = newMember;
    } else {
        membresData.push(newMember);
    }
    loadMembres();
}

// ---------------------------
// GESTION DU CV (VIOLET)
// ---------------------------
function openCV(index) {
    currentOpenIndex = index;
    const m = filteredMembres[index];
    document.getElementById("membres-view").classList.add("hidden");
    const cvView = document.getElementById("cv-view");
    cvView.classList.remove("hidden");

    cvView.innerHTML = `
    <div class="cv-container">
        <div class="left">
            <div class="photo">${m.photo ? `<img src="${m.photo}">` : `<i class="fa-solid fa-user" style="font-size:80px;"></i>`}</div>
            <div class="name">${m.nom} <br> ${m.prenom}</div>
            <div class="fiantso">Mpiantrana</div>
            <div class="section">
                <div class="section-title">FIFANDRAISANA</div>
                <div class="contact-item"><i class="fa-solid fa-phone"></i> ${m.telephone}</div>
            </div>
        </div>
        <div class="right">
            <h1 class="right-title">DETAILS DU MEMBRE</h1>
            <p><strong>Fonction :</strong> ${m.type}</p>
            <p><strong>Sexe :</strong> ${m.sexe}</p>
        </div>
        <div class="cv-actions-floating">
            <button class="cv-action-btn back" onclick="closeCV()"><i class="fa-solid fa-arrow-left"></i></button>
            <button class="cv-action-btn edit" onclick="showMemberForm(membresData[currentOpenIndex])"><i class="fa-solid fa-user-pen"></i></button>
            <button class="cv-action-btn print" onclick="exportPDF()"><i class="fa-solid fa-print"></i></button>
        </div>
    </div>
    `;
}

function closeCV() {
    document.getElementById("cv-view").classList.add("hidden");
    document.getElementById("membres-view").classList.remove("hidden");
}

// Fermer le dropdown type si clic extérieur
window.onclick = function(event) {
    if (!event.target.closest('.search-combo')) {
        const d = document.getElementById("typeDropdown");
        if (d) d.style.display = "none";
    }
};

function exportPDF() {
    if (window.backend) {
        // On récupère les données complètes du membre grâce à l'index stocké
        const membre = membresData[currentOpenIndex]; 
        
        if (membre) {
            // On envoie l'objet à Python
            window.backend.exportCVtoPDF(membre); 
        }
    } else {
        alert("Erreur : Backend non connecté");
    }
}

function exportCSV() {
    const table = document.querySelector(".membres-table");
    if (!table) {
        alert("Veuillez afficher le tableau avant d'exporter.");
        return;
    }

    // Récupérer les entêtes (sauf la colonne Photo et Actions)
    const headers = ["Nom", "Prénom", "Téléphone", "Type"];
    
    // Récupérer les données
    const rows = filteredMembres.map(m => ({
        "Nom": m.nom,
        "Prénom": m.prenom,
        "Téléphone": m.telephone,
        "Type": m.type
    }));

    if (window.backend) {
        window.backend.exportTableToCSV(rows);
        alert("Exportation CSV réussie !");
    } else {
        alert("Backend non connecté.");
    }
}


// Exemple pour ajouter une langue à un membre
function saveLangue(idMembre) {
    const lg = document.getElementById("input_langue").value;
    const niv = document.getElementById("select_niveau").value;
    
    if (window.backend) {
        window.backend.ajouter_fiteny_sql(idMembre, lg, niv);
    }
}

// Exemple pour ajouter un parcours scout
function saveParcours(idMembre) {
    const etape = document.getElementById("select_etape").value; // ex: Tp2
    const date = document.getElementById("date_etape").value;
    const lieu = document.getElementById("lieu_etape").value;

    if (window.backend) {
        window.backend.ajouter_dingana_sql(idMembre, etape, date, lieu);
    }
}

