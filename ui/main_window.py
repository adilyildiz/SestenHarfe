"""
SestenHarfe - Ana Uygulama Penceresi (PyQt6)
Optimize Edilmiş Wav2Vec2 Modeli ile Minimum Donanım Gereksinimlerinde Birebir Fonetik Transkripsiyon
"""
import sys
import threading
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QMessageBox, QFileDialog, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

import config
from audio.capture import AudioCapture
from audio.vad import VoiceActivityDetector
from audio.buffer import AudioBuffer
from transcriber.wav2vec2_engine import Wav2Vec2Engine
from utils.exporter import export_to_txt, export_to_srt
from .styles import DARK_THEME_QSS
from .level_meter import AudioLevelMeter
from .controls import ControlsPanel
from .transcript_view import TranscriptView


class ModelLoaderThread(QThread):
    """Wav2Vec2 modelini seçilen donanım optimizasyonlarıyla arka planda yükleyen iş parçacığı."""
    loaded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, engine: Wav2Vec2Engine, target_device: str):
        super().__init__()
        self.engine = engine
        self.target_device = target_device

    def run(self):
        try:
            self.engine.load(self.target_device)
            self.loaded.emit(self.engine.hardware_summary)
        except Exception as e:
            self.failed.emit(str(e))


class AudioWorker(QThread):
    """Mikrofondan ses okuyan, VAD uygulayan ve anlık transkribe eden iş parçacığı."""
    level_updated = pyqtSignal(float)
    partial_produced = pyqtSignal(str)  # Konuşulurken anlık akan metin sinyali
    segment_produced = pyqtSignal(str, bool, float, float)  # Kesinleşen satır: text, is_speech, start_time, duration
    status_changed = pyqtSignal(str)  # 'listening', 'transcribing'

    def __init__(self, capture: AudioCapture, buffer: AudioBuffer, engine: Wav2Vec2Engine):
        super().__init__()
        self.capture = capture
        self.buffer = buffer
        self.engine = engine
        self._is_running = False

    def stop(self):
        self._is_running = False

    def run(self):
        import time
        self._is_running = True
        self.buffer.reset()

        last_partial_time = 0.0
        partial_interval = getattr(config, "STREAMING_PARTIAL_INTERVAL_MS", 140) / 1000.0

        while self._is_running:
            chunk = self.capture.get_chunk(timeout=0.04)
            if chunk is None:
                continue

            # Seviye göstergesi sinyali
            level = VoiceActivityDetector.calculate_energy(chunk)
            self.level_updated.emit(level)

            # Segmentasyon işlemi
            segments = self.buffer.process_chunk(chunk)
            now = time.time()

            # 1. Konuşma devam ederken anlık/senkron canlı transkripsiyon (Sıfır Gecikme)
            if config.STREAMING_ENABLED and self.buffer.is_currently_speaking:
                if now - last_partial_time >= partial_interval:
                    last_partial_time = now
                    partial_audio = self.buffer.get_current_speech_audio()
                    # En az 150ms ses birikmişse çıkarım yap
                    if len(partial_audio) >= int(self.buffer.sample_rate * 0.15):
                        if self.engine and self.engine.is_loaded:
                            try:
                                partial_text = self.engine.transcribe(partial_audio)
                                if partial_text:
                                    self.partial_produced.emit(partial_text)
                            except Exception:
                                pass

            # 2. Tamamlanan kesin segmentler (sessizlik molası veya zorunlu kesim)
            for seg in segments:
                if seg.is_speech:
                    if self.engine and self.engine.is_loaded:
                        self.status_changed.emit("transcribing")
                        try:
                            text = self.engine.transcribe(seg.audio_data)
                            if text:
                                self.segment_produced.emit(text, True, seg.start_time, seg.duration)
                        except Exception as e:
                            print(f"[ASR Hatası] {e}")
                        finally:
                            if self._is_running:
                                self.status_changed.emit("listening")
                else:
                    # Sessizlik aralığı
                    self.segment_produced.emit("", False, seg.start_time, seg.duration)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_TITLE)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setStyleSheet(DARK_THEME_QSS)

        # Temel Nesneler
        self.vad = VoiceActivityDetector()
        self.buffer = AudioBuffer(vad=self.vad)
        self.capture = AudioCapture()

        # Optimize Wav2Vec2 Motoru
        self.engine = Wav2Vec2Engine()

        # İş parçacıkları
        self.audio_worker = None
        self.loader_thread = None

        self._build_ui()
        self._connect_signals()

        # Modeli başlat
        self._load_engine(config.FORCE_DEVICE)

    def _build_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # 1. Üst Başlık ve Durum Çubuğu
        header_card = QFrame(self)
        header_card.setObjectName("card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(12, 10, 12, 10)

        title_col = QVBoxLayout()
        title_label = QLabel(config.APP_TITLE, self)
        title_label.setObjectName("titleLabel")
        title_col.addWidget(title_label)

        sub_label = QLabel("Wav2Vec2 Greedy CTC • Sıfır Düzeltme • Anlık Senkron Akış", self)
        sub_label.setObjectName("subtitleLabel")
        title_col.addWidget(sub_label)
        header_layout.addLayout(title_col, stretch=1)

        # Sağ Taraf: Seviye Göstergesi ve Durum Rozeti
        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignmentFlag.AlignRight)

        status_row = QHBoxLayout()
        status_row.addStretch()
        self.status_badge = QLabel("Boşta", self)
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setProperty("status", "idle")
        status_row.addWidget(self.status_badge)
        right_col.addLayout(status_row)

        level_row = QHBoxLayout()
        level_label = QLabel("Mikrofon:", self)
        level_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        level_row.addWidget(level_label)

        self.level_meter = AudioLevelMeter(self)
        level_row.addWidget(self.level_meter)
        right_col.addLayout(level_row)

        header_layout.addLayout(right_col)
        main_layout.addWidget(header_card)

        # 2. Donanım ve Optimizasyon Kartı
        hw_card = QFrame(self)
        hw_card.setObjectName("card")
        hw_layout = QHBoxLayout(hw_card)
        hw_layout.setContentsMargins(12, 10, 12, 10)

        hw_info_col = QVBoxLayout()
        hw_title = QLabel("Donanım ve Optimizasyon Durumu:", self)
        hw_title.setObjectName("sectionTitle")
        hw_info_col.addWidget(hw_title)

        self.hw_desc_label = QLabel("Yükleniyor...", self)
        self.hw_desc_label.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 12px;")
        hw_info_col.addWidget(self.hw_desc_label)
        hw_layout.addLayout(hw_info_col, stretch=1)

        # Donanım Modu Seçici
        hw_combo_col = QVBoxLayout()
        hw_combo_label = QLabel("Çalışma Modu:", self)
        hw_combo_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        hw_combo_col.addWidget(hw_combo_label)

        self.hw_mode_combo = QComboBox(self)
        self.hw_mode_combo.addItem("Otomatik / GPU (FP16 Optimize ~600 MB)", userData="auto")
        self.hw_mode_combo.addItem("Düşük Güç CPU (INT8 Kuantize ~350 MB)", userData="cpu")
        self.hw_mode_combo.currentIndexChanged.connect(self._on_hw_mode_changed)
        hw_combo_col.addWidget(self.hw_mode_combo)
        hw_layout.addLayout(hw_combo_col)

        main_layout.addWidget(hw_card)

        # 3. Kontrol Paneli Kartı
        controls_card = QFrame(self)
        controls_card.setObjectName("card")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(12, 10, 12, 10)
        self.controls = ControlsPanel(self)
        controls_layout.addWidget(self.controls)
        main_layout.addWidget(controls_card)

        # 4. Transkript Görüntüleme Alanı
        self.transcript_view = TranscriptView(self)
        main_layout.addWidget(self.transcript_view, stretch=1)

    def _connect_signals(self):
        self.controls.start_clicked.connect(self.start_listening)
        self.controls.stop_clicked.connect(self.stop_listening)
        self.controls.clear_clicked.connect(self.transcript_view.clear_all)
        self.controls.export_txt_clicked.connect(self._export_txt)
        self.controls.export_srt_clicked.connect(self._export_srt)
        self.controls.device_changed.connect(self._on_device_changed)
        self.controls.timestamps_toggled.connect(self.transcript_view.set_show_timestamps)

    def _set_status(self, text: str, status_type: str = "idle"):
        self.status_badge.setText(text)
        self.status_badge.setProperty("status", status_type)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def _load_engine(self, target_device: str):
        """Modeli arka planda yükler."""
        self._set_status("Model Yükleniyor...", "transcribing")
        self.controls.start_btn.setEnabled(False)
        self.hw_mode_combo.setEnabled(False)

        self.loader_thread = ModelLoaderThread(self.engine, target_device)
        self.loader_thread.loaded.connect(self._on_engine_loaded)
        self.loader_thread.failed.connect(self._on_engine_load_failed)
        self.loader_thread.start()

    def _on_engine_loaded(self, hw_summary: str):
        self._set_status("Hazır", "idle")
        self.hw_desc_label.setText(f"Aktif: {hw_summary}")
        self.hw_mode_combo.setEnabled(True)
        if not (self.audio_worker and self.audio_worker.isRunning()):
            self.controls.start_btn.setEnabled(True)

    def _on_engine_load_failed(self, error_msg: str):
        self._set_status("Yükleme Hatası", "idle")
        self.hw_desc_label.setText("Model yüklenemedi!")
        self.controls.start_btn.setEnabled(False)
        self.hw_mode_combo.setEnabled(True)
        QMessageBox.critical(
            self,
            "Model Yükleme Hatası",
            f"Wav2Vec2 modeli yüklenirken hata oluştu:\n\n{error_msg}"
        )

    def _on_hw_mode_changed(self, index: int):
        target_device = self.hw_mode_combo.itemData(index)
        was_listening = self.audio_worker is not None and self.audio_worker.isRunning()
        if was_listening:
            self.stop_listening()

        self.engine.unload()
        self._load_engine(target_device)

    def _on_device_changed(self, device_id: int):
        self.capture.device_index = device_id if device_id >= 0 else None

    def start_listening(self):
        if not self.engine.is_loaded:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce modelin yüklenmesini bekleyin.")
            return

        try:
            self.capture.start()
        except Exception as e:
            QMessageBox.critical(self, "Mikrofon Hatası", f"Mikrofon başlatılamadı:\n{e}")
            return

        self.controls.set_listening_state(True)
        self._set_status("Dinleniyor...", "listening")

        # İş parçacığını başlat
        self.audio_worker = AudioWorker(
            capture=self.capture,
            buffer=self.buffer,
            engine=self.engine
        )
        self.audio_worker.level_updated.connect(self.level_meter.set_level)
        self.audio_worker.partial_produced.connect(self.transcript_view.update_partial)
        self.audio_worker.segment_produced.connect(self.transcript_view.add_entry)
        self.audio_worker.status_changed.connect(self._on_worker_status_changed)
        self.audio_worker.start()

    def _on_worker_status_changed(self, status: str):
        if status == "transcribing":
            self._set_status("Çözümleniyor...", "transcribing")
        elif status == "listening":
            self._set_status("Dinleniyor...", "listening")

    def stop_listening(self):
        self.controls.set_listening_state(False)
        self._set_status("Durduruldu", "idle")
        self.level_meter.set_level(0.0)
        self.transcript_view.update_partial("")

        if self.audio_worker:
            self.audio_worker.stop()
            self.audio_worker.wait(1000)
            self.audio_worker = None

        self.capture.stop()

    def _export_txt(self):
        entries = self.transcript_view.get_entries()
        if not entries:
            QMessageBox.information(self, "Bilgi", "Dışa aktarılacak transkript bulunmuyor.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Transkripti TXT Olarak Kaydet", "transkript.txt", "Metin Dosyaları (*.txt)"
        )
        if filepath:
            try:
                export_to_txt(entries, filepath, include_timestamps=self.controls.ts_checkbox.isChecked())
                QMessageBox.information(self, "Başarılı", f"Transkript kaydedildi:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{e}")

    def _export_srt(self):
        entries = self.transcript_view.get_entries()
        if not entries:
            QMessageBox.information(self, "Bilgi", "Dışa aktarılacak transkript bulunmuyor.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Altyazı Olarak Kaydet (SRT)", "altyazi.srt", "SRT Altyazı (*.srt)"
        )
        if filepath:
            try:
                export_to_srt(entries, filepath)
                QMessageBox.information(self, "Başarılı", f"Altyazı dosyası kaydedildi:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{e}")

    def closeEvent(self, event):
        """Pencere kapatıldığında arka plan işlerini temizle."""
        self.stop_listening()
        if self.engine and self.engine.is_loaded:
            self.engine.unload()
        event.accept()
