# 🌍 EARTH PULSE – Hear the Earth Through NASA Data
**NASA Space Apps Challenge 2026**

## 📖 Overview
Earth Pulse is an interactive web application designed for the NASA Space Apps Challenge 2026. It transforms complex NASA climate and Earth observation data into an immersive, multi-sensory experience combining visual thermal maps with **Data Sonification** (converting data into actual sound frequencies and amplitudes). 

The platform bridges visual data with auditory discovery, making Earth science more accessible and supporting "eyes-free" environmental monitoring—particularly for visually impaired users.

---

## 🚀 Key Features
* **Interactive Climate Exploration:** Explore 36 years of historical climate records (1990–2025) across selected grid points.
* **Data Sonification Engine:** Translates annual temperature levels into pitch (`Hz`) and year-to-year change magnitude into amplitude using Python, NumPy, and SciPy.
* **Blind Listening Challenge:** An engaging feature where users listen to audio clips of different years and try to deduce climate variations before looking at the charts.
* **WCAG Accessibility Compliance:** Built with high-contrast UI design, clear text descriptions, and audio-first exploration options.

---

## 📊 Data Source
* **Dataset:** NASA POWER (MERRA-2 Earth Skin Temperature, TS parameter).
* **Official Data Portal:** [NASA POWER Data Portal](https://go.nasa.gov/4iPGljT).
* **Geographic Scope:** Equatorial Pacific grid location (Latitude: 0.5° N, Longitude: -150° W).
* **Temporal Coverage:** 1990–2025 (36 annual observations).

---

## 🛠️ Technology Stack
* **Language & Framework:** Python, Streamlit
* **Data Processing:** Pandas, NumPy
* **Audio Generation:** SciPy (`scipy.io.wavfile`), NumPy sine waves, Web Audio API
* **Accessibility:** WCAG Standards[span_6](start_span)[span_6](end_span)[span_7](start_span)[span_7](end_span)[span_8](start_span)[span_8](end_span)[span_9](start_span)[span_9](end_span)[span_10](start_span)[span_10](end_span)[span_11](start_span)[span_11](end_span)[span_12](start_span)[span_12](end_span)

---

## 👥 Team EARTH PULSE
* **Fatima Sinan & Ghada Saman:** Design & Integration / NASA Data
* **Giyana Al-Ghamdi:** Visualizations / EIC
* **Jana Al-Zahrani:** Data Analysis
* **Wasan Al-Dheeb:** Sonification
* **Najoud Al-Shafei:** Web Development & Accessibility[span_13](start_span)[span_13](end_span)
