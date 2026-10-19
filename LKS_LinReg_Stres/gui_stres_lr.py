"""
Modul D - GUI Cek Tingkat Stres Mahasiswa (Linear Regression)
Jalankan: python gui_stres_lr.py
Butuh model_linreg.py dan model_stres_lr.json (dibuat notebook) di folder yang sama.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from model_linreg import StressModel

# (kolom, label, pilihan). pilihan None = isian angka. * = dipakai model
FORM = [
    ('Age', 'Usia', None),
    ('Gender', 'Jenis kelamin', ['Male', 'Female']),
    ('Department', 'Jurusan', ['Arts', 'Business', 'Engineering', 'Medical', 'Science']),
    ('CGPA', 'IPK (0-4)', None),
    ('Sleep_Duration', 'Jam tidur per malam *', None),
    ('Study_Hours', 'Jam belajar per hari *', None),
    ('Social_Media_Hours', 'Jam medsos per hari', None),
    ('Physical_Activity', 'Aktivitas fisik (menit/minggu) *', None),
]
NAMA_FAKTOR = {'Tidur_Kurang': 'Tidur < 5 jam',
               'Aktivitas_Rendah': 'Aktivitas fisik <= 60 menit',
               'Belajar_Berlebih': 'Belajar > 10 jam'}
WARNA = {'Rendah': 'green', 'Sedang': 'darkorange', 'Tinggi': 'red'}


class AppStres(tk.Tk):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.title('Cek Tingkat Stres Mahasiswa')
        self.isian = {}

        for i, (kolom, label, pilihan) in enumerate(FORM):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky='w', padx=10, pady=3)
            if pilihan:
                w = ttk.Combobox(self, values=pilihan, state='readonly', width=18)
            else:
                w = ttk.Entry(self, width=21)
            w.grid(row=i, column=1, padx=10)
            self.isian[kolom] = w

        n = len(FORM)
        ttk.Label(self, text='* dipakai model. Kosong = diisi nilai tengah data latih.',
                  foreground='gray').grid(row=n, column=0, columnspan=2, padx=10, sticky='w')
        ttk.Button(self, text='Prediksi', command=self.prediksi).grid(row=n + 1, column=0, columnspan=2, pady=8)
        self.hasil = tk.Label(self, text='', font=('Arial', 16, 'bold'))
        self.hasil.grid(row=n + 2, column=0, columnspan=2)
        self.rincian = tk.Label(self, text='', justify='left')
        self.rincian.grid(row=n + 3, column=0, columnspan=2, padx=10, pady=(0, 10))

    def baca_form(self):
        data = {}
        for kolom, label, pilihan in FORM:
            teks = self.isian[kolom].get().strip()
            if teks == '':
                data[kolom] = None
            elif pilihan:
                data[kolom] = teks
            else:
                try:
                    data[kolom] = float(teks.replace(',', '.'))
                except ValueError:
                    raise ValueError(f'"{label}" harus angka')
        return data

    def prediksi(self):
        try:
            data = self.baca_form()
        except ValueError as e:
            messagebox.showerror('Input salah', str(e))
            return
        skor, kategori = self.model.prediksi(data)
        skor, kategori = float(skor[0]), kategori[0]

        # Rincian: stres dasar + efek tiap faktor yang aktif
        intercept, efek = self.model.koefisien()
        fitur = self.model.prep.fitur_mentah(data).iloc[0]
        baris = [f'Stres dasar: {intercept:.2f}']
        for f, aktif in fitur.items():
            if aktif:
                baris.append(f'+ {NAMA_FAKTOR.get(f, f)}: {efek[f]:+.2f}')

        self.hasil.config(text=f'Stres {kategori} ({skor:.1f} / 10)', fg=WARNA[kategori])
        self.rincian.config(text='\n'.join(baris))


if __name__ == '__main__':
    AppStres(StressModel.load('model_stres_lr.json')).mainloop()
