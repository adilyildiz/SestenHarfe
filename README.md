# SestenHarfe: Birebir Fonetik Transkripsiyon (Wav2Vec2)

SestenHarfe, kullanıcının telaffuz ve söyleyiş hatalarını otomatik olarak düzeltmeyen, mikrofondan duyduğu akustik sesleri birebir harfe dönüştüren hafif ve optimize edilmiş bir masaüstü uygulamasıdır.

Örneğin:
- *"Akıl"* yerine *"akil"* dediğinizde dil modeli düzeltmesi yapmaz, inatla **"akil"** yazar.
- *"Dünya"* yerine *"donya"* ya da *"tonya"* dediğinizde kelime anlamını tahmin etmeye çalışmaz, duyduğu harfleri birebir korur.
- Sessiz geçen süreleri kaçırmaz, kesintisiz dinler ve canlı ses seviyesini takip eder.

---

## ⚡ Minimum Donanım Optimizasyonları

Uygulama, sadece **Wav2Vec2 + Greedy CTC** mimarisine odaklanacak şekilde sadeleştirilmiş ve minimum donanımlarda bile sıfır gecikmeyle çalışacak 2 özel optimizasyonla donatılmıştır:

1. **GPU Modu (FP16 Yarı Hassasiyet):**
   - VRAM tüketimi 1.2 GB'dan **~600 MB'a** düşürüldü.
   - 1 GB veya 2 GB VRAM'e sahip giriş seviyesi ekran kartlarında bile sıfır gecikmeyle (~30-40 ms) çalışır.
2. **CPU Modu (INT8 Dinamik Kuantizasyon):**
   - Ekran kartsız sıradan bilgisayarlar için RAM tüketimi **~350 MB'a** indirildi.
   - AVX2 işlemci yönergeleriyle çıkarım hızı 2 katına çıkarıldı.

Arayüzdeki **"Çalışma Modu"** menüsünden GPU veya Düşük Güç CPU modları arasında tek tıkla geçiş yapabilirsiniz.

---

## 🚀 Başlatma

```powershell
cd e:\PythonProjects\SestenHarfe
.\venv\Scripts\python.exe main.py
```

### Özellikler
- **Gerçek Zamanlı Canlı Akış (Streaming):** Konuştuğunuz anda harfler ekranda belirir (`[Anlık] ... ▌`).
- **Canlı VU Meter:** Donanım ivmeli, yumuşak geçişli mikrofon seviye çubuğu.
- **Dışa Aktarma:** Tek tıkla `.txt` veya zaman damgalı `.srt` altyazı olarak kaydetme.
