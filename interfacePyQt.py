"""
Application de gestion de services de bus avec timeline
Chaque service est une ligne horizontale, les voyages sont des rectangles sur cette ligne
"""

import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsLineItem, QPushButton, QLabel, QSpinBox, QTimeEdit,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QRectF, QTime, QPointF
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter


# Configuration de la timeline
HEURE_DEBUT = 5  # 5h du matin
HEURE_FIN = 23   # 23h
PIXELS_PAR_HEURE = 80
HAUTEUR_SERVICE = 50
MARGE_GAUCHE = 120
MARGE_HAUT = 40


class VoyageItem(QGraphicsRectItem):
    """Rectangle représentant un voyage sur la timeline"""

    def __init__(self, voyage_data, y_position, parent=None):
        self.voyage_data = voyage_data

        # Calcul de la position X basée sur l'heure de départ
        heure_depart = voyage_data['heure_depart']
        x = MARGE_GAUCHE + (heure_depart - HEURE_DEBUT) * PIXELS_PAR_HEURE

        # Calcul de la largeur basée sur la durée
        duree_heures = voyage_data['duree_minutes'] / 60
        largeur = duree_heures * PIXELS_PAR_HEURE

        # Position Y centrée sur la ligne du service
        y = y_position - 15

        super().__init__(x, y, largeur, 30)

        # Style du rectangle
        couleur = QColor(voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        self.setPen(QPen(couleur.darker(120), 2))

        # Rendre l'item interactif
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        # Texte du voyage
        self.text_item = QGraphicsTextItem(voyage_data['nom'], self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.text_item.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.text_item.setPos(x + 5, y + 5)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor('#2ecc71')))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        couleur = QColor(self.voyage_data.get('couleur', '#3498db'))
        self.setBrush(QBrush(couleur))
        super().hoverLeaveEvent(event)


class ServiceLine:
    """Représente une ligne de service avec sa timeline"""

    def __init__(self, scene, nom, y_position, couleur='#34495e'):
        self.scene = scene
        self.nom = nom
        self.y_position = y_position
        self.couleur = couleur
        self.voyages = []

        self._dessiner_ligne()

    def _dessiner_ligne(self):
        # Ligne horizontale de la timeline
        largeur_totale = (HEURE_FIN - HEURE_DEBUT) * PIXELS_PAR_HEURE
        ligne = QGraphicsLineItem(MARGE_GAUCHE, self.y_position,
                                   MARGE_GAUCHE + largeur_totale, self.y_position)
        ligne.setPen(QPen(QColor(self.couleur), 2))
        self.scene.addItem(ligne)

        # Label du service (à gauche)
        label = QGraphicsTextItem(self.nom)
        label.setDefaultTextColor(QColor('#2c3e50'))
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setPos(10, self.y_position - 10)
        self.scene.addItem(label)

        # Fond alterné pour meilleure lisibilité
        index = (self.y_position - MARGE_HAUT) // HAUTEUR_SERVICE
        if index % 2 == 0:
            fond = QGraphicsRectItem(MARGE_GAUCHE, self.y_position - 25,
                                      largeur_totale, HAUTEUR_SERVICE)
            fond.setBrush(QBrush(QColor(240, 240, 240, 100)))
            fond.setPen(QPen(Qt.PenStyle.NoPen))
            fond.setZValue(-1)
            self.scene.addItem(fond)

    def ajouter_voyage(self, voyage_data):
        """Ajoute un voyage à ce service"""
        voyage_item = VoyageItem(voyage_data, self.y_position)
        self.scene.addItem(voyage_item)
        self.voyages.append(voyage_item)
        return voyage_item


class TimelineView(QGraphicsView):
    """Vue principale de la timeline"""

    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Configuration de la vue
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.services = []

        self._dessiner_echelle_temps()

    def _dessiner_echelle_temps(self):
        """Dessine l'échelle de temps en haut"""
        for heure in range(HEURE_DEBUT, HEURE_FIN + 1):
            x = MARGE_GAUCHE + (heure - HEURE_DEBUT) * PIXELS_PAR_HEURE

            # Ligne verticale de repère
            ligne = QGraphicsLineItem(x, MARGE_HAUT - 10, x, MARGE_HAUT)
            ligne.setPen(QPen(QColor('#7f8c8d'), 1))
            self.scene.addItem(ligne)

            # Label de l'heure
            label = QGraphicsTextItem(f"{heure:02d}:00")
            label.setDefaultTextColor(QColor('#7f8c8d'))
            label.setFont(QFont("Arial", 8))
            label.setPos(x - 15, MARGE_HAUT - 30)
            self.scene.addItem(label)

            # Ligne verticale en pointillés sur toute la hauteur
            ligne_guide = QGraphicsLineItem(x, MARGE_HAUT, x, 600)
            pen = QPen(QColor('#ecf0f1'), 1, Qt.PenStyle.DotLine)
            ligne_guide.setPen(pen)
            ligne_guide.setZValue(-2)
            self.scene.addItem(ligne_guide)

    def ajouter_service(self, nom, couleur='#34495e'):
        """Ajoute un nouveau service à la timeline"""
        y_position = MARGE_HAUT + len(self.services) * HAUTEUR_SERVICE + 30
        service = ServiceLine(self.scene, nom, y_position, couleur)
        self.services.append(service)

        # Mettre à jour la taille de la scène
        largeur = MARGE_GAUCHE + (HEURE_FIN - HEURE_DEBUT) * PIXELS_PAR_HEURE + 50
        hauteur = y_position + HAUTEUR_SERVICE
        self.scene.setSceneRect(0, 0, largeur, hauteur)

        return service


