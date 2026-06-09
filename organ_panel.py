"""
Organ Risk Panel — displays organ risk levels with visual indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


RISK_COLORS = {
    "Low": ("#3a789c", "#0a1d2d"),
    "Medium": ("#b88a30", "#281e0a"),
    "High": ("#c45d30", "#2b140a"),
    "Critical": ("#b83b3b", "#280a0a"),
}

ORGAN_ICONS = {
    "Liver": "◈",
    "Spleen": "◈",
    "Brain": "◈",
    "Heart": "◈",
    "Lungs": "◈",
    "Kidneys": "◈",
    "Blood System": "◈",
    "Muscles": "◈",
    "Joints": "◈",
    "Skin": "◈",
}


class OrganRiskPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("  ORGAN RISK ANALYSIS", parent)
        self.organ_widgets = {}
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 12, 8, 8)

        organs = ["Liver", "Spleen", "Brain", "Heart", "Lungs", "Kidneys", "Blood System", "Muscles", "Joints"]
        for organ in organs:
            row = self._make_organ_row(organ)
            layout.addWidget(row)

    def _make_organ_row(self, organ):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: transparent; }")
        h = QHBoxLayout(frame)
        h.setContentsMargins(0, 1, 0, 1)
        h.setSpacing(6)

        icon = ORGAN_ICONS.get(organ, "◈")
        icon_lbl = QLabel(f"{icon}")
        icon_lbl.setFixedWidth(16)
        icon_lbl.setStyleSheet("font-size: 11px;")
        h.addWidget(icon_lbl)

        name_lbl = QLabel(organ.upper())
        name_lbl.setFixedWidth(78)
        name_lbl.setStyleSheet("color: #5a8fd4; font-size: 9px; font-weight: bold;")
        h.addWidget(name_lbl)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(7)
        bar.setStyleSheet("""
            QProgressBar { background: #0a1828; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #3a789c; border-radius: 3px; }
        """)
        h.addWidget(bar)

        risk_lbl = QLabel("LOW")
        risk_lbl.setFixedWidth(44)
        risk_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_lbl.setStyleSheet("""
            color: #3a789c; font-size: 8px; font-weight: bold;
            background: #0a1d2d; border-radius: 3px; padding: 1px 3px;
        """)
        h.addWidget(risk_lbl)

        self.organ_widgets[organ] = (bar, risk_lbl)
        return frame

    def update_organs(self, organ_risks: dict):
        for organ, (bar, lbl) in self.organ_widgets.items():
            if organ in organ_risks:
                level, score = organ_risks[organ]
                bar.setValue(int(score))
                lbl.setText(level.upper())

                fg, bg = RISK_COLORS.get(level, ("#00e676", "#003316"))
                bar.setStyleSheet(f"""
                    QProgressBar {{ background: #0a1828; border: none; border-radius: 3px; }}
                    QProgressBar::chunk {{ background: {fg}; border-radius: 3px; }}
                """)
                lbl.setStyleSheet(f"""
                    color: {fg}; font-size: 8px; font-weight: bold;
                    background: {bg}; border-radius: 3px; padding: 1px 3px;
                """)
            else:
                bar.setValue(5)
                lbl.setText("--")
                lbl.setStyleSheet("color: #1a4060; font-size: 8px; font-weight: bold;")
