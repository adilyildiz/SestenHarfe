"""
SestenHarfe - Modern Koyu Tema Stilleri (QSS)
"""

DARK_THEME_QSS = """
/* Genel Pencere */
QMainWindow, QWidget {
    background-color: #121318;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Üst Panel & Kartlar */
QFrame#card {
    background-color: #1a1b26;
    border: 1px solid #2a2b3d;
    border-radius: 10px;
    padding: 12px;
}

/* Başlıklar */
QLabel#titleLabel {
    font-size: 18px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Butonlar */
QPushButton {
    background-color: #252837;
    color: #f1f5f9;
    border: 1px solid #3b3f54;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #32374a;
    border-color: #6366f1;
}

QPushButton:pressed {
    background-color: #1e202e;
}

QPushButton:disabled {
    background-color: #181922;
    color: #475569;
    border-color: #242634;
}

/* Birincil Başlat/Durdur Butonları */
QPushButton#startBtn {
    background-color: #059669;
    border-color: #10b981;
    color: #ffffff;
    font-size: 14px;
}
QPushButton#startBtn:hover {
    background-color: #10b981;
}

QPushButton#stopBtn {
    background-color: #dc2626;
    border-color: #ef4444;
    color: #ffffff;
    font-size: 14px;
}
QPushButton#stopBtn:hover {
    background-color: #ef4444;
}

/* Açılır Kutular (QComboBox) */
QComboBox {
    background-color: #1e202e;
    color: #f8fafc;
    border: 1px solid #373b52;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
}

QComboBox QAbstractItemView {
    background-color: #1e202e;
    color: #e2e8f0;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
    border: 1px solid #373b52;
    border-radius: 6px;
    padding: 4px;
}

/* Transkript Metin Kutusu */
QTextEdit#transcriptBox {
    background-color: #15161e;
    color: #e2e8f0;
    border: 1px solid #282a3a;
    border-radius: 10px;
    font-family: 'Consolas', 'Cascadia Code', 'Fira Code', monospace;
    font-size: 14px;
    line-height: 1.6;
    padding: 14px;
}

QTextEdit#transcriptBox:focus {
    border: 1px solid #6366f1;
}

/* Kaydırma Çubukları (QScrollBar) */
QScrollBar:vertical {
    border: none;
    background: #15161e;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2e3247;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #4f46e5;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Durum Rozeti (Badge) */
QLabel#statusBadge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}

/* Durum Renkleri */
QLabel#statusBadge[status="idle"] {
    background-color: #272738;
    color: #94a3b8;
    border: 1px solid #3f3f5a;
}

QLabel#statusBadge[status="listening"] {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
}

QLabel#statusBadge[status="transcribing"] {
    background-color: #312e81;
    color: #a5b4fc;
    border: 1px solid #6366f1;
}
"""
