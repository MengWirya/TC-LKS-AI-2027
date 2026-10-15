"""
Modul D - GUI Cek Risiko Stroke (Logistic Regression dari nol)
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from model_lr import StrokeModel

FILE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_stroke_lr.json')

FORM = [
    ('age', 'Usia (tahun)', (0.08, 120, False), None),                     # usia 0,08 sampai 120 tahun, wajib diisi
    ('avg_glucose_level', 'Gula darah (mg/dL)', (40, 400, False), None),   # gula darah 40 sampai 400, wajib diisi
    ('hypertension', 'Hipertensi', {'Ya': 1, 'Tidak': 0}, 0),              # dropdown Ya/Tidak - disimpan sebagai 1/0
    ('heart_disease', 'Penyakit jantung', {'Ya': 1, 'Tidak': 0}, 0),       # dropdown Ya/Tidak - disimpan sebagai 1/0
    ('bmi', 'BMI (boleh kosong)', (10, 100, True), None),                  # BMI 10 sampai 100, True = boleh kosong (nanti diisi median)
    ('gender', 'Jenis kelamin', {'Laki-laki': 'Male', 'Perempuan': 'Female'}, 'Female'),
    ('ever_married', 'Status menikah', {'Sudah': 'Yes', 'Belum': 'No'}, 'No'),
    ('work_type', 'Jenis pekerjaan', {'Swasta': 'Private', 'Wiraswasta': 'Self-employed', 'PNS / Pemerintah': 'Govt_job', 'Anak-anak': 'children', 'Belum pernah bekerja': 'Never_worked'}, 'Private'),
    ('Residence_type', 'Tempat tinggal', {'Kota': 'Urban', 'Desa': 'Rural'}, 'Urban'),
    ('smoking_status', 'Status merokok', {'Tidak pernah merokok': 'never smoked', 'Mantan perokok': 'formerly smoked', 'Perokok aktif': 'smokes', 'Tidak diketahui': 'Unknown'}, 'never smoked'),
]

# True  = tampilkan SEMUA input (seperti mengisi data pasien baru yang lengkap)
# False = tampilkan hanya input yang dipakai model
TAMPILKAN_SEMUA = True

# Beberapa nama fitur hasil Preprocessor berbeda dengan nama kolom aslinya.
# Kamus ini menerjemahkan nama fitur - nama kolom input
ASAL_FITUR = {'is_male': 'gender', 'is_urban': 'Residence_type'}


def kolom_dipakai(fitur):
    """Mencari kolom input mana saja yang benar-benar dipakai model."""
    if fitur is None:                                   # kalau model tidak menyimpan daftar fitur
        return {kolom for kolom, *_ in FORM}            # berarti model memakai SEMUA kolom
    # Untuk setiap fitur:
    #   - kalau ada di ASAL_FITUR, ambil nama kolom aslinya (is_male -> gender)
    #   - kalau namanya seperti 'work_type=Govt_job', ambil bagian sebelum '=' (work_type)
    #   - selain itu, nama fitur = nama kolom (age -> age)
    return {ASAL_FITUR.get(f, f.split('=')[0]) for f in fitur}


def baca_angka(teks, nama, minimum, maksimum, boleh_kosong=False):
    """Mengubah teks dari kotak input menjadi angka, sekaligus mengecek apakah isinya benar."""
    teks = teks.strip().replace(',', '.')               # hapus spasi di awal/akhir, ubah koma jadi titik (27,5 -> 27.5)
    if teks == '':                                      # kalau kotak dikosongkan
        if boleh_kosong:                                # dan kolom ini boleh kosong (BMI)
            return None                                 # kirim None, nanti Preprocessor mengisinya dengan median
        raise ValueError(f'{nama} wajib diisi.')        # kalau tidak boleh kosong, tampilkan peringatan
    try:
        nilai = float(teks)                             # coba ubah teks jadi angka desimal
    except ValueError:                                  # gagal, berarti yang diketik bukan angka (misal "abc")
        raise ValueError(f'{nama} harus berupa angka, bukan "{teks}".')
    if not (minimum <= nilai <= maksimum):              # cek apakah angka ada di rentang yang masuk akal
        raise ValueError(f'{nama} harus di antara {minimum} dan {maksimum}.')
    return nilai                                        # angka sudah benar, kembalikan nilainya


class AppStroke(tk.Tk):                                 # AppStroke adalah turunan dari tk.Tk (jendela utama)

    def __init__(self):
        """Dijalankan sekali saat aplikasi dibuka: membuat jendela dan semua isinya."""
        super().__init__()                              # jalankan dulu __init__ milik tk.Tk agar jendela terbentuk
        self.title('Cek Risiko Stroke')                 # judul di bagian atas jendela
        self.resizable(False, False)                    # ukuran jendela tidak bisa ditarik/diubah

        frame = ttk.Frame(self, padding=16)             # wadah untuk semua widget, dengan jarak 16 piksel dari tepi
        frame.grid()                                    # tampilkan wadah di jendela

        # Judul besar di bagian atas form
        ttk.Label(frame, text='Cek Risiko Stroke', font=('Segoe UI', 14, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(0, 10))  # baris 0, lebar 2 kolom, jarak bawah 10

        # --- Memuat model dari file JSON ---
        try:
            self.model = StrokeModel.load(FILE_MODEL)   # baca preprocessor, bobot, threshold, dan fitur dari JSON
        except Exception as e:                          # kalau gagal (misal file JSON belum ada)
            self.model = None                           # tandai bahwa model tidak ada
            messagebox.showerror('Model tidak ditemukan', f'Jalankan notebook Main dulu.\n\n{e}')

        # --- Memilih input yang ditampilkan ---
        dipakai = kolom_dipakai(self.model.fitur) if self.model else set()   # kolom yang dipakai model
        if TAMPILKAN_SEMUA:
            self.form = FORM                                                 # tampilkan semua baris FORM
        else:
            self.form = [baris for baris in FORM if baris[0] in dipakai]     # hanya ambil baris FORM yang dipakai

        #Membuat label dan kotak input untuk setiap baris form
        self.widget = {}                                # kamus untuk menyimpan semua kotak input: {kolom: widget}
        for i, (kolom, label, isian, _) in enumerate(self.form, start=1):    # i mulai dari 1 (baris 0 dipakai judul)
            if kolom in dipakai:                        # input yang dipakai model diberi tanda bintang
                label = label + ' *'
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=3)   # label di kolom kiri, rata kiri
            if isinstance(isian, dict):                 # kalau isian berupa dict -> buat dropdown
                w = ttk.Combobox(frame, values=list(isian), state='readonly', width=25)  # readonly = tidak bisa diketik bebas
            else:                                       # kalau isian berupa tuple -> buat kotak ketik angka
                w = ttk.Entry(frame, width=28)
            w.grid(row=i, column=1, pady=3)             # kotak input di kolom kanan
            self.widget[kolom] = w                      # simpan widget agar nanti isinya bisa dibaca

        n = len(self.form) + 1                          # nomor baris pertama setelah semua input

        # --- Tombol Prediksi ---
        self.tombol = ttk.Button(frame, text='Prediksi', command=self.prediksi)   # saat diklik, jalankan self.prediksi
        self.tombol.grid(row=n, column=0, columnspan=2, pady=(10, 0))

        # --- Kotak hasil prediksi ---
        self.hasil = tk.Label(frame, text='Isi data lalu tekan Prediksi', font=('Segoe UI', 11), width=40, height=4, relief='groove', wraplength=330)  # groove = kotak bergaris tepi
        self.hasil.grid(row=n + 1, column=0, columnspan=2, pady=(12, 0))

        # --- Catatan di bagian bawah ---
        ttk.Label(frame, text='* = dipakai model untuk menghitung skor\n''Alat bantu skrining, bukan diagnosis dokter.\n''Skor bukan persentase peluang stroke.', foreground='gray', justify='center').grid(row=n + 2, column=0, columnspan=2, pady=(8, 0))

        if self.model is None:                          # kalau model gagal dimuat
            self.tombol.state(['disabled'])             # matikan tombol Prediksi agar tidak bisa diklik

    def ambil_data(self):
        """Membaca semua isian form, lalu menyusunnya jadi dict satu pasien (format sama dengan dataset)."""
        data = {kolom: bawaan for kolom, _, _, bawaan in FORM}   # mulai dari nilai bawaan untuk SEMUA kolom
                                                                # (Preprocessor butuh semua kolom walau tidak dipakai model)
        for kolom, label, isian, _ in self.form:        # lalu timpa dengan isian user untuk kolom yang ditampilkan
            teks = self.widget[kolom].get()             # ambil teks dari kotak input / dropdown
            nama = label.split(' (')[0]                 # ambil nama tanpa keterangan, 'Usia (tahun)' - 'Usia'
            if isinstance(isian, dict):                 # kalau dropdown
                if teks == '':                          # belum dipilih
                    raise ValueError(f'Pilih {nama.lower()}.')
                data[kolom] = isian[teks]               # ubah tulisan layar jadi nilai dataset ('Ya' - 1)
            else:                                       # kalau kotak angka
                data[kolom] = baca_angka(teks, nama, *isian)   # *isian = mengirim (minimum, maksimum, boleh_kosong)
        return data                                     # contoh: {'age': 75.0, 'avg_glucose_level': 210.0, ...}

    def prediksi(self):
        """Dijalankan saat tombol Prediksi diklik."""
        try:
            data = self.ambil_data()                    # 1. baca dan cek semua isian
            skor = float(self.model.skor(data)[0])      # 2. hitung skor risiko 0 sampai 1 (preprocessing + model)
            tinggi = skor >= self.model.threshold       # 3. bandingkan dengan threshold (0,53) - True/False
            # 4. susun teks hasil
            teks = 'RISIKO TINGGI - sarankan pemeriksaan ke dokter' if tinggi else 'Risiko rendah'
            teks += f'\nSkor risiko {skor * 100:.0f} dari 100 (batas waspada: {self.model.threshold * 100:.0f})'
            # 5. kalau BMI dikosongkan, tampilkan BMI yang dipakai (hasil isian median per kelompok usia)
            if data['bmi'] is None:
                bmi_isi = self.model.prep._impute(pd.DataFrame([data]))['bmi'].iloc[0]   # isi BMI kosong dengan cara yang sama seperti di notebook
                teks += f'\n(BMI kosong, diisi median kelompok usianya: {float(bmi_isi):.1f})'
            # 6. tampilkan hasil: merah muda kalau risiko tinggi, hijau muda kalau rendah
            self.hasil.config(text=teks, bg='#f8d7da' if tinggi else '#d4edda')
        except ValueError as e:                         # kesalahan input (kosong, bukan angka, di luar rentang)
            messagebox.showwarning('Input belum benar', str(e))
        except Exception as e:                          # kesalahan lain yang tidak terduga
            messagebox.showerror('Terjadi kesalahan', str(e))

if __name__ == '__main__':
    AppStroke().mainloop()                              # buat jendela, lalu tunggu terus sampai jendela ditutup