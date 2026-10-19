import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from model_linreg import StressModel

FOLDER = os.path.dirname(os.path.abspath(__file__))
FILE_MODEL = os.path.join(FOLDER, 'model_stres_lr.json')
FILE_RIWAYAT = os.path.join(FOLDER, 'riwayat_prediksi.csv')

TAMPILKAN_SEMUA = False

SEMUA_FORM = [
    ('Age', 'Usia (tahun)', None),
    ('Gender', 'Jenis kelamin', ['Male', 'Female']),
    ('Department', 'Jurusan', ['Arts', 'Business', 'Engineering', 'Medical', 'Science']),
    ('CGPA', 'IPK (0-4)', None),
    ('Sleep_Duration', 'Jam tidur per malam', None),
    ('Study_Hours', 'Jam belajar per hari', None),
    ('Social_Media_Hours', 'Jam medsos per hari', None),
    ('Physical_Activity', 'Aktivitas fisik (menit/minggu)', None),
]
DIPAKAI_MODEL = ['Sleep_Duration', 'Study_Hours', 'Physical_Activity']
RENTANG = {'Age': (15, 40), 'CGPA': (0, 4), 'Sleep_Duration': (0, 24), 'Study_Hours': (0, 24),
           'Social_Media_Hours': (0, 24), 'Physical_Activity': (0, 3000)}

if TAMPILKAN_SEMUA:
    FORM = [(k, lbl + ' *' if k in DIPAKAI_MODEL else lbl, p) for k, lbl, p in SEMUA_FORM]
else:
    FORM = [(k, lbl, p) for k, lbl, p in SEMUA_FORM if k in DIPAKAI_MODEL]
KOLOM_LAIN = [k for k, _, _ in SEMUA_FORM if k not in [f[0] for f in FORM]]

FAKTOR = {
    'Tidur_Kurang': ('Tidur kurang dari 5 jam',
                     'Usahakan tidur minimal 5 jam, idealnya 7-8 jam. Matikan HP 30 menit sebelum tidur.'),
    'Aktivitas_Rendah': ('Aktivitas fisik 60 menit/minggu atau kurang',
                         'Tambah olahraga ringan, misalnya jalan kaki 15 menit sehari, supaya lebih dari 60 menit seminggu.'),
    'Belajar_Berlebih': ('Belajar lebih dari 10 jam per hari',
                         'Kurangi jam belajar di bawah 10 jam. Pakai teknik Pomodoro: 25 menit belajar, 5 menit istirahat.'),
}

TIPS_UMUM = """Tips umum agar tidak stres:

1. Tidur cukup. Dari data, tidur kurang dari 5 jam menaikkan stres paling besar (+2,5 level).
2. Bergerak. Olahraga lebih dari 60 menit per minggu menurunkan stres sekitar 1 level.
3. Belajar secukupnya. Belajar lebih dari 10 jam per hari menaikkan stres sekitar 1,35 level.
4. Istirahat di sela belajar dan atur jadwal harian.
5. Cerita ke teman, keluarga, atau guru BK kalau merasa berat.

Catatan: tips nomor 1 sampai 3 berasal dari hasil model.
Tips nomor 4 dan 5 adalah saran umum."""

WARNA = {'Rendah': 'green', 'Sedang': 'darkorange', 'Tinggi': 'red'}
KOLOM_RIWAYAT = ['Waktu', 'Tidur', 'Belajar', 'Aktivitas', 'Skor', 'Kategori']


