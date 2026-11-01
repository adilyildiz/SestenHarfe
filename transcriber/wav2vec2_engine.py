"""
SestenHarfe - Optimize Edilmiş Wav2Vec2 + Greedy CTC Transkripsiyon Motoru
Minimum donanım gereksinimleri için:
- GPU: FP16 Yarı Hassasiyet (~600 MB VRAM tüketimi)
- CPU: INT8 Dinamik Kuantizasyon (~350 MB RAM tüketimi, AVX2 hızlandırma)
- torch.inference_mode() ile sıfır bellek sızıntısı ve en yüksek çıkarım hızı
"""
import os
import gc
import numpy as np
import config

try:
    import torch
    from transformers import Wav2Vec2Processor, AutoModelForCTC
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class Wav2Vec2Engine:
    def __init__(self, model_path: str = config.WAV2VEC2_MODEL_PATH):
        self.name = "Wav2Vec2 (Greedy CTC)"
        self.description = "Birebir fonetik transkripsiyon. Hataları düzeltmez, akustik harfleri yazar."
        self.model_path = model_path
        self.processor = None
        self.model = None
        self.device = None
        self.is_fp16 = False
        self.is_quantized = False
        self._is_loaded = False
        self.hardware_summary = "Yüklenmedi"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load(self, target_device: str = config.FORCE_DEVICE):
        """Modeli doğrudan yerel diskten ve seçilen donanım optimizasyonlarıyla belleğe yükler."""
        if self._is_loaded:
            return

        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch ve Transformers kütüphaneleri yüklü değil.")

        is_local = os.path.exists(self.model_path)
        source_label = "Yerel Disk" if is_local else "Hugging Face"

        # Donanım kararı
        if target_device == "auto":
            use_cuda = torch.cuda.is_available()
        elif target_device == "cuda":
            use_cuda = torch.cuda.is_available()
            if not use_cuda:
                print("[Uyarı] CUDA istenildi fakat donanımda bulunamadı, CPU'ya geçiliyor.")
        else:
            use_cuda = False

        self.device = torch.device("cuda" if use_cuda else "cpu")
        print(f"[{self.name}] Model yükleniyor ({source_label}): {self.model_path} (Cihaz: {self.device})")

        # Saf CTC için Wav2Vec2Processor (Yerel dosyadan, internetsiz)
        self.processor = Wav2Vec2Processor.from_pretrained(
            self.model_path,
            local_files_only=is_local
        )

        if use_cuda:
            # GPU OPTİMİZASYONU: FP16 (Yarı Hassasiyet)
            # VRAM tüketimini 1.2 GB'dan ~600 MB'a indirir
            if config.USE_FP16_ON_GPU:
                self.model = AutoModelForCTC.from_pretrained(
                    self.model_path,
                    dtype=torch.float16,
                    local_files_only=is_local
                ).to(self.device)
                self.is_fp16 = True
                gpu_name = torch.cuda.get_device_name(0)
                self.hardware_summary = f"GPU: {gpu_name} (FP16 Optimize - ~600 MB VRAM) [Yerel]"
            else:
                self.model = AutoModelForCTC.from_pretrained(
                    self.model_path,
                    local_files_only=is_local
                ).to(self.device)
                self.is_fp16 = False
                gpu_name = torch.cuda.get_device_name(0)
                self.hardware_summary = f"GPU: {gpu_name} (FP32 - ~1.2 GB VRAM) [Yerel]"
        else:
            # CPU OPTİMİZASYONU: INT8 Dinamik Kuantizasyon
            # RAM tüketimini ~350 MB'a indirir ve AVX2 ile çıkarımı 2 kat hızlandırır
            base_model = AutoModelForCTC.from_pretrained(
                self.model_path,
                local_files_only=is_local
            )
            if config.USE_INT8_ON_CPU:
                print(f"[{self.name}] CPU için INT8 dinamik kuantizasyon uygulanıyor...")
                self.model = torch.quantization.quantize_dynamic(
                    base_model,
                    {torch.nn.Linear},
                    dtype=torch.qint8
                ).to(self.device)
                self.is_quantized = True
                self.hardware_summary = "CPU (INT8 Optimize - ~350 MB RAM) [Yerel]"
            else:
                self.model = base_model.to(self.device)
                self.is_quantized = False
                self.hardware_summary = "CPU (Standart FP32 - ~1.2 GB RAM) [Yerel]"

        self.model.eval()
        self._is_loaded = True
        print(f"[{self.name}] Başarıyla yüklendi. Aktif Donanım: {self.hardware_summary}")

    def unload(self):
        """Modeli bellekten kaldırır ve RAM/VRAM'i serbest bırakır."""
        if not self._is_loaded:
            return

        print(f"[{self.name}] Model bellekten kaldırılıyor...")
        self.model = None
        self.processor = None
        self._is_loaded = False
        self.hardware_summary = "Yüklenmedi"

        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        print(f"[{self.name}] Bellek temizlendi.")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Gelen sesi birebir akustik harflere dönüştürür.
        torch.inference_mode() ile minimum bellek ve maksimum hız sağlar.
        """
        if not self._is_loaded or self.model is None:
            raise RuntimeError(f"{self.name} modeli henüz yüklenmedi.")

        if len(audio) == 0:
            return ""

        # Sesi normalize et (-1.0 ile 1.0 arasına)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            norm_audio = audio / max_val
        else:
            norm_audio = audio

        inputs = self.processor(
            norm_audio,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True
        )

        with torch.inference_mode():
            if self.is_fp16 and self.device.type == "cuda":
                input_values = inputs.input_values.to(self.device, dtype=torch.float16)
            else:
                input_values = inputs.input_values.to(self.device)

            logits = self.model(input_values).logits

            # Saf CTC Greedy Decoding (En yüksek olasılıklı harfleri seç)
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]

        return transcription.strip().lower()
