import sys
import sqlite3
import json
import hashlib
import traceback
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QGraphicsBlurEffect,
    QFileDialog, QMainWindow, QFrame, QGraphicsDropShadowEffect,
    QVBoxLayout, QHBoxLayout, QDialog, QComboBox, QListWidget, QDateEdit,
    QStackedWidget, QTableWidget, QTableWidgetItem, QMessageBox, QFormLayout,
    QGridLayout, QMenu, QTabWidget, QHeaderView, QSizePolicy, QAbstractItemView, QStyle
)
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator, QPainter, QColor
from PyQt6.QtCore import Qt, QSize, QDate, pyqtSignal

#===================== BASE DE DONNÉES =====================

DB_NAME = "mouvement.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def __init_db__():
    conn = get_db()
    c = conn.cursor()

    # Table des structures (schémas)
    c.execute('''
        CREATE TABLE IF NOT EXISTS schemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            field_name TEXT,
            field_type TEXT,
            ui_type TEXT,
            options TEXT
        )
    ''')
    c.execute("PRAGMA table_info(schemas)")
    cols = [col[1] for col in c.fetchall()]

    if "ui_type" not in cols:
        c.execute("ALTER TABLE schemas ADD COLUMN ui_type TEXT")

    if "options" not in cols:
        c.execute("ALTER TABLE schemas ADD COLUMN options TEXT")

    # Table admin
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Table membres (corrigé: virgules manquantes)
    c.execute('''
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            photo TEXT
        )
    ''')

    # Admin par défaut (hachage SHA256 pour éviter mot de passe en clair)
    c.execute("SELECT password FROM admin LIMIT 1")
    row = c.fetchone()
    if not row:
        pwd_hash = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
                  ("DFH", pwd_hash))
    else:
        # si mot de passe existant et non-haché (longueur différente de 64), le hacher
        existing = row[0] or ""
        if len(existing) != 64:
            hashed = hashlib.sha256(existing.encode()).hexdigest()
            try:
                c.execute("UPDATE admin SET password=? WHERE id=1", (hashed,))
            except Exception:
                pass

    conn.commit()
    conn.close()

#===================== STYLE (CSS Qt) =====================

STYLE = """
QWidget {
    background-color: #ffffff;
    font-family: Arial;
    font-size: 14px;
    color: #000000;
}
QLabel {
    color: #000000;
}
QLineEdit {
    padding: 8px;
    border-radius: 15px;
    border: 2px solid #622599;
}
QPushButton {
    color : white;
    background-color: #622599;
    padding: 8px;
    border-radius: 15px;
    border: none;
}
QPushButton:hover {
    background-color: #0041a0;
}
QFrame, QWidget#card {
    background: white;
    border-radius: 10px;
}
"""

#===================== PAGE LOGIN =====================

