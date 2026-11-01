"""
SestenHarfe - Canlı Mikrofon Seviye Göstergesi (VU Meter)
PyQt6 QPainter ile donanım ivmeli, yumuşak geçişli ses seviyesi çubuğu
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QPen
from PyQt6.QtCore import Qt, QTimer


class AudioLevelMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setMinimumWidth(120)

        self._current_level = 0.0  # 0.0 - 1.0
        self._target_level = 0.0
        self._peak_level = 0.0

        # Yumuşak animasyon için 30 FPS zamanlayıcı
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animation)
        self.anim_timer.start(33)

    def set_level(self, level: float):
        """0.0 ile 1.0 arasındaki mikrofon seviyesini günceller."""
        self._target_level = max(0.0, min(1.0, level))
        if self._target_level > self._peak_level:
            self._peak_level = self._target_level

    def _update_animation(self):
        """Düşüş animasyonunu yumuşatır."""
        # Seviye yukarı hızla çıkar, aşağı yavaş iner (decay)
        if self._current_level < self._target_level:
            self._current_level = self._target_level
        else:
            self._current_level = max(0.0, self._current_level - 0.05)

        # Tepe noktası yavaşça sönsün
        self._peak_level = max(0.0, self._peak_level - 0.02)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = 4

        # Arka plan yuvası
        bg_brush = QBrush(QColor("#1e202e"))
        painter.setBrush(bg_brush)
        painter.setPen(QPen(QColor("#2c2f42"), 1))
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Doluluk çubuğu
        filled_w = int(w * self._current_level)
        if filled_w > 0:
            # Yeşil -> Sarı -> Kırmızı gradyan
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, QColor("#10b981"))  # Yeşil
            gradient.setColorAt(0.7, QColor("#f59e0b"))  # Kehribar sarısı
            gradient.setColorAt(1.0, QColor("#ef4444"))  # Kırmızı

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, filled_w, h, radius, radius)

        # Tepe noktası çizgisi (Peak indicator)
        if self._peak_level > 0.05:
            peak_x = int(w * self._peak_level)
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(peak_x, 1, peak_x, h - 2)

        painter.end()