class AppStres(tk.Tk):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.title('Cek Tingkat Stres Mahasiswa')
        self.geometry('560x520' if TAMPILKAN_SEMUA else '560x420')

        tab = ttk.Notebook(self)
        tab.pack(fill='both', expand=True, padx=8, pady=8)
        self.tab_prediksi = ttk.Frame(tab, padding=10)
        self.tab_tips = ttk.Frame(tab, padding=10)
        self.tab_riwayat = ttk.Frame(tab, padding=10)
        tab.add(self.tab_prediksi, text='Prediksi')
        tab.add(self.tab_tips, text='Cara Agar Tidak Stres')
        tab.add(self.tab_riwayat, text='Riwayat Prediksi')

        self.buat_tab_prediksi()
        self.buat_tab_tips()
        self.buat_tab_riwayat()
        self.muat_riwayat()

    def buat_tab_prediksi(self):
        f = self.tab_prediksi
        self.isian = {}
        for i, (kolom, label, pilihan) in enumerate(FORM):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky='w', pady=3)
            if pilihan:
                w = ttk.Combobox(f, values=pilihan, state='readonly', width=20)
            else:
                w = ttk.Entry(f, width=23)
            w.grid(row=i, column=1, padx=10)
            self.isian[kolom] = w

        n = len(FORM)
        ttk.Label(f, text='Semua isian wajib diisi.' + (' * = dipakai model.' if TAMPILKAN_SEMUA else ''),
                  foreground='gray').grid(row=n, column=0, columnspan=2, sticky='w', pady=(5, 0))
        tombol = ttk.Frame(f)
        tombol.grid(row=n + 1, column=0, columnspan=2, pady=8)
        ttk.Button(tombol, text='Prediksi', command=self.prediksi).pack(side='left', padx=4)
        ttk.Button(tombol, text='Reset', command=self.reset).pack(side='left', padx=4)

        self.lbl_hasil = tk.Label(f, text='', font=('Arial', 16, 'bold'))
        self.lbl_hasil.grid(row=n + 2, column=0, columnspan=2)
        self.lbl_rincian = tk.Label(f, text='', justify='left')
        self.lbl_rincian.grid(row=n + 3, column=0, columnspan=2, pady=(5, 0))

    def baca_form(self):
        """Ambil isian form jadi dict. Semua wajib diisi dan angkanya harus masuk akal."""
        data = {k: None for k in KOLOM_LAIN}
        for kolom, label, pilihan in FORM:
            teks = self.isian[kolom].get().strip()
            if teks == '':
                raise ValueError(f'"{label}" belum diisi')
            if pilihan:
                data[kolom] = teks
                continue
            try:
                angka = float(teks.replace(',', '.'))
            except ValueError:
                raise ValueError(f'"{label}" harus angka')
            bawah, atas = RENTANG[kolom]
            if not bawah <= angka <= atas:
                raise ValueError(f'"{label}" harus antara {bawah} dan {atas}')
            data[kolom] = angka
        jam = ['Sleep_Duration', 'Study_Hours', 'Social_Media_Hours']
        total = sum(data[k] for k in jam if data[k] is not None)
        if total > 24:
            raise ValueError(f'Total jam tidur, belajar, dan medsos = {total:g} jam, lebih dari 24 jam sehari')
        return data

    def prediksi(self):
        try:
            data = self.baca_form()
        except ValueError as e:
            messagebox.showerror('Input salah', str(e))
            return

        skor, kategori = self.model.prediksi(data)
        skor, kategori = float(skor[0]), str(kategori[0])

        intercept, efek = self.model.koefisien()
        fitur = self.model.prep.fitur_mentah(data).iloc[0]
        aktif = [f for f, nilai in fitur.items() if nilai == 1]
        baris = [f'Stres dasar: {intercept:.2f}']
        for f in aktif:
            baris.append(f'+ {FAKTOR[f][0]}: {efek[f]:+.2f}')
        if not aktif:
            baris.append('Tidak ada faktor risiko. Pertahankan!')

        self.lbl_hasil.config(text=f'Stres {kategori} ({skor:.1f} / 10)', fg=WARNA[kategori])
        self.lbl_rincian.config(text='\n'.join(baris))

        self.perbarui_tips(aktif, kategori)
        self.tambah_riwayat(data, skor, kategori)

    def reset(self):
        for w in self.isian.values():
            if isinstance(w, ttk.Combobox):
                w.set('')
            else:
                w.delete(0, 'end')
        self.lbl_hasil.config(text='')
        self.lbl_rincian.config(text='')

    def buat_tab_tips(self):
        f = self.tab_tips
        ttk.Label(f, text='Saran untuk kamu (dari prediksi terakhir):',
                  font=('Arial', 11, 'bold')).pack(anchor='w')
        self.lbl_tips_pribadi = tk.Label(f, text='Lakukan prediksi dulu di tab Prediksi.',
                                         justify='left', wraplength=500, fg='gray')
        self.lbl_tips_pribadi.pack(anchor='w', pady=(4, 12))
        ttk.Separator(f).pack(fill='x', pady=4)
        tk.Label(f, text=TIPS_UMUM, justify='left', wraplength=500).pack(anchor='w', pady=(8, 0))

    def perbarui_tips(self, aktif, kategori):
        if not aktif:
            teks = f'Stres kamu {kategori}. Tidak ada faktor risiko yang aktif, pertahankan kebiasaanmu.'
        else:
            teks = f'Stres kamu {kategori}. Yang perlu diperbaiki:\n'
            teks += '\n'.join(f'- {FAKTOR[f][1]}' for f in aktif)
        self.lbl_tips_pribadi.config(text=teks, fg=WARNA[kategori])

    def buat_tab_riwayat(self):
        f = self.tab_riwayat
        self.tabel = ttk.Treeview(f, columns=KOLOM_RIWAYAT, show='headings', height=15)
        for k in KOLOM_RIWAYAT:
            self.tabel.heading(k, text=k)
            self.tabel.column(k, width=130 if k == 'Waktu' else 70, anchor='center')
        self.tabel.pack(fill='both', expand=True)
        ttk.Button(f, text='Hapus Riwayat', command=self.hapus_riwayat).pack(pady=6)

    def tambah_riwayat(self, data, skor, kategori):
        baris = [datetime.now().strftime('%Y-%m-%d %H:%M'), f"{data['Sleep_Duration']:g}",
                 f"{data['Study_Hours']:g}", f"{data['Physical_Activity']:g}", f'{skor:.1f}', kategori]
        self.tabel.insert('', 0, values=baris)

        baru = not os.path.exists(FILE_RIWAYAT)
        with open(FILE_RIWAYAT, 'a', newline='') as f:
            tulis = csv.writer(f)
            if baru:
                tulis.writerow(KOLOM_RIWAYAT)
            tulis.writerow(baris)

    def muat_riwayat(self):
        """Saat GUI dibuka, tampilkan riwayat lama dari file CSV."""
        if not os.path.exists(FILE_RIWAYAT):
            return
        with open(FILE_RIWAYAT, newline='') as f:
            baris = list(csv.reader(f))[1:]
        for b in baris:
            self.tabel.insert('', 0, values=b)

    def hapus_riwayat(self):
        if messagebox.askyesno('Hapus', 'Hapus semua riwayat prediksi?'):
            self.tabel.delete(*self.tabel.get_children())
            if os.path.exists(FILE_RIWAYAT):
                os.remove(FILE_RIWAYAT)


if __name__ == '__main__':
    AppStres(StressModel.load(FILE_MODEL)).mainloop()