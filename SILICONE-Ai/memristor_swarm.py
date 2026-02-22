# file: memristor_swarm.py
"""
Stochastic Reservoir Computer with Passive Memristor Crossbar
Analog edge computing via Ohm's and Kirchhoff's laws in ReRAM arrays
Keywords: memristor, ReRAM, crossbar array, reservoir computing, stochastic computing, graceful degradation
"""

import numpy as np
from dataclasses import dataclass

@dataclass
class MemristorParams:
    G_min: float = 1e-6      # minimum conductance, S
    G_max: float = 1e-3      # maximum conductance, S
    tau_switch: float = 1e-6 # switching time constant, s
    device_noise: float = 0.15 # factory-induced conductance variability (σ/μ)

class MemristorCrossbar:
    """Passive analog VMM engine: I = G·V via Ohm's law in crossbar topology"""
    
    def __init__(self, n_inputs: int, n_outputs: int, params: MemristorParams):
        self.n_in = n_inputs
        self.n_out = n_outputs
        self.p = params
        # Initialize with realistic device-to-device variability
        self.G = np.random.lognormal(
            mean=np.log((params.G_min + params.G_max)/2),
            sigma=params.device_noise,
            size=(n_outputs, n_inputs)
        )
        self.G = np.clip(self.G, params.G_min, params.G_max)
        
    def forward_analog(self, V_in: np.ndarray) -> np.ndarray:
        """Hardware-native vector-matrix multiplication: I = G·V"""
        return self.G @ V_in
    
    def update_conductance_local(self, V_in: np.ndarray, error: np.ndarray, lr: float = 1e-4):
        """Local learning rule: ΔG_ij ∝ V_i · error_j (no backpropagation)"""
        delta_G = lr * np.outer(error, V_in)
        self.G = np.clip(self.G + delta_G, self.p.G_min, self.p.G_max)
        
    def test_graceful_degradation(self, failure_fraction: float = 0.6, n_trials: int = 10):
        """Red-team: quantify performance retention under node loss"""
        errors = []
        for _ in range(n_trials):
            G_nominal = self.G.copy()
            # Randomly disable fraction of input channels (sensor destruction)
            failed_idx = np.random.choice(
                self.n_in, size=int(self.n_in * failure_fraction), replace=False
            )
            V_test = np.random.randn(self.n_in) * 0.1
            V_test[failed_idx] = 0  # failed sensors output zero
            
            I_degraded = self.forward_analog(V_test)
            I_nominal = G_nominal @ np.random.randn(self.n_in) * 0.1
            
            # Relative output deviation (normalized)
            rel_err = np.mean(np.abs(I_degraded - I_nominal) / (np.abs(I_nominal) + 1e-10))
            errors.append(rel_err)
        
        mean_err = np.mean(errors)
        print(f"✓ Graceful degradation: {failure_fraction*100:.0f}% node loss → output error {mean_err*100:.2f}%")
        assert mean_err < 0.05, f"Excessive degradation: {mean_err*100:.2f}% > 5% threshold"
        return True

class StochasticReservoirSystem:
    """Full edge sensing pipeline: uncalibrated sensors + passive analog compute"""
    
    def __init__(self, n_sensors: int = 256, n_features: int = 32):
        self.crossbar = MemristorCrossbar(n_sensors, n_features, MemristorParams())
        self.sensor_noise_rms = 0.05  # typical commercial hydrophone SNR
        
    def sense_analog(self, acoustic_field: np.ndarray) -> np.ndarray:
        """Simulate uncalibrated sensor array with additive noise"""
        raw = acoustic_field + np.random.randn(len(acoustic_field)) * self.sensor_noise_rms
        # Weak nonlinearity (piezo response saturation)
        return np.tanh(raw * 8.0)
    
    def process_edge(self, acoustic_input: np.ndarray) -> np.ndarray:
        """End-to-end analog inference: sensing → reservoir → readout"""
        V_in = self.sense_analog(acoustic_input)
        return self.crossbar.forward_analog(V_in)
    
    def train_online(self, acoustic_input: np.ndarray, target: np.ndarray, lr: float = 1e-4) -> float:
        """In-situ learning: local weight update without digital backprop"""
        V_in = self.sense_analog(acoustic_input)
        output = self.crossbar.forward_analog(V_in)
        error = target - output
        self.crossbar.update_conductance_local(V_in, error, lr)
        return np.mean(error**2)  # MSE loss

if __name__ == "__main__":
    print("=== Stochastic Reservoir: Distributed Edge Sensing ===")
    swarm = StochasticReservoirSystem(n_sensors=256, n_features=32)
    
    # Online training on binary acoustic classification task
    for epoch in range(200):
        acoustic = np.random.randn(256) * 0.1  # synthetic sensor input
        target = np.array([1.0 if acoustic[i] > 0 else -1.0 for i in range(32)])
        loss = swarm.train_online(acoustic, target, lr=5e-5)
        if epoch % 40 == 0:
            print(f"Epoch {epoch:3d}: MSE loss = {loss:.4f}")
    
    # Survivability validation
    swarm.crossbar.test_graceful_degradation(failure_fraction=0.6)
    print("Stochastic reservoir simulation completed.\n")
