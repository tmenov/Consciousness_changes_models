import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import pi

class LPTVAntennaModel:
    """
    Computational model for a Multi-Tone Modulated Antenna system
    based on US Patent 2026/0039519 A1 architecture.
    """
    
    def __init__(self, f_esa=300e6, f_r=300e6, q_esa=1000, q_r=100):
        """
        Initialize the antenna model parameters.
        
        Args:
            f_esa (float): Resonant frequency of the Electrically Small Antenna (Hz).
            f_r (float): Resonant frequency of the drive resonator (Hz).
            q_esa (float): Quality factor of the ESA.
            q_r (float): Quality factor of the drive resonator.
        """
        self.f_esa = f_esa
        self.f_r = f_r
        self.q_esa = q_esa
        self.q_r = q_r
        
        # Calculate linewidths (decay rates)
        # kappa = f_res / Q
        self.kappa_esa = self.f_esa / self.q_esa
        self.kappa_r = self.f_r / self.q_r
        
        # Modulation frequencies
        self.f_sum = self.f_r + self.f_esa
        self.f_diff = abs(self.f_r - self.f_esa)
        
    def calculate_stability_margin(self, g_amp, d_amp):
        """
        Calculate the stability margin based on modulation amplitudes.
        
        Args:
            g_amp (float): Amplitude of the sum tone modulation.
            d_amp (float): Amplitude of the difference tone modulation.
            
        Returns:
            float: Stability metric. Positive values indicate stability.
        """
        # Stability condition derived from patent Eq. 3-5
        # Critical threshold is (kappa_r * kappa_esa) / 4
        threshold = (self.kappa_r * self.kappa_esa) / 4
        metric = d_amp**2 - g_amp**2
        return metric - threshold

    def get_reflection_coefficient(self, frequencies, g_amp, d_amp):
        """
        Compute the reflection coefficient Gamma over a frequency span.
        This is a heuristic model approximating the coupled-mode behavior.
        
        Args:
            frequencies (np.array): Array of frequency points (Hz).
            g_amp (float): Sum tone amplitude.
            d_amp (float): Difference tone amplitude.
            
        Returns:
            np.array: Magnitude of reflection coefficient |Gamma|.
        """
        # Effective linewidth modification due to LPTV modulation
        # This mimics the bandwidth expansion described in the patent
        delta_kappa = (d_amp**2 - g_amp**2) / self.kappa_esa
        
        # Prevent negative linewidth (instability region)
        kappa_eff = np.maximum(self.kappa_esa + delta_kappa, 1e-3)
        
        # Normalized detuning
        detuning = (frequencies - self.f_esa) / self.f_esa
        
        # Calculate reflection coefficient magnitude for a resonant system
        # |Gamma| = |j * 2 * Q_eff * detuning / (1 + j * 2 * Q_eff * detuning)|
        # Where Q_eff = f_esa / kappa_eff
        q_eff = self.f_esa / kappa_eff
        
        numerator = 1j * 2 * q_eff * detuning
        denominator = 1 + 1j * 2 * q_eff * detuning
        
        gamma = np.abs(numerator / denominator)
        return gamma

    def plot_performance(self, g_amp, d_amp):
        """
        Generate performance plots for bandwidth and stability.
        
        Args:
            g_amp (float): Sum tone amplitude.
            d_amp (float): Difference tone amplitude.
        """
        # Frequency span around resonance
        f_span = np.linspace(self.f_esa * 0.9, self.f_esa * 1.1, 1000)
        
        # Calculate LTI (Passive) baseline
        gamma_lti = self.get_reflection_coefficient(f_span, g_amp=0, d_amp=0)
        
        # Calculate LPTV (Active)
        gamma_lptv = self.get_reflection_coefficient(f_span, g_amp, d_amp)
        
        # Calculate Stability
        stability = self.calculate_stability_margin(g_amp, d_amp)
        is_stable = stability >= 0
        
        # Plotting
        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot 1: Return Loss
        axs[0].plot(f_span/1e6, 20*np.log10(gamma_lti + 1e-6), label='Passive ESA (LTI)', linewidth=2)
        axs[0].plot(f_span/1e6, 20*np.log10(gamma_lptv + 1e-6), 
                    label=f'LPTV Mode (g={g_amp}, d={d_amp})', linewidth=2, linestyle='--')
        axs[0].set_title(f'Reflection Coefficient |Γ| (Stable: {is_stable})')
        axs[0].set_xlabel('Frequency (MHz)')
        axs[0].set_ylabel('Return Loss (dB)')
        axs[0].set_ylim(-40, 5)
        axs[0].grid(True, alpha=0.3)
        axs[0].legend()
        
        # Plot 2: Bode-Fano Integral Comparison
        # Numerical integration of ln(1/|Gamma|)
        def bode_integral(f, gamma):
            gamma_safe = np.clip(gamma, 1e-6, 1.0)
            return np.trapz(np.log(1 / gamma_safe), f)
        
        int_lti = bode_integral(f_span, gamma_lti)
        int_lptv = bode_integral(f_span, gamma_lptv)
        
        metrics = ['Passive\n(LTI)', 'LPTV\n(Active)']
        values = [int_lti, int_lptv]
        colors = ['blue', 'orange']
        
        axs[1].bar(metrics, values, color=colors, alpha=0.7)
        axs[1].set_title('Bode-Fano Integral (Bandwidth Efficiency)')
        axs[1].set_ylabel('∫ ln(1/|Γ|) df (norm.)')
        axs[1].grid(axis='y', alpha=0.3)
        
        # Annotate bars
        for i, v in enumerate(values):
            axs[1].text(i, v + 0.1, f'{v:.2f}', ha='center')
            
        plt.tight_layout()
        plt.show()
        
        # Print Stability Report
        print(f"--- Stability Report ---")
        print(f"Threshold Value: {(self.kappa_r * self.kappa_esa) / 4:.2e}")
        print(f"Current Metric (d² - g²): {d_amp**2 - g_amp**2:.2e}")
        print(f"Stability Margin: {stability:.2e}")
        if not is_stable:
            print("WARNING: System is in parametric oscillation region!")

# =============================================================================
# Main Execution Block
# =============================================================================
if __name__ == "__main__":
    # Initialize the model with VHF parameters
    # ESA at 300 MHz, High Q (1000) representing a small antenna
    antenna = LPTVAntennaModel(f_esa=300e6, f_r=300e6, q_esa=1000, q_r=100)
    
    print(f"System Initialized: f_esa={antenna.f_esa/1e6} MHz, Q_esa={antenna.q_esa}")
    print(f"Modulation Frequencies: f_sum={antenna.f_sum/1e6} MHz, f_diff={antenna.f_diff/1e6} MHz")
    
    # Scenario 1: Wide Bandwidth Mode (Aggressive)
    # High d, moderate g. Close to instability.
    print("\n--- Scenario 1: Wide Bandwidth Mode ---")
    antenna.plot_performance(g_amp=3.0, d_amp=4.5)
    
    # Scenario 2: Perfect Matching Mode (Conservative)
    # Balanced d and g.
    print("\n--- Scenario 2: Perfect Matching Mode ---")
    antenna.plot_performance(g_amp=2.0, d_amp=2.5)
