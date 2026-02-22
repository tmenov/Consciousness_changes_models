# file: mems_ctrnn_rc.py
"""
MEMS CTRNN Oscillator Model
Based on US Patent 2026/0050780 A1
Implements electrostatic spring softening + vulnerability testing
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class MEMSParams:
    """Физические параметры МЭМС-осциллятора"""
    m: float = 1e-9          # масса, кг
    k0: float = 1.0          # механическая жёсткость, Н/м
    zeta: float = 0.01       # коэффициент демпфирования
    omega0: float = 1e5      # собственная частота, рад/с
    A: float = 1e-10         # площадь электрода, м²
    d: float = 1e-6          # начальный зазор, м
    epsilon: float = 8.85e-12 # диэлектрическая проницаемость, Ф/м
    V_pull_in: Optional[float] = None
    
    def __post_init__(self):
        if self.V_pull_in is None:
            self.V_pull_in = np.sqrt(8 * self.k0 * self.d**3 / (27 * self.epsilon * self.A))

class MEMSNeuron:
    """Аналоговый нейрон на базе МЭМС-осциллятора"""
    
    def __init__(self, params: MEMSParams, V_bias: float = 0.0):
        self.p = params
        self.V_bias = V_bias  # напряжение настройки из FPAA
        self.state = np.array([0.0, 0.0])  # [x, v]
        
    def effective_stiffness(self) -> float:
        """Эффективная жёсткость с учётом электростатического размягчения"""
        electrostatic_term = self.p.epsilon * self.p.A * self.V_bias**2 / self.p.d**3
        k_eff = self.p.k0 - electrostatic_term
        if k_eff <= 0:
            raise RuntimeError(f"PULL-IN: k_eff={k_eff:.2e} <= 0 при V_bias={self.V_bias:.2f}В")
        return k_eff
    
    def time_constant(self) -> float:
        """Постоянная времени нейрона τ"""
        k_eff = self.effective_stiffness()
        omega_eff = np.sqrt(k_eff / self.p.m)
        return 2 * self.p.zeta * omega0 / (omega0**2 - self.p.epsilon * self.p.A * self.V_bias**2 / (self.p.m * self.p.d**3))
    
    def dynamics(self, t: float, y: np.ndarray, input_force: Callable[[float], float]) -> np.ndarray:
        """Система ОДУ: dy/dt = f(y, t)"""
        x, v = y
        k_eff = self.effective_stiffness()
        F_elec = 0.5 * self.p.epsilon * self.p.A * self.V_bias**2 / (self.p.d - x)**2
        F_in = input_force(t)
        dxdt = v
        dvdt = (F_in + F_elec - self.p.k0 * x - 2 * self.p.zeta * self.p.omega0 * self.p.m * v) / self.p.m
        return np.array([dxdt, dvdt])
    
    def simulate(self, t_span: tuple, input_force: Callable, dt: float = 1e-7) -> dict:
        """Интегрирование динамики с обработкой исключений"""
        try:
            sol = solve_ivp(
                lambda t, y: self.dynamics(t, y, input_force),
                t_span, self.state, method='RK45', max_step=dt, rtol=1e-8
            )
            return {'success': True, 't': sol.t, 'x': sol.y[0], 'v': sol.y[1], 'tau': self.time_constant()}
        except RuntimeError as e:
            return {'success': False, 'error': str(e), 'tau': None}

# === Red Team: тестирование уязвимостей ===
def test_pull_in_vulnerability():
    """Тест: превышение V_bias вызывает pull-in"""
    p = MEMSParams()
    neuron = MEMSNeuron(p, V_bias=p.V_pull_in * 1.05)  # на 5% выше порога
    result = neuron.simulate((0, 1e-5), lambda t: 0)
    assert not result['success'], "Pull-in не сработал!"
    print(f"✓ Pull-in подтверждён: {result['error']}")

def test_vacuum_dependency():
    """Тест: нарушение вакуума (рост zeta) гасит резонанс"""
    p = MEMSParams(zeta=0.01)
    neuron_vac = MEMSNeuron(p)
    p_air = MEMSParams(zeta=0.5)  # атмосферное демпфирование
    neuron_air = MEMSNeuron(p_air)
    
    input_sig = lambda t: 1e-12 * np.sin(2*np.pi*1e4*t)
    res_vac = neuron_vac.simulate((0, 1e-4), input_sig)
    res_air = neuron_air.simulate((0, 1e-4), input_sig)
    
    amp_vac = np.max(np.abs(res_vac['x']))
    amp_air = np.max(np.abs(res_air['x']))
    assert amp_air < amp_vac * 0.1, "Демпфирование не подавляет резонанс!"
    print(f"✓ Вакуумная зависимость: A_vac={amp_vac:.2e}, A_air={amp_air:.2e}")

if __name__ == "__main__":
    test_pull_in_vulnerability()
    test_vacuum_dependency()
    print("Все тесты уязвимостей пройдены.")
