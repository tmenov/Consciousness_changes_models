# BioKey v0.4.0_SYNC - READY TO START
## Финальный чеклист перед разработкой

**Дата:** 2026-02-15  
**Версия ТЗ:** 1.2 (финальная)  
**Статус:** ГОТОВО К РАЗРАБОТКЕ

---

## ВСЕ СОГЛАСОВАНО

### 1. MQTT Broker
- [x] **HiveMQ Cloud** (публичный, free tier)
- URL: `ssl://broker.hivemq.com:8883`
- Connections: 100 concurrent (достаточно для MVP)
- Anonymous auth (для начала)

### 2. Терминал
- [x] **Включен в MVP**
- Доступ: Long-press на лого
- Команды: stats, geocell, wave, users, sensors, mqtt, export
- Цель: Отладка + power users

### 3. DataQuality порог для MQTT
- [x] **GOOD+ (≥60%)**
- Публикуются только: EXCELLENT (>80%) и GOOD (60-80%)
- FAIR (40-60%), POOR, UNUSABLE - НЕ публикуются
- Цель: Меньше трафика, выше качество данных

### 4. Микрофон duty cycle
- [x] **50% (15 сек ON / 15 сек OFF)**
- Экономия батареи: ~5% за ночь вместо ~10%
- Точность: Достаточная для детекции дыхания
- Можно динамически увеличивать в critical windows (TTS, wake)

### 5. Smartwatch интеграция
- [x] **Полная поддержка**
- Приоритет: Wear OS (Health Services) > Generic BLE HR
- Метрики: HR, HRV (RMSSD, SDNN), SpO2, BP (если есть)
- Но: **Микрофон всё равно главный** для детекции фаз сна

### 6. UI стиль
- [x] **Terminal-style минимализм**
- Одним листом (scroll вверх/вниз)
- Никаких графиков (только текст + progress bars)
- Быстрый доступ ко всем функциям

---

## ПРИОРИТЕТ СЕНСОРОВ (ФИНАЛЬНЫЙ)

```
1. МИКРОФОН (главный)
   - Детекция дыхания (0.1-0.5 Hz)
   - Детекция храпа (150-300 Hz)
   - Дальность: до 5 метров
   - Duty cycle: 50%
   - Вес в fusion: 60%

2. SMARTWATCH (если подключен)
   - HR, HRV, SpO2, BP
   - Телеметрия в MQTT
   - Повышает DataQuality
   - Вес в fusion: 30%
   
3. АКСЕЛЕРОМЕТР (вторичный)
   - Подтверждение фаз
   - Работает только если телефон на кровати
   - Вес в fusion: 10%
```

---

## КЛЮЧЕВЫЕ МЕТРИКИ

### DataQuality
- **EXCELLENT** (>80%): Микрофон отлично + Smartwatch
- **GOOD** (60-80%): Микрофон хорошо
- **FAIR** (40-60%): Микрофон средне или только Smartwatch
- **POOR** (20-40%): Слабые сигналы
- **UNUSABLE** (<20%): Данных нет

### WaveQuality
```
Score = (
    PhaseScore × 0.4 +       // Deep = 1.0, Light = 0.7, REM = 0.5
    FrequencyScore × 0.3 +   // Близость к 7.83 Hz
    SyncScore × 0.2 +        // Синхронизация с дыханием
    Confidence × 0.1         // Уверенность классификации
) × DataQualityMultiplier
```

### MQTT публикация
```
if (DataQuality >= GOOD && WaveQuality >= FAIR) {
    publish_telemetry()
}
```

---

## ЧТО СОЗДАЕМ

