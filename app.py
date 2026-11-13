import io
import os
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import wavfile
import streamlit as st

st.set_page_config(
    page_title="EARTH PULSE | NASA Space Apps 2026",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #040C18;
        color: #E6F1FF;
    }
    [data-testid="stSidebar"] {
        background-color: #071324;
        border-right: 1px solid #1E3A5F;
    }
    h1, h2, h3 {
        color: #00D4FF !important;
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        background-color: #0A192F;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #1E3A5F;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.08);
    }
    [data-testid="stMetricLabel"] {
        color: #8892B0 !important;
        font-size: 0.9rem;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.65rem;
    }
    .thermal-bar {
        height: 14px;
        width: 100%;
        border-radius: 7px;
        background: linear-gradient(90deg, #0055FF 0%, #00D4FF 25%, #FFD166 50%, #FF7B00 75%, #FF2A2A 100%);
        margin: 10px 0 5px 0;
        border: 1px solid #1E3A5F;
    }
    .thermal-labels {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: #8892B0;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #0A192F;
        border-left: 4px solid #00D4FF;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

MONTHS = [
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
]


@st.cache_data
def load_full_excel():
  possible_paths = [
      "data/POWER_Regional_Monthly_1990_2025.xlsx",
      "POWER_Regional_Monthly_1990_2025.xlsx",
      "data/POWER_Regional_Monthly_1990_2025 copy.xlsx",
      "POWER_Regional_Monthly_1990_2025 copy.xlsx",
  ]
  file_path = next((p for p in possible_paths if os.path.exists(p)), None)

  if file_path is None:
    st.error(
        "⚠️ لم يتم العثور على ملف الإكسل! تأكدي من وضعه داخل مجلد data باسم"
        " POWER_Regional_Monthly_1990_2025.xlsx"
    )
    st.stop()

  df = pd.read_excel(file_path, sheet_name="in", skiprows=9, header=None)
  df.columns = ["PARAMETER", "YEAR", "LAT", "LON"] + MONTHS + ["ANN"]

  num_cols = ["YEAR", "LAT", "LON"] + MONTHS + ["ANN"]
  for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

  df = df.dropna(subset=["YEAR", "LAT", "LON"]).copy()
  df["YEAR"] = df["YEAR"].astype(int)
  df[MONTHS + ["ANN"]] = df[MONTHS + ["ANN"]].replace(-999, np.nan)

  df = df.sort_values(["LAT", "LON", "YEAR"]).reset_index(drop=True)
  df["Delta_T"] = df.groupby(["LAT", "LON"])["ANN"].diff()
  return df


df_all = load_full_excel()

GLOBAL_T_MIN = float(df_all[MONTHS + ["ANN"]].min().min())
GLOBAL_T_MAX = float(df_all[MONTHS + ["ANN"]].max().max())


def temp_to_freq(temp_val, t_min=25.15, t_max=29.22):
  f_min, f_max = 220.0, 880.0
  clamped = max(t_min, min(t_max, float(temp_val)))
  return f_min + ((clamped - t_min) / (t_max - t_min)) * (f_max - f_min)


def generate_annual_audio(temp_val, delta_val):
  sample_rate = 44100
  duration = 2.0
  frequency = temp_to_freq(temp_val)

  if pd.isna(delta_val) or delta_val == 0:
    amplitude = 0.25
  else:
    abs_dt = abs(float(delta_val))
    clamped_dt = max(0.02, min(2.09, abs_dt))
    amplitude = 0.1 + ((clamped_dt - 0.02) / (2.09 - 0.02)) * 0.7

  t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
  envelope = np.ones_like(t)
  fade = int(0.05 * sample_rate)
  envelope[:fade] = np.linspace(0, 1, fade)
  envelope[-fade:] = np.linspace(1, 0, fade)

  wave = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
  wave = (wave * 32767).astype(np.int16)

  buf = io.BytesIO()
  wavfile.write(buf, sample_rate, wave)
  return buf.getvalue(), frequency, amplitude


def generate_monthly_sequence_audio(monthly_values):
  sample_rate = 44100
  note_duration = 0.28
  full_wave = np.array([], dtype=np.float64)

  for val in monthly_values:
    if pd.isna(val):
      continue
    freq = temp_to_freq(val, t_min=GLOBAL_T_MIN, t_max=GLOBAL_T_MAX)
    t = np.linspace(
        0, note_duration, int(sample_rate
