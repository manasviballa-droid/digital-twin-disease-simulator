"""
Organ Risk Panel — displays organ risk levels with visual indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QProgressBar, QFrame, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
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


class OrganRow(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, organ, parent=None):
        super().__init__(parent)
        self.organ = organ
        self.selected = False
        self.setObjectName("OrganRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#OrganRow {
                background: #061224;
                border: 1px solid #0d2d5e;
                border-radius: 4px;
            }
            QFrame#OrganRow:hover {
                background: #0d2547;
                border-color: #4fc3f7;
            }
        """)

        h = QHBoxLayout(self)
        h.setContentsMargins(6, 4, 6, 4)
        h.setSpacing(6)

        icon = ORGAN_ICONS.get(organ, "◈")
        self.icon_lbl = QLabel(f"{icon}")
        self.icon_lbl.setFixedWidth(16)
        self.icon_lbl.setStyleSheet("font-size: 11px; color: #4fc3f7;")
        h.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(organ.upper())
        self.name_lbl.setFixedWidth(78)
        self.name_lbl.setStyleSheet("color: #5a8fd4; font-size: 9px; font-weight: bold;")
        h.addWidget(self.name_lbl)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(7)
        self.bar.setStyleSheet("""
            QProgressBar { background: #0a1828; border: none; border-radius: 3px; }
            QProgressBar::chunk { background: #3a789c; border-radius: 3px; }
        """)
        h.addWidget(self.bar)

        self.risk_lbl = QLabel("LOW")
        self.risk_lbl.setFixedWidth(44)
        self.risk_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.risk_lbl.setStyleSheet("""
            color: #3a789c; font-size: 8px; font-weight: bold;
            background: #0a1d2d; border-radius: 3px; padding: 1px 3px;
        """)
        h.addWidget(self.risk_lbl)

    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame#OrganRow {
                    background: #10305a;
                    border: 1.5px solid #4fc3f7;
                    border-radius: 4px;
                }
                QFrame#OrganRow:hover {
                    background: #143a6d;
                    border-color: #4fc3f7;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#OrganRow {
                    background: #061224;
                    border: 1px solid #0d2d5e;
                    border-radius: 4px;
                }
                QFrame#OrganRow:hover {
                    background: #0d2547;
                    border-color: #4fc3f7;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.organ)
            event.accept()
        else:
            super().mousePressEvent(event)


class OrganRiskPanel(QGroupBox):
    organ_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__("  ORGAN RISK ANALYSIS", parent)
        self.organ_widgets = {}
        self.rows = {}
        self.selected_organ = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 12, 8, 8)

        organs = ["Liver", "Spleen", "Brain", "Heart", "Lungs", "Kidneys", "Blood System", "Muscles", "Joints"]
        for organ in organs:
            row = self._make_organ_row(organ)
            layout.addWidget(row)

    def _make_organ_row(self, organ):
        row = OrganRow(organ)
        row.clicked.connect(self.select_organ)
        self.organ_widgets[organ] = (row.bar, row.risk_lbl)
        self.rows[organ] = row
        return row

    def select_organ(self, organ_name):
        if self.selected_organ in self.rows:
            self.rows[self.selected_organ].set_selected(False)
        self.selected_organ = organ_name
        if organ_name in self.rows:
            self.rows[organ_name].set_selected(True)
        self.organ_selected.emit(organ_name)

    def deselect_all(self):
        if self.selected_organ in self.rows:
            self.rows[self.selected_organ].set_selected(False)
        self.selected_organ = None
        self.organ_selected.emit(None)

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


class OrganDetailPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("  ORGAN PHYSIOLOGICAL ANALYSIS", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        self.desc_text = QTextBrowser()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(180)
        self.desc_text.setMaximumHeight(280)
        self.desc_text.setStyleSheet("""
            QTextBrowser {
                background: #040c1a;
                border: 1px solid #0d2d5e;
                color: #7ecbf5;
                font-size: 11px;
                font-family: 'Consolas', monospace;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.desc_text)
        
        self.set_placeholder()

    def set_placeholder(self):
        self.desc_text.setHtml("""
            <div style="color: #4a7ab5; text-align: center; margin-top: 50px; font-family: 'Consolas', monospace; font-size: 11px;">
                ◈ SYSTEM IDLE ◈<br><br>
                SELECT AN ORGAN ABOVE TO INITIATE<br>
                PHYSIOLOGICAL STATUS SCAN
            </div>
        """)

    def update_details(self, html_content):
        self.desc_text.setHtml(html_content)
