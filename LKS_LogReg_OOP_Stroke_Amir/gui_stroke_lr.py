"""
Modul D - GUI Cek Risiko Stroke (Logistic Regression dari nol)
Jalankan:  python gui_stroke_lr.py
Satu folder dengan model_lr.py dan model_stroke_lr.json (keduanya dibuat oleh notebook).
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

from model_lr import StrokeModel          # class yang SAMA dengan di notebook

FILE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_stroke_lr.json')

# (kolom, label, isian): dict -> Combobox (label Indonesia -> nilai dataset),
#                        tuple (min, maks, boleh_kosong) -> isian angka
FORM = [
    ('age', 'Usia (tahun)', (0, 120, False)),
    ('gender', 'Jenis kelamin', {'Laki-laki': 'Male', 'Perempuan': 'Female'}),
    ('hypertension', 'Hipertensi', {'Ya': 1, 'Tidak': 0}),
    ('heart_disease', 'Penyakit jantung', {'Ya': 1, 'Tidak': 0}),
    ('ever_married', 'Status menikah', {'Sudah': 'Yes', 'Belum': 'No'}),
    ('work_type', 'Jenis pekerjaan', {'Swasta': 'Private', 'Wiraswasta': 'Self-employed',
                                      'PNS / Pemerintah': 'Govt_job', 'Anak-anak': 'children',
                                      'Belum pernah bekerja': 'Never_worked'}),
    ('Residence_type', 'Tempat tinggal', {'Kota': 'Urban', 'Desa': 'Rural'}),
    ('smoking_status', 'Status merokok', {'Tidak pernah merokok': 'never smoked',
                                          'Mantan perokok': 'formerly smoked',
                                          'Perokok aktif': 'smokes', 'Tidak diketahui': 'Unknown'}),
    ('avg_glucose_level', 'Gula darah (mg/dL)', (40, 400, False)),
    ('bmi', 'BMI (boleh kosong)', (10, 100, True)),
]


def baca_angka(teks, nama, minimum, maksimum, boleh_kosong=False):
    """Ubah teks jadi angka. Lempar ValueError dengan pesan jelas kalau salah."""
    teks = teks.strip().replace(',', '.')          # terima koma desimal: 27,5
    if teks == '':
        if boleh_kosong:
            return None
        raise ValueError(f'{nama} wajib diisi.')
    try:
        nilai = float(teks)
    except ValueError:
        raise ValueError(f'{nama} harus berupa angka, bukan "{teks}".')
    if not (minimum <= nilai <= maksimum):         # juga menolak nan / inf
        raise ValueError(f'{nama} harus di antara {minimum} dan {maksimum}.')
    return nilai


class AppStroke(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Cek Risiko Stroke')
        self.resizable(False, False)
        frame = ttk.Frame(self, padding=16)
        frame.grid()
        ttk.Label(frame, text='Cek Risiko Stroke', font=('Segoe UI', 14, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(0, 10))

        self.widget = {}
        for i, (kolom, label, isian) in enumerate(FORM, start=1):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=3)
            if isinstance(isian, dict):
                w = ttk.Combobox(frame, values=list(isian), state='readonly', width=25)
            else:
                w = ttk.Entry(frame, width=28)
            w.grid(row=i, column=1, pady=3)
            self.widget[kolom] = w

        n = len(FORM) + 1
        self.tombol = ttk.Button(frame, text='Prediksi', command=self.prediksi)
        self.tombol.grid(row=n, column=0, columnspan=2, pady=(10, 0))
        self.hasil = tk.Label(frame, text='Isi data lalu tekan Prediksi', font=('Segoe UI', 11),
                              width=40, height=4, relief='groove', wraplength=330)
        self.hasil.grid(row=n + 1, column=0, columnspan=2, pady=(12, 0))
        ttk.Label(frame, text='Alat bantu skrining, bukan diagnosis dokter.\n'
                              'Skor bukan persentase peluang stroke.',
                  foreground='gray', justify='center').grid(row=n + 2, column=0, columnspan=2, pady=(8, 0))

        try:
            self.model = StrokeModel.load(FILE_MODEL)
        except Exception as e:
            self.tombol.state(['disabled'])
            messagebox.showerror('Model tidak ditemukan', f'Jalankan notebook dulu.\n\n{e}')

    def ambil_data(self):
        """Baca semua isian form -> dict satu pasien (format sama dengan dataset)."""
        data = {}
        for kolom, label, isian in FORM:
            teks = self.widget[kolom].get()
            nama = label.split(' (')[0]
            if isinstance(isian, dict):
                if teks == '':
                    raise ValueError(f'Pilih {nama.lower()}.')
                data[kolom] = isian[teks]
            else:
                data[kolom] = baca_angka(teks, nama, *isian)
        return data

    def prediksi(self):
        try:
            data = self.ambil_data()
            skor = float(self.model.skor(data)[0])
            tinggi = skor >= self.model.threshold
            teks = 'RISIKO TINGGI - sarankan pemeriksaan ke dokter' if tinggi else 'Risiko rendah'
            teks += f'\nSkor risiko {skor * 100:.0f} dari 100 (batas waspada: {self.model.threshold * 100:.0f})'
            if data['bmi'] is None:
                teks += f'\n(BMI kosong, diisi median {self.model.prep.bmi_median:.1f})'
            self.hasil.config(text=teks, bg='#f8d7da' if tinggi else '#d4edda')
        except ValueError as e:
            messagebox.showwarning('Input belum benar', str(e))
        except Exception as e:
            messagebox.showerror('Terjadi kesalahan', str(e))


if __name__ == '__main__':
    AppStroke().mainloop()
