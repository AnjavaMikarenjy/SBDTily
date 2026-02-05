import os
import sys
import sqlite3
import csv
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QObject, pyqtSlot, QVariant
from PIL import Image  # Assure-toi d'avoir fait : pip install Pillow

# --- FORCE LE CHEMIN DU PROJET ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    import database
except ImportError:
    # Si le fichier est juste à côté
    import database


class Backend(QObject):
    def __init__(self, webview):
        super().__init__()
        self.webview = webview
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, 'diana_members.db')

#-------exportation PDF --------------
    # ... votre code ...

    @pyqtSlot(QVariant) # Utilisez QVariant au lieu de dict
    def exportCVtoPDF(self, membre_data):
        try:
            # membre_data arrive maintenant proprement comme un dictionnaire Python
            nom_membre = membre_data.get('nom', 'membre')
            
            path, _ = QFileDialog.getSaveFileName(
                None,
                "Exporter le CV en PDF",
                f"CV_{nom_membre}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if path:
                # On lance l'impression PDF de la page actuelle
                self.webview.page().printToPdf(path)
                return True
            return False
        except Exception as e:
            print(f"Erreur Python : {e}")
            return False
    

    @pyqtSlot(result=str)
    def ping(self):
        return "Backend OK"

    @pyqtSlot(result=list)
    def getMembers(self):
        # temporaire
        return []

    @pyqtSlot(dict)
    def saveMember(self, data):
        print("SAVE MEMBER :", data)

#-----exportation CSV-----------
    @pyqtSlot(list)
    def exportTableToCSV(self, rows):
        if not rows:
            return

        path, _ = QFileDialog.getSaveFileName(
            None,
            "Exporter le tableau en CSV",
            "tableau.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        headers = rows[0].keys()

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    @pyqtSlot(dict, result=int)
    def ajouter_membre_sql(self, m):
        conn = sqlite3.connect('diana_members.db')
        cursor = conn.cursor()
        new_id = -1 # Valeur par défaut en cas d'erreur
        try:
            # 1. Récupérer l'ID de la Faritra
            cursor.execute("SELECT id_faritra FROM faritra WHERE nom_faritra = ?", (m['faritra'],))
            res = cursor.fetchone()
            id_f = res[0] if res else None

            # 2. Préparer la requête
            query = '''
                INSERT INTO mpikambana (
                    nom, prenom, surnom, type, fafy, sampana, andraikitra, 
                    adresse, telephone, email, fiangonana, vady, nombre_zanaka, id_faritra
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            values = (
                m['nom'], m['prenom'], m['surnom'], m['type'], m['fafy'], 
                m['sampana'], m['andraikitra'], m['adresse'], m['telephone'], 
                m['email'], m['fiangonana'], m['vady'], m['zanaka'], id_f
            )
            
            # 3. Exécuter et récupérer l'ID immédiatement
            cursor.execute(query, values)
            new_id = cursor.lastrowid  # <--- C'est ici qu'on récupère l'ID
            conn.commit()
            print(f"Membre enregistré avec succès ! ID: {new_id}")
            
        except Exception as e:
            print(f"Erreur d'enregistrement : {e}")
            conn.rollback() # Annule l'opération en cas d'erreur
            new_id = 0 # 0 indique une erreur au JavaScript
        finally:
            conn.close()
        
        return new_id # On renvoie l'ID à la fin

    @pyqtSlot(result=list)
    def charger_membres(self):
        """Lit la base de données au lancement et après chaque action"""
        if not os.path.exists(self.db_path):
            print(f"Base introuvable à : {self.db_path}")
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.*, f.nom_faritra 
                FROM mpikambana m 
                LEFT JOIN faritra f ON m.id_faritra = f.id_faritra
            """)
            rows = [dict(row) for row in cursor.fetchall()]
            return rows
        except Exception as e:
            print(f"Erreur chargement : {e}")
            return []
        finally:
            conn.close()
    
    # --- TABLE OFANA (Formation) ---
    @pyqtSlot(int, str, str, str)
    def ajouter_ofana_sql(self, id_membre, nom, date, lieu):
        database.ajouter_formation_db(id_membre, nom, date, lieu)

    # --- TABLE FITENY (Langues) ---
    @pyqtSlot(int, str, str)
    def ajouter_fiteny_sql(self, id_membre, langue, niveau):
        database.ajouter_langue_db(id_membre, langue, niveau)

    # --- TABLE TRAKEFA (Expériences) ---
    @pyqtSlot(int, str, str, str, str, str)
    def ajouter_trakefa_sql(self, id_membre, poste, lieu, debut, fin, desc):
        database.ajouter_experience_db(id_membre, poste, lieu, debut, fin, desc)

    # --- TABLE DINGAMPIOFANANA (Parcours Scout) ---
    @pyqtSlot(int, str, str, str)
    def ajouter_dingana_sql(self, id_membre, etape, date, lieu):
        database.ajouter_parcours_scout_db(id_membre, etape, date, lieu)

# ... (reste du code)
    @pyqtSlot(QVariant, result=bool)
    def sauvegarder_tout_sql(self, data):
        conn = None
        try:
            # --- 1. CONFIGURATION DES CHEMINS ---
            # 'api.py' est dans /backend, on remonte d'un niveau pour la racine du projet
            current_folder = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_folder)
            db_path = os.path.join(project_root, 'diana_members.db')

            # --- 2. INITIALISATION / SÉCURITÉ DE LA BASE ---
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # On force la création des tables si elles n'existent pas
            cursor.execute("CREATE TABLE IF NOT EXISTS faritra (id_faritra INTEGER PRIMARY KEY AUTOINCREMENT, nom_faritra TEXT NOT NULL UNIQUE)")
            cursor.execute("SELECT COUNT(*) FROM faritra")
            if cursor.fetchone()[0] == 0:
                secteurs = [('Diego',), ('Anivorano',), ('Ambilobe',), ('Ambanja',), ('Nosy Be',)]
                cursor.executemany("INSERT INTO faritra (nom_faritra) VALUES (?)", secteurs)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mpikambana (
                    id_membre INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL, prenom TEXT, surnom TEXT, type TEXT,
                    fafy TEXT, sampana TEXT, andraikitra TEXT, telephone TEXT,
                    email TEXT, fiangonana TEXT, vady TEXT, nombre_zanaka INTEGER,
                    photo TEXT, id_faritra INTEGER,
                    FOREIGN KEY(id_faritra) REFERENCES faritra(id_faritra)
                )
            ''')
            # Tables secondaires
            cursor.execute("CREATE TABLE IF NOT EXISTS fiteny (id_fiteny INTEGER PRIMARY KEY AUTOINCREMENT, id_membre INTEGER, nom_langue TEXT, niveau TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS ofana (id_ofana INTEGER PRIMARY KEY AUTOINCREMENT, id_membre INTEGER, nom_formation TEXT, date_diplome TEXT, lieu_formation TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS trakefa (id_trakefa INTEGER PRIMARY KEY AUTOINCREMENT, id_membre INTEGER, poste TEXT, entreprise_lieu TEXT, date_debut TEXT, date_fin TEXT, description TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS dingampiofanana (id_dingana INTEGER PRIMARY KEY AUTOINCREMENT, id_membre INTEGER, etape TEXT, date_etape TEXT, lieu_etape TEXT)")
            conn.commit()

            # --- 3. RÉCUPÉRATION DES DONNÉES ---
            if hasattr(data, 'toVariantMap'):
                data = data.toVariantMap()
            
            p = data.get("perso", {})
            print(f"--- Enregistrement de {p.get('nom')} dans {db_path} ---")

            # --- 4. GESTION DE LA PHOTO ---
            photo_path_source = p.get("photo", "")
            final_photo_db_path = "" # Ce qui sera écrit en base

            if photo_path_source:
                # Nettoyage du chemin Windows/Qt
                clean_source = photo_path_source.replace("file:///", "")
                if os.name == 'nt' and clean_source.startswith("/"):
                    clean_source = clean_source[1:]
                
                if os.path.exists(clean_source):
                    # Dossier /uploads à la racine du projet
                    upload_dir = os.path.join(project_root, "uploads")
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    dest_path = os.path.join(upload_dir, filename)
                    
                    # Traitement et sauvegarde de l'image
                    with Image.open(clean_source) as img:
                        img = img.convert('RGB')
                        img.thumbnail((400, 400))
                        img.save(dest_path, "JPEG", quality=85)
                    
                    # On stocke le chemin relatif à la racine
                    final_photo_db_path = f"uploads/{filename}"

            # --- 5. INSERTION DU MEMBRE ---
            cursor.execute("SELECT id_faritra FROM faritra WHERE nom_faritra = ?", (p.get("faritra"),))
            res = cursor.fetchone()
            id_f = res[0] if res else 1

            cursor.execute("""
                INSERT INTO mpikambana (nom, prenom, surnom, type, fafy, sampana, andraikitra, 
                telephone, email, fiangonana, vady, nombre_zanaka, photo, id_faritra)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                p.get("nom"), p.get("prenom"), p.get("surnom"), p.get("type"),
                p.get("fafy"), p.get("sampana"), p.get("andraikitra"),
                p.get("telephone"), p.get("email"), p.get("fiangonana"),
                p.get("vady"), p.get("zanaka"), final_photo_db_path, id_f
            ))

            membre_id = cursor.lastrowid

            # --- 6. INSERTION DES TABLES LIÉES (Langues, Formations, etc.) ---
            for l in data.get("langues", []):
                cursor.execute("INSERT INTO fiteny (id_membre, nom_langue, niveau) VALUES (?,?,?)", 
                               (membre_id, l.get("nom"), l.get("niveau")))
            
            for f in data.get("formations", []):
                cursor.execute("INSERT INTO ofana (id_membre, nom_formation, date_diplome, lieu_formation) VALUES (?,?,?,?)", 
                               (membre_id, f.get("nom"), f.get("date"), f.get("lieu")))
            
            for t in data.get("trakefa", []):
                cursor.execute("INSERT INTO trakefa (id_membre, poste, entreprise_lieu, date_debut, date_fin, description) VALUES (?,?,?,?,?,?)", 
                               (membre_id, t.get("poste"), t.get("lieu"), t.get("debut"), t.get("fin"), ""))
            
            for d in data.get("dingana", []):
                cursor.execute("INSERT INTO dingampiofanana (id_membre, etape, date_etape, lieu_etape) VALUES (?,?,?,?)", 
                               (membre_id, d.get("etape"), d.get("date"), d.get("lieu")))

            conn.commit()
            print("✅ Enregistrement réussi !")
            return True

        except Exception as e:
            print(f"❌ Erreur critique : {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()