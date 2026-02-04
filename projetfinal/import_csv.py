"""
Module d'import CSV pour les voyages
Fichier: import_csv.py
"""

import csv
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class DialogImportCSV(QDialog):
    """Dialogue pour importer des voyages depuis un fichier CSV"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer des voyages depuis CSV")
        self.setMinimumSize(900, 600)

        self.donnees = []
        self.donnees_selectionnees = []

        layout = QVBoxLayout(self)

        # Bouton sélection fichier
        btn_layout = QHBoxLayout()

        self.btn_parcourir = QPushButton("📂 Parcourir...")
        self.btn_parcourir.setStyleSheet("padding: 8px 16px;")
        self.btn_parcourir.clicked.connect(self.parcourir_fichier)
        btn_layout.addWidget(self.btn_parcourir)

        self.label_fichier = QLabel("Aucun fichier sélectionné")
        self.label_fichier.setStyleSheet("color: #666;")
        btn_layout.addWidget(self.label_fichier)

        btn_layout.addStretch()

        # Boutons sélection
        btn_select_all = QPushButton("✅ Tout sélectionner")
        btn_select_all.clicked.connect(self.selectionner_tous)
        btn_layout.addWidget(btn_select_all)

        btn_deselect_all = QPushButton("❌ Tout désélectionner")
        btn_deselect_all.clicked.connect(self.deselectionner_tous)
        btn_layout.addWidget(btn_deselect_all)

        layout.addLayout(btn_layout)

        # Info colonnes attendues
        info_label = QLabel("📋 Colonnes attendues : Ligne, Voy., Début, Fin, De, À, Js srv")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        layout.addWidget(info_label)

        # Tableau de prévisualisation
        self.tableau = QTableWidget()
        self.tableau.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableau.setAlternatingRowColors(True)
        self.tableau.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.tableau)

        # Label compteur
        self.label_selection = QLabel("0 voyage(s) sélectionné(s)")
        self.label_selection.setStyleSheet("font-weight: bold; color: #2980b9;")
        layout.addWidget(self.label_selection)

        # Boutons d'action
        btn_actions = QHBoxLayout()
        btn_actions.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.reject)
        btn_actions.addWidget(btn_annuler)

        self.btn_importer = QPushButton("📥 Importer la sélection")
        self.btn_importer.setStyleSheet("background-color: #27ae60; color: white; padding: 10px 20px; font-weight: bold;")
        self.btn_importer.clicked.connect(self.importer_selection)
        self.btn_importer.setEnabled(False)
        btn_actions.addWidget(self.btn_importer)

        layout.addLayout(btn_actions)

    def parcourir_fichier(self):
        """Ouvre le dialogue de sélection de fichier"""
        fichier, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier CSV",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
        )

        if fichier:
            self.charger_csv(fichier)

    def charger_csv(self, chemin_fichier):
        """Charge et affiche le contenu du CSV"""
        try:
            with open(chemin_fichier, 'r', encoding='utf-8-sig') as file:
                # Détecter le délimiteur
                premiere_ligne = file.readline()
                file.seek(0)

                if ';' in premiere_ligne:
                    delimiter = ';'
                else:
                    delimiter = ','

                reader = csv.DictReader(file, delimiter=delimiter)
                self.donnees = list(reader)

            if not self.donnees:
                QMessageBox.warning(self, "Attention", "Le fichier CSV est vide")
                return

            # Afficher le nom du fichier
            nom_fichier = chemin_fichier.split('/')[-1].split('\\')[-1]
            self.label_fichier.setText(f"✅ {nom_fichier} ({len(self.donnees)} lignes)")
            self.label_fichier.setStyleSheet("color: #27ae60; font-weight: bold;")

            self.afficher_tableau()
            self.btn_importer.setEnabled(True)
            self.maj_compteur()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement :\n{str(e)}")

    def afficher_tableau(self):
        """Affiche les données dans le tableau"""
        if not self.donnees:
            return

        # Colonnes à afficher
        colonnes = ['✓', 'Ligne', 'Voy.', 'Début', 'Fin', 'De', 'À', 'Js srv']

        self.tableau.setColumnCount(len(colonnes))
        self.tableau.setRowCount(len(self.donnees))
        self.tableau.setHorizontalHeaderLabels(colonnes)

        # Style header
        header = self.tableau.horizontalHeader()
        header.setFont(QFont("Arial", 9, QFont.Weight.Bold))

        for row, ligne in enumerate(self.donnees):
            # Case sélection (☐ ou ☑)
            item_check = QTableWidgetItem('☑')
            item_check.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_check.setFont(QFont("Arial", 12))
            self.tableau.setItem(row, 0, item_check)

            # Données du voyage
            valeurs = [
                ligne.get('Ligne', ligne.get('ligne', '')),
                ligne.get('Voy.', ligne.get('Voyage', ligne.get('voy', ''))),
                ligne.get('Début', ligne.get('Debut', '')),
                ligne.get('Fin', ligne.get('fin', '')),
                ligne.get('De', ligne.get('de', '')),
                ligne.get('À', ligne.get('A', ligne.get('à', ''))),
                ligne.get('Js srv', ligne.get('JS SRV', ''))
            ]

            for col, valeur in enumerate(valeurs):
                item = QTableWidgetItem(str(valeur).strip())
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tableau.setItem(row, col + 1, item)

        # Largeurs des colonnes
        self.tableau.setColumnWidth(0, 35)
        self.tableau.setColumnWidth(1, 60)
        self.tableau.setColumnWidth(2, 50)
        self.tableau.setColumnWidth(3, 60)
        self.tableau.setColumnWidth(4, 60)
        self.tableau.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tableau.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tableau.setColumnWidth(7, 80)

    def on_cell_clicked(self, row, col):
        """Toggle la sélection quand on clique sur une ligne"""
        item = self.tableau.item(row, 0)
        if item:
            if item.text() == '☐':
                item.setText('☑')
            else:
                item.setText('☐')
            self.maj_compteur()

    def selectionner_tous(self):
        """Sélectionne tous les voyages"""
        for row in range(self.tableau.rowCount()):
            item = self.tableau.item(row, 0)
            if item:
                item.setText('☑')
        self.maj_compteur()

    def deselectionner_tous(self):
        """Désélectionne tous les voyages"""
        for row in range(self.tableau.rowCount()):
            item = self.tableau.item(row, 0)
            if item:
                item.setText('☐')
        self.maj_compteur()

    def maj_compteur(self):
        """Met à jour le compteur de sélection"""
        count = 0
        for row in range(self.tableau.rowCount()):
            item = self.tableau.item(row, 0)
            if item and item.text() == '☑':
                count += 1
        self.label_selection.setText(f"{count} voyage(s) sélectionné(s) sur {len(self.donnees)}")

    def importer_selection(self):
        """Importe les voyages sélectionnés"""
        self.donnees_selectionnees = []

        for row in range(self.tableau.rowCount()):
            item_check = self.tableau.item(row, 0)
            if item_check and item_check.text() == '☑':
                if row < len(self.donnees):
                    self.donnees_selectionnees.append(self.donnees[row])

        if not self.donnees_selectionnees:
            QMessageBox.warning(self, "Attention", "Aucun voyage sélectionné !")
            return

        self.accept()

    def get_voyages_importes(self):
        """Retourne les voyages importés au format standardisé"""
        voyages = []

        for ligne in self.donnees_selectionnees:
            voyage = self._parser_ligne(ligne)
            if voyage:
                voyages.append(voyage)

        return voyages

    def _parser_ligne(self, donnee):
        """Parse une ligne CSV en dictionnaire voyage"""
        try:
            # Nettoyer les données
            donnee_clean = {k: str(v).strip() if v else '' for k, v in donnee.items()}

            # Récupérer les valeurs
            numero_ligne = donnee_clean.get('Ligne', donnee_clean.get('ligne', ''))
            numero_voyage = donnee_clean.get('Voy.', donnee_clean.get('Voyage', donnee_clean.get('voy', '')))
            heure_debut_str = donnee_clean.get('Début', donnee_clean.get('Debut', '00:00'))
            heure_fin_str = donnee_clean.get('Fin', donnee_clean.get('fin', '00:00'))
            arret_depart = donnee_clean.get('De', donnee_clean.get('de', ''))
            arret_arrivee = donnee_clean.get('À', donnee_clean.get('A', donnee_clean.get('à', '')))
            js_srv = donnee_clean.get('Js srv', donnee_clean.get('JS SRV', ''))

            # Convertir les heures
            heure_depart = self._heure_vers_decimal(heure_debut_str)
            heure_fin = self._heure_vers_decimal(heure_fin_str)

            # Calculer la durée
            duree_minutes = int((heure_fin - heure_depart) * 60)
            if duree_minutes <= 0:
                duree_minutes = 60

            return {
                'id': None,
                'nom': f"{numero_ligne}-{numero_voyage}",
                'numero_ligne': numero_ligne,
                'numero_voyage': numero_voyage,
                'heure_depart': heure_depart,
                'heure_debut_str': heure_debut_str,
                'heure_fin_str': heure_fin_str,
                'duree_minutes': duree_minutes,
                'arret_depart': arret_depart,
                'arret_arrivee': arret_arrivee,
                'js_srv': js_srv,
                'couleur': '#3498db',
                'assigne': False,
                'service_assigne': None
            }
        except Exception as e:
            print(f"Erreur parsing: {e}")
            return None

    def _heure_vers_decimal(self, heure_str):
        """Convertit HH:MM en décimal"""
        try:
            if ':' in str(heure_str):
                parts = str(heure_str).split(':')
                return int(parts[0]) + int(parts[1]) / 60
            return float(heure_str) if heure_str else 0
        except:
            return 0.0


def importer_voyages_csv(parent=None):
    """
    Fonction utilitaire pour importer des voyages.
    Retourne la liste des voyages ou None si annulé.
    """
    dialog = DialogImportCSV(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_voyages_importes()
    return None