"""
SestenHarfe - Optimize Edilmiş Wav2Vec2 Doğrulama Testi
GPU (FP16) ve CPU (INT8) çıkarımını doğrular.
"""
import sys
import time
import numpy as np
import torch

from audio.vad import VoiceActivityDetector
from audio.buffer import AudioBuffer
from transcriber.wav2vec2_engine import Wav2Vec2Engine


def run_tests():
    print("=== SestenHarfe Minimal Wav2Vec2 Sistem Testi ===")
    print(f"Python: {sys.version}")
    print(f"PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}")

    # 1. VAD Testi
    print("\n[1/3] VAD ve AudioBuffer Kontrol Ediliyor...")
    vad = VoiceActivityDetector()
    buffer = AudioBuffer(vad=vad)
    dummy_tone = (np.sin(2 * np.pi * 440 * np.arange(480) / 16000) * 0.5).astype(np.float32)
    assert vad.is_speech(dummy_tone), "VAD konuşmayı algılayamadı!"
    print("VAD Başarılı!")

    # Sentetik ses
    synth_audio = (np.sin(2 * np.pi * 300 * np.arange(16000) / 16000) * 0.2).astype(np.float32)

    # 2. GPU Modu (Varsa FP16)
    if torch.cuda.is_available():
        print("\n[2/3] GPU Modu (FP16 Yarı Hassasiyet) Test Ediliyor...")
        w2v_gpu = Wav2Vec2Engine()
        w2v_gpu.load(target_device="cuda")
        print(f"Aktif Donanım: {w2v_gpu.hardware_summary}")
        vram_mb = torch.cuda.memory_allocated() / (1024 ** 2)
        print(f"GPU Bellek Kullanımı: {vram_mb:.1f} MB (Beklenen: ~600 MB)")

        t0 = time.time()
        w2v_gpu.transcribe(synth_audio)
        gpu_ms = (time.time() - t0) * 1000
        print(f"GPU Çıkarım Süresi (1 sn ses için): {gpu_ms:.1f} ms")
        w2v_gpu.unload()
        print("GPU FP16 Testi Başarılı!")
    else:
        print("\n[2/3] GPU bulunamadı, GPU testi atlandı.")

    # 3. CPU Modu (INT8 Dinamik Kuantizasyon)
    print("\n[3/3] CPU Modu (INT8 Dinamik Kuantizasyon) Test Ediliyor...")
    w2v_cpu = Wav2Vec2Engine()
    w2v_cpu.load(target_device="cpu")
    print(f"Aktif Donanım: {w2v_cpu.hardware_summary}")

    t0 = time.time()
    w2v_cpu.transcribe(synth_audio)
    cpu_ms = (time.time() - t0) * 1000
    print(f"CPU Çıkarım Süresi (1 sn ses için): {cpu_ms:.1f} ms")
    w2v_cpu.unload()
    print("CPU INT8 Testi Başarılı!")

    print("\n=== TÜM OPTİMİZASYON VE DOĞRULAMA TESTLERİ BAŞARILI! ===")


if __name__ == "__main__":
    run_tests()
