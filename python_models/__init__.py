"""Python equivalents of the Primal Overlay physiology models.

Each function mirrors the signature used by the APL dfns: ``model(mode, t, x, theta, overlay=None)``
where ``overlay`` is an optional iterable containing up to three callables ``(R, M, U)`` for residual,
parameter modulation, and control inputs respectively.
"""
from __future__ import annotations

from math import log, pi
from typing import Callable, Iterable, Optional, Sequence, Tuple

Mode = str
OverlayIterable = Optional[Iterable[Optional[Callable]]]


def _normalize_mode(mode: Mode) -> str:
    return str(mode).strip().lower()


def _default_residual(x: float, t: float) -> float:
    return 0.0


def _default_modulation(x: float, t: float) -> float:
    return 1.0


def _default_control(t: float) -> float:
    return 0.0


def _resolve_overlay(overlay: OverlayIterable) -> Tuple[
    Callable[[float, float], float],
    Callable[[float, float], float],
    Callable[[float], float],
]:
    if overlay is None:
        return _default_residual, _default_modulation, _default_control

    sequence: Sequence[Optional[Callable]] = tuple(overlay)
    residual = sequence[0] if len(sequence) > 0 and sequence[0] is not None else _default_residual
    modulation = sequence[1] if len(sequence) > 1 and sequence[1] is not None else _default_modulation
    control = sequence[2] if len(sequence) > 2 and sequence[2] is not None else _default_control
    return residual, modulation, control


# Michaelis–Menten -----------------------------------------------------------

def michaelis_menten(
    mode: Mode,
    t: float,
    x: Sequence[float],
    theta: Sequence[float],
    overlay: OverlayIterable = None,
) -> Tuple[float, float]:
    """Michaelis–Menten kinetics with overlay hooks."""
    residual, modulation, control = _resolve_overlay(overlay)
    S = x[0]
    Vmax, Km = theta

    if _normalize_mode(mode) == "parammod":
        Vmax *= modulation(S, t)

    v = Vmax * S / (Km + S)
    norm_mode = _normalize_mode(mode)

    if norm_mode == "residual":
        v += residual(S, t)
    elif norm_mode == "control":
        v += control(t)

    return -v, v


# SIR -----------------------------------------------------------------------

def sir(
    mode: Mode,
    t: float,
    x: Sequence[float],
    theta: Sequence[float],
    overlay: OverlayIterable = None,
) -> Tuple[float, float, float]:
    """Susceptible–Infected–Recovered dynamics with overlay hooks."""
    residual, modulation, control = _resolve_overlay(overlay)
    S, I, Rc = x
    beta, gamma, N = theta

    if _normalize_mode(mode) == "parammod":
        beta *= modulation(I, t)

    inf = beta * S * I / N
    rec = gamma * I

    dS = -inf
    dI = inf - rec
    dRc = rec

    norm_mode = _normalize_mode(mode)
    if norm_mode == "residual":
        dS += residual(S, t)
        dI += residual(I, t)
        dRc += residual(Rc, t)
    elif norm_mode == "control":
        dI += control(t)

    return dS, dI, dRc


# FitzHugh–Nagumo -----------------------------------------------------------

def fitzhugh_nagumo(
    mode: Mode,
    t: float,
    x: Sequence[float],
    theta: Sequence[float],
    overlay: OverlayIterable = None,
) -> Tuple[float, float]:
    """FitzHugh–Nagumo neuron oscillator with overlay hooks."""
    residual, modulation, control = _resolve_overlay(overlay)
    v, w = x
    a, b, c = theta

    norm_mode = _normalize_mode(mode)
    if norm_mode == "parammod":
        a *= modulation(v, t)
        b *= modulation(w, t)

    dv = v - v ** 3 / 3.0 - w
    dw = (v + a - b * w) / c

    if norm_mode == "residual":
        dv += residual(v, t)
        dw += residual(w, t)
    elif norm_mode == "control":
        dv += control(t)

    return dv, dw


# Nernst --------------------------------------------------------------------

def nernst(
    mode: Mode,
    t: float,
    x: Sequence[float],
    theta: Sequence[float],
    overlay: OverlayIterable = None,
) -> Tuple[float]:
    """Nernst membrane potential relaxation with overlay hooks."""
    residual, modulation, control = _resolve_overlay(overlay)
    (E,) = x
    T, z, Co, Ci = theta
    Rgas = 8.314_462_618
    F = 96_485.332_12

    norm_mode = _normalize_mode(mode)
    if norm_mode == "parammod":
        T *= modulation(E, t)

    EN = (Rgas * T / (z * F)) * log(Co / Ci)
    k = 10.0
    dE = k * (EN - E)

    if norm_mode == "residual":
        dE += residual(E, t)
    elif norm_mode == "control":
        dE += control(t)

    return (dE,)


# Poiseuille ----------------------------------------------------------------

def poiseuille(
    mode: Mode,
    t: float,
    x: Sequence[float],
    theta: Sequence[float],
    overlay: OverlayIterable = None,
) -> Tuple[float]:
    """Poiseuille flow relaxation with overlay hooks."""
    residual, modulation, control = _resolve_overlay(overlay)
    (Q,) = x
    dP, mu, L, r = theta

    norm_mode = _normalize_mode(mode)
    if norm_mode == "parammod":
        r *= modulation(Q, t)

    Qss = (pi * r ** 4 * dP) / (8.0 * mu * L)
    k = 5.0
    dQ = k * (Qss - Q)

    if norm_mode == "residual":
        dQ += residual(Q, t)
    elif norm_mode == "control":
        dQ += control(t)

    return (dQ,)


__all__ = [
    "michaelis_menten",
    "sir",
    "fitzhugh_nagumo",
    "nernst",
    "poiseuille",
]
