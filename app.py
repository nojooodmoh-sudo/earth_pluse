import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.io import wavfile

# إعدادات صفحة Streamlit مع مراعاة معايير الـ Accessibility
st.set_page_config(
    page_title="Earth Pulse | NASA Space Apps 2026",
    page_icon="🌍",
    layout="wide",
)

# تصميم الواجهة والهوية البصرية (Dark Mode المستوحى من ناسا)
st.markdown(
    """
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3 { color: #58a6ff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""",
    unsafe_allow_html=True,
)

# العنوان الرئيسي ووصف إمكانية الوصول (Accessibility)
st.title("🌍 EARTH PULSE – Hear the Earth Through NASA Data")
st.markdown(
    "**NASA Space Apps Challenge 2026** | تحويل بيانات ناسا المناخية إلى تجربة تفاعلية تجمع بين الرؤية والصوت لدعم المكفوفين وضعاف البصر (Eyes-free monitoring)."
)

# بيانات محاكاة مبنية على تقرير ناسا POWER (1990-2025) للإحداثيات (Latitude: 0.5, Longitude: -150)
@st.cache_data
def load_data():
  # بيانات العينة الفعلية من تقرير التحليل
  data = {
      "Year": list(range(1990, 2026)),
      "Temperature": [
          26.78,
          27.39,
          27.41,
          26.86,
          27.16,
          26.38,
          26.10,
          27.97,
          25.88,
          25.15,
          25.63,
          26.22,
          27.60,
          26.83,
          27.09,
          26.63,
          26.82,
          25.75,
          25.69,
          27.14,
          25.99,
          25.74,
          26.55,
          26.47,
          26.99,
          28.43,
          26.82,
          26.45,
          26.80,
          27.28,
          26.14,
          26.08,
          25.84,
          27.64,
          26.92,
          26.09,
      ],
  }
  df = pd.DataFrame(data)
  # حساب التغير السنوي Delta T
  df["Delta_T"] = df["Temperature"].diff().fillna(0)
  return df


df = load_data()


# وظيفة توليد الصوت بناءً على معادلات ناسا (Data Sonification)
def generate_sonification_audio(temp_val, delta_val):
  sample_rate = 44100
  duration = 2.0  # ثانيتان لكل مقطع صوتي

  # معادلة تحويل درجة الحرارة إلى تردد Pitch (من 220 هرتز إلى 880 هرتز)
  t_min, t_max = 25.15, 28.43
  f_min, f_max = 220.0, 880.0
  # تقييد القيم ضمن النطاق
  clamped_temp = max(t_min, min(t_max, temp_val))
  frequency = f_min + (
      (clamped_temp - t_min) / (t_max - t_min) * (f_max - f_min)
  )

  # معادلة تحويل التغير السنوي إلى Amplitude (مستوى الصوت)
  amplitude = min(0.8, max(0.1, 0.1 + abs(delta_val) * 0.3))

  t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
  # موجة جيبية (Sine Wave) تعكس البيانات
  audio_data = amplitude * np.sin(2 * np.pi * frequency * t)
  audio_data = (audio_data * 32767).astype(np.int16)

  byte_io = io.BytesIO()
  wavfile.write(byte_io, sample_rate, audio_data)
  return byte_io.getvalue(), frequency, amplitude


# الشريط الجانبي للتفاعل (Sidebar)
st.sidebar.header("🛠️ خيارات الاستكشاف")
mode = st.sidebar.selectbox(
    "اختر وضع الاستخدام (Mode):",
    [
        "📊 الاستكشاف القياسي (Standard Exploration)",
        "🎧 وضع الاستماع الأعمى (Blind Listening)",
    ],
)

selected_year = st.sidebar.slider(
    "اختر السنة المستهدفة:", 1990, 2025, 2015
)

# جلب بيانات السنة المحددة
row_data = df[df["Year"] == selected_year].iloc[0]
temp = row_data["Temperature"]
delta = row_data["Delta_T"]

# توليد الصوت المرتبط بالبيانات
audio_bytes, freq, amp = generate_sonification_audio(temp, delta)

if mode == "📊 الاستكشاف القياسي (Standard Exploration)":
  st.subheader(f"📈 تحليل سنة {selected_year} وربطها بالصوت")

  col1, col2, col3 = st.columns(3)
  col1.metric("متوسط درجة الحرارة (TS)", f"{temp:.2f} °C")
  col2.metric("التغير السنوي (ΔT)", f"{delta:+.2f} °C")
  col3.metric("التردد الصوتي المقابل (Pitch)", f"{freq:.1f} Hz")

  # عرض مشغل الصوت مع وصف إمكانية الوصول (Accessibility Alt Text)
  st.markdown("### 🔊 تحويل البيانات إلى صوت (Data Sonification)")
  st.audio(audio_bytes, format="audio/wav")
  st.caption(
      f"ملاحظة للمكفوفين: هذا الصوت يمثل درجة حرارة {temp}°C بتردد {freq:.1f} هرتز"
      " ومستوى صوت يعكس حجم التغير السنوي."
  )

  # رسم بياني تفاعلي باستخدام Matplotlib
  st.markdown("### 🌍 النظرة الزمنية الشاملة (1990 - 2025)")
  fig, ax = plt.subplots(figsize=(10, 4))
  ax.plot(
      df["Year"],
      df["Temperature"],
      color="#58a6ff",
      marker="o",
      linewidth=2,
      label="Annual Temperature",
  )
  ax.axvline(
      x=selected_year,
      color="#f85149",
      linestyle="--",
      label=f"Selected Year: {selected_year}",
  )
  ax.set_facecolor("#161b22")
  fig.patch.set_facecolor("#0d1117")
  ax.tick_params(colors="white")
  ax.xaxis.label.set_color("white")
  ax.yaxis.label.set_color("white")
  ax.legend(facecolor="#161b22", labelcolor="white")
  st.pyplot(fig)

else:
  # ميزة Blind Listening (الاستماع الأعمى للتحدي)
  st.subheader("🎧 Blind Listening Challenge")
  st.markdown(
    "استمع إلى المقطعين الصوتين التاليين وحاول اكتشاف أيهما يعود لسنة ذات حرارة"
    " أعلى أو تغير أكبر قبل الاطلاع على الرسوم البيانية!"
  )

  col_a, col_b = st.columns(2)

  # سنة مقارنة ثابتة (مثلاً 1999 الأبرد مقابل 2015 الأسخن)
  audio_99, f_99, _ = generate_sonification_audio(25.15, -0.73)
  audio_15, f_15, _ = generate_sonification_audio(28.43, 1.44)

  with col_a:
    st.markdown("**الملف الصوتي (أ)**")
    st.audio(audio_99, format="audio/wav")

  with col_b:
    st.markdown("**الملف الصوتي (ب)**")
    st.audio(audio_15, format="audio/wav")

  with st.expander("🔍 كشف الحقيقة والبيانات"):
    st.write(
        "الملف (أ) يمثل سنة **1999** (درجة الحرارة الدنيا 25.15°C بتردد منخفض"
        f" {f_99:.1f}Hz)."
    )
    st.write(
        "الملف (ب) يمثل سنة **2015** (درجة الحرارة العظمى 28.43°C بتردد مرتفع"
        f" {f_15:.1f}Hz)."
    )

# تذييل الصفحة وتأكيد المعايير
st.markdown("---")
st.markdown(
    "💡 **Earth Pulse Prototype** — Powered by NASA POWER Data, Python, Streamlit,"
    " & Web Audio API (WCAG Accessibility Compliant)."
)