class LoginPage(QWidget):
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked

        # ===== IMAGE DE FOND =====
        self.bg = QLabel(self)
        self.bg.setPixmap(QPixmap("assets/login_bg.jpg"))
        self.bg.setScaledContents(True)
        self.bg.lower()

        # ===== ZONE FLOUTÉE =====
        self.blur_bg = QLabel(self)
        self.blur_bg.setScaledContents(True)
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(5)
        self.blur_bg.setGraphicsEffect(blur)

        # ===== CARTE LOGIN =====
        card = QFrame(self)
        card.setFixedSize(360, 320)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 18px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setYOffset(8)
        card.setGraphicsEffect(shadow)

        # ===== FORMULAIRE =====
        form = QVBoxLayout(card)
        form.setSpacing(10)

        #logo
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QPixmap("assets/logo.png")
        logo = logo.scaled(
                130, 130,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        label.setPixmap(logo)
        label.show()

        self.user = QLineEdit()
        self.user.setPlaceholderText("Nom d'utilisateur")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Mot de passe")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        btn = QPushButton("Se connecter")
        btn.clicked.connect(self.login)

        form.addStretch()
        form.addWidget(label)
        form.addWidget(self.user)
        form.addWidget(self.password)
        form.addWidget(btn)
        form.addStretch()

        # ===== CENTRAGE =====
        main = QVBoxLayout(self)
        main.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        self.blur_bg.lower()
        card.raise_()

    def resizeEvent(self, event):
        self.bg.resize(self.size())

        # flou seulement derrière la carte
        w, h = 420, 380
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2

        full_pixmap = self.bg.pixmap()
        if full_pixmap:
            scaled = full_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            cropped = scaled.copy(x, y, w, h)
            self.blur_bg.setPixmap(cropped)
            self.blur_bg.setGeometry(x, y, w, h)

    def login(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            pwd_hash = hashlib.sha256(self.password.text().encode()).hexdigest()
            c.execute(
                "SELECT * FROM admin WHERE username=? AND password=?",
                (self.user.text(), pwd_hash)
            )
            if c.fetchone():
                self.stacked.setCurrentIndex(1)
            else:
                QMessageBox.warning(self, "Erreur", "Identifiants incorrects")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur base de données: {e}")
        finally:
            conn.close()


class SidebarButton(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px 10px 12px;
                border: none;
                background-color: #622599;
                font-size: 14px;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0041a0;
            }
            QPushButton:checked {
                background-color: #0041a0;
                color: white;
            }
        """)

#===================== DASHBOARD =====================

class Dashboard(QWidget):
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        # ===== SIDEBAR FIXE =====
        menu = QFrame()
        menu.setFixedWidth(230)
        menu.setStyleSheet("""
            QFrame {
                background-color: rgb(236, 236, 236);
                border: 1px solid rgb(236, 236, 236);
                margin: 10px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setYOffset(6)
        menu.setGraphicsEffect(shadow)

        menu_layout = QVBoxLayout(menu)
        menu_layout.setContentsMargins(12, 20, 12, 20)

        title = QLabel("BD DIANA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold; padding-bottom:20px;border: none;")

        def sidebar(icon_path, text, parent):
            button = QPushButton(text, parent)
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(28, 28))
            button.setFixedHeight(52)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px 18px 10px 12px;
                    border: none;
                    background-color: #622599;
                    font-size: 14px;
                    color: white;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #0041a0;
                }
                QPushButton:checked {
                    background-color: #0041a0;
                    color: white;
                }
            """)
            return button

        btn_dashboard = SidebarButton("🏠", "Dashboard")
        btn_membres   = sidebar("assets/people-group.png", "Membres", self)
        btn_stats     = SidebarButton("📊", "Statistiques")
        btn_params    = SidebarButton("⚙", "Paramètres")

        btn_dashboard.setChecked(True)

        menu_layout.addWidget(title)
        menu_layout.addWidget(btn_dashboard)
        menu_layout.addWidget(btn_membres)
        menu_layout.addWidget(btn_stats)
        menu_layout.addStretch()
        menu_layout.addWidget(btn_params)

        btn_params.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 18px;
                border: none;
                background-color: black;
                font-size: 14px;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgb(5, 192, 30);
            }
            QPushButton:checked {
                background-color: rgb(5, 192, 30);
                border-radius: 6px;
            }
        """)

        # ===== CONTENU (STACK INTERNE) =====
        content = QFrame()
        content.setStyleSheet("background-color: rgb(236, 236, 236); margin: 10px; border: 1px solid rgb(236, 236, 236);")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setYOffset(6)
        content.setGraphicsEffect(shadow)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet("font-size:22px; font-weight:bold;")

        self.content_stack = QStackedWidget()

        # Pages internes
        self.page_home = QLabel("Bienvenue sur le tableau de bord")
        self.page_membres = MembresPage()
        self.page_stats = StatsPage()
        self.page_params = ParametresPage()

        self.content_stack.addWidget(self.page_home)     # index 0
        self.content_stack.addWidget(self.page_membres)  # index 1
        self.content_stack.addWidget(self.page_stats)    # index 2
        self.content_stack.addWidget(self.page_params)   # index 3

        content_layout.addWidget(self.page_title)
        content_layout.addWidget(self.content_stack)

        # ===== NAVIGATION SANS BOUGER LE MENU =====
        def activate(btn, title, index):
            for b in [btn_dashboard, btn_membres, btn_stats, btn_params]:
                b.setChecked(False)
            btn.setChecked(True)
            self.page_title.setText(title)
            self.content_stack.setCurrentIndex(index)

        btn_dashboard.clicked.connect(lambda: activate(btn_dashboard, "Dashboard", 0))
        btn_membres.clicked.connect(lambda: activate(btn_membres, "Membres", 1))
        btn_stats.clicked.connect(lambda: activate(btn_stats, "Statistiques", 2))
        btn_params.clicked.connect(lambda: activate(btn_params, "Paramètres", 3))

        # ===== GRID =====
        grid.addWidget(menu, 0, 0)
        grid.addWidget(content, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 4)

#===================== MEMBRES =====================

