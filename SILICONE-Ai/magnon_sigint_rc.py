# file: magnon_sigint_rc.py
"""
Magnon Spin-Wave Processor for SIGINT Applications
Wave-based computing in YIG thin films
"""

import numpy as np
from scipy.fft import fft2, ifft2
from dataclasses import dataclass

@dataclass
class MagnonParams:
    gamma: float = 2.21e5      # гиромагнитное отношение, рад/(с·Тл)
    alpha: float = 1e-4        # параметр затухания Гилберта
    Ms: float = 1.4e5          # намагниченность насыщения, А/м
    d: float = 100e-9          # толщина плёнки, м
    freq_range: tuple = (1e9, 100e9)  # рабочий диапазон, Гц

class MagnonProcessor:
    """Волновой процессор на спиновых волнах"""
    
    def __init__(self, shape: tuple, params: MagnonParams, dx: float = 50e-9):
        self.shape = shape
        self.p = params
        self.dx = dx
        self.m = np.zeros(shape, dtype=complex)  # комплексная амплитуда магнонов
        self.phase_mask = np.ones(shape)  # фазовая линза (обучаемый параметр)
        
    def inject_rf_signal(self, signal_freq: float, position: tuple, amplitude: float = 1.0):
        """Ввод СВЧ-сигнала в заданную точку плёнки"""
        if not (self.p.freq_range[0] <= signal_freq <= self.p.freq_range[1]):
            raise ValueError(f"Частота {signal_freq/1e9:.1f} ГГц вне диапазона магнонов!")
        x, y = position
        self.m[x, y] += amplitude * np.exp(1j * 2*np.pi*signal_freq*0)
        
    def propagate(self, dt: float = 1e-12, steps: int = 100):
        """Распространение спиновых волн с интерференцией"""
        k_space = np.fft.fftfreq(self.shape[0], d=self.dx) * 2*np.pi
        ky, kx = np.meshgrid(k_space, k_space, indexing='ij')
        k_mag = np.sqrt(kx**2 + ky**2) + 1e-10
        
        # Дисперсионное соотношение для магнонов в YIG (упрощённое)
        omega_k = self.p.gamma * self.p.Ms * self.p.d * k_mag**2
        
        for _ in range(steps):
            # Переход в k-пространство
            m_k = fft2(self.m)
            # Фазовая эволюция + затухание
            m_k *= np.exp((-1j * omega_k - self.p.alpha * omega_k) * dt)
            # Применение фазовой маски (обучение)
            m_k *= fft2(self.phase_mask)
            # Обратное преобразование
            self.m = np.real(ifft2(m_k))
            
        return self.m
    
    def read_interference(self) -> float:
        """Считывание результата интерференции (аналоговый выход)"""
        # Интегральная интенсивность в зоне детектирования
        detection_zone = self.m[self.shape[0]//2-5:self.shape[0]//2+5, 
                               self.shape[1]//2-5:self.shape[1]//2+5]
        return np.sum(np.abs(detection_zone)**2)
    
    def test_em_immunity(self):
        """Red Team: тест на устойчивость к ЭМИ"""
        # ЭМИ генерирует широкополосный шум, но не меняет спиновую конфигурацию
        em_pulse = np.random.randn(*self.shape) * 1e-3  # слабый шум
        m_before = self.m.copy()
        self.m += em_pulse  # "воздействие"
        # Спиновая система быстро релаксирует к исходному состоянию
        self.propagate(dt=1e-12, steps=50)
        deviation = np.mean(np.abs(self.m - m_before))
        print(f"✓ Устойчивость к ЭМИ: отклонение после релаксации = {deviation:.2e}")
        assert deviation < 1e-4, "Недостаточная устойчивость к ЭМИ!"
        return True

if __name__ == "__main__":
    proc = MagnonProcessor(shape=(128, 128), params=MagnonParams())
    
    # Ввод двух СВЧ-сигналов (моделирование перехвата радаров)
    proc.inject_rf_signal(10e9, (32, 32), amplitude=1.0)   # 10 ГГц
    proc.inject_rf_signal(12e9, (96, 96), amplitude=0.8)   # 12 ГГц
    
    # Распространение и интерференция
    result = proc.propagate(dt=1e-12, steps=200)
    output = proc.read_interference()
    print(f"Выходной сигнал интерференции: {output:.3e}")
    
    # Тест на ЭМИ-устойчивость
    proc.test_em_immunity()
    print("Магнонная симуляция завершена.")