### Фаза 1 (3 недели): Core + Sensors
```
 НОВЫЕ МОДУЛИ:
├─ sensors/fusion/
│  ├─ TripleSensorFusion.kt           КРИТИЧНО
│  ├─ AudioBreathDetector.kt          КРИТИЧНО
│  ├─ MotionBreathDetector.kt
│  └─ WearableHealthReader.kt         КРИТИЧНО
├─ sensors/quality/
│  ├─ DataQualityMonitor.kt
│  └─ PhonePlacementDetector.kt
├─ wave/
│  └─ WaveQualityCalculator.kt        КРИТИЧНО
└─ audio/tts/
   └─ TtsPlayer.kt                    КРИТИЧНО

 ДОРАБОТАТЬ:
├─ sleep/SleepPhaseClassifier.kt     (+ DataQuality)
├─ sleep/BreathAnalyzer.kt           (+ fusion support)
└─ sensors/SensorAggregator.kt       (+ triple fusion)
```

### Фаза 2 (3 недели): Network
```
 НОВЫЕ МОДУЛИ:
├─ network/mqtt/
│  ├─ MqttManager.kt                  КРИТИЧНО
│  ├─ TelemetryPublisher.kt           КРИТИЧНО
│  └─ TelemetrySubscriber.kt
├─ network/sync/
│  ├─ SyncEngine.kt                   КРИТИЧНО
│  └─ CoherenceCalculator.kt
└─ util/
   ├─ Geolocation.kt
   ├─ UserId.kt
   └─ Geocell.kt
```

### Фаза 3 (2 недели): Polish
```
 НОВЫЕ МОДУЛИ:
├─ export/
│  ├─ SnapshotExporter.kt
│  └─ JsonSerializer.kt
├─ ui/terminal/
│  ├─ TerminalScreen.kt               КРИТИЧНО
│  └─ CommandProcessor.kt
└─ ui/minimal/
   ├─ MinimalMainScreen.kt           (переделать текущий)
   ├─ MinimalSleepScreen.kt
   └─ MinimalReportScreen.kt
```

---

##  ГОТОВАЯ БАЗА (из v0.3.9.3)

###  Используем без изменений:
- WaveCore.kt
- NightTargetModel.kt (04:30 target)
- OneShotGuard.kt (TTS/alarm protection)
- AudioEngine.kt
- BioAudioEngine.kt
- BrainWaveLibrary.kt
- WaveBreathCoupler.kt
- SmartWakeEngine.kt
- AlarmEngine.kt (проверить hard alarm)
- MotionSensor.kt
- NoiseSensor.kt
- AudioFFTAnalyzer.kt (для микрофона!)
- SleepForegroundService.kt

---

