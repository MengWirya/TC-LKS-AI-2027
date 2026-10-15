# LKS AI — Prediksi Risiko Stroke, Logistic Regression dari nol (OOP, split 70/15/15)

| File | Isi |
|---|---|
| LKS_LogReg_7015_Stroke_Amir.ipynb | Notebook utama Modul A–D, sudah dijalankan |
| model_lr.py | 3 class: Preprocessor, LogisticRegression, StrokeModel (DIBUAT OTOMATIS oleh notebook lewat %%writefile) |
| gui_stroke_lr.py | GUI Tkinter (class AppStroke), memakai StrokeModel dari model_lr.py |
| model_stroke_lr.json | Bobot + threshold + parameter preprocessing |
| Eksperimen_Split_Data.ipynb | Bukti pilihan split: 70/15/15 vs 80/16/4, 100 seed |
| df_clean.csv / healthcare-dataset-stroke-data.csv | Data bersih / dataset asli |

Cara pakai: semua file di satu folder → notebook: Restart & Run All → `python gui_stroke_lr.py`.

Hasil (data uji 767 pasien, 38 stroke): recall 0,87 (33/38), F2 0,43, accuracy 0,73, lift 2,8×.
Dari eksperimen 100 seed, recall skema ini rata-rata ±0,80 — itu angka yang jujur untuk disebut.
