"""
SestenHarfe - Kontrol Paneli Bileşeni
Başlat/Durdur, Mikrofon Aygıtı Seçimi, Temizle, Dışa Aktar ve Seçenekler
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QLabel, QCheckBox, QFrame
)
from PyQt6.QtCore import pyqtSignal
from audio.capture import AudioCapture


class ControlsPanel(QWidget):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    export_txt_clicked = pyqtSignal()
    export_srt_clicked = pyqtSignal()
    device_changed = pyqtSignal(int)
    timestamps_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Satır: Mikrofon Seçici ve Zaman Damgası
        top_row = QHBoxLayout()
        mic_label = QLabel("Mikrofon:", self)
        mic_label.setObjectName("sectionTitle")
        top_row.addWidget(mic_label)

        self.device_combo = QComboBox(self)
        self._populate_audio_devices()
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        top_row.addWidget(self.device_combo, stretch=1)

        self.ts_checkbox = QCheckBox("Zaman Damgaları", self)
        self.ts_checkbox.setChecked(True)
        self.ts_checkbox.toggled.connect(self.timestamps_toggled.emit)
        top_row.addWidget(self.ts_checkbox)
        layout.addLayout(top_row)

        # 2. Satır: Eylem Butonları
        btn_row = QHBoxLayout()

        self.start_btn = QPushButton("▶ Dinlemeyi Başlat", self)
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_clicked.emit)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Durdur", self)
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        btn_row.addWidget(self.stop_btn)

        btn_row.addSpacing(10)

        self.clear_btn = QPushButton("🗑 Temizle", self)
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        btn_row.addWidget(self.clear_btn)

        self.export_txt_btn = QPushButton("💾 TXT İndir", self)
        self.export_txt_btn.clicked.connect(self.export_txt_clicked.emit)
        btn_row.addWidget(self.export_txt_btn)

        self.export_srt_btn = QPushButton("🎬 SRT Altyazı", self)
        self.export_srt_btn.clicked.connect(self.export_srt_clicked.emit)
        btn_row.addWidget(self.export_srt_btn)

        layout.addLayout(btn_row)

    def _populate_audio_devices(self):
        self.device_combo.clear()
        try:
            devices = AudioCapture.list_input_devices()
            default_index = 0
            for idx, dev in enumerate(devices):
                title = dev["name"]
                if dev["default"]:
                    title += " (Varsayılan)"
                    default_index = idx
                self.device_combo.addItem(title, userData=dev["id"])
            if devices:
                self.device_combo.setCurrentIndex(default_index)
        except Exception:
            self.device_combo.addItem("Varsayılan Mikrofon", userData=None)

    def _on_device_changed(self, index: int):
        device_id = self.device_combo.itemData(index)
        self.device_changed.emit(device_id if device_id is not None else -1)

    def set_listening_state(self, is_listening: bool):
        """Dinleme durumuna göre butonları etkinleştirir/devre dışı bırakır."""
        self.start_btn.setEnabled(not is_listening)
        self.stop_btn.setEnabled(is_listening)
        self.device_combo.setEnabled(not is_listening)
