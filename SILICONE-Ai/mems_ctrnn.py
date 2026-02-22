# file: mems_ctrnn.py
"""
MEMS-based CTRNN Oscillator Model
Reference implementation of US Patent 2026/0050780 A1
Includes electrostatic spring softening + pull-in vulnerability testing
Keywords: MEMS, CTRNN, electrostatic actuation, pull-in instability, edge AI
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class MEMSParams:
    """Physical parameters of a silicon MEMS oscillator"""
    m: float = 1e-9          # effective mass, kg
    k0: float = 1.0          # mechanical stiffness, N/m
    zeta: float = 0.01       # damping ratio (requires vacuum)
    omega0: float = 1e5      # natural frequency, rad/s
    A: float = 1e-10         # electrode area, m²
    d: float = 1e-6          # nominal gap, m
    epsilon: float = 8.85e-12 # permittivity of free space, F/m
    V_pull_in: Optional[float] = None
    
    def __post_init__(self):
        if self.V_pull_in is None:
            # Analytical pull-in voltage for parallel-plate actuator
            self.V_pull_in = np.sqrt(8 * self.k0 * self.d**3 / (27 * self.epsilon * self.A))

class MEMSNeuron:
    """Analog neuromorphic unit based on electrostatically-tuned MEMS resonator"""
    
    def __init__(self, params: MEMSParams, V_bias: float = 0.0):
        self.p = params
        self.V_bias = V_bias  # FPAA-stored tuning voltage (synaptic weight analog)
        self.state = np.array([0.0, 0.0])  # [displacement x, velocity v]
        
    def effective_stiffness(self) -> float:
        """Compute k_eff including electrostatic spring softening"""
        electrostatic_term = self.p.epsilon * self.p.A * self.V_bias**2 / self.p.d**3
        k_eff = self.p.k0 - electrostatic_term
        if k_eff <= 1e-12:  # numerical stability threshold
            raise RuntimeError(f"PULL-IN INSTABILITY: k_eff={k_eff:.2e} <= 0 at V_bias={self.V_bias:.2f}V")
        return k_eff
    
    def time_constant(self) -> float:
        """Compute neuronal time constant τ from mechanical parameters"""
        k_eff = self.effective_stiffness()
        omega_eff = np.sqrt(k_eff / self.p.m)
        denominator = self.p.omega0**2 - self.p.epsilon * self.p.A * self.V_bias**2 / (self.p.m * self.p.d**3)
        if abs(denominator) < 1e-12:
            raise RuntimeError("Singularity in τ computation: denominator ≈ 0")
        return 2 * self.p.zeta * self.p.omega0 / denominator
    
    def dynamics(self, t: float, y: np.ndarray, input_force: Callable[[float], float]) -> np.ndarray:
        """ODE system: dy/dt = f(y, t, input)"""
        x, v = y
        k_eff = self.effective_stiffness()
        # Electrostatic force with gap dependence (nonlinear)
        gap = self.p.d - x
        if gap <= 1e-9:  # prevent numerical singularity
            raise RuntimeError("Gap closure detected")
        F_elec = 0.5 * self.p.epsilon * self.p.A * self.V_bias**2 / gap**2
        F_in = input_force(t)
        dxdt = v
        dvdt = (F_in + F_elec - k_eff * x - 2 * self.p.zeta * self.p.omega0 * self.p.m * v) / self.p.m
        return np.array([dxdt, dvdt])
    
    def simulate(self, t_span: tuple, input_force: Callable, dt: float = 1e-7) -> dict:
        """Numerical integration with exception handling for failure modes"""
        try:
            sol = solve_ivp(
                lambda t, y: self.dynamics(t, y, input_force),
                t_span, self.state, method='RK45', max_step=dt, rtol=1e-8, atol=1e-10
            )
            return {'success': True, 't': sol.t, 'x': sol.y[0], 'v': sol.y[1], 'tau': self.time_constant()}
        except (RuntimeError, ValueError) as e:
            return {'success': False, 'error': str(e), 'tau': None}

# === Red-Team Vulnerability Assessment ===
def test_pull_in_threshold():
    """Verify pull-in instability when V_bias exceeds critical voltage"""
    p = MEMSParams()
    neuron = MEMSNeuron(p, V_bias=p.V_pull_in * 1.02)  # 2% above threshold
    result = neuron.simulate((0, 1e-5), lambda t: 0)
    assert not result['success'], "Pull-in failure mode not triggered!"
    print(f"✓ Pull-in vulnerability confirmed: {result['error'][:80]}...")

def test_vacuum_dependency_squeeze_film():
    """Demonstrate resonance suppression under atmospheric damping"""
    p_vac = MEMSParams(zeta=0.01)   # high-Q vacuum operation
    p_air = MEMSParams(zeta=0.5)    # atmospheric squeeze-film damping
    neuron_vac = MEMSNeuron(p_vac)
    neuron_air = MEMSNeuron(p_air)
    
    input_sig = lambda t: 1e-12 * np.sin(2*np.pi*1e4*t)  # 10 kHz acoustic drive
    res_vac = neuron_vac.simulate((0, 1e-4), input_sig)
    res_air = neuron_air.simulate((0, 1e-4), input_sig)
    
    amp_vac = np.max(np.abs(res_vac['x'])) if res_vac['success'] else 0
    amp_air = np.max(np.abs(res_air['x'])) if res_air['success'] else 0
    assert amp_air < amp_vac * 0.15, "Insufficient damping contrast!"
    print(f"✓ Vacuum dependency: A_vac={amp_vac:.2e}, A_air={amp_air:.2e} (Q-factor collapse)")

def test_fpaa_radiation_vulnerability():
    """Simulate EMP-induced charge loss in FPAA memory (CMOS floating-gate)"""
    # FPAA stores V_bias values as charges on floating gates
    # Ionizing radiation generates e-h pairs in gate oxide → charge leakage
    V_bias_nominal = 3.3  # V
    emp_induced_leakage = np.random.normal(0, 0.8)  # stochastic charge loss
    V_bias_corrupted = np.clip(V_bias_nominal + emp_induced_leakage, 0, 5.0)
    
    if abs(V_bias_corrupted - V_bias_nominal) > 1.0:
        print(f"✓ FPAA vulnerability: EMP-induced weight corruption ΔV={abs(V_bias_corrupted - V_bias_nominal):.2f}V")
        return True
    return False

if __name__ == "__main__":
    print("=== MEMS CTRNN Reference Model: Vulnerability Assessment ===")
    test_pull_in_threshold()
    test_vacuum_dependency_squeeze_film()
    test_fpaa_radiation_vulnerability()
    print("All red-team tests completed.\n")
