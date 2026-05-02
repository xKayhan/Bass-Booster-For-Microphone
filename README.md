# 🎵 AK Company Bass Booster

<div align="center">

![AK Company Bass Booster](https://img.shields.io/badge/AK%20Company-Bass%20Booster-ff8800?style=for-the-badge&logo=audiomack&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**VST plugin tarzı gerçek zamanlı mikrofon bass booster.**  
Discord, oyun içi sesleşme ve her türlü sesli iletişim için tasarlandı.

</div>

---

## 📸 Görünüm

> Altın/koyu VST plugin estetiği — döner çark ile +600 dB'e kadar bass kontrolü.

---

## ✨ Özellikler

- 🎚️ **Döner Çark (Knob)** — Sürükle veya fare tekerleği ile 0'dan +600 dB'e kadar bass kontrolü
- 🔊 **Gerçek Low-Shelf EQ** — Sadece bass frekanslarını hedef alır, sesi bozmaz
- 💥 **Hard Clip Distortion** — Clownfish/Skype tarzı karakteristik patlama efekti
- 📊 **Gerçek Zamanlı VU Meter** — Anlık ses seviyesi göstergesi
- 🎙️ **Cihaz Seçimi** — Mikrofon girişi ve çıkış cihazını ayrı ayrı seç
- 🔌 **VB-Cable Desteği** — Otomatik algılar, Discord ile kusursuz entegrasyon
- 🪟 **Hafif & Bağımsız** — Tek EXE, kurulum gerektirmez

---

## 🚀 Kurulum

### Yöntem 1 — Hazır EXE (Önerilen)

1. [Releases](../../releases) sayfasından `AK_Bass_Booster.exe` dosyasını indir
2. Çalıştır — kurulum gerekmez ✅

### Yöntem 2 — Python ile Çalıştır

```bash
# Gereksinimleri kur
pip install pyaudio numpy scipy

# Çalıştır
python ak_bass_booster.py
```

### Yöntem 3 — Kendin Derle

```bash
# Repoyu klonla
git clone https://github.com/xKayhan/ak-bass-booster.git
cd ak-bass-booster

# build_exe.bat çalıştır (Windows)
build_exe.bat
```

> `dist/AK_Bass_Booster.exe` oluşacak.

---

## 🎮 Discord ile Kullanım

Discord'da karşı tarafa bass efektli sesin gitmesi için **VB-Cable** gerekli (ücretsiz).

### Adım 1 — VB-Cable Kur
[vb-audio.com/Cable](https://vb-audio.com/Cable/) adresinden indir ve kur.

### Adım 2 — AK Bass Booster Ayarla
| Alan | Seçim |
|------|-------|
| **Mikrofon** | Kendi gerçek mikrofonun |
| **Çıkış** | CABLE Input (VB-Audio) |

### Adım 3 — Discord Ayarla
| Alan | Seçim |
|------|-------|
| **Giriş Cihazı** | CABLE Output (VB-Audio) |

### Sinyal Akışı
```
Mikrofon → AK Bass Booster → CABLE Input → CABLE Output → Discord ✅
```

> Program doğru ayarlandığında alt kısımda **yeşil onay mesajı** görünür.

---

## 🎛️ Kullanım

| Eylem | Nasıl |
|-------|-------|
| Bass artır | Knob'u yukarı sürükle |
| Bass azalt | Knob'u aşağı sürükle |
| İnce ayar | Fare tekerleği |
| Sıfırla | Knob'u tamamen aşağı çek |

### Önerilen Discord Ayarları
| Parametre | Değer |
|-----------|-------|
| Knob pozisyonu | %30–%50 |
| Efektif dB | +180 – +300 dB |

> Çok yüksek değerler Discord'un AGC'sini tetikleyebilir.

---

## ⚙️ Gereksinimler

| Gereksinim | Versiyon |
|-----------|---------|
| Python | 3.8+ |
| pyaudio | 0.2.11+ |
| numpy | 1.20+ |
| scipy | 1.7+ |
| İşletim Sistemi | Windows 10/11 |

---

## 🔧 Teknik Detaylar

Program ses işlemeyi şu aşamalarda yapar:

1. **High-Pass Filter** — 30 Hz altındaki DC offset ve rumble temizlenir
2. **Low-Shelf EQ** — Seçilen frekansın altı (varsayılan 150 Hz) güçlendirilir
3. **Distortion** — Hard clip ile karakteristik bass patlama efekti oluşturulur
4. **Harmonik Exciter** — Üst harmonikler eklenerek ses "dolgunlaşır"
5. **Final Clip** — 16-bit sınırına sabitlenir

```
Örnekleme Hızı : 44100 Hz
Buffer Boyutu  : 512 sample (~11ms gecikme)
Format         : 16-bit PCM Mono
```

---

## 📦 Proje Yapısı

```
ak-bass-booster/
├── ak_bass_booster.py   # Ana uygulama
├── build_exe.bat        # Windows EXE derleyici
├── ak_icon.ico          # Uygulama ikonu
└── README.md
```

---

## 🤝 Katkı

Pull request ve issue'lar her zaman açık. Öneri veya hata bildirimi için:

- 🐛 [Issue Aç](../../issues)
- 💬 [WhatsApp](https://wa.me/905412664569)
- 🌐 [xkayhan.github.io](https://xkayhan.github.io)

---

## 📄 Lisans

MIT License — dilediğin gibi kullan, değiştir, dağıt.

---

<div align="center">

Made with 🔊 by **[Ağahan Kayhan](https://xkayhan.github.io)**

</div>
