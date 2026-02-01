"""
Application de gestion de services de bus avec timeline
Chaque service est une ligne horizontale, les voyages sont des rectangles sur cette ligne
Avec panneau de détails à droite
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QPushButton, QLabel, QSpinBox, QTimeEdit,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QFrame, QProgressBar, QSplitter, QInputDialog
)
from PyQt6.QtCore import Qt, QRectF, QTime, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter


# Configuration de la timeline
HEURE_DEBUT = 5
HEURE_FIN = 23
PIXELS_PAR_HEURE = 60
HAUTEUR_SERVICE = 50
MARGE_GAUCHE = 100
MARGE_HAUT = 40


class VoyageItem(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_data, y_position, timeline_view, parent=None):
        self.voyage_data = voyage_data
        self.timeline_view = timeline_view
        self.y_position = y_position
        self.is_selected = False

        # Calcul de la position X basée sur l'heure de départ
        heure_depart = voyage_data['heure_depart']
        x = MARGE_GAUCHE + (heure_depart - HEURE_DEBUT) * PIXELS_PAR_HEURE

        # Calcul de la largeur basée sur la durée
        duree_heures = voyage_data['duree_minutes'] / 60
        largeur = max(duree_heures * PIXELS_PAR_HEURE, 40)

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

        # Texte du voyage
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


class ServiceLine:
    """Représente une ligne de service avec sa timeline"""

    def __init__(self, scene, nom, y_position, timeline_view, couleur='#34495e'):
        self.scene = scene
        self.nom = nom
        self.y_position = y_position
        self.timeline_view = timeline_view
        self.couleur = couleur
        self.voyages = []

        self._dessiner_ligne()

    def _dessiner_ligne(self):
        largeur_totale = (HEURE_FIN - HEURE_DEBUT) * PIXELS_PAR_HEURE
        ligne = QGraphicsLineItem(MARGE_GAUCHE, self.y_position,
                                   MARGE_GAUCHE + largeur_totale, self.y_position)
        ligne.setPen(QPen(QColor(self.couleur), 2))
        self.scene.addItem(ligne)

        label = QGraphicsTextItem(self.nom)
        label.setDefaultTextColor(QColor('#2c3e50'))
        label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        label.setPos(5, self.y_position - 10)
        self.scene.addItem(label)

        index = (self.y_position - MARGE_HAUT) // HAUTEUR_SERVICE
        if index % 2 == 0:
            fond = QGraphicsRectItem(MARGE_GAUCHE, self.y_position - 25,
                                      largeur_totale, HAUTEUR_SERVICE)
            fond.setBrush(QBrush(QColor(240, 240, 240, 100)))
            fond.setPen(QPen(Qt.PenStyle.NoPen))
            fond.setZValue(-1)
            self.scene.addItem(fond)

    def ajouter_voyage(self, voyage_data):
        voyage_data['service_nom'] = self.nom
        voyage_item = VoyageItem(voyage_data, self.y_position, self.timeline_view)
        self.scene.addItem(voyage_item)
        self.voyages.append(voyage_item)
        return voyage_item


class TimelineView(QGraphicsView):
    """Vue principale de la timeline"""

    voyage_selected = pyqtSignal(dict)
    voyage_deselected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumHeight(200)

        self.services = []
        self.selected_voyage = None

        self._dessiner_echelle_temps()

    def _dessiner_echelle_temps(self):
        for heure in range(HEURE_DEBUT, HEURE_FIN + 1):
            x = MARGE_GAUCHE + (heure - HEURE_DEBUT) * PIXELS_PAR_HEURE

            ligne = QGraphicsLineItem(x, MARGE_HAUT - 10, x, MARGE_HAUT)
            ligne.setPen(QPen(QColor('#7f8c8d'), 1))
            self.scene.addItem(ligne)

            label = QGraphicsTextItem(f"{heure:02d}h")
            label.setDefaultTextColor(QColor('#7f8c8d'))
            label.setFont(QFont("Arial", 8))
            label.setPos(x - 12, MARGE_HAUT - 30)
            self.scene.addItem(label)

            ligne_guide = QGraphicsLineItem(x, MARGE_HAUT, x, 600)
            pen = QPen(QColor('#ecf0f1'), 1, Qt.PenStyle.DotLine)
            ligne_guide.setPen(pen)
            ligne_guide.setZValue(-2)
            self.scene.addItem(ligne_guide)

    def ajouter_service(self, nom, couleur='#34495e'):
        y_position = MARGE_HAUT + len(self.services) * HAUTEUR_SERVICE + 30
        service = ServiceLine(self.scene, nom, y_position, self, couleur)
        self.services.append(service)

        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * PIXELS_PAR_HEURE + 50
        hauteur = y_position + HAUTEUR_SERVICE
        self.scene.setSceneRect(0, 0, largeur, hauteur)

        return service

    def select_voyage(self, voyage_item):
        # Désélectionner l'ancien
        if self.selected_voyage and self.selected_voyage != voyage_item:
            self.selected_voyage.set_selected(False)

        # Si on clique sur le même, on désélectionne
        if self.selected_voyage == voyage_item:
            voyage_item.set_selected(False)
            self.selected_voyage = None
            self.voyage_deselected.emit()
        else:
            voyage_item.set_selected(True)
            self.selected_voyage = voyage_item
            self.voyage_selected.emit(voyage_item.voyage_data)


class DetailPanel(QFrame):
    """Panneau de détails du voyage sélectionné"""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)

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

        # Widgets de détails (cachés par défaut)
        self.nom_label = QLabel()
        self.nom_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.nom_label.setWordWrap(True)
        self.nom_label.hide()
        self.details_layout.addWidget(self.nom_label)

        self.service_label = QLabel()
        self.service_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        self.service_label.hide()
        self.details_layout.addWidget(self.service_label)

        # Horaires
        self.horaires_frame = self._create_info_frame("🕐", "Horaires", "#f3f4f6")
        self.horaires_frame.hide()
        self.details_layout.addWidget(self.horaires_frame)

        # Chauffeur
        self.chauffeur_frame = self._create_info_frame("👤", "Chauffeur", "#dbeafe")
        self.chauffeur_frame.hide()
        self.details_layout.addWidget(self.chauffeur_frame)

        # Bus
        self.bus_frame = self._create_info_frame("🚌", "Véhicule", "#dcfce7")
        self.bus_frame.hide()
        self.details_layout.addWidget(self.bus_frame)

        # Remplissage
        self.remplissage_frame = QFrame()
        self.remplissage_frame.setStyleSheet("background-color: #f3f4f6; border-radius: 8px; padding: 5px;")
        remplissage_layout = QVBoxLayout(self.remplissage_frame)

        self.remplissage_header = QHBoxLayout()
        self.remplissage_title = QLabel("Remplissage")
        self.remplissage_title.setStyleSheet("color: #6b7280; font-size: 11px;")
        self.statut_label = QLabel()
        self.statut_label.setStyleSheet("font-size: 10px; padding: 2px 8px; border-radius: 10px;")
        self.remplissage_header.addWidget(self.remplissage_title)
        self.remplissage_header.addStretch()
        self.remplissage_header.addWidget(self.statut_label)
        remplissage_layout.addLayout(self.remplissage_header)

        self.places_label = QLabel()
        self.places_label.setFont(QFont("Arial", 11))
        remplissage_layout.addWidget(self.places_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(20)
        remplissage_layout.addWidget(self.progress_bar)

        self.remplissage_frame.hide()
        self.details_layout.addWidget(self.remplissage_frame)

        # Places disponibles
        self.dispo_frame = QFrame()
        self.dispo_frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #d1d5db;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        dispo_layout = QVBoxLayout(self.dispo_frame)
        self.dispo_count = QLabel()
        self.dispo_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dispo_count.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.dispo_count.setStyleSheet("color: #16a34a; border: none;")
        dispo_layout.addWidget(self.dispo_count)
        self.dispo_text = QLabel("places disponibles")
        self.dispo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dispo_text.setStyleSheet("color: #6b7280; font-size: 11px; border: none;")
        dispo_layout.addWidget(self.dispo_text)
        self.dispo_frame.hide()
        self.details_layout.addWidget(self.dispo_frame)

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
        value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
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

        # Nom et service
        self.nom_label.setText(data['nom'])
        self.nom_label.show()

        self.service_label.setText(data.get('service_nom', ''))
        self.service_label.show()

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

        # Chauffeur
        self.chauffeur_frame.value_label.setText(data.get('chauffeur', 'Non assigné'))
        self.chauffeur_frame.show()

        # Bus
        self.bus_frame.value_label.setText(data.get('bus', 'Non assigné'))
        self.bus_frame.show()

        # Remplissage
        places = data.get('places', 50)
        reservees = data.get('places_reservees', 0)
        taux = int((reservees / places) * 100) if places > 0 else 0

        self.places_label.setText(f"<b style='font-size: 18px;'>{reservees}</b> / {places} places")
        self.progress_bar.setValue(taux)

        # Couleur et statut
        if taux >= 100:
            statut, couleur_statut, bg_statut = "Complet", "#dc2626", "#fecaca"
            bar_color = "#ef4444"
        elif taux >= 75:
            statut, couleur_statut, bg_statut = "Presque complet", "#ea580c", "#fed7aa"
            bar_color = "#f97316"
        elif taux >= 50:
            statut, couleur_statut, bg_statut = "Bien rempli", "#ca8a04", "#fef08a"
            bar_color = "#eab308"
        else:
            statut, couleur_statut, bg_statut = "Disponible", "#16a34a", "#bbf7d0"
            bar_color = "#22c55e"

        self.statut_label.setText(statut)
        self.statut_label.setStyleSheet(f"color: {couleur_statut}; background-color: {bg_statut}; font-size: 10px; padding: 2px 8px; border-radius: 10px;")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 5px;
                background-color: #e5e7eb;
                text-align: center;
            }}
            QProgressBar::chunk {{
                border-radius: 5px;
                background-color: {bar_color};
            }}
        """)
        self.remplissage_frame.show()

        # Places disponibles
        dispo = places - reservees
        self.dispo_count.setText(str(dispo))
        self.dispo_frame.show()

    def clear_voyage(self):
        self.header.setStyleSheet("""
            QLabel {
                background-color: #6b7280;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.nom_label.hide()
        self.service_label.hide()
        self.horaires_frame.hide()
        self.chauffeur_frame.hide()
        self.bus_frame.hide()
        self.remplissage_frame.hide()
        self.dispo_frame.hide()
        self.placeholder.show()


class DialogAjoutVoyage(QDialog):
    """Dialogue pour ajouter un nouveau voyage"""

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un voyage")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Ex: Paris → Lyon")
        layout.addRow("Nom du voyage:", self.nom_edit)

        self.service_combo = QComboBox()
        for i, service in enumerate(services):
            self.service_combo.addItem(service.nom, i)
        layout.addRow("Service:", self.service_combo)

        self.heure_depart = QTimeEdit()
        self.heure_depart.setTime(QTime(8, 0))
        self.heure_depart.setDisplayFormat("HH:mm")
        layout.addRow("Heure de départ:", self.heure_depart)

        self.duree_spin = QSpinBox()
        self.duree_spin.setRange(15, 480)
        self.duree_spin.setValue(60)
        self.duree_spin.setSuffix(" minutes")
        layout.addRow("Durée:", self.duree_spin)

        self.chauffeur_edit = QLineEdit()
        self.chauffeur_edit.setPlaceholderText("Nom du chauffeur")
        layout.addRow("Chauffeur:", self.chauffeur_edit)

        self.bus_edit = QLineEdit()
        self.bus_edit.setPlaceholderText("Ex: Bus 42 - Mercedes")
        layout.addRow("Bus:", self.bus_edit)

        self.places_spin = QSpinBox()
        self.places_spin.setRange(1, 100)
        self.places_spin.setValue(50)
        layout.addRow("Places:", self.places_spin)

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        time = self.heure_depart.time()
        heure_decimale = time.hour() + time.minute() / 60

        return {
            'nom': self.nom_edit.text() or "Voyage",
            'service_index': self.service_combo.currentData(),
            'heure_depart': heure_decimale,
            'duree_minutes': self.duree_spin.value(),
            'chauffeur': self.chauffeur_edit.text() or "Non assigné",
            'bus': self.bus_edit.text() or "Non assigné",
            'places': self.places_spin.value(),
            'places_reservees': 0,
            'couleur': self.couleur_combo.currentData()
        }


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Gestion des Services de Bus - Timeline")
        self.setMinimumSize(1100, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Barre d'outils
        toolbar = QHBoxLayout()

        btn_add_service = QPushButton("➕ Ajouter Service")
        btn_add_service.clicked.connect(self.ajouter_service)
        toolbar.addWidget(btn_add_service)

        btn_add_voyage = QPushButton("🚌 Ajouter Voyage")
        btn_add_voyage.clicked.connect(self.ajouter_voyage)
        toolbar.addWidget(btn_add_voyage)

        toolbar.addStretch()

        self.info_label = QLabel("Cliquez sur un voyage pour voir ses détails")
        self.info_label.setStyleSheet("color: #6b7280;")
        toolbar.addWidget(self.info_label)

        main_layout.addLayout(toolbar)

        # Splitter horizontal: Timeline | Détails
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Timeline
        self.timeline = TimelineView()
        self.timeline.voyage_selected.connect(self.on_voyage_selected)
        self.timeline.voyage_deselected.connect(self.on_voyage_deselected)
        splitter.addWidget(self.timeline)

        # Panneau de détails
        self.detail_panel = DetailPanel()
        splitter.addWidget(self.detail_panel)

        splitter.setSizes([800, 300])
        main_layout.addWidget(splitter)

        self._creer_demo()

    def _creer_demo(self):
        service1 = self.timeline.ajouter_service("Service A", "#2c3e50")
        service2 = self.timeline.ajouter_service("Service B", "#8e44ad")
        service3 = self.timeline.ajouter_service("Service C", "#c0392b")

        service1.ajouter_voyage({
            'nom': "Paris → Lyon",
            'heure_depart': 6.5,
            'duree_minutes': 120,
            'couleur': '#3498db',
            'chauffeur': 'Jean Dupont',
            'bus': 'Bus 42 - Mercedes Citaro',
            'places': 54,
            'places_reservees': 38
        })
        service1.ajouter_voyage({
            'nom': "Lyon → Marseille",
            'heure_depart': 10,
            'duree_minutes': 90,
            'couleur': '#3498db',
            'chauffeur': 'Marie Martin',
            'bus': 'Bus 15 - Iveco Crossway',
            'places': 50,
            'places_reservees': 45
        })
        service1.ajouter_voyage({
            'nom': "Marseille → Nice",
            'heure_depart': 14,
            'duree_minutes': 150,
            'couleur': '#2ecc71',
            'chauffeur': 'Jean Dupont',
            'bus': 'Bus 42 - Mercedes Citaro',
            'places': 54,
            'places_reservees': 22
        })

        service2.ajouter_voyage({
            'nom': "Bordeaux → Toulouse",
            'heure_depart': 7,
            'duree_minutes': 150,
            'couleur': '#e74c3c',
            'chauffeur': 'Pierre Durand',
            'bus': 'Bus 28 - Setra S 415',
            'places': 48,
            'places_reservees': 48
        })
        service2.ajouter_voyage({
            'nom': "Toulouse → Montpellier",
            'heure_depart': 12,
            'duree_minutes': 180,
            'couleur': '#f39c12',
            'chauffeur': 'Pierre Durand',
            'bus': 'Bus 28 - Setra S 415',
            'places': 48,
            'places_reservees': 31
        })

        service3.ajouter_voyage({
            'nom': "Paris → Lille",
            'heure_depart': 8,
            'duree_minutes': 60,
            'couleur': '#9b59b6',
            'chauffeur': 'Sophie Bernard',
            'bus': 'Bus 07 - MAN Lion\'s Coach',
            'places': 44,
            'places_reservees': 44
        })
        service3.ajouter_voyage({
            'nom': "Lille → Bruxelles",
            'heure_depart': 11,
            'duree_minutes': 45,
            'couleur': '#9b59b6',
            'chauffeur': 'Sophie Bernard',
            'bus': 'Bus 07 - MAN Lion\'s Coach',
            'places': 44,
            'places_reservees': 40
        })
        service3.ajouter_voyage({
            'nom': "Bruxelles → Amsterdam",
            'heure_depart': 15,
            'duree_minutes': 120,
            'couleur': '#1abc9c',
            'chauffeur': 'Sophie Bernard',
            'bus': 'Bus 07 - MAN Lion\'s Coach',
            'places': 44,
            'places_reservees': 12
        })

    def on_voyage_selected(self, data):
        self.detail_panel.show_voyage(data)
        self.info_label.setText(f"Voyage sélectionné: {data['nom']}")

    def on_voyage_deselected(self):
        self.detail_panel.clear_voyage()
        self.info_label.setText("Cliquez sur un voyage pour voir ses détails")

    def ajouter_service(self):
        nom, ok = QInputDialog.getText(self, "Nouveau service", "Nom du service:")
        if ok and nom:
            self.timeline.ajouter_service(nom)
            self.info_label.setText(f"Service '{nom}' ajouté")

    def ajouter_voyage(self):
        if not self.timeline.services:
            self.info_label.setText("⚠️ Ajoutez d'abord un service!")
            return

        dialog = DialogAjoutVoyage(self.timeline.services, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            service = self.timeline.services[data['service_index']]
            service.ajouter_voyage(data)
            self.info_label.setText(f"Voyage '{data['nom']}' ajouté")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()