# 🖨️ 3D-Druck Preisrechner (Streamlit)

Moderner Preisrechner für 3D-Drucke – optimiert für **Bambu Lab P1S** und Standard-PLA.  
Berechnet Material, Energie, Maschinenverschleiß, Arbeit, Risiko-Puffer, Marge und Freundschaftsrabatt.
Läuft lokal als hübsche **Streamlit-Web-App**.

## ✨ Features
- Dark UI mit Karten, Slidern & kleinen Effekten
- Purge/Abfall in g (z. B. AMS-Farbwechsel)
- Kernmetriken (Preis, kWh, Zeit, Filament)
- Detailtabelle + **Export** als JSON/CSV
- Presets: **PLA**, **PETG**, **ABS/ASA**
- Mindestbetrag, Verpackung/Versand, Freundschaftsrabatt

## 🚀 Quickstart
### 1) Umgebung
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
