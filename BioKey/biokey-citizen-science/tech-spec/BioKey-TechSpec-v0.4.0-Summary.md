# BioKey v0.4.0 - Ключевые изменения ТЗ
## Summary после анализа снапов

**Дата обновления:** 2026-02-15  
**Версия ТЗ:** 1.1 (обновлено после анализа кодовой базы)

---

##  ГЛАВНЫЕ ИЗМЕНЕНИЯ

### 1. Приоритет сенсоров: МИКРОФОН → АКСЕЛЕРОМЕТР

**БЫЛО (в первой версии ТЗ):**
- Акселерометр - главный сенсор
- Микрофон - опционально

**СТАЛО (после уточнений):**
- **Микрофон - ПРИОРИТЕТ №1** (дальность до 5 метров)
- **Акселерометр - вторичный** (подтверждающий)

**Обоснование:**
- Микрофон слышит дыхание на расстоянии (тумбочка, стол)
- Акселерометр работает только если телефон на кровати
- Большинство пользователей ставят телефон на тумбочку

---

### 2. Sensor Fusion - объединение двух источников

**Новый модуль:** `SensorFusion.kt`

**Логика:**
```
Микрофон (Audio) → AudioBreathDetector → BreathSignal + confidence
                                              ↓
                                          [Fusion]
                                              ↓
Акселерометр (Motion) → MotionBreathDetector → BreathSignal + confidence
                                              ↓
                                      FusedBreathSignal
                                  (weighted average по confidence)
```

**Веса зависят от размещения телефона:**
- Тумбочка: Аудио 100%, Движение 0%
- Рядом на кровати: Аудио 60%, Движение 40%
- На груди: Аудио 50%, Движение 50%

---

### 3. Data Quality - новая метрика

**5 уровней качества данных:**
- **EXCELLENT** (>80%) - оба сенсора отлично
- **GOOD** (60-80%) - один сенсор отлично, второй средне
- **FAIR** (40-60%) - один сенсор работает
- **POOR** (20-40%) - слабый сигнал
- **UNUSABLE** (<20%) - данных нет

**Применение:**
- Классификация фаз сна учитывает DataQuality
- MQTT публикует только FAIR и выше
- Утренний отчет показывает качество

---

### 4. Wave Quality Score - расчет качества волны

**Новый модуль:** `WaveQualityCalculator.kt`

**Формула:**
```
WaveQuality = (
    PhaseScore × 0.4 +       // Deep sleep = 1.0
    FrequencyScore × 0.3 +   // Близость к 7.83 Hz
    SyncScore × 0.2 +        // Синхронизация с дыханием
    Confidence × 0.1         // Уверенность классификации
) × DataQualityMultiplier
```

**Рейтинг:**
- EXCELLENT (>90%)
- GOOD (70-90%)
- FAIR (50-70%)
- POOR (30-50%)
- UNUSABLE (<30%)

**Использование:**
- В MQTT публикуется только если FAIR+
- Показывается в UI
- Влияет на синхронизацию

---

### 5. Интеграция с существующей кодовой базой

**Что УЖЕ есть в v0.3.9.3_ME:**

 **Используем без изменений:**
- `WaveCore.kt` - главный движок
- `NightTargetModel.kt` - целевая точка 04:30
- `OneShotGuard.kt` - защита от повторов TTS/alarm
- `AudioEngine.kt` - аудио-система
- `BrainWaveLibrary.kt` - библиотека частот
- `WaveBreathCoupler.kt` - связка дыхание-волна
- `SmartWakeEngine.kt` - умный будильник
- `MotionSensor.kt` - акселерометр
- `NoiseSensor.kt` - микрофон
- `SleepForegroundService.kt` - foreground service

 **Дорабатываем:**
- `SleepPhaseClassifier.kt` → добавить DataQuality
- `BreathAnalyzer.kt` → адаптация для fusion
- `SensorAggregator.kt` → fusion logic
- `AlarmEngine.kt` → hard alarm
- `BioSyncManager.kt` → MQTT integration

 **Создаем с нуля:**
- `SensorFusion.kt` - объединение сенсоров
- `WaveQualityCalculator.kt` - расчет качества
- `MqttManager.kt` - MQTT клиент
- `TelemetryPublisher.kt` - публикация
- `SyncEngine.kt` - синхронизация
- `TtsPlayer.kt` - TTS установка
- `SnapshotExporter.kt` - экспорт JSON
- Геолокация (Geolocation, UserId, Geocell)

---

##  ОБНОВЛЕННАЯ АРХИТЕКТУРА

### Поток данных (сенсоры → MQTT):

```
[Микрофон 16kHz]              [Акселерометр 50Hz]
       ↓                              ↓
[AudioFFTAnalyzer]            [MotionSensor]
       ↓                              ↓
[AudioBreathDetector]         [MotionBreathDetector]
  (confidence, rate)            (confidence, rate)
       ↓                              ↓
       └──────────[SensorFusion]─────┘
                       ↓
              [FusedBreathSignal]
          (detected, confidence, 
           dataQuality, placement)
                       ↓
          [SleepPhaseClassifier]
         (Enhanced with quality)
                       ↓
            [SleepPhaseResult]
          (phase, confidence, 
              dataQuality)
                       ↓
       [WaveQualityCalculator]
                       ↓
              [WaveQuality]
           (score, rating)
                       ↓
        [Quality Filter: FAIR+?]
                       ↓
        [TelemetryPublisher]
                       ↓
              [MQTT Broker]
```

---

##  ПРАКТИЧЕСКИЕ СЦЕНАРИИ

