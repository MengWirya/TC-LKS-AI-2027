# LKS AI — Prediksi Risiko Stroke, Logistic Regression dari nol (versi OOP)

| File | Isi |
|---|---|
| LKS_LogReg_OOP_Stroke_Amir.ipynb | Modul A–D, sudah dijalankan |
| model_lr.py | 3 class: Preprocessor, LogisticRegression, StrokeModel (DIBUAT OTOMATIS oleh notebook lewat %%writefile) |
| gui_stroke_lr.py | GUI Tkinter (class AppStroke), memakai StrokeModel dari model_lr.py |
| model_stroke_lr.json | Bobot + threshold + parameter preprocessing |
| df_clean.csv / healthcare-dataset-stroke-data.csv | Data bersih / dataset asli |

Cara pakai: semua file di satu folder → notebook: Restart & Run All → `python gui_stroke_lr.py`.
Kalau mengubah isi class di notebook, jalankan ulang sel %%writefile lalu sel %run di bawahnya.
