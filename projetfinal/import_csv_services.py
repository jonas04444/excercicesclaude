"""
Module d'import CSV avec création automatique des services
Fichier: import_csv_services.py
"""

import csv
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QCheckBox, QFrame, QTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QColor, QBrush

from objet import voyage, service_agent


class DialogImportCSVAvecServices(QDialog):
    """
    Dialogue pour importer des voyages depuis un CSV
    et créer automatiquement les services basés sur la colonne "Voiture"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📥 Importer CSV avec Services (colonne Voiture)")
        self.setMinimumSize(1200, 700)

        self.donnees = []
        self.services_detectes = {}  # {nom_service: [liste de voyages]}
        self.services_a_creer = []
        self.voyages_a_creer = []

        layout = QVBoxLayout(self)

        # ===== SECTION 1: Sélection fichier =====
        btn_layout = QHBoxLayout()

        self.btn_parcourir = QPushButton("📂 Parcourir...")
        self.btn_parcourir.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        self.btn_parcourir.clicked.connect(self.parcourir_fichier)
        btn_layout.addWidget(self.btn_parcourir)

        self.label_fichier = QLabel("Aucun fichier sélectionné")
        self.label_fichier.setStyleSheet("color: #666;")
        btn_layout.addWidget(self.label_fichier)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Info colonnes attendues
        info_label = QLabel(
            "📋 Colonnes attendues : Ligne, Via, Direction, De, Début, Fin, À, Voy., Voiture, InfPub, Prot., Régul.\n"
            "💡 La colonne 'Voiture' sera utilisée pour créer les services automatiquement."
        )
        info_label.setStyleSheet(
            "color: #666; font-style: italic; padding: 8px; "
            "background-color: #e8f4fd; border-radius: 5px; border: 1px solid #3498db;"
        )
        layout.addWidget(info_label)

        # ===== SECTION 2: Splitter avec services et voyages =====
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Panneau gauche : Services détectés ---
        panel_services = QFrame()
        panel_services.setFrameStyle(QFrame.Shape.StyledPanel)
        panel_services_layout = QVBoxLayout(panel_services)

        titre_services = QLabel("🚌 Services détectés (colonne Voiture)")
        titre_services.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_services.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; border-radius: 3px;")
        panel_services_layout.addWidget(titre_services)

        # Boutons sélection services
        btn_services_layout = QHBoxLayout()
        btn_select_all_services = QPushButton("✅ Tous")
        btn_select_all_services.clicked.connect(self.selectionner_tous_services)
        btn_services_layout.addWidget(btn_select_all_services)

        btn_deselect_all_services = QPushButton("❌ Aucun")
        btn_deselect_all_services.clicked.connect(self.deselectionner_tous_services)
        btn_services_layout.addWidget(btn_deselect_all_services)
        panel_services_layout.addLayout(btn_services_layout)

        # Liste des services
        self.liste_services = QListWidget()
        self.liste_services.setAlternatingRowColors(True)
        self.liste_services.itemClicked.connect(self.on_service_clicked)
        panel_services_layout.addWidget(self.liste_services)

        self.label_count_services = QLabel("0 service(s) détecté(s)")
        self.label_count_services.setStyleSheet("font-weight: bold; color: #27ae60;")
        panel_services_layout.addWidget(self.label_count_services)

        splitter.addWidget(panel_services)

        # --- Panneau droit : Voyages du service sélectionné ---
        panel_voyages = QFrame()
        panel_voyages.setFrameStyle(QFrame.Shape.StyledPanel)
        panel_voyages_layout = QVBoxLayout(panel_voyages)

        titre_voyages = QLabel("🚍 Voyages du service sélectionné")
        titre_voyages.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titre_voyages.setStyleSheet("background-color: #3498db; color: white; padding: 8px; border-radius: 3px;")
        panel_voyages_layout.addWidget(titre_voyages)

        # Tableau des voyages
        self.tableau_voyages = QTableWidget()
        self.tableau_voyages.setColumnCount(8)
        self.tableau_voyages.setHorizontalHeaderLabels(
            ['Ligne', 'Via', 'Direction', 'Début', 'Fin', 'De', 'À', 'Voy.']
        )
        self.tableau_voyages.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableau_voyages.setAlternatingRowColors(True)
        self.tableau_voyages.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        panel_voyages_layout.addWidget(self.tableau_voyages)

        self.label_count_voyages = QLabel("0 voyage(s)")
        self.label_count_voyages.setStyleSheet("font-weight: bold; color: #3498db;")
        panel_voyages_layout.addWidget(self.label_count_voyages)

        splitter.addWidget(panel_voyages)

        # Proportions du splitter
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)

        # ===== SECTION 3: Résumé et actions =====
        resume_layout = QHBoxLayout()

        self.label_resume = QLabel("📊 Résumé : 0 service(s), 0 voyage(s) à importer")
        self.label_resume.setStyleSheet(
            "font-weight: bold; padding: 10px; "
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        resume_layout.addWidget(self.label_resume)

        resume_layout.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.reject)
        resume_layout.addWidget(btn_annuler)

        self.btn_importer = QPushButton("🚀 Importer et créer les services")
        self.btn_importer.setStyleSheet(
            "background-color: #27ae60; color: white; "
            "padding: 12px 24px; font-weight: bold; font-size: 12px;"
        )
        self.btn_importer.clicked.connect(self.importer_tout)
        self.btn_importer.setEnabled(False)
        resume_layout.addWidget(self.btn_importer)

        layout.addLayout(resume_layout)

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
        """Charge et analyse le CSV"""
        try:
            with open(chemin_fichier, 'r', encoding='utf-8-sig') as file:
                premiere_ligne = file.readline()
                file.seek(0)

                delimiter = ';' if ';' in premiere_ligne else ','
                reader = csv.DictReader(file, delimiter=delimiter)
                self.donnees = list(reader)

            if not self.donnees:
                QMessageBox.warning(self, "Attention", "Le fichier CSV est vide")
                return

            # Vérifier la colonne Voiture
            if 'Voiture' not in self.donnees[0] and 'voiture' not in self.donnees[0]:
                QMessageBox.warning(
                    self, "Attention",
                    "La colonne 'Voiture' n'a pas été trouvée dans le CSV.\n"
                    "Vérifiez que votre fichier contient bien cette colonne."
                )
                return

            nom_fichier = chemin_fichier.split('/')[-1].split('\\')[-1]
            self.label_fichier.setText(f"✅ {nom_fichier} ({len(self.donnees)} lignes)")
            self.label_fichier.setStyleSheet("color: #27ae60; font-weight: bold;")

            self.analyser_services()
            self.btn_importer.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement :\n{str(e)}")

    def analyser_services(self):
        """Analyse les données et regroupe par service (colonne Voiture)"""
        self.services_detectes = {}

        for ligne in self.donnees:
            # Récupérer le nom du service depuis la colonne Voiture
            nom_service = ligne.get('Voiture', ligne.get('voiture', '')).strip()

            if not nom_service:
                nom_service = "Sans service"

            if nom_service not in self.services_detectes:
                self.services_detectes[nom_service] = []

            self.services_detectes[nom_service].append(ligne)

        # Trier les services par nom
        self.services_detectes = dict(sorted(self.services_detectes.items()))

        self.afficher_liste_services()
        self.maj_resume()

    def afficher_liste_services(self):
        """Affiche la liste des services détectés"""
        self.liste_services.clear()

        for nom_service, voyages in self.services_detectes.items():
            item = QListWidgetItem()
            item.setText(f"☑ {nom_service} ({len(voyages)} voyage(s))")
            item.setData(Qt.ItemDataRole.UserRole, nom_service)
            item.setData(Qt.ItemDataRole.UserRole + 1, True)  # Sélectionné par défaut

            # Couleur selon le nombre de voyages
            if len(voyages) >= 10:
                item.setForeground(QBrush(QColor('#27ae60')))  # Vert
            elif len(voyages) >= 5:
                item.setForeground(QBrush(QColor('#f39c12')))  # Orange
            else:
                item.setForeground(QBrush(QColor('#3498db')))  # Bleu

            item.setFont(QFont("Arial", 10))
            self.liste_services.addItem(item)

        self.label_count_services.setText(f"{len(self.services_detectes)} service(s) détecté(s)")

    def on_service_clicked(self, item):
        """Quand on clique sur un service"""
        nom_service = item.data(Qt.ItemDataRole.UserRole)
        est_selectionne = item.data(Qt.ItemDataRole.UserRole + 1)

        # Toggle la sélection
        est_selectionne = not est_selectionne
        item.setData(Qt.ItemDataRole.UserRole + 1, est_selectionne)

        if est_selectionne:
            item.setText(f"☑ {nom_service} ({len(self.services_detectes[nom_service])} voyage(s))")
        else:
            item.setText(f"☐ {nom_service} ({len(self.services_detectes[nom_service])} voyage(s))")

        # Afficher les voyages du service
        self.afficher_voyages_service(nom_service)
        self.maj_resume()

    def afficher_voyages_service(self, nom_service):
        """Affiche les voyages d'un service dans le tableau"""
        voyages = self.services_detectes.get(nom_service, [])

        self.tableau_voyages.setRowCount(len(voyages))

        for row, ligne in enumerate(voyages):
            valeurs = [
                ligne.get('Ligne', ligne.get('ligne', '')),
                ligne.get('Via', ligne.get('via', '')),
                ligne.get('Direction', ligne.get('direction', '')),
                ligne.get('Début', ligne.get('Debut', '')),
                ligne.get('Fin', ligne.get('fin', '')),
                ligne.get('De', ligne.get('de', '')),
                ligne.get('À', ligne.get('A', ligne.get('à', ''))),
                ligne.get('Voy.', ligne.get('Voyage', ''))
            ]

            for col, val in enumerate(valeurs):
                item = QTableWidgetItem(str(val).strip())
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tableau_voyages.setItem(row, col, item)

        self.label_count_voyages.setText(f"{len(voyages)} voyage(s) dans ce service")

    def selectionner_tous_services(self):
        """Sélectionne tous les services"""
        for i in range(self.liste_services.count()):
            item = self.liste_services.item(i)
            nom_service = item.data(Qt.ItemDataRole.UserRole)
            item.setData(Qt.ItemDataRole.UserRole + 1, True)
            item.setText(f"☑ {nom_service} ({len(self.services_detectes[nom_service])} voyage(s))")
        self.maj_resume()

    def deselectionner_tous_services(self):
        """Désélectionne tous les services"""
        for i in range(self.liste_services.count()):
            item = self.liste_services.item(i)
            nom_service = item.data(Qt.ItemDataRole.UserRole)
            item.setData(Qt.ItemDataRole.UserRole + 1, False)
            item.setText(f"☐ {nom_service} ({len(self.services_detectes[nom_service])} voyage(s))")
        self.maj_resume()

    def maj_resume(self):
        """Met à jour le résumé"""
        nb_services = 0
        nb_voyages = 0

        for i in range(self.liste_services.count()):
            item = self.liste_services.item(i)
            if item.data(Qt.ItemDataRole.UserRole + 1):
                nom_service = item.data(Qt.ItemDataRole.UserRole)
                nb_services += 1
                nb_voyages += len(self.services_detectes[nom_service])

        self.label_resume.setText(
            f"📊 Résumé : {nb_services} service(s), {nb_voyages} voyage(s) à importer"
        )

    def importer_tout(self):
        """Prépare les services et voyages à créer"""
        self.services_a_creer = []
        self.voyages_a_creer = []

        couleurs = ['#e3f2fd', '#e8f5e9', '#fff3e0', '#fce4ec', '#f3e5f5', '#e0f7fa', '#fbe9e7']
        couleur_idx = 0

        for i in range(self.liste_services.count()):
            item = self.liste_services.item(i)

            if not item.data(Qt.ItemDataRole.UserRole + 1):
                continue  # Service non sélectionné

            nom_service = item.data(Qt.ItemDataRole.UserRole)
            voyages_csv = self.services_detectes[nom_service]

            if not voyages_csv:
                continue

            # Trouver les heures min/max pour le service
            heure_min = 24 * 60
            heure_max = 0

            voyages_du_service = []

            for ligne in voyages_csv:
                voy_data = self._parser_ligne(ligne)
                if voy_data:
                    voyages_du_service.append(voy_data)

                    # Mettre à jour les heures du service
                    hdebut = voy_data['hdebut']
                    hfin = voy_data['hfin']

                    if hdebut < heure_min:
                        heure_min = hdebut
                    if hfin > heure_max:
                        heure_max = hfin

            if not voyages_du_service:
                continue

            # Créer les données du service
            service_data = {
                'nom': nom_service,
                'num_service': nom_service,
                'type_service': 'journée',
                'heure_debut': heure_min,
                'heure_fin': heure_max,
                'couleur': couleurs[couleur_idx % len(couleurs)],
                'voyages': voyages_du_service
            }

            self.services_a_creer.append(service_data)
            couleur_idx += 1

        if not self.services_a_creer:
            QMessageBox.warning(self, "Attention", "Aucun service sélectionné !")
            return

        # Confirmation
        msg = f"Vous allez créer :\n\n"
        msg += f"• {len(self.services_a_creer)} service(s)\n"
        total_voyages = sum(len(s['voyages']) for s in self.services_a_creer)
        msg += f"• {total_voyages} voyage(s)\n\n"
        msg += "Continuer ?"

        reply = QMessageBox.question(
            self, "Confirmation",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def _parser_ligne(self, donnee):
        """Parse une ligne CSV en données voyage"""
        try:
            donnee_clean = {k: str(v).strip() if v else '' for k, v in donnee.items()}

            numero_ligne = donnee_clean.get('Ligne', donnee_clean.get('ligne', ''))
            numero_voyage = donnee_clean.get('Voy.', donnee_clean.get('Voyage', donnee_clean.get('voy', '')))
            heure_debut_str = donnee_clean.get('Début', donnee_clean.get('Debut', '00:00'))
            heure_fin_str = donnee_clean.get('Fin', donnee_clean.get('fin', '00:00'))
            arret_depart = donnee_clean.get('De', donnee_clean.get('de', ''))
            arret_arrivee = donnee_clean.get('À', donnee_clean.get('A', donnee_clean.get('à', '')))
            js_srv = donnee_clean.get('Js srv', donnee_clean.get('JS SRV', ''))

            # Convertir les heures en minutes
            hdebut = self._heure_vers_minutes(heure_debut_str)
            hfin = self._heure_vers_minutes(heure_fin_str)

            if hfin <= hdebut:
                hfin = hdebut + 60  # Durée par défaut 1h

            return {
                'num_ligne': numero_ligne,
                'num_voyage': numero_voyage,
                'arret_debut': arret_depart,
                'arret_fin': arret_arrivee,
                'heure_debut_str': heure_debut_str,
                'heure_fin_str': heure_fin_str,
                'hdebut': hdebut,
                'hfin': hfin,
                'js_srv': js_srv
            }

        except Exception as e:
            print(f"Erreur parsing: {e}")
            return None

    def _heure_vers_minutes(self, heure_str):
        """Convertit HH:MM en minutes depuis minuit"""
        try:
            if ':' in str(heure_str):
                parts = str(heure_str).split(':')
                return int(parts[0]) * 60 + int(parts[1])
            return int(float(heure_str) * 60) if heure_str else 0
        except:
            return 0

    def get_services_a_creer(self):
        """Retourne la liste des services à créer avec leurs voyages"""
        return self.services_a_creer


def importer_csv_avec_services(parent=None):
    """
    Fonction utilitaire pour importer un CSV avec création de services.
    Retourne la liste des services ou None si annulé.
    """
    dialog = DialogImportCSVAvecServices(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_services_a_creer()
    return None