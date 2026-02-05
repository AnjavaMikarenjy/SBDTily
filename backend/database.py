import sqlite3

def init_db():
    conn = sqlite3.connect('diana_members.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    # Table Faritra (Les 5 secteurs de DIANA)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faritra (
            id_faritra INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_faritra TEXT NOT NULL UNIQUE
        )
    ''')

    # Insertion automatique des 5 Faritra si la table est vide
    secteurs = [('Diego',), ('Anivorano',), ('Ambilobe',), ('Ambanja',), ('Nosy Be',)]
    cursor.execute("SELECT COUNT(*) FROM faritra")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO faritra (nom_faritra) VALUES (?)", secteurs)
        print("Secteurs Diego, Anivorano, Ambilobe, Ambanja et Nosy Be ajoutés.")

    # Table Mpikambana liée à Faritra
    # Mise à jour finale de la table PRINCIPALE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mpikambana (
            id_membre INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,           -- Anarana
            prenom TEXT,                  -- Fanampiny
            surnom TEXT,                  -- Fiantso
            type TEXT CHECK( type IN ('Filoha', 'Tonia', 'Mpiandraikitra', 'Beazina') ),
            fafy TEXT,                    -- Fafy
            sampana TEXT CHECK( sampana IN ('Mavo', 'Maitso', 'Mena', 'Menafify') ),
            andraikitra TEXT,             -- Andraikitra
            adresse TEXT,                 -- Adresy
            telephone TEXT,               -- Finday
            email TEXT,                   -- Mail
            fiangonana TEXT,              -- Fiangonana
            vady TEXT DEFAULT 'Tsisy',    -- Vady
            nombre_zanaka INTEGER DEFAULT 0, -- Zanaka
            photo TEXT,                    -- Chemin vers la photo
            id_faritra INTEGER,           -- Lien vers Diego, Ambanja...
            synced INTEGER DEFAULT 0,
            FOREIGN KEY (id_faritra) REFERENCES faritra (id_faritra)
        )
    ''')

# 3. Table FORMATION (Ofana)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ofana (
            id_ofana INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,         -- Lien vers le membre
            nom_formation TEXT NOT NULL,
            date_diplome DATE,         -- Format DD-MM-YYYY
            lieu_formation TEXT,
            synced INTEGER DEFAULT 0,  -- Pour la future API
            FOREIGN KEY (id_membre) REFERENCES mpikambana (id_membre) ON DELETE CASCADE
        )
    ''')

# Table LANGUE (Fiteny)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fiteny (
            id_fiteny INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,
            nom_langue TEXT NOT NULL, 
            niveau TEXT CHECK( niveau IN ('Tsy mahay', 'Mahay kely', 'Afaka iasana', 'Mahafehy') ),
            FOREIGN KEY (id_membre) REFERENCES mpikambana (id_membre) ON DELETE CASCADE
        )
    ''')

# Table EXPERIENCE (Trakefa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trakefa (
            id_trakefa INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,
            poste TEXT NOT NULL,         -- ex: "Chef de Groupe" ou "Comptable"
            entreprise_lieu TEXT,        -- Entreprise ou branche scout
            date_debut TEXT,             -- Format MM-YYYY
            date_fin TEXT,               -- Format MM-YYYY ou "Présent"
            description TEXT,            -- Ce qu'on y fait (missions)
            FOREIGN KEY (id_membre) REFERENCES mpikambana (id_membre) ON DELETE CASCADE
        )
    ''')

    # Table PARCOURS SCOUT (Dingampiofanana)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dingampiofanana (
            id_dingana INTEGER PRIMARY KEY AUTOINCREMENT,
            id_membre INTEGER,
            etape TEXT CHECK( etape IN (
                'Fanomanana', 'Fananterana', 'Ravinala', 
                'Fanolorana Tp2', 'Fiofanana Tp3', 'Fanolorana Tp3', 
                'Fiofanana Tp4', 'Fanolorana Tp4'
            )),
            date_etape DATE,
            lieu_etape TEXT,
            FOREIGN KEY (id_membre) REFERENCES mpikambana (id_membre) ON DELETE CASCADE
        )
    ''')
        # ... (les autres tables ofana, trakefa, etc. restent identiques)
    
    conn.commit()
    conn.close()

init_db()

def ajouter_formation(id_membre, nom, date, lieu):
    conn = sqlite3.connect('diana_members.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO ofana (id_membre, nom_formation, date_diplome, lieu_formation)
            VALUES (?, ?, ?, ?)
        ''', (id_membre, nom, date, lieu))
        conn.commit()
    except Exception as e:
        print(f"Erreur d'insertion : {e}")
    finally:
        conn.close()

# Exemple : ajouter_formation(1, "Secourisme", "2023-05-15", "Antsiranana")

def ajouter_langue_db(id_membre, langue, niveau):
    """Insère une langue pour un membre spécifique"""
    conn = sqlite3.connect('diana_members.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO fiteny (id_membre, nom_langue, niveau)
            VALUES (?, ?, ?)
        ''', (id_membre, langue, niveau))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erreur SQL Fiteny : {e}")
        return False
    finally:
        conn.close()

def ajouter_experience_db(id_membre, poste, entreprise, debut, fin, description):
    conn = sqlite3.connect('diana_members.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO trakefa (id_membre, poste, entreprise_lieu, date_debut, date_fin, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_membre, poste, entreprise, debut, fin, description))
        conn.commit()
    finally:
        conn.close()

def ajouter_parcours_scout(id_membre, etape, date, lieu):
    conn = sqlite3.connect('diana_members.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO dingampiofanana (id_membre, etape, date_etape, lieu_etape)
            VALUES (?, ?, ?, ?)
        ''', (id_membre, etape, date, lieu))
        conn.commit()
    finally:
        conn.close()