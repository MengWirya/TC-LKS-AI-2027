import json
import numpy as np
import pandas as pd


class Preprocessor:
    NUM = ['Age', 'CGPA', 'Sleep_Duration', 'Study_Hours', 'Social_Media_Hours', 'Physical_Activity']
    KAT = ['Gender', 'Department']

    def __init__(self, ambang=True):
        self.ambang = ambang          # True = 3 fitur ambang hasil EDA, False = fitur asli

    def fit(self, data):
        """Pelajari semua parameter dari data LATIH."""
        self.median = {c: float(data[c].median()) for c in self.NUM}
        self.modus = {c: str(data[c].mode()[0]) for c in self.KAT}
        self.onehot = {c: sorted(str(k) for k in data[c].dropna().unique() if k != self.modus[c]) for c in self.KAT}
        X = self.fitur_mentah(data)
        self.kolom = list(X.columns)
        self.mean = X.mean().to_dict()
        self.std = X.std().to_dict()
        return self

    def fitur_mentah(self, data):
        """Isi kosong lalu buat fitur (belum di-z-score). data bisa DataFrame atau dict (dari GUI)."""
        if isinstance(data, dict):
            data = pd.DataFrame([data])
        d = data.copy()
        for c in self.NUM:
            d[c] = pd.to_numeric(d[c], errors='coerce').fillna(self.median[c])
        for c in self.KAT:
            d[c] = d[c].fillna(self.modus[c])
        X = pd.DataFrame(index=d.index)
        if self.ambang:
            X['Tidur_Kurang'] = d['Sleep_Duration'] < 5
            X['Aktivitas_Rendah'] = d['Physical_Activity'] <= 60
            X['Belajar_Berlebih'] = d['Study_Hours'] > 10
        else:
            for c in self.NUM:
                X[c] = d[c]
            for c, kelas in self.onehot.items():
                for k in kelas:
                    X[f'{c}_{k}'] = d[c] == k
        return X.astype(float)

    def transform(self, data):
        """Fitur + z-score memakai mean/std data latih."""
        X = self.fitur_mentah(data)[self.kolom]
        return (X - pd.Series(self.mean)) / pd.Series(self.std)


class LinearRegression:
    def __init__(self, lr=0.1, epochs=500):
        self.lr = lr
        self.epochs = epochs

    def predict(self, X):
        return X @ self.w + self.b

    def loss(self, X, y):
        return np.mean((self.predict(X) - y) ** 2)            # MSE

    def fit(self, X, y):
        """Gradient descent."""
        self.w, self.b = np.zeros(X.shape[1]), 0.0
        self.riwayat = []
        for _ in range(self.epochs):
            self.riwayat.append(self.loss(X, y))
            err = self.predict(X) - y
            self.w -= self.lr * 2 * X.T @ err / len(y)          # dMSE/dw
            self.b -= self.lr * 2 * err.mean()                  # dMSE/db
        return self

    def fit_normal(self, X, y):
        """Jawaban pasti (Normal Equation), untuk mengecek gradient descent."""
        X1 = np.column_stack([np.ones(len(X)), X])
        theta = np.linalg.solve(X1.T @ X1, X1.T @ y)
        self.b, self.w = theta[0], theta[1:]
        return self


class StressModel:
    KATEGORI = np.array(['Rendah', 'Sedang', 'Tinggi'])

    def __init__(self, prep, model, batas=(3.5, 5.5)):
        self.prep, self.model, self.batas = prep, model, list(batas)

    @staticmethod
    def ke_kategori(nilai, batas=(3.5, 5.5)):
        return StressModel.KATEGORI[np.digitize(nilai, batas)]

    def skor(self, data):
        """Prediksi level stres 0-10."""
        return np.clip(self.model.predict(self.prep.transform(data).values), 0, 10)

    def prediksi(self, data):
        s = self.skor(data)
        return s, self.ke_kategori(s, self.batas)

    def koefisien(self):
        """Bobot dalam satuan asli: efek = w / std, intercept = b - sum(efek * mean)."""
        efek = pd.Series(self.model.w, index=self.prep.kolom) / pd.Series(self.prep.std)[self.prep.kolom]
        intercept = self.model.b - (efek * pd.Series(self.prep.mean)[self.prep.kolom]).sum()
        return float(intercept), efek

    def save(self, path):
        p = self.prep
        isi = {'ambang': p.ambang, 'median': p.median, 'modus': p.modus, 'onehot': p.onehot, 'kolom': p.kolom,
               'mean': p.mean, 'std': p.std, 'w': self.model.w.tolist(), 'b': float(self.model.b), 'batas': self.batas}
        with open(path, 'w') as f:
            json.dump(isi, f, indent=1)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            isi = json.load(f)
        prep = Preprocessor(isi['ambang'])
        for k in ['median', 'modus', 'onehot', 'kolom', 'mean', 'std']:
            setattr(prep, k, isi[k])
        model = LinearRegression()
        model.w, model.b = np.array(isi['w']), isi['b']
        return cls(prep, model, isi['batas'])
