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
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter

# Import des classes métier
from objet import voyage, service_agent, hlp, proposition
from import_csv import DialogImportCSV


# ==================== CONFIGURATION ====================

HEURE_DEBUT = 4  # Heure de début de la timeline (en heures)
HEURE_FIN = 24  # Heure de fin de la timeline
HAUTEUR_SERVICE = 50  # Hauteur d'une ligne de service en pixels
MARGE_GAUCHE = 100  # Marge pour les noms de services
MARGE_HAUT = 40  # Marge pour les heures
PAUSE_MIN = 5  # Pause minimum entre voyages (en minutes)


# ==================== CLASSE VOYAGE GRAPHIQUE ====================

class VoyageGraphique(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_obj, y_pos, pixels_par_heure, parent_view):
        """
        Args:
            voyage_obj: Instance de la classe voyage (objet.py)
            y_pos: Position Y sur la timeline
            pixels_par_heure: Échelle de la timeline
            parent_view: Référence vers TimelineView
        """
        self.voyage_obj = voyage_obj
        self.parent_view = parent_view

        # Position et taille (hdebut et hfin sont en MINUTES)
        heure_debut = voyage_obj.hdebut / 60  # Convertir en heures décimales
        heure_fin = voyage_obj.hfin / 60
        duree_heures = heure_fin - heure_debut

        x = MARGE_GAUCHE + (heure_debut - HEURE_DEBUT) * pixels_par_heure
        largeur = duree_heures * pixels_par_heure
        hauteur = HAUTEUR_SERVICE - 10

        super().__init__(x, y_pos + 5, largeur, hauteur)

        # Couleur (on peut ajouter un attribut couleur à voyage si besoin)
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

    voyage_selectionne = pyqtSignal(object)  # Émet un objet voyage

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.services = []  # Liste d'objets service_agent
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
        """Dessine un service_agent avec ses voyages"""
        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * self.pixels_par_heure

        # Fond alternée
        couleur_fond = QColor('#f8f9fa') if index % 2 == 0 else QColor('#ffffff')
        self.scene.addRect(0, y, largeur, HAUTEUR_SERVICE,
                           QPen(Qt.PenStyle.NoPen), QBrush(couleur_fond))

        # Nom du service
        nom = f"Service {service.num_service}" if service.num_service else f"Service {index + 1}"
        text = self.scene.addText(nom)
        text.setDefaultTextColor(QColor('#333'))
        text.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        text.setPos(5, y + 15)

        # Zone horaire du service (heure_debut et heure_fin sont en MINUTES)
        if service.heure_debut is not None and service.heure_fin is not None:
            h_debut = service.heure_debut / 60  # Convertir en heures
            h_fin = service.heure_fin / 60

            x_debut = MARGE_GAUCHE + (h_debut - HEURE_DEBUT) * self.pixels_par_heure
            x_fin = MARGE_GAUCHE + (h_fin - HEURE_DEBUT) * self.pixels_par_heure

            couleur_zone = QColor(getattr(service, 'couleur', '#e3f2fd'))
            couleur_zone.setAlpha(80)
            self.scene.addRect(x_debut, y + 2, x_fin - x_debut, HAUTEUR_SERVICE - 4,
                               QPen(QColor('#90caf9'), 1), QBrush(couleur_zone))

        # Voyages du service
        for voy in service.get_voyages():
            item = VoyageGraphique(voy, y, self.pixels_par_heure, self)
            self.scene.addItem(item)

    def on_voyage_clicked(self, item):
        """Quand on clique sur un voyage"""
        # Désélectionner l'ancien
        if self.voyage_actuel:
            old_color = QColor(getattr(self.voyage_actuel.voyage_obj, 'couleur', '#3498db'))
            self.voyage_actuel.setPen(QPen(old_color.darker(120), 2))

        # Sélectionner le nouveau
        self.voyage_actuel = item
        item.setPen(QPen(QColor('#e74c3c'), 3))

        self.voyage_selectionne.emit(item.voyage_obj)

    def ajouter_service(self, service):
        """Ajoute un service_agent"""
        self.services.append(service)
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
        self.voyages_importes = []  # Liste d'objets voyage

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
        """Ouvre le dialogue d'import CSV et crée des objets voyage"""
        dialog = DialogImportCSV(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            donnees = dialog.get_voyages_importes()

            # Convertir les dictionnaires en objets voyage
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
                    # Ajouter des attributs supplémentaires pour l'interface
                    voy.couleur = '#3498db'
                    voy.assigne = False
                    voy.service_assigne = None

                    self.voyages_importes.append(voy)
                except Exception as e:
                    print(f"Erreur création voyage: {e}")

            self.refresh_table_importes()
            QMessageBox.information(self, "Import réussi", f"{len(donnees)} voyage(s) importé(s)")

    def refresh_table_importes(self):
        """Rafraîchit la table des voyages importés"""
        self.table_importes.setRowCount(len(self.voyages_importes))

        for row, voy in enumerate(self.voyages_importes):
            # Indicateur assigné
            if getattr(voy, 'assigne', False):
                item_v = QTableWidgetItem('✓')
                item_v.setForeground(QColor('#27ae60'))
            else:
                item_v = QTableWidgetItem('')
            item_v.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_importes.setItem(row, 0, item_v)

            # Données du voyage
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
        """Rafraîchit le combo des services"""
        self.combo_services.clear()
        for i, s in enumerate(self.timeline.services):
            nom = f"Service {s.num_service}" if s.num_service else f"Service {i + 1}"
            self.combo_services.addItem(nom, i)

    def on_service_change(self):
        """Met à jour la table du service sélectionné"""
        idx = self.combo_services.currentData()
        if idx is None or idx >= len(self.timeline.services):
            self.table_service.setRowCount(0)
            return

        service = self.timeline.services[idx]
        voyages_list = service.get_voyages()

        self.table_service.setRowCount(len(voyages_list))

        for row, voy in enumerate(voyages_list):
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

    def ajouter_service(self):
        """Ajoute un nouveau service_agent"""
        dialog = DialogAjoutService(len(self.timeline.services) + 1, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service = dialog.get_service()
            self.timeline.ajouter_service(service)
            self.refresh_combo_services()

    def supprimer_service(self):
        """Supprime le service sélectionné"""
        idx = self.combo_services.currentData()
        if idx is not None and idx < len(self.timeline.services):
            service = self.timeline.services[idx]

            # Désassigner les voyages du service
            for voy in service.get_voyages():
                # Retrouver le voyage original dans la liste importée
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

        voy = self.voyages_importes[row]

        # Déjà assigné ?
        if getattr(voy, 'assigne', False):
            QMessageBox.warning(self, "Déjà assigné",
                                f"Ce voyage est déjà assigné à {getattr(voy, 'service_assigne', '')}")
            return

        service = self.timeline.services[idx_service]

        # Vérifier limites horaires (tout en minutes)
        if service.heure_debut is not None and service.heure_fin is not None:
            if voy.hdebut < service.heure_debut or voy.hfin > service.heure_fin:
                QMessageBox.warning(self, "Hors limites",
                                    f"Le voyage est hors des limites du service")
                return

        # Vérifier chevauchements avec pause
        for v_exist in service.get_voyages():
            # Chevauchement si les intervalles se croisent (avec pause de 5 min)
            if not (voy.hfin + PAUSE_MIN <= v_exist.hdebut or voy.hdebut >= v_exist.hfin + PAUSE_MIN):
                QMessageBox.warning(self, "Chevauchement",
                                    f"Ce voyage chevauche {v_exist.num_ligne}-{v_exist.num_voyage}")
                return

        # Ajouter le voyage au service (sans utiliser ajouter_voyage pour éviter la validation)
        service.voyages.append(voy)

        # Marquer comme assigné
        voy.assigne = True
        nom_service = f"Service {service.num_service}" if service.num_service else f"Service {idx_service + 1}"
        voy.service_assigne = nom_service

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
        voyages_list = service.get_voyages()

        if row >= len(voyages_list):
            return

        voy = voyages_list[row]

        # Retirer du service
        service.voyages.remove(voy)

        # Désassigner
        voy.assigne = False
        voy.service_assigne = None

        self.timeline.redessiner()
        self.refresh_table_importes()
        self.on_service_change()


# ==================== DIALOGUE AJOUT SERVICE ====================

class DialogAjoutService(QDialog):
    """Dialogue pour créer un service_agent"""

    def __init__(self, num_service=1, parent=None):
        super().__init__(parent)
        self.num_service = num_service
        self.setWindowTitle("Nouveau service")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Numéro du service
        self.edit_num = QLineEdit(str(num_service))
        layout.addRow("Numéro:", self.edit_num)

        # Type de service
        self.combo_type = QComboBox()
        self.combo_type.addItems(["matin", "soir", "journée", "coupé"])
        layout.addRow("Type:", self.combo_type)

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

    def get_service(self):
        """Retourne un objet service_agent configuré"""
        t_debut = self.time_debut.time()
        t_fin = self.time_fin.time()

        # Créer le service_agent
        service = service_agent(
            num_service=self.edit_num.text() or str(self.num_service),
            type_service=self.combo_type.currentText()
        )

        # Définir les limites horaires (en minutes)
        heure_debut_min = t_debut.hour() * 60 + t_debut.minute()
        heure_fin_min = t_fin.hour() * 60 + t_fin.minute()
        service.set_limites(heure_debut_min, heure_fin_min)

        # Ajouter la couleur comme attribut
        service.couleur = self.combo_couleur.currentData()

        return service


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
        champs = ['Ligne', 'Voyage', 'Départ', 'Arrivée', 'Heure', 'Durée', 'Js srv']

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

    def afficher(self, voy):
        """Affiche les détails d'un objet voyage"""
        self.msg.hide()

        self.labels['Ligne'].setText(str(voy.num_ligne))
        self.labels['Voyage'].setText(str(voy.num_voyage))
        self.labels['Départ'].setText(voy.arret_debut)
        self.labels['Arrivée'].setText(voy.arret_fin)
        self.labels['Heure'].setText(f"{voyage.minutes_to_time(voy.hdebut)} - {voyage.minutes_to_time(voy.hfin)}")
        self.labels['Durée'].setText(f"{voy.hfin - voy.hdebut} min")
        self.labels['Js srv'].setText(voy.js_srv or "-")

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

        self.btn_solver = QPushButton("Trouver solution")
        self.btn_solver.clicked.connect(self.effacer_tout)
        toolbar.addWidget(self.btn_solver)

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

    def on_voyage_selected(self, voy):
        """Quand un voyage est sélectionné"""
        self.panneau_details.afficher(voy)
        self.label_info.setText(f"Voyage sélectionné: {voy.num_ligne}-{voy.num_voyage}")

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