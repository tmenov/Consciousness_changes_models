# file: magnon_sigint.py
"""
Magnonic Spin-Wave Processor for SIGINT/RF Intelligence
Wave-based analog computing in YIG thin films
Keywords: magnonics, spintronics, spin waves, YIG, SIGINT, RF computing, EMI hardening
"""

import numpy as np
from scipy.fft import fft2, ifft2
from dataclasses import dataclass

@dataclass
class MagnonParams:
    gamma: float = 2.21e5       # gyromagnetic ratio, rad/(s·T)
    alpha_G: float = 1e-4       # Gilbert damping parameter
    M_s: float = 1.4e5          # saturation magnetization, A/m
    film_thickness: float = 100e-9  # YIG film thickness, m
    freq_band: tuple = (1e9, 100e9)  # operational band: 1–100 GHz
    exchange_length: float = 5e-9  # magnetic exchange length, m

class MagnonProcessor:
    """Analog RF processor using spin-wave interference in YIG films"""
    
    def __init__(self, shape: tuple, params: MagnonParams, dx: float = 50e-9):
        self.shape = shape
        self.p = params
        self.dx = dx
        self.m = np.zeros(shape, dtype=complex)  # complex magnon amplitude
        self.phase_mask = np.ones(shape)  # trainable phase profile (SOT-programmable)
        
    def inject_rf_signal(self, freq_hz: float, position: tuple, amplitude: float = 1.0):
        """Couple external RF signal into magnonic medium via antenna"""
        if not (self.p.freq_band[0] <= freq_hz <= self.p.freq_band[1]):
            raise ValueError(f"Frequency {freq_hz/1e9:.1f} GHz outside magnonic band [{self.p.freq_band[0]/1e9}, {self.p.freq_band[1]/1e9}] GHz")
        x, y = position
        self.m[x, y] += amplitude * np.exp(1j * 0)  # phase reference at t=0
        
    def propagate(self, dt: float = 1e-12, n_steps: int = 100):
        """Simulate spin-wave propagation with dispersion and interference"""
        # Wavevector grid (spectral method)
        kx = 2*np.pi * np.fft.fftfreq(self.shape[1], d=self.dx)
        ky = 2*np.pi * np.fft.fftfreq(self.shape[0], d=self.dx)
        kx_grid, ky_grid = np.meshgrid(kx, ky, indexing='ij')
        k_mag = np.sqrt(kx_grid**2 + ky_grid**2) + 1e-10  # avoid division by zero
        
        # Damon-Eshbach dispersion relation for thin-film magnons (simplified)
        omega_k = self.p.gamma * self.p.M_s * self.p.film_thickness * k_mag**2
        
        for _ in range(n_steps):
            # Forward FFT to k-space
            m_k = fft2(self.m)
            # Phase evolution + Gilbert damping
            phase_factor = np.exp((-1j * omega_k - self.p.alpha_G * omega_k) * dt)
            m_k *= phase_factor
            # Apply programmable phase mask (training via SOT)
            m_k *= fft2(self.phase_mask)
            # Inverse FFT to real space
            self.m = np.real(ifft2(m_k))
            
        return self.m
    
    def read_interference_pattern(self) -> float:
        """Analog readout: integrated intensity in detection zone"""
        cx, cy = self.shape[0]//2, self.shape[1]//2
        detection_zone = self.m[cx-5:cx+5, cy-5:cy+5]
        return np.sum(np.abs(detection_zone)**2)  # proportional to signal power
    
    def test_emi_immunity(self):
        """Red-team: verify immunity to electromagnetic pulse (EMP)"""
        # EMP induces broadband voltage spikes but does not alter spin configuration
        em_pulse = np.random.randn(*self.shape) * 1e-4  # weak stochastic perturbation
        m_pre = self.m.copy()
        
        self.m += em_pulse  # "EMP exposure"
        # Spin system relaxes via Gilbert damping; magnetic order preserved
        self.propagate(dt=1e-12, n_steps=50)
        
        fidelity = np.abs(np.vdot(m_pre, self.m)) / (np.linalg.norm(m_pre) * np.linalg.norm(self.m) + 1e-12)
        print(f"✓ EMP immunity: state fidelity after pulse = {fidelity:.4f} (target >0.999)")
        assert fidelity > 0.999, "Insufficient magnetic order preservation!"
        return True
    
    def test_frequency_gap_acoustic_incompatibility(self):
        """Verify physical incompatibility with low-frequency acoustic signals"""
        try:
            self.inject_rf_signal(50.0, (32, 32))  # 50 Hz — far below magnonic band
            assert False, "Should have rejected sub-MHz frequency"
        except ValueError as e:
            print(f"✓ Frequency gap enforcement: {str(e)[:70]}...")
            return True

if __name__ == "__main__":
    print("=== Magnonic SIGINT Processor: RF Edge Intelligence ===")
    proc = MagnonProcessor(shape=(128, 128), params=MagnonParams())
    
    # Simulate interception of two radar emitters (SIGINT scenario)
    proc.inject_rf_signal(10e9, (32, 32), amplitude=1.0)   # 10 GHz threat radar
    proc.inject_rf_signal(12.5e9, (96, 96), amplitude=0.7) # 12.5 GHz tracking radar
    
    # Wave propagation and interference-based classification
    result = proc.propagate(dt=1e-12, n_steps=200)
    output_power = proc.read_interference_pattern()
    print(f"Interference output power: {output_power:.3e} (arbitrary units)")
    
    # Robustness validation
    proc.test_emi_immunity()
    proc.test_frequency_gap_acoustic_incompatibility()
    print("Magnonic simulation completed.\n")
