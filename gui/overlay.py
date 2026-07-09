import sys
import math

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QSystemTrayIcon,
    QMenu,
)

STATE_COLORS = {
    "idle": QColor(170, 175, 185),
    "listening": QColor(120, 170, 200),
    "thinking": QColor(180, 180, 180),
    "speaking": QColor(180, 100, 100),
    "error": QColor(180, 100, 100),
}

overlay_instance = None


class OrbWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.state = "idle"
        self.t = 0

        self.resize(100, 100)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.drag_pos = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

        self.setup_tray()

    def setup_tray(self):

        self.tray = QSystemTrayIcon(self)

        self.tray.setIcon(
            self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            )
        )

        menu = QMenu()

        show_action = menu.addAction("Show Aria")
        hide_action = menu.addAction("Hide Aria")
        quit_action = menu.addAction("Quit")

        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)

        self.tray.setToolTip("Aria")

        self.tray.activated.connect(
            self.on_tray_click
        )

        self.tray.show()

    def on_tray_click(self, reason):

        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:

            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def set_state(self, state):
        self.state = state

    def animate(self):
        self.t += 0.025
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        cx = self.width() / 2
        cy = self.height() / 2

        color = STATE_COLORS.get(
            self.state,
            STATE_COLORS["idle"]
        )

        pulse_speed = 1

        if self.state == "listening":
            pulse_speed = 2

        elif self.state == "speaking":
            pulse_speed = 3

        radius = 10 + math.sin(
            self.t * pulse_speed
        ) * 2

        if self.state == "idle":
            radius = 10 + math.sin(self.t) * 0.8

        for i in range(6):

            glow_radius = radius + i * 7

            alpha = max(
                0,
                25 - i * 2
            )

            glow = QColor(color)
            glow.setAlpha(alpha)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))

            painter.drawEllipse(
                int(cx - glow_radius),
                int(cy - glow_radius),
                int(glow_radius * 2),
                int(glow_radius * 2)
            )

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(
            int(cx - radius),
            int(cy - radius),
            int(radius * 2),
            int(radius * 2)
        )

        painter.setBrush(
            QBrush(QColor(255, 255, 255, 80))
        )

        painter.drawEllipse(
            int(cx - radius * 0.5),
            int(cy - radius * 0.5),
            int(radius),
            int(radius)
        )

        if self.state == "thinking":

            ring_r = radius + 30

            angle = self.t * 2

            x = cx + math.cos(angle) * ring_r
            y = cy + math.sin(angle) * ring_r

            painter.setBrush(QBrush(color))

            painter.drawEllipse(
                int(x - 8),
                int(y - 8),
                16,
                16
            )

        if self.state == "listening":

            ripple = (
                self.t * 40
            ) % 120

            pen = QPen(color)
            pen.setWidth(2)

            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawEllipse(
                int(cx - ripple),
                int(cy - ripple),
                int(ripple * 2),
                int(ripple * 2)
            )

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):

        if self.drag_pos:
            self.move(
                event.globalPosition().toPoint()
                - self.drag_pos
            )

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self.hide()


def set_status(text, state="idle"):
    global overlay_instance

    if overlay_instance:
        overlay_instance.set_state(state)


def start_overlay_blocking():

    global overlay_instance

    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)

    overlay_instance = OrbWindow()

    overlay_instance.move(1400, 150)

    overlay_instance.show()

    app.exec()