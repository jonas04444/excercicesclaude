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
    QFrame, QInputDialog
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
        """Dessine une ligne de service"""
        largeur_totale = (HEURE_FIN - HEURE_DEBUT) * pixels_par_heure

        # Ligne horizontale
        ligne = QGraphicsLineItem(MARGE_GAUCHE, y_position,
                                   MARGE_GAUCHE + largeur_totale, y_position)
        ligne.setPen(QPen(QColor(service_data['couleur']), 2))
        self.scene.addItem(ligne)

        # Label du service
        label = QGraphicsTextItem(service_data['nom'])
        label.setDefaultTextColor(QColor('#2c3e50'))
        label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        label.setPos(5, y_position - 10)
        self.scene.addItem(label)

        # Fond alterné
        index = (y_position - MARGE_HAUT) // HAUTEUR_SERVICE
        if index % 2 == 0:
            fond = QGraphicsRectItem(MARGE_GAUCHE, y_position - 25,
                                      largeur_totale, HAUTEUR_SERVICE)
            fond.setBrush(QBrush(QColor(240, 240, 240, 100)))
            fond.setPen(QPen(Qt.PenStyle.NoPen))
            fond.setZValue(-1)
            self.scene.addItem(fond)

    def _dessiner_voyage(self, voyage_data, y_position, pixels_par_heure):
        """Dessine un voyage et retourne l'item"""
        item = VoyageItem(voyage_data, y_position, self, pixels_par_heure)
        self.scene.addItem(item)
        return item

    def ajouter_service(self, nom, couleur='#34495e'):
        """Ajoute un nouveau service"""
        service_data = {
            'nom': nom,
            'couleur': couleur,
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

        # Layout horizontal: Timeline (extensible) | Détails (fixe)
        content_layout = QHBoxLayout()

        # Timeline - prend tout l'espace disponible
        self.timeline = TimelineView()
        self.timeline.voyage_selected.connect(self.on_voyage_selected)
        self.timeline.voyage_deselected.connect(self.on_voyage_deselected)
        self.timeline.setSizePolicy(self.timeline.sizePolicy().horizontalPolicy(),
                                     self.timeline.sizePolicy().verticalPolicy())
        content_layout.addWidget(self.timeline, stretch=1)

        # Panneau de détails - taille fixe
        self.detail_panel = DetailPanel()
        self.detail_panel.setFixedWidth(290)
        content_layout.addWidget(self.detail_panel, stretch=0)

        main_layout.addLayout(content_layout)

        self._creer_demo()

    def _creer_demo(self):
        # Créer les services
        self.timeline.ajouter_service("Service A", "#2c3e50")
        self.timeline.ajouter_service("Service B", "#8e44ad")
        self.timeline.ajouter_service("Service C", "#c0392b")

        # Service A - index 0
        self.timeline.ajouter_voyage(0, {
            'nom': "Paris → Lyon",
            'numero_ligne': "L01",
            'numero_voyage': "V001",
            'heure_depart': 6.5,
            'duree_minutes': 120,
            'arret_depart': "Paris Bercy",
            'arret_arrivee': "Lyon Perrache",
            'couleur': '#3498db'
        })
        self.timeline.ajouter_voyage(0, {
            'nom': "Lyon → Marseille",
            'numero_ligne': "L01",
            'numero_voyage': "V002",
            'heure_depart': 10,
            'duree_minutes': 90,
            'arret_depart': "Lyon Perrache",
            'arret_arrivee': "Marseille St-Charles",
            'couleur': '#3498db'
        })
        self.timeline.ajouter_voyage(0, {
            'nom': "Marseille → Nice",
            'numero_ligne': "L01",
            'numero_voyage': "V003",
            'heure_depart': 14,
            'duree_minutes': 150,
            'arret_depart': "Marseille St-Charles",
            'arret_arrivee': "Nice Côte d'Azur",
            'couleur': '#2ecc71'
        })

        # Service B - index 1
        self.timeline.ajouter_voyage(1, {
            'nom': "Bordeaux → Toulouse",
            'numero_ligne': "L02",
            'numero_voyage': "V010",
            'heure_depart': 7,
            'duree_minutes': 150,
            'arret_depart': "Bordeaux St-Jean",
            'arret_arrivee': "Toulouse Matabiau",
            'couleur': '#e74c3c'
        })
        self.timeline.ajouter_voyage(1, {
            'nom': "Toulouse → Montpellier",
            'numero_ligne': "L02",
            'numero_voyage': "V011",
            'heure_depart': 12,
            'duree_minutes': 180,
            'arret_depart': "Toulouse Matabiau",
            'arret_arrivee': "Montpellier Sud",
            'couleur': '#f39c12'
        })

        # Service C - index 2
        self.timeline.ajouter_voyage(2, {
            'nom': "Paris → Lille",
            'numero_ligne': "L03",
            'numero_voyage': "V020",
            'heure_depart': 8,
            'duree_minutes': 60,
            'arret_depart': "Paris Nord",
            'arret_arrivee': "Lille Flandres",
            'couleur': '#9b59b6'
        })
        self.timeline.ajouter_voyage(2, {
            'nom': "Lille → Bruxelles",
            'numero_ligne': "L03",
            'numero_voyage': "V021",
            'heure_depart': 11,
            'duree_minutes': 45,
            'arret_depart': "Lille Flandres",
            'arret_arrivee': "Bruxelles Midi",
            'couleur': '#9b59b6'
        })
        self.timeline.ajouter_voyage(2, {
            'nom': "Bruxelles → Amsterdam",
            'numero_ligne': "L03",
            'numero_voyage': "V022",
            'heure_depart': 15,
            'duree_minutes': 120,
            'arret_depart': "Bruxelles Midi",
            'arret_arrivee': "Amsterdam Centraal",
            'couleur': '#1abc9c'
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
        if not self.timeline.services_data:
            self.info_label.setText("⚠️ Ajoutez d'abord un service!")
            return

        dialog = DialogAjoutVoyage(self.timeline.services_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            service_index = data.pop('service_index')
            self.timeline.ajouter_voyage(service_index, data)
            self.info_label.setText(f"Voyage '{data['nom']}' ajouté")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()