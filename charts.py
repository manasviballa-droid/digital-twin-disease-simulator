"""
Charts Widget — Comprehensive disease progression visualization
Multiple chart panels: fever, platelets, organs, recovery, vitals
"""

import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import Qt


CHART_STYLE = {
    "bg": "#040c1a",
    "panel_bg": "#070f20",
    "grid": "#0d2040",
    "text": "#5a8fd4",
    "title": "#4fc3f7",
    "border": "#0d2d5e",
}

DISEASE_PALETTE = {
    "Malaria": {
        "primary": "#c57552", "secondary": "#b85151", "tertiary": "#bfa054",
        "accent": "#c07a4a", "positive": "#438c75", "negative": "#b83b3b",
    },
    "Dengue Fever": {
        "primary": "#b85165", "secondary": "#b33b5c", "tertiary": "#9b7fa8",
        "accent": "#b86882", "positive": "#4fa8b8", "negative": "#b83b3b",
    },
    "Chikungunya": {
        "primary": "#bfa054", "secondary": "#b3833b", "tertiary": "#b3733b",
        "accent": "#bfa068", "positive": "#589e7d", "negative": "#c57552",
    },
}


def style_ax(ax, title=""):
    ax.set_facecolor(CHART_STYLE["panel_bg"])
    ax.tick_params(colors=CHART_STYLE["text"], labelsize=7)
    ax.spines[:].set_color(CHART_STYLE["border"])
    ax.grid(True, color=CHART_STYLE["grid"], alpha=0.5, linewidth=0.5)
    if title:
        ax.set_title(title, color=CHART_STYLE["title"], fontsize=8,
                    fontweight='bold', pad=5, fontfamily='monospace')


class ChartsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_disease = "Malaria"
        self.data_history = []
        self.days = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self._build_fever_tab()
        self._build_vitals_tab()
        self._build_organ_tab()

    def _make_figure(self, rows=1, cols=1, figsize=(10, 3.2)):
        fig = Figure(figsize=figsize, facecolor=CHART_STYLE["bg"])
        fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.14, hspace=0.45, wspace=0.35)
        return fig

    def _build_fever_tab(self):
        self.fever_fig = self._make_figure(1, 3, (12, 3.2))
        self.fever_canvas = FigureCanvas(self.fever_fig)
        self.fever_canvas.setStyleSheet(f"background: {CHART_STYLE['bg']};")

        gs = GridSpec(1, 3, figure=self.fever_fig)
        self.ax_temp = self.fever_fig.add_subplot(gs[0, 0])
        self.ax_platelet = self.fever_fig.add_subplot(gs[0, 1])
        self.ax_wbc = self.fever_fig.add_subplot(gs[0, 2])

        for ax, title in [(self.ax_temp, "FEVER PROGRESSION (°F)"),
                          (self.ax_platelet, "PLATELET COUNT (×10³/μL)"),
                          (self.ax_wbc, "WBC COUNT (/μL)")]:
            style_ax(ax, title)

        self.tab_widget.addTab(self.fever_canvas, "Fever & Blood")

    def _build_vitals_tab(self):
        self.vitals_fig = self._make_figure(2, 2, (12, 4.5))
        self.vitals_fig.subplots_adjust(left=0.07, right=0.97, top=0.90, bottom=0.10, hspace=0.55, wspace=0.35)
        self.vitals_canvas = FigureCanvas(self.vitals_fig)
        self.vitals_canvas.setStyleSheet(f"background: {CHART_STYLE['bg']};")

        gs = GridSpec(2, 2, figure=self.vitals_fig)
        self.ax_hr = self.vitals_fig.add_subplot(gs[0, 0])
        self.ax_bp = self.vitals_fig.add_subplot(gs[0, 1])
        self.ax_spo2 = self.vitals_fig.add_subplot(gs[1, 0])
        self.ax_hgb = self.vitals_fig.add_subplot(gs[1, 1])

        for ax, title in [(self.ax_hr, "HEART RATE (bpm)"),
                          (self.ax_bp, "BLOOD PRESSURE (mmHg)"),
                          (self.ax_spo2, "OXYGEN SATURATION (%)"),
                          (self.ax_hgb, "HEMOGLOBIN (g/dL)")]:
            style_ax(ax, title)

        self.tab_widget.addTab(self.vitals_canvas, "Vital Signs")

    def _build_organ_tab(self):
        self.organ_fig = self._make_figure(1, 3, (12, 3.5))
        self.organ_canvas = FigureCanvas(self.organ_fig)
        self.organ_canvas.setStyleSheet(f"background: {CHART_STYLE['bg']};")

        gs = GridSpec(1, 3, figure=self.organ_fig)
        self.ax_organ_risk = self.organ_fig.add_subplot(gs[0, 0])
        self.ax_severity = self.organ_fig.add_subplot(gs[0, 1])
        self.ax_liver = self.organ_fig.add_subplot(gs[0, 2])

        for ax, title in [(self.ax_organ_risk, "ORGAN RISK OVER TIME"),
                          (self.ax_severity, "DISEASE SEVERITY (%)"),
                          (self.ax_liver, "LIVER ENZYME TREND")]:
            style_ax(ax, title)

        self.tab_widget.addTab(self.organ_canvas, "Organ Risk")



    def set_disease(self, disease):
        self.current_disease = disease
        self.reset()

    def reset(self):
        self.data_history = []
        self.days = []
        self._redraw_all()

    def add_data_point(self, day, data):
        self.days.append(day)
        self.data_history.append(data)
        self._redraw_all()

    def _get_palette(self):
        return DISEASE_PALETTE.get(self.current_disease, DISEASE_PALETTE["Malaria"])

    def _redraw_all(self):
        pal = self._get_palette()
        self._draw_fever_charts(pal)
        self._draw_vitals_charts(pal)
        self._draw_organ_charts(pal)

        for canvas in [self.fever_canvas, self.vitals_canvas, self.organ_canvas]:
            canvas.draw_idle()

    def _draw_fever_charts(self, pal):
        for ax in [self.ax_temp, self.ax_platelet, self.ax_wbc]:
            ax.clear()
            style_ax(ax)

        if not self.days:
            self.ax_temp.set_title("FEVER PROGRESSION (°F)", color=CHART_STYLE["title"],
                                    fontsize=8, fontweight='bold', fontfamily='monospace')
            self.ax_platelet.set_title("PLATELET COUNT (×10³/μL)", color=CHART_STYLE["title"],
                                        fontsize=8, fontweight='bold', fontfamily='monospace')
            self.ax_wbc.set_title("WBC COUNT (/μL)", color=CHART_STYLE["title"],
                                   fontsize=8, fontweight='bold', fontfamily='monospace')
            return

        temps_c = [d.get('temperature', 36.6) for d in self.data_history]
        temps = [t * 1.8 + 32.0 for t in temps_c]
        platelets = [d.get('platelet_count', 250) for d in self.data_history]
        wbcs = [d.get('wbc_count', 7000) for d in self.data_history]

        # Temp chart with fever zones
        self.ax_temp.axhspan(99.5, 101.3, alpha=0.08, color="#b88a30")
        self.ax_temp.axhspan(101.3, 104.0, alpha=0.08, color="#c57552")
        self.ax_temp.axhspan(104.0, 107.6, alpha=0.08, color="#b83b3b")
        self.ax_temp.axhline(99.5, color="#b88a30", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_temp.axhline(101.3, color="#c57552", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_temp.fill_between(self.days, temps, 97.7, alpha=0.25, color=pal["primary"])
        self.ax_temp.plot(self.days, temps, color=pal["primary"], linewidth=2, marker='o', markersize=3)
        self.ax_temp.set_ylim(95.9, 107.6)
        self.ax_temp.set_xlabel("Day", color=CHART_STYLE["text"], fontsize=7)
        self.ax_temp.set_ylabel("°F", color=CHART_STYLE["text"], fontsize=7)
        style_ax(self.ax_temp, "FEVER PROGRESSION (°F)")

        # Platelet chart
        self.ax_platelet.axhspan(0, 50, alpha=0.1, color="#b83b3b")
        self.ax_platelet.axhspan(50, 100, alpha=0.08, color="#c57552")
        self.ax_platelet.axhspan(100, 150, alpha=0.06, color="#b88a30")
        self.ax_platelet.axhline(150, color="#4faf8c", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_platelet.fill_between(self.days, platelets, 0, alpha=0.25, color=pal["secondary"])
        self.ax_platelet.plot(self.days, platelets, color=pal["secondary"], linewidth=2, marker='s', markersize=3)
        self.ax_platelet.set_xlabel("Day", color=CHART_STYLE["text"], fontsize=7)
        self.ax_platelet.set_ylabel("Count", color=CHART_STYLE["text"], fontsize=7)
        style_ax(self.ax_platelet, "PLATELET COUNT (×10³/μL)")

        # WBC chart
        self.ax_wbc.axhline(4000, color="#b88a30", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_wbc.axhline(11000, color="#b88a30", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_wbc.fill_between(self.days, wbcs, 0, alpha=0.25, color=pal["tertiary"])
        self.ax_wbc.plot(self.days, wbcs, color=pal["tertiary"], linewidth=2, marker='^', markersize=3)
        self.ax_wbc.set_xlabel("Day", color=CHART_STYLE["text"], fontsize=7)
        self.ax_wbc.set_ylabel("/μL", color=CHART_STYLE["text"], fontsize=7)
        style_ax(self.ax_wbc, "WBC COUNT (/μL)")

    def _draw_vitals_charts(self, pal):
        for ax in [self.ax_hr, self.ax_bp, self.ax_spo2, self.ax_hgb]:
            ax.clear()

        if not self.days:
            for ax, t in [(self.ax_hr, "HEART RATE (bpm)"), (self.ax_bp, "BLOOD PRESSURE (mmHg)"),
                           (self.ax_spo2, "OXYGEN SATURATION (%)"), (self.ax_hgb, "HEMOGLOBIN (g/dL)")]:
                style_ax(ax, t)
            return

        hrs = [d.get('heart_rate', 72) for d in self.data_history]
        sys_bp = [d.get('systolic_bp', 120) for d in self.data_history]
        dia_bp = [d.get('diastolic_bp', 80) for d in self.data_history]
        spo2s = [d.get('oxygen_saturation', 98) for d in self.data_history]
        hgbs = [d.get('hemoglobin', 15) for d in self.data_history]

        # Heart rate
        self.ax_hr.axhline(100, color="#c57552", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_hr.fill_between(self.days, hrs, 60, alpha=0.15, color="#b83b3b")
        self.ax_hr.plot(self.days, hrs, color="#b83b3b", linewidth=2, marker='o', markersize=3)
        self.ax_hr.set_ylim(55, 140)
        style_ax(self.ax_hr, "HEART RATE (bpm)")

        # Blood pressure
        self.ax_bp.fill_between(self.days, sys_bp, dia_bp, alpha=0.3, color="#ce93d8")
        self.ax_bp.plot(self.days, sys_bp, color="#ce93d8", linewidth=2, label="SYS", marker='o', markersize=3)
        self.ax_bp.plot(self.days, dia_bp, color="#9c64d0", linewidth=2, label="DIA", marker='s', markersize=3)
        self.ax_bp.legend(fontsize=7, facecolor="#070f20", edgecolor="#0d2d5e", labelcolor="#5a8fd4")
        style_ax(self.ax_bp, "BLOOD PRESSURE (mmHg)")

        # SpO2
        self.ax_spo2.axhspan(85, 92, alpha=0.1, color="#b83b3b")
        self.ax_spo2.axhspan(92, 95, alpha=0.08, color="#b88a30")
        self.ax_spo2.axhline(95, color="#4faf8c", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_spo2.fill_between(self.days, spo2s, 80, alpha=0.3, color="#4fc3f7")
        self.ax_spo2.plot(self.days, spo2s, color="#4fc3f7", linewidth=2, marker='o', markersize=3)
        self.ax_spo2.set_ylim(80, 100)
        style_ax(self.ax_spo2, "OXYGEN SATURATION (%)")

        # Hemoglobin
        self.ax_hgb.axhline(12, color="#b88a30", alpha=0.3, linewidth=0.8, linestyle='--')
        self.ax_hgb.fill_between(self.days, hgbs, 0, alpha=0.15, color="#5ca8b8")
        self.ax_hgb.plot(self.days, hgbs, color="#5ca8b8", linewidth=2, marker='o', markersize=3)
        style_ax(self.ax_hgb, "HEMOGLOBIN (g/dL)")

    def _draw_organ_charts(self, pal):
        for ax in [self.ax_organ_risk, self.ax_severity, self.ax_liver]:
            ax.clear()

        if not self.days:
            for ax, t in [(self.ax_organ_risk, "ORGAN RISK OVER TIME"),
                           (self.ax_severity, "DISEASE SEVERITY (%)"),
                           (self.ax_liver, "LIVER ENZYME TREND")]:
                style_ax(ax, t)
            return

        # Organ risk trends - pick top 3 organs by current risk
        organ_colors = {
            "Liver": "#c57552", "Spleen": "#9c609c", "Blood System": "#b83b3b",
            "Joints": "#bfa054", "Muscles": "#b3833b", "Brain": "#4fa8b8",
            "Kidneys": "#b3733b", "Heart": "#b34242", "Lungs": "#5ca8b8",
            "Skin": "#b86882",
        }

        if self.data_history:
            latest = self.data_history[-1]
            organ_risks = latest.get('organ_risks', {})
            for organ, (level, score) in list(organ_risks.items())[:5]:
                scores = [d.get('organ_risks', {}).get(organ, ("Low", 0))[1]
                         for d in self.data_history]
                col = organ_colors.get(organ, "#4fc3f7")
                self.ax_organ_risk.plot(self.days, scores, color=col, linewidth=1.5,
                                        label=organ[:7], alpha=0.9)

        self.ax_organ_risk.legend(fontsize=6, facecolor="#070f20",
                                   edgecolor="#0d2d5e", labelcolor="#5a8fd4",
                                   loc='upper left', ncol=2)
        self.ax_organ_risk.set_ylim(0, 105)
        style_ax(self.ax_organ_risk, "ORGAN RISK OVER TIME")

        # Severity
        severities = [d.get('severity', 0) for d in self.data_history]
        hosp_risks = [d.get('hospitalization_risk', 0) for d in self.data_history]
        self.ax_severity.fill_between(self.days, severities, 0, alpha=0.4, color=pal["primary"])
        self.ax_severity.fill_between(self.days, hosp_risks, 0, alpha=0.25, color=pal["negative"])
        self.ax_severity.plot(self.days, severities, color=pal["primary"], linewidth=2, label="Severity")
        self.ax_severity.plot(self.days, hosp_risks, color=pal["negative"], linewidth=1.5,
                               linestyle='--', label="Hosp.Risk")
        self.ax_severity.legend(fontsize=7, facecolor="#070f20", edgecolor="#0d2d5e", labelcolor="#5a8fd4")
        self.ax_severity.set_ylim(0, 105)
        style_ax(self.ax_severity, "DISEASE SEVERITY (%)")

        # Liver enzymes
        liver_enzymes = [d.get('liver_enzymes', 40) for d in self.data_history]
        self.ax_liver.axhline(56, color="#b88a30", alpha=0.3, linewidth=0.8, linestyle='--',
                              label="Normal limit")
        self.ax_liver.fill_between(self.days, liver_enzymes, 0, alpha=0.15, color="#c57552")
        self.ax_liver.plot(self.days, liver_enzymes, color="#c57552", linewidth=2, marker='o', markersize=3)
        self.ax_liver.set_ylabel("ALT (U/L)", color=CHART_STYLE["text"], fontsize=7)
        style_ax(self.ax_liver, "LIVER ENZYME TREND")


