"""
Unified Python Model — US Patent 2026/0039519 A1
"Multi-Tone Modulated Antenna" | RTX BBN Technologies / CUNY / Wayne State
Synthesizes Model A (OOP coupled-mode, MultiToneAntenn.pdf) + Model B (direct patent params)
Dependencies: numpy, matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt

class LPTVAntennaUnified:
    """
    Unified model for US Patent 2026/0039519 A1.
    Combines coupled-mode theory (CMT) with direct patent parameters.
    """
    # ── Patent constants [0044] ──────────────────────────────────────────
    C0, A, D = 0.5, 1.0, 1.0           # normalized capacitor params
    C1 = 0.9 * 0.5 / 2.0               # = 0.225  operating c1
    C1_CRIT = 0.5 * 0.5                 # = 0.250  oscillation threshold
    STABILITY_MARGIN = (C1_CRIT - C1) / C1_CRIT * 100   # = 10.0 %

    def __init__(self, f_esa=300e6, f_r=300e6, q_esa=1000, q_r=100):
        self.f_esa, self.f_r = f_esa, f_r
        self.q_esa, self.q_r = q_esa, q_r
        # Linewidths (Hz) — Model A convention
        self.kappa_esa = f_esa / q_esa   # 300 kHz
        self.kappa_r   = f_r  / q_r      # 3 MHz
        self.threshold = self.kappa_r * self.kappa_esa / 4
        # Modulation frequencies
        self.f_sum  = f_r + f_esa        # 600 MHz (when f_r = f_esa)
        self.f_diff = abs(f_r - f_esa)   # 0 Hz (f_r = f_esa case)

    # ── Model A: CMT stability & reflection ──────────────────────────────
    def stability_margin_cmt(self, g, d):
        """Returns (metric - threshold). Positive = stable."""
        return d**2 - g**2 - self.threshold

    def reflection_cmt(self, freqs, g, d):
        """Coupled-mode heuristic |Gamma(f)|."""
        dk = (d**2 - g**2) / self.kappa_esa
        k_eff = np.maximum(self.kappa_esa + dk, 1e3)
        q_eff = self.f_esa / k_eff
        det   = (freqs - self.f_esa) / self.f_esa
        num   = 1j * 2 * q_eff * det
        return np.abs(num / (1 + num))

    def bode_integral(self, freqs, gamma):
        """Numerical Bode-Fano integral: integral of ln(1/|Gamma|) df"""
        g_safe = np.clip(gamma, 1e-6, 1.0)
        return np.trapz(np.log(1/g_safe), freqs)

    # ── Model B: direct patent capacitances ──────────────────────────────
    def lptv_capacitances(self, t, f_mod=10e6):
        """C1(t), C2(t), C3(t) from patent Eqs. 6-9 with params [0044]."""
        Omega = 2*np.pi*f_mod
        c_t   = self.C0 + 2*self.C1*np.cos(Omega*t)
        den   = self.A*self.D - c_t**2
        den   = np.where(np.abs(den)<1e-9, 1e-9, den)
        return 2*(self.A-c_t)/den, 2*c_t/den, 2*(self.D-c_t)/den, c_t

    # ── Thermal stability ──────────────────────────────────────────────────
    def thermal_stability(self, dT_array, alpha_f=2e-4):
        """
        c1_eff as function of temperature drift.
        alpha_f = 2e-4 /C is representative of copper loop antenna.
        Returns c1_eff/c1_crit * 100 (%) — crosses 100% = instability.
        """
        c1_eff = self.C1 * (1.0 + 3*alpha_f*np.abs(dT_array))
        return c1_eff / self.C1_CRIT * 100

    # ── Combined plotting ─────────────────────────────────────────────────
    def full_analysis(self, g, d, f_mod=10e6, save=False, label=''):
        f_span = np.linspace(self.f_esa*0.9, self.f_esa*1.1, 1000)
        t      = np.linspace(0, 3/f_mod, 2000)
        g_lti  = self.reflection_cmt(f_span, 0, 0)
        g_lptv = self.reflection_cmt(f_span, g, d)
        C1t, C2t, C3t, c_t = self.lptv_capacitances(t, f_mod)
        stab   = self.stability_margin_cmt(g, d)
        dT     = np.linspace(-50, 100, 400)
        frac   = self.thermal_stability(dT)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'US 2026/0039519 A1 Unified Analysis {label}\n'
                     f'g={g}, d={d} | Stability margin = {self.STABILITY_MARGIN:.0f}%',
                     fontweight='bold', fontsize=12)

        # 1. Return loss
        ax = axes[0,0]
        ax.plot(f_span/1e6, 20*np.log10(g_lti+1e-9), 'b-', lw=2, label='Passive LTI')
        ax.plot(f_span/1e6, 20*np.log10(g_lptv+1e-9), 'r--', lw=2,
                label=f'LPTV (g={g}, d={d})')
        ax.set(xlabel='Frequency (MHz)', ylabel='Return Loss (dB)',
               title=f'Reflection | Stable: {stab>=0}', ylim=(-40, 5))
        ax.axhline(-10, color='gray', lw=1, ls=':', alpha=0.7)
        ax.legend(); ax.grid(alpha=0.3)

        # 2. Bode-Fano comparison
        ax = axes[0,1]
        bi_lti  = self.bode_integral(f_span, g_lti)
        bi_lptv = self.bode_integral(f_span, g_lptv)
        bars = ax.bar(['LTI (Passive)', 'LPTV (Active)'], [bi_lti, bi_lptv],
                      color=['steelblue', 'tomato'], alpha=0.85, edgecolor='white')
        ax.set(ylabel='∫ ln(1/|Γ|) df', title='Bode-Fano Integral\nLTI vs LPTV')
        for bar, val in zip(bars, [bi_lti, bi_lptv]):
            ax.text(bar.get_x()+bar.get_width()/2, val, f'{val:.2e}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # 3. LPTV capacitances
        ax = axes[1,0]
        t_us = t * 1e6
        ax.plot(t_us, C1t, label='C1(t)')
        ax.plot(t_us, C2t, label='C2(t) coupling', lw=2)
        ax.plot(t_us, C3t, '--', label='C3(t)')
        ax.axhline(self.C1, ls='--', color='red', lw=1.5,
                   label=f'c1={self.C1} (90% of crit)')
        ax.axhline(self.C1_CRIT, ls=':', color='black', lw=1.5,
                   label=f'c1_crit={self.C1_CRIT}')
        ax.set(xlabel='Time (µs)', ylabel='Normalized capacitance',
               title='LPTV Capacitance Evolution [0044]')
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

        # 4. Thermal stability
        ax = axes[1,1]
        ax.plot(dT, frac, 'b-', lw=2.5)
        ax.axhline(100, color='red', lw=2, ls='--', label='100% = oscillation onset')
        unstable = dT[frac >= 100]
        if len(unstable):
            ax.axvline(unstable[0], color='red', lw=1.5, ls=':',
                       label=f'ΔT_crit ≈ {unstable[0]:.0f}°C')
            ax.fill_between(dT, frac, 100, where=(frac >= 100),
                            alpha=0.2, color='red')
        ax.set(xlabel='ΔT (°C)', ylabel='c1_eff / c1_crit × 100 %',
               title='Thermal Stability Analysis\nα_f = 2×10⁻⁴ /°C', ylim=(80, 115))
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

        plt.tight_layout()
        if save:
            fname = f'analysis_{label}.png'.replace(' ','_')
            plt.savefig(fname, dpi=150, bbox_inches='tight')
            print(f"Saved: {fname}")
        plt.show()

        print(f"\n{'='*55}")
        print(f"STABILITY REPORT [{label}]")
        print(f"  CMT stability margin:    {stab:.3e} Hz²")
        print(f"  c-space margin:          {self.STABILITY_MARGIN:.1f}%")
        print(f"  B-F integral LTI:        {bi_lti:.3e}")
        print(f"  B-F integral LPTV:       {bi_lptv:.3e}")
        print(f"  B-F ratio (LPTV/LTI):    {bi_lptv/max(bi_lti,1e-30):.3f}x")
        if stab < 0:
            print("  WARNING: System in parametric oscillation region!")
        print(f"{'='*55}")


# ══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ant = LPTVAntennaUnified(f_esa=300e6, f_r=300e6, q_esa=1000, q_r=100)

    print(f"System: f_ESA={ant.f_esa/1e6} MHz  Q_ESA={ant.q_esa}")
    print(f"Pump:   f_sum={ant.f_sum/1e6} MHz  f_diff={ant.f_diff/1e6} MHz")
    print(f"kappa_ESA={ant.kappa_esa/1e3:.0f} kHz | kappa_r={ant.kappa_r/1e6:.1f} MHz")
    print(f"Threshold = {ant.threshold:.3e} Hz^2")
    print(f"c1 = {ant.C1} | c1_crit = {ant.C1_CRIT} | margin = {ant.STABILITY_MARGIN:.0f}%")

    # — Scenario 1: Wide Bandwidth (from MultiToneAntenn.pdf, Fig. 5 params)
    ant.full_analysis(g=3.0, d=4.5, save=True, label='Wide_BW_Scenario1')

    # — Scenario 2: Perfect Matching (from MultiToneAntenn.pdf)
    ant.full_analysis(g=2.0, d=2.5, save=True, label='Perfect_Match_Scenario2')

    # — Scenario 3: Patent Fig. 4 exact parameters
    ant.full_analysis(g=3.36, d=3.5, save=True, label='Patent_Fig4_Regime_II')
