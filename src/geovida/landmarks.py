"""Morfometría geométrica de landmarks: lectura MNI .tag, Procrustes generalizado y trayectorias.

Definiciones (Dryden y Mardia, *Statistical Shape Analysis*, 2.ª ed., 2016; Mitteroecker et al.
2004, doi:10.1016/j.jhevol.2004.03.006; Adams y Collyer 2009, doi:10.1111/j.1558-5646.2009.00649.x):

* Configuración: matriz ``(k, m)`` de k landmarks en m = 2 o 3 dimensiones, con unidades físicas.
* Tamaño de centroide: ``CS(X) = ||X − X̄||_F`` (mismas unidades que X).
* Preforma: X centrada y dividida por su CS. Entre dos preformas Z1 y Z2, con σ los valores
  singulares de ``Z2ᵀ Z1`` (el último con el signo de ``det``, para excluir reflexiones):
  - distancia de Procrustes ρ = arccos(Σσ) (radianes, en [0, π/2]);
  - distancia parcial d_P = √(2(1 − Σσ));
  - distancia completa d_F = √(1 − (Σσ)²).
* Procrustes generalizado (GPA): centra, escala a CS = 1 y rota cada configuración hacia la media
  iterativamente hasta que la media cambia menos de ``tol``. Sin reflexiones.
* Coordenadas tangentes: proyección ortogonal de las formas alineadas sobre el plano tangente en la
  media (``X − (X·M) M`` con ‖M‖ = 1), aplanadas a ``k·m`` variables. Válidas si la variación es
  pequeña (ρ ≪ 1), lo que se comprueba y se informa.

Los landmarks de MusMorph se generan por registro con atlas por estadio (Devine et al. 2022,
doi:10.1038/s41597-022-01338-x): son homólogos entre especímenes del mismo atlas; entre atlas de
distintos estadios la correspondencia debe comprobarse (``correspondence_check``).

Solo investigación; no es una herramienta clínica.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------- lectura
def read_tag(path) -> np.ndarray:
    """Puntos de un archivo MNI Tag Point (``.tag``) de un solo volumen, como arreglo ``(k, 3)`` en mm.

    Formato: cabecera ``MNI Tag Point File``, ``Volumes = 1;`` y, tras ``Points =``, una línea por
    punto con x y z (más campos opcionales); la última termina en ``;``.
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if not text.lstrip().startswith("MNI Tag Point File"):
        raise ValueError(f"{path}: no es un archivo MNI Tag Point")
    vols = [ln for ln in text.splitlines() if ln.strip().startswith("Volumes")]
    if vols and vols[0].split("=")[1].strip().rstrip(";").strip() != "1":
        raise ValueError(f"{path}: solo se admiten archivos de un volumen")
    if "Points" not in text:
        raise ValueError(f"{path}: falta la sección Points")
    body = text.split("Points", 1)[1].split("=", 1)[1]
    pts = []
    for ln in body.splitlines():
        f = ln.strip().rstrip(";").split()
        if len(f) < 3:
            continue
        try:
            pts.append([float(f[0]), float(f[1]), float(f[2])])
        except ValueError:
            continue
    if not pts:
        raise ValueError(f"{path}: sin puntos")
    arr = np.asarray(pts, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{path}: coordenadas no finitas")
    return arr


# ---------------------------------------------------------------- Procrustes
def _check(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] not in (2, 3) or x.shape[0] < 3:
        raise ValueError(f"configuración (k, m) con k ≥ 3 y m ∈ {{2, 3}}; forma {x.shape}")
    return x


def centroid_size(x: np.ndarray) -> float:
    x = _check(x)
    return float(np.linalg.norm(x - x.mean(axis=0)))


def preshape(x: np.ndarray) -> np.ndarray:
    x = _check(x)
    c = x - x.mean(axis=0)
    cs = np.linalg.norm(c)
    if cs == 0:
        raise ValueError("configuración degenerada (tamaño de centroide 0)")
    return c / cs


def _rotation(z: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    """Rotación R (det = +1) que minimiza ‖z R − target‖ y la suma de valores singulares con signo."""
    u, s, vt = np.linalg.svd(z.T @ target)
    d = np.ones(len(s))
    if np.linalg.det(u @ vt) < 0:
        d[-1] = -1.0
    r = u @ np.diag(d) @ vt
    return r, float((s * d).sum())


def procrustes_distances(a: np.ndarray, b: np.ndarray) -> dict:
    """ρ, d_P y d_F entre las formas de ``a`` y ``b`` (sin reflexiones)."""
    za, zb = preshape(a), preshape(b)
    if za.shape != zb.shape:
        raise ValueError(f"configuraciones de forma distinta: {za.shape} y {zb.shape}")
    _, t = _rotation(zb, za)
    t = min(max(t, -1.0), 1.0)
    return {"rho": math.acos(t), "partial": math.sqrt(max(0.0, 2 * (1 - t))),
            "full": math.sqrt(max(0.0, 1 - t * t))}


def gpa(configs, tol: float = 1e-10, max_iter: int = 100) -> dict:
    """Procrustes generalizado. ``configs``: secuencia o arreglo ``(n, k, m)``.

    Devuelve ``aligned`` (n, k, m) con CS = 1, ``mean`` (‖M‖ = 1), ``centroid_size`` (n,) en las
    unidades originales, ``iterations`` y ``converged``.
    """
    xs = np.asarray(configs, dtype=float)
    if xs.ndim != 3 or len(xs) < 2:
        raise ValueError("se necesitan al menos 2 configuraciones (n, k, m)")
    cs = np.array([centroid_size(x) for x in xs])
    z = np.stack([preshape(x) for x in xs])
    mean = z[0].copy()
    converged, it = False, 0
    for it in range(1, max_iter + 1):
        z = np.stack([zi @ _rotation(zi, mean)[0] for zi in z])
        new = z.mean(axis=0)
        new = preshape(new)
        new = new @ _rotation(new, mean)[0]  # fija la orientación de la media
        delta = float(np.linalg.norm(new - mean))
        mean = new
        if delta < tol:
            converged = True
            break
    z = np.stack([zi @ _rotation(zi, mean)[0] for zi in z])
    return {"aligned": z, "mean": mean, "centroid_size": cs, "iterations": it, "converged": converged}


def tangent_coordinates(aligned: np.ndarray, mean: np.ndarray) -> tuple[np.ndarray, float]:
    """Coordenadas tangentes aplanadas (n, k·m) y ρ máxima a la media (control de validez)."""
    m = preshape(mean)
    a = np.asarray(aligned, dtype=float)
    flat_m = m.ravel()
    out = np.empty((len(a), flat_m.size))
    rho_max = 0.0
    for i, x in enumerate(a):
        v = x.ravel()
        out[i] = v - (v @ flat_m) * flat_m
        rho_max = max(rho_max, procrustes_distances(x, m)["rho"])
    return out, rho_max


# ---------------------------------------------------------------- trayectorias
def angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    """Ángulo entre dos vectores (grados, en [0, 180])."""
    u = np.asarray(u, dtype=float).ravel()
    v = np.asarray(v, dtype=float).ravel()
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        raise ValueError("vector nulo")
    return math.degrees(math.acos(min(max(float(u @ v) / (nu * nv), -1.0), 1.0)))


def allometry_vector(shape: np.ndarray, log_size: np.ndarray) -> np.ndarray:
    """Pendiente de la regresión multivariada de la forma (n, p) sobre log(CS) (n,): vector (p,)."""
    y = np.asarray(shape, dtype=float)
    x = np.asarray(log_size, dtype=float).ravel()
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("se necesitan ≥ 3 observaciones con forma y tamaño")
    xc = x - x.mean()
    sxx = float(xc @ xc)
    if sxx == 0:
        raise ValueError("el tamaño no varía")
    return xc @ (y - y.mean(axis=0)) / sxx


def random_angle_quantile(dim: int, q: float, n: int = 20000, seed: int = 0) -> float:
    """Cuantil q del ángulo sin signo (grados, en [0, 90]) entre dos rectas aleatorias uniformes en R^dim.

    Referencia nula para decir si dos vectores de forma están más alineados que por azar. Para
    compararlo con ``angle_deg`` (con signo, [0, 180]) use min(θ, 180 − θ).
    """
    if dim < 2:
        raise ValueError("dim ≥ 2")
    rng = np.random.default_rng(seed)
    u = rng.normal(size=(n, dim))
    v = rng.normal(size=(n, dim))
    c = np.einsum("ij,ij->i", u, v) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1))
    return float(np.quantile(np.degrees(np.arccos(np.clip(np.abs(c), 0, 1))), q))


def correspondence_check(a: np.ndarray, b: np.ndarray, n_perm: int = 200, seed: int = 0) -> dict:
    """¿El punto i de ``a`` corresponde al punto i de ``b``? Compara ρ con el orden dado frente a
    órdenes barajados. Una ρ observada muy por debajo del mínimo barajado es evidencia de
    correspondencia; no prueba homología anatómica."""
    rng = np.random.default_rng(seed)
    obs = procrustes_distances(a, b)["rho"]
    perm = [procrustes_distances(a, np.asarray(b)[rng.permutation(len(b))])["rho"] for _ in range(n_perm)]
    return {"rho_observed": obs, "rho_permuted_min": float(min(perm)),
            "rho_permuted_median": float(np.median(perm)),
            "corresponds": bool(obs < min(perm))}