def load_members(type_membre):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT * FROM membres
            WHERE type=?
        """, (type_membre,))
        rows = c.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

class FormView(QWidget):
    submitted = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.type_membre = None
        self.inputs = {}
        self.current_id = None

        self.layout = QFormLayout(self)
        self.layout.setSpacing(12)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.submit)

    def build(self, type_membre):
        self.type_membre = type_membre
        self.inputs.clear()
        self.current_id = None

        # Nettoyer le layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w and w is not self.btn_save:
                w.deleteLater()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT field_name, ui_type, options
            FROM schemas WHERE type=?
        """, (type_membre,))

        for name, ui, options in c.fetchall():
            widget = self.create_widget(ui, options)
            self.inputs[name] = widget
            self.layout.addRow(name.capitalize(), widget)

        conn.close()
        self.layout.addRow(self.btn_save)

    def create_widget(self, ui, options):
        if ui == "Liste":
            combo = QComboBox()
            try:
                items = json.loads(options) if options else []
            except Exception:
                items = []
            combo.addItems(items)
            return combo

        if ui == "Date":
            date = QDateEdit()
            date.setCalendarPopup(True)
            date.setDisplayFormat("yyyy-MM-dd")
            # placeholder via special value
            min_date = QDate(1900, 1, 1)
            date.setMinimumDate(min_date)
            date.setMaximumDate(QDate.currentDate())
            date.setSpecialValueText("aaaa-mm-jj")
            date.setDate(min_date)
            return date

        # Texte / Email / Téléphone / Nombre
        line = QLineEdit()
        if ui == "Nombre":
            line.setValidator(QIntValidator())
        return line

    def submit(self):
        data = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                data[name] = widget.currentText()
            elif isinstance(widget, QDateEdit):
                d = widget.date()
                if hasattr(widget, 'minimumDate') and d == widget.minimumDate():
                    data[name] = ""
                else:
                    data[name] = d.toString("yyyy-MM-dd")
            elif isinstance(widget, QPushButton):
                data[name] = getattr(widget, "path", "")
            else:
                data[name] = widget.text()

        self.submitted.emit(data)

class TableView(QTableWidget):
    rowSelected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.data = []

        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

        self.cellClicked.connect(self.on_row_click)

    def load_data(self, data):
        """data = liste de dictionnaires"""
        self.data = data
        self.clear()

        if not data:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        headers = list(data[0].keys())
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(data))

        for r, row in enumerate(data):
            for c, key in enumerate(headers):
                self.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))

        self.resizeColumnsToContents()

    def on_row_click(self, row, _):
        if row < 0 or row >= len(self.data):
            return
        self.rowSelected.emit(self.data[row])

