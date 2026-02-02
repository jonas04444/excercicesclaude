"""
Application de gestion de services de bus avec timeline
Chaque service est une ligne horizontale, les voyages sont des rectangles sur cette ligne
Avec panneau de détails à droite et import CSV
"""

import sys
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QPushButton, QLabel, QSpinBox, QTimeEdit,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QFrame, QInputDialog, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QRectF, QTime, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter


# Configuration de la timeline
HEURE_DEBUT = 4
HEURE_FIN = 24
HAUTEUR_SERVICE = 50
MARGE_GAUCHE = 80
MARGE_HAUT = 40


class VoyageItem(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_data, y_position, timeline_view, pixels_par_heure, parent=None):
        self.voyage_data = voyage_data
        self.timeline_view = timeline_view
        self.y_position = y_position
        self.is_selected = False

        # Calcul de la position X basée sur l'heure de départ
        heure_depart = voyage_data['heure_depart']
        x = MARGE_GAUCHE + (heure_depart - HEURE_DEBUT) * pixels_par_heure

        # Calcul de la largeur basée sur la durée
        duree_heures = voyage_data['duree_minutes'] / 60
        largeur = max(duree_heures * pixels_par_heure, 40)

        # Position Y centrée sur la ligne du service
        y = y_position - 15

        super().__init__(x, y, largeur, 30)

        # Style du rectangle
        self.couleur_base = QColor(voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(self.couleur_base))
        self.setPen(QPen(self.couleur_base.darker(120), 2))

        # Rendre l'item interactif
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Texte du voyage (seulement si assez de place)
        if largeur > 50:
            self.text_item = QGraphicsTextItem(voyage_data['nom'], self)
            self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
            self.text_item.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            self.text_item.setPos(x + 5, y + 3)

            # Heure
            heure_str = f"{int(heure_depart):02d}:{int((heure_depart % 1) * 60):02d}"
            self.heure_item = QGraphicsTextItem(heure_str, self)
            self.heure_item.setDefaultTextColor(QColor(255, 255, 255, 180))
            self.heure_item.setFont(QFont("Arial", 7))
            self.heure_item.setPos(x + 5, y + 16)

    def hoverEnterEvent(self, event):
        if not self.is_selected:
            self.setBrush(QBrush(self.couleur_base.lighter(120)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_selected:
            self.setBrush(QBrush(self.couleur_base))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.timeline_view.select_voyage(self)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.setBrush(QBrush(self.couleur_base.lighter(130)))
            self.setPen(QPen(QColor('#f1c40f'), 3))
        else:
            self.setBrush(QBrush(self.couleur_base))
            self.setPen(QPen(self.couleur_base.darker(120), 2))


class TimelineView(QGraphicsView):
    """Vue principale de la timeline - responsive"""

    voyage_selected = pyqtSignal(dict)
    voyage_deselected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumHeight(200)

        self.services_data = []  # Stocke les données des services
        self.selected_voyage = None
        self.voyage_items = []  # Référence aux items de voyage pour la sélection

    def get_pixels_par_heure(self):
        """Calcule dynamiquement les pixels par heure selon la largeur disponible"""
        largeur_disponible = self.viewport().width() - MARGE_GAUCHE - 20
        return largeur_disponible / (HEURE_FIN - HEURE_DEBUT)

    def resizeEvent(self, event):
        """Redessine la timeline quand la vue est redimensionnée"""
        super().resizeEvent(event)
        self._redessiner_tout()

    def _redessiner_tout(self):
        """Redessine tous les éléments de la timeline"""
        # Sauvegarder le voyage sélectionné
        selected_data = None
        if self.selected_voyage:
            selected_data = self.selected_voyage.voyage_data

        self.scene.clear()
        self.voyage_items = []
        self.selected_voyage = None

        pixels_par_heure = self.get_pixels_par_heure()

        self._dessiner_echelle_temps(pixels_par_heure)

        # Redessiner les services et voyages
        for i, service_data in enumerate(self.services_data):
            y_position = MARGE_HAUT + i * HAUTEUR_SERVICE + 30
            self._dessiner_service(service_data, y_position, pixels_par_heure)

            for voyage_data in service_data['voyages']:
                item = self._dessiner_voyage(voyage_data, y_position, pixels_par_heure)
                self.voyage_items.append(item)

                # Restaurer la sélection
                if selected_data and voyage_data['id'] == selected_data['id']:
                    item.set_selected(True)
                    self.selected_voyage = item

        # Mettre à jour la taille de la scène
        largeur = self.viewport().width()
        hauteur = MARGE_HAUT + len(self.services_data) * HAUTEUR_SERVICE + 50
        self.scene.setSceneRect(0, 0, largeur, max(hauteur, self.viewport().height()))

    def _dessiner_echelle_temps(self, pixels_par_heure):
        """Dessine l'échelle de temps en haut"""
        largeur_totale = (HEURE_FIN - HEURE_DEBUT) * pixels_par_heure

        for heure in range(HEURE_DEBUT, HEURE_FIN + 1):
            x = MARGE_GAUCHE + (heure - HEURE_DEBUT) * pixels_par_heure

            ligne = QGraphicsLineItem(x, MARGE_HAUT - 10, x, MARGE_HAUT)
            ligne.setPen(QPen(QColor('#7f8c8d'), 1))
            self.scene.addItem(ligne)

            # Afficher 24h comme "00h" si on veut, ou garder "24h"
            heure_affichee = heure if heure < 24 else 0
            label = QGraphicsTextItem(f"{heure_affichee:02d}h")
            label.setDefaultTextColor(QColor('#7f8c8d'))
            label.setFont(QFont("Arial", 8))
            label.setPos(x - 12, MARGE_HAUT - 30)
            self.scene.addItem(label)

            # Ligne verticale en pointillés
            ligne_guide = QGraphicsLineItem(x, MARGE_HAUT, x, 600)
            pen = QPen(QColor('#ecf0f1'), 1, Qt.PenStyle.DotLine)
            ligne_guide.setPen(pen)
            ligne_guide.setZValue(-2)
            self.scene.addItem(ligne_guide)

    def _dessiner_service(self, service_data, y_position, pixels_par_heure):
        """Dessine une ligne de service avec ses limites d'heures"""
        largeur_totale = (HEURE_FIN - HEURE_DEBUT) * pixels_par_heure

        # Limites du service
        service_heure_debut = service_data.get('heure_debut', HEURE_DEBUT)
        service_heure_fin = service_data.get('heure_fin', HEURE_FIN)

        # Zone active du service (fond coloré)
        x_debut_service = MARGE_GAUCHE + (service_heure_debut - HEURE_DEBUT) * pixels_par_heure
        x_fin_service = MARGE_GAUCHE + (service_heure_fin - HEURE_DEBUT) * pixels_par_heure
        largeur_service = x_fin_service - x_debut_service

        # Fond de la zone active
        fond_actif = QGraphicsRectItem(x_debut_service, y_position - 25, largeur_service, HAUTEUR_SERVICE)
        couleur_fond = QColor(service_data['couleur'])
        couleur_fond.setAlpha(30)
        fond_actif.setBrush(QBrush(couleur_fond))
        fond_actif.setPen(QPen(Qt.PenStyle.NoPen))
        fond_actif.setZValue(-1)
        self.scene.addItem(fond_actif)

        # Zones hors limites (grisées)
        if service_heure_debut > HEURE_DEBUT:
            x_avant = MARGE_GAUCHE
            largeur_avant = (service_heure_debut - HEURE_DEBUT) * pixels_par_heure
            fond_avant = QGraphicsRectItem(x_avant, y_position - 25, largeur_avant, HAUTEUR_SERVICE)
            fond_avant.setBrush(QBrush(QColor(200, 200, 200, 100)))
            fond_avant.setPen(QPen(Qt.PenStyle.NoPen))
            fond_avant.setZValue(-1)
            self.scene.addItem(fond_avant)

        if service_heure_fin < HEURE_FIN:
            x_apres = MARGE_GAUCHE + (service_heure_fin - HEURE_DEBUT) * pixels_par_heure
            largeur_apres = (HEURE_FIN - service_heure_fin) * pixels_par_heure
            fond_apres = QGraphicsRectItem(x_apres, y_position - 25, largeur_apres, HAUTEUR_SERVICE)
            fond_apres.setBrush(QBrush(QColor(200, 200, 200, 100)))
            fond_apres.setPen(QPen(Qt.PenStyle.NoPen))
            fond_apres.setZValue(-1)
            self.scene.addItem(fond_apres)

        # Ligne horizontale (seulement dans la zone active)
        ligne = QGraphicsLineItem(x_debut_service, y_position, x_fin_service, y_position)
        ligne.setPen(QPen(QColor(service_data['couleur']), 2))
        self.scene.addItem(ligne)

        # Marqueurs de limites (lignes verticales)
        ligne_debut = QGraphicsLineItem(x_debut_service, y_position - 20, x_debut_service, y_position + 20)
        ligne_debut.setPen(QPen(QColor(service_data['couleur']), 2))
        self.scene.addItem(ligne_debut)

        ligne_fin = QGraphicsLineItem(x_fin_service, y_position - 20, x_fin_service, y_position + 20)
        ligne_fin.setPen(QPen(QColor(service_data['couleur']), 2))
        self.scene.addItem(ligne_fin)

        # Label du service avec heures
        h_deb = f"{int(service_heure_debut):02d}:{int((service_heure_debut % 1) * 60):02d}"
        h_fin = f"{int(service_heure_fin):02d}:{int((service_heure_fin % 1) * 60):02d}"
        label_text = f"{service_data['nom']}\n{h_deb}-{h_fin}"
        label = QGraphicsTextItem(label_text)
        label.setDefaultTextColor(QColor('#2c3e50'))
        label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        label.setPos(5, y_position - 18)
        self.scene.addItem(label)

    def _dessiner_voyage(self, voyage_data, y_position, pixels_par_heure):
        """Dessine un voyage et retourne l'item"""
        item = VoyageItem(voyage_data, y_position, self, pixels_par_heure)
        self.scene.addItem(item)
        return item

    def ajouter_service(self, nom, couleur='#34495e', heure_debut=None, heure_fin=None):
        """Ajoute un nouveau service avec limites d'heures optionnelles"""
        service_data = {
            'nom': nom,
            'couleur': couleur,
            'heure_debut': heure_debut if heure_debut is not None else HEURE_DEBUT,
            'heure_fin': heure_fin if heure_fin is not None else HEURE_FIN,
            'voyages': []
        }
        self.services_data.append(service_data)
        self._redessiner_tout()
        return service_data

    def ajouter_voyage(self, service_index, voyage_data):
        """Ajoute un voyage à un service"""
        if 0 <= service_index < len(self.services_data):
            # Générer un ID unique
            voyage_data['id'] = id(voyage_data)
            voyage_data['service_nom'] = self.services_data[service_index]['nom']
            self.services_data[service_index]['voyages'].append(voyage_data)
            self._redessiner_tout()

    def select_voyage(self, voyage_item):
        """Sélectionne un voyage"""
        if self.selected_voyage and self.selected_voyage != voyage_item:
            self.selected_voyage.set_selected(False)

        if self.selected_voyage == voyage_item:
            voyage_item.set_selected(False)
            self.selected_voyage = None
            self.voyage_deselected.emit()
        else:
            voyage_item.set_selected(True)
            self.selected_voyage = voyage_item
            self.voyage_selected.emit(voyage_item.voyage_data)


class PanneauVoyages(QFrame):
    """Panneau latéral gauche avec la liste des voyages importés et assignés"""

    voyage_clicked = pyqtSignal(dict)

    def __init__(self, timeline_view):
        super().__init__()
        self.timeline = timeline_view
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedWidth(550)  # Plus large pour voir toutes les infos

        # Liste des voyages importés (non assignés)
        self.voyages_importes = []

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ===== SECTION 1: Voyages importés (non assignés) =====
        titre_importes = QLabel("📥 Voyages importés")
        titre_importes.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_importes.setStyleSheet("color: #2c3e50; padding: 3px; background-color: #e8f4fd; border-radius: 3px;")
        layout.addWidget(titre_importes)

        # Bouton importer CSV
        btn_import = QPushButton("📂 Importer CSV")
        btn_import.clicked.connect(self.importer_csv)
        layout.addWidget(btn_import)

        # Liste des voyages importés - TOUTES LES COLONNES
        self.liste_importes = QTableWidget()
        self.liste_importes.setColumnCount(8)
        self.liste_importes.setHorizontalHeaderLabels(['✓', 'Ligne', 'Voy.', 'Début', 'Fin', 'De', 'À', 'Js srv'])

        # Configuration des largeurs de colonnes - PLUS LARGES
        header = self.liste_importes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 25)  # ✓
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 50)  # Ligne
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(2, 50)  # Voy.
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 50)  # Début
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 50)  # Fin
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # De
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # À
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(7, 80)  # Js srv

        self.liste_importes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.liste_importes.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.liste_importes.setAlternatingRowColors(True)
        self.liste_importes.verticalHeader().setVisible(False)
        self.liste_importes.setMaximumHeight(280)
        self.liste_importes.cellClicked.connect(self.on_voyage_importe_clicked)
        self.liste_importes.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
            }
            QHeaderView::section {
                font-size: 10px;
                padding: 3px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.liste_importes)

        # Compteur voyages importés
        self.label_count_importes = QLabel("0 voyage(s) importé(s)")
        self.label_count_importes.setStyleSheet("color: #6b7280; font-size: 10px;")
        layout.addWidget(self.label_count_importes)

        # Bouton ajouter au service
        self.btn_ajouter_service = QPushButton("⬇️ Ajouter au service sélectionné")
        self.btn_ajouter_service.setStyleSheet("background-color: #27ae60; color: white;")
        self.btn_ajouter_service.clicked.connect(self.ajouter_voyage_au_service)
        layout.addWidget(self.btn_ajouter_service)

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #bdc3c7; margin: 5px 0;")
        separator.setFixedHeight(2)
        layout.addWidget(separator)

        # ===== SECTION 2: Services et voyages assignés =====
        titre_services = QLabel("🚌 Services")
        titre_services.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_services.setStyleSheet("color: #2c3e50; padding: 3px; background-color: #e8f8e8; border-radius: 3px;")
        layout.addWidget(titre_services)

        # Sélection du service + bouton ajouter
        service_layout = QHBoxLayout()

        self.combo_service = QComboBox()
        self.combo_service.currentIndexChanged.connect(self.on_service_change)
        service_layout.addWidget(self.combo_service, stretch=1)

        btn_add_service = QPushButton("+")
        btn_add_service.setFixedWidth(30)
        btn_add_service.setToolTip("Ajouter un service")
        btn_add_service.clicked.connect(self.ajouter_service)
        service_layout.addWidget(btn_add_service)

        layout.addLayout(service_layout)

        # Liste des voyages du service - TOUTES LES COLONNES
        self.liste_voyages = QTableWidget()
        self.liste_voyages.setColumnCount(7)
        self.liste_voyages.setHorizontalHeaderLabels(['Ligne', 'Voy.', 'Début', 'Fin', 'De', 'À', 'Js srv'])

        # Configuration des largeurs - PLUS LARGES
        header2 = self.liste_voyages.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header2.resizeSection(0, 50)  # Ligne
        header2.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header2.resizeSection(1, 50)  # Voy.
        header2.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header2.resizeSection(2, 50)  # Début
        header2.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header2.resizeSection(3, 50)  # Fin
        header2.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # De
        header2.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # À
        header2.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header2.resizeSection(6, 80)  # Js srv

        self.liste_voyages.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.liste_voyages.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.liste_voyages.setAlternatingRowColors(True)
        self.liste_voyages.verticalHeader().setVisible(False)
        self.liste_voyages.cellClicked.connect(self.on_voyage_service_clicked)
        self.liste_voyages.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
            }
            QHeaderView::section {
                font-size: 10px;
                padding: 3px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.liste_voyages)

        # Compteur voyages service
        self.label_count_service = QLabel("0 voyage(s) dans ce service")
        self.label_count_service.setStyleSheet("color: #6b7280; font-size: 10px;")
        layout.addWidget(self.label_count_service)

        # Bouton retirer du service
        self.btn_retirer = QPushButton("⬆️ Retirer du service")
        self.btn_retirer.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_retirer.clicked.connect(self.retirer_voyage_du_service)
        layout.addWidget(self.btn_retirer)

    def importer_csv(self):
        """Ouvre le dialogue d'import CSV"""
        dialog = DialogImportCSV(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nouveaux_voyages = dialog.get_voyages()

            # Ajouter un ID unique à chaque voyage importé
            for v in nouveaux_voyages:
                v['id'] = id(v)
                v['assigne'] = False  # Pas encore assigné à un service
                v['service_assigne'] = None

            self.voyages_importes.extend(nouveaux_voyages)
            self.refresh_liste_importes()
            QMessageBox.information(self, "Succès", f"{len(nouveaux_voyages)} voyage(s) importé(s)")

    def refresh_liste_importes(self):
        """Met à jour la liste des voyages importés avec toutes les infos"""
        self.liste_importes.setRowCount(len(self.voyages_importes))

        # Trier par heure
        voyages_tries = sorted(self.voyages_importes, key=lambda v: v.get('heure_depart', 0))

        for row, voyage in enumerate(voyages_tries):
            # Couleur grisée si assigné
            couleur_texte = QColor('#95a5a6') if voyage.get('assigne', False) else QColor('#2c3e50')

            # Colonne 0: Indicateur d'assignation - "V" si assigné
            if voyage.get('assigne', False):
                item_check = QTableWidgetItem('V')
                item_check.setForeground(QColor('#27ae60'))
                item_check.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                item_check.setToolTip(f"Assigné au service: {voyage.get('service_assigne', 'N/A')}")
            else:
                item_check = QTableWidgetItem('')
            item_check.setFlags(item_check.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # Stocker l'ID du voyage, pas l'objet entier
            item_check.setData(Qt.ItemDataRole.UserRole, voyage.get('id'))
            item_check.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.liste_importes.setItem(row, 0, item_check)

            # Colonne 1: Ligne
            item_ligne = QTableWidgetItem(voyage.get('numero_ligne', ''))
            item_ligne.setFlags(item_ligne.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_ligne.setForeground(couleur_texte)
            self.liste_importes.setItem(row, 1, item_ligne)

            # Colonne 2: Numéro voyage
            item_voy = QTableWidgetItem(voyage.get('numero_voyage', ''))
            item_voy.setFlags(item_voy.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_voy.setForeground(couleur_texte)
            self.liste_importes.setItem(row, 2, item_voy)

            # Colonne 3: Heure début
            heure_debut = voyage.get('heure_depart', 0)
            heure_debut_str = f"{int(heure_debut):02d}:{int((heure_debut % 1) * 60):02d}"
            item_debut = QTableWidgetItem(heure_debut_str)
            item_debut.setFlags(item_debut.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_debut.setForeground(couleur_texte)
            self.liste_importes.setItem(row, 3, item_debut)

            # Colonne 4: Heure fin
            duree = voyage.get('duree_minutes', 60)
            heure_fin = heure_debut + duree / 60
            heure_fin_str = f"{int(heure_fin):02d}:{int((heure_fin % 1) * 60):02d}"
            item_fin = QTableWidgetItem(heure_fin_str)
            item_fin.setFlags(item_fin.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_fin.setForeground(couleur_texte)
            self.liste_importes.setItem(row, 4, item_fin)

            # Colonne 5: Arrêt de départ
            item_de = QTableWidgetItem(voyage.get('arret_depart', ''))
            item_de.setFlags(item_de.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_de.setForeground(couleur_texte)
            item_de.setToolTip(voyage.get('arret_depart', ''))
            self.liste_importes.setItem(row, 5, item_de)

            # Colonne 6: Arrêt d'arrivée
            item_a = QTableWidgetItem(voyage.get('arret_arrivee', ''))
            item_a.setFlags(item_a.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_a.setForeground(couleur_texte)
            item_a.setToolTip(voyage.get('arret_arrivee', ''))
            self.liste_importes.setItem(row, 6, item_a)

            # Colonne 7: Jours de service
            item_js = QTableWidgetItem(voyage.get('js_srv', ''))
            item_js.setFlags(item_js.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_js.setForeground(couleur_texte)
            self.liste_importes.setItem(row, 7, item_js)

        # Compter assignés vs non assignés
        nb_assignes = sum(1 for v in self.voyages_importes if v.get('assigne', False))
        nb_total = len(self.voyages_importes)
        self.label_count_importes.setText(f"{nb_total} voyage(s) ({nb_assignes} assigné(s), {nb_total - nb_assignes} en attente)")

    def refresh_services(self):
        """Met à jour la liste des services dans le combobox"""
        current = self.combo_service.currentText()
        self.combo_service.blockSignals(True)
        self.combo_service.clear()

        for service in self.timeline.services_data:
            heure_debut = service.get('heure_debut', HEURE_DEBUT)
            heure_fin = service.get('heure_fin', HEURE_FIN)
            nom_affiche = f"{service['nom']} ({self._format_heure(heure_debut)}-{self._format_heure(heure_fin)})"
            self.combo_service.addItem(nom_affiche)

        # Restaurer la sélection si possible
        for i in range(self.combo_service.count()):
            if current.split(' (')[0] in self.combo_service.itemText(i):
                self.combo_service.setCurrentIndex(i)
                break

        self.combo_service.blockSignals(False)
        self.refresh_voyages_service()

    def refresh_voyages_service(self):
        """Met à jour la liste des voyages du service sélectionné avec toutes les infos"""
        self.liste_voyages.setRowCount(0)

        service_index = self.combo_service.currentIndex()
        if service_index < 0 or service_index >= len(self.timeline.services_data):
            self.label_count_service.setText("0 voyage(s) dans ce service")
            return

        service = self.timeline.services_data[service_index]
        voyages = service.get('voyages', [])

        # Trier par heure de départ
        voyages_tries = sorted(voyages, key=lambda v: v.get('heure_depart', 0))

        self.liste_voyages.setRowCount(len(voyages_tries))

        for row, voyage in enumerate(voyages_tries):
            # Colonne 0: Ligne
            item_ligne = QTableWidgetItem(voyage.get('numero_ligne', ''))
            item_ligne.setFlags(item_ligne.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_ligne.setData(Qt.ItemDataRole.UserRole, voyage)
            self.liste_voyages.setItem(row, 0, item_ligne)

            # Colonne 1: Numéro voyage
            item_voy = QTableWidgetItem(voyage.get('numero_voyage', ''))
            item_voy.setFlags(item_voy.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.liste_voyages.setItem(row, 1, item_voy)

            # Colonne 2: Heure début
            heure_debut = voyage.get('heure_depart', 0)
            heure_debut_str = f"{int(heure_debut):02d}:{int((heure_debut % 1) * 60):02d}"
            item_debut = QTableWidgetItem(heure_debut_str)
            item_debut.setFlags(item_debut.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.liste_voyages.setItem(row, 2, item_debut)

            # Colonne 3: Heure fin
            duree = voyage.get('duree_minutes', 60)
            heure_fin = heure_debut + duree / 60
            heure_fin_str = f"{int(heure_fin):02d}:{int((heure_fin % 1) * 60):02d}"
            item_fin = QTableWidgetItem(heure_fin_str)
            item_fin.setFlags(item_fin.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.liste_voyages.setItem(row, 3, item_fin)

            # Colonne 4: Arrêt de départ
            item_de = QTableWidgetItem(voyage.get('arret_depart', ''))
            item_de.setFlags(item_de.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_de.setToolTip(voyage.get('arret_depart', ''))
            self.liste_voyages.setItem(row, 4, item_de)

            # Colonne 5: Arrêt d'arrivée
            item_a = QTableWidgetItem(voyage.get('arret_arrivee', ''))
            item_a.setFlags(item_a.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_a.setToolTip(voyage.get('arret_arrivee', ''))
            self.liste_voyages.setItem(row, 5, item_a)

            # Colonne 6: Jours de service
            item_js = QTableWidgetItem(voyage.get('js_srv', ''))
            item_js.setFlags(item_js.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.liste_voyages.setItem(row, 6, item_js)

        self.label_count_service.setText(f"{len(voyages_tries)} voyage(s) dans ce service")

    def on_service_change(self, index):
        """Appelé quand on change de service"""
        self.refresh_voyages_service()

    def on_voyage_importe_clicked(self, row, col):
        """Appelé quand on clique sur un voyage importé"""
        item = self.liste_importes.item(row, 0)
        if item:
            voyage_id = item.data(Qt.ItemDataRole.UserRole)
            # Retrouver le voyage par son ID
            for v in self.voyages_importes:
                if v.get('id') == voyage_id:
                    self.voyage_clicked.emit(v)
                    break

    def on_voyage_service_clicked(self, row, col):
        """Appelé quand on clique sur un voyage du service"""
        item = self.liste_voyages.item(row, 0)
        if item:
            voyage_data = item.data(Qt.ItemDataRole.UserRole)
            if voyage_data:
                self.voyage_clicked.emit(voyage_data)
                # Sélectionner dans la timeline
                for item in self.timeline.voyage_items:
                    if item.voyage_data.get('id') == voyage_data.get('id'):
                        self.timeline.select_voyage(item)
                        break

    def ajouter_service(self):
        """Ajoute un nouveau service avec limites d'heures"""
        dialog = DialogAjoutService(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.timeline.ajouter_service(data['nom'], data['couleur'], data['heure_debut'], data['heure_fin'])
            self.refresh_services()
            # Sélectionner le nouveau service
            self.combo_service.setCurrentIndex(self.combo_service.count() - 1)

    def ajouter_voyage_au_service(self):
        """Ajoute le voyage sélectionné au service courant"""
        # Vérifier qu'un service est sélectionné
        service_index = self.combo_service.currentIndex()
        if service_index < 0:
            QMessageBox.warning(self, "Attention", "Créez d'abord un service!")
            return

        # Récupérer le voyage sélectionné
        selected_rows = self.liste_importes.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord un voyage à ajouter!")
            return

        row = selected_rows[0].row()
        item = self.liste_importes.item(row, 0)
        voyage_id = item.data(Qt.ItemDataRole.UserRole)

        # Retrouver le voyage original dans la liste par son ID
        voyage_data = None
        for v in self.voyages_importes:
            if v.get('id') == voyage_id:
                voyage_data = v
                break

        if not voyage_data:
            return

        # Vérifier si déjà assigné à un service
        if voyage_data.get('assigne', False):
            QMessageBox.warning(
                self,
                "Voyage déjà assigné",
                f"Ce voyage est déjà attaché au service '{voyage_data.get('service_assigne', 'inconnu')}'."
            )
            return

        service = self.timeline.services_data[service_index]
        service_nom = service['nom']

        # Récupérer les infos du voyage
        heure_debut_voyage = voyage_data.get('heure_depart', 0)
        duree = voyage_data.get('duree_minutes', 60)
        heure_fin_voyage = heure_debut_voyage + duree / 60

        # Vérifier les limites d'heures du service
        service_heure_debut = service.get('heure_debut', HEURE_DEBUT)
        service_heure_fin = service.get('heure_fin', HEURE_FIN)

        if heure_debut_voyage < service_heure_debut:
            QMessageBox.warning(
                self,
                "Hors limites",
                f"Le voyage commence à {self._format_heure(heure_debut_voyage)} mais le service '{service_nom}' commence à {self._format_heure(service_heure_debut)}."
            )
            return

        if heure_fin_voyage > service_heure_fin:
            QMessageBox.warning(
                self,
                "Hors limites",
                f"Le voyage se termine à {self._format_heure(heure_fin_voyage)} mais le service '{service_nom}' se termine à {self._format_heure(service_heure_fin)}."
            )
            return

        # Vérifier les chevauchements avec les voyages existants
        for voyage_existant in service.get('voyages', []):
            exist_debut = voyage_existant.get('heure_depart', 0)
            exist_duree = voyage_existant.get('duree_minutes', 60)
            exist_fin = exist_debut + exist_duree / 60

            # Vérifier le chevauchement
            if not (heure_fin_voyage <= exist_debut or heure_debut_voyage >= exist_fin):
                QMessageBox.warning(
                    self,
                    "Chevauchement détecté",
                    f"Le voyage ({self._format_heure(heure_debut_voyage)} - {self._format_heure(heure_fin_voyage)}) chevauche le voyage existant '{voyage_existant.get('nom', '')}' ({self._format_heure(exist_debut)} - {self._format_heure(exist_fin)})."
                )
                return

        # Créer une copie du voyage pour le service
        voyage_copie = voyage_data.copy()
        voyage_copie['id'] = id(voyage_copie)  # Nouvel ID unique pour la copie
        voyage_copie['original_id'] = voyage_id  # Garder référence à l'original

        # Ajouter au service
        self.timeline.ajouter_voyage(service_index, voyage_copie)

        # Marquer l'ORIGINAL comme assigné (UN SEUL service possible)
        voyage_data['assigne'] = True
        voyage_data['service_assigne'] = service_nom

        # Rafraîchir les listes
        self.refresh_liste_importes()
        self.refresh_voyages_service()

    def _format_heure(self, heure_decimale):
        """Formate une heure décimale en HH:MM"""
        h = int(heure_decimale)
        m = int((heure_decimale % 1) * 60)
        return f"{h:02d}:{m:02d}"

    def retirer_voyage_du_service(self):
        """Retire le voyage sélectionné du service"""
        # Récupérer le voyage sélectionné
        selected_rows = self.liste_voyages.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord un voyage à retirer!")
            return

        row = selected_rows[0].row()
        item = self.liste_voyages.item(row, 0)
        voyage_data = item.data(Qt.ItemDataRole.UserRole)

        if not voyage_data:
            return

        service_index = self.combo_service.currentIndex()
        service = self.timeline.services_data[service_index]

        # Retirer du service
        service['voyages'] = [v for v in service['voyages'] if v.get('id') != voyage_data.get('id')]

        # Retrouver le voyage original dans les imports par son original_id
        original_id = voyage_data.get('original_id')
        if original_id:
            for v in self.voyages_importes:
                if v.get('id') == original_id:
                    # Démarquer le voyage - il peut maintenant être réassigné
                    v['assigne'] = False
                    v['service_assigne'] = None
                    break

        # Rafraîchir
        self.timeline._redessiner_tout()
        self.refresh_liste_importes()
        self.refresh_voyages_service()


class DetailPanel(QFrame):
    """Panneau de détails du voyage sélectionné"""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)

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

        self.details_layout.addStretch()
        self.layout.addWidget(self.details_container)

    def _create_info_frame(self, icon, title, bg_color):
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

    def show_voyage(self, data):
        self.placeholder.hide()

        # Header couleur
        couleur = data.get('couleur', '#3498db')
        self.header.setStyleSheet(f"""
            QLabel {{
                background-color: {couleur};
                color: white;
                padding: 10px;
                border-radius: 5px;
            }}
        """)

        # Numéro de ligne
        self.ligne_frame.value_label.setText(data.get('numero_ligne', 'N/A'))
        self.ligne_frame.show()

        # Numéro de voyage
        self.voyage_num_frame.value_label.setText(data.get('numero_voyage', 'N/A'))
        self.voyage_num_frame.show()

        # Horaires
        heure_dep = data['heure_depart']
        duree = data['duree_minutes']
        heure_arr = heure_dep + duree / 60
        h_dep = f"{int(heure_dep):02d}:{int((heure_dep % 1) * 60):02d}"
        h_arr = f"{int(heure_arr):02d}:{int((heure_arr % 1) * 60):02d}"
        duree_h = duree // 60
        duree_m = duree % 60
        duree_str = f"{duree_h}h{duree_m:02d}" if duree_m else f"{duree_h}h"
        self.horaires_frame.value_label.setText(f"{h_dep} → {h_arr}\nDurée: {duree_str}")
        self.horaires_frame.show()

        # Arrêt de départ
        self.depart_frame.value_label.setText(data.get('arret_depart', 'N/A'))
        self.depart_frame.show()

        # Arrêt d'arrivée
        self.arrivee_frame.value_label.setText(data.get('arret_arrivee', 'N/A'))
        self.arrivee_frame.show()

    def clear_voyage(self):
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
        self.placeholder.show()


class DialogImportCSV(QDialog):
    """Dialogue pour importer des voyages depuis un fichier CSV"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer des voyages depuis CSV")
        self.setMinimumSize(900, 600)

        self.donnees = []
        self.voyages_importes = []

        layout = QVBoxLayout(self)

        # Barre de boutons
        btn_layout = QHBoxLayout()

        btn_charger = QPushButton("📂 Sélectionner un fichier CSV")
        btn_charger.clicked.connect(self.charger_csv)
        btn_layout.addWidget(btn_charger)

        btn_select_all = QPushButton("☑ Sélectionner tous")
        btn_select_all.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_select_all.clicked.connect(self.selectionner_tous)
        btn_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("☐ Désélectionner tous")
        btn_deselect_all.setStyleSheet("background-color: #FF9800; color: white;")
        btn_deselect_all.clicked.connect(self.deselectionner_tous)
        btn_layout.addWidget(btn_deselect_all)

        btn_layout.addStretch()

        self.label_info = QLabel("Aucun fichier chargé")
        self.label_info.setStyleSheet("color: #6b7280;")
        btn_layout.addWidget(self.label_info)

        layout.addLayout(btn_layout)

        # Tableau
        self.tableau = QTableWidget()
        self.tableau.setColumnCount(8)
        self.tableau.setHorizontalHeaderLabels(['✓', 'Ligne', 'Voy.', 'Début', 'Fin', 'De', 'À', 'Js srv'])

        # Configuration du tableau
        header = self.tableau.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 40)
        for i in range(1, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.tableau.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableau.setAlternatingRowColors(True)
        self.tableau.cellClicked.connect(self.on_cell_clicked)

        layout.addWidget(self.tableau)

        # Boutons de validation
        btn_valid_layout = QHBoxLayout()
        btn_valid_layout.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.reject)
        btn_valid_layout.addWidget(btn_annuler)

        btn_importer = QPushButton("Importer les voyages sélectionnés")
        btn_importer.setStyleSheet("background-color: #3498db; color: white; padding: 8px 16px;")
        btn_importer.clicked.connect(self.importer_selection)
        btn_valid_layout.addWidget(btn_importer)

        layout.addLayout(btn_valid_layout)

    def charger_csv(self):
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier CSV",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
        )

        if not fichier:
            return

        try:
            with open(fichier, 'r', encoding='utf-8-sig') as file:
                premiere_ligne = file.readline()
                file.seek(0)

                # Détection du délimiteur
                delimiter = ';' if ';' in premiere_ligne else ','
                lecture = csv.DictReader(file, delimiter=delimiter)
                self.donnees = list(lecture)

            self.remplir_tableau()
            self.label_info.setText(f"{len(self.donnees)} voyage(s) trouvé(s)")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement du CSV : {e}")
            self.donnees = []

    def remplir_tableau(self):
        self.tableau.setRowCount(len(self.donnees))

        for idx, ligne in enumerate(self.donnees):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left: 10px;")
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.tableau.setCellWidget(idx, 0, checkbox_widget)

            # Données
            colonnes = ['Ligne', 'Voy.', 'Début', 'Fin', 'De', 'À', 'Js srv']
            for col_idx, col_name in enumerate(colonnes):
                valeur = ligne.get(col_name, '').strip() if isinstance(ligne.get(col_name, ''), str) else str(ligne.get(col_name, ''))
                item = QTableWidgetItem(valeur)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tableau.setItem(idx, col_idx + 1, item)

    def get_checkbox(self, row):
        """Récupère la checkbox d'une ligne"""
        widget = self.tableau.cellWidget(row, 0)
        if widget:
            checkbox = widget.findChild(QCheckBox)
            return checkbox
        return None

    def on_cell_clicked(self, row, col):
        """Coche/décoche quand on clique sur une ligne"""
        checkbox = self.get_checkbox(row)
        if checkbox and col != 0:
            checkbox.setChecked(not checkbox.isChecked())

    def selectionner_tous(self):
        for row in range(self.tableau.rowCount()):
            checkbox = self.get_checkbox(row)
            if checkbox:
                checkbox.setChecked(True)

    def deselectionner_tous(self):
        for row in range(self.tableau.rowCount()):
            checkbox = self.get_checkbox(row)
            if checkbox:
                checkbox.setChecked(False)

    def importer_selection(self):
        """Importe les voyages sélectionnés"""
        self.voyages_importes = []

        couleurs = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

        for row in range(self.tableau.rowCount()):
            checkbox = self.get_checkbox(row)
            if checkbox and checkbox.isChecked():
                voyage_dict = self.donnees[row]

                # Convertir les heures en format décimal
                heure_debut_str = voyage_dict.get('Début', '00:00').strip()
                heure_fin_str = voyage_dict.get('Fin', '00:00').strip()

                try:
                    h_deb, m_deb = map(int, heure_debut_str.replace('h', ':').replace('H', ':').split(':'))
                    heure_debut = h_deb + m_deb / 60
                except:
                    heure_debut = 8.0

                try:
                    h_fin, m_fin = map(int, heure_fin_str.replace('h', ':').replace('H', ':').split(':'))
                    heure_fin = h_fin + m_fin / 60
                except:
                    heure_fin = heure_debut + 1

                # Calculer la durée
                duree_minutes = int((heure_fin - heure_debut) * 60)
                if duree_minutes <= 0:
                    duree_minutes = 60  # Durée par défaut

                arret_depart = voyage_dict.get('De', '').strip()
                arret_arrivee = voyage_dict.get('À', '').strip()
                num_ligne = voyage_dict.get('Ligne', '').strip()

                # Couleur basée sur le numéro de ligne
                try:
                    couleur_idx = int(num_ligne) % len(couleurs) if num_ligne.isdigit() else hash(num_ligne) % len(couleurs)
                except:
                    couleur_idx = row % len(couleurs)

                voyage_data = {
                    'nom': f"{arret_depart} → {arret_arrivee}",
                    'numero_ligne': num_ligne,
                    'numero_voyage': voyage_dict.get('Voy.', '').strip(),
                    'heure_depart': heure_debut,
                    'duree_minutes': duree_minutes,
                    'arret_depart': arret_depart,
                    'arret_arrivee': arret_arrivee,
                    'js_srv': voyage_dict.get('Js srv', '').strip(),
                    'couleur': couleurs[couleur_idx]
                }
                self.voyages_importes.append(voyage_data)

        if not self.voyages_importes:
            QMessageBox.warning(self, "Attention", "Aucun voyage sélectionné")
            return

        self.accept()

    def get_voyages(self):
        """Retourne les voyages importés"""
        return self.voyages_importes


class DialogAjoutService(QDialog):
    """Dialogue pour ajouter un nouveau service avec limites d'heures"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau service")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Nom du service
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Ex: Service Matin")
        layout.addRow("Nom du service:", self.nom_edit)

        # Heure de début
        self.heure_debut = QTimeEdit()
        self.heure_debut.setTime(QTime(4, 0))
        self.heure_debut.setDisplayFormat("HH:mm")
        layout.addRow("Heure de début:", self.heure_debut)

        # Heure de fin
        self.heure_fin = QTimeEdit()
        self.heure_fin.setTime(QTime(24, 0) if QTime(24, 0).isValid() else QTime(23, 59))
        self.heure_fin.setDisplayFormat("HH:mm")
        layout.addRow("Heure de fin:", self.heure_fin)

        # Note: pour 24h, on utilisera 23:59 ou on gère spécialement
        self.checkbox_minuit = QCheckBox("Jusqu'à minuit (24:00)")
        self.checkbox_minuit.setChecked(True)
        self.checkbox_minuit.stateChanged.connect(self.on_minuit_change)
        layout.addRow("", self.checkbox_minuit)

        # Couleur
        self.couleur_combo = QComboBox()
        couleurs = [
            ("#2c3e50", "Gris foncé"),
            ("#8e44ad", "Violet"),
            ("#c0392b", "Rouge foncé"),
            ("#2980b9", "Bleu"),
            ("#27ae60", "Vert"),
            ("#d35400", "Orange"),
            ("#16a085", "Turquoise"),
        ]
        for code, nom in couleurs:
            self.couleur_combo.addItem(nom, code)
        layout.addRow("Couleur:", self.couleur_combo)

        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.on_minuit_change()

    def on_minuit_change(self):
        """Active/désactive le champ heure de fin selon la checkbox"""
        if self.checkbox_minuit.isChecked():
            self.heure_fin.setEnabled(False)
            self.heure_fin.setTime(QTime(23, 59))
        else:
            self.heure_fin.setEnabled(True)

    def get_data(self):
        """Retourne les données du service"""
        time_debut = self.heure_debut.time()
        heure_debut_dec = time_debut.hour() + time_debut.minute() / 60

        if self.checkbox_minuit.isChecked():
            heure_fin_dec = 24.0
        else:
            time_fin = self.heure_fin.time()
            heure_fin_dec = time_fin.hour() + time_fin.minute() / 60

        return {
            'nom': self.nom_edit.text() or "Nouveau service",
            'heure_debut': heure_debut_dec,
            'heure_fin': heure_fin_dec,
            'couleur': self.couleur_combo.currentData()
        }


class DialogAjoutVoyage(QDialog):
    """Dialogue pour ajouter un nouveau voyage"""

    def __init__(self, services_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un voyage")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        # Service
        self.service_combo = QComboBox()
        for i, service in enumerate(services_data):
            self.service_combo.addItem(service['nom'], i)
        layout.addRow("Service:", self.service_combo)

        # Numéro de ligne
        self.ligne_edit = QLineEdit()
        self.ligne_edit.setPlaceholderText("Ex: L42")
        layout.addRow("Numéro de ligne:", self.ligne_edit)

        # Numéro de voyage
        self.voyage_num_edit = QLineEdit()
        self.voyage_num_edit.setPlaceholderText("Ex: V001")
        layout.addRow("Numéro de voyage:", self.voyage_num_edit)

        # Heure de départ
        self.heure_depart = QTimeEdit()
        self.heure_depart.setTime(QTime(8, 0))
        self.heure_depart.setDisplayFormat("HH:mm")
        layout.addRow("Heure de départ:", self.heure_depart)

        # Durée
        self.duree_spin = QSpinBox()
        self.duree_spin.setRange(15, 480)
        self.duree_spin.setValue(60)
        self.duree_spin.setSuffix(" minutes")
        layout.addRow("Durée:", self.duree_spin)

        # Arrêt de départ
        self.arret_depart_edit = QLineEdit()
        self.arret_depart_edit.setPlaceholderText("Ex: Paris Bercy")
        layout.addRow("Arrêt de départ:", self.arret_depart_edit)

        # Arrêt d'arrivée
        self.arret_arrivee_edit = QLineEdit()
        self.arret_arrivee_edit.setPlaceholderText("Ex: Lyon Perrache")
        layout.addRow("Arrêt d'arrivée:", self.arret_arrivee_edit)

        # Couleur
        self.couleur_combo = QComboBox()
        couleurs = [
            ("#3498db", "Bleu"),
            ("#e74c3c", "Rouge"),
            ("#2ecc71", "Vert"),
            ("#f39c12", "Orange"),
            ("#9b59b6", "Violet"),
            ("#1abc9c", "Turquoise"),
        ]
        for code, nom in couleurs:
            self.couleur_combo.addItem(nom, code)
        layout.addRow("Couleur:", self.couleur_combo)

        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        time = self.heure_depart.time()
        heure_decimale = time.hour() + time.minute() / 60

        # Créer le nom à partir des arrêts
        arret_dep = self.arret_depart_edit.text() or "Départ"
        arret_arr = self.arret_arrivee_edit.text() or "Arrivée"

        return {
            'nom': f"{arret_dep} → {arret_arr}",
            'service_index': self.service_combo.currentData(),
            'numero_ligne': self.ligne_edit.text() or "N/A",
            'numero_voyage': self.voyage_num_edit.text() or "N/A",
            'heure_depart': heure_decimale,
            'duree_minutes': self.duree_spin.value(),
            'arret_depart': arret_dep,
            'arret_arrivee': arret_arr,
            'couleur': self.couleur_combo.currentData()
        }


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Gestion des Services de Bus - Timeline")
        self.setMinimumSize(1600, 750)
        self.resize(1800, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Barre d'outils simplifiée
        toolbar = QHBoxLayout()

        btn_clear = QPushButton("🗑️ Tout effacer")
        btn_clear.clicked.connect(self.effacer_tout)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()

        self.info_label = QLabel("Importez des voyages via le panneau de gauche, puis assignez-les aux services")
        self.info_label.setStyleSheet("color: #6b7280;")
        toolbar.addWidget(self.info_label)

        main_layout.addLayout(toolbar)

        # Layout horizontal: Liste voyages | Timeline (extensible) | Détails
        content_layout = QHBoxLayout()

        # Timeline d'abord (pour pouvoir la passer au panneau voyages)
        self.timeline = TimelineView()
        self.timeline.voyage_selected.connect(self.on_voyage_selected)
        self.timeline.voyage_deselected.connect(self.on_voyage_deselected)

        # Panneau des voyages à gauche
        self.panneau_voyages = PanneauVoyages(self.timeline)
        self.panneau_voyages.voyage_clicked.connect(self.on_voyage_from_list)
        content_layout.addWidget(self.panneau_voyages, stretch=0)

        # Timeline au centre - prend tout l'espace disponible
        content_layout.addWidget(self.timeline, stretch=1)

        # Panneau de détails à droite - taille fixe
        self.detail_panel = DetailPanel()
        self.detail_panel.setFixedWidth(300)
        content_layout.addWidget(self.detail_panel, stretch=0)

        main_layout.addLayout(content_layout)

        # Pas de démo, on commence vide

    def on_voyage_selected(self, data):
        self.detail_panel.show_voyage(data)
        self.info_label.setText(f"Voyage sélectionné: {data['nom']}")

    def on_voyage_deselected(self):
        self.detail_panel.clear_voyage()
        self.info_label.setText("Cliquez sur un voyage pour voir ses détails")

    def on_voyage_from_list(self, voyage_data):
        """Appelé quand on clique sur un voyage dans la liste de gauche"""
        # Afficher les détails
        self.detail_panel.show_voyage(voyage_data)
        self.info_label.setText(f"Voyage sélectionné: {voyage_data['nom']}")

        # Sélectionner visuellement dans la timeline
        for item in self.timeline.voyage_items:
            if item.voyage_data.get('id') == voyage_data.get('id'):
                self.timeline.select_voyage(item)
                break

    def effacer_tout(self):
        """Efface tous les services et voyages"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir tout effacer (voyages importés et services) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.timeline.services_data = []
            self.timeline._redessiner_tout()
            self.panneau_voyages.voyages_importes = []
            self.panneau_voyages.refresh_liste_importes()
            self.panneau_voyages.refresh_services()
            self.detail_panel.clear_voyage()
            self.info_label.setText("Tout a été effacé")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()