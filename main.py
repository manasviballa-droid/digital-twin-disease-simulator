#!/usr/bin/env python3
"""
AI-Powered Digital Twin of the Human Body
Infectious Disease Simulation Platform
Simulates Malaria, Dengue Fever, and Chikungunya
"""

import sys
import os
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton, QComboBox, QSlider,
    QGroupBox, QGridLayout, QScrollArea, QFrame, QProgressBar,
    QTextEdit, QSpinBox, QCheckBox, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

from disease_engine import DiseaseEngine
from body_model import BodyModelWidget
from organ_panel import OrganRiskPanel
from medication_panel import MedicationPanel
from ai_prediction import AIPredictionEngine
from dashboard import DashboardWidget
from charts import ChartsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Digital Twin — Infectious Disease Simulator")
        self.setMinimumSize(1600, 950)
        self.resize(1800, 1050)

        self.disease_engine = DiseaseEngine()
        self.ai_engine = AIPredictionEngine()
        self.current_day = 0
        self.max_days = 21
        self.is_running = False
        self.current_disease = "Malaria"
        self.medications = []

        self._setup_style()
        self._build_ui()
        self._connect_signals()
        self._setup_timer()
        self.select_disease("Malaria")

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #050d1a;
            }
            QWidget {
                background-color: #050d1a;
                color: #c8daf5;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QSplitter::handle {
                background: #0a1f3d;
                width: 2px;
                height: 2px;
            }
            QTabWidget::pane {
                border: 1px solid #0d2d5e;
                background: #070f20;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #0a1828;
                color: #5a8fd4;
                padding: 8px 18px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #0d2d5e;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QTabBar::tab:selected {
                background: #0d2d5e;
                color: #4fc3f7;
                border-bottom: 2px solid #00b4ff;
            }
            QTabBar::tab:hover {
                background: #0d2040;
                color: #7ecbf5;
            }
            QGroupBox {
                border: 1px solid #0d2d5e;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                background: #070f20;
                font-weight: bold;
                color: #4fc3f7;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #4fc3f7;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d2d5e, stop:1 #071a38);
                color: #4fc3f7;
                border: 1px solid #1a4d8e;
                border-radius: 5px;
                padding: 7px 14px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a4d8e, stop:1 #0d2d5e);
                border-color: #4fc3f7;
                color: #7ed4f7;
            }
            QPushButton:pressed {
                background: #071a38;
            }
            QPushButton:disabled {
                color: #2a4060;
                border-color: #0d2040;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #0d2040;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4fc3f7;
                border: 1px solid #1a4d8e;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #ffffff;
                border-color: #4fc3f7;
            }
            QSlider::sub-page:horizontal {
                background: #1a6ea8;
                border-radius: 3px;
            }
            QComboBox {
                background: #0a1828;
                border: 1px solid #1a4d8e;
                border-radius: 4px;
                padding: 5px 10px;
                color: #4fc3f7;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #0a1828;
                border: 1px solid #1a4d8e;
                color: #4fc3f7;
                selection-background-color: #0d2d5e;
            }
            QLabel {
                color: #c8daf5;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background: #050d1a;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1a4d8e;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QProgressBar {
                background: #0a1828;
                border: 1px solid #0d2d5e;
                border-radius: 3px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a6ea8, stop:1 #4fc3f7);
            }
            QTextEdit {
                background: #070f20;
                border: 1px solid #0d2d5e;
                border-radius: 4px;
                color: #a0c4e8;
                font-size: 11px;
                line-height: 1.4;
            }
            QFrame[frameShape="4"] {
                color: #0d2d5e;
            }
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header bar
        header = self._build_header()
        root_layout.addWidget(header)

        # Main content splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(3)

        # Left panel - disease controls + organs
        left_panel = self._build_left_panel()
        self.main_splitter.addWidget(left_panel)

        # Center - 3D body model + tabs
        center_panel = self._build_center_panel()
        self.main_splitter.addWidget(center_panel)

        # Right panel - dashboard + AI predictions
        right_panel = self._build_right_panel()
        self.main_splitter.addWidget(right_panel)

        self.main_splitter.setSizes([320, 900, 380])
        root_layout.addWidget(self.main_splitter)

        # Bottom status bar
        status = self._build_status_bar()
        root_layout.addWidget(status)

    def _build_header(self):
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #030810, stop:0.3 #071428, stop:0.7 #071428, stop:1 #030810);
                border-bottom: 1px solid #0d2d5e;
            }
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + title
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        dna_label = QLabel("⬡")
        dna_label.setStyleSheet("color: #4fc3f7; font-size: 28px;")
        title_layout.addWidget(dna_label)

        title_text = QVBoxLayout()
        main_title = QLabel("AI DIGITAL TWIN — HUMAN BODY SIMULATOR")
        main_title.setStyleSheet("color: #4fc3f7; font-size: 15px; font-weight: bold; letter-spacing: 2px;")
        sub_title = QLabel("Infectious Disease Research Platform  ·  Malaria · Dengue · Chikungunya")
        sub_title.setStyleSheet("color: #3a6ea0; font-size: 10px; letter-spacing: 1px;")
        title_text.addWidget(main_title)
        title_text.addWidget(sub_title)
        title_layout.addLayout(title_text)
        layout.addWidget(title_widget)

        layout.addStretch()

        # Live indicators
        for label, color in [("● SIMULATION ACTIVE", "#00e676"), ("◈ AI ENGINE ONLINE", "#4fc3f7"), ("◉ VITALS MONITOR", "#ff9100")]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin: 0 10px;")
            layout.addWidget(lbl)

        return header

    def _build_left_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(320)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)


        # Disease selection
        disease_group = QGroupBox("  DISEASE SELECTION")
        dg_layout = QVBoxLayout(disease_group)

        self.disease_buttons = {}
        disease_info = {
            "Malaria": ("#c57552", "Plasmodium parasite\nLiver & Blood System"),
            "Dengue Fever": ("#b85165", "Aedes mosquito virus\nBlood & Platelets"),
            "Chikungunya": ("#bfa054", "Alphavirus infection\nJoints & Muscles"),
        }

        for disease, (color, desc) in disease_info.items():
            btn_frame = QFrame()
            btn_frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid #0d2d5e;
                    border-radius: 6px;
                    background: #070f20;
                }}
                QFrame:hover {{
                    border-color: {color};
                    background: #0a1828;
                }}
            """)
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.setContentsMargins(12, 6, 12, 6)

            text_layout = QVBoxLayout()
            name_lbl = QLabel(disease)
            name_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #5a8fd4; font-size: 9px;")
            text_layout.addWidget(name_lbl)
            text_layout.addWidget(desc_lbl)
            btn_layout.addLayout(text_layout)
            btn_layout.addStretch()

            select_btn = QPushButton("SELECT")
            select_btn.setFixedSize(60, 26)
            select_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {color}33;
                }}
            """)
            select_btn.clicked.connect(lambda checked, d=disease: self.select_disease(d))
            btn_layout.addWidget(select_btn)

            self.disease_buttons[disease] = (btn_frame, select_btn, color)
            dg_layout.addWidget(btn_frame)

        layout.addWidget(disease_group)

        # Simulation control
        sim_group = QGroupBox("  SIMULATION CONTROL")
        sg_layout = QVBoxLayout(sim_group)

        # Day slider
        day_header = QHBoxLayout()
        day_lbl = QLabel("SIMULATION DAY:")
        day_lbl.setStyleSheet("color: #5a8fd4; font-size: 10px; font-weight: bold;")
        self.day_value_lbl = QLabel("0 / 21")
        self.day_value_lbl.setStyleSheet("color: #4fc3f7; font-size: 12px; font-weight: bold;")
        day_header.addWidget(day_lbl)
        day_header.addStretch()
        day_header.addWidget(self.day_value_lbl)
        sg_layout.addLayout(day_header)

        self.day_slider = QSlider(Qt.Orientation.Horizontal)
        self.day_slider.setRange(0, self.max_days)
        self.day_slider.setValue(0)
        sg_layout.addWidget(self.day_slider)

        # Speed control
        speed_layout = QHBoxLayout()
        speed_lbl = QLabel("SPEED:")
        speed_lbl.setStyleSheet("color: #5a8fd4; font-size: 10px;")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "2x", "5x"])
        self.speed_combo.setCurrentIndex(1)
        speed_layout.addWidget(speed_lbl)
        speed_layout.addWidget(self.speed_combo)
        sg_layout.addLayout(speed_layout)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶  START")
        self.pause_btn = QPushButton("⏸  PAUSE")
        self.reset_btn = QPushButton("↺  RESET")
        self.pause_btn.setEnabled(False)
        for btn in [self.start_btn, self.pause_btn, self.reset_btn]:
            btn_layout.addWidget(btn)
        sg_layout.addLayout(btn_layout)

        layout.addWidget(sim_group)

        # Organ risk panel
        self.organ_panel = OrganRiskPanel()
        layout.addWidget(self.organ_panel)

        # Medication panel
        self.med_panel = MedicationPanel()
        layout.addWidget(self.med_panel)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_center_panel(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 3D Body model
        body_container = QGroupBox("  3D HUMAN BODY MODEL — INTERACTIVE DISEASE VISUALIZATION")
        body_layout = QVBoxLayout(body_container)

        self.body_widget = BodyModelWidget()
        self.body_widget.setMinimumHeight(380)
        body_layout.addWidget(self.body_widget)

        # Model controls
        ctrl_layout = QHBoxLayout()
        for label, action in [("⟳ ROTATE", "rotate"), ("⊕ ZOOM IN", "zoom_in"), ("⊖ ZOOM OUT", "zoom_out"), ("⌖ RESET VIEW", "reset")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, a=action: self.body_widget.control_action(a))
            ctrl_layout.addWidget(btn)

        self.view_combo = QComboBox()
        self.view_combo.addItems(["Front View", "Side View", "Back View", "Top View", "3D Orbit"])
        self.view_combo.currentTextChanged.connect(self.body_widget.set_view)
        ctrl_layout.addWidget(self.view_combo)
        body_layout.addLayout(ctrl_layout)
        layout.addWidget(body_container)

        # Charts tabs
        self.charts = ChartsWidget()
        self.charts.setMinimumHeight(280)
        layout.addWidget(self.charts)

        return container

    def _build_right_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(380)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Dashboard
        self.dashboard = DashboardWidget()
        layout.addWidget(self.dashboard)

        # AI Predictions
        ai_group = QGroupBox("  AI HEALTH PREDICTION ENGINE")
        ai_layout = QVBoxLayout(ai_group)

        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setMinimumHeight(350)
        self.ai_text.setStyleSheet("""
            QTextEdit {
                background: #040c1a;
                border: 1px solid #0d2d5e;
                color: #7ecbf5;
                font-size: 12px;
                font-family: 'Consolas', monospace;
                line-height: 1.6;
            }
        """)
        ai_layout.addWidget(self.ai_text)

        self.run_ai_btn = QPushButton("RUN AI ANALYSIS")
        self.run_ai_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #071a38, stop:1 #0d2d5e);
                color: #4fc3f7;
                border: 1px solid #4fc3f7;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d2d5e, stop:1 #1a4d8e);
                color: #7ed4f7;
            }
        """)
        self.run_ai_btn.clicked.connect(self.run_ai_analysis)
        ai_layout.addWidget(self.run_ai_btn)
        layout.addWidget(ai_group)

        # Symptom severity
        sym_group = QGroupBox("  SYMPTOM SEVERITY INDICATORS")
        sym_layout = QGridLayout(sym_group)
        sym_layout.setSpacing(4)

        self.symptom_bars = {}
        symptoms = ["Fever", "Fatigue", "Pain", "Nausea", "Headache",
                    "Inflammation", "Dehydration", "Weakness"]
        colors = ["#5a8fd4"] * 8

        for i, (sym, col) in enumerate(zip(symptoms, colors)):
            row, col_idx = i // 2, i % 2
            lbl = QLabel(sym.upper())
            lbl.setStyleSheet(f"color: {col}; font-size: 9px; font-weight: bold;")
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"""
                QProgressBar {{ background: #0a1828; border: none; border-radius: 3px; }}
                QProgressBar::chunk {{ background: {col}; border-radius: 3px; }}
            """)
            sym_layout.addWidget(lbl, row * 2, col_idx)
            sym_layout.addWidget(bar, row * 2 + 1, col_idx)
            self.symptom_bars[sym] = bar

        layout.addWidget(sym_group)
        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _build_status_bar(self):
        status = QFrame()
        status.setFixedHeight(30)
        status.setStyleSheet("""
            QFrame {
                background: #030810;
                border-top: 1px solid #0d2d5e;
            }
        """)
        layout = QHBoxLayout(status)
        layout.setContentsMargins(15, 0, 15, 0)

        self.status_lbl = QLabel("● SYSTEM READY — Select a disease and press START to begin simulation")
        self.status_lbl.setStyleSheet("color: #3a6ea0; font-size: 10px;")
        layout.addWidget(self.status_lbl)
        layout.addStretch()

        self.fps_lbl = QLabel("SIM ENGINE: IDLE")
        self.fps_lbl.setStyleSheet("color: #1a4d8e; font-size: 10px;")
        layout.addWidget(self.fps_lbl)

        return status

    def _connect_signals(self):
        self.start_btn.clicked.connect(self.start_simulation)
        self.pause_btn.clicked.connect(self.pause_simulation)
        self.reset_btn.clicked.connect(self.reset_simulation)
        self.day_slider.valueChanged.connect(self.seek_to_day)
        self.med_panel.medication_added.connect(self.add_medication)

    def _setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_day)

    def select_disease(self, disease):
        self.current_disease = disease
        self.reset_simulation()

        # Update button highlighting
        disease_colors = {"Malaria": "#c57552", "Dengue Fever": "#b85165", "Chikungunya": "#bfa054"}
        for d, (frame, btn, color) in self.disease_buttons.items():
            if d == disease:
                frame.setStyleSheet(f"""
                    QFrame {{
                        border: 1px solid {color};
                        border-radius: 6px;
                        background: {color}22;
                    }}
                """)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {color};
                        color: #050d1a;
                        border: none;
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: bold;
                    }}
                """)
            else:
                frame.setStyleSheet("""
                    QFrame {
                        border: 1px solid #0d2d5e;
                        border-radius: 6px;
                        background: #070f20;
                    }
                    QFrame:hover {
                        border-color: #1a4d8e;
                    }
                """)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {self.disease_buttons[d][2]};
                        border: 1px solid {self.disease_buttons[d][2]};
                        border-radius: 3px;
                        font-size: 9px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: {self.disease_buttons[d][2]}33;
                    }}
                """)

        self.disease_engine.set_disease(disease)
        self.body_widget.set_disease(disease)
        self.med_panel.set_disease(disease)
        self.charts.set_disease(disease)
        self.dashboard.set_disease(disease)
        self.status_lbl.setText(f"● Disease selected: {disease} — Press START to begin simulation")
        self.update_display(0)

    def start_simulation(self):
        if self.current_day >= self.max_days:
            self.reset_simulation()
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        speeds = {"0.5x": 2000, "1x": 1000, "2x": 500, "5x": 200}
        speed = speeds.get(self.speed_combo.currentText(), 1000)
        self.timer.start(speed)
        self.fps_lbl.setText("SIM ENGINE: RUNNING")
        self.status_lbl.setText(f"● Simulating {self.current_disease} progression...")

    def pause_simulation(self):
        self.is_running = False
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.fps_lbl.setText("SIM ENGINE: PAUSED")

    def reset_simulation(self):
        self.timer.stop()
        self.is_running = False
        self.current_day = 0
        self.medications = []
        self.day_slider.setValue(0)
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.fps_lbl.setText("SIM ENGINE: IDLE")
        self.disease_engine.reset()
        self.med_panel.clear_medications()
        self.charts.reset()
        self.update_display(0)

    def advance_day(self):
        if self.current_day < self.max_days:
            self.current_day += 1
            self.day_slider.blockSignals(True)
            self.day_slider.setValue(self.current_day)
            self.day_slider.blockSignals(False)
            self.update_display(self.current_day)
        else:
            self.pause_simulation()
            self.status_lbl.setText("● Simulation complete — Patient outcome determined")
            self.fps_lbl.setText("SIM ENGINE: COMPLETE")

    def seek_to_day(self, day):
        self.current_day = day
        self.update_display(day)

    def update_display(self, day):
        self.day_value_lbl.setText(f"{day} / {self.max_days}")
        data = self.disease_engine.get_day_data(day, self.medications)

        # Update all panels
        self.body_widget.update_disease_visualization(day, data)
        self.organ_panel.update_organs(data['organ_risks'])
        self.dashboard.update_vitals(day, data)
        self.charts.add_data_point(day, data)
        self._update_symptoms(data)

    def _update_symptoms(self, data):
        symptom_map = {
            "Fever": min(100, (data['temperature'] - 36.5) / 4 * 100),
            "Fatigue": data['fatigue'],
            "Pain": data['pain_level'],
            "Nausea": data.get('nausea', 0),
            "Headache": data.get('headache', 0),
            "Inflammation": data['inflammation'],
            "Dehydration": 100 - data['hydration'],
            "Weakness": data.get('weakness', data['fatigue'] * 0.8),
        }
        for sym, bar in self.symptom_bars.items():
            bar.setValue(int(symptom_map.get(sym, 0)))

    def add_medication(self, medication):
        if medication not in self.medications:
            self.medications.append(medication)
            self.disease_engine.apply_medication(medication)
            self.status_lbl.setText(f"● Medication applied: {medication}")

    def run_ai_analysis(self):
        data = self.disease_engine.get_day_data(self.current_day, self.medications)
        analysis = self.ai_engine.analyze(
            self.current_disease, self.current_day, data, self.medications
        )
        self.ai_text.setHtml(analysis)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(5, 13, 26))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 218, 245))
    palette.setColor(QPalette.ColorRole.Base, QColor(7, 15, 32))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(10, 24, 40))
    palette.setColor(QPalette.ColorRole.Text, QColor(200, 218, 245))
    palette.setColor(QPalette.ColorRole.Button, QColor(10, 24, 40))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(79, 195, 247))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(13, 45, 94))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(79, 195, 247))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
