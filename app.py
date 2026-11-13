import io
import os
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import wavfile
import streamlit as st

# إعدادات الصفحة
st.set_page_config(
    page_title="EARTH PULSE | NASA Space Apps 2026",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# حقن CSS لمطابقة هوية العرض التقديمي (Deep Space Navy + NASA Thermal Palette)
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


# تحميل وتنظيف جميع البيانات من ملف Excel (6,120 صف × 17 عمود)
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

  # تخطي سطور الترويسة التسعة الخاصة بملفات NASA POWER
  df = pd.read_excel(file_path, sheet_name="in", skiprows=9, header=None)
  df.columns = ["PARAMETER", "YEAR", "LAT", "LON"] + MONTHS + ["ANN"]

  num_cols = ["YEAR", "LAT", "LON"] + MONTHS + ["ANN"]
  for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

  df = df.dropna(subset=["YEAR", "LAT", "LON"]).copy()
  df["YEAR"] = df["YEAR"].astype(int)
  df[MONTHS + ["ANN"]] = df[MONTHS + ["ANN"]].replace(-999, np.nan)

  # ترتيب البيانات وحساب التغير السنوي Delta_T لكل موقع جغرافي بشكل مستقل
  df = df.sort_values(["LAT", "LON", "YEAR"]).reset_index(drop=True)
  df["Delta_T"] = df.groupby(["LAT", "LON"])["ANN"].diff()
  return df


df_all = load_full_excel()

# النطاق الكلي لدرجات الحرارة في قاعدة البيانات بالكامل
GLOBAL_T_MIN = float(df_all[MONTHS + ["ANN"]].min().min())  # 23.61°C
GLOBAL_T_MAX = float(df_all[MONTHS + ["ANN"]].max().max())  # 30.49°C


# دالة تحويل القيمة الحرارية إلى تردد صوتي (220 Hz - 880 Hz)
def temp_to_freq(temp_val, t_min=25.15, t_max=29.22):
  f_min, f_max = 220.0, 880.0
  clamped = max(t_min, min(t_max, float(temp_val)))
  return f_min + ((clamped - t_min) / (t_max - t_min)) * (f_max - f_min)


# توليد نغمة واحدة للمعدل السنوي
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


# توليد لحن متسلسل يعزف الـ 12 شهراً (JAN -> DEC) للسنة المختارة
def generate_monthly_sequence_audio(monthly_values):
  sample_rate = 44100
  note_duration = 0.28  # 0.28 ثانية لكل شهر (المجموع ~3.36 ثانية)
  full_wave = np.array([], dtype=np.float64)

  for val in monthly_values:
    if pd.isna(val):
      continue
    freq = temp_to_freq(val, t_min=GLOBAL_T_MIN, t_max=GLOBAL_T_MAX)
    t = np.linspace(
        0, note_duration, int(sample_rate * note_duration), endpoint=False
    )
    envelope = np.ones_like(t)
    fade = int(0.025 * sample_rate)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)

    note = 0.5 * envelope * np.sin(2 * np.pi * freq * t)
    full_wave = np.concatenate([full_wave, note])

  wave_int16 = (full_wave * 32767).astype(np.int16)
  buf = io.BytesIO()
  wavfile.write(buf, sample_rate, wave_int16)
  return buf.getvalue()


# --- الهيدر الرئيسي ---
st.title("🌍 EARTH PULSE")
st.markdown(
    "#### **Hear the Earth Through NASA Data** | *NASA Space Apps Challenge"
    " 2026*"
)

