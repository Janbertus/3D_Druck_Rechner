#!/usr/bin/env python3
"""
Streamlit-App: 3D‑Druck Preisrechner (Bambu Lab P1S)
Stylish UI mit Slidern, Presets, Export und kleinen Effekten.

Starten:
  streamlit run preisrechner.py
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import time
import math
import pandas as pd
import streamlit as st

# =====================
# Kern-Modelle & Logik
# =====================
@dataclass
class PricingInputs:
    filament_used_g: float
    print_time_h: float

    filament_eur_per_kg: float = 22.0
    electricity_eur_per_kwh: float = 0.25
    avg_power_w: float = 80.0

    depreciation_eur_per_h: float = 0.50
    consumables_ratio: float = 0.05

    labor_hours: float = 1.0
    labor_rate_eur_per_h: float = 30.0

    risk_ratio: float = 0.10
    markup_ratio: float = 0.0
    friend_discount_ratio: float = 0.20

    packaging_shipping_eur: float = 0.0
    min_fee_eur: float = 10.0

    purge_waste_g: float = 0.0   # z.B. AMS Farbwechsel-Abfall


def round_money(x: float) -> float:
    return round(x + 1e-9, 2)


def compute_cost(inputs: PricingInputs):
    grams_total = inputs.filament_used_g + inputs.purge_waste_g

    material_eur = (grams_total / 1000.0) * inputs.filament_eur_per_kg
    kwh = (inputs.avg_power_w * inputs.print_time_h) / 1000.0
    energy_eur = kwh * inputs.electricity_eur_per_kwh
    machine_eur = inputs.print_time_h * inputs.depreciation_eur_per_h
    labor_eur = inputs.labor_hours * inputs.labor_rate_eur_per_h

    consumables_eur = (material_eur + energy_eur) * inputs.consumables_ratio
    risk_buffer_eur = (material_eur + energy_eur + machine_eur) * inputs.risk_ratio

    subtotal_before_markup = material_eur + energy_eur + machine_eur + labor_eur + consumables_eur + risk_buffer_eur
    markup_eur = subtotal_before_markup * inputs.markup_ratio
    pre_discount_total = subtotal_before_markup + markup_eur
    friend_discount_eur = pre_discount_total * inputs.friend_discount_ratio
    total = pre_discount_total - friend_discount_eur + inputs.packaging_shipping_eur
    final_total_eur = max(total, inputs.min_fee_eur)

    breakdown = {
        "Material": round_money(material_eur),
        "Energie": round_money(energy_eur),
        "Maschine/Verschleiß": round_money(machine_eur),
        "Arbeit": round_money(labor_eur),
        "Verbrauchsmaterial-Puffer": round_money(consumables_eur),
        "Risiko-Puffer": round_money(risk_buffer_eur),
        "Zwischensumme": round_money(subtotal_before_markup),
        "Marge/Aufschlag": round_money(markup_eur),
        "Summe vor Rabatt": round_money(pre_discount_total),
        "Freundschaftsrabatt": round_money(friend_discount_eur),
        "Verpackung/Versand": round_money(inputs.packaging_shipping_eur),
        "Empfohlener Preis": round_money(final_total_eur),
    }

    meta = {
        "kwh": round(kwh, 3),
        "filament_total_g": round(grams_total, 1)
    }
    return breakdown, meta


# =====================
# UI-Helfer
# =====================
PRIMARY = "#12a87a"  # sanftes Grün
ACCENT = "#6b4df6"   # violetter Akzent
BG = "#0b0f14"       # dunkles Blau-Schwarz
CARD = "#0f1620"     # Kartenhintergrund
MUTED = "#a6b0c3"

CUSTOM_CSS = f"""
<style>
  .stApp {{ background: linear-gradient(180deg,{BG} 0%, #0c1117 100%); }}
  h1, h2, h3, h4, h5, h6, .stMarkdown p {{ color: #e8eef8; }}
  .metric-card {{
    background: {CARD};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px; padding: 18px; box-shadow: 0 6px 30px rgba(0,0,0,0.35);
  }}
  .pill {{
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:rgba(255,255,255,0.08); color:{MUTED}; font-size:12px; margin-right:6px;
  }}
  .price {{ font-size:38px; font-weight:800; color:white; }}
  .sub {{ color:{MUTED}; font-size:13px; }}
  .accent {{ color:{PRIMARY}; }}
  .footer-note {{ color:{MUTED}; font-size:12px; margin-top:8px; }}
</style>
"""


def metric_card(title: str, value: str, subtitle: str = ""):
    st.markdown("<div class='metric-card'>" +
                f"<div class='sub'>{title}</div>" +
                f"<div class='price'>{value}</div>" +
                (f"<div class='footer-note'>{subtitle}</div>" if subtitle else "") +
                "</div>", unsafe_allow_html=True)


# =====================
# App
# =====================
st.set_page_config(page_title="3D‑Druck Preisrechner", page_icon="🖨️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown("""
# 🖨️ 3D‑Druck Preisrechner
<span class="pill">Bambu Lab P1S</span><span class="pill">PLA Standard</span><span class="pill">Streamlit</span>

Berechne fair & transparent – mit Freundschaftsrabatt, Risiko‑Puffer und allen Kostenfaktoren.
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Eingaben")
    st.caption("Nutze Slider für schnelle Schätzungen – Feintuning per Zahleneingabe.")

    grams = st.slider("Filamentverbrauch (g)", 0, 2000, 100, 10)
    purge = st.slider("Purge/Abfall (g)", 0, 500, 0, 5, help="z. B. AMS‑Farbwechsel")
    hours = st.slider("Druckzeit (h)", 0.0, 48.0, 6.0, 0.5)

    st.divider()
    st.subheader("Material & Energie")
    filament_eur_kg = st.number_input("Filament €/kg", 0.0, 150.0, 22.0, 0.5)
    kwh_price = st.number_input("Strompreis €/kWh", 0.0, 2.0, 0.25, 0.01)
    power_w = st.slider("Ø Leistung (W)", 0, 500, 80, 5)

    st.subheader("Maschine & Arbeit")
    depr = st.slider("Verschleiß/Abschreibung €/h", 0.0, 5.0, 0.5, 0.1)
    consumables = st.slider("Verbrauchsmaterial‑Anteil", 0.0, 0.5, 0.05, 0.01)
    labor_h = st.slider("Arbeitszeit (h)", 0.0, 24.0, 1.0, 0.5)
    labor_rate = st.slider("Stundensatz €/h", 0.0, 200.0, 30.0, 5.0)

    st.subheader("Puffer, Rabatt & Co.")
    risk = st.slider("Risiko‑Anteil", 0.0, 0.5, 0.10, 0.01)
    markup = st.slider("Marge/Aufschlag", 0.0, 0.5, 0.0, 0.01)
    friend = st.slider("Freundschaftsrabatt", 0.0, 0.9, 0.20, 0.01)
    pack_ship = st.number_input("Verpackung/Versand (€)", 0.0, 500.0, 0.0, 0.5)
    min_fee = st.number_input("Mindestbetrag (€)", 0.0, 100.0, 10.0, 1.0)

    st.divider()
    if st.button("🎈 Kleines Easter‑Egg"):
        st.balloons()

inputs = PricingInputs(
    filament_used_g=grams,
    purge_waste_g=purge,
    print_time_h=hours,
    filament_eur_per_kg=filament_eur_kg,
    electricity_eur_per_kwh=kwh_price,
    avg_power_w=power_w,
    depreciation_eur_per_h=depr,
    consumables_ratio=consumables,
    labor_hours=labor_h,
    labor_rate_eur_per_h=labor_rate,
    risk_ratio=risk,
    markup_ratio=markup,
    friend_discount_ratio=friend,
    packaging_shipping_eur=pack_ship,
    min_fee_eur=min_fee,
)

# Simulierter Mini‑Progress für "Feedback"
with st.spinner("Berechne Preis …"):
    time.sleep(0.2)

breakdown, meta = compute_cost(inputs)

# ======= Kopfzeile mit Kernmetriken ========
colA, colB, colC, colD = st.columns([1.2,1,1,1])
with colA:
    metric_card("Empfohlener Preis", f"€ {breakdown['Empfohlener Preis']:.2f}", "inkl. Mindestbetrag & Rabatt")
with colB:
    metric_card("Filament gesamt", f"{meta['filament_total_g']} g", "inkl. Purge")
with colC:
    metric_card("Energie", f"{meta['kwh']} kWh")
with colD:
    metric_card("Druckzeit", f"{inputs.print_time_h:.1f} h")

st.write("")

# ======= Detailtabelle ========
df = pd.DataFrame([
    ("Material", breakdown["Material"]),
    ("Energie", breakdown["Energie"]),
    ("Maschine/Verschleiß", breakdown["Maschine/Verschleiß"]),
    ("Arbeit", breakdown["Arbeit"]),
    ("Verbrauchsmaterial-Puffer", breakdown["Verbrauchsmaterial-Puffer"]),
    ("Risiko-Puffer", breakdown["Risiko-Puffer"]),
    ("Zwischensumme", breakdown["Zwischensumme"]),
    ("Marge/Aufschlag", breakdown["Marge/Aufschlag"]),
    ("Summe vor Rabatt", breakdown["Summe vor Rabatt"]),
    ("Freundschaftsrabatt", -abs(breakdown["Freundschaftsrabatt"])) ,
    ("Verpackung/Versand", breakdown["Verpackung/Versand"]),
], columns=["Posten", "€"])

st.markdown("### Kostenaufschlüsselung")
st.dataframe(df, hide_index=True, use_container_width=True)

# ======= Export & Sharing ========
col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.download_button(
        "📄 Export als JSON",
        data=json.dumps({**asdict(inputs), **{"breakdown": breakdown, **meta}}, ensure_ascii=False, indent=2),
        file_name="druck_preis_kalkulation.json",
        mime="application/json",
    )
with col2:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📊 Export Tabelle (CSV)", data=csv, file_name="kostenaufstellung.csv", mime="text/csv")
with col3:
    note = f"Empfohlener Preis: € {breakdown['Empfohlener Preis']:.2f} — Filament {meta['filament_total_g']} g, Zeit {inputs.print_time_h:.1f} h"
    st.text_area("Notiz/Angebot (kopieren)", value=note, height=80)

# ======= Presets / Profile ========
with st.expander("⚙️ Presets & Schnellwahl"):
    c1, c2, c3 = st.columns(3)
    if c1.button("PLA – Standard (Bambu)"):
        st.session_state.update({
            "Filament €/kg":22.0, "Strompreis €/kWh":0.25, "Ø Leistung (W)":80,
            "Verschleiß/Abschreibung €/h":0.5, "Verbrauchsmaterial‑Anteil":0.05,
        })
        st.toast("Preset PLA gesetzt", icon="✅")
    if c2.button("PETG – robust"):
        st.session_state.update({
            "Filament €/kg":26.0, "Ø Leistung (W)":90, "Risiko‑Anteil":0.12,
        })
        st.toast("Preset PETG gesetzt", icon="✅")
    if c3.button("ABS/ASA – technisch"):
        st.session_state.update({
            "Filament €/kg":28.0, "Ø Leistung (W)":110, "Risiko‑Anteil":0.18,
        })
        st.toast("Preset ABS/ASA gesetzt", icon="✅")

st.markdown("<div class='footer-note'>Tipp: Teile die JSON mit Freund:innen – sie können deine Kalkulation 1:1 nachverfolgen.</div>", unsafe_allow_html=True)
