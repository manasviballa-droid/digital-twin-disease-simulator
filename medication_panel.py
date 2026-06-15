"""
Medication Panel — Drug administration and effect simulation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QFrame, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


DISEASE_MEDICATIONS = {
    "Malaria": [
        ("Chloroquine", "#5a8fd4", "Classic antimalarial\nBlood schizonticide"),
        ("Primaquine", "#5a8fd4", "Radical cure\nEradicates liver stage"),
        ("Paracetamol", "#5a8fd4", "Fever & pain relief\nSymptomatic treatment"),
    ],
    "Dengue Fever": [
        ("Paracetamol", "#5a8fd4", "Fever & pain control\nDO NOT use NSAIDs"),
        ("Oral Rehydration (ORT)", "#5a8fd4", "Fluid replacement\nMaintains electrolytes"),
        ("IV Fluids", "#5a8fd4", "Hospital-grade hydration\nPrevents plasma leakage"),
        ("Platelet Transfusion", "#5a8fd4", "Critical platelet support\n<20,000 threshold"),
    ],
    "Chikungunya": [
        ("Paracetamol", "#5a8fd4", "Fever & mild pain\nFirst choice analgesic"),
        ("Anti-inflammatory (NSAIDs)", "#5a8fd4", "Joint & muscle pain\nIbuprofen/Naproxen"),
        ("Corticosteroids", "#5a8fd4", "Severe arthritis\nShort-term use"),
    ],
}


class MedicationPanel(QGroupBox):
    medication_added = pyqtSignal(str)
    medications_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("  MEDICATION SIMULATION", parent)
        self.current_disease = "Malaria"
        self.active_medications = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        # Active meds display
        active_lbl = QLabel("ACTIVE TREATMENTS:")
        active_lbl.setStyleSheet("color: #3a6ea0; font-size: 9px; font-weight: bold;")
        layout.addWidget(active_lbl)

        self.active_text = QLabel("None")
        self.active_text.setWordWrap(True)
        self.active_text.setStyleSheet("""
            color: #00e676; font-size: 9px; font-weight: bold;
            background: #003316; border-radius: 4px; padding: 4px 6px;
        """)
        layout.addWidget(self.active_text)

        # Med buttons container
        self.med_container = QFrame()
        self.med_layout = QVBoxLayout(self.med_container)
        self.med_layout.setContentsMargins(0, 0, 0, 0)
        self.med_layout.setSpacing(4)
        layout.addWidget(self.med_container)

        # Clear button
        clear_btn = QPushButton("✕  CLEAR ALL MEDICATIONS")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #1a0a0a;
                color: #ff4444;
                border: 1px solid #441111;
                border-radius: 4px;
                padding: 5px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #330000;
                border-color: #ff4444;
            }
        """)
        clear_btn.clicked.connect(self.clear_medications)
        layout.addWidget(clear_btn)

        self._build_med_buttons()

    def set_disease(self, disease):
        self.current_disease = disease
        self.clear_medications()
        self._build_med_buttons()

    def _build_med_buttons(self):
        # Clear existing
        for i in reversed(range(self.med_layout.count())):
            widget = self.med_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        meds = DISEASE_MEDICATIONS.get(self.current_disease, [])
        for med_name, color, desc in meds:
            btn_frame = QFrame()
            btn_frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid #0d2d5e;
                    border-radius: 5px;
                    background: #070f20;
                }}
            """)
            bl = QHBoxLayout(btn_frame)
            bl.setContentsMargins(6, 4, 6, 4)
            bl.setSpacing(8)

            text_col = QVBoxLayout()
            name = QLabel(med_name)
            name.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #3a6ea0; font-size: 8px;")
            text_col.addWidget(name)
            text_col.addWidget(desc_lbl)
            bl.addLayout(text_col)
            bl.addStretch()

            adm_btn = QPushButton("ADMINISTER")
            adm_btn.setFixedSize(75, 24)
            adm_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 3px;
                    font-size: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {color}33;
                }}
                QPushButton:pressed {{
                    background: {color}66;
                }}
            """)
            adm_btn.clicked.connect(lambda checked, m=med_name, b=adm_btn, c=color: self._administer(m, b, c))
            bl.addWidget(adm_btn)

            self.med_layout.addWidget(btn_frame)

    def _administer(self, medication, btn, color):
        if medication not in self.active_medications:
            self.active_medications.append(medication)
            btn.setText("✓ ACTIVE")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color}44;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 3px;
                    font-size: 8px;
                    font-weight: bold;
                }}
            """)
            btn.setEnabled(False)
            self._update_active_display()
            self.medication_added.emit(medication)

    def _update_active_display(self):
        if self.active_medications:
            self.active_text.setText("\n".join(f"✓ {m}" for m in self.active_medications))
        else:
            self.active_text.setText("None")

    def clear_medications(self):
        self.active_medications = []
        self.active_text.setText("None")
        self._build_med_buttons()
        self.medications_cleared.emit()
