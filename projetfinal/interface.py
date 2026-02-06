"""
Interface de gestion des services de bus avec timeline
Utilise les classes de objet.py (voyage, service_agent, hlp, proposition)
"""

import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QPushButton, QLabel, QTimeEdit, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter

# Import des classes métier
from objet import voyage, service_agent, hlp, proposition
from import_csv import DialogImportCSV


# ==================== CONFIGURATION ====================

HEURE_DEBUT = 4       # Heure de début de la timeline (en heures)
HEURE_FIN = 24        # Heure de fin de la timeline
HAUTEUR_SERVICE = 50  # Hauteur d'une ligne de service en pixels
MARGE_GAUCHE = 100    # Marge pour les noms de services
MARGE_HAUT = 40       # Marge pour les heures
PAUSE_MIN = 5         # Pause minimum entre voyages (en minutes)


# ==================== CLASSE VOYAGE GRAPHIQUE ====================

class VoyageGraphique(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_obj, y_pos, pixels_par_heure, parent_view):
        self.voyage_obj = voyage_obj
        self.parent_view = parent_view

        # Position et taille (hdebut et hfin sont en MINUTES)
        heure_debut = voyage_obj.hdebut / 60
        heure_fin = voyage_obj.hfin / 60
        duree_heures = heure_fin - heure_debut

        x = MARGE_GAUCHE + (heure_debut - HEURE_DEBUT) * pixels_par_heure
        largeur = duree_heures * pixels_par_heure
        hauteur = HAUTEUR_SERVICE - 10

        super().__init__(x, y_pos + 5, largeur, hauteur)

        # Couleur
        couleur = QColor(getattr(voyage_obj, 'couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        self.setPen(QPen(couleur.darker(120), 2))

        # Texte du voyage
        nom = f"{voyage_obj.num_ligne}-{voyage_obj.num_voyage}"
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
            f"Ligne: {voyage_obj.num_ligne}\n"
            f"De: {voyage_obj.arret_debut}\n"
            f"À: {voyage_obj.arret_fin}\n"
            f"Heure: {voyage.minutes_to_time(voyage_obj.hdebut)} - {voyage.minutes_to_time(voyage_obj.hfin)}"
        )

    def hoverEnterEvent(self, event):
        couleur = QColor(getattr(self.voyage_obj, 'couleur', '#3498db'))
        self.setBrush(QBrush(couleur.lighter(120)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        couleur = QColor(getattr(self.voyage_obj, 'couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.parent_view.on_voyage_clicked(self)
        super().mousePressEvent(event)


# ==================== VUE TIMELINE ====================

class TimelineView(QGraphicsView):
    """Vue principale de la timeline"""

    voyage_selectionne = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.services = []
        self.pixels_par_heure = 80
        self.voyage_actuel = None

        # Configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumHeight(200)

        # Fond sombre par défaut
        self.setStyleSheet("background-color: #2c3e50;")

    def redessiner(self):
        """Redessine toute la timeline"""
        self.scene.clear()

        if not self.services:
            text = self.scene.addText("Aucun service créé. Utilisez le panneau de gauche pour ajouter des services.")
            text.setDefaultTextColor(QColor('#ecf0f1'))
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
        """Dessine la grille des heures avec lignes pointillées rouges"""
        hauteur_totale = MARGE_HAUT + len(self.services) * HAUTEUR_SERVICE
        largeur_totale = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * self.pixels_par_heure

        # Lignes verticales pour chaque heure
        for heure in range(HEURE_DEBUT, HEURE_FIN + 1):
            x = MARGE_GAUCHE + (heure - HEURE_DEBUT) * self.pixels_par_heure

            # Graduation en haut
            ligne_grad = self.scene.addLine(x, MARGE_HAUT - 10, x, MARGE_HAUT)
            ligne_grad.setPen(QPen(QColor('#bdc3c7'), 1))

            # Label de l'heure
            heure_affichee = heure if heure < 24 else 0
            label = QGraphicsTextItem(f"{heure_affichee:02d}h")
            label.setDefaultTextColor(QColor('#ecf0f1'))
            label.setFont(QFont("Arial", 8))
            label.setPos(x - 12, MARGE_HAUT - 30)
            self.scene.addItem(label)

            # Ligne verticale en pointillés ROUGES sur toute la hauteur
            ligne_guide = self.scene.addLine(x, MARGE_HAUT, x, hauteur_totale)
            pen = QPen(QColor('#e74c3c'), 2, Qt.PenStyle.DotLine)  # Rouge, plus épais
            pen.setDashPattern([1, 4])  # Points courts, grands espaces
            ligne_guide.setPen(pen)
            ligne_guide.setZValue(1)

    def _dessiner_service(self, service, y, index):
        """Dessine un service_agent avec ses voyages"""
        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * self.pixels_par_heure

        # Fond alternée avec couleurs sombres
        couleur_fond = QColor('#34495e') if index % 2 == 0 else QColor('#3d566e')
        self.scene.addRect(0, y, largeur, HAUTEUR_SERVICE,
                           QPen(Qt.PenStyle.NoPen), QBrush(couleur_fond))

        # Nom du service
        nom = f"Service {service.num_service}" if service.num_service else f"Service {index + 1}"
        text = self.scene.addText(nom)
        text.setDefaultTextColor(QColor('#ecf0f1'))
        text.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        text.setPos(5, y + 15)

        # Zone horaire du service
        if service.heure_debut is not None and service.heure_fin is not None:
            h_debut = service.heure_debut / 60
            h_fin = service.heure_fin / 60

            x_debut = MARGE_GAUCHE + (h_debut - HEURE_DEBUT) * self.pixels_par_heure
            x_fin = MARGE_GAUCHE + (h_fin - HEURE_DEBUT) * self.pixels_par_heure

            couleur_zone = QColor(getattr(service, 'couleur', '#e3f2fd'))
            couleur_zone.setAlpha(100)
            self.scene.addRect(x_debut, y + 2, x_fin - x_debut, HAUTEUR_SERVICE - 4,
                               QPen(QColor('#90caf9'), 1), QBrush(couleur_zone))

        # Voyages du service
        for voy in service.get_voyages():
            item = VoyageGraphique(voy, y, self.pixels_par_heure, self)
            self.scene.addItem(item)

    def on_voyage_clicked(self, item):
        """Quand on clique sur un voyage"""
        if self.voyage_actuel:
            old_color = QColor(getattr(self.voyage_actuel.voyage_obj, 'couleur', '#3498db'))
            self.voyage_actuel.setPen(QPen(old_color.darker(120), 2))

        self.voyage_actuel = item
        item.setPen(QPen(QColor('#e74c3c'), 3))
        self.voyage_selectionne.emit(item.voyage_obj)

    def ajouter_service(self, service):
        """Ajoute un service_agent EN HAUT de la liste"""
        self.services.insert(0, service)  # Insert au début
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

        btn_row = QHBoxLayout()

        btn_add = QPushButton("➕ Ajouter")
        btn_add.clicked.connect(self.ajouter_service)
        btn_row.addWidget(btn_add)

        btn_del = QPushButton("🗑️ Supprimer")
        btn_del.clicked.connect(self.supprimer_service)
        btn_row.addWidget(btn_del)

        layout.addLayout(btn_row)

        self.combo_services = QComboBox()
        self.combo_services.currentIndexChanged.connect(self.on_service_change)
        layout.addWidget(self.combo_services)

        self.table_service = QTableWidget()
        self.table_service.setColumnCount(6)
        self.table_service.setHorizontalHeaderLabels(['Ligne', 'Voy', 'Début', 'Fin', 'De', 'À'])
        self.table_service.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_service.setMaximumHeight(180)
        self.table_service.setAlternatingRowColors(True)
        layout.addWidget(self.table_service)

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
        dialog = DialogImportCSV(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            donnees = dialog.get_voyages_importes()

            for d in donnees:
                try:
                    voy = voyage(
                        num_ligne=d.get('numero_ligne', ''),
                        num_voyage=d.get('numero_voyage', ''),
                        arret_debut=d.get('arret_depart', ''),
                        arret_fin=d.get('arret_arrivee', ''),
                        heure_debut=d.get('heure_debut_str', '00:00'),
                        heure_fin=d.get('heure_fin_str', '00:00'),
                        js_srv=d.get('js_srv', '')
                    )
                    voy.couleur = '#3498db'
                    voy.assigne = False
                    voy.service_assigne = None
                    self.voyages_importes.append(voy)
                except Exception as e:
                    print(f"Erreur création voyage: {e}")

            self.refresh_table_importes()
            QMessageBox.information(self, "Import réussi", f"{len(donnees)} voyage(s) importé(s)")

    def refresh_table_importes(self):
        self.table_importes.setRowCount(len(self.voyages_importes))

        for row, voy in enumerate(self.voyages_importes):
            if getattr(voy, 'assigne', False):
                item_v = QTableWidgetItem('✓')
                item_v.setForeground(QColor('#27ae60'))
            else:
                item_v = QTableWidgetItem('')
            item_v.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_importes.setItem(row, 0, item_v)

            valeurs = [
                voy.num_ligne,
                voy.num_voyage,
                voyage.minutes_to_time(voy.hdebut),
                voyage.minutes_to_time(voy.hfin),
                voy.arret_debut,
                voy.arret_fin
            ]

            for col, val in enumerate(valeurs):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_importes.setItem(row, col + 1, item)

    def refresh_combo_services(self):
        self.combo_services.clear()
        for i, s in enumerate(self.timeline.services):
            nom = f"Service {s.num_service}" if s.num_service else f"Service {i + 1}"
            self.combo_services.addItem(nom, i)

    def on_service_change(self):
        try:
            idx = self.combo_services.currentData()
            if idx is None or idx >= len(self.timeline.services):
                self.table_service.setRowCount(0)
                return

            service = self.timeline.services[idx]
            voyages_list = service.get_voyages()

            self.table_service.setRowCount(len(voyages_list))

            for row, voy in enumerate(voyages_list):
                if voy is None:
                    continue

                valeurs = [
                    voy.num_ligne,
                    voy.num_voyage,
                    voyage.minutes_to_time(voy.hdebut),
                    voyage.minutes_to_time(voy.hfin),
                    voy.arret_debut,
                    voy.arret_fin
                ]

                for col, val in enumerate(valeurs):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_service.setItem(row, col, item)

        except Exception as e:
            print(f"❌ Erreur on_service_change: {e}")
            import traceback
            traceback.print_exc()

    def ajouter_service(self):
        dialog = DialogAjoutService(len(self.timeline.services) + 1, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service = dialog.get_service()
            self.timeline.ajouter_service(service)
            self.refresh_combo_services()

    def supprimer_service(self):
        idx = self.combo_services.currentData()
        if idx is not None and idx < len(self.timeline.services):
            service = self.timeline.services[idx]

            for voy in service.get_voyages():
                for v_imp in self.voyages_importes:
                    if (v_imp.num_ligne == voy.num_ligne and
                        v_imp.num_voyage == voy.num_voyage and
                        v_imp.hdebut == voy.hdebut):
                        v_imp.assigne = False
                        v_imp.service_assigne = None
                        break

            self.timeline.supprimer_service(idx)
            self.refresh_combo_services()
            self.refresh_table_importes()

    def ajouter_voyage_au_service(self):
        try:
            idx_service = self.combo_services.currentData()
            if idx_service is None or idx_service >= len(self.timeline.services):
                QMessageBox.warning(self, "Attention", "Sélectionnez un service")
                return

            selection = self.table_importes.selectedItems()
            if not selection:
                QMessageBox.warning(self, "Attention", "Sélectionnez un voyage")
                return

            row = selection[0].row()
            if row >= len(self.voyages_importes):
                return

            voy = self.voyages_importes[row]

            if voy is None:
                QMessageBox.warning(self, "Erreur", "Voyage invalide")
                return

            if getattr(voy, 'assigne', False):
                QMessageBox.warning(self, "Déjà assigné",
                                    f"Ce voyage est déjà assigné à {getattr(voy, 'service_assigne', '')}")
                return

            service = self.timeline.services[idx_service]

            if service.heure_debut is not None and service.heure_fin is not None:
                if voy.hdebut < service.heure_debut or voy.hfin > service.heure_fin:
                    QMessageBox.warning(self, "Hors limites",
                                        f"Le voyage est hors des limites du service")
                    return

            for v_exist in service.get_voyages():
                if not (voy.hfin + PAUSE_MIN <= v_exist.hdebut or voy.hdebut >= v_exist.hfin + PAUSE_MIN):
                    QMessageBox.warning(self, "Chevauchement",
                                        f"Ce voyage chevauche {v_exist.num_ligne}-{v_exist.num_voyage}")
                    return

            service.voyages.append(voy)

            voy.assigne = True
            nom_service = f"Service {service.num_service}" if service.num_service else f"Service {idx_service + 1}"
            voy.service_assigne = nom_service

            self.timeline.redessiner()
            self.refresh_table_importes()
            self.on_service_change()

        except Exception as e:
            print(f"❌ Erreur ajouter_voyage_au_service: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")

    def retirer_voyage_du_service(self):
        try:
            idx_service = self.combo_services.currentData()
            if idx_service is None or idx_service >= len(self.timeline.services):
                return

            selection = self.table_service.selectedItems()
            if not selection:
                QMessageBox.warning(self, "Attention", "Sélectionnez un voyage")
                return

            row = selection[0].row()
            service = self.timeline.services[idx_service]
            voyages_list = service.get_voyages()

            if row >= len(voyages_list):
                return

            voy = voyages_list[row]

            if voy is None:
                QMessageBox.warning(self, "Erreur", "Voyage invalide")
                return

            service.voyages.remove(voy)

            voy.assigne = False
            voy.service_assigne = None

            self.timeline.redessiner()
            self.refresh_table_importes()
            self.on_service_change()

        except Exception as e:
            print(f"❌ Erreur retirer_voyage_du_service: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")


# ==================== DIALOGUE AJOUT SERVICE ====================

class DialogAjoutService(QDialog):
    def __init__(self, num_service=1, parent=None):
        super().__init__(parent)
        self.num_service = num_service
        self.setWindowTitle("Nouveau service")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        self.edit_num = QLineEdit(str(num_service))
        layout.addRow("Numéro:", self.edit_num)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["matin", "soir", "journée", "coupé"])
        layout.addRow("Type:", self.combo_type)

        self.time_debut = QTimeEdit()
        self.time_debut.setTime(QTime(6, 0))
        self.time_debut.setDisplayFormat("HH:mm")
        layout.addRow("Heure début:", self.time_debut)

        self.time_fin = QTimeEdit()
        self.time_fin.setTime(QTime(14, 0))
        self.time_fin.setDisplayFormat("HH:mm")
        layout.addRow("Heure fin:", self.time_fin)

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_service(self):
        t_debut = self.time_debut.time()
        t_fin = self.time_fin.time()

        service = service_agent(
            num_service=self.edit_num.text() or str(self.num_service),
            type_service=self.combo_type.currentText()
        )

        heure_debut_min = t_debut.hour() * 60 + t_debut.minute()
        heure_fin_min = t_fin.hour() * 60 + t_fin.minute()
        service.set_limites(heure_debut_min, heure_fin_min)

        service.couleur = self.combo_couleur.currentData()

        return service


# ==================== PANNEAU DÉTAILS ====================

class PanneauDetails(QFrame):
    """Panneau de détails du voyage sélectionné - Style moderne"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedWidth(300)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        # Header
        self.header = QLabel("📋 Détails du voyage")
        self.header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.header.setStyleSheet("""
            QLabel {
                background-color: #6b7280;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.layout.addWidget(self.header)

        # Container pour les détails
        self.details_container = QWidget()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setSpacing(8)

        # Placeholder
        self.placeholder = QLabel("👆\n\nCliquez sur un voyage\npour voir ses détails")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #9ca3af; font-size: 13px;")
        self.details_layout.addWidget(self.placeholder)

        # Numéro de ligne
        self.ligne_frame = self._create_info_frame("🚌", "Numéro de ligne", "#dbeafe")
        self.ligne_frame.hide()
        self.details_layout.addWidget(self.ligne_frame)

        # Numéro de voyage
        self.voyage_num_frame = self._create_info_frame("🎫", "Numéro de voyage", "#fef3c7")
        self.voyage_num_frame.hide()
        self.details_layout.addWidget(self.voyage_num_frame)

        # Horaires
        self.horaires_frame = self._create_info_frame("🕐", "Horaires", "#f3f4f6")
        self.horaires_frame.hide()
        self.details_layout.addWidget(self.horaires_frame)

        # Arrêt de départ
        self.depart_frame = self._create_info_frame("🟢", "Arrêt de départ", "#dcfce7")
        self.depart_frame.hide()
        self.details_layout.addWidget(self.depart_frame)

        # Arrêt d'arrivée
        self.arrivee_frame = self._create_info_frame("🔴", "Arrêt d'arrivée", "#fee2e2")
        self.arrivee_frame.hide()
        self.details_layout.addWidget(self.arrivee_frame)

        # Jours de service
        self.js_srv_frame = self._create_info_frame("📅", "Jours de service", "#e0e7ff")
        self.js_srv_frame.hide()
        self.details_layout.addWidget(self.js_srv_frame)

        self.details_layout.addStretch()
        self.layout.addWidget(self.details_container)

    def _create_info_frame(self, icon, title, bg_color):
        """Crée un cadre d'information stylisé"""
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {bg_color}; border-radius: 8px; padding: 5px;")
        layout = QHBoxLayout(frame)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #6b7280; font-size: 10px; background: transparent;")
        info_layout.addWidget(title_label)

        value_label = QLabel()
        value_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        value_label.setStyleSheet("background: transparent;")
        value_label.setWordWrap(True)
        info_layout.addWidget(value_label)

        frame.value_label = value_label
        layout.addWidget(info_widget)
        layout.addStretch()

        return frame

    def afficher(self, voy):
        """Affiche les détails d'un objet voyage"""
        self.placeholder.hide()

        # Header avec couleur du voyage
        couleur = getattr(voy, 'couleur', '#3498db')
        self.header.setStyleSheet(f"""
            QLabel {{
                background-color: {couleur};
                color: white;
                padding: 10px;
                border-radius: 5px;
            }}
        """)

        # Numéro de ligne
        self.ligne_frame.value_label.setText(str(voy.num_ligne))
        self.ligne_frame.show()

        # Numéro de voyage
        self.voyage_num_frame.value_label.setText(str(voy.num_voyage))
        self.voyage_num_frame.show()

        # Horaires
        h_debut = voyage.minutes_to_time(voy.hdebut)
        h_fin = voyage.minutes_to_time(voy.hfin)
        duree = voy.hfin - voy.hdebut
        duree_h = duree // 60
        duree_m = duree % 60
        if duree_h > 0:
            duree_str = f"{duree_h}h{duree_m:02d}" if duree_m else f"{duree_h}h"
        else:
            duree_str = f"{duree_m} min"
        self.horaires_frame.value_label.setText(f"{h_debut} → {h_fin}\nDurée: {duree_str}")
        self.horaires_frame.show()

        # Arrêt de départ
        self.depart_frame.value_label.setText(voy.arret_debut or "N/A")
        self.depart_frame.show()

        # Arrêt d'arrivée
        self.arrivee_frame.value_label.setText(voy.arret_fin or "N/A")
        self.arrivee_frame.show()

        # Jours de service
        if voy.js_srv:
            self.js_srv_frame.value_label.setText(voy.js_srv)
            self.js_srv_frame.show()
        else:
            self.js_srv_frame.hide()

    def effacer(self):
        """Efface les détails et affiche le placeholder"""
        self.header.setStyleSheet("""
            QLabel {
                background-color: #6b7280;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.ligne_frame.hide()
        self.voyage_num_frame.hide()
        self.horaires_frame.hide()
        self.depart_frame.hide()
        self.arrivee_frame.hide()
        self.js_srv_frame.hide()
        self.placeholder.show()


# ==================== DIALOGUE SOLUTIONS OPTIMISATION ====================

class DialogSolutionsOptimisation(QDialog):
    """Dialogue pour afficher et choisir une solution d'optimisation"""

    def __init__(self, solutions, services_originaux, parent=None):
        super().__init__(parent)
        self.solutions = solutions
        self.services_originaux = services_originaux
        self.solution_choisie = None

        print(f"📋 Initialisation dialogue avec {len(solutions)} solution(s)")

        self.setWindowTitle("Solutions d'optimisation")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"🎉 {len(solutions)} solution(s) trouvée(s) !")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        layout.addWidget(header)

        # Sélection de solution
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Choisir une solution :"))

        self.combo_solutions = QComboBox()
        for i, sol in enumerate(solutions):
            strategie = sol.get("strategie", "Solution")
            nb_non_assignes = sol.get("nb_non_assignes", 0)
            label = f"Solution {i + 1}: {strategie}"
            if nb_non_assignes > 0:
                label += f" ⚠️ ({nb_non_assignes} non assignés)"
            self.combo_solutions.addItem(label, i)
        self.combo_solutions.currentIndexChanged.connect(self.afficher_solution)
        select_layout.addWidget(self.combo_solutions)
        select_layout.addStretch()

        layout.addLayout(select_layout)

        # Info stratégie
        self.label_strategie = QLabel()
        self.label_strategie.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.label_strategie)

        # Zone d'affichage
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.text_display)

        # Boutons
        buttons_layout = QHBoxLayout()

        btn_appliquer = QPushButton("✅ Appliquer cette solution")
        btn_appliquer.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_appliquer.clicked.connect(self.appliquer_solution)
        buttons_layout.addWidget(btn_appliquer)

        btn_annuler = QPushButton("❌ Annuler")
        btn_annuler.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_annuler)

        layout.addLayout(buttons_layout)

        print("📋 Dialogue créé, affichage de la première solution...")

        # Afficher la première solution
        if solutions:
            self.afficher_solution()

    def afficher_solution(self):
        print("📊 afficher_solution() appelée")
        idx = self.combo_solutions.currentData()
        if idx is None:
            print("⚠️ Aucun index sélectionné")
            return

        print(f"📊 Affichage de la solution {idx}")

        solution = self.solutions[idx]

        # Afficher info stratégie
        strategie = solution.get("strategie", "Stratégie inconnue")
        nb_non_assignes = solution.get("nb_non_assignes", 0)
        info = f"📊 Stratégie: {strategie}"
        if nb_non_assignes > 0:
            info += f" | ⚠️ {nb_non_assignes} voyage(s) non assigné(s)"
        self.label_strategie.setText(info)

        # Générer le texte
        texte = ""

        total_voyages = 0
        for service_id, voyages_list in solution["services"].items():
            total_voyages += len(voyages_list)

            try:
                service_original = self.services_originaux[service_id]

                # Header du service
                service_nom = f"Service {service_original.num_service}" if service_original.num_service else f"Service {service_id + 1}"
                h_debut = voyage.minutes_to_time(service_original.heure_debut)
                h_fin = voyage.minutes_to_time(service_original.heure_fin)

                texte += f"\n{'=' * 70}\n"
                texte += f"=== {service_nom} ({h_debut} - {h_fin}) - {len(voyages_list)} voyage(s) ===\n"
                texte += f"{'=' * 70}\n\n"

                # Voyages du service
                for i, voy_data in enumerate(voyages_list):
                    voy = voy_data["voyage_obj"]
                    statut = "🔒 FIXE  " if voy_data["fixe"] else "✨ AJOUTÉ"

                    texte += f"  {i + 1}. {statut} | {voy.num_ligne}-{voy.num_voyage:>2} | "
                    texte += f"{voyage.minutes_to_time(voy.hdebut)}-{voyage.minutes_to_time(voy.hfin)} | "
                    texte += f"{voy.arret_debut[:15]:15} → {voy.arret_fin[:15]:15}"

                    # Vérifier continuité avec voyage précédent
                    if i > 0:
                        voy_prec = voyages_list[i - 1]["voyage_obj"]
                        try:
                            if voy_prec.arret_fin_id() != voy.arret_debut_id():
                                texte += " ⚠️ RUPTURE GÉO"
                        except:
                            pass

                    texte += "\n"

                if not voyages_list:
                    texte += "  (aucun voyage)\n"

            except Exception as e:
                print(f"❌ Erreur affichage service {service_id}: {e}")
                import traceback
                traceback.print_exc()

        texte += f"\n{'=' * 70}\n"
        texte += f"TOTAL: {total_voyages} voyage(s) assignés\n"
        texte += f"{'=' * 70}\n"

        print(f"📝 Texte généré ({len(texte)} caractères)")
        self.text_display.setPlainText(texte)

    def appliquer_solution(self):
        idx = self.combo_solutions.currentData()
        self.solution_choisie = self.solutions[idx]
        print(f"✅ Solution {idx} choisie")
        self.accept()

# ==================== FENÊTRE PRINCIPALE ====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Gestion des Services de Bus")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()

        self.btn_effacer = QPushButton("🗑️ Tout effacer")
        self.btn_effacer.clicked.connect(self.effacer_tout)
        toolbar.addWidget(self.btn_effacer)

        # ✨ NOUVEAU BOUTON OPTIMISER
        self.btn_optimiser = QPushButton("🚀 Optimiser l'attribution")
        self.btn_optimiser.setStyleSheet("background-color: #e67e22; color: white; padding: 8px; font-weight: bold;")
        self.btn_optimiser.clicked.connect(self.optimiser_services)
        toolbar.addWidget(self.btn_optimiser)

        toolbar.addStretch()

        self.label_info = QLabel("Bienvenue ! Importez des voyages et créez des services.")
        self.label_info.setStyleSheet("color: #666;")
        toolbar.addWidget(self.label_info)

        main_layout.addLayout(toolbar)

        content = QHBoxLayout()

        self.timeline = TimelineView()
        self.timeline.voyage_selectionne.connect(self.on_voyage_selected)

        self.panneau_gauche = PanneauGauche(self.timeline)
        content.addWidget(self.panneau_gauche)

        content.addWidget(self.timeline, stretch=1)

        self.panneau_details = PanneauDetails()
        content.addWidget(self.panneau_details)

        main_layout.addLayout(content)

    def optimiser_services(self):
        """Lance l'optimisation des services"""
        from solver_bus import optimiser_services

        print("🚀 Début optimisation")

        # Vérifications
        if not self.panneau_gauche.voyages_importes:
            QMessageBox.warning(self, "Attention", "Aucun voyage importé")
            return

        if not self.timeline.services:
            QMessageBox.warning(self, "Attention", "Aucun service créé")
            return

        # Préparer les données
        voyages_list = self.panneau_gauche.voyages_importes
        print(f"🚌 Nombre de voyages : {len(voyages_list)}")

        services_data = []
        for service in self.timeline.services:
            # Trouver les indices des voyages déjà assignés
            indices_assignes = []
            for i, voy in enumerate(voyages_list):
                if voy in service.get_voyages():
                    indices_assignes.append(i)

            print(f"📋 Service {service.num_service} : {len(indices_assignes)} voyages pré-assignés")
            services_data.append((service, indices_assignes))

        # Lancer l'optimisation avec indicateur de chargement
        self.label_info.setText("⏳ Optimisation en cours...")
        QApplication.processEvents()  # Forcer l'affichage

        try:
            solutions = optimiser_services(voyages_list, services_data, max_solutions=5)

            print(f"✅ Nombre de solutions trouvées : {len(solutions)}")

            if not solutions:
                QMessageBox.warning(self, "Aucune solution",
                                    "Le solver n'a pas trouvé de solution.\n"
                                    "Vérifiez que les contraintes sont réalisables.")
                self.label_info.setText("❌ Aucune solution trouvée")
                return

            # DEBUG: Afficher la première solution
            print(f"📊 Solution 1 - Services : {len(solutions[0]['services'])}")
            for service_id, voyages_list_sol in solutions[0]["services"].items():
                print(f"   Service {service_id} : {len(voyages_list_sol)} voyages")

            # Afficher le dialogue des solutions
            print("🖥️ Création du dialogue...")
            dialog = DialogSolutionsOptimisation(solutions, self.timeline.services, self)

            print("🖥️ Affichage du dialogue...")
            result = dialog.exec()
            print(f"🖥️ Résultat du dialogue : {result}")

            if result == QDialog.DialogCode.Accepted:
                print("✅ Solution acceptée, application en cours...")
                self.appliquer_solution_optimisee(dialog.solution_choisie)
            else:
                print("❌ Solution annulée")
                self.label_info.setText("Optimisation annulée")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'optimisation:\n{str(e)}")
            self.label_info.setText("❌ Erreur d'optimisation")
            import traceback
            traceback.print_exc()

    def appliquer_solution_optimisee(self, solution):
        """Applique une solution d'optimisation à l'interface"""

        print("🔧 Début application solution...")

        try:
            # Réinitialiser TOUS les services
            print("   Réinitialisation des services...")
            for service in self.timeline.services:
                service.voyages.clear()  # Clear au lieu de = []

            # Réinitialiser l'état de TOUS les voyages
            print("   Réinitialisation des voyages...")
            for voy in self.panneau_gauche.voyages_importes:
                voy.assigne = False
                voy.service_assigne = None

            # Appliquer la nouvelle attribution
            print("   Application de la nouvelle attribution...")
            voyages_a_assigner = []

            for service_id, voyages_list in solution["services"].items():
                if service_id >= len(self.timeline.services):
                    print(f"   ⚠️ Service {service_id} n'existe plus, skip")
                    continue

                service = self.timeline.services[service_id]

                for voy_data in voyages_list:
                    v_idx = voy_data["index"]

                    # Vérifier que l'index est valide
                    if v_idx >= len(self.panneau_gauche.voyages_importes):
                        print(f"   ⚠️ Index voyage {v_idx} invalide, skip")
                        continue

                    # Récupérer le voyage ORIGINAL depuis voyages_importes
                    voy_original = self.panneau_gauche.voyages_importes[v_idx]

                    # Vérification de sécurité
                    if voy_original is None:
                        print(f"   ⚠️ Voyage à l'index {v_idx} est None, skip")
                        continue

                    # Ajouter au service
                    service.voyages.append(voy_original)

                    # Marquer comme assigné
                    voy_original.assigne = True
                    nom_service = f"Service {service.num_service}" if service.num_service else f"Service {service_id + 1}"
                    voy_original.service_assigne = nom_service

                    voyages_a_assigner.append((service_id, v_idx))

            print(f"   ✅ {len(voyages_a_assigner)} voyages assignés")

            # Rafraîchir l'interface dans l'ordre correct
            print("   Rafraîchissement de l'interface...")

            # 1. Timeline en premier
            self.timeline.redessiner()

            # 2. Table des voyages importés
            self.panneau_gauche.refresh_table_importes()

            # 3. Combo des services
            self.panneau_gauche.refresh_combo_services()

            # 4. Si un service est sélectionné, rafraîchir sa table
            if self.panneau_gauche.combo_services.currentData() is not None:
                self.panneau_gauche.on_service_change()

            # 5. Effacer les détails du voyage sélectionné
            self.panneau_details.effacer()

            print("✅ Solution appliquée avec succès")

            self.label_info.setText("✅ Solution appliquée avec succès !")
            QMessageBox.information(self, "Succès",
                                    f"La solution d'optimisation a été appliquée\n{len(voyages_a_assigner)} voyage(s) assigné(s)")

        except Exception as e:
            print(f"❌ Erreur lors de l'application: {e}")
            import traceback
            traceback.print_exc()

            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'application de la solution:\n{str(e)}")
            self.label_info.setText("❌ Erreur lors de l'application")
    def on_voyage_selected(self, voy):
        self.panneau_details.afficher(voy)
        self.label_info.setText(f"Voyage sélectionné: {voy.num_ligne}-{voy.num_voyage}")

    def effacer_tout(self):
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