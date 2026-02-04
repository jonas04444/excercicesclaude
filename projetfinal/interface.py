"""
Interface de gestion des services de bus avec timeline
Fichier: interface.py

Utilisation:
    python interface.py

Nécessite: PyQt6, import_csv.py dans le même dossier
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QPushButton, QLabel, QTimeEdit, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QSplitter, QListWidget,
    QTextEdit
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter

# Import du module CSV
from import_csv import DialogImportCSV

# ==================== CONFIGURATION ====================

HEURE_DEBUT = 4  # Heure de début de la timeline
HEURE_FIN = 24  # Heure de fin de la timeline
HAUTEUR_SERVICE = 50  # Hauteur d'une ligne de service
MARGE_GAUCHE = 100  # Marge pour les noms de services
MARGE_HAUT = 40  # Marge pour les heures
PAUSE_MIN = 5 / 60  # Pause minimum entre voyages (5 min)


# ==================== CLASSE VOYAGE GRAPHIQUE ====================

class VoyageGraphique(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_data, y_pos, pixels_par_heure, parent_view):
        self.voyage_data = voyage_data
        self.parent_view = parent_view

        # Position et taille
        heure_debut = voyage_data.get('heure_depart', 8)
        duree_heures = voyage_data.get('duree_minutes', 60) / 60

        x = MARGE_GAUCHE + (heure_debut - HEURE_DEBUT) * pixels_par_heure
        largeur = max(duree_heures * pixels_par_heure, 20)
        hauteur = HAUTEUR_SERVICE - 10

        super().__init__(x, y_pos + 5, largeur, hauteur)

        # Couleur
        couleur = QColor(voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        self.setPen(QPen(couleur.darker(120), 2))

        # Texte
        nom = voyage_data.get('nom', 'Voyage')
        self.text_item = QGraphicsTextItem(nom, self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.text_item.setFont(QFont("Arial", 8, QFont.Weight.Bold))

        # Centrer le texte
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            (largeur - text_rect.width()) / 2,
            (hauteur - text_rect.height()) / 2
        )

        # Interactivité
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Tooltip
        self.setToolTip(
            f"{nom}\n"
            f"Ligne: {voyage_data.get('numero_ligne', '-')}\n"
            f"De: {voyage_data.get('arret_depart', '-')}\n"
            f"À: {voyage_data.get('arret_arrivee', '-')}\n"
            f"Heure: {voyage_data.get('heure_debut_str', '-')} - {voyage_data.get('heure_fin_str', '-')}"
        )

    def hoverEnterEvent(self, event):
        couleur = QColor(self.voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(couleur.lighter(120)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        couleur = QColor(self.voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.parent_view.on_voyage_clicked(self)
        super().mousePressEvent(event)


# ==================== VUE TIMELINE ====================

class TimelineView(QGraphicsView):
    """Vue principale de la timeline"""

    voyage_selectionne = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.services = []  # Liste des services
        self.pixels_par_heure = 80
        self.voyage_actuel = None

        # Configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumHeight(200)

    def redessiner(self):
        """Redessine toute la timeline"""
        self.scene.clear()

        if not self.services:
            text = self.scene.addText("Aucun service créé. Utilisez le panneau de gauche pour ajouter des services.")
            text.setDefaultTextColor(QColor('#999'))
            return

        # Dimensions
        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * self.pixels_par_heure + 50
        hauteur = MARGE_HAUT + len(self.services) * HAUTEUR_SERVICE + 50
        self.scene.setSceneRect(0, 0, largeur, hauteur)

        # Grille horaire
        self._dessiner_grille()

        # Services et voyages
        for i, service in enumerate(self.services):
            y = MARGE_HAUT + i * HAUTEUR_SERVICE
            self._dessiner_service(service, y, i)

    def _dessiner_grille(self):
        """Dessine la grille des heures"""
        pen = QPen(QColor('#e0e0e0'), 1, Qt.PenStyle.DashLine)
        hauteur = MARGE_HAUT + len(self.services) * HAUTEUR_SERVICE

        for heure in range(HEURE_DEBUT, HEURE_FIN + 1):
            x = MARGE_GAUCHE + (heure - HEURE_DEBUT) * self.pixels_par_heure

            # Ligne verticale
            self.scene.addLine(x, MARGE_HAUT, x, hauteur, pen)

            # Label heure
            text = self.scene.addText(f"{heure}:00")
            text.setDefaultTextColor(QColor('#666'))
            text.setFont(QFont("Arial", 8))
            text.setPos(x - 15, 5)

    def _dessiner_service(self, service, y, index):
        """Dessine un service avec ses voyages"""
        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * self.pixels_par_heure

        # Fond alternée
        couleur_fond = QColor('#f8f9fa') if index % 2 == 0 else QColor('#ffffff')
        self.scene.addRect(0, y, largeur, HAUTEUR_SERVICE,
                           QPen(Qt.PenStyle.NoPen), QBrush(couleur_fond))

        # Nom du service
        nom = service.get('nom', f'Service {index + 1}')
        text = self.scene.addText(nom)
        text.setDefaultTextColor(QColor('#333'))
        text.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        text.setPos(5, y + 15)

        # Zone horaire du service
        h_debut = service.get('heure_debut', HEURE_DEBUT)
        h_fin = service.get('heure_fin', HEURE_FIN)

        x_debut = MARGE_GAUCHE + (h_debut - HEURE_DEBUT) * self.pixels_par_heure
        x_fin = MARGE_GAUCHE + (h_fin - HEURE_DEBUT) * self.pixels_par_heure

        couleur_zone = QColor(service.get('couleur', '#e3f2fd'))
        couleur_zone.setAlpha(80)
        self.scene.addRect(x_debut, y + 2, x_fin - x_debut, HAUTEUR_SERVICE - 4,
                           QPen(QColor('#90caf9'), 1), QBrush(couleur_zone))

        # Voyages
        for voyage in service.get('voyages', []):
            item = VoyageGraphique(voyage, y, self.pixels_par_heure, self)
            self.scene.addItem(item)

    def on_voyage_clicked(self, item):
        """Quand on clique sur un voyage"""
        # Désélectionner l'ancien
        if self.voyage_actuel:
            old_color = QColor(self.voyage_actuel.voyage_data.get('couleur', '#3498db'))
            self.voyage_actuel.setPen(QPen(old_color.darker(120), 2))

        # Sélectionner le nouveau
        self.voyage_actuel = item
        item.setPen(QPen(QColor('#e74c3c'), 3))

        self.voyage_selectionne.emit(item.voyage_data)

    def ajouter_service(self, service_data):
        """Ajoute un service"""
        self.services.append(service_data)
        self.redessiner()

    def supprimer_service(self, index):
        """Supprime un service"""
        if 0 <= index < len(self.services):
            del self.services[index]
            self.redessiner()


# ==================== PANNEAU DE GAUCHE ====================

class PanneauGauche(QFrame):
    """Panneau de gestion des voyages et services"""

    def __init__(self, timeline, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.voyages_importes = []

        self.setFixedWidth(500)
        self.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ===== SECTION IMPORT =====
        titre_import = QLabel("📂 VOYAGES IMPORTÉS")
        titre_import.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_import.setStyleSheet("background-color: #3498db; color: white; padding: 8px; border-radius: 3px;")
        layout.addWidget(titre_import)

        btn_import = QPushButton("📥 Importer depuis CSV")
        btn_import.setStyleSheet("background-color: #2980b9; color: white; padding: 10px;")
        btn_import.clicked.connect(self.importer_csv)
        layout.addWidget(btn_import)

        # Tableau voyages importés
        self.table_importes = QTableWidget()
        self.table_importes.setColumnCount(7)
        self.table_importes.setHorizontalHeaderLabels(['V', 'Ligne', 'Voy', 'Début', 'Fin', 'De', 'À'])
        self.table_importes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_importes.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_importes.setMaximumHeight(200)
        self.table_importes.setAlternatingRowColors(True)

        # Largeurs colonnes
        self.table_importes.setColumnWidth(0, 25)
        self.table_importes.setColumnWidth(1, 50)
        self.table_importes.setColumnWidth(2, 40)
        self.table_importes.setColumnWidth(3, 50)
        self.table_importes.setColumnWidth(4, 50)
        self.table_importes.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table_importes.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table_importes)

        # ===== SECTION SERVICES =====
        titre_services = QLabel("🚌 SERVICES")
        titre_services.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_services.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; border-radius: 3px;")
        layout.addWidget(titre_services)

        # Boutons services
        btn_row = QHBoxLayout()

        btn_add = QPushButton("➕ Ajouter")
        btn_add.clicked.connect(self.ajouter_service)
        btn_row.addWidget(btn_add)

        btn_del = QPushButton("🗑️ Supprimer")
        btn_del.clicked.connect(self.supprimer_service)
        btn_row.addWidget(btn_del)

        layout.addLayout(btn_row)

        # Combo services
        self.combo_services = QComboBox()
        self.combo_services.currentIndexChanged.connect(self.on_service_change)
        layout.addWidget(self.combo_services)

        # Tableau voyages du service
        self.table_service = QTableWidget()
        self.table_service.setColumnCount(6)
        self.table_service.setHorizontalHeaderLabels(['Ligne', 'Voy', 'Début', 'Fin', 'De', 'À'])
        self.table_service.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_service.setMaximumHeight(180)
        self.table_service.setAlternatingRowColors(True)
        layout.addWidget(self.table_service)

        # Boutons assignation
        btn_assign_row = QHBoxLayout()

        btn_ajouter = QPushButton("⬇️ Ajouter au service")
        btn_ajouter.setStyleSheet("background-color: #27ae60; color: white;")
        btn_ajouter.clicked.connect(self.ajouter_voyage_au_service)
        btn_assign_row.addWidget(btn_ajouter)

        btn_retirer = QPushButton("⬆️ Retirer du service")
        btn_retirer.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_retirer.clicked.connect(self.retirer_voyage_du_service)
        btn_assign_row.addWidget(btn_retirer)

        layout.addLayout(btn_assign_row)

        layout.addStretch()

    def importer_csv(self):
        """Ouvre le dialogue d'import CSV"""
        dialog = DialogImportCSV(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nouveaux = dialog.get_voyages_importes()

            # Assigner des IDs uniques
            for v in nouveaux:
                v['id'] = id(v)

            self.voyages_importes.extend(nouveaux)
            self.refresh_table_importes()

            QMessageBox.information(self, "Import réussi", f"{len(nouveaux)} voyage(s) importé(s)")

    def refresh_table_importes(self):
        """Rafraîchit la table des voyages importés"""
        self.table_importes.setRowCount(len(self.voyages_importes))

        for row, v in enumerate(self.voyages_importes):
            # Indicateur assigné
            if v.get('assigne'):
                item_v = QTableWidgetItem('✓')
                item_v.setForeground(QColor('#27ae60'))
            else:
                item_v = QTableWidgetItem('')
            item_v.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_importes.setItem(row, 0, item_v)

            # Données
            valeurs = [
                v.get('numero_ligne', ''),
                v.get('numero_voyage', ''),
                v.get('heure_debut_str', ''),
                v.get('heure_fin_str', ''),
                v.get('arret_depart', ''),
                v.get('arret_arrivee', '')
            ]

            for col, val in enumerate(valeurs):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_importes.setItem(row, col + 1, item)

    def refresh_combo_services(self):
        """Rafraîchit le combo des services"""
        self.combo_services.clear()
        for i, s in enumerate(self.timeline.services):
            self.combo_services.addItem(s.get('nom', f'Service {i + 1}'), i)

    def on_service_change(self):
        """Met à jour la table du service sélectionné"""
        idx = self.combo_services.currentData()
        if idx is None or idx >= len(self.timeline.services):
            self.table_service.setRowCount(0)
            return

        service = self.timeline.services[idx]
        voyages = service.get('voyages', [])

        self.table_service.setRowCount(len(voyages))

        for row, v in enumerate(voyages):
            valeurs = [
                v.get('numero_ligne', ''),
                v.get('numero_voyage', ''),
                v.get('heure_debut_str', ''),
                v.get('heure_fin_str', ''),
                v.get('arret_depart', ''),
                v.get('arret_arrivee', '')
            ]

            for col, val in enumerate(valeurs):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_service.setItem(row, col, item)

    def ajouter_service(self):
        """Ajoute un nouveau service"""
        dialog = DialogAjoutService(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.timeline.ajouter_service(data)
            self.refresh_combo_services()

    def supprimer_service(self):
        """Supprime le service sélectionné"""
        idx = self.combo_services.currentData()
        if idx is not None and idx < len(self.timeline.services):
            # Désassigner les voyages
            service = self.timeline.services[idx]
            for v in service.get('voyages', []):
                orig_id = v.get('original_id')
                if orig_id:
                    for vi in self.voyages_importes:
                        if vi.get('id') == orig_id:
                            vi['assigne'] = False
                            vi['service_assigne'] = None

            self.timeline.supprimer_service(idx)
            self.refresh_combo_services()
            self.refresh_table_importes()

    def ajouter_voyage_au_service(self):
        """Ajoute le voyage sélectionné au service"""
        # Vérifier service
        idx_service = self.combo_services.currentData()
        if idx_service is None or idx_service >= len(self.timeline.services):
            QMessageBox.warning(self, "Attention", "Sélectionnez un service")
            return

        # Vérifier voyage
        selection = self.table_importes.selectedItems()
        if not selection:
            QMessageBox.warning(self, "Attention", "Sélectionnez un voyage")
            return

        row = selection[0].row()
        if row >= len(self.voyages_importes):
            return

        voyage = self.voyages_importes[row]

        # Déjà assigné ?
        if voyage.get('assigne'):
            QMessageBox.warning(self, "Déjà assigné",
                                f"Ce voyage est déjà assigné à {voyage.get('service_assigne', '')}")
            return

        service = self.timeline.services[idx_service]

        # Vérifier limites horaires
        h_debut = voyage.get('heure_depart', 0)
        h_fin = h_debut + voyage.get('duree_minutes', 60) / 60

        if h_debut < service.get('heure_debut', 0) or h_fin > service.get('heure_fin', 24):
            QMessageBox.warning(self, "Hors limites",
                                f"Le voyage est hors des limites du service")
            return

        # Vérifier chevauchements
        for v_exist in service.get('voyages', []):
            ve_debut = v_exist.get('heure_depart', 0)
            ve_fin = ve_debut + v_exist.get('duree_minutes', 60) / 60

            if not (h_fin + PAUSE_MIN <= ve_debut or h_debut >= ve_fin + PAUSE_MIN):
                QMessageBox.warning(self, "Chevauchement",
                                    f"Ce voyage chevauche {v_exist.get('nom', '')}")
                return

        # Ajouter
        voyage_copie = voyage.copy()
        voyage_copie['id'] = id(voyage_copie)
        voyage_copie['original_id'] = voyage.get('id')

        if 'voyages' not in service:
            service['voyages'] = []
        service['voyages'].append(voyage_copie)

        voyage['assigne'] = True
        voyage['service_assigne'] = service.get('nom', '')

        self.timeline.redessiner()
        self.refresh_table_importes()
        self.on_service_change()

    def retirer_voyage_du_service(self):
        """Retire le voyage sélectionné du service"""
        idx_service = self.combo_services.currentData()
        if idx_service is None or idx_service >= len(self.timeline.services):
            return

        selection = self.table_service.selectedItems()
        if not selection:
            QMessageBox.warning(self, "Attention", "Sélectionnez un voyage")
            return

        row = selection[0].row()
        service = self.timeline.services[idx_service]
        voyages = service.get('voyages', [])

        if row >= len(voyages):
            return

        voyage = voyages[row]
        orig_id = voyage.get('original_id')

        # Retirer
        del voyages[row]

        # Désassigner
        if orig_id:
            for v in self.voyages_importes:
                if v.get('id') == orig_id:
                    v['assigne'] = False
                    v['service_assigne'] = None
                    break

        self.timeline.redessiner()
        self.refresh_table_importes()
        self.on_service_change()


# ==================== DIALOGUE AJOUT SERVICE ====================

class DialogAjoutService(QDialog):
    """Dialogue pour créer un service"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau service")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Nom
        self.edit_nom = QLineEdit()
        self.edit_nom.setPlaceholderText("Ex: Service 1")
        layout.addRow("Nom:", self.edit_nom)

        # Heure début
        self.time_debut = QTimeEdit()
        self.time_debut.setTime(QTime(6, 0))
        self.time_debut.setDisplayFormat("HH:mm")
        layout.addRow("Heure début:", self.time_debut)

        # Heure fin
        self.time_fin = QTimeEdit()
        self.time_fin.setTime(QTime(14, 0))
        self.time_fin.setDisplayFormat("HH:mm")
        layout.addRow("Heure fin:", self.time_fin)

        # Couleur
        self.combo_couleur = QComboBox()
        couleurs = [
            ("#e3f2fd", "Bleu"),
            ("#e8f5e9", "Vert"),
            ("#fff3e0", "Orange"),
            ("#fce4ec", "Rose"),
            ("#f3e5f5", "Violet"),
        ]
        for code, nom in couleurs:
            self.combo_couleur.addItem(nom, code)
        layout.addRow("Couleur:", self.combo_couleur)

        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        """Retourne les données du service"""
        t_debut = self.time_debut.time()
        t_fin = self.time_fin.time()

        return {
            'nom': self.edit_nom.text() or f"Service {id(self) % 100}",
            'heure_debut': t_debut.hour() + t_debut.minute() / 60,
            'heure_fin': t_fin.hour() + t_fin.minute() / 60,
            'couleur': self.combo_couleur.currentData(),
            'voyages': []
        }


# ==================== PANNEAU DÉTAILS ====================

class PanneauDetails(QFrame):
    """Panneau affichant les détails d'un voyage"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)

        titre = QLabel("📋 Détails")
        titre.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(titre)

        # Labels
        self.labels = {}
        champs = ['Ligne', 'Voyage', 'Départ', 'Arrivée', 'Heure', 'Durée']

        for champ in champs:
            row = QHBoxLayout()
            lbl_nom = QLabel(f"{champ}:")
            lbl_nom.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl_nom.setFixedWidth(60)
            row.addWidget(lbl_nom)

            lbl_val = QLabel("-")
            row.addWidget(lbl_val)

            self.labels[champ] = lbl_val
            layout.addLayout(row)

        layout.addStretch()

        self.msg = QLabel("Cliquez sur un voyage\npour voir ses détails")
        self.msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg.setStyleSheet("color: #999; padding: 20px;")
        layout.addWidget(self.msg)

    def afficher(self, data):
        """Affiche les détails d'un voyage"""
        self.msg.hide()

        self.labels['Ligne'].setText(str(data.get('numero_ligne', '-')))
        self.labels['Voyage'].setText(str(data.get('numero_voyage', '-')))
        self.labels['Départ'].setText(data.get('arret_depart', '-'))
        self.labels['Arrivée'].setText(data.get('arret_arrivee', '-'))
        self.labels['Heure'].setText(f"{data.get('heure_debut_str', '-')} - {data.get('heure_fin_str', '-')}")
        self.labels['Durée'].setText(f"{data.get('duree_minutes', 0):.0f} min")

    def effacer(self):
        """Efface les détails"""
        for lbl in self.labels.values():
            lbl.setText("-")
        self.msg.show()


# ==================== FENÊTRE PRINCIPALE ====================

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Gestion des Services de Bus")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Barre d'outils
        toolbar = QHBoxLayout()

        self.btn_effacer = QPushButton("🗑️ Tout effacer")
        self.btn_effacer.clicked.connect(self.effacer_tout)
        toolbar.addWidget(self.btn_effacer)

        toolbar.addStretch()

        self.label_info = QLabel("Bienvenue ! Importez des voyages et créez des services.")
        self.label_info.setStyleSheet("color: #666;")
        toolbar.addWidget(self.label_info)

        main_layout.addLayout(toolbar)

        # Contenu
        content = QHBoxLayout()

        # Timeline
        self.timeline = TimelineView()
        self.timeline.voyage_selectionne.connect(self.on_voyage_selected)

        # Panneau gauche
        self.panneau_gauche = PanneauGauche(self.timeline)
        content.addWidget(self.panneau_gauche)

        # Timeline
        content.addWidget(self.timeline, stretch=1)

        # Panneau détails
        self.panneau_details = PanneauDetails()
        content.addWidget(self.panneau_details)

        main_layout.addLayout(content)

    def on_voyage_selected(self, data):
        """Quand un voyage est sélectionné"""
        self.panneau_details.afficher(data)
        self.label_info.setText(f"Voyage sélectionné: {data.get('nom', '-')}")

    def effacer_tout(self):
        """Efface toutes les données"""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Êtes-vous sûr de vouloir tout effacer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.timeline.services = []
            self.timeline.redessiner()
            self.panneau_gauche.voyages_importes = []
            self.panneau_gauche.refresh_table_importes()
            self.panneau_gauche.refresh_combo_services()
            self.panneau_details.effacer()
            self.label_info.setText("Données effacées")


# ==================== MAIN ====================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()