##  НОВАЯ ТЕЛЕМЕТРИЯ (MQTT)

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
    "wearable_confidence": 0.88,
    "motion_confidence": 0.45,
    "phone_placement": "nightstand",
    "primary_source": "microphone"
  },
  
  "breathing": {
    "rate_bpm": 8.5,
    "regularity": 0.91,
    "detected_by": "microphone"
  },
  
  "heart": {
    "rate_bpm": 58,
    "hrv_rmssd_ms": 42.3,
    "hrv_sdnn_ms": 48.7,
    "spo2_percent": 97,
    "device": "Galaxy Watch 4"
  },
  
  "wave_quality": {
    "score": 0.89,
    "rating": "excellent",
    "binaural_freq": 7.83
  }
}
```

---

##  NEXT STEPS (НЕМЕДЛЕННО)

### День 1-2: Environment Setup
1. [ ] Создать ветку `feature/v0.4.0-sync`
2. [ ] Обновить `build.gradle`:
   ```gradle
   // Добавить новые dependencies
   implementation "androidx.health:health-services-client:1.0.0-beta03"
   implementation "org.eclipse.paho:org.eclipse.paho.client.mqttv3:1.2.5"
   implementation "org.eclipse.paho:org.eclipse.paho.android.service:1.1.1"
   ```
3. [ ] Обновить `AndroidManifest.xml`:
   ```xml
   <!-- MQTT Service -->
   <service android:name="org.eclipse.paho.android.service.MqttService"/>
   
   <!-- Health Services (Wear OS) -->
   <uses-permission android:name="android.permission.BODY_SENSORS"/>
   <uses-permission android:name="android.permission.ACTIVITY_RECOGNITION"/>
   
   <!-- Bluetooth (Smartwatch) -->
   <uses-permission android:name="android.permission.BLUETOOTH_CONNECT"/>
   <uses-permission android:name="android.permission.BLUETOOTH_SCAN"/>
   ```

### День 3-5: Core Fusion
1. [ ] Создать `AudioBreathDetector.kt`
   - Использовать существующий `AudioFFTAnalyzer.kt`
   - Детекция дыхания (0.1-0.5 Hz)
   - SNR calculation
   - Confidence scoring

2. [ ] Создать `WearableHealthReader.kt`
   - Health Services интеграция (Wear OS)
   - Generic Bluetooth HR
   - Парсинг GATT characteristics

3. [ ] Создать `TripleSensorFusion.kt`
   - Weighted fusion (60% audio, 30% wearable, 10% motion)
   - DataQuality calculation
   - FusedSleepSignal output

### День 6-10: Sleep Classification
1. [ ] Доработать `SleepPhaseClassifier.kt`
   - Принимать FusedSleepSignal
   - Учитывать DataQuality
   - Enhanced confidence scoring

2. [ ] Создать `WaveQualityCalculator.kt`
   - Score formula implementation
   - Rating system (EXCELLENT → UNUSABLE)

3. [ ] Создать `TtsPlayer.kt`
   - Android TTS API
   - Multi-language support
   - OneShotGuard integration

### День 11-15: Testing Phase 1
1. [ ] Unit tests для fusion
2. [ ] Manual testing (1 ночь)
3. [ ] Smartwatch testing (если есть устройство)

---

##  ТЕСТОВЫЕ УСТРОЙСТВА

### Минимально необходимо:
- [x] Android телефон (API 26+)
- [ ] Тихая комната для теста микрофона

### Желательно:
- [ ] Smartwatch (Wear OS, Fitbit, или Generic HR)
- [ ] Второй телефон (для multi-user MQTT теста)

### Можно без этого (для Фазы 1):
- Cloud API tokens (Fitbit/Garmin) - для Фазы 2
- Oura Ring - не критично

---

##  DEFINITION OF DONE (Фаза 1)

### MVP Criteria:
- [x] ТЗ финализировано
- [ ] AudioBreathDetector работает (confidence >60%)
- [ ] WearableHealthReader подключается к 1+ устройству
- [ ] TripleSensorFusion корректно взвешивает источники
- [ ] DataQuality рассчитывается корректно
- [ ] SleepPhaseClassifier использует DataQuality
- [ ] WaveQuality рассчитывается
- [ ] TtsPlayer проигрывает установку в 04:15-04:45
- [ ] Прошли 1 ночь тестирования (solo, без MQTT)
- [ ] Батарея: < 10% за 8 часов
- [ ] Unit tests: coverage >60%

---

##  КОНТАКТЫ

**Разработчики:**
- Sergey Tmenov (Lead)
- Maria Tmenova (Co-Dev)
- Maya Tmenova (Co-Dev)

**Support:**
- Helen Tmenova
- Zara Tmenova
- Georgi Kozarev

**GitHub:** https://github.com/tmenov/Consciousness_changes_models/tree/main/BioKey/biokey-citizen-science  
**OSF:** osf.io/[your-project] (после Фазы 1)  
**Email:** dr.tmenov@gmail.com

---

## LET'S BUILD THIS!

**Целевая дата релиза MVP:** 8 недель от старта

**Фаза 1:** 3 недели → Solo app works  
**Фаза 2:** 3 недели → MQTT sync works  
**Фаза 3:** 2 недели → Polished & tested  

**Start date:** 2026-02-16    
**Target release:** [TBD + 8 weeks]

---

**Версия:** 1.2 FINAL  
**Дата:** 2026-02-15  
**Статус:** READY TO CODE  

---

Все готово! Можно начинать разработку!

END OF CHECKLIST