### Сценарий 1: Телефон на тумбочке (30-100 см)
```
Микрофон:  Confidence 0.9 (слышит дыхание отлично)
Акселерометр:  Confidence 0.1 (движений не видит)

→ Fusion: Audio 90%, Motion 10%
→ DataQuality: EXCELLENT (audio dominates)
→ SleepPhase: DEEP (regularity 0.92)
→ WaveQuality: EXCELLENT (0.91)
→ MQTT:  Публикуется
```

### Сценарий 2: Телефон далеко на столе (200 см)
```
Микрофон:  Confidence 0.5 (слышит слабо, шумы)
Акселерометр:  Confidence 0.05 (ничего)

→ Fusion: Audio 95%, Motion 5%
→ DataQuality: FAIR (weak signal)
→ SleepPhase: LIGHT (uncertainty high)
→ WaveQuality: FAIR (0.58)
→ MQTT:  Публикуется (на грани)
```

### Сценарий 3: Телефон на груди
```
Микрофон:  Confidence 0.95 (очень близко)
Акселерометр:  Confidence 0.85 (дыхание + движения)

→ Fusion: Audio 55%, Motion 45%
→ DataQuality: EXCELLENT (both sensors)
→ SleepPhase: DEEP (both agree)
→ WaveQuality: EXCELLENT (0.94)
→ MQTT:  Публикуется
```

### Сценарий 4: Шумная комната (кондиционер, улица)
```
Микрофон:  Confidence 0.2 (шум >> дыхание)
Акселерометр:  Confidence 0.3 (телефон на кровати)

→ Fusion: Audio 40%, Motion 60%
→ DataQuality: POOR (both weak)
→ SleepPhase: UNKNOWN (can't classify)
→ WaveQuality: UNUSABLE (0.18)
→ MQTT:  НЕ публикуется
```

---

##  НОВЫЕ МЕТРИКИ В ТЕЛЕМЕТРИИ

**Старая версия (базовая):**
```json
{
  "user_id": "...",
  "timestamp": 1709596830,
  "sleep_stage": "deep",
  "binaural_freq": 7.83,
  "breathing_rate": 8.5,
  "heart_rate": 58
}
```

**Новая версия (с качеством):**
```json
{
  "user_id": "geo_990_1005_a3f9c2d8_1709596800",
  "timestamp": 1709596830,
  
  "sleep_phase": {
    "current": "deep",
    "confidence": 0.95
  },
  
  "data_quality": {
    "overall": "excellent",
    "audio_confidence": 0.92,
    "motion_confidence": 0.45,
    "phone_placement": "nightstand"
  },
  
  "breathing": {
    "rate_bpm": 8.5,
    "regularity": 0.91,
    "detected_by": "audio_primary"
  },
  
  "wave_quality": {
    "score": 0.89,
    "rating": "excellent",
    "binaural_freq": 7.83
  },
  
  "heart_rate": 58,
  "hrv_rmssd": 42.3
}
```

---

##  ИЗМЕНЕНИЯ В ПЛАНЕ РАЗРАБОТКИ

### Обновленные приоритеты:

**Фаза 1 (3 недели):**
1.  **SensorFusion** - критично, основа всего
2.  **WaveQuality** - нужно для фильтрации MQTT
3.  **TTS Player** - простой модуль
4.  Доработка классификатора
5.  Hard Alarm

**Фаза 2 (3 недели):**
1.  **MQTT интеграция** - главная фича
2.  **SyncEngine** - адаптация к глобальной волне
3.  Геолокация (простая)
4.  Telemetry publisher

**Фаза 3 (2 недели):**
1.  Export JSON
2.  UI polish
3.  Тесты
4.  Документация

---

##  CHECKLIST ГОТОВНОСТИ К РАЗРАБОТКЕ

### Перед стартом Фазы 1:
- [x] ТЗ обновлено с учетом снапов
- [x] Приоритеты сенсоров уточнены
- [x] DataQuality концепция определена
- [x] WaveQuality формула согласована
- [x] Интеграция с существующим кодом спланирована
- [ ] Выбран MQTT broker (публичный / свой?)
- [ ] Решение по терминалу (MVP / post-MVP?)
- [ ] Решение по UI (минимализм / rich?)

### Вопросы для финального согласования:

1. **MQTT Broker:** 
   - Публичный HiveMQ (быстро, ограничения) ← рекомендую для MVP
   - Свой на VPS ($5-10/мес, полный контроль)

2. **Терминал:**
   - В MVP (полезно для отладки) ← рекомендую
   - Post-MVP (не отвлекает)

3. **DataQuality порог для MQTT:**
   - FAIR+ (40%+) ← текущий выбор
   - GOOD+ (60%+) - строже, меньше трафика

4. **Микрофон duty cycle:**
   - Continuous (больше точность, больше батарея)
   - 50% duty (меньше батарея) ← рекомендую для MVP

---

##  CHANGELOG ТЗ

### v1.1 (2026-02-14) - После анализа снапов
-  Изменен приоритет: микрофон → акселерометр
-  Добавлен SensorFusion модуль
-  Добавлена концепция DataQuality
-  Добавлен WaveQualityCalculator
-  Обновлена архитектура с учетом существующего кода
-  Детализирован жизненный цикл session
-  Добавлены практические сценарии
-  Обновлен план разработки (5-8 недель)

### v1.0 (2026-02-14) - Первая версия
- Базовое ТЗ для v0.4.0_SYNC
- 8 функциональных требований
- MQTT архитектура
- Резонанс Шумана обоснование

---

**Версия:** 1.1  
**Дата:** 2026-02-15  
**Авторы:** Sergey Tmenov, Maria Tmenova, Maya Tmenova  
**Статус:** Ready for Development  

---

END OF SUMMARY
