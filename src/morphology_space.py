from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import pairwise_distances

NUMERIC = [
    'area','perimeter','major_axis','minor_axis','aspect_ratio',
    'circularity','solidity','extent','eccentricity',
    'beta0','beta1','euler_characteristic'
]

DEFAULT_SCALE_FREE = ['aspect_ratio','circularity','solidity','extent','eccentricity','beta0','beta1','euler_characteristic']

def prepare_features(df: pd.DataFrame, columns=None):
    columns = columns or [c for c in NUMERIC if c in df.columns]
    if not columns:
        raise ValueError('No hay variables numéricas compatibles.')
    X = df[columns].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)
    keep = X.notna().all(axis=1)
    return X.loc[keep], keep


def standardize(df: pd.DataFrame, columns=None):
    X, keep = prepare_features(df, columns)
    scaler = StandardScaler()
    Z = scaler.fit_transform(X)
    return pd.DataFrame(Z, index=X.index, columns=X.columns), keep, scaler


def pca_projection(df: pd.DataFrame, columns=None, n_components=2):
    Z, keep, scaler = standardize(df, columns)
    n = min(n_components, Z.shape[1], Z.shape[0])
    if n < 1:
        raise ValueError('No hay suficientes datos para PCA.')
    pca = PCA(n_components=n)
    coords = pca.fit_transform(Z)
    out = pd.DataFrame(coords, index=Z.index,
                       columns=[f'PC{i+1}' for i in range(n)])
    return out, pca.explained_variance_ratio_, pca.components_, keep, scaler


def morphology_distance_matrix(df: pd.DataFrame, columns=None, metric='euclidean'):
    Z, keep, _ = standardize(df, columns)
    D = pairwise_distances(Z.to_numpy(), metric=metric)
    ids = df.loc[keep, 'observation_id'].astype(str).tolist() if 'observation_id' in df else list(map(str, Z.index))
    return pd.DataFrame(D, index=ids, columns=ids), keep
