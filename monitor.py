"""
ICU Bedside Patient Monitor Widget
Animates real-time patient physiological signals (ECG II, ECG V5, PPG/Pleth, Respiration waves)
and displays hospital-style large glowing vital sign readouts.
Simulates second-by-second physiological changes over a 24-hour period based on active disease/day.
Designed to prevent text overlapping and allow interactive timer play/pause/reset.
"""

import sys
import collections
import datetime
import numpy as np
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QFrame, QGridLayout, QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class BedsideMonitorWidget(QWidget):
    vitals_updated = pyqtSignal(dict)
    timer_state_changed = pyqtSignal(bool)
    day_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sim_tick_seconds = 72
        # Baselines
        self.current_day_data = {}
        self.next_day_data = {}
        self.date_str = "15.06.2026"

        self.baseline_hr = 72
        self.baseline_sys_bp = 120
        self.baseline_dia_bp = 80
        self.baseline_spo2 = 98
        self.baseline_resp_rate = 16
        self.baseline_temp_f = 98.6
        self.baseline_platelets = 250
        self.baseline_severity = 0.0
        self.baseline_highest_organ_name = "None"
        self.baseline_highest_organ_score = 0.0
        self.baseline_second_organ_name = ""
        self.baseline_second_organ_score = 0.0

        # Current values
        self.heart_rate = 72
        self.systolic_bp = 120
        self.diastolic_bp = 80
        self.spo2 = 98
        self.resp_rate = 16
        self.temp_f = 98.6
        self.platelets = 250
        self.severity = 0.0
        self.highest_organ_score = 0.0

        # Clock Time (simulated)
        self.sim_hour = 0
        self.sim_minute = 0
        self.sim_second = 0
        self.frame_count = 0

        self.t = 0.0
        self.is_frozen = False

        # Rolling buffers
        self.ecg_data = collections.deque([0.0] * 200, maxlen=200)
        self.ecg2_data = collections.deque([0.0] * 200, maxlen=200)
        self.ppg_data = collections.deque([0.5] * 200, maxlen=200)
        self.resp_data = collections.deque([0.5] * 200, maxlen=200)
        self.x_data = list(np.linspace(0, 10, 200))

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0c0e12;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bezel frame
        self.bezel = QFrame()
        self.bezel.setObjectName("Bezel")
        self.bezel.setStyleSheet("""
            #Bezel {
                background-color: #1a1c20;
                border: 4px solid #282b30;
                border-radius: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self.bezel)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 3)
        self.bezel.setGraphicsEffect(shadow)
        main_layout.addWidget(self.bezel)

        bezel_layout = QVBoxLayout(self.bezel)
        bezel_layout.setContentsMargins(10, 4, 10, 4)
        bezel_layout.setSpacing(4)

        # Bezel Top Bar
        top_bar = QHBoxLayout()
        logo_label = QLabel("Hwatime")
        logo_label.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold; font-family: 'Arial', sans-serif; letter-spacing: 1.5px;")
        top_bar.addWidget(logo_label)
        
        top_bar.addStretch()
        
        self.disease_day_label = QLabel("NORMAL STATUS")
        self.disease_day_label.setStyleSheet("color: #4fc3f7; font-size: 9px; font-weight: bold; font-family: 'Arial', sans-serif; letter-spacing: 1px;")
        top_bar.addWidget(self.disease_day_label)
        
        top_bar.addStretch()
        
        model_label = QLabel("ICU BED SIDE MONITOR")
        model_label.setStyleSheet("color: #555860; font-size: 8px; font-weight: bold; font-family: 'Arial', sans-serif;")
        top_bar.addWidget(model_label)
        bezel_layout.addLayout(top_bar)

        # Inner Screen
        self.screen_frame = QFrame()
        self.screen_frame.setObjectName("ScreenFrame")
        self.screen_frame.setStyleSheet("""
            #ScreenFrame {
                background-color: #000000;
                border: 1px solid #111111;
                border-radius: 4px;
            }
        """)
        screen_layout = QHBoxLayout(self.screen_frame)
        screen_layout.setContentsMargins(2, 2, 2, 2)
        screen_layout.setSpacing(4)

        # Matplotlib canvas for 4 waveforms
        self.fig = Figure(figsize=(7, 2.8), facecolor="#000000")
        self.fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02, hspace=0.04)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #000000;")
        screen_layout.addWidget(self.canvas, stretch=58)

        self.ax_ecg = self.fig.add_subplot(4, 1, 1, facecolor="#000000")
        self.ax_ecg2 = self.fig.add_subplot(4, 1, 2, facecolor="#000000")
        self.ax_ppg = self.fig.add_subplot(4, 1, 3, facecolor="#000000")
        self.ax_resp = self.fig.add_subplot(4, 1, 4, facecolor="#000000")

        for ax in [self.ax_ecg, self.ax_ecg2, self.ax_ppg, self.ax_resp]:
            ax.set_xlim(0, 10)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines[:].set_visible(False)

        self.ax_ecg.set_ylim(-0.5, 1.5)
        self.ax_ecg2.set_ylim(-0.5, 1.5)
        self.ax_ppg.set_ylim(-0.1, 1.1)
        self.ax_resp.set_ylim(-0.1, 1.1)

        self.ecg_line, = self.ax_ecg.plot(self.x_data, list(self.ecg_data), color="#00e676", linewidth=1.5)
        self.ecg2_line, = self.ax_ecg2.plot(self.x_data, list(self.ecg2_data), color="#00e676", linewidth=1.5)
        self.ppg_line, = self.ax_ppg.plot(self.x_data, list(self.ppg_data), color="#00e5ff", linewidth=1.5)
        self.resp_line, = self.ax_resp.plot(self.x_data, list(self.resp_data), color="#ffea00", linewidth=1.5)

        self.ax_ecg.text(0.1, 1.1, "ECG II", color="#00e676", fontsize=7, fontfamily='monospace', fontweight='bold')
        self.ax_ecg2.text(0.1, 1.1, "ECG V5", color="#00e676", fontsize=7, fontfamily='monospace', fontweight='bold')
        self.ax_ppg.text(0.1, 0.9, "SPO2 PLETH", color="#00e5ff", fontsize=7, fontfamily='monospace', fontweight='bold')
        self.ax_resp.text(0.1, 0.9, "RESP CO2", color="#ffea00", fontsize=7, fontfamily='monospace', fontweight='bold')

        # DEMO watermark
        self.demo_text = self.ax_ecg.text(5.0, 0.6, "DEMO", color="#ffffff", fontsize=14, fontweight='bold',
                                          fontfamily='Arial',
                                          bbox=dict(facecolor='#3a7bc8', alpha=0.6, edgecolor='none', boxstyle='square,pad=0.3'),
                                          ha='center', va='center')

        # Live figure clock overlay
        self.fig_time_text = self.fig.text(0.99, 0.98, "15.06.2026\n00:00:00", 
                                           color="#00e5ff", fontsize=7, fontfamily='monospace',
                                           ha='right', va='top', fontweight='bold')

        # Vitals container panel (main vertical layout)
        self.vitals_panel = QFrame()
        self.vitals_panel.setStyleSheet("background-color: #000000; border: none;")
        self.vitals_layout = QVBoxLayout(self.vitals_panel)
        self.vitals_layout.setContentsMargins(1, 1, 1, 1)
        self.vitals_layout.setSpacing(4)

        # 1. Cards Grid Layout
        self.vitals_grid = QGridLayout()
        self.vitals_grid.setContentsMargins(0, 0, 0, 0)
        self.vitals_grid.setSpacing(2)

        # Standard vitals (Column 0)
        self.hr_card = self._create_hr_card()
        self.bp_card = self._create_bp_card()
        self.spo2_card = self._create_spo2_card()
        self.resp_card = self._create_resp_card()
        self.temp_card = self._create_temp_card()

        # Lab values (Column 1)
        self.plt_card = self._create_plt_card()
        self.sev_card = self._create_sev_card()
        self.org_card = self._create_org_card()
        self.status_card = self._create_status_card()
        self.alarm_card = self._create_alarm_card()

        # Add to grid
        self.vitals_grid.addWidget(self.hr_card, 0, 0)
        self.vitals_grid.addWidget(self.bp_card, 1, 0)
        self.vitals_grid.addWidget(self.spo2_card, 2, 0)
        self.vitals_grid.addWidget(self.resp_card, 3, 0)
        self.vitals_grid.addWidget(self.temp_card, 4, 0)

        self.vitals_grid.addWidget(self.plt_card, 0, 1)
        self.vitals_grid.addWidget(self.sev_card, 1, 1)
        self.vitals_grid.addWidget(self.org_card, 2, 1)
        self.vitals_grid.addWidget(self.status_card, 3, 1)
        self.vitals_grid.addWidget(self.alarm_card, 4, 1)
        self.vitals_layout.addLayout(self.vitals_grid)

        # 2. Touch Control Row
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(2, 0, 2, 2)
        controls_layout.setSpacing(4)

        self.play_pause_btn = QPushButton("PAUSE TIMER")
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d2d5e;
                color: #4fc3f7;
                font-family: Arial, sans-serif;
                font-size: 8px;
                font-weight: bold;
                border: 1px solid #1a365d;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #1a365d;
                color: #ffffff;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_timer)

        self.reset_time_btn = QPushButton("RESET TIME")
        self.reset_time_btn.setStyleSheet("""
            QPushButton {
                background-color: #263238;
                color: #cfd8dc;
                font-family: Arial, sans-serif;
                font-size: 8px;
                font-weight: bold;
                border: 1px solid #37474f;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #37474f;
                color: #ffffff;
            }
        """)
        self.reset_time_btn.clicked.connect(self.reset_timer_clock)

        controls_layout.addWidget(self.play_pause_btn, stretch=1)
        controls_layout.addWidget(self.reset_time_btn, stretch=1)
        self.vitals_layout.addLayout(controls_layout)

        screen_layout.addWidget(self.vitals_panel, stretch=42)
        bezel_layout.addWidget(self.screen_frame)

    def _create_hr_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #113f1f; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("ECG II")
        title_lbl.setStyleSheet("color: #00e676; font-size: 7px; font-weight: bold; border: none; background: transparent; padding: 0;")
        self.hr_val = QLabel("72")
        self.hr_val.setStyleSheet("color: #00e676; font-size: 18px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent; padding: 0;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.hr_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        for label_text in ["PR OFF", "ST1 OFF", "ST2 OFF", "PVCs OFF"]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #00e676; font-size: 5px; font-weight: bold; border: none; background: transparent; padding: 0;")
            right_layout.addWidget(lbl)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_bp_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #3c3c3c; border-radius: 3px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(0)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("NIBP")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.bp_time_lbl = QLabel("00:00")
        self.bp_time_lbl.setStyleSheet("color: #aaaaaa; font-size: 6px; border: none; background: transparent;")
        top_bar_spacer = QWidget()
        top_bar_spacer.setStyleSheet("background: transparent; border: none;")
        top_layout.addWidget(title_lbl)
        top_layout.addWidget(top_bar_spacer)
        top_layout.addStretch()
        top_layout.addWidget(self.bp_time_lbl)
        layout.addLayout(top_layout)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        self.bp_val = QLabel("120/80")
        self.bp_val.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        
        self.bp_mean_lbl = QLabel("90")
        self.bp_mean_lbl.setStyleSheet("color: #ffffff; font-size: 9px; font-weight: bold; border: none; background: transparent;")
        self.bp_mean_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(self.bp_val)
        main_layout.addWidget(self.bp_mean_lbl)
        main_layout.addStretch()
        layout.addLayout(main_layout)

        return card

    def _create_spo2_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #113f4f; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("SpO2")
        title_lbl.setStyleSheet("color: #00e5ff; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.spo2_val = QLabel("98")
        self.spo2_val.setStyleSheet("color: #00e5ff; font-size: 18px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.spo2_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(1)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        pi_lbl = QLabel("PI 0.80")
        pi_lbl.setStyleSheet("color: #00e5ff; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(pi_lbl)
        
        self.pulse_bar = QFrame()
        self.pulse_bar.setStyleSheet("background-color: #00e5ff; border-radius: 1px; min-width: 6px; max-width: 6px; min-height: 8px; border: none;")
        right_layout.addWidget(self.pulse_bar)
        
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_resp_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #3f3f11; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("RESP")
        title_lbl.setStyleSheet("color: #ffea00; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.resp_val = QLabel("20")
        self.resp_val.setStyleSheet("color: #ffea00; font-size: 18px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.resp_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_info = QLabel("rpm")
        lbl_info.setStyleSheet("color: #ffea00; font-size: 6px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(lbl_info)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_temp_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #333333; border-radius: 3px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(0)

        # Top row: title & unit
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("TEMP")
        title_lbl.setStyleSheet("color: #e0e0e0; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        unit_lbl = QLabel("°F")
        unit_lbl.setStyleSheet("color: #e0e0e0; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        top_bar_spacer = QWidget()
        top_bar_spacer.setStyleSheet("background: transparent; border: none;")
        top_layout.addWidget(title_lbl)
        top_layout.addWidget(top_bar_spacer)
        top_layout.addStretch()
        top_layout.addWidget(unit_lbl)
        layout.addLayout(top_layout)

        # Values in a single horizontal row
        val_layout = QHBoxLayout()
        val_layout.setContentsMargins(0, 0, 0, 0)
        val_layout.setSpacing(2)

        self.t1_val = QLabel("T1:98.6")
        self.t1_val.setStyleSheet("color: #e0e0e0; font-size: 8px; font-weight: bold; border: none; background: transparent;")
        
        self.t2_val = QLabel("T2:97.7")
        self.t2_val.setStyleSheet("color: #e0e0e0; font-size: 8px; font-weight: bold; border: none; background: transparent;")
        
        self.td_val = QLabel("TD:0.9")
        self.td_val.setStyleSheet("color: #e0e0e0; font-size: 8px; font-weight: bold; border: none; background: transparent;")

        val_layout.addWidget(self.t1_val)
        val_layout.addWidget(self.t2_val)
        val_layout.addWidget(self.td_val)
        val_layout.addStretch()
        layout.addLayout(val_layout)

        return card

    def _create_plt_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #4f2c11; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("PLT")
        title_lbl.setStyleSheet("color: #ff7043; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.plt_val = QLabel("250")
        self.plt_val.setStyleSheet("color: #ff7043; font-size: 18px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.plt_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_info = QLabel("10³/uL")
        lbl_info.setStyleSheet("color: #ff7043; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(lbl_info)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_sev_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #3c114f; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("SEV")
        title_lbl.setStyleSheet("color: #ba68c8; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.sev_val = QLabel("0%")
        self.sev_val.setStyleSheet("color: #ba68c8; font-size: 18px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.sev_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_info = QLabel("SCORE")
        lbl_info.setStyleSheet("color: #ba68c8; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(lbl_info)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_org_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #4f3c11; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("ORG RISK")
        title_lbl.setStyleSheet("color: #ffb74d; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.org_val = QLabel("OK")
        self.org_val.setStyleSheet("color: #ffb74d; font-size: 14px; font-weight: bold; border: none; font-family: 'Arial', sans-serif; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.org_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.org_sub_lbl = QLabel("")
        self.org_sub_lbl.setStyleSheet("color: #ffb74d; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(self.org_sub_lbl)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_status_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #114f45; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("STATUS")
        title_lbl.setStyleSheet("color: #4db6ac; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.status_val = QLabel("STABLE")
        self.status_val.setStyleSheet("color: #4db6ac; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.status_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_info = QLabel("PATIENT")
        lbl_info.setStyleSheet("color: #4db6ac; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(lbl_info)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _create_alarm_card(self):
        card = QFrame()
        card.setStyleSheet("background-color: #000000; border: 1px solid #4f1111; border-radius: 3px;")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(2)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        title_lbl = QLabel("ALARM")
        title_lbl.setStyleSheet("color: #e57373; font-size: 7px; font-weight: bold; border: none; background: transparent;")
        self.alarm_val = QLabel("OK")
        self.alarm_val.setStyleSheet("color: #e57373; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        left_layout.addWidget(title_lbl)
        left_layout.addWidget(self.alarm_val)
        layout.addLayout(left_layout, stretch=3)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_info = QLabel("SYS")
        lbl_info.setStyleSheet("color: #e57373; font-size: 5px; font-weight: bold; border: none; background: transparent;")
        right_layout.addWidget(lbl_info)
        layout.addLayout(right_layout, stretch=2)
        return card

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._scroll_waveforms)
        self.timer.start(40)  # ~25 FPS

    def update_vitals(self, data):
        self.update_vitals_v2(data, None)

    def update_vitals_v2(self, current_data, next_data=None):
        if not current_data:
            current_data = {}
        self.current_day_data = current_data
        self.next_day_data = next_data if next_data else current_data

        # Reset clock
        self.sim_hour = 0
        self.sim_minute = 0
        self.sim_second = 0
        self.frame_count = 0

        # Calculate exact target date
        day_num = current_data.get('day', 0)
        base_date = datetime.date(2026, 6, 15)
        target_date = base_date + datetime.timedelta(days=day_num)
        self.date_str = target_date.strftime("%d.%m.%Y")

        # Top Bar status
        disease = current_data.get('disease', 'Malaria')
        self.disease_day_label.setText(f"{disease.upper()} | DAY {day_num}")

        self._update_second_by_second_vitals()

    def set_simulation_speed(self, speed_text):
        """Sets simulated clock speed multiplier based on combo text."""
        factors = {"0.5x": 36, "1x": 72, "2x": 144, "5x": 360}
        self.sim_tick_seconds = factors.get(speed_text, 72)

    def toggle_timer(self):
        """Toggles the frozen state and emits state changed signal."""
        new_frozen = not self.is_frozen
        self.set_frozen(new_frozen)
        self.timer_state_changed.emit(not new_frozen)

    def set_frozen(self, frozen):
        """Updates internal frozen state and play/pause button styling."""
        self.is_frozen = frozen
        if self.is_frozen:
            self.play_pause_btn.setText("RESUME TIMER")
            self.play_pause_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffd600;
                    color: #000000;
                    font-family: Arial, sans-serif;
                    font-size: 8px;
                    font-weight: bold;
                    border: 1px solid #b29500;
                    border-radius: 3px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #ffee55;
                }
            """)
        else:
            self.play_pause_btn.setText("PAUSE TIMER")
            self.play_pause_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0d2d5e;
                    color: #4fc3f7;
                    font-family: Arial, sans-serif;
                    font-size: 8px;
                    font-weight: bold;
                    border: 1px solid #1a365d;
                    border-radius: 3px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #1a365d;
                    color: #ffffff;
                }
            """)


    def reset_timer_clock(self):
        """Returns the simulated clock to 00:00:00 for the selected day."""
        self.sim_hour = 0
        self.sim_minute = 0
        self.sim_second = 0
        self.frame_count = 0
        self.bp_time_lbl.setText("00:00")
        self.fig_time_text.set_text(f"{self.date_str}\n00:00:00")
        self._update_second_by_second_vitals()

    def _update_second_by_second_vitals(self):
        f = (self.sim_hour * 3600.0 + self.sim_minute * 60.0 + self.sim_second) / 86400.0

        def interp(key, default):
            v_start = self.current_day_data.get(key, default)
            v_end = self.next_day_data.get(key, default)
            return (1.0 - f) * v_start + f * v_end

        # Calculate baselines
        self.baseline_hr = interp('heart_rate', 72)
        self.baseline_sys_bp = interp('systolic_bp', 120)
        self.baseline_dia_bp = interp('diastolic_bp', 80)
        self.baseline_spo2 = interp('oxygen_saturation', 98)
        
        temp_c = interp('temperature', 36.6)
        self.baseline_temp_f = temp_c * 1.8 + 32.0

        self.baseline_resp_rate = int(12 + (self.baseline_hr - 70) * 0.15 + max(0.0, (self.baseline_temp_f - 98.6) * 1.5))
        self.baseline_resp_rate = max(10, min(35, self.baseline_resp_rate))

        self.baseline_platelets = interp('platelet_count', 250)
        self.baseline_severity = interp('severity', 0.0)

        organ_risks_start = self.current_day_data.get('organ_risks', {})
        organ_risks_end = self.next_day_data.get('organ_risks', {})
        
        interpolated_organs = {}
        self.organ_risks_dict = {}
        for organ in organ_risks_start:
            score_start = organ_risks_start[organ][1]
            score_end = organ_risks_end.get(organ, organ_risks_start[organ])[1]
            score = (1.0 - f) * score_start + f * score_end
            interpolated_organs[organ] = score
            
            # Compute risk level status string
            if score < 25:
                level = "Low"
            elif score < 55:
                level = "Medium"
            elif score < 80:
                level = "High"
            else:
                level = "Critical"
            self.organ_risks_dict[organ] = (level, score)

        sorted_organs = sorted(interpolated_organs.items(), key=lambda x: x[1], reverse=True)
        if sorted_organs:
            self.baseline_highest_organ_name, self.baseline_highest_organ_score = sorted_organs[0]
            if len(sorted_organs) > 1:
                self.baseline_second_organ_name, self.baseline_second_organ_score = sorted_organs[1]
            else:
                self.baseline_second_organ_name = ""
                self.baseline_second_organ_score = 0.0
        else:
            self.baseline_highest_organ_name = "None"
            self.baseline_highest_organ_score = 0.0
            self.baseline_second_organ_name = ""
            self.baseline_second_organ_score = 0.0

        # Circadian modulation
        hour_rad = (self.sim_hour + self.sim_minute / 60.0) * (2.0 * np.pi / 24.0)
        circ_temp = 0.4 * np.sin(hour_rad - np.pi / 2)
        circ_hr = 4.0 * np.sin(hour_rad - np.pi / 2)
        circ_bp = 3.0 * np.sin(hour_rad - np.pi / 2)

        # Micro-fluctuations
        noise_hr = np.random.normal(0, 0.4)
        noise_temp = np.random.normal(0, 0.015)
        noise_spo2 = np.random.normal(0, 0.08)
        noise_resp = np.random.normal(0, 0.25)
        noise_bp_sys = np.random.normal(0, 0.5)
        noise_bp_dia = np.random.normal(0, 0.4)
        noise_plt = np.random.normal(0, 0.6)
        noise_sev = np.random.normal(0, 0.15)
        noise_org = np.random.normal(0, 0.15)

        # Apply values
        self.heart_rate = int(round(self.baseline_hr + circ_hr + noise_hr))
        self.heart_rate = max(20, min(220, self.heart_rate))

        self.temp_f = self.baseline_temp_f + circ_temp + noise_temp
        self.temp_f = max(94.0, min(110.0, self.temp_f))

        self.spo2 = int(round(self.baseline_spo2 + noise_spo2))
        self.spo2 = max(50, min(100, self.spo2))

        self.resp_rate = int(round(self.baseline_resp_rate + noise_resp))
        self.resp_rate = max(5, min(60, self.resp_rate))

        self.systolic_bp = int(round(self.baseline_sys_bp + circ_bp + noise_bp_sys))
        self.diastolic_bp = int(round(self.baseline_dia_bp + circ_bp + noise_bp_dia))
        self.systolic_bp = max(60, min(240, self.systolic_bp))
        self.diastolic_bp = max(30, min(150, self.diastolic_bp))

        self.platelets = int(round(self.baseline_platelets + noise_plt))
        self.platelets = max(0, self.platelets)

        self.severity = self.baseline_severity + noise_sev
        self.severity = max(0.0, min(100.0, self.severity))

        self.highest_organ_score = self.baseline_highest_organ_score + noise_org
        self.highest_organ_score = max(0.0, min(100.0, self.highest_organ_score))

        # Update labels
        self.hr_val.setText(str(self.heart_rate))
        
        self.bp_val.setText(f"{self.systolic_bp}/{self.diastolic_bp}")
        mean_bp = int(self.diastolic_bp + (self.systolic_bp - self.diastolic_bp) / 3)
        self.bp_mean_lbl.setText(str(mean_bp))

        self.spo2_val.setText(str(self.spo2))
        self.resp_val.setText(str(self.resp_rate))
        
        t2_f = self.temp_f - 0.9 - max(0.0, (self.temp_f - 98.6) * 0.15)
        td_f = self.temp_f - t2_f
        self.t1_val.setText(f"T1:{self.temp_f:.1f}")
        self.t2_val.setText(f"T2:{t2_f:.1f}")
        self.td_val.setText(f"TD:{td_f:.1f}")

        # Column 2 updates
        self.plt_val.setText(str(self.platelets))
        self.sev_val.setText(f"{int(round(self.severity))}%")
        
        if self.baseline_highest_organ_name != "None":
            short_name = self.baseline_highest_organ_name[:3].upper()
            self.org_val.setText(f"{short_name} {int(round(self.highest_organ_score))}%")
            if self.baseline_second_organ_name:
                short2 = self.baseline_second_organ_name[:3].upper()
                self.org_sub_lbl.setText(f"{short2} {int(round(self.baseline_second_organ_score))}%")
            else:
                self.org_sub_lbl.setText("")
        else:
            self.org_val.setText("OK")
            self.org_sub_lbl.setText("")

        # Status
        if self.severity < 30.0:
            self.status_val.setText("STABLE")
            self.status_val.setStyleSheet("color: #4db6ac; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        elif self.severity < 60.0:
            self.status_val.setText("GUARDED")
            self.status_val.setStyleSheet("color: #ffb74d; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        else:
            self.status_val.setText("CRITICAL")
            self.status_val.setStyleSheet("color: #e57373; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        # Alarm
        if self.severity > 75.0:
            self.alarm_val.setText("ALARM")
            self.alarm_val.setStyleSheet("color: #ff5252; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        elif self.severity > 45.0:
            self.alarm_val.setText("WARN")
            self.alarm_val.setStyleSheet("color: #ffd600; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        else:
            self.alarm_val.setText("OK")
            self.alarm_val.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        # Prepare dictionary and emit
        current_day_val = self.current_day_data.get('day', 0)
        vitals_dict = {
            'heart_rate': self.heart_rate,
            'temperature': round((self.temp_f - 32.0) / 1.8, 1),
            'systolic_bp': self.systolic_bp,
            'diastolic_bp': self.diastolic_bp,
            'oxygen_saturation': self.spo2,
            'platelet_count': self.platelets,
            'severity': self.severity,
            'recovery_probability': interp('recovery_probability', 100.0),
            'progression': interp('progression', 0.0),
            'day': current_day_val,
            'disease': self.current_day_data.get('disease', 'Malaria'),
            'medications': self.current_day_data.get('medications', []),
            'hospitalization_risk': interp('hospitalization_risk', 0.0),
            
            # Additional fields for dashboard
            'hemoglobin': round(interp('hemoglobin', 15.0), 1),
            'wbc_count': int(interp('wbc_count', 7000)),
            'rbc_count': round(interp('rbc_count', 5.0), 2),
            'fatigue': int(interp('fatigue', 0)),
            'hydration': int(interp('hydration', 100)),
            'pain_level': int(interp('pain_level', 0)),
            'inflammation': int(interp('inflammation', 0)),
            'nausea': int(interp('nausea', 0)),
            'headache': int(interp('headache', 0)),
            'weakness': int(interp('weakness', 0)),
            'spleen_size': round(interp('spleen_size', 1.0), 1),
            'liver_enzymes': int(interp('liver_enzymes', 40)),
            
            # Organ risks expected by organ panel and body model
            'organ_risks': self.organ_risks_dict
        }
        self.vitals_updated.emit(vitals_dict)


    def _tick_clock_and_update_vitals(self):
        self.sim_second += self.sim_tick_seconds
        if self.sim_second >= 60:
            mins = self.sim_second // 60
            self.sim_second = self.sim_second % 60
            self.sim_minute += mins
            if self.sim_minute >= 60:
                hrs = self.sim_minute // 60
                self.sim_minute = self.sim_minute % 60
                self.sim_hour += hrs
                if self.sim_hour >= 24:
                    self.sim_hour = 0
                    self.day_completed.emit()

        self.bp_time_lbl.setText(f"{self.sim_hour:02d}:{self.sim_minute:02d}")
        self.fig_time_text.set_text(f"{self.date_str}\n{self.sim_hour:02d}:{self.sim_minute:02d}:{self.sim_second:02d}")

        self.frame_count += 1
        if self.frame_count >= 25:
            self.frame_count = 0
            self._update_second_by_second_vitals()

    def _scroll_waveforms(self):
        """Scrolls the oscilloscope waves on the canvas in real-time."""
        if self.is_frozen:
            return

        self._tick_clock_and_update_vitals()

        self.t += 0.04

        T_heart = 60.0 / self.heart_rate
        phase = self.t % T_heart

        val_ecg = 0.0
        if 0.0 <= phase < 0.08 * T_heart:
            val_ecg = 0.15 * np.sin((phase / (0.08 * T_heart)) * np.pi)
        elif 0.12 * T_heart <= phase < 0.15 * T_heart:
            val_ecg = -0.2 * np.sin(((phase - 0.12 * T_heart) / (0.03 * T_heart)) * np.pi)
        elif 0.15 * T_heart <= phase < 0.19 * T_heart:
            val_ecg = 1.25 * np.sin(((phase - 0.15 * T_heart) / (0.04 * T_heart)) * np.pi)
        elif 0.19 * T_heart <= phase < 0.23 * T_heart:
            val_ecg = -0.35 * np.sin(((phase - 0.19 * T_heart) / (0.04 * T_heart)) * np.pi)
        elif 0.32 * T_heart <= phase < 0.52 * T_heart:
            val_ecg = 0.25 * np.sin(((phase - 0.32 * T_heart) / (0.20 * T_heart)) * np.pi)

        val_ecg += np.random.normal(0, 0.012)

        # ECG2 Lead V5
        val_ecg2 = val_ecg * 0.75
        if 0.32 * T_heart <= phase < 0.52 * T_heart:
            val_ecg2 = -0.1 * np.sin(((phase - 0.32 * T_heart) / (0.20 * T_heart)) * np.pi)
        val_ecg2 += np.random.normal(0, 0.01)

        # PPG
        val_ppg = 0.0
        if 0.0 <= phase < 0.32 * T_heart:
            val_ppg = np.sin((phase / (0.32 * T_heart)) * (np.pi / 2))
        elif 0.32 * T_heart <= phase < 0.46 * T_heart:
            val_ppg = 1.0 - 0.18 * np.sin(((phase - 0.32 * T_heart) / (0.14 * T_heart)) * np.pi)
        elif 0.46 * T_heart <= T_heart:
            val_ppg = 0.82 * (1.0 - (phase - 0.46 * T_heart) / (0.54 * T_heart))
        val_ppg = val_ppg * 0.7 + 0.1 + np.random.normal(0, 0.008)

        # RESP
        T_resp = 60.0 / self.resp_rate
        phase_resp = self.t % T_resp
        val_resp = 0.5 * np.sin((phase_resp / T_resp) * 2 * np.pi) + 0.5 + np.random.normal(0, 0.005)

        self.ecg_data.append(val_ecg)
        self.ecg2_data.append(val_ecg2)
        self.ppg_data.append(val_ppg)
        self.resp_data.append(val_resp)

        self.ecg_line.set_ydata(list(self.ecg_data))
        self.ecg2_line.set_ydata(list(self.ecg2_data))
        self.ppg_line.set_ydata(list(self.ppg_data))
        self.resp_line.set_ydata(list(self.resp_data))

        self.canvas.draw_idle()
