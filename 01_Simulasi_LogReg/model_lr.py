import json
import numpy as np
import pandas as pd

AGE_BINS = [0, 13, 18, 30, 45, 60, 200]
AGE_LABELS = ['0-12', '13-17','18-29', '30-44', '45-59', '60+']

class Preprocessor:
    """Semua parameter dipelajari dari data training jadi tidak ada data leakage"""
    NUM = ['age', 'avg_glucose_level', 'bmi']
    ONESHOT = {'work_type': 'Private', 'smoking_status': 'never smoked'}  # Nilai diambil dari data yang jumlahnya paling banyak

    def fit(self, d):
        grp = pd.cut(d['age'], bins=AGE_BINS, labels=AGE_LABELS, right=False)
        self.bmi_median = d.groupby(grp, observed=False)['bmi'].median().to_dict()
        d = self._impute(d)
        self.mean = d[self.NUM].mean().to_dict()
        self.std = d[self.NUM].std().to_dict()
        self.categories = {c: sorted(v for v in d[c].unique() if v != base)
                            for c, base in self.ONESHOT.items()}
        return self

    def _impute(self, d):
        d = d.copy()
        grp = pd.cut(d['age'], bins=AGE_BINS, labels=AGE_LABELS, right=False).astype(str)
        d['bmi'] = d['bmi'].fillna(grp.map(self.bmi_median))
        return d

    def transform(self, d):
        d = self._impute(d)
        X = pd.DataFrame(index=d.index)
        for c in self.NUM:
            X[c] = (d[c] - self.mean[c]) / self.std[c]
        X['hypertension'] = d['hypertension']
        X['heart_disease'] = d['heart_disease']
        X['is_male'] = (d['gender'] == 'Male').astype(int)
        X['ever_married'] = (d['ever_married'] == 'Yes').astype(int)
        X['is_urban'] = (d['Residence_type'] == 'Urban').astype(int)
        for c, cats in self.categories.items():
            for v in cats:
                X[f'{c}={v}'] = (d[c] == v).astype(int)
        return X.astype(float)

class LogisticRegression:
    def __init__(self, lr=0.1, epochs=2000, class_weight=None):
        self.lr, self.epochs, self.class_weight = lr, epochs, class_weight

    @staticmethod
    def sigmoid(z):
        return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))

    def _sample_weight(self, y):
        if self.class_weight is None:
            return np.ones_like(y)
        return np.where(y == 1, self.class_weight[1], self.class_weight[0])

    def loss(self, X, y, w=None, b=None):
        w = self.w if w is None else w
        b = self.b if b is None else b
        p = np.clip(self.sigmoid(X @ w + b), 1e-12, 1 - 1e-12)
        s = self._sample_weight(y)
        return -np.sum(s * (y * np.log(p) + (1 - y) * np.log(1 - p))) / s.sum()

    def gradient(self, X, y, w, b):
        s = self._sample_weight(y)
        err = s * (self.sigmoid(X @ w + b) - y)
        return X.T @ err / s.sum(), err.sum() / s.sum()

    def fit(self, X, y, X_val=None, y_val=None):
        self.w, self.b = np.zeros(X.shape[1]), 0.0
        self.history = {'train': [], 'val': []}
        for _ in range(self.epochs):
            self.history['train'].append(self.loss(X, y))
            if X_val is not None:
                self.history['val'].append(self.loss(X_val, y_val))
            dw, db = self.gradient(X, y, self.w, self.b)
            self.w -= self.lr * dw
            self.b -= self.lr * db
        return self

    def predict_proba(self, X):
        return self.sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)

class StrokeModel:
    """Paket siap pakai: preprocessing + model + threshold. Dipakai notebook DAN GUI."""

    def __init__(self, prep, model, threshold, fitur=None):
        self.prep, self.model, self.threshold, self.fitur = prep, model, threshold, fitur

    def skor(self, data):
        """data mentah (DataFrame, atau dict untuk 1 pasien) -> skor risiko 0..1"""
        if isinstance(data, dict):
            data = pd.DataFrame([data])
        X = self.prep.transform(data)
        if self.fitur is not None:          # pakai fitur terpilih saja (hasil seleksi fitur di Modul C)
            X = X[self.fitur]
        return self.model.predict_proba(X.values)

    def prediksi(self, data):
        return (self.skor(data) >= self.threshold).astype(int)

    def save(self, path, **info):
        isi = {'preprocessing': vars(self.prep), 'weights': self.model.w.tolist(),
               'bias': float(self.model.b), 'threshold': self.threshold, 'fitur': self.fitur, **info}
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
        return cls(prep, model, isi['threshold'], isi.get('fitur'))