class DialogAjoutVoyage(QDialog):
    """Dialogue pour ajouter un nouveau voyage"""

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un voyage")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)

        # Nom du voyage
        self.nom_edit = QLineEdit()
        self.nom_edit.setPlaceholderText("Ex: Paris → Lyon")
        layout.addRow("Nom du voyage:", self.nom_edit)

        # Service
        self.service_combo = QComboBox()
        for i, service in enumerate(services):
            self.service_combo.addItem(service.nom, i)
        layout.addRow("Service:", self.service_combo)

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
        """Retourne les données du voyage"""
        time = self.heure_depart.time()
        heure_decimale = time.hour() + time.minute() / 60

        return {
            'nom': self.nom_edit.text() or "Voyage",
            'service_index': self.service_combo.currentData(),
            'heure_depart': heure_decimale,
            'duree_minutes': self.duree_spin.value(),
            'couleur': self.couleur_combo.currentData()
        }


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚌 Gestion des Services de Bus - Timeline")
        self.setMinimumSize(1200, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
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

        # Label d'info
        self.info_label = QLabel("Cliquez sur les boutons pour ajouter des services et voyages")
        toolbar.addWidget(self.info_label)

        main_layout.addLayout(toolbar)

        # Timeline
        self.timeline = TimelineView()
        main_layout.addWidget(self.timeline)

        # Ajouter quelques services de démonstration
        self._creer_demo()

    def _creer_demo(self):
        """Crée des données de démonstration"""
        # Services
        service1 = self.timeline.ajouter_service("Service A - Ligne 1", "#2c3e50")
        service2 = self.timeline.ajouter_service("Service B - Ligne 2", "#8e44ad")
        service3 = self.timeline.ajouter_service("Service C - Express", "#c0392b")

        # Voyages de démonstration
        service1.ajouter_voyage({
            'nom': "Paris → Lyon",
            'heure_depart': 6.5,  # 6h30
            'duree_minutes': 120,
            'couleur': '#3498db'
        })
        service1.ajouter_voyage({
            'nom': "Lyon → Marseille",
            'heure_depart': 10,
            'duree_minutes': 90,
            'couleur': '#3498db'
        })
        service1.ajouter_voyage({
            'nom': "Marseille → Nice",
            'heure_depart': 14,
            'duree_minutes': 150,
            'couleur': '#2ecc71'
        })

        service2.ajouter_voyage({
            'nom': "Bordeaux → Toulouse",
            'heure_depart': 7,
            'duree_minutes': 150,
            'couleur': '#e74c3c'
        })
        service2.ajouter_voyage({
            'nom': "Toulouse → Montpellier",
            'heure_depart': 12,
            'duree_minutes': 180,
            'couleur': '#f39c12'
        })

        service3.ajouter_voyage({
            'nom': "Express Paris → Lille",
            'heure_depart': 8,
            'duree_minutes': 60,
            'couleur': '#9b59b6'
        })
        service3.ajouter_voyage({
            'nom': "Express Lille → Bruxelles",
            'heure_depart': 11,
            'duree_minutes': 45,
            'couleur': '#9b59b6'
        })
        service3.ajouter_voyage({
            'nom': "Express Bruxelles → Amsterdam",
            'heure_depart': 15,
            'duree_minutes': 120,
            'couleur': '#1abc9c'
        })

    def ajouter_service(self):
        """Ajoute un nouveau service"""
        nom, ok = self._input_dialog("Nouveau service", "Nom du service:")
        if ok and nom:
            self.timeline.ajouter_service(nom)
            self.info_label.setText(f"Service '{nom}' ajouté")

    def _input_dialog(self, titre, label):
        """Dialogue simple pour saisir du texte"""
        from PyQt6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, titre, label)

    def ajouter_voyage(self):
        """Ouvre le dialogue pour ajouter un voyage"""
        if not self.timeline.services:
            self.info_label.setText("⚠️ Ajoutez d'abord un service!")
            return

        dialog = DialogAjoutVoyage(self.timeline.services, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            service = self.timeline.services[data['service_index']]
            service.ajouter_voyage(data)
            self.info_label.setText(f"Voyage '{data['nom']}' ajouté au {service.nom}")


def main():
    app = QApplication(sys.argv)

    # Style moderne
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()