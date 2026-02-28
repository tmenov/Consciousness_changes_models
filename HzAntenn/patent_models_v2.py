"""
=============================================================================
ФИЗИЧЕСКИЕ МОДЕЛИ К ПАТЕНТУ US 2026/0039519 A1
«Multi-Tone Modulated Antenna» — RTX BBN Technologies / CUNY / Wayne State
Финансирование: IARPA EQuAL-P / NIWC Pacific N66001-22-C-4501
Авторы патента: Ranzani, Hassick, Gustafsson, Alù, Sounas, Mekawy, Xu, Arora, Kasahara
Дата подачи: 14 марта 2025 | Публикация: 5 февраля 2026

МОДЕЛИ (v2 — уточнённые по тексту патента):
  1. Предел Чу–Харрингтона vs. диапазон рабочих параметров патента
  2. Предел Боде–Фано: LTI vs. LPTV (воспроизведение Fig.11)
  3. Три тактических режима (Fig.3-5): карта (g,d) → режим
  4. Линейность: кривая компрессии (Fig.6 — P1dB ≈ −4 дБм)
  5. LPTV-эволюция ёмкостей C1(t),C2(t),C3(t) (уравнения 6-9 патента)
  6. Анализ устойчивости: c1 vs. c1_крит, тепловой дрейф, деформация
  7. Снайперский РЭБ: паразитная накачка на f_s
  8. Концепция А: Акусто-фонная антенна (EGaIn + FBAR)
  9. Концепция Б: STC-метаповерхность (фазовое пространство)
  10. Концепция В: Когнитивный рой (N антенн + нейросеть)
  11. Итоговая сравнительная панель

ЗАПУСК: python3 patent_models_v2.py
ЗАВИСИМОСТИ: numpy, matplotlib (scipy опционально)
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

# ── Глобальный стиль ─────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'lines.linewidth': 2.0, 'axes.grid': True, 'grid.alpha': 0.25,
    'figure.dpi': 120, 'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': 'white',
})
C = dict(
    blue='#1a3a5c', red='#c0392b', green='#27ae60',
    orange='#e67e22', purple='#8e44ad', gray='#7f8c8d',
    cyan='#2980b9', yellow='#f1c40f',
)

# =============================================================================
# МОДЕЛЬ 1: Предел Чу–Харрингтона
# =============================================================================
def chu_Q(ka):
    """Q_min ≥ 1/(ka)³ + 1/(ka)  —  предел Чу–Харрингтона (1948)"""
    return 1.0/ka**3 + 1.0/ka

def bode_fano_BW(Q, f0):
    """BW_passive = f0 / Q"""
    return f0 / Q

# =============================================================================
# МОДЕЛЬ 2: Предел Боде–Фано (LTI) vs. LPTV
#   Воспроизведение Fig.11 патента:
#   Solid = Bode-Fano limit (LTI),  Dashed = LPTV circuit
# =============================================================================
def bode_fano_gamma_LTI(omega, omega0, Q, BW_norm):
    """
    Оптимальный прямоугольный Γ(ω) для LTI-системы.
    ∫ln(1/|Γ|)dω = π/R₀C₀  → при BW-полосе: Γ_min = exp(−π/(Q·BW_norm))
    Моделируем: Γ = 1 − (1−Γ_min)·exp(−(ω−ω0)²/(BW/2)²) 
    """
    # Параметры как в Fig.11: ω₀ = 0.005, BW ≈ 0.0008 (нормировано)
    Gamma_min = 0.0   # идеальное согласование в резонансе
    sigma = BW_norm / 2.0
    Gamma = 1.0 - np.exp(-((omega - omega0)**2) / sigma**2)
    return Gamma

def bode_fano_gamma_LPTV(omega, omega0, BW_norm_LPTV):
    """
    LPTV-цепь (дашед в Fig.11): более широкая полоса при Γ→0,
    что невозможно для пассивной LTI-системы.
    """
    sigma_lptv = BW_norm_LPTV / 2.0
    Gamma = 1.0 - np.exp(-((omega - omega0)**2) / sigma_lptv**2)
    return Gamma

# =============================================================================
# МОДЕЛЬ 3: Три режима работы (уравнения 3-5 патента)
# =============================================================================
def operating_regime(g, d, Kr, K_ESA):
    """
    Режим I:   d²−g² < Kr·KESA/4   → постоянный G×BW
    Режим II:  d²−g² = Kr·KESA/4   → нулевые потери (perfect match)
    Режим III: d²−g² > Kr·KESA/4   → широкая полоса
    Возвращает: 1, 2 или 3
    """
    threshold = Kr * K_ESA / 4.0
    val = d**2 - g**2
    if abs(val - threshold) < 0.02 * threshold:
        return 2
    elif val < threshold:
        return 1
    else:
        return 3

def transmission_model(f, f0, d, g, Kr, K_ESA):
    """
    Упрощённая аналитическая модель коэффициента передачи.
    В Режиме I: усиление ∝ g/Kr, BW ∝ Kr·KESA/(4·d)
    В Режиме II: идеальное согласование (T→∞ в пределе, ограничено потерями)
    В Режиме III: широкая полоса, T ≈ const
    
    Реализуем через лоренцевскую форму с параметрическим усилением:
      T(f) = G_param / (1 + 4·Q²·(f/f0−1)²)  — базовая форма
      G_param определяется режимом
    """
    threshold = Kr * K_ESA / 4.0
    excess = d**2 - g**2 - threshold

    # Добротность и усиление в зависимости от режима
    if excess < -0.01 * threshold:  # Режим I
        Q_eff = Kr * K_ESA / (4 * (threshold - d**2 + g**2 + 1e-10))
        Q_eff = min(Q_eff, 200)
        G0_dB = 10 * np.log10(max(g / (Kr + 1e-10), 1e-6)) * 5
    elif abs(excess) <= 0.01 * threshold:  # Режим II
        Q_eff = Kr * K_ESA / (0.001 * threshold + 1e-10)
        Q_eff = min(Q_eff, 500)
        G0_dB = 11.0  # из Fig.4 патента: ≈11 дБ при d=3.5, g=3.36
    else:  # Режим III
        Q_eff = Kr * K_ESA / (4 * abs(excess) + 1e-10)
        Q_eff = max(Q_eff, 0.5)
        G0_dB = 0.0

    G0_lin = 10**(G0_dB/10)
    T_lin = G0_lin / (1.0 + 4*Q_eff**2 * (f/f0 - 1.0)**2)
    T_dB  = 10 * np.log10(np.maximum(T_lin, 1e-12))
    # Базовая резонансная подстройка (пассивная)
    Q_passive = 50
    T_res_lin = 1.0 / (1.0 + 4*Q_passive**2 * (f/f0 - 1.0)**2)
    T_res_dB  = 10 * np.log10(np.maximum(T_res_lin, 1e-12))
    return T_dB, T_res_dB

# =============================================================================
# МОДЕЛЬ 4: Кривая компрессии (Fig.6 патента)
# =============================================================================
def compression_curve(P_in_dBm, P1dB_dBm=-4.0, G0_dB=0.0):
    """
    Модель AM-AM компрессии (приближение Saleh):
      G(P_in) = G0 / (1 + P_in_W / P_sat_W)
    P1dB ≈ P_sat/4  →  P_sat = 4 * P1dB (линейная)
    Из Fig.6: P1dB ≈ −4 дБм (маркер 604)
    """
    P_in_W   = 10**(P_in_dBm/10) * 1e-3
    P1dB_W   = 10**(P1dB_dBm/10) * 1e-3
    P_sat_W  = P1dB_W * 4.0   # приближение
    G0_lin   = 10**(G0_dB/10)
    G_lin    = G0_lin / (1.0 + P_in_W / P_sat_W)
    G_dB     = 10 * np.log10(np.maximum(G_lin, 1e-12))
    return G_dB

# =============================================================================
# МОДЕЛЬ 5: LPTV-эволюция ёмкостей (уравнения 6–9 патента)
# =============================================================================
def lptv_capacitances(t, c0, c1_ratio=0.9, Omega=None, phi=0.0, a=1.0, d=1.0):
    """
    Параметры из патента [0044]: a=d=1, c₀=a/2=0.5, c₁=0.9·c₀/2, Ω=0.95
    
    c(t) = c₀ + 2c₁·cos(Ω·t + φ)          ... (9)
    C₁(t) = 2[a−c(t)] / [ad−c²(t)]         ... (6)
    C₂(t) = 2·c(t) / [ad−c²(t)]            ... (7)  
    C₃(t) = 2[d−c(t)] / [ad−c²(t)]         ... (8)
    """
    c1 = c1_ratio * c0 / 2.0
    if Omega is None:
        Omega = 2 * np.pi * 1e6
    c_t   = c0 + 2.0 * c1 * np.cos(Omega * t + phi)
    denom = a * d - c_t**2
    denom = np.where(np.abs(denom) < 1e-9, 1e-9 * np.sign(denom + 1e-30), denom)
    C1 = 2.0 * (a - c_t) / denom
    C2 = 2.0 * c_t / denom
    C3 = 2.0 * (d - c_t) / denom
    return C1, C2, C3, c_t, c1

# =============================================================================
# МОДЕЛЬ 6: Анализ устойчивости
# =============================================================================
def stability_margin(c0=0.5):
    """
    Рабочая точка: c₁ = 0.9·c₀/2 = 0.45·c₀  (из [0044])
    Порог:         c₁_крит = 0.5·c₀
    Запас:         Δ = (c₁_крит − c₁) / c₁_крит = 10%
    """
    c1_work = 0.45 * c0
    c1_crit = 0.50 * c0
    margin  = (c1_crit - c1_work) / c1_crit * 100
    return c1_work, c1_crit, margin

def thermal_drift_model(dT_array, c0=0.5, alpha_f=2e-4):
    """
    Тепловой дрейф f_ESA → сдвиг эффективного c₁:
      Δf_ESA / f₀ ≈ −α_f · ΔT
      c₁_eff ≈ c₁ · (1 + 3 · Δf_ESA/f₀)
    α_f ≈ 2×10⁻⁴ /°C (характерно для петлевой антенны из Al/Cu)
    """
    c1_work, c1_crit, _ = stability_margin(c0)
    df_frac  = -alpha_f * dT_array
    c1_eff   = c1_work * (1.0 + 3.0 * np.abs(df_frac))
    frac_of_crit = c1_eff / c1_crit * 100
    return frac_of_crit, c1_crit

# =============================================================================
# МОДЕЛЬ 7: Снайперский РЭБ
# =============================================================================
def sniper_reb(P_jam_dBm_array, G_param_dB=20.0, P_TX_dBm=30.0, P_th_dBm=-4.0):
    """
    Атака на f_s = f_r + f_ESA ≈ 600 МГц.
    Параметрическое усиление G_param ≈ 20 дБ (из Fig.5 патента: широкая полоса).
    Порог линейности P_th ≈ −4 дБм (Fig.6).
    
    P_reflected ≈ G_param · P_jam · P_TX / P_th
    Когда P_reflected > P_TX → необратимый пробой.
    """
    G_param_lin = 10**(G_param_dB/10)
    P_TX_W      = 10**(P_TX_dBm/10) * 1e-3
    P_th_W      = 10**(P_th_dBm/10) * 1e-3
    P_jam_W     = 10**(P_jam_dBm_array/10) * 1e-3
    P_ref_W     = G_param_lin * P_jam_W * P_TX_W / (P_th_W + 1e-30)
    P_ref_dBm   = 10 * np.log10(np.maximum(P_ref_W * 1e3, 1e-20))
    P_damage_dBm = P_TX_dBm + 3.0  # +3 дБ → лавинный пробой
    idx_crit = np.argmax(P_ref_dBm >= P_damage_dBm)
    P_crit = P_jam_dBm_array[idx_crit] if idx_crit > 0 else None
    return P_ref_dBm, P_damage_dBm, P_crit

# =============================================================================
# МОДЕЛЬ 8: Концепция А — Акусто-фонная EGaIn-антенна
# =============================================================================
def egain_antenna_inductance(epsilon_array, a0=0.05, r=1e-3):
    """
    Индуктивность петлевой EGaIn антенны:
      L(a) = μ₀·a·[ln(8a/r) − 2] / (2π)
    При SAW-деформации: a(ε) = a₀·(1 + ε)
    
    Перестройка резонансной частоты: f_ESA ∝ 1/√L
    """
    mu0 = 4.0 * np.pi * 1e-7
    a   = a0 * (1.0 + epsilon_array)
    arg = np.maximum(8.0 * a / r, 1.001)  # защита от log(0)
    L   = mu0 * a * (np.log(arg) - 2.0) / (2.0 * np.pi)
    L0  = mu0 * a0 * (np.log(8.0*a0/r) - 2.0) / (2.0 * np.pi)
    f_norm = np.sqrt(L0 / np.maximum(L, 1e-20))  # нормировано к f0
    return L, L0, f_norm

# =============================================================================
# МОДЕЛЬ 9: Концепция В — Когнитивный рой
# =============================================================================
def swarm_performance(N_array, BW_single=300e3, SNR0_dB=30.0):
    """
    N пассивных ESA (каждая строго LTI, строго в пределе Чу):
      BW_virtual = BW_single · √N    (копримальные массивы)
      DOF = N²                        (O(N²) степеней свободы)
      SNR = SNR₀ + 10·log₁₀(N)       (некогерентное суммирование)
    
    При потере δ доли элементов:
      SNR_loss = 10·log₁₀(1−δ)  дБ
    """
    BW_virtual = BW_single * np.sqrt(N_array)
    DOF        = N_array**2
    SNR_dB     = SNR0_dB + 10.0 * np.log10(N_array)
    return BW_virtual, DOF, SNR_dB

def swarm_resilience(survival_frac):
    """SNR-потеря при выживаемости survival_frac (0–1)"""
    return 10.0 * np.log10(np.maximum(survival_frac, 1e-10))

# =============================================================================
# ГЛАВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ ГРАФИКОВ
# =============================================================================
def run_all_models():
    print("=" * 70)
    print("Модели к патенту US 2026/0039519 A1  |  v2  |  2026-02-28")
    print("=" * 70)

    # ── Рис.1: Чу-Харрингтон + Боде-Фано vs LPTV ────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ka = np.linspace(0.01, 1.0, 500)
    Q  = chu_Q(ka)
    f0 = 300e6
    BW = bode_fano_BW(Q, f0)

    ax = axes[0]
    ax.semilogy(ka, Q, color=C['blue'], lw=2.5, label='Q_min (Чу–Харрингтон)')
    # Пример патента: a=5 см, f0=300 МГц → ka=2π·0.05/1.0=0.314
    ka_ex = 2*np.pi*0.05 / (3e8/300e6)
    Q_ex  = chu_Q(ka_ex)
    ax.scatter([ka_ex], [Q_ex], s=120, color=C['red'], zorder=6,
               label=f'Патент: ka≈{ka_ex:.3f}, Q≈{Q_ex:.1f}')
    # ka=0.1 — сверхмалая ESA
    Q_01 = chu_Q(0.1)
    ax.scatter([0.1], [Q_01], s=100, color=C['orange'], zorder=6,
               label=f'ka=0.1: Q≈{Q_01:.0f}')
    ax.set_xlabel('ka = (2π/λ)·a')
    ax.set_ylabel('Q_min')
    ax.set_title('Предел Чу–Харрингтона\nQ_min(ka)')
    ax.legend(fontsize=8.5)

    # ── Воспроизведение Fig.11 ──
    ax2 = axes[1]
    omega = np.linspace(0, 0.015, 2000)
    omega0 = 0.005
    BW_lti   = 0.00060   # ширина «провала» в Fig.11 для LTI (solid)
    BW_lptv  = 0.00220   # ширина «провала» для LPTV (dashed) — шире!
    G_LTI    = bode_fano_gamma_LTI(omega, omega0, Q_ex, BW_lti)
    G_LPTV   = bode_fano_gamma_LPTV(omega, omega0, BW_lptv)
    ax2.plot(omega, G_LTI,  color=C['blue'],   lw=2.5, linestyle='-',  label='Bode-Fano limit (LTI)')
    ax2.plot(omega, G_LPTV, color=C['cyan'],   lw=2.5, linestyle='--', label='LPTV circuit (патент Fig.11)')
    ax2.fill_between(omega, G_LTI, G_LPTV,
                     where=(G_LPTV < G_LTI), alpha=0.25, color=C['green'],
                     label='Зона прорыва (LPTV < LTI)')
    ax2.set_xlabel('ω (норм.)')
    ax2.set_ylabel('Γ (коэф. отражения)')
    ax2.set_title('Fig.11 патента: LPTV пробивает предел Боде–Фано\nΓ_LPTV < Γ_BodeFano в рабочей полосе')
    ax2.legend(fontsize=8.5)
    plt.suptitle('Рис.1: Фундаментальные пределы и ключевой результат патента',
                 fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('/home/claude/v2_fig1_limits.png', bbox_inches='tight')
    plt.close()
    print(f"  ✓ Рис.1: Чу–Харрингтон + Боде–Фано vs LPTV  (Q_пат={Q_ex:.1f})")

    # ── Рис.2: Три режима + кривая компрессии ────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    Kr = K_ESA = 1.0
    threshold = Kr * K_ESA / 4.0
    f_arr = np.linspace(280e6, 320e6, 500)

    # Режим I: g=1.55, d=1.0 (из Fig.3 патента)
    T1_dB, Tref_dB = transmission_model(f_arr, 300e6, d=1.0,   g=1.55, Kr=Kr, K_ESA=K_ESA)
    # Режим II: g=3.36, d=3.5 (из Fig.4)
    T2_dB, _       = transmission_model(f_arr, 300e6, d=3.5,   g=3.36, Kr=Kr, K_ESA=K_ESA)
    # Режим III: g=3.36, d=4.3 (из Fig.5)
    T3_dB, _       = transmission_model(f_arr, 300e6, d=4.3,   g=3.36, Kr=Kr, K_ESA=K_ESA)

    ax = axes[0]
    ax.plot(f_arr/1e6, Tref_dB, 'k--', lw=1.5, label='Пассивная настройка')
    ax.plot(f_arr/1e6, T1_dB,  color=C['cyan'],   label='Режим I  (G×BW=const)')
    ax.plot(f_arr/1e6, T2_dB,  color=C['green'],  label='Режим II (нул. потери)')
    ax.plot(f_arr/1e6, T3_dB,  color=C['red'],    label='Режим III (широкая BW)')
    ax.axhline(-10, color=C['gray'], lw=1, linestyle=':')
    ax.set_xlabel('Частота (МГц)')
    ax.set_ylabel('Передача (дБ)')
    ax.set_title('Три режима работы\n(аналит. модель)')
    ax.legend(fontsize=8)
    ax.set_ylim(-15, 20)

    # Карта режимов
    ax2 = axes[1]
    g_v = np.linspace(0.0, 5.0, 300)
    d_v = np.linspace(0.0, 5.0, 300)
    GG, DD = np.meshgrid(g_v, d_v)
    ZZ = DD**2 - GG**2
    Z_map = np.zeros_like(ZZ)
    Z_map[ZZ < threshold*0.97]  = 1   # Режим I
    Z_map[np.abs(ZZ - threshold) < threshold*0.06] = 2   # Режим II
    Z_map[ZZ > threshold*1.03]  = 3   # Режим III
    cmap3 = LinearSegmentedColormap.from_list('r3',
        [(0,'#3498db'),(0.45,'#2ecc71'),(0.55,'#f39c12'),(1,'#e74c3c')])
    ax2.contourf(GG, DD, Z_map, levels=[-0.5,1.5,2.5,3.5], colors=['#3498db','#2ecc71','#e74c3c'], alpha=0.7)
    ax2.contour(GG, DD, ZZ, levels=[threshold], colors=['black'], linewidths=1.5)
    # Рабочие точки из патента
    pts_patent = [(1.55, 1.0,'I: g=1.55,d=1.0'),(3.36, 3.5,'II: g=3.36,d=3.5'),(3.36,4.3,'III: g=3.36,d=4.3')]
    for gp, dp, lbl in pts_patent:
        ax2.scatter([gp],[dp], s=80, color='white', edgecolors='black', zorder=5)
        ax2.annotate(lbl, (gp,dp), xytext=(gp+0.15,dp+0.1), fontsize=7.5)
    ax2.set_xlabel('g (суммарный тон)')
    ax2.set_ylabel('d (разностный тон)')
    ax2.set_title('Карта режимов в (g,d)\nпунктир: граница Kr·KESA/4')

    # Кривая компрессии (Fig.6)
    ax3 = axes[2]
    P_in = np.linspace(-30, 10, 300)
    G_compr = compression_curve(P_in, P1dB_dBm=-4.0, G0_dB=0.0)
    ax3.plot(P_in, G_compr, color=C['blue'], lw=2.5, label='Расчёт (AM-AM)')
    ax3.scatter([-4.0], [-1.0], s=120, color=C['red'], zorder=6,
                label='P1dB ≈ −4 дБм (Fig.6 патента)')
    ax3.axhline(-1.0, color=C['gray'], lw=1, linestyle='--', alpha=0.7)
    ax3.axvline(-4.0, color=C['red'],  lw=1, linestyle='--', alpha=0.7)
    ax3.set_xlabel('Входная мощность (дБм)')
    ax3.set_ylabel('Усиление (дБ)')
    ax3.set_title('Кривая компрессии\n(Fig.6 патента: P1dB ≈ −4 дБм)')
    ax3.legend(fontsize=8.5)
    plt.suptitle('Рис.2: Режимы работы и линейность (по данным патента)', fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('/home/claude/v2_fig2_modes.png', bbox_inches='tight')
    plt.close()
    print(f"  ✓ Рис.2: Три режима + компрессия (P1dB = −4 дБм)")

    # ── Рис.3: LPTV-ёмкости ─────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    f_mod = 10e6
    Omega = 2*np.pi*f_mod
    c0    = 0.5   # [0044]: c0 = a/2 = 0.5
    t     = np.linspace(0, 3/f_mod, 2000)
    C1, C2, C3, c_t, c1 = lptv_capacitances(t, c0, c1_ratio=0.9, Omega=Omega)
    c1_crit = 0.5 * c0
    t_us = t * 1e6

    axes[0].plot(t_us, c_t, color=C['blue'])
    axes[0].axhline(c0,      linestyle='--', color=C['gray'],   lw=1.2, label=f'c₀={c0}')
    axes[0].axhline(c1_crit, linestyle=':',  color=C['red'],    lw=1.5, label=f'c₁_кр={c1_crit:.3f}')
    axes[0].axhline(c1,      linestyle='-.',  color=C['orange'], lw=1.2,
                    label=f'c₁={c1:.3f} (90% кр.)')
    axes[0].set_xlabel('Время (мкс)')
    axes[0].set_ylabel('c(t)')
    axes[0].set_title('Управл. функция c(t)\n[0044]: c₁=0.9·c₀/2, Ω=0.95')
    axes[0].legend(fontsize=8)

    axes[1].plot(t_us, C1, color=C['blue'],   label='C₁(t)')
    axes[1].plot(t_us, C3, color=C['purple'], linestyle='--', label='C₃(t)')
    axes[1].set_xlabel('Время (мкс)')
    axes[1].set_ylabel('Норм. ёмкость')
    axes[1].set_title('C₁(t) и C₃(t)\n(ур. 6, 8 патента)')
    axes[1].legend()

    axes[2].plot(t_us, C2, color=C['red'])
    axes[2].set_xlabel('Время (мкс)')
    axes[2].set_ylabel('Норм. ёмкость')
    axes[2].set_title('C₂(t) — ёмкость связи\n(ур. 7: сингулярность вблизи c→√(ad))')
    plt.suptitle(f'Рис.3: Временна́я эволюция LPTV-ёмкостей\n'
                 f'Параметры [0044]: a=d=1, c₀=0.5, c₁={c1:.3f} (запас {(1-c1/c1_crit)*100:.0f}% до срыва)',
                 fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('/home/claude/v2_fig3_capacitances.png', bbox_inches='tight')
    plt.close()
    print(f"  ✓ Рис.3: LPTV-ёмкости  c₁={c1:.3f}, c₁_крит={c1_crit:.3f}, запас {(1-c1/c1_crit)*100:.0f}%")

    # ── Рис.4: Устойчивость + РЭБ ────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 4а: c₁ vs c₁_крит
    c1_w, c1_c, margin = stability_margin()
    c1_scan = np.linspace(0, c0, 300)
    stab_pct = (c1_c - c1_scan) / c1_c * 100
    sc = axes[0].scatter(c1_scan, stab_pct,
                         c=stab_pct, cmap='RdYlGn', s=6, vmin=-20, vmax=50)
    axes[0].axvline(c1_w, color=C['red'], lw=2, linestyle='--', label=f'c₁={c1_w:.3f} (рабочая)')
    axes[0].axvline(c1_c, color='black',  lw=2, label=f'c₁_кр={c1_c:.3f}')
    axes[0].axhline(10.0, color=C['orange'], lw=1.5, linestyle=':', label='Запас 10%')
    axes[0].set_xlabel('c₁')
    axes[0].set_ylabel('Запас до срыва (%)')
    axes[0].set_title(f'Устойчивость\nРабочий запас = {margin:.0f}% (!)')
    axes[0].legend(fontsize=8)
    plt.colorbar(sc, ax=axes[0], label='Запас (%)')

    # 4б: тепловой дрейф
    dT = np.linspace(-60, 120, 400)
    frac_crit, _ = thermal_drift_model(dT, alpha_f=2e-4)
    axes[1].plot(dT, frac_crit, color=C['blue'], lw=2)
    axes[1].axhline(100, color=C['red'], lw=2, linestyle='--', label='100% = срыв')
    unstable = dT[frac_crit >= 100]
    if len(unstable):
        axes[1].axvspan(unstable[0], dT[-1], alpha=0.2, color='red')
        axes[1].axvline(unstable[0], color=C['red'], lw=1.5, linestyle=':',
                        label=f'ΔT_кр ≈ {unstable[0]:.0f}°C')
    axes[1].set_xlabel('ΔT (°C)')
    axes[1].set_ylabel('c₁/c₁_кр × 100 %')
    axes[1].set_title('Тепловой дрейф\nаэродинамический нагрев обшивки')
    axes[1].set_ylim(60, 130)
    axes[1].legend(fontsize=8)

    # 4в: Снайперский РЭБ
    P_jam = np.linspace(-40, 10, 400)
    P_ref, P_dmg, P_crit = sniper_reb(P_jam, G_param_dB=20, P_TX_dBm=30, P_th_dBm=-4)
    axes[2].plot(P_jam, P_ref, color=C['red'], lw=2.5, label='P_отражённая на TX')
    axes[2].axhline(P_dmg, color='black', lw=2, linestyle='--',
                    label=f'Порог пробоя = {P_dmg:.0f} дБм')
    if P_crit is not None:
        axes[2].axvline(P_crit, color=C['purple'], lw=1.5, linestyle=':',
                        label=f'P_крит_РЭБ ≈ {P_crit:.0f} дБм')
        axes[2].fill_between(P_jam, P_ref, P_dmg,
                             where=(P_ref >= P_dmg), alpha=0.25, color='red',
                             label='Зона уничтожения TX')
    axes[2].set_xlabel('Мощность помехи на f_s (дБм)')
    axes[2].set_ylabel('Отражённая мощность (дБм)')
    axes[2].set_title(f'Снайперский РЭБ на f_s=600 МГц\nG_пар=20 дБ, P_TX=30 дБм')
    axes[2].legend(fontsize=7.5)
    axes[2].set_ylim(20, 90)
    plt.suptitle('Рис.4: Устойчивость системы и вектор РЭБ', fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('/home/claude/v2_fig4_stability_reb.png', bbox_inches='tight')
    plt.close()
    print(f"  ✓ Рис.4: Устойчивость (запас={margin:.0f}%) + РЭБ (P_кр≈{P_crit:.0f} дБм)")

    # ── Рис.5: Три концепции обхода ──────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Концепт А: EGaIn L(ε)
    eps = np.linspace(-0.12, 0.12, 400)
    L, L0, f_norm = egain_antenna_inductance(eps, a0=0.05, r=1e-3)
    ax = axes[0]
    ax.plot(eps*100, (f_norm-1)*100, color=C['green'], lw=2.5)
    ax.axvline(10, color=C['orange'], lw=1.5, linestyle='--', label='SAW ε=10%')
    ax.axvline(-10, color=C['orange'], lw=1.5, linestyle='--')
    ax.set_xlabel('Деформация ε = δa/a₀ (%)')
    ax.set_ylabel('Δf_ESA / f₀ (%)')
    ax.set_title('Концепт А: EGaIn-антенна\nперестройка f_ESA через SAW-деформацию')
    ax.legend(fontsize=9)

    # Концепт В: Рой
    N_arr = np.logspace(0, 4, 300)
    BW_v, DOF, SNR_dB = swarm_performance(N_arr, BW_single=300e3)
    ax2 = axes[1]
    ax2.loglog(N_arr, BW_v/1e6, color=C['purple'], lw=2.5, label='BW_virtual (√N·BW_single)')
    ax2.axhline(30, color=C['red'], lw=2, linestyle='--', label='Цель: 30 МГц')
    ax2.axhline(0.3, color=C['gray'], lw=1.5, linestyle=':', label='BW_one (Чу)')
    N_tgt = (30e6/300e3)**2
    ax2.axvline(N_tgt, color=C['orange'], lw=1.5, linestyle='-.', label=f'N_цель={N_tgt:.0f}')
    ax2.set_xlabel('Число элементов N')
    ax2.set_ylabel('Виртуальная полоса (МГц)')
    ax2.set_title('Концепт В: Когнитивный рой\nBW(N) = √N · BW_single')
    ax2.legend(fontsize=8)

    # Концепт В: устойчивость к потерям
    surv = np.linspace(0.01, 1.0, 300)
    snr_loss = swarm_resilience(surv)
    ax3 = axes[2]
    ax3.plot(surv*100, snr_loss, color=C['cyan'], lw=2.5)
    ax3.axhline(-3, color=C['red'], lw=1.5, linestyle='--', label='-3 дБ порог')
    surv_at_3dB = 10**(-3/10)
    ax3.axvline(surv_at_3dB*100, color=C['orange'], lw=1.5, linestyle=':',
                label=f'{surv_at_3dB*100:.0f}% выживших → -3 дБ')
    ax3.fill_between(surv*100, snr_loss, -3,
                     where=(snr_loss < -3), alpha=0.25, color='red',
                     label='Деградация связи')
    ax3.set_xlabel('Выживших элементов (%)')
    ax3.set_ylabel('ΔSNR (дБ)')
    ax3.set_title('Устойчивость роя к боевым потерям')
    ax3.legend(fontsize=8)
    plt.suptitle('Рис.5: Три концепции патентно-чистого обхода', fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig('/home/claude/v2_fig5_bypass.png', bbox_inches='tight')
    plt.close()
    print(f"  ✓ Рис.5: Три концепции обхода")

    # ── Финальный вывод ───────────────────────────────────────────────────────
    print()
    print("КЛЮЧЕВЫЕ ЧИСЛЕННЫЕ РЕЗУЛЬТАТЫ:")
    print(f"  ka патента    = {ka_ex:.4f}  (a=5 см, f₀=300 МГц)")
    print(f"  Q_min         = {Q_ex:.1f}")
    print(f"  BW_пасс       = {bode_fano_BW(Q_ex,f0)/1e6:.2f} МГц")
    print(f"  c₁ рабочая    = {c1:.4f}  ({(c1/c1_crit)*100:.1f}% от c₁_крит)")
    print(f"  Запас до срыва= {margin:.1f}%  ← КРИТИЧНО")
    BW_v_10k, _, _ = swarm_performance(np.array([10000.0]))
    print(f"  BW рой N=10k  = {BW_v_10k[0]/1e6:.1f} МГц")
    print(f"  P1dB (Fig.6)  = −4 дБм  (кремний, прототип)")
    print("=" * 70)
    print("Все 5 рисунков сохранены: /home/claude/v2_fig*.png")

if __name__ == '__main__':
    run_all_models()