class ProfileView(QWidget):
    def __init__(self):
        super().__init__()

        self.data = []
        self.index = 0

        main = QVBoxLayout(self)
        main.setSpacing(16)

        # ===== CARTE =====
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)

        # ===== PHOTO =====
        self.photo = QLabel()
        self.photo.setFixedSize(140, 140)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setStyleSheet("""
            QLabel {
                border: 2px solid black;
                border-radius: 70px;
            }
        """)
        card_layout.addWidget(self.photo, alignment=Qt.AlignmentFlag.AlignCenter)

        # ===== INFOS =====
        self.info_layout = QGridLayout()
        self.info_layout.setHorizontalSpacing(20)
        card_layout.addLayout(self.info_layout)

        main.addWidget(card)

        # ===== NAVIGATION =====
        nav = QHBoxLayout()
        self.lbl_index = QLabel("0 / 0")

        btn_prev = QPushButton("◀ Précédent")
        btn_next = QPushButton("Suivant ▶")

        btn_prev.clicked.connect(self.prev)
        btn_next.clicked.connect(self.next)

        nav.addWidget(btn_prev)
        nav.addStretch()
        nav.addWidget(self.lbl_index)
        nav.addStretch()
        nav.addWidget(btn_next)

        main.addLayout(nav)

    def set_data(self, data):
        """data = liste de dictionnaires"""
        self.data = data
        self.index = 0
        self.refresh()

    def refresh(self):
        # Nettoyer
        while self.info_layout.count():
            item = self.info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.data:
            self.lbl_index.setText("0 / 0")
            return

        person = self.data[self.index]

        row = 0
        for key, value in person.items():
            if key == "photo":
                self.load_photo(value)
                continue

            lbl_key = QLabel(key.capitalize())
            lbl_key.setStyleSheet("font-weight:bold;")

            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet("padding:4px 0;")

            self.info_layout.addWidget(lbl_key, row, 0)
            self.info_layout.addWidget(lbl_val, row, 1)
            row += 1

        self.lbl_index.setText(f"{self.index + 1} / {len(self.data)}")

    def load_photo(self, path):
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(
                    140, 140,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.photo.setPixmap(pix)
                return
        self.photo.setText("Photo")

    def prev(self):
        if self.index > 0:
            self.index -= 1
            self.refresh()

    def next(self):
        if self.index < len(self.data) - 1:
            self.index += 1
            self.refresh()

class MembresPage(QWidget):
    def __init__(self):
        super().__init__()

        # ===== STATE =====
        self.current_type = "Filoha"
        self.search_text = ""

        # ===== LAYOUT PRINCIPAL =====
        main = QVBoxLayout(self)
        main.setSpacing(12)

        # Card principale pour Membres (même thème que Paramètres)
        card = QFrame()
        card.setObjectName("members_card")
        card.setStyleSheet("""
            QFrame#members_card { background: #ffffff; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); }
            QLineEdit, QComboBox { min-height: 36px; border-radius: 8px; padding: 6px 10px; border: 1px solid rgba(0,0,0,0.12); background: white; }
            QPushButton[role="secondary"] { background: transparent; color: #222; border: 1px solid rgba(0,0,0,0.12); padding: 8px 14px; border-radius: 8px; }
            QPushButton { background: #000; color: white; padding: 8px 14px; border-radius: 8px; }
            QTableWidget { background: #eefafb; gridline-color: rgba(0,0,0,0.15); }
            QScrollBar:vertical { width: 12px; background: transparent; margin: 4px; }
            QScrollBar::handle:vertical { background: #622599; border-radius: 6px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #0041a0; }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setYOffset(6)
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        # ===== HEADER =====
        header = QHBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Filoha", "Mpiandraikitra", "Tonia", "Beazina"])
        self.type_combo.currentTextChanged.connect(self.change_type)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un membre...")
        self.search.textChanged.connect(self.apply_search)

        btn_filter = QPushButton("Filtrer")

        header.addWidget(self.type_combo)
        header.addWidget(self.search)
        header.addWidget(btn_filter)

        card_layout.addLayout(header)

        # ================= SWITCHER =================
        switcher = QHBoxLayout()

        btn_form = QPushButton("📝 Saisie")
        btn_table = QPushButton("📋 Tableau")
        btn_profile = QPushButton("👤 Fiche")

        switcher.addWidget(btn_form)
        switcher.addWidget(btn_table)
        switcher.addWidget(btn_profile)
        switcher.addStretch()

        card_layout.addLayout(switcher)

        # ================= STACK =================
        self.stack = QStackedWidget()

        self.form_view = FormView()
        self.table_view = TableView()
        self.profile_view = ProfileView()

        self.stack.addWidget(self.form_view)
        self.stack.addWidget(self.table_view)
        self.stack.addWidget(self.profile_view)

        card_layout.addWidget(self.stack)

        # afficher la card dans le layout principal
        main.addWidget(card)

        # ===== BOUTONS SWITCH =====
        btn_form.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_table.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_profile.clicked.connect(lambda: self.stack.setCurrentIndex(2))

        # ===== SIGNALS =====
        self.form_view.submitted.connect(self.save_member)
        self.table_view.rowSelected.connect(self.show_profile)

        # ===== INIT =====
        self.change_type(self.type_combo.currentText())

        # remove invalid placeholder stylesheet (was '...')
        self.setStyleSheet("")    

    def show_profile(self, row_data):
        self.stack.setCurrentWidget(self.profile_view)
        self.profile_view.set_data([row_data])

    def save_member(self, data):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            data["type"] = self.current_type

            if self.form_view.current_id:  # UPDATE
                member_id = self.form_view.current_id

                cols = [f"{k}=?" for k in data.keys()]
                values = list(data.values())
                values.append(member_id)

                c.execute(
                    f"UPDATE membres SET {', '.join(cols)} WHERE id=?",
                    values
                )

            else:  # INSERT
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                values = list(data.values())

                c.execute(
                    f"INSERT INTO membres ({cols}) VALUES ({placeholders})",
                    values
                )

            conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur base de données: {e}")
        finally:
            conn.close()

        self.form_view.current_id = None

        # Refresh
        self.members_data = load_members(self.current_type)
        self.table_view.load_data(self.members_data)
        self.profile_view.set_data(self.members_data)
        self.form_view.build(self.current_type)

    def change_type(self, type_membre):
        self.current_type = type_membre

        self.form_view.build(type_membre)

        self.members_data = load_members(type_membre)
        self.filtered_data = self.members_data

        self.table_view.load_data(self.members_data)
        self.profile_view.set_data(self.members_data)

    def apply_search(self, text):
        self.search_text = text.lower()

        if not hasattr(self, "members_data"):
            return

        if not self.search_text:
            filtered = self.members_data
        else:
            filtered = []
            for row in self.members_data:
                for value in row.values():
                    if self.search_text in str(value).lower():
                        filtered.append(row)
                        break

        self.table_view.load_data(filtered)
        self.profile_view.set_data(filtered)

class StatsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Statistiques des membres (à venir : graphiques)"))
        self.setLayout(layout)

class ListOptionsDialog(QDialog):
    def __init__(self, options=None):
        super().__init__()
        self.setWindowTitle("Configurer la liste")
        self.setFixedSize(360, 300)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        if options:
            for opt in options:
                self.list_widget.addItem(opt)

        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Nouvelle option")

        btn_add = QPushButton("➕")
        btn_del = QPushButton("❌")

        btn_add.clicked.connect(self.add_option)
        btn_del.clicked.connect(self.remove_option)

        input_layout.addWidget(self.input)
        input_layout.addWidget(btn_add)
        input_layout.addWidget(btn_del)

        layout.addLayout(input_layout)

        btn_validate = QPushButton("Valider")
        btn_validate.clicked.connect(self.accept)
        layout.addWidget(btn_validate)

    def add_option(self):
        text = self.input.text().strip()
        if text:
            self.list_widget.addItem(text)
            self.input.clear()

    def remove_option(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.list_widget.takeItem(row)

    def get_options(self):
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]

def sync_membres_table(type_membre):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT field_name, field_type
        FROM schemas WHERE type=?
    """, (type_membre,))
    fields = c.fetchall()

    c.execute("PRAGMA table_info(membres)")
    existing = [col[1] for col in c.fetchall()]

    for name, sql_type in fields:
        safe_name = str(name).replace('"', '').replace(" ", "_")
        if safe_name not in existing:
            try:
                c.execute(f'ALTER TABLE membres ADD COLUMN "{safe_name}" {sql_type}')
            except Exception:
                pass

    conn.commit()
    conn.close()

class StructureTablesPage(QWidget):
    def __init__(self):
        super().__init__()

        self.editing_field_id = None
        self.list_options = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)   # réduire les marges pour améliorer l'espace disponible
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(120)
        self.type_combo.addItems(["Filoha", "Mpiandraikitra", "Tonia", "Beazina"])
        self.type_combo.currentTextChanged.connect(self.load_fields)

        top.addStretch()
        top.addWidget(self.type_combo, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        layout.addLayout(top)

        self.table = QTableWidget(0,4)
        # Colonnes : Numéro (auto), Nom, Type, Actions
        self.table.setHorizontalHeaderLabels(["#", "Nom du champ", "Type", "Actions"])
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f4f7fb;
                gridline-color: #cfd8dc;
                font-size: 13px;
                color: black;
            }
            QTableWidget::item { padding: 8px; color: #000000; }
            QTableWidget::item:selected { background-color: #cce5ff; color: #000000; }
            QTableWidget::item:hover { background-color: #eaf2ff; }
            QHeaderView::section { background-color: #e6eef7; color: #000000; padding: 8px; border: 1px solid #cfd8dc; font-weight: bold; }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # numero
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)       # nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)         # actions
        self.table.setColumnWidth(3, 120)

        # améliorer le design du tableau
        
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.table, 4)

        form = QGridLayout()
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(8)

        self.field_name = QLineEdit()
        self.field_name.setPlaceholderText("Nom du champ")
        self.field_name.setMinimumHeight(36)
        self.field_name.setStyleSheet("QLineEdit { padding: 4px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.2); }")

        self.ui_type = QComboBox()
        self.ui_type.addItems(["Texte", "Email", "Téléphone", "Nombre", "Date", "Photo", "Liste"])
        self.ui_type.setMinimumHeight(36)
        self.ui_type.setStyleSheet("QComboBox { padding: 4px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.2); }")

        self.btn_config_list = QPushButton("Configurer la liste")
        self.btn_config_list.clicked.connect(self.open_list_dialog)
        self.btn_config_list.setVisible(False)
        self.btn_config_list.setMinimumHeight(36)
        self.btn_config_list.setStyleSheet("QPushButton { padding: 4px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.2); background: #f0f0f0; }")

        form.addWidget(QLabel("Nom"), 0, 0)
        form.addWidget(self.field_name, 0, 1)
        form.addWidget(QLabel("Type"), 0, 2)
        form.addWidget(self.ui_type, 0, 3)
        form.addWidget(self.btn_config_list, 2, 1)

        layout.addLayout(form, 1)

        actions = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.clicked.connect(self.reset_form)
        btn_cancel.setStyleSheet("QPushButton { background: white; color: black; border: 1px solid rgba(0,0,0,0.2); padding: 6px 12px; border-radius: 6px; } QPushButton:hover { background: rgba(0,0,0,0.06); color: black; }")

        btn_save = QPushButton("Valider")
        btn_save.clicked.connect(self.save_field)
        btn_save.setStyleSheet("QPushButton { background: #000; color: white; padding: 6px 12px; border-radius: 6px; } QPushButton:hover { background: #16a34a; color: white; }")

        actions.addStretch()
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)

        self.load_fields(self.type_combo.currentText())

    def sql_type(self, ui):
        return {
            "Texte": "TEXT",
            "Email": "TEXT",
            "Téléphone": "TEXT",
            "Nombre": "INTEGER",
            "Date": "TEXT",
            "Photo": "TEXT",
            "Liste": "TEXT"
        }[ui]

    def toggle_options(self, ui):
        self.btn_config_list.setVisible(ui == "Liste")

    def open_list_dialog(self):
        dlg = ListOptionsDialog(self.list_options)
        if dlg.exec():
            self.list_options = dlg.get_options()
            # afficher le nombre d'options sur le bouton
            try:
                self.btn_config_list.setText(f"Configurer la liste ({len(self.list_options)})")
            except Exception:
                pass

    def load_fields(self, type_membre):
        self.table.setRowCount(0)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("""
            SELECT id, field_name, ui_type
            FROM schemas WHERE type=?
        """, (type_membre,))

        for fid, name, ui in c.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Numéro automatique (comme Excel) à gauche
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setFlags(item_idx.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_idx)

            # Nom (on stocke l'id réel dans UserRole pour retrouver facilement)
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, fid)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_name)

            # Type
            item_type = QTableWidgetItem(ui)
            item_type.setFlags(item_type.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_type)

            # Actions (boutons) liés à l'id
            self.table.setCellWidget(row, 3, self.action_buttons(fid, row))

        conn.close()

    def action_buttons(self, fid, row):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # icônes standard via QStyle (plus portable que des fichiers PNG)
        style = QApplication.style()
        edit_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        # Le pixmap pour "corbeille" peut varier selon plateforme -> fallback
        try:
            del_icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        except Exception:
            del_icon = QIcon.fromTheme("edit-delete") or QIcon.fromTheme("user-trash") or QIcon()

        # calculer taille d'icône à partir de la hauteur de ligne
        row_h = self.table.rowHeight(row) if row is not None else self.table.verticalHeader().defaultSectionSize()
        icon_px = max(12, row_h - 10)
        size = QSize(icon_px, icon_px)

        def tint(icon: QIcon, size: QSize, color: str) -> QIcon:
            pm = icon.pixmap(size)
            if pm.isNull():
                return QIcon()
            out = QPixmap(pm.size())
            out.fill(Qt.GlobalColor.transparent)
            p = QPainter(out)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.drawPixmap(0, 0, pm)
            # PyQt6 enum names : use CompositionMode_CompositionMode_SourceIn
            try:
                comp_mode = QPainter.CompositionMode.SourceIn
            except Exception:
                comp_mode = QPainter.CompositionMode.CompositionMode_SourceIn
            p.setCompositionMode(comp_mode)
            p.fillRect(out.rect(), QColor(color))
            p.end()
            return QIcon(out)

        l.addStretch()

        # Edit button (teint en vert)
        be = QPushButton()
        edit_col = tint(edit_icon, size, "#16a34a") if not edit_icon.isNull() else edit_icon
        if not edit_col.isNull():
            be.setIcon(edit_col)
            be.setIconSize(size)
        be.setFixedSize(size.width() + 8, size.height() + 8)
        be.setFlat(True)
        be.setToolTip("Modifier")
        be.clicked.connect(lambda _, _id=fid: self.edit_field_by_fid(_id))
        be.setStyleSheet("QPushButton{border:none;background:transparent;} QPushButton:hover{background: rgba(22,163,74,0.08)}")
        l.addWidget(be)

        # Delete button (teint en rouge)
        bd = QPushButton()
        del_col = tint(del_icon, size, "#ef4444") if not del_icon.isNull() else del_icon
        if not del_col.isNull():
            bd.setIcon(del_col)
            bd.setIconSize(size)
        bd.setFixedSize(size.width() + 8, size.height() + 8)
        bd.setFlat(True)
        bd.setToolTip("Supprimer")
        bd.clicked.connect(lambda _, _id=fid: self.delete_field_by_fid(_id))
        bd.setStyleSheet("QPushButton{border:none;background:transparent;} QPushButton:hover{background: rgba(239,68,68,0.08)}")
        l.addWidget(bd)

        l.addStretch()

        return w

    def edit_field_by_fid(self, fid):
        # Remplir le formulaire depuis la BDD pour l'id donné
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT field_name, ui_type, options FROM schemas WHERE id=?", (fid,))
        res = c.fetchone()
        conn.close()
        if not res:
            return
        name, ui, options = res
        self.editing_field_id = fid
        try:
            self.field_name.setText(name)
            self.ui_type.setCurrentText(ui)
        except Exception:
            pass
        # si Liste, charger les options et afficher le compteur
        if ui == "Liste":
            try:
                self.list_options = json.loads(options) if options else []
            except Exception:
                self.list_options = []
            try:
                self.btn_config_list.setVisible(True)
                self.btn_config_list.setText(f"Configurer la liste ({len(self.list_options)})")
            except Exception:
                pass
        else:
            try:
                self.btn_config_list.setVisible(False)
                self.btn_config_list.setText("Configurer la liste")
            except Exception:
                pass

    def delete_field_by_fid(self, fid):
        # Supprimer via l'id fourni
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT field_name FROM schemas WHERE id=?", (fid,))
        row = c.fetchone()
        name = row[0] if row else str(fid)
        if QMessageBox.question(self, "Confirmation", f"Supprimer le champ '{name}' ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            conn.close()
            return
        c.execute("DELETE FROM schemas WHERE id=?", (fid,))
        conn.commit()
        conn.close()
        # resync DB and UI
        sync_membres_table(self.type_combo.currentText())
        self.load_fields(self.type_combo.currentText())
        # refresh any open forms/tables
        for w in QApplication.allWidgets():
            try:
                if isinstance(w, FormView):
                    if w.type_membre:
                        w.build(w.type_membre)
                if isinstance(w, MembresPage):
                    w.change_type(w.current_type)
            except Exception:
                pass

    def save_field(self):
        name_raw = self.field_name.text().strip()
        if not name_raw:
            QMessageBox.warning(self, "Erreur", "Nom du champ obligatoire")
            return

        # sanitize column name (remplacement des espaces)
        name = name_raw.replace(" ", "_").replace('"', '')

        ui = self.ui_type.currentText()
        sql_type = self.sql_type(ui)

        options = None
        if ui == "Liste":
            # si pas configuré, ouvrir automatiquement le dialogue
            if not self.list_options:
                dlg = ListOptionsDialog(self.list_options)
                if dlg.exec():
                    self.list_options = dlg.get_options()
                    try:
                        self.btn_config_list.setText(f"Configurer la liste ({len(self.list_options)})")
                    except Exception:
                        pass
                else:
                    QMessageBox.warning(self, "Erreur", "Configurer la liste")
                    return
            options = json.dumps(self.list_options)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        if self.editing_field_id:
            c.execute("""
                UPDATE schemas
                SET field_name=?, field_type=?, ui_type=?, options=?
                WHERE id=?
            """, (name, sql_type, ui, options, self.editing_field_id))
        else:
            c.execute("""
                INSERT INTO schemas (type, field_name, field_type, ui_type, options)
                VALUES (?, ?, ?, ?, ?)
            """, (self.type_combo.currentText(), name, sql_type, ui, options))

        conn.commit()
        conn.close()

        sync_membres_table(self.type_combo.currentText())
        self.reset_form()
        self.load_fields(self.type_combo.currentText())

        # rebuild forms and refresh membres pages so new field appears immediately
        for w in QApplication.allWidgets():
            try:
                if isinstance(w, FormView):
                    if w.type_membre:
                        w.build(w.type_membre)
                if isinstance(w, MembresPage):
                    w.change_type(w.current_type)
            except Exception:
                pass

    def reset_form(self):
        # remet à zéro le formulaire d'édition/ajout de champ
        self.editing_field_id = None
        try:
            self.field_name.clear()
        except Exception:
            pass
        try:
            self.ui_type.setCurrentIndex(0)
        except Exception:
            pass
        self.list_options = []

#===================== PARAMETRES =====================

class ParametresPage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)   # marges réduites
        root.setSpacing(8)


        # Card principale
        card = QFrame()
        card.setObjectName("param_card")
        card.setMinimumWidth(760)
        card.setMinimumHeight(480)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(8)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        card.setGraphicsEffect(shadow)

        # Styles locaux pour la card / tableau / onglets
        card.setStyleSheet("""
            QFrame#param_card {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.06);
            }
            QTabWidget::pane {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                padding: 8px 14px;
                border-radius: 6px 6px 0 0;
                background: rgba(0,0,0,0.03);
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                font-weight: bold;
            }
            QTableWidget {
                background: #eefafb;
                gridline-color: rgba(0,0,0,0.15);
            }
            QHeaderView::section {
                background: #bfeff7;
                padding: 8px;
                border: 1px solid rgba(0,0,0,0.08);
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QLineEdit, QComboBox {
                min-height: 36px;
                border-radius: 8px;
                padding: 6px 10px;
                border: 1px solid rgba(0,0,0,0.12);
                background: white;
            }
            QPushButton[role="secondary"] {
                background: transparent;
                color: #222;
                border: 1px solid rgba(0,0,0,0.12);
                padding: 8px 14px;
                border-radius: 8px;
            }
            QPushButton {
                background: #000;
                color: white;
                padding: 8px 14px;
                border-radius: 8px;
            }
            QScrollBar:vertical {
            width: 10px;
            background: transparent;
            margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: #622599;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0041a0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
            
        """)

        # Onglets
        tabs = QTabWidget()
        tabs.setMinimumHeight(420)

        # -- Onglet Structure des tables --
        tab_struct = QWidget()
        tab_layout = QVBoxLayout(tab_struct)
        tab_layout.setContentsMargins(0, 0, 0, 0)  # supprimer marges autour du contenu
        tab_layout.setSpacing(4)

        try:
            self.structure = StructureTablesPage()
            scroll = QScrollArea()
            # assurer direction normale et scrollbar visible à droite
            scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.structure.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            scroll.setWidgetResizable(True)
            scroll.setWidget(self.structure)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setViewportMargins(0, 0, 0, 0)
            # style de scrollbar plus visible, contraste et largeur accrue
            scroll.setStyleSheet("""
                QScrollArea { border: none; }
                QScrollBar:vertical { width: 12px; background: rgba(0,0,0,0.03); margin: 4px; }
                QScrollBar::handle:vertical { background: #622599; border-radius: 6px; min-height: 30px; }
                QScrollBar::handle:vertical:hover { background: #0041a0; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
                QScrollArea > QWidget { margin:0; padding:0; }
            """)
            tab_layout.addWidget(scroll)
        except Exception as e:
            tb = traceback.format_exc()
            with open('crash.log', 'a', encoding='utf-8') as f:
                f.write(tb + "\n")
            lbl = QLabel("Erreur initialisation module. Voir crash.log")
            lbl.setStyleSheet("color: red;")
            tab_layout.addWidget(lbl)

        # -- Onglet Utilisateurs (placeholder) --
        tab_users = QWidget()
        users_layout = QVBoxLayout(tab_users)
        users_layout.setContentsMargins(12, 12, 12, 12)
        users_layout.addWidget(QLabel("Gestion des utilisateurs — à implémenter"))
        users_layout.addStretch()

        # -- Onglet Thème (placeholder) --
        tab_theme = QWidget()
        theme_layout = QVBoxLayout(tab_theme)
        theme_layout.setContentsMargins(12, 12, 12, 12)
        theme_layout.addWidget(QLabel("Personnalisation du thème"))
        theme_layout.addStretch()

        tabs.addTab(tab_struct, "Structure des tables")
        tabs.addTab(tab_users, "Utilisateurs")
        tabs.addTab(tab_theme, "Thème")

        card_layout.addWidget(tabs)
        root.addWidget(card)

#===================== MAIN =====================

def main():
    __init_db__()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    stacked = QStackedWidget()
    stacked.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    login = LoginPage(stacked)
    dashboard = Dashboard(stacked)
    membres = MembresPage()
    stats = StatsPage()
    params = ParametresPage()

    stacked.addWidget(login)      # index 0
    stacked.addWidget(dashboard)  # index 1
    stacked.addWidget(membres)    # index 2
    stacked.addWidget(stats)      # index 3
    stacked.addWidget(params)     # index 4

    main_win = QMainWindow()
    main_win.setCentralWidget(stacked)
    main_win.setWindowTitle("BD DIANA")
    main_win.showMaximized()
    print("Application started - main window shown")

    sys.exit(app.exec())

if __name__== "__main__":
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        with open('crash.log', 'w', encoding='utf-8') as f:
            f.write(tb)
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, 'Erreur fatale', f"Une erreur s'est produite. Voir crash.log.\n{str(e)}")
        sys.exit(1)