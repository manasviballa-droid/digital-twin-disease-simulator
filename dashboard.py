"""
Dashboard Widget — Real-time vitals and patient status display
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor


class VitalCard(QFrame):
    def __init__(self, label, unit, color="#4fc3f7", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.unit = unit
        self.color = color
        self.setFixedHeight(68)
        self.setStyleSheet(f"""
            QFrame {{
                background: #070f20;
                border: 1px solid #0d2d5e;
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self.name_lbl = QLabel(label.upper())
        self.name_lbl.setStyleSheet(f"color: #3a6ea0; font-size: 8px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(self.name_lbl)

        value_row = QHBoxLayout()
        self.value_lbl = QLabel("--")
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold; font-family: 'Consolas';")
        value_row.addWidget(self.value_lbl)

        self.unit_lbl = QLabel(unit)
        self.unit_lbl.setStyleSheet("color: #2a4060; font-size: 9px; margin-top: 5px;")
        self.unit_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        value_row.addWidget(self.unit_lbl)
        value_row.addStretch()
        layout.addLayout(value_row)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 8px; font-weight: bold;")
        layout.addWidget(self.status_lbl)

    def update_value(self, value, status="", status_color="#00e676"):
        if isinstance(value, float):
            self.value_lbl.setText(f"{value:.1f}")
        elif isinstance(value, int):
            self.value_lbl.setText(f"{value:,}")
        else:
            self.value_lbl.setText(str(value))

        if status:
            self.status_lbl.setText(status)
            self.status_lbl.setStyleSheet(f"color: {status_color}; font-size: 8px; font-weight: bold;")

        # Color the value based on status
        val_color = {"NORMAL": self.color, "WARNING": "#b88a30", "DANGER": "#c45d30", "CRITICAL": "#b83b3b"}.get(
            status.upper() if status else "NORMAL", self.color)
        self.value_lbl.setStyleSheet(f"color: {val_color}; font-size: 18px; font-weight: bold; font-family: 'Consolas';")

        border_color = {"WARNING": "#ffab00", "DANGER": "#ff6b35", "CRITICAL": "#ff1744"}.get(
            status.upper() if status else "", "#0d2d5e")
        self.setStyleSheet(f"""
            QFrame {{
                background: #070f20;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
        """)


class DashboardWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("  PATIENT DASHBOARD — REAL-TIME VITALS", parent)
        self.current_disease = "Malaria"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)

        # Status banner
        self.status_banner = QLabel("SELECT DISEASE TO BEGIN")
        self.status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_banner.setFixedHeight(32)
        self.status_banner.setStyleSheet("""
            background: #0a1828;
            border: 1px solid #0d2d5e;
            border-radius: 4px;
            color: #4fc3f7;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.status_banner)

        # Summary row
        summary = QHBoxLayout()
        self.disease_lbl = self._info_lbl("DISEASE", "--", "#4fc3f7")
        self.day_lbl = self._info_lbl("DAY", "0/21", "#4fc3f7")
        self.severity_lbl = self._info_lbl("SEVERITY", "0%", "#00e676")
        self.recovery_lbl = self._info_lbl("RECOVERY", "100%", "#00e676")
        for lbl in [self.disease_lbl, self.day_lbl, self.severity_lbl, self.recovery_lbl]:
            summary.addWidget(lbl)
        layout.addLayout(summary)

        # Vitals grid
        grid = QGridLayout()
        grid.setSpacing(5)

        self.temp_card = VitalCard("Temperature", "°F", "#ff6b35")
        self.hr_card = VitalCard("Heart Rate", "bpm", "#ff4444")
        self.bp_card = VitalCard("Blood Pressure", "mmHg", "#ce93d8")
        self.spo2_card = VitalCard("SpO₂", "%", "#4fc3f7")
        self.platelet_card = VitalCard("Platelets", "×10³/μL", "#ff80ab")
        self.hgb_card = VitalCard("Hemoglobin", "g/dL", "#80cbc4")
        self.wbc_card = VitalCard("WBC Count", "/μL", "#a5d6a7")
        self.fatigue_card = VitalCard("Fatigue", "%", "#ffcc02")

        cards = [
            (self.temp_card, 0, 0), (self.hr_card, 0, 1),
            (self.bp_card, 1, 0), (self.spo2_card, 1, 1),
            (self.platelet_card, 2, 0), (self.hgb_card, 2, 1),
            (self.wbc_card, 3, 0), (self.fatigue_card, 3, 1),
        ]
        for card, row, col in cards:
            grid.addWidget(card, row, col)

        layout.addLayout(grid)

        # Additional stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: #040c1a; border: 1px solid #0d2d5e; border-radius: 4px;")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setContentsMargins(8, 6, 8, 6)
        stats_layout.setSpacing(4)

        self.extra_labels = {}
        extra_stats = [
            ("Hydration", "hydration", "%"),
            ("Pain Level", "pain_level", "%"),
            ("Inflammation", "inflammation", "%"),
            ("Hosp. Risk", "hospitalization_risk", "%"),
        ]
        for i, (label, key, unit) in enumerate(extra_stats):
            row, col = i // 2, i % 2
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #2a4060; font-size: 9px;")
            val_lbl = QLabel("--")
            val_lbl.setStyleSheet("color: #4fc3f7; font-size: 10px; font-weight: bold;")
            stats_layout.addWidget(lbl, row, col * 2)
            stats_layout.addWidget(val_lbl, row, col * 2 + 1)
            self.extra_labels[key] = (val_lbl, unit)

        layout.addWidget(stats_frame)

    def _info_lbl(self, label, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"background: #070f20; border: 1px solid #0d2d5e; border-radius: 4px;")
        v = QVBoxLayout(frame)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(1)
        l = QLabel(label)
        l.setStyleSheet("color: #2a4060; font-size: 8px; font-weight: bold;")
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(l)
        v.addWidget(v_lbl)
        frame._val_lbl = v_lbl
        return frame

    def set_disease(self, disease):
        self.current_disease = disease
        self.disease_lbl._val_lbl.setText(disease[:10])

    def update_vitals(self, day, data, max_days=21):
        prog = data.get('progression', 0)
        severity = data.get('severity', 0)
        recovery = data.get('recovery_probability', 0)

        # Status banner
        if prog < 0.1:
            status, bg, col = "● HEALTHY — NO ACTIVE INFECTION", "#041a12", "#4faf8c"
        elif prog < 0.3:
            status, bg, col = "⚠ EARLY INFECTION — MONITORING", "#1a160a", "#b88a30"
        elif prog < 0.6:
            status, bg, col = "▲ MODERATE DISEASE — TREATMENT ADVISED", "#1a0f0a", "#c45d30"
        elif prog < 0.85:
            status, bg, col = "◆ SEVERE — MEDICAL ATTENTION REQUIRED", "#1a0a0a", "#b83b3b"
        else:
            status, bg, col = "⬛ CRITICAL — EMERGENCY INTERVENTION", "#220505", "#a32c2c"

        self.status_banner.setText(status)
        self.status_banner.setStyleSheet(f"""
            background: {bg}; border: 1px solid {col};
            border-radius: 4px; color: {col};
            font-size: 10px; font-weight: bold; letter-spacing: 1px;
        """)

        # Update summary
        self.day_lbl._val_lbl.setText(f"{day}/{max_days}")
        sev_col = "#4faf8c" if severity < 30 else ("#b88a30" if severity < 60 else "#b83b3b")
        self.severity_lbl._val_lbl.setText(f"{severity:.0f}%")
        self.severity_lbl._val_lbl.setStyleSheet(f"color: {sev_col}; font-size: 10px; font-weight: bold;")
        rec_col = "#4faf8c" if recovery > 60 else ("#b88a30" if recovery > 30 else "#b83b3b")
        self.recovery_lbl._val_lbl.setText(f"{recovery:.0f}%")
        self.recovery_lbl._val_lbl.setStyleSheet(f"color: {rec_col}; font-size: 10px; font-weight: bold;")

        # Temperature
        temp_c = data.get('temperature', 36.6)
        temp_f = temp_c * 1.8 + 32.0
        temp_status = "NORMAL" if temp_f < 99.5 else ("WARNING" if temp_f < 101.3 else ("DANGER" if temp_f < 104.0 else "CRITICAL"))
        self.temp_card.update_value(temp_f, temp_status,
            {"NORMAL": "#4faf8c", "WARNING": "#b88a30", "DANGER": "#c45d30", "CRITICAL": "#b83b3b"}[temp_status])

        # Heart rate
        hr = data.get('heart_rate', 72)
        hr_status = "NORMAL" if 60 <= hr <= 100 else ("WARNING" if hr <= 110 else "DANGER")
        self.hr_card.update_value(hr, hr_status, "#b88a30" if hr_status != "NORMAL" else "#4faf8c")

        # Blood pressure
        sys = data.get('systolic_bp', 120)
        dia = data.get('diastolic_bp', 80)
        bp_status = "WARNING" if sys < 100 else "NORMAL"
        self.bp_card.update_value(f"{sys}/{dia}", bp_status, "#b88a30" if bp_status != "NORMAL" else "#4faf8c")

        # SpO2
        spo2 = data.get('oxygen_saturation', 98)
        spo2_status = "NORMAL" if spo2 >= 95 else ("WARNING" if spo2 >= 92 else "CRITICAL")
        self.spo2_card.update_value(spo2, spo2_status,
            {"NORMAL": "#4faf8c", "WARNING": "#b88a30", "CRITICAL": "#b83b3b"}[spo2_status])

        # Platelets
        plt = data.get('platelet_count', 250)
        plt_status = "NORMAL" if plt >= 150 else ("WARNING" if plt >= 100 else ("DANGER" if plt >= 50 else "CRITICAL"))
        self.platelet_card.update_value(plt, plt_status,
            {"NORMAL": "#4faf8c", "WARNING": "#b88a30", "DANGER": "#c45d30", "CRITICAL": "#b83b3b"}[plt_status])

        # Hemoglobin
        hgb = data.get('hemoglobin', 15.0)
        hgb_status = "NORMAL" if hgb >= 12 else ("WARNING" if hgb >= 10 else ("DANGER" if hgb >= 8 else "CRITICAL"))
        self.hgb_card.update_value(hgb, hgb_status,
            {"NORMAL": "#4faf8c", "WARNING": "#b88a30", "DANGER": "#c45d30", "CRITICAL": "#b83b3b"}[hgb_status])

        # WBC
        wbc = data.get('wbc_count', 7000)
        wbc_status = "NORMAL" if 4000 <= wbc <= 11000 else "WARNING"
        self.wbc_card.update_value(wbc, wbc_status, "#b88a30" if wbc_status != "NORMAL" else "#4faf8c")

        # Fatigue
        fat = data.get('fatigue', 0)
        fat_status = "NORMAL" if fat < 30 else ("WARNING" if fat < 60 else "DANGER")
        self.fatigue_card.update_value(fat, fat_status, "#b88a30" if fat_status != "NORMAL" else "#4faf8c")

        # Extra stats
        for key, (val_lbl, unit) in self.extra_labels.items():
            val = data.get(key, 0)
            if isinstance(val, (int, float)):
                val_lbl.setText(f"{val:.0f}{unit}")
            else:
                val_lbl.setText(str(val))
