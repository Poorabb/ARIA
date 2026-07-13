import sys
import math

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QActionGroup
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QSystemTrayIcon,
    QMenu,
)

from agent.state import get_mode, set_mode

# Colors for the four normal-mode sub-states
STATE_COLORS = {
    "idle": QColor(255, 255, 255),        # white
    "listening": QColor(41, 121, 255),    # blue
    "thinking": QColor(13, 71, 161),      # deep blue (same palette, no purple tint)
    "speaking": QColor(46, 204, 113),     # green (responding)
    "error": QColor(231, 76, 60),         # red
}

# Colors that override everything above when a special mode is active
MODE_COLORS = {
    "dnd": QColor(231, 76, 60),           # red
    "mute": QColor(149, 165, 166),        # grey
}

_CLICK_DRAG_THRESHOLD = 6  # pixels - below this, a mouse-up counts as a click, not a drag
_GLOW_RINGS = 6
_GLOW_STEP = 7

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
        self._press_global = None
        self._moved = 0

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

        menu.addSeparator()

        # Mode toggle - exclusive selection (only one checked at a time)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)

        self.normal_action = menu.addAction("Normal Mode")
        self.mute_action = menu.addAction("Mute Mode")
        self.dnd_action = menu.addAction("Do Not Disturb")

        for action, mode_value in (
            (self.normal_action, "normal"),
            (self.mute_action, "mute"),
            (self.dnd_action, "dnd"),
        ):
            action.setCheckable(True)
            mode_group.addAction(action)
            action.triggered.connect(lambda checked, m=mode_value: set_mode(m))

        menu.addSeparator()

        quit_action = menu.addAction("Quit")

        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)

        self.tray.setToolTip("Aria")

        self.tray.activated.connect(
            self.on_tray_click
        )

        # Refresh the checkmarks right before the menu opens, so they reflect
        # mode changes made via voice command since the menu was last shown
        menu.aboutToShow.connect(self._sync_mode_menu)

        self.tray.show()

    def _sync_mode_menu(self):
        mode = get_mode()
        self.normal_action.setChecked(mode == "normal")
        self.mute_action.setChecked(mode == "mute")
        self.dnd_action.setChecked(mode == "dnd")

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
        self.t += 0.01
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        cx = self.width() / 2
        cy = self.height() / 2

        mode = get_mode()
        special = mode in MODE_COLORS

        color = MODE_COLORS[mode] if special else STATE_COLORS.get(self.state, STATE_COLORS["idle"])

        radius = 10

        if not special:
            if self.state == "listening":
                radius = 10 + math.sin(self.t * 3) * 2
            elif self.state == "thinking":
                radius = 10 + math.sin(self.t * 6) * 3  # faster, slightly deeper breathing
            elif self.state == "idle":
                radius = 10 + math.sin(self.t) * 0.8

        outer_glow_radius = radius + (_GLOW_RINGS - 1) * _GLOW_STEP  # the orb's true outer edge

        for i in range(_GLOW_RINGS):

            glow_radius = radius + i * _GLOW_STEP

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

        if not special and self.state == "speaking":

            # Ripple pulses outward from the center but is capped at the orb's own
            # outer glow edge, instead of shooting out past it indefinitely.
            ripple = (self.t * 40) % outer_glow_radius

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
            self._press_global = event.globalPosition().toPoint()
            self._moved = 0

    def mouseMoveEvent(self, event):

        if self.drag_pos:
            self.move(
                event.globalPosition().toPoint()
                - self.drag_pos
            )
            if self._press_global:
                delta = event.globalPosition().toPoint() - self._press_global
                self._moved = max(self._moved, abs(delta.x()) + abs(delta.y()))

    def mouseReleaseEvent(self, event):
        # A near-stationary click (not a drag) while in DND resumes normal mode
        if self._moved < _CLICK_DRAG_THRESHOLD and get_mode() == "dnd":
            set_mode("normal")

        self.drag_pos = None
        self._press_global = None
        self._moved = 0

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

    overlay_instance.move(10, 10)

    overlay_instance.show()

    app.exec()


