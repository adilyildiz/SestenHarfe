"""
SestenHarfe - Optimize Edilmiş Yapılandırma
Sadece Wav2Vec2 + Greedy CTC (Minimum Donanım Gereksinimleri)
"""
import os
from pathlib import Path

# Proje Kök Dizini
BASE_DIR = Path(__file__).resolve().parent

# --- Ses Yakalama Parametreleri ---
SAMPLE_RATE = 16000          # 16kHz standart mono
CHANNELS = 1                 # Mono
CHUNK_DURATION_MS = 30       # 30 ms
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)  # 480 örnek

# --- VAD ve Segmentasyon Eşikleri ---
VAD_AGGRESSIVENESS = 2       # WebRTC VAD hassasiyeti (0: toleranslı - 3: katı)
MIN_SPEECH_DURATION_MS = 180 # 180ms altındaki tıklamaları yoksay
SILENCE_TRIGGER_MS = 550     # 550ms duraklama olduğunda segmenti kesinleştir
MAX_SPEECH_DURATION_MS = 12000 # 12 saniyede bir zorunlu bölme
ENERGY_THRESHOLD = 0.01      # Seviye göstergesi ve yedek VAD eşiği

# --- Canlı Akış (Streaming / Sıfır Gecikme) ---
STREAMING_ENABLED = True
STREAMING_PARTIAL_INTERVAL_MS = 140 # Konuşurken her 140ms'de bir ekranda anlık harfler belirir

# --- Wav2Vec2 Model ve Donanım Optimizasyonları ---
LOCAL_MODEL_DIR = BASE_DIR / "models" / "wav2vec2-turkish"
WAV2VEC2_MODEL_PATH = str(LOCAL_MODEL_DIR) if LOCAL_MODEL_DIR.exists() else "mpoyraz/wav2vec2-xls-r-300m-cv7-turkish"

# Donanım Optimizasyonu:
# GPU varsa: FP16 (Yarı Hassasiyet) -> VRAM tüketimi 1.2 GB'dan ~600 MB'a düşer.
# CPU modu: INT8 Dinamik Kuantizasyon -> RAM tüketimi ~350 MB'a düşer, AVX2 ile 2x hızlanır.
FORCE_DEVICE = "auto"        # "auto", "cuda", veya "cpu"
USE_FP16_ON_GPU = True       # GPU'da 600 MB VRAM optimizasyonu
USE_INT8_ON_CPU = True       # CPU'da 350 MB RAM optimizasyonu

# --- UI Ayarları ---
APP_TITLE = "SestenHarfe - Birebir Fonetik Transkripsiyon (Wav2Vec2)"
WINDOW_WIDTH = 880
WINDOW_HEIGHT = 680
SHOW_TIMESTAMPS = True
SILENCE_MARKER = "--- [Sessizlik] ---"
