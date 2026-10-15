import json
import numpy as np
import pandas as pd


class Preprocessor:
    NUM = ['age', 'avg_glucose_level', 'bmi']
    BINER = {'gender': {'Male': 1, 'Female': 0},
             'ever_married': {'Yes': 1, 'No': 0},
             'Residence_type': {'Urban': 1, 'Rural': 0}}
    PEMBANDING = {'work_type': 'Private', 'smoking_status': 'never smoked'}   # kategori yang dibuang

    def fit(self, data):
        """Pelajari semua parameter dari data LATIH."""
        self.bmi_median = float(data['bmi'].median())
        d = data.assign(bmi=data['bmi'].fillna(self.bmi_median))
        self.mean = {c: float(d[c].mean()) for c in self.NUM}
        self.std = {c: float(d[c].std()) for c in self.NUM}
        self.onehot = {c: [str(k) for k in sorted(data[c].unique()) if k != base]
                       for c, base in self.PEMBANDING.items()}
        self.fitur = (self.NUM + ['hypertension', 'heart_disease'] + list(self.BINER)
                      + [f'{c}_{k}' for c, ks in self.onehot.items() for k in ks])
        return self

    def transform(self, data):
        """Terapkan parameter dari data latih ke data mana pun (latih, uji, atau input GUI)."""
        d = data.assign(bmi=pd.to_numeric(data['bmi']).fillna(self.bmi_median))
        X = pd.DataFrame(index=d.index)
        for c in self.NUM:
            X[c] = (d[c].astype(float) - self.mean[c]) / self.std[c]
        X['hypertension'], X['heart_disease'] = d['hypertension'], d['heart_disease']
        for col, peta in self.BINER.items():
            X[col] = d[col].map(peta)
        for col, kategori in self.onehot.items():
            for k in kategori:
                X[f'{col}_{k}'] = (d[col] == k).astype(int)
        return X[self.fitur].astype(float)


class LogisticRegression:
    def __init__(self, lr=0.1, epochs=2000, class_weight=True):
        self.lr, self.epochs, self.class_weight = lr, epochs, class_weight

    @staticmethod
    def sigmoid(z):
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))          # clip: cegah overflow exp

    def bobot_sampel(self, y):
        if not self.class_weight:
            return np.ones(len(y))
        n, n_pos = len(y), y.sum()
        return np.where(y == 1, n / (2 * n_pos), n / (2 * (n - n_pos)))

    def loss(self, X, y, w, b):
        p = np.clip(self.sigmoid(X @ w + b), 1e-12, 1 - 1e-12)  # clip: cegah log(0)
        s = self.bobot_sampel(y)
        return -np.sum(s * (y * np.log(p) + (1 - y) * np.log(1 - p))) / s.sum()

    def gradien(self, X, y, w, b):
        s = self.bobot_sampel(y)
        err = s * (self.sigmoid(X @ w + b) - y)
        return X.T @ err / s.sum(), err.sum() / s.sum()

    def fit(self, X, y):
        self.w, self.b, self.riwayat = np.zeros(X.shape[1]), 0.0, []
        for _ in range(self.epochs):
            self.riwayat.append(self.loss(X, y, self.w, self.b))
            dw, db = self.gradien(X, y, self.w, self.b)
            self.w -= self.lr * dw
            self.b -= self.lr * db
        return self

    def predict_proba(self, X):
        return self.sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)


class StrokeModel:
    """Paket siap pakai: preprocessing + model + threshold. Dipakai notebook DAN GUI."""

    def __init__(self, prep, model, threshold):
        self.prep, self.model, self.threshold = prep, model, threshold

    def skor(self, data):
        """data mentah (DataFrame, atau dict untuk 1 pasien) -> skor risiko 0..1"""
        if isinstance(data, dict):
            data = pd.DataFrame([data])
        return self.model.predict_proba(self.prep.transform(data).values)

    def prediksi(self, data):
        return (self.skor(data) >= self.threshold).astype(int)

    def save(self, path, **info):
        isi = {'preprocessing': vars(self.prep), 'weights': self.model.w.tolist(),
               'bias': float(self.model.b), 'threshold': self.threshold, **info}
        with open(path, 'w') as f:
            json.dump(isi, f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            isi = json.load(f)
        prep = Preprocessor()
        prep.__dict__.update(isi['preprocessing'])
        model = LogisticRegression()
        model.w, model.b = np.array(isi['weights']), isi['bias']
        return cls(prep, model, isi['threshold'])
