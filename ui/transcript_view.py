"""
SestenHarfe - Transkript Görünümü Bileşeni
Konuşma ve sessizlik kayıtlarını zengin metin (HTML) olarak biçimlendirip sunar.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt
import utils.text_merger as tm


class TranscriptView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []  # [{'text': str, 'start': float, 'duration': float, 'is_speech': bool}]
        self.show_timestamps = True
        self.partial_text = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Üst Çubuk: Başlık ve Kopyala Butonu
        top_bar = QHBoxLayout()
        title = QLabel("Canlı Transkript:", self)
        title.setObjectName("sectionTitle")
        top_bar.addWidget(title)

        top_bar.addStretch()

        self.copy_btn = QPushButton("📋 Metni Kopyala", self)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        top_bar.addWidget(self.copy_btn)

        layout.addLayout(top_bar)

        # Transkript Metin Kutusu
        self.text_box = QTextEdit(self)
        self.text_box.setObjectName("transcriptBox")
        self.text_box.setReadOnly(True)
        self.text_box.setPlaceholderText("Mikrofonu başlatıp konuştuğunuzda sözcükler anlık olarak burada belirecektir...")
        layout.addWidget(self.text_box)

    def set_show_timestamps(self, show: bool):
        self.show_timestamps = show
        self._rebuild_display()

    def update_partial(self, text: str):
        """Konuşma esnasında anlık harfleri/kelimeleri gecikmesiz gösterir."""
        clean = text.strip()
        if clean == self.partial_text:
            return
        self.partial_text = clean
        self._rebuild_display()

    def add_entry(self, text: str, is_speech: bool, start_time: float, duration: float):
        """Bir konuşma veya sessizlik segmenti kesinleştiğinde ekler."""
        self.partial_text = ""
        entry = {
            "text": text,
            "is_speech": is_speech,
            "start": start_time,
            "duration": duration
        }
        self.entries.append(entry)
        self._rebuild_display()

    def _rebuild_display(self):
        """Tüm kesinleşen kayıtları ve varsa canlı akıştaki anlık metni ekrana basar."""
        sb = self.text_box.verticalScrollBar()
        was_at_bottom = sb.value() >= (sb.maximum() - 30)

        html_parts = []
        for entry in self.entries:
            text = entry.get("text", "").strip()
            is_speech = entry.get("is_speech", True)
            start_time = entry.get("start", 0.0)
            duration = entry.get("duration", 0.0)

            ts_str = ""
            if self.show_timestamps:
                ts_str = f"<span style='color: #6366f1; font-weight: 600;'>{tm.format_timestamp(start_time)}</span> "

            if is_speech:
                if text:
                    html_parts.append(
                        f"<div style='margin-bottom: 6px;'>{ts_str}<span style='color: #f8fafc; font-size: 14px;'>{text}</span></div>"
                    )
            else:
                html_parts.append(
                    f"<div style='margin-bottom: 6px; color: #64748b; font-style: italic;'>{ts_str}--- [Sessizlik ({duration:.1f} sn)] ---</div>"
                )

        # Canlı anlık satır (konuşulurken gerçek zamanlı akan kısım)
        if self.partial_text:
            html_parts.append(
                f"<div style='margin-bottom: 6px; color: #38bdf8;'>"
                f"<span style='color: #a855f7; font-weight: 700;'>[Anlık]</span> "
                f"<span style='color: #38bdf8; font-weight: 600; font-size: 14px;'>{self.partial_text}</span>"
                f"<span style='color: #06b6d4; font-weight: 900;'> ▌</span>"
                f"</div>"
            )

        self.text_box.setHtml("".join(html_parts))
        if was_at_bottom:
            self.text_box.moveCursor(QTextCursor.MoveOperation.End)

    def clear_all(self):
        self.entries.clear()
        self.text_box.clear()

    def copy_to_clipboard(self):
        plain_text = self.text_box.toPlainText()
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(plain_text)

    def get_entries(self) -> list[dict]:
        return self.entries