st.markdown('<div class="thermal-bar"></div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="thermal-labels">
        <span>❄️ {GLOBAL_T_MIN:.2f}°C (220 Hz - Cold / Low Pitch)</span>
        <span>🌐 170 Locations | 36 Years | 6,120 Records</span>
        <span>🔥 {GLOBAL_T_MAX:.2f}°C (880 Hz - Hot / High Pitch)</span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- الشريط الجانبي (Control Panel) ---
st.sidebar.markdown("## 🎛️ Control Panel")
st.sidebar.markdown("**Dataset:** NASA POWER (MERRA-2 TS)")

lats = sorted(df_all["LAT"].unique())
lons = sorted(df_all["LON"].unique(), reverse=True)

selected_lat = st.sidebar.selectbox("خط العرض (Latitude °N):", lats, index=0)
selected_lon = st.sidebar.selectbox("خط الطول (Longitude °W):", lons, index=0)

# تصفية بيانات الموقع المختار (36 سنة)
df_loc = df_all[
    (df_all["LAT"] == selected_lat) & (df_all["LON"] == selected_lon)
].copy()

st.sidebar.markdown("---")
mode = st.sidebar.radio(
    "اختر وضع التجربة (Mode):",
    [
        "📊 Standard Exploration (الاستكشاف البصري والصوتي)",
        "🎧 Blind Listening Mode (الاستماع الأعمى)",
    ],
)

nasa_cmap = mcolors.LinearSegmentedColormap.from_list(
    "nasa_thermal", ["#0055FF", "#00D4FF", "#FFD166", "#FF7B00", "#FF2A2A"]
)

if mode == "📊 Standard Exploration (الاستكشاف البصري والصوتي)":
  selected_year = st.sidebar.slider("اختر السنة (Year):", 1990, 2025, 2015)

  row = df_loc[df_loc["YEAR"] == selected_year].iloc[0]
  ann_temp = row["ANN"]
  delta_t = row["Delta_T"]
  monthly_vals = [row[m] for m in MONTHS]

  ann_audio, freq, amp = generate_annual_audio(ann_temp, delta_t)
  monthly_audio = generate_monthly_sequence_audio(monthly_vals)

  # بطاقات القياس الرئيسية
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("الموقع المختار", f"{selected_lat}°N, {selected_lon}°W")
  c2.metric(f"المعدل السنوي ({selected_year})", f"{ann_temp:.2f} °C")
  delta_str = "N/A (سنة الأساس)" if pd.isna(delta_t) else f"{delta_t:+.2f} °C"
  c3.metric("التغير السنوي (ΔT)", delta_str)
  c4.metric("التردد السنوي (Pitch)", f"{freq:.1f} Hz")

  # قسم مشغلات الصوت (السنوي + الشهري)
  st.markdown("### 🔊 Data Sonification Players")
  aud1, aud2 = st.columns(2)

  with aud1:
    st.markdown(f"**1️⃣ النغمة السنوية لعام {selected_year} (Annual Pitch)**")
    st.audio(ann_audio, format="audio/wav")
    st.caption(
        f"تردد ثابت {freq:.1f} Hz يمثل المتوسط السنوي ({ann_temp:.2f}°C) بشدة"
        f" صوت {amp:.2f}."
    )

  with aud2:
    st.markdown(
        f"**2️⃣ التسلسل الصوتي لـ 12 شهراً ({selected_year} JAN → DEC)**"
    )
    st.audio(monthly_audio, format="audio/wav")
    st.caption(
        "استمع لتغير درجات الحرارة شهراً بشهر خلال العام كسلسلة نغمات متتابعة."
    )

  # وصف إمكانية الوصول (WCAG Accessibility)
  hottest_month = MONTHS[int(np.argmax(monthly_vals))]
  coldest_month = MONTHS[int(np.argmin(monthly_vals))]
  st.markdown(
      f"""
        <div class="info-box">
            <strong>♿ الوصف الصوتي والنصي لإمكانية الوصول (Accessibility Summary):</strong><br>
            في الإحداثيات <b>({selected_lat}°N, {selected_lon}°W)</b> خلال عام <b>{selected_year}</b>: 
            بلغ المتوسط السنوي <b>{ann_temp:.2f}°C</b>. وسُجلت أعلى حرارة شهرية في شهر <b>{hottest_month} ({max(monthly_vals):.2f}°C)</b>، 
            بينما سُجلت أدنى حرارة في شهر <b>{coldest_month} ({min(monthly_vals):.2f}°C)</b>.
        </div>
        """,
      unsafe_allow_html=True,
  )

  # الرسوم البيانية التفاعلية (3 تبويبات تغطي كل البيانات)
  st.markdown("### 📈 NASA Thermal Visualizations")
  tab1, tab2, tab3 = st.tabs([
      f"📅 الدورة الشهرية لعام {selected_year} (JAN - DEC)",
      "🌡️ السلسلة السنوية (1990 - 2025)",
      "📊 التغير السنوي (Annual ΔT)",
  ])

  with tab1:
    fig_m, ax_m = plt.subplots(figsize=(11, 4))
    fig_m.patch.set_facecolor("#040C18")
    ax_m.set_facecolor("#0A192F")

    norm_m = plt.Normalize(GLOBAL_T_MIN, GLOBAL_T_MAX)
    colors_m = [nasa_cmap(norm_m(v)) for v in monthly_vals]

    bars = ax_m.bar(
        MONTHS, monthly_vals, color=colors_m, edgecolor="#FFFFFF", linewidth=0.5
    )
    ax_m.plot(MONTHS, monthly_vals, color="#00D4FF", marker="o", linewidth=2)
    ax_m.set_ylim(min(monthly_vals) - 0.5, max(monthly_vals) + 0.5)
    ax_m.set_ylabel("Temperature (°C)", color="#E6F1FF")
    ax_m.set_title(
        f"Monthly Skin Temperature Profile — {selected_year} (Lat:"
        f" {selected_lat}, Lon: {selected_lon})",
        color="#00D4FF",
    )
    ax_m.tick_params(colors="#8892B0")
    ax_m.grid(True, linestyle=":", alpha=0.2, color="#8892B0")
    for spine in ax_m.spines.values():
      spine.set_color("#1E3A5F")
    st.pyplot(fig_m)

  with tab2:
    fig1, ax1 = plt.subplots(figsize=(11, 4))
    fig1.patch.set_facecolor("#040C18")
    ax1.set_facecolor("#0A192F")

    norm_a = plt.Normalize(df_all["ANN"].min(), df_all["ANN"].max())
    ax1.plot(
        df_loc["YEAR"], df_loc["ANN"], color="#1E3A5F", linewidth=2, zorder=1
    )
    sc = ax1.scatter(
        df_loc["YEAR"],
        df_loc["ANN"],
        c=df_loc["ANN"],
        cmap=nasa_cmap,
        norm=norm_a,
        s=75,
        zorder=2,
        edgecolors="#FFFFFF",
        linewidth=0.6,
    )
    ax1.axvline(x=selected_year, color="#00D4FF", linestyle="--", alpha=0.8)
    ax1.scatter(
        [selected_year],
        [ann_temp],
        color="#FF2A2A",
        s=180,
        zorder=3,
        edgecolors="#FFFFFF",
        linewidth=2,
    )

    ax1.set_ylabel("Annual Mean Temp (°C)", color="#E6F1FF")
    ax1.set_xlabel("Year (1990 - 2025)", color="#E6F1FF")
    ax1.tick_params(colors="#8892B0")
    ax1.grid(True, linestyle=":", alpha=0.2, color="#8892B0")
    for spine in ax1.spines.values():
      spine.set_color("#1E3A5F")

    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label("Temp (°C)", color="#E6F1FF")
    cbar.ax.yaxis.set_tick_params(color="#8892B0")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#8892B0")
    st.pyplot(fig1)

  with tab3:
    fig2, ax2 = plt.subplots(figsize=(11, 4))
    fig2.patch.set_facecolor("#040C18")
    ax2.set_facecolor("#0A192F")

    df_valid = df_loc.dropna(subset=["Delta_T"])
    bar_colors = [
        "#FF5500" if val > 0 else "#00D4FF" for val in df_valid["Delta_T"]
    ]
    ax2.bar(
        df_valid["YEAR"],
        df_valid["Delta_T"],
        color=bar_colors,
        alpha=0.9,
        width=0.65,
    )
    ax2.axhline(0, color="#8892B0", linewidth=1)
    if selected_year != 1990:
      ax2.axvline(x=selected_year, color="#FFD166", linestyle="--", alpha=0.9)

    ax2.set_ylabel("Annual Change ΔT (°C)", color="#E6F1FF")
    ax2.set_xlabel("Year (1991 - 2025)", color="#E6F1FF")
    ax2.tick_params(colors="#8892B0")
    ax2.grid(True, linestyle=":", alpha=0.2, color="#8892B0")
    for spine in ax2.spines.values():
      spine.set_color("#1E3A5F")
    st.pyplot(fig2)

  # جدول البيانات الخام للموقع المختار مع زر تحميل CSV
  with st.expander(
      "📋 استعراض وتحميل جدول البيانات الكامل لهذا الموقع (1990 - 2025)"
  ):
    st.dataframe(df_loc, use_container_width=True)

else:
  # --- وضع الاستماع الأعمى (Blind Listening Mode) ---
  st.subheader("🎧 Blind Listening Challenge (اختبار الاستماع الأعمى)")
  st.markdown(
      """
        <div class="info-box">
            استمع إلى المقطعين الصوتيين الخاصين بالموقع الجغرافي المختار <b>({lat}°N, {lon}°W)</b> 
            وحاول تحديد أيهما يمثل أبرد سنة وأيهما يمثل أسخن سنة في هذا الموقع قبل كشف البيانات!
        </div>
        """.format(lat=selected_lat, lon=selected_lon),
      unsafe_allow_html=True,
  )

  min_row = df_loc.loc[df_loc["ANN"].idxmin()]
  max_row = df_loc.loc[df_loc["ANN"].idxmax()]

  audio_cold, f_cold, _ = generate_annual_audio(
      min_row["ANN"], min_row["Delta_T"]
  )
  audio_hot, f_hot, _ = generate_annual_audio(
      max_row["ANN"], max_row["Delta_T"]
  )

  col_a, col_b = st.columns(2)
  with col_a:
    st.markdown("### 🔵 المقطع الصوتي (A)")
    st.audio(audio_cold, format="audio/wav")

  with col_b:
    st.markdown("### 🔴 المقطع الصوتي (B)")
    st.audio(audio_hot, format="audio/wav")

  st.markdown("<br>", unsafe_allow_html=True)
  with st.expander("👁️ كشف البيانات والنتائج (Reveal Data)"):
    r1, r2 = st.columns(2)
    with r1:
      st.info(
          f"**المقطع (A) يمثل عام {int(min_row['YEAR'])} (الأبرد في هذا"
          f" الموقع):**\n- المتوسط السنوي: **{min_row['ANN']:.2f}°C**\n-"
          f" التردد: **{f_cold:.1f} Hz**"
      )
    with r2:
      st.error(
          f"**المقطع (B) يمثل عام {int(max_row['YEAR'])} (الأسخن في هذا"
          f" الموقع):**\n- المتوسط السنوي: **{max_row['ANN']:.2f}°C**\n-"
          f" التردد: **{f_hot:.1f} Hz**"
      )

st.markdown("---")
st.caption(
    "EARTH PULSE Prototype | NASA Space Apps Challenge 2026 | Full NASA POWER"
    " Regional Dataset (6,120 Records)."
)
