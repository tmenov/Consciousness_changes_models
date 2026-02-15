# ТЕХНИЧЕСКОЕ ЗАДАНИЕ
## BioKey v0.3.9.3_ME → v0.4.0_SYNC (Базовая версия для запуска)

---

## ФИНАЛЬНАЯ КОНФИГУРАЦИЯ v0.4.0_SYNC

### СОГЛАСОВАННЫЕ ПАРАМЕТРЫ

1. **MQTT Broker:** HiveMQ Cloud (публичный, free tier)
2. **Терминал:** Включен в MVP (отладка + power users)
3. **DataQuality порог:** GOOD+ (≥60%) для MQTT публикации
4. **Микрофон duty cycle:** 50% (15 сек ON / 15 сек OFF)
5. **Smartwatch:** Полная интеграция (HR, HRV, SpO2, BP)
6. **UI:** Минимализм, terminal-style (одним листом, прокрутка)

### Приоритет сенсоров (окончательный):

```
1. МИКРОФОН (главный)        - детекция дыхания, фаз сна
2. SMARTWATCH (если есть)    - HR, HRV, SpO2, BP (телеметрия + достоверность)
3. АКСЕЛЕРОМЕТР (вторичный)  - подтверждение, если телефон на кровати
```

---

### Научное обоснование
**Резонатор Земля-Ионосфера:**
- Резонанс Шумана (7.83 Hz, 14.3 Hz, 20.8 Hz, 27.3 Hz, 33.8 Hz)
- Ионосфера как полый сферический резонатор (высота ~100 км)
- Распространение электромагнитных волн в ионосфере
- Интерференция и дифракция волн в замкнутом резонаторе

**Биоэлектрическая синхронизация:**
- Теория морфостатической информации (Levin, 2024) как базис
- Групповая когерентность мозговых ритмов
- Синхронизация через общий резонатор (ионосфера)
- Эффект умножения при когерентной суперпозиции

**Отличие от коммерческих решений:**
- НЕ продукт - открытая технология
- НЕ патентуется - защита через публикацию
- НЕ монетизируется - полностью бесплатно
- Цель: предотвратить патентование + citizen science

---

## ТЕКУЩЕЕ СОСТОЯНИЕ (v0.3.9.3_ME)

### Что работает:
 Wave Engine (детерминистический фазовый осциллятор)
 Эмуляция биометрических сигналов (HR, дыхание)
 Android Audio API (временная база)
 Архитектура: Data Layer → Wave Engine → UI
 Real-time визуализация

### Что НЕ работает:
 Реальные сенсоры (только эмуляция)
 Детекция фаз сна
 Аудио-стимуляция (бинауральные ритмы)
 TTS установка
 Будильник (умный и обычный)
 Сетевая синхронизация
 Экспорт данных
 Геолокация

---

## ЦЕЛЕВАЯ ВЕРСИЯ (v0.4.0_SYNC)

### Философия:
- **Минимализм:** Только критичные функции для proof-of-concept
- **Открытость:** Весь код GPL-3.0, никаких секретов
- **Надежность:** Работает оффлайн, не зависит от серверов
- **Масштабируемость:** P2P архитектура через MQTT
- **Научность:** Логирование всех параметров для анализа

---

## ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### FR-1: БУДИЛЬНИК

#### FR-1.1: Жесткий будильник
**Описание:** Классический будильник с фиксированным временем
**UI:**
```
[Установить будильник]
Время: [06] : [30]
Повтор: [ ] Пн [ ] Вт [x] Ср [x] Чт [x] Пт [ ] Сб [ ] Вс
Звук: [Выбрать] → thunder_rain_looped.wav
Громкость: [▓▓▓▓▓▓▓▓░░] 80%
[Сохранить]
```

**Логика:**
- Срабатывает точно в указанное время
- Постепенное увеличение громкости (fade-in 30 сек)
- Вибрация + звук
- Кнопки: [Отложить на 10 мин] [Выключить]

**Технические детали:**
- AlarmManager для надежности (работает даже если app убит)
- Foreground Service для гарантированного срабатывания
- WakeLock для пробуждения экрана

#### FR-1.2: Умный будильник (Smart Wake)
**Описание:** Будильник с окном просыпания в легкой фазе сна

**UI:**
```
[Умный будильник]
Целевое время: [07] : [00]
Окно поиска: 
  [ ] Только до (-30 мин)
  [x] До и после (±30 мин)
  [ ] Только после (+30 мин)
  
Результат: будет звонить между 06:30 - 07:30
Звук: [Выбрать] → ocean_performance_soft_looped.wav
[Сохранить]
```

**Логика:**
1. В период [06:30 - 07:30] анализировать фазу сна каждые 30 сек
2. Искать оптимальный момент (критерии):
   - Легкий сон (Light sleep) OR
   - REM фаза OR
   - Движение (пользователь ворочается)
3. Если найден → срабатывает немедленно
4. Если не найден до 07:30 → срабатывает в 07:30 принудительно

**Определение "легкой фазы":**
```kotlin
fun isGoodWakeWindow(sensorData: SensorData): Boolean {
    return when {
        sensorData.movement > MOVEMENT_THRESHOLD -> true // Ворочается
        sensorData.hr > sensorData.averageHR + 5 -> true // ЧСС повышен
        sensorData.sleepStage == SleepStage.LIGHT -> true
        sensorData.sleepStage == SleepStage.REM -> true
        else -> false
    }
}
```

---

### FR-2: БИНАУРАЛЬНЫЕ РИТМЫ

#### FR-2.1: Непрерывное проигрывание
**Описание:** Бинауральные ритмы играют всю ночь до будильника

**Параметры:**
- **Базовый фон:** ocean_performance_soft_looped.wav (непрерывно)
- **Бинауральная частота:** Динамическая, зависит от фазы сна
  - Засыпание: 8-12 Hz (Alpha)
  - Легкий сон: 4-8 Hz (Theta)
  - Глубокий сон: 0.5-4 Hz (Delta)
  - REM: 8-13 Hz (Alpha/Theta border)
  - Подготовка к TTS (04:00-04:15): 7.83 Hz (резонанс Шумана)

**Технология:**
- Левый канал: Базовая частота (например, 200 Hz)
- Правый канал: Базовая + дельта (например, 207.83 Hz)
- Мозг воспринимает разницу: 7.83 Hz

**Реализация:**
```kotlin
class BinauralGenerator {
    private val baseFreq = 200.0 // Hz
    
    fun generate(targetFreq: Double): ShortArray {
        val leftFreq = baseFreq
        val rightFreq = baseFreq + targetFreq
        
        // Generate stereo audio buffer
        val buffer = ShortArray(SAMPLE_RATE) // 1 second
        for (i in buffer.indices) {
            val t = i.toDouble() / SAMPLE_RATE
            val left = (sin(2 * PI * leftFreq * t) * AMPLITUDE).toInt()
            val right = (sin(2 * PI * rightFreq * t) * AMPLITUDE).toInt()
            buffer[i] = left.toShort() // Interleaved stereo
            buffer[i+1] = right.toShort()
        }
        return buffer
    }
}
```

#### FR-2.2: Адаптация к дыханию пользователя
**Описание:** Синхронизация бинауральных ритмов с дыханием

**Логика:**
1. Акселерометр детектирует ритм дыхания (грудная клетка поднимается/опускается)
2. Рассчитываем частоту дыхания (breaths per minute, BPM)
3. Плавно подстраиваем бинауральную частоту:
   - Быстрое дыхание (>15 BPM) → повышаем частоту
   - Медленное дыхание (<10 BPM) → понижаем частоту
4. Цель: Создать биофидбек-петлю (дыхание ↔ бинауралка)

**Алгоритм:**
```kotlin
fun adaptToBreathing(breathingRate: Double, currentFreq: Double): Double {
    val targetFreq = when {
        breathingRate > 15 -> 10.0 // Активное состояние
        breathingRate in 10.0..15.0 -> 7.83 // Нормальное (Schumann)
        else -> 4.0 // Глубокий сон
    }
    
    // Плавный переход (exponential moving average)
    val alpha = 0.1 // Коэффициент сглаживания
    return alpha * targetFreq + (1 - alpha) * currentFreq
}
```

---

### FR-3: TTS УСТАНОВКА

#### FR-3.1: Текст установки
**Оригинал (русский):** "Я за здоровье и долголетие"
**Английский:** "I am for health and longevity"

**Другие языки (определяется автоматически):**
- Испанский: "Estoy por la salud y la longevidad"
- Немецкий: "Ich bin für Gesundheit und Langlebigkeit"
- Французский: "Je suis pour la santé et la longévité"
- Китайский: "我支持健康和长寿"
- Японский: "私は健康と長寿を支持します"

#### FR-3.2: Параметры воспроизведения
**Окно:** 04:15 - 04:45 (30 минут)
**Условия запуска:**
1. Пользователь в фазе глубокого сна (N3)
2. Бинауральная частота = 7.83 Hz (резонанс Шумана)
3. Дыхание медленное и ритмичное (<10 BPM)
4. Низкая двигательная активность

**Если условия НЕ выполнены к 04:45:**
- Запустить принудительно в 04:45
- Логировать: "TTS forced trigger (conditions not met)"

**Параметры TTS:**
```kotlin
val ttsParams = Bundle().apply {
    putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 0.3f) // Тихо, 30%
    putFloat(TextToSpeech.Engine.KEY_PARAM_PAN, 0f) // Центр (оба канала)
    putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, "morning_affirmation")
}

tts.speak(
    affirmationText,
    TextToSpeech.QUEUE_FLUSH,
    ttsParams,
    "affirmation_id"
)
```

**Повторение:**
- 3 раза с паузой 15 секунд между повторениями
- Итого: ~45 секунд

#### FR-3.3: Язык определяется автоматически
```kotlin
val locale = Locale.getDefault()
val affirmationText = when (locale.language) {
    "ru" -> "Я за здоровье и долголетие"
    "es" -> "Estoy por la salud y la longevidad"
    "de" -> "Ich bin für Gesundheit und Langlebigkeit"
    "fr" -> "Je suis pour la santé et la longévité"
    "zh" -> "我支持健康和长寿"
    "ja" -> "私は健康と長寿を支持します"
    else -> "I am for health and longevity" // English default
}
```

---

### FR-4: ДЕТЕКЦИЯ ФАЗ СНА

#### FR-4.1: Входные данные (Triple-Sensor Architecture)

**ПРИОРИТЕТ №1: МИКРОФОН (главный сенсор)**
```kotlin
// Существующий: NoiseSensor.kt
class NoiseSensor {
    // Частота: 16 kHz (достаточно для речи/дыхания)
    // Анализ: FFT для выделения дыхания из шума
    // Дальность: До 5 метров в тишине
    // Duty cycle: 50% (15s ON / 15s OFF)
    // Сценарий: Телефон на тумбочке / столе
}
```

**Детектируем:**
- **Дыхание (primary):** Ритмичные низкочастотные звуки (0.1-0.5 Hz)
- **Храп:** Пики на 150-300 Hz
- **Бормотание во сне:** Речевой диапазон (300-3000 Hz)
- **Тишина:** Глубокий сон или пробуждение
- **Фоновый шум:** Для калибровки порога

**Duty Cycle (экономия батареи):**
```kotlin
class MicrophoneDutyCycle {
    private val onDuration = 15_000L  // 15 сек ON
    private val offDuration = 15_000L // 15 сек OFF
    
    fun shouldRecordNow(): Boolean {
        val cycleTime = System.currentTimeMillis() % (onDuration + offDuration)
        return cycleTime < onDuration
    }
}
```

---

**ПРИОРИТЕТ №2: SMARTWATCH (если подключен)**

#### Стандартные метрики всех smartwatch:

**Health & Fitness Standards:**
- **Bluetooth LE GATT** (Generic Attribute Profile)
  - Heart Rate Service (0x180D)
  - Blood Pressure Service (0x1810)
  - Health Thermometer Service (0x1809)

**Supported devices & protocols:**
1. **Wear OS** (Samsung Galaxy Watch, Pixel Watch)
   - Health Services API
   - HR, Steps, Sleep stages
   
2. **Apple Watch** (через HealthKit на iOS)
   - HR, HRV, SpO2, ECG, Sleep
   
3. **Fitbit** (Charge, Versa, Sense)
   - Web API (OAuth)
   - HR, HRV, SpO2, Sleep stages, Skin temp
   
4. **Garmin** (Forerunner, Venu, Fenix)
   - Connect IQ API
   - HR, HRV, SpO2, Sleep, Stress
   
5. **Polar** (H10, Verity Sense)
   - Bluetooth HR strap
   - HR, HRV (RMSSD, SDNN)
   
6. **Oura Ring**
   - Cloud API
   - HR, HRV, SpO2, Temp, Sleep stages
   
7. **Whoop**
   - Cloud API
   - HR, HRV, Strain, Recovery

**Общие метрики (core set):**
```kotlin
data class SmartwatchData(
    // ОБЯЗАТЕЛЬНЫЕ (все устройства)
    val heartRate: Float,              // BPM (ударов в минуту)
    val timestamp: Long,
    
    // РЕКОМЕНДУЕМЫЕ (большинство устройств)
    val hrvRmssd: Float?,              // HRV RMSSD (ms)
    val hrvSdnn: Float?,               // HRV SDNN (ms)
    val spo2: Float?,                  // SpO2 (% насыщение кислородом)
    
    // ОПЦИОНАЛЬНЫЕ (premium устройства)
    val bloodPressureSystolic: Int?,   // Систолическое давление (mmHg)
    val bloodPressureDiastolic: Int?,  // Диастолическое давление (mmHg)
    val skinTemperature: Float?,       // Температура кожи (°C)
    val respiratoryRate: Float?,       // Частота дыхания (BPM)
    val stressLevel: Float?,           // Уровень стресса (0-100)
    
    // МЕТАДАННЫЕ
    val deviceModel: String,           // "Galaxy Watch 4", "Oura Ring", etc
    val confidence: Float              // Качество сигнала (0-1)
)
```

#### Интеграция с Android:

**Wear OS Health Services:**
```kotlin
// Используем Health Services API (Android)
class WearOsHealthReader {
    
    private val healthClient: HealthServicesClient = 
        HealthServices.getClient(context)
    
    suspend fun startHeartRateStream(): Flow<SmartwatchData> {
        return healthClient.measureClient
            .registerMeasureCallback(
                DataType.HEART_RATE_BPM
            )
            .map { update ->
                SmartwatchData(
                    heartRate = update.getData(DataType.HEART_RATE_BPM).first().value,
                    hrvRmssd = tryGetHrv(update),
                    spo2 = tryGetSpO2(update),
                    timestamp = System.currentTimeMillis(),
                    deviceModel = getDeviceModel(),
                    confidence = calculateConfidence(update)
                )
            }
    }
}
```

**Fitbit / Garmin (Cloud APIs):**
```kotlin
// OAuth 2.0 подключение
class CloudWearableReader(
    private val apiClient: WearableApiClient
) {
    suspend fun fetchLatestMetrics(): SmartwatchData? {
        val response = apiClient.getHeartRate(
            date = LocalDate.now(),
            detailLevel = "1min"
        )
        
        return response?.let {
            SmartwatchData(
                heartRate = it.value.last().bpm,
                hrvRmssd = it.hrv?.rmssd,
                spo2 = it.spo2?.value,
                // ...
            )
        }
    }
}
```

**Bluetooth LE (generic HR straps):**
```kotlin
// Для устройств без специального API
class BluetoothHeartRateReader {
    
    private val hrServiceUuid = UUID.fromString("0000180d-0000-1000-8000-00805f9b34fb")
    
    fun connectAndStream(device: BluetoothDevice): Flow<SmartwatchData> {
        return flow {
            val gatt = device.connectGatt(context, false, gattCallback)
            
            gatt.getService(hrServiceUuid)
                ?.getCharacteristic(HR_MEASUREMENT_UUID)
                ?.let { characteristic ->
                    gatt.setCharacteristicNotification(characteristic, true)
                    
                    // Получаем HR updates
                    gattCallback.onCharacteristicChanged
                        .collect { value ->
                            emit(parseHrValue(value))
                        }
                }
        }
    }
}
```

---

**ПРИОРИТЕТ №3: АКСЕЛЕРОМЕТР (вторичный)**
```kotlin
// Существующий: MotionSensor.kt
class MotionSensor {
    // Частота: 50 Hz
    // Оси: X, Y, Z
    // Сценарий: Телефон на кровати рядом с пользователем
}
```

---

#### FR-4.2: Fusion Algorithm (Тройная интеграция)

**Новая архитектура:**
```
[Микрофон]    [Smartwatch]    [Акселерометр]
     ↓              ↓                ↓
[AudioBreath]  [WearableHR]   [MotionBreath]
  Detector       Reader          Detector
     ↓              ↓                ↓
     └──────────────┴────────────────┘
                    ↓
          [TripleSensorFusion]
                    ↓
         [FusedSleepSignal]
    (breathing, HR, HRV, movement,
     dataQuality, confidence)
```

**Обновленный SensorFusion:**
```kotlin
class TripleSensorFusion {
    
    private val audioDetector = AudioBreathDetector()
    private val motionDetector = MotionBreathDetector()
    
    fun fuse(
        audioBuffer: ShortArray?,
        smartwatchData: SmartwatchData?,
        motionFrame: SensorFrame?
    ): FusedSleepSignal {
        
        // 1. Получаем сигналы от всех источников
        val audioSignal = audioBuffer?.let { audioDetector.analyzeAudioFrame(it) }
        val wearableSignal = smartwatchData // Уже готовые метрики
        val motionSignal = motionFrame?.let { motionDetector.analyzeMotionFrame(it) }
        
        // 2. Рассчитываем веса (приоритет микрофону)
        val audioWeight = audioSignal?.confidence ?: 0f
        val wearableWeight = wearableSignal?.confidence ?: 0f
        val motionWeight = motionSignal?.confidence ?: 0f
        
        // Приоритеты:
        // - Микрофон всегда главный (если работает)
        // - Smartwatch дополняет (HR, HRV, SpO2)
        // - Акселерометр подтверждает (если телефон на кровати)
        
        val totalWeight = audioWeight + (wearableWeight * 0.5f) + (motionWeight * 0.3f)
        
        // 3. DataQuality зависит в основном от микрофона
        val dataQuality = when {
            audioWeight > 0.8f && wearableWeight > 0.6f -> DataQuality.EXCELLENT
            audioWeight > 0.6f -> DataQuality.GOOD
            audioWeight > 0.4f || wearableWeight > 0.6f -> DataQuality.FAIR
            totalWeight > 0.2f -> DataQuality.POOR
            else -> DataQuality.UNUSABLE
        }
        
        // 4. Дыхание - из микрофона (primary)
        val breathingRate = audioSignal?.rate ?: wearableSignal?.respiratoryRate ?: 0f
        
        // 5. HR/HRV - из smartwatch (если есть)
        val heartRate = wearableSignal?.heartRate
        val hrv = wearableSignal?.hrvRmssd
        val spo2 = wearableSignal?.spo2
        
        return FusedSleepSignal(
            detected = dataQuality >= DataQuality.FAIR,
            confidence = calculateOverallConfidence(audioWeight, wearableWeight, motionWeight),
            dataQuality = dataQuality,
            
            // Дыхание (из микрофона)
            breathingRate = breathingRate,
            breathingRegularity = audioSignal?.regularity ?: 0f,
            
            // Сердце (из smartwatch)
            heartRate = heartRate,
            hrv = hrv,
            spo2 = spo2,
            bloodPressure = wearableSignal?.let {
                BloodPressure(it.bloodPressureSystolic, it.bloodPressureDiastolic)
            },
            
            // Движение (из акселерометра)
            movementIntensity = motionSignal?.amplitude ?: 0f,
            
            // Метаданные
            placement = estimatePlacement(audioWeight, motionWeight),
            primarySource = when {
                audioWeight > 0.5f -> SensorSource.MICROPHONE
                wearableWeight > 0.5f -> SensorSource.SMARTWATCH
                else -> SensorSource.ACCELEROMETER
            },
            wearableConnected = wearableSignal != null,
            wearableModel = wearableSignal?.deviceModel,
            
            timestamp = System.currentTimeMillis()
        )
    }
    
    private fun calculateOverallConfidence(
        audio: Float,
        wearable: Float,
        motion: Float
    ): Float {
        // Взвешенное среднее с приоритетом микрофону
        return (audio * 0.6f + wearable * 0.3f + motion * 0.1f).coerceIn(0f, 1f)
    }
}

data class FusedSleepSignal(
    val detected: Boolean,
    val confidence: Float,
    val dataQuality: DataQuality,
    
    // Дыхание (микрофон)
    val breathingRate: Float,
    val breathingRegularity: Float,
    
    // Сердце (smartwatch)
    val heartRate: Float?,
    val hrv: Float?,
    val spo2: Float?,
    val bloodPressure: BloodPressure?,
    
    // Движение (акселерометр)
    val movementIntensity: Float,
    
    // Метаданные
    val placement: PhonePlacement,
    val primarySource: SensorSource,
    val wearableConnected: Boolean,
    val wearableModel: String?,
    val timestamp: Long
)

enum class SensorSource {
    MICROPHONE,
    SMARTWATCH,
    ACCELEROMETER
}

data class BloodPressure(
    val systolic: Int?,
    val diastolic: Int?
)
```

---

#### FR-4.3: Обновленная телеметрия (с smartwatch данными)

**Новый формат MQTT телеметрии:**
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
    "detected_by": "smartwatch",
    "device": "Galaxy Watch 4"
  },
  
  "blood_pressure": {
    "systolic_mmhg": 118,
    "diastolic_mmhg": 76,
    "detected_by": "smartwatch"
  },
  
  "wave_quality": {
    "score": 0.89,
    "rating": "excellent",
    "binaural_freq": 7.83
  },
  
  "movement_index": 2.1
}
```

**Фильтр публикации (обновлен):**
```kotlin
class MqttQualityFilter {
    
    fun shouldPublish(dataQuality: DataQuality): Boolean {
        // Публикуем только GOOD+ (≥60%)
        return dataQuality in listOf(
            DataQuality.EXCELLENT,  // >80%
            DataQuality.GOOD        // 60-80%
        )
        // FAIR, POOR, UNUSABLE - не публикуются
    }
}
```

**МИКРОФОН (ПРИОРИТЕТ №1 - Главный сенсор):**
```kotlin
// Существующий: NoiseSensor.kt
class NoiseSensor {
    // Частота: 16 kHz (достаточно для речи/дыхания)
    // Анализ: FFT для выделения дыхания из шума
    // Дальность: До 5 метров в тишине
    // Сценарий: Телефон на тумбочке / столе
}
```

**Что детектируем:**
- **Дыхание (primary):** Ритмичные низкочастотные звуки (0.1-0.5 Hz)
- **Храп:** Пики на 150-300 Hz
- **Бормотание/разговор во сне:** Речевой диапазон (300-3000 Hz)
- **Тишина:** Глубокий сон или пробуждение
- **Фоновый шум:** Для калибровки порога

**Алгоритм обработки звука:**
```kotlin
// Существующий: BreathAnalyzer.kt (использовать как основу)
class AudioBreathDetector {
    
    private val breathingFreqRange = 0.1f..0.5f // Hz (6-30 BPM)
    
    fun analyzeAudioFrame(audioBuffer: ShortArray): BreathSignal {
        // 1. FFT на аудио буфере
        val spectrum = fft(audioBuffer)
        
        // 2. Выделение дыхательного диапазона
        val breathPower = spectrum
            .filterKeys { it in breathingFreqRange }
            .values.sum()
        
        // 3. Детекция вдоха/выдоха по пикам
        val isBreathEvent = breathPower > adaptiveThreshold
        
        // 4. Расчет BPM
        val bpm = detectBreathingRate(spectrum)
        
        return BreathSignal(
            detected = breathPower > noiseFloor * 2,
            confidence = calculateConfidence(breathPower, noiseFloor),
            rate = bpm,
            amplitude = breathPower,
            timestamp = System.currentTimeMillis()
        )
    }
    
    private fun calculateConfidence(signal: Float, noise: Float): Float {
        val snr = signal / noise // Signal-to-Noise Ratio
        return when {
            snr > 10 -> 1.0f  // Отлично (>20 dB)
            snr > 5  -> 0.8f  // Хорошо (>14 dB)
            snr > 3  -> 0.6f  // Средне (>9 dB)
            snr > 2  -> 0.4f  // Плохо (>6 dB)
            else     -> 0.2f  // Очень плохо
        }
    }
}
```

---

**АКСЕЛЕРОМЕТР (ВТОРИЧНЫЙ - Подтверждающий сенсор):**
```kotlin
// Существующий: MotionSensor.kt
class MotionSensor {
    // Частота: 50 Hz
    // Оси: X, Y, Z
    // Сценарий: Телефон на кровати рядом с пользователем
}
```

**Что детектируем:**
- **Движения тела:** Ворочание, смена позы
- **Дыхание (если телефон на груди):** Вибрации грудной клетки
- **Активность:** Пользователь встал (spike в acceleration)
- **Положение телефона:** Стабильное или движется

**Алгоритм обработки движения:**
```kotlin
// Существующий: SensorAggregator.kt (доработать)
class MotionBreathDetector {
    
    fun analyzeMotionFrame(sensorFrame: SensorFrame): BreathSignal {
        // 1. Вычисляем magnitude
        val magnitude = sqrt(
            sensorFrame.x.pow(2) + 
            sensorFrame.y.pow(2) + 
            sensorFrame.z.pow(2)
        )
        
        // 2. Высокочастотная фильтрация (движения тела)
        val movement = highPassFilter(magnitude, cutoff = 0.5f) // > 0.5 Hz
        
        // 3. Низкочастотная фильтрация (дыхание)
        val breathing = lowPassFilter(magnitude, cutoff = 0.5f) // < 0.5 Hz
        
        // 4. Определяем confidence на основе стабильности
        val stability = 1.0f - (movement / (breathing + 1e-6f)).coerceIn(0f, 1f)
        
        return BreathSignal(
            detected = breathing > motionThreshold,
            confidence = stability,
            rate = detectPeaks(breathing),
            amplitude = breathing,
            timestamp = System.currentTimeMillis()
        )
    }
}
```

---

#### FR-4.2: Fusion Algorithm (Объединение сенсоров)

**Существующий модуль:** `SensorAggregator.kt` - использовать как основу

**Сценарии размещения телефона:**

| Сценарий | Микрофон | Акселерометр | Приоритет |
|----------|----------|--------------|-----------|
| **Тумбочка (30-100 см)** | Отлично | Не работает | Микрофон 100% |
| **Стол (100-500 см)** | Средне | Не работает | Микрофон 100% |
| **На кровати (далеко)** | Хорошо | Слабо | Микрофон 80%, Аксель 20% |
| **Рядом на кровати** | Хорошо | Хорошо | Микрофон 60%, Аксель 40% |
| **На груди** | Отлично | Отлично | Микрофон 50%, Аксель 50% |

**Алгоритм fusion:**
```kotlin
// Новый модуль: SensorFusion.kt
class SensorFusion {
    
    private val audioDetector = AudioBreathDetector()
    private val motionDetector = MotionBreathDetector()
    
    fun fuse(
        audioBuffer: ShortArray?,
        motionFrame: SensorFrame?
    ): FusedBreathSignal {
        
        // 1. Получаем сигналы от обоих сенсоров
        val audioSignal = audioBuffer?.let { audioDetector.analyzeAudioFrame(it) }
        val motionSignal = motionFrame?.let { motionDetector.analyzeMotionFrame(it) }
        
        // 2. Определяем веса на основе confidence
        val audioWeight = audioSignal?.confidence ?: 0f
        val motionWeight = motionSignal?.confidence ?: 0f
        val totalWeight = audioWeight + motionWeight
        
        // 3. Если оба не работают - возвращаем null
        if (totalWeight < 0.3f) {
            return FusedBreathSignal(
                detected = false,
                confidence = 0f,
                dataQuality = DataQuality.POOR,
                placement = estimatePlacement(audioWeight, motionWeight)
            )
        }
        
        // 4. Взвешенное среднее
        val fusedRate = if (totalWeight > 0) {
            ((audioSignal?.rate ?: 0f) * audioWeight + 
             (motionSignal?.rate ?: 0f) * motionWeight) / totalWeight
        } else 0f
        
        val fusedConfidence = totalWeight / 2f // Нормализуем
        
        // 5. Определяем качество данных
        val dataQuality = when {
            fusedConfidence > 0.8f -> DataQuality.EXCELLENT
            fusedConfidence > 0.6f -> DataQuality.GOOD
            fusedConfidence > 0.4f -> DataQuality.FAIR
            fusedConfidence > 0.2f -> DataQuality.POOR
            else -> DataQuality.UNUSABLE
        }
        
        return FusedBreathSignal(
            detected = true,
            confidence = fusedConfidence,
            rate = fusedRate,
            dataQuality = dataQuality,
            placement = estimatePlacement(audioWeight, motionWeight),
            audioContribution = audioWeight / totalWeight,
            motionContribution = motionWeight / totalWeight
        )
    }
    
    private fun estimatePlacement(audioConf: Float, motionConf: Float): PhonePlacement {
        return when {
            audioConf > 0.7f && motionConf < 0.3f -> PhonePlacement.NIGHTSTAND
            audioConf > 0.5f && motionConf < 0.4f -> PhonePlacement.TABLE_FAR
            audioConf > 0.5f && motionConf > 0.5f -> PhonePlacement.ON_CHEST
            audioConf > 0.4f && motionConf > 0.3f -> PhonePlacement.BED_NEARBY
            else -> PhonePlacement.UNKNOWN
        }
    }
}

data class FusedBreathSignal(
    val detected: Boolean,
    val confidence: Float,
    val rate: Float = 0f,
    val dataQuality: DataQuality,
    val placement: PhonePlacement,
    val audioContribution: Float = 0f,
    val motionContribution: Float = 0f,
    val timestamp: Long = System.currentTimeMillis()
)

enum class DataQuality {
    EXCELLENT,  // >80% confidence
    GOOD,       // 60-80%
    FAIR,       // 40-60%
    POOR,       // 20-40%
    UNUSABLE    // <20%
}

enum class PhonePlacement {
    ON_CHEST,      // На груди (оба сенсора отлично)
    BED_NEARBY,    // Рядом на кровати (оба работают)
    NIGHTSTAND,    // Тумбочка (только микрофон)
    TABLE_FAR,     // Стол далеко (только микрофон, слабо)
    UNKNOWN        // Непонятно
}
```

---

#### FR-4.3: Классификация фаз сна (с учетом качества данных)

**Существующий модуль:** `SleepPhaseClassifier.kt` - доработать с учетом DataQuality

**Модель классификации (улучшенная):**
```kotlin
// Доработка существующего SleepPhaseClassifier.kt
class EnhancedSleepPhaseClassifier {
    
    fun classify(
        fusedSignal: FusedBreathSignal,
        heartRate: Float?,
        history: List<SleepPhase>
    ): SleepPhaseResult {
        
        // 1. Если данные плохие - помечаем как UNCERTAIN
        if (fusedSignal.dataQuality == DataQuality.UNUSABLE) {
            return SleepPhaseResult(
                phase = SleepPhase.UNKNOWN,
                confidence = 0f,
                dataQuality = fusedSignal.dataQuality
            )
        }
        
        // 2. Извлекаем признаки
        val features = extractFeatures(fusedSignal, heartRate, history)
        
        // 3. Классифицируем
        val phase = when {
            // AWAKE: Нерегулярное дыхание, высокая активность
            features.breathingRegularity < 0.5f -> SleepPhase.AWAKE
            
            // DEEP: Очень регулярное медленное дыхание
            features.breathingRate < 10f && 
            features.breathingRegularity > 0.8f &&
            features.stability > 0.9f -> SleepPhase.DEEP
            
            // REM: Нерегулярное дыхание + низкая активность + после deep
            features.breathingRegularity < 0.7f &&
            features.stability > 0.7f &&
            history.lastOrNull() == SleepPhase.DEEP -> SleepPhase.REM
            
            // LIGHT: Все остальное
            else -> SleepPhase.LIGHT
        }
        
        // 4. Уверенность зависит от качества данных
        val phaseConfidence = when (fusedSignal.dataQuality) {
            DataQuality.EXCELLENT -> 0.95f
            DataQuality.GOOD -> 0.80f
            DataQuality.FAIR -> 0.60f
            DataQuality.POOR -> 0.40f
            DataQuality.UNUSABLE -> 0f
        }
        
        return SleepPhaseResult(
            phase = phase,
            confidence = phaseConfidence,
            dataQuality = fusedSignal.dataQuality,
            features = features
        )
    }
    
    private fun extractFeatures(
        signal: FusedBreathSignal,
        heartRate: Float?,
        history: List<SleepPhase>
    ): SleepFeatures {
        // Анализ последних 5 минут истории
        val recentBreathing = historyBuffer.takeLast(600) // 5 min × 2 samples/sec
        
        return SleepFeatures(
            breathingRate = signal.rate,
            breathingRegularity = calculateRegularity(recentBreathing),
            stability = signal.confidence,
            heartRate = heartRate,
            timeInPhase = calculateTimeInCurrentPhase(history)
        )
    }
    
    private fun calculateRegularity(samples: List<Float>): Float {
        if (samples.size < 10) return 0f
        
        // Стандартное отклонение дыхания (чем меньше - тем регулярнее)
        val mean = samples.average()
        val variance = samples.map { (it - mean).pow(2) }.average()
        val stdDev = sqrt(variance)
        
        // Нормализуем: регулярность = 1 - (stdDev / mean)
        return (1f - (stdDev / mean).toFloat()).coerceIn(0f, 1f)
    }
}

data class SleepPhaseResult(
    val phase: SleepPhase,
    val confidence: Float,
    val dataQuality: DataQuality,
    val features: SleepFeatures? = null
)

data class SleepFeatures(
    val breathingRate: Float,
    val breathingRegularity: Float,
    val stability: Float,
    val heartRate: Float?,
    val timeInPhase: Int
)

enum class SleepPhase {
    AWAKE,
    LIGHT,
    DEEP,
    REM,
    UNKNOWN  // Когда данных недостаточно
}
```

---

#### FR-4.4: Расчет качества волны (Wave Quality Score)

**Новый модуль:** `WaveQualityCalculator.kt`

**Концепция:** Качество волны = насколько хорошо пользователь синхронизирован с резонансом Шумана

```kotlin
class WaveQualityCalculator {
    
    private val schumannResonance = 7.83f // Hz
    
    fun calculate(
        sleepPhase: SleepPhaseResult,
        binauralFreq: Float,
        breathingSync: Float,
        dataQuality: DataQuality
    ): WaveQuality {
        
        // 1. Оценка фазы сна (Deep = лучше всего)
        val phaseScore = when (sleepPhase.phase) {
            SleepPhase.DEEP -> 1.0f
            SleepPhase.LIGHT -> 0.7f
            SleepPhase.REM -> 0.5f
            SleepPhase.AWAKE -> 0.0f
            SleepPhase.UNKNOWN -> 0.0f
        }
        
        // 2. Оценка соответствия резонансу Шумана
        val freqDeviation = abs(binauralFreq - schumannResonance)
        val freqScore = (1f - (freqDeviation / 10f)).coerceIn(0f, 1f)
        
        // 3. Оценка синхронизации дыхания с бинауралкой
        val syncScore = breathingSync.coerceIn(0f, 1f)
        
        // 4. Штраф за плохое качество данных
        val qualityMultiplier = when (dataQuality) {
            DataQuality.EXCELLENT -> 1.0f
            DataQuality.GOOD -> 0.9f
            DataQuality.FAIR -> 0.7f
            DataQuality.POOR -> 0.5f
            DataQuality.UNUSABLE -> 0.0f
        }
        
        // 5. Взвешенная сумма
        val rawScore = (
            phaseScore * 0.4f +
            freqScore * 0.3f +
            syncScore * 0.2f +
            sleepPhase.confidence * 0.1f
        ) * qualityMultiplier
        
        return WaveQuality(
            score = rawScore,
            phaseContribution = phaseScore,
            frequencyContribution = freqScore,
            syncContribution = syncScore,
            dataQuality = dataQuality,
            rating = when {
                rawScore > 0.9f -> WaveRating.EXCELLENT
                rawScore > 0.7f -> WaveRating.GOOD
                rawScore > 0.5f -> WaveRating.FAIR
                rawScore > 0.3f -> WaveRating.POOR
                else -> WaveRating.UNUSABLE
            }
        )
    }
}

data class WaveQuality(
    val score: Float,              // 0.0 - 1.0
    val phaseContribution: Float,
    val frequencyContribution: Float,
    val syncContribution: Float,
    val dataQuality: DataQuality,
    val rating: WaveRating
)

enum class WaveRating {
    EXCELLENT,  // >90% - идеальная синхронизация
    GOOD,       // 70-90% - хорошая
    FAIR,       // 50-70% - средняя
    POOR,       // 30-50% - плохая
    UNUSABLE    // <30% - не используется для MQTT
}
```

---

#### FR-4.5: Интеграция с существующими модулями

**Что уже есть (из снапа):**
- `BreathAnalyzer.kt` - анализ дыхания
- `SleepPhaseDetector.kt` - детекция фаз
- `SleepPhaseClassifier.kt` - классификация
- `MotionSensor.kt` - акселерометр
- `NoiseSensor.kt` - микрофон
- `SensorAggregator.kt` - агрегация сенсоров
- `SleepSignalProcessor.kt` - обработка сигналов

**Что нужно добавить:**
- `SensorFusion.kt` - объединение микрофон + акселерометр
- `WaveQualityCalculator.kt` - расчет качества волны
- `DataQualityMonitor.kt` - мониторинг качества в реальном времени

**Архитектура обработки:**
```
[Микрофон]           [Акселерометр]
     ↓                      ↓
[AudioBreathDetector] [MotionBreathDetector]
     ↓                      ↓
     └──────────┬──────────┘
                ↓
        [SensorFusion]
                ↓
      [FusedBreathSignal]
                ↓
   [EnhancedSleepPhaseClassifier]
                ↓
       [SleepPhaseResult]
                ↓
   [WaveQualityCalculator]
                ↓
         [WaveQuality]
                ↓
      [MQTT Publisher] (только если quality > FAIR)
```

---

#### FR-4.6: Экспорт метрик качества (для MQTT и логов)

**Телеметрия с метриками качества:**
```json
{
  "user_id": "geo_990_1005_a3f9c2d8_1709596800",
  "timestamp": 1709596830,
  
  "sleep_phase": {
    "current": "deep",
    "confidence": 0.95,
    "time_in_phase_min": 12
  },
  
  "data_quality": {
    "overall": "excellent",
    "audio_confidence": 0.92,
    "motion_confidence": 0.45,
    "phone_placement": "nightstand",
    "sensor_fusion": {
      "audio_contribution": 0.87,
      "motion_contribution": 0.13
    }
  },
  
  "breathing": {
    "rate_bpm": 8.5,
    "regularity": 0.91,
    "detected_by": "audio_primary"
  },
  
  "wave_quality": {
    "score": 0.89,
    "rating": "excellent",
    "binaural_freq": 7.83,
    "schumann_alignment": 1.0,
    "components": {
      "phase_score": 1.0,
      "frequency_score": 1.0,
      "sync_score": 0.87
    }
  },
  
  "heart_rate": 58,
  "hrv_rmssd": 42.3,
  "movement_index": 2.1
}
```

**Фильтрация для MQTT:**
```kotlin
class MqttQualityFilter {
    
    fun shouldPublish(waveQuality: WaveQuality): Boolean {
        // Публикуем только если качество достаточное
        return waveQuality.rating in listOf(
            WaveRating.EXCELLENT,
            WaveRating.GOOD,
            WaveRating.FAIR
        )
        // POOR и UNUSABLE не публикуются
    }
    
    fun createTelemetry(
        userId: String,
        sleepPhase: SleepPhaseResult,
        fusedSignal: FusedBreathSignal,
        waveQuality: WaveQuality,
        heartRate: Float?,
        hrv: Float?
    ): TelemetryMessage? {
        
        // Не публикуем, если качество плохое
        if (!shouldPublish(waveQuality)) {
            return null
        }
        
        return TelemetryMessage(
            user_id = userId,
            timestamp = System.currentTimeMillis() / 1000,
            sleep_phase = SleepPhaseData(
                current = sleepPhase.phase.name.lowercase(),
                confidence = sleepPhase.confidence,
                time_in_phase_min = /* рассчитать */
            ),
            data_quality = DataQualityData(
                overall = fusedSignal.dataQuality.name.lowercase(),
                audio_confidence = fusedSignal.audioContribution,
                motion_confidence = fusedSignal.motionContribution,
                phone_placement = fusedSignal.placement.name.lowercase()
            ),
            wave_quality = WaveQualityData(
                score = waveQuality.score,
                rating = waveQuality.rating.name.lowercase(),
                components = waveQuality
            ),
            heart_rate = heartRate,
            hrv_rmssd = hrv
        )
    }
}
```

---

### FR-5: ГЕОЛОКАЦИЯ И ID ПОЛЬЗОВАТЕЛЯ

#### FR-5.1: Геолокация
**Точность:** До города (~2 км)
**Не нужна:** GPS с точностью до метра

**Получение:**
```kotlin
// Используем LocationManager (Android)
val locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager

// Запрашиваем только грубую локацию (COARSE)
val location = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)

val lat = location?.latitude ?: 0.0
val lon = location?.longitude ?: 0.0

// Округляем до 2 знаков после запятой (~1 км точность)
val latRounded = (lat * 100).roundToInt() / 100.0
val lonRounded = (lon * 100).roundToInt() / 100.0
```

**Преобразование в Geocell (для MQTT топиков):**
```kotlin
// Делим мир на сетку 10x10 км
fun geocellFromCoords(lat: Double, lon: Double): String {
    val latCell = ((lat + 90) / 0.1).toInt() // 0.1° ≈ 11 км
    val lonCell = ((lon + 180) / 0.1).toInt()
    return "geo_${latCell}_${lonCell}"
}

// Пример: Панама (9.0°N, -79.5°W) → geo_990_1005
```

#### FR-5.2: Генерация User ID
**Формат:** UUID v4 + геолокация + timestamp
```kotlin
fun generateUserId(lat: Double, lon: Double): String {
    val uuid = UUID.randomUUID().toString().take(8) // Первые 8 символов
    val geocell = geocellFromCoords(lat, lon)
    val timestamp = System.currentTimeMillis() / 1000 // Unix timestamp
    
    return "${geocell}_${uuid}_${timestamp}"
    // Пример: geo_990_1005_a3f9c2d8_1709596800
}
```

**Хранение:**
- SharedPreferences (Android)
- Генерируется один раз при первом запуске
- Остается постоянным

---

### FR-6: MQTT СЕТЬ (P2P СИНХРОНИЗАЦИЯ)

#### FR-6.1: Почему MQTT?
 **Легковесный:** Идеален для IoT и мобильных устройств
 **Pub/Sub модель:** Broadcast без центрального сервера
 **QoS уровни:** Гарантия доставки сообщений
 **Open Source:** Mosquitto broker (бесплатный)
 **Масштабируемость:** Миллионы клиентов
 **Оффлайн режим:** Работает с локальным кэшем

#### FR-6.2: Архитектура

```
MQTT Broker (Eclipse Mosquitto)
    ↑
    ↓ (subscribe/publish)
    ↓
[BioKey App 1] ←→ [BioKey App 2] ←→ [BioKey App 3] ← ... → [BioKey App N]

Каждое приложение:
- Публикует свою телеметрию
- Подписывается на телеметрию других в своем geocell
```

**Альтернативы MQTT:**
1. **WebRTC Data Channels** - Прямой P2P, но сложнее (требует signaling сервер)
2. **IPFS (libp2p)** - Децентрализованный, но оверкил для нашей задачи
3. **Blockchain (Ethereum/IPFS)** - Избыточно + медленно
4. **Firebase Realtime Database** - Проще, но закрытая инфраструктура

**Рекомендация: MQTT** - баланс простоты и функциональности

#### FR-6.3: Топики (Topics)

**Иерархия:**
```
biokey/
├── global/                     # Глобальные метрики
│   ├── stats                   # Общая статистика сети
│   └── sync_pulse              # Синхро-импульс (каждые 10 сек)
│
├── geo/{geocell}/              # По геолокации
│   ├── telemetry               # Телеметрия пользователей в зоне
│   └── resonance               # Резонансные параметры зоны
│
└── user/{user_id}/             # Личные топики
    ├── state                   # Текущее состояние (фаза сна, и т.д.)
    └── snapshot                # Утренний снапшот сна
```

**Примеры:**
- Публикация: `biokey/geo/geo_990_1005/telemetry`
- Подписка: `biokey/geo/geo_990_1005/#` (все в моем geocell)
- Глобал: `biokey/global/stats`

#### FR-6.4: Формат сообщений (JSON)

**Телеметрия (каждые 30 сек во время сна):**
```json
{
  "user_id": "geo_990_1005_a3f9c2d8_1709596800",
  "timestamp": 1709596830,
  "sleep_stage": "deep",
  "binaural_freq": 7.83,
  "breathing_rate": 8.5,
  "heart_rate": 58,
  "hrv_rmssd": 42.3,
  "movement": 2.1,
  "coherence_score": 0.87
}
```

**Утренний снапшот (после пробуждения):**
```json
{
  "user_id": "geo_990_1005_a3f9c2d8_1709596800",
  "date": "2026-03-05",
  "total_sleep_min": 425,
  "deep_sleep_min": 78,
  "light_sleep_min": 310,
  "rem_sleep_min": 95,
  "awake_min": 22,
  "average_hr": 58,
  "average_hrv": 42.3,
  "tts_delivered": true,
  "tts_timestamp": "2026-03-05T04:23:15Z",
  "binaural_adaptation": {
    "avg_freq": 7.2,
    "sync_rate": 0.91
  }
}
```

**Глобальная статистика (обновляется каждые 10 минут):**
```json
{
  "timestamp": 1709596800,
  "active_users": 1247,
  "users_in_deep_sleep": 342,
  "global_coherence": 0.73,
  "top_geocells": [
    {"geocell": "geo_990_1005", "users": 23, "coherence": 0.89},
    {"geocell": "geo_405_742", "users": 45, "coherence": 0.85}
  ]
}
```

#### FR-6.5: Реализация MQTT клиента

**Библиотека:** Eclipse Paho MQTT Android
```gradle
dependencies {
    implementation 'org.eclipse.paho:org.eclipse.paho.client.mqttv3:1.2.5'
    implementation 'org.eclipse.paho:org.eclipse.paho.android.service:1.1.1'
}
```

**Код:**
```kotlin
class MqttManager(context: Context) {
    
    private val client: MqttAndroidClient
    private val serverUri = "tcp://broker.hivemq.com:1883" // Публичный broker для MVP
    private val clientId = generateUserId(lat, lon)
    
    init {
        client = MqttAndroidClient(context, serverUri, clientId)
        client.setCallback(object : MqttCallbackExtended {
            override fun messageArrived(topic: String, message: MqttMessage) {
                handleIncomingTelemetry(topic, message)
            }
        })
    }
    
    fun connect() {
        val options = MqttConnectOptions().apply {
            isAutomaticReconnect = true
            isCleanSession = false
            connectionTimeout = 30
            keepAliveInterval = 60
        }
        
        client.connect(options, null, object : IMqttActionListener {
            override fun onSuccess(asyncActionToken: IMqttToken?) {
                subscribeToTopics()
            }
            override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                Log.e("MQTT", "Connection failed: ${exception?.message}")
            }
        })
    }
    
    fun subscribeToTopics() {
        val myGeocell = geocellFromCoords(userLat, userLon)
        
        // Подписываемся на свою зону
        client.subscribe("biokey/geo/$myGeocell/#", 1)
        
        // Подписываемся на глобальную статистику
        client.subscribe("biokey/global/stats", 0)
    }
    
    fun publishTelemetry(telemetry: Telemetry) {
        val myGeocell = geocellFromCoords(userLat, userLon)
        val topic = "biokey/geo/$myGeocell/telemetry"
        
        val message = MqttMessage(telemetry.toJson().toByteArray()).apply {
            qos = 1 // At least once delivery
            isRetained = false
        }
        
        client.publish(topic, message)
    }
    
    private fun handleIncomingTelemetry(topic: String, message: MqttMessage) {
        val json = String(message.payload)
        val telemetry = Telemetry.fromJson(json)
        
        // Обрабатываем телеметрию других пользователей
        syncEngine.processExternalTelemetry(telemetry)
    }
}
```

---

### FR-7: АЛГОРИТМ СИНХРОНИЗАЦИИ И "УМНОЖЕНИЯ ВОЛН"

#### FR-7.1: Концепция
**Цель:** Каждое приложение старается привести своего пользователя в резонанс с глобальной волной

**Метафора:**
- Представьте оркестр, где каждый музыкант (приложение) старается сыграть в такт с дирижером (глобальная волна)
- Чем больше музыкантов в такт → тем мощнее звучание
- Один музыкант подстраивается под других → все вместе усиливают звук

**Физика:**
- Конструктивная интерференция волн
- Когерентная суперпозиция
- Резонанс Шумана как "несущая частота"

#### FR-7.2: Метрики когерентности

**Индивидуальная когерентность (локальная):**
```kotlin
fun calculateLocalCoherence(user: UserState): Float {
    val targetFreq = 7.83 // Резонанс Шумана
    val freqDeviation = abs(user.binauralFreq - targetFreq)
    val freqScore = 1.0f - (freqDeviation / 10.0f).coerceIn(0f, 1f)
    
    val stageScore = when (user.sleepStage) {
        SleepStage.DEEP -> 1.0f
        SleepStage.LIGHT -> 0.7f
        SleepStage.REM -> 0.5f
        SleepStage.AWAKE -> 0.0f
    }
    
    val breathingScore = if (user.breathingRate in 6.0..10.0) 1.0f else 0.5f
    
    return (freqScore * 0.5f + stageScore * 0.3f + breathingScore * 0.2f)
}
```

**Групповая когерентность (глобальная):**
```kotlin
fun calculateGlobalCoherence(users: List<UserState>): Float {
    val avgFreq = users.map { it.binauralFreq }.average()
    val freqVariance = users.map { (it.binauralFreq - avgFreq).pow(2) }.average()
    val freqDeviation = sqrt(freqVariance)
    
    // Чем меньше разброс → тем выше когерентность
    val coherence = 1.0f / (1.0f + freqDeviation)
    
    return coherence
}
```

#### FR-7.3: Алгоритм адаптации

**Каждое приложение:**
1. Получает телеметрию других пользователей в своем geocell
2. Рассчитывает "центр масс" глобальной волны:
   - Средняя бинауральная частота
   - Средняя фаза сна
   - Средняя когерентность
3. Плавно подстраивает своего пользователя к этому центру
4. НО учитывает индивидуальные потребности (не жертвует качеством сна)

**Код:**
```kotlin
class SyncEngine {
    
    private val externalTelemetry = mutableListOf<Telemetry>()
    
    fun processExternalTelemetry(telemetry: Telemetry) {
        externalTelemetry.add(telemetry)
        
        // Храним только последние 100 записей (10 мин при 30 сек интервале)
        if (externalTelemetry.size > 100) {
            externalTelemetry.removeAt(0)
        }
    }
    
    fun calculateGlobalTarget(): GlobalTarget {
        if (externalTelemetry.isEmpty()) {
            return GlobalTarget(freq = 7.83f, coherence = 0f)
        }
        
        val avgFreq = externalTelemetry.map { it.binaural_freq }.average().toFloat()
        val coherence = calculateGlobalCoherence(externalTelemetry.map { it.toUserState() })
        
        return GlobalTarget(freq = avgFreq, coherence = coherence)
    }
    
    fun adaptUserToBinaural(
        currentFreq: Float,
        userState: UserState,
        globalTarget: GlobalTarget
    ): Float {
        // Целевая частота = взвешенное среднее между индивидуальной и глобальной
        val individualTarget = getIndividualTarget(userState)
        val globalWeight = globalTarget.coherence // Чем выше когерентность → тем больше вес
        
        val targetFreq = individualTarget * (1 - globalWeight) + 
                         globalTarget.freq * globalWeight
        
        // Плавный переход (exponential moving average)
        val alpha = 0.05f // Медленная адаптация
        return alpha * targetFreq + (1 - alpha) * currentFreq
    }
    
    private fun getIndividualTarget(userState: UserState): Float {
        return when (userState.sleepStage) {
            SleepStage.AWAKE -> 12.0f // Alpha
            SleepStage.LIGHT -> 7.0f // Theta
            SleepStage.DEEP -> 3.0f // Delta
            SleepStage.REM -> 9.0f // Alpha/Theta border
        }
    }
}

data class GlobalTarget(
    val freq: Float,
    val coherence: Float
)
```

#### FR-7.4: "Умножение" эффекта

**Гипотеза:** Эффект масштабируется нелинейно с количеством участников

**Математическая модель (для тестирования):**
```kotlin
// Три модели для сравнения
fun effectMagnitude(n: Int, coherence: Float): Float {
    return when (preferredModel) {
        Model.LINEAR -> n * coherence
        Model.POWER -> n.pow(coherence + 1.0f)
        Model.EXPONENTIAL -> exp(coherence * ln(n.toFloat()))
    }
}
```

**Логирование для анализа:**
- Каждое утро сохраняем:
  - Количество синхронизированных пользователей (n)
  - Среднюю когерентность (coherence)
  - Индивидуальные метрики (HRV, качество сна)
- После 3-6 месяцев → статистический анализ
- Определяем лучшую модель

---

### FR-8: ЭКСПОРТ ДАННЫХ (УТРЕННИЙ СЛЕПОК)

#### FR-8.1: Формат
**Файл:** `biokey_sleep_YYYY-MM-DD.json`

**Содержание:**
```json
{
  "user_id": "geo_990_1005_a3f9c2d8_1709596800",
  "date": "2026-03-05",
  "app_version": "0.4.0_SYNC",
  
  "sleep_summary": {
    "bed_time": "2026-03-04T23:15:00Z",
    "wake_time": "2026-03-05T07:23:00Z",
    "total_sleep_min": 425,
    "sleep_efficiency": 0.91,
    "stages": {
      "awake_min": 22,
      "light_min": 310,
      "deep_min": 78,
      "rem_min": 95
    }
  },
  
  "biometrics": {
    "avg_heart_rate": 58,
    "avg_hrv_rmssd": 42.3,
    "avg_breathing_rate": 8.5,
    "movement_index": 2.1
  },
  
  "intervention": {
    "binaural_enabled": true,
    "tts_delivered": true,
    "tts_timestamp": "2026-03-05T04:23:15Z",
    "tts_language": "en",
    "tts_sleep_stage": "deep"
  },
  
  "synchronization": {
    "geocell": "geo_990_1005",
    "active_users_in_cell": 23,
    "global_coherence_avg": 0.73,
    "personal_coherence_avg": 0.87,
    "sync_events": 124
  },
  
  "raw_timeline": [
    {
      "timestamp": "2026-03-04T23:15:00Z",
      "sleep_stage": "awake",
      "hr": 72,
      "movement": 15.3
    },
    {
      "timestamp": "2026-03-04T23:45:00Z",
      "sleep_stage": "light",
      "hr": 65,
      "movement": 3.2
    }
    // ... каждые 30 сек
  ]
}
```

#### FR-8.2: Хранение
**Локально:**
- `/sdcard/Android/data/com.biokey.app/files/sleep_logs/`
- Хранится 30 дней
- Потом автоматически удаляется (или по желанию пользователя)

**MQTT:**
- Утром публикуется в топик `biokey/user/{user_id}/snapshot`
- Другие приложения НЕ сохраняют эти данные (только свои)
- Но могут использовать для расчета глобальной статистики

**Облако (опционально, для citizen science):**
- Если пользователь согласился на участие в исследовании
- Загрузка на OSF через HTTPS API
- Полностью анонимно (user_id не содержит PII)

---

### FR-9: UI (TERMINAL-STYLE МИНИМАЛИЗМ)

#### Философия дизайна:
- **Одним листом** - вся информация на одном экране
- **Прокрутка вверх/вниз** - как в терминале
- **Минимум кнопок** - только критичные действия
- **Текстовый интерфейс** - никаких излишних графиков
- **Быстрый доступ** - все настройки на одном экране

#### FR-9.1: Главный экран (перед сном)

```
┌─────────────────────────────────────────┐
│ BioKey v0.4.0_SYNC                      │
│ ════════════════════════════════════════│
│                                         │
│ SENSORS STATUS:                         │
│  Microphone     [●] READY  conf: 95%    │
│  Galaxy Watch 4 [●] CONNECTED           │
│    HR: 72 bpm  HRV: 45ms  SpO2: 98%     │
│  Accelerometer  [●] READY  conf: 40%    │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ ALARM CONFIGURATION:                    │
│ Type: [●] Smart  [ ] Hard               │
│ Time: 07:00                             │
│ Window: ±30 min (06:30 - 07:30)         │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ NETWORK:                                │
│ MQTT: [●] Connected to HiveMQ           │
│ Geocell: geo_990_1005                   │
│ Active users nearby: 23                 │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ NIGHT TARGET:                           │
│ TTS Window: 04:15 - 04:45               │
│ Language: English                       │
│ Phrase: "I am for health and longevity" │
│                                         │
│ ════════════════════════════════════════│
│                                         │
│        [START SLEEP SESSION]            │
│                                         │
│        [Settings]  [Terminal]  [Help]   │
└─────────────────────────────────────────┘
```

**Взаимодействие:**
- Tap на "Type" → переключение Smart/Hard
- Tap на "Time" → time picker
- Tap на "Window" → выбор ±15/±30/±45 мин
- Tap на "Language" → список языков
- Scroll вверх/вниз → вся информация видна

---

#### FR-9.2: Экран во время сна (упрощенный)

```
┌─────────────────────────────────────────┐
│ SLEEP SESSION ACTIVE                    │
│ ════════════════════════════════════════│
│                                         │
│ Time: 02:34:12                          │
│ Phase: DEEP SLEEP (conf: 95%)           │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ BIOMETRICS:                             │
│ Breathing:  8.5 BPM  (regularity: 91%)  │
│ Heart:     58 BPM    (HRV: 42.3 ms)     │
│ SpO2:      97%                          │
│ Movement:  Low (2.1)                    │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ AUDIO:                                  │
│ Binaural: 7.83 Hz (Schumann Resonance)  │
│ Scene: Ocean Waves (soft loop)          │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ SYNC STATUS:                            │
│ Quality: EXCELLENT (89%)                │
│ Global coherence: 73%                   │
│ Users synced: 23                        │
│ MQTT: [●] Publishing every 30s          │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ NIGHT PROGRESS:                         │
│ TTS: [PENDING] in 1h 41m                │
│ Wake: [PENDING] in 4h 26m               │
│                                         │
│ ════════════════════════════════════════│
│                                         │
│           [STOP SESSION]                │
│           (tap + hold 3 sec)            │
│                                         │
└─────────────────────────────────────────┘
```

**Особенности:**
- Screen dimmed (низкая яркость)
- Updates каждые 30 сек
- Tap на экран → показать на 10 сек, затем dim
- Hold 3 sec → остановка сессии

---

#### FR-9.3: Утренний отчет (terminal-style)

```
┌─────────────────────────────────────────┐
│ GOOD MORNING!                           │
│ ════════════════════════════════════════│
│                                         │
│ SESSION SUMMARY:                        │
│ Date: 2026-03-05                        │
│ Duration: 7h 12m (432 min)              │
│ Efficiency: 91%                         │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ SLEEP STAGES:                           │
│ Awake:  22 min  ( 5%) ░░░░░░░░░░        │
│ Light: 310 min  (72%) ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
│ Deep:   78 min  (18%) ▓▓▓▓▓▓▓▓░░░░░░░   │
│ REM:    95 min  (22%) ▓▓▓▓▓▓▓▓▓░░░░░░   │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ BIOMETRICS:                             │
│ Avg HR:    58 bpm (range: 52-68)        │
│ Avg HRV:   42.3 ms (RMSSD)              │
│ Avg SpO2:  97% (min: 94%, max: 99%)     │
│ Breathing: 8.5 BPM (very regular)       │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ INTERVENTION:                           │
│ ✓ TTS delivered at 04:23 AM             │
│   Stage: DEEP (confidence: 97%)         │
│   Binaural: 7.83 Hz (perfect sync)      │
│                                         │
│ ✓ Smart wake triggered at 07:12 AM      │
│   Reason: Light sleep detected          │
│   Window match: YES (within ±30 min)    │
│                                         │
│ ────────────────────────────────────────│
│                                         │
│ SYNCHRONIZATION:                        │
│ Data quality: EXCELLENT (avg 87%)       │
│ Wave quality: EXCELLENT (89%)           │
│                                         │
│ Global stats:                           │
│ - Users in area: 23                     │
│ - Global coherence: 73%                 │
│ - Your contribution: High               │
│ - MQTT packets sent: 864                │
│                                         │
│ ════════════════════════════════════════│
│                                         │
│ [View Timeline] [Export JSON] [Share]   │
│                                         │
│ [Start New Session]                     │
└─────────────────────────────────────────┘
```

---

#### FR-9.4: Terminal (for power users)

**Доступ:** Long-press на "BioKey v0.4.0" в главном экране

```
┌─────────────────────────────────────────┐
│ BioKey Terminal v0.4.0_SYNC             │
│ ════════════════════════════════════════│
│                                         │
│ > _                                     │
│                                         │
│ Available commands:                     │
│   stats    - Global network stats       │
│   geocell  - Your geocell info          │
│   wave     - Wave parameters            │
│   users    - Nearby users               │
│   sensors  - Sensor diagnostics         │
│   mqtt     - MQTT connection status     │
│   export   - Export last session        │
│   config   - Show configuration         │
│   help     - List all commands          │
│   clear    - Clear terminal             │
│                                         │
│ Type 'help' for detailed info           │
└─────────────────────────────────────────┘
```

**Примеры команд:**

```
> stats

GLOBAL NETWORK STATISTICS
─────────────────────────────────────
Active users:       1,247
Users in deep:        342
Global coherence:    73%
Avg wave quality:    0.68

Top geocells:
  geo_990_1005: 23 users, coherence 89%
  geo_405_742:  45 users, coherence 85%
  geo_520_830:  31 users, coherence 78%

Last updated: 2 minutes ago
─────────────────────────────────────
```

```
> sensors

SENSOR DIAGNOSTICS
─────────────────────────────────────
   MICROPHONE:
   Status: ACTIVE (duty cycle 50%)
   Confidence: 92%
   SNR: 18 dB
   Breathing detected: YES (8.5 BPM)
   Noise floor: -42 dB

   SMARTWATCH (Galaxy Watch 4):
   Status: CONNECTED (BLE)
   Battery: 78%
   HR: 58 bpm (confidence: 95%)
   HRV: 42.3 ms (RMSSD)
   SpO2: 97%
   Last update: 2 sec ago

   ACCELEROMETER:
   Status: ACTIVE
   Confidence: 45%
   Movement detected: LOW (2.1)
   Placement: NIGHTSTAND (estimated)

   FUSION RESULT:
   Overall confidence: 89%
   Data quality: EXCELLENT
   Primary source: MICROPHONE
─────────────────────────────────────
```

```
> wave

WAVE PARAMETERS
─────────────────────────────────────
Your Wave:
  Frequency: 7.83 Hz (Schumann)
  Phase: 142°
  Amplitude: 0.89
  Quality: EXCELLENT (89%)

Components:
  Phase score:     1.00 (deep sleep)
  Frequency score: 1.00 (perfect match)
  Sync score:      0.87 (breathing sync)

Binaural adaptation:
  Target: 7.83 Hz
  Current: 7.81 Hz
  Drift: -0.02 Hz (negligible)
  Adaptation rate: 5%/min

Breath coupling:
  Your breathing: 8.5 BPM
  Binaural influence: 92%
  Coherence: HIGH
─────────────────────────────────────
```

---

#### FR-9.5: Settings (одним списком)

```
┌─────────────────────────────────────────┐
│ SETTINGS                                │
│ ════════════════════════════════════════│
│                                         │
│ ALARM                                   │
│ ├─ Type: [Smart ▼]                      │
│ ├─ Time: [07:00]                        │
│ ├─ Window: [±30 min ▼]                  │
│ └─ Sound: [Thunder Rain ▼]              │
│                                         │
│ AUDIO                                   │
│ ├─ Binaural: [Enabled ✓]                │
│ ├─ Scene: [Ocean Waves ▼]               │
│ ├─ Volume: [80% ▓▓▓▓▓▓▓▓░░]             │
│ └─ TTS Volume: [30% ▓▓▓░░░░░░░]         │
│                                         │
│ NIGHT TARGET                            │
│ ├─ TTS Window: [04:15 - 04:45]          │
│ ├─ Language: [English ▼]                │
│ └─ Custom phrase: [Edit...]             │
│                                         │
│ SENSORS                                 │
│ ├─ Microphone: [Enabled ✓]              │
│ ├─ Mic duty cycle: [50% ▼]              │
│ ├─ Smartwatch: [Auto-detect ✓]          │
│ └─ Accelerometer: [Enabled ✓]           │
│                                         │
│ NETWORK                                 │
│ ├─ MQTT: [Enabled ✓]                    │
│ ├─ Broker: [HiveMQ Cloud]               │
│ ├─ Quality threshold: [GOOD+ ▼]         │
│ └─ Telemetry rate: [30 sec ▼]           │
│                                         │
│ DATA                                    │
│ ├─ Local storage: [30 days ▼]           │
│ ├─ Auto-export: [Disabled ▼]            │
│ └─ Upload to OSF: [Disabled ▼]          │
│                                         │
│ ADVANCED                                │
│ ├─ Terminal access: [Enabled ✓]         │
│ ├─ Debug logging: [Disabled]            │
│ └─ Battery optimization: [Enabled ✓]    │
│                                         │
│ ════════════════════════════════════════│
│                                         │
│ [Reset to defaults] [Export config]     │
└─────────────────────────────────────────┘
```

**Все настройки на одном экране**, scroll для доступа к нижним.

#### FR-9.1: Главный экран (во время сна)
```
┌─────────────────────────────────────┐
│  BioKey Sleep Session               │
│  ●●●●●●●●●●○○○○○○○○○○  3h 42m       │
├─────────────────────────────────────┤
│                                     │
│      ╱╲  ╱╲  ╱╲                     │
│     ╱  ╲╱  ╲╱  ╲   DEEP SLEEP       │
│                                     │
│  Binaural: 7.83 Hz (Schumann)       │
│  Breathing: 8.5 BPM                 │
│  Heart Rate: 58 BPM                 │
│                                     │
├─────────────────────────────────────┤
│   23 users synced in your area      │
│  Coherence: ▓▓▓▓▓▓▓▓░░ 87%          │
└─────────────────────────────────────┘
     [Stop Session]  [Settings]
```

#### FR-9.2: Утренний отчет
```
┌─────────────────────────────────────┐
│  Good Morning!                      │
│  You slept 7h 5m (91% efficiency)   │
├─────────────────────────────────────┤
│  Sleep Stages:                      │
│  ▓▓▓▓░░░░ Deep:  1h 18m (18%)       │
│  ▓▓▓▓▓▓▓░ Light: 5h 10m (73%)       │
│  ▓▓░░░░░░ REM:   1h 35m (22%)       │
│                                     │
│  Biometrics:                        │
│   Avg HR:  58 BPM                   │
│   Avg HRV: 42.3 ms                  │
│                                     │
│  Synchronization:                   │
│   23 users in your area             │
│   Coherence: 87% (Excellent!)       │
│                                     │
│   TTS delivered at 04:23 AM         │
│   Binaural adaptation: 91%          │
└─────────────────────────────────────┘
   [View Details]  [Export Data]
```

---

## НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ

### NFR-1: Производительность
- **Время отклика:** < 100 мс для любых UI операций
- **Потребление батареи:** < 10% за ночь (8 часов)
- **Использование RAM:** < 100 MB в фоне
- **MQTT latency:** < 1 сек для доставки сообщений

### NFR-2: Надежность
- **Uptime:** 99.9% (допустимо падение 1 раз в 1000 ночей)
- **Будильник ДОЛЖЕН сработать:** даже если app crashed
- **Оффлайн режим:** Работает без интернета (только MQTT не работает)
- **Восстановление:** После перезагрузки телефона session продолжается

### NFR-3: Безопасность
- **Данные:** Хранятся локально, шифрование AES-256
- **MQTT:** Никаких личных данных, только анонимные метрики
- **Permissions:** Минимум (Location coarse, Audio record, Vibrate, Alarm)

### NFR-4: Масштабируемость
- **MQTT broker:** Должен выдерживать 10,000+ одновременных клиентов
- **Geocells:** Автоматическое разделение на зоны (load balancing)
- **Рост:** От 10 пользователей → 100,000+ без изменений архитектуры

### NFR-5: Открытость
- **Код:** GPL-3.0, весь код на GitHub
- **Протокол:** MQTT (открытый стандарт)
- **Данные:** JSON (читаемый формат)
- **Документация:** Полная, на английском + русском

---

## АРХИТЕКТУРА ПРИЛОЖЕНИЯ

### Существующая структура (из v0.3.9.3_ME)

```
app/src/main/java/com/insightcine/biokey/
├── core/
│   └── WaveCore.kt                    # Существующий Wave Engine
│
├── engine/                             #  Архитектура v0.3.9.3
│   ├── alarm/
│   │   ├── AlarmEngine.kt             # Умный будильник (частично)
│   │   ├── AlarmConfig.kt
│   │   ├── AlarmWindow.kt
│   │   └── WakeDecision.kt
│   ├── guard/
│   │   └── OneShotGuard.kt            # Защита от повторов (TTS, alarm)
│   └── night/
│       ├── NightTargetModel.kt        # Целевая точка 04:30
│       ├── NightPhaseState.kt
│       └── NightTargetConfig.kt
│
├── sleep/                              # Существующая логика сна
│   ├── SleepSessionManager.kt         #  Менеджер сессий
│   ├── SleepPhaseDetector.kt          #  Детектор фаз
│   ├── SleepPhaseClassifier.kt        #  Доработать (добавить DataQuality)
│   ├── BreathAnalyzer.kt              #  Доработать (fusion с motion)
│   ├── BreathSignal.kt
│   ├── SleepSignal.kt
│   ├── SmartWakeEngine.kt             #  Умный будильник
│   ├── WakeUpStrategy.kt
│   ├── SleepCycleController.kt
│   ├── SleepViewModel.kt
│   ├── SleepAnalyzer.kt
│   ├── SleepRecorder.kt               #  Запись сессий
│   ├── SleepTimeline.kt
│   ├── SleepReportBuilder.kt          #  Отчеты
│   └── processing/
│       └── SleepSignalProcessor.kt    #  Обработка сигналов
│
├── sensors/                            # Существующие сенсоры
│   ├── MotionSensor.kt                #  Акселерометр
│   ├── NoiseSensor.kt                 #  Микрофон
│   ├── SensorAggregator.kt            #  Доработать (fusion)
│   └── SensorFrame.kt
│
├── audio/                              # Существующая аудио-система
│   ├── AudioEngine.kt                 #  Главный движок
│   ├── BioAudioEngine.kt              #  Биомодуляция
│   ├── BrainWaveLibrary.kt            #  Библиотека частот
│   ├── AudioPlaylist.kt
│   ├── AudioLoop.kt
│   ├── AudioFade.kt
│   ├── AudioController.kt
│   ├── AudioFFTAnalyzer.kt            #  FFT анализ (для дыхания!)
│   ├── scene/
│   │   ├── SceneLibrary.kt            #  Сцены (фоновые звуки)
│   │   └── AudioScene.kt
│   └── wave/
│       ├── WaveCoordinator.kt         #  Координация волны
│       └── WaveBreathCoupler.kt       #  Связка дыхание-волна
│
├── brainwave/                          # Бинауральные ритмы
│   ├── BrainWaveProfile.kt            #  Профили частот
│   ├── BrainWaveLibrary.kt
│   └── BrainWavePlaylistBuilder.kt
│
├── network/                            # P2P сеть (заглушка)
│   ├── IPeerNetwork.kt                #  Интерфейс (реализовать MQTT)
│   └── LocalMeshStub.kt               #  Заглушка
│
├── sync/                               # Синхронизация (частично)
│   ├── BioSyncManager.kt              #  Доработать
│   └── MeshNode.kt
│
├── service/
│   ├── SleepForegroundService.kt      #  Foreground Service
│   └── SleepNotificationActions.kt
│
└── ui/                                 # Существующий UI
    ├── screen/
    │   ├── SleepRootScreen.kt
    │   ├── SleepIdleScreen.kt
    │   ├── ActiveSleepScreen.kt
    │   ├── SleepWakingUpScreen.kt
    │   └── SleepFinishedScreen.kt
    └── state/
        └── SleepUiState.kt
```

---

### Новые модули для v0.4.0_SYNC

```
app/src/main/java/com/insightcine/biokey/
├── sensors/
│   ├── fusion/                         #  Fusion сенсоров
│   │   ├── SensorFusion.kt
│   │   ├── AudioBreathDetector.kt
│   │   ├── MotionBreathDetector.kt
│   │   └── FusedBreathSignal.kt
│   └── quality/                        #  Качество данных
│       ├── DataQualityMonitor.kt
│       └── PhonePlacementDetector.kt
│
├── wave/                               #  Расчет качества волны
│   ├── WaveQualityCalculator.kt
│   └── WaveQuality.kt
│
├── network/
│   ├── mqtt/                           #  MQTT реализация
│   │   ├── MqttManager.kt
│   │   ├── MqttConfig.kt
│   │   ├── TelemetryPublisher.kt
│   │   └── TelemetrySubscriber.kt
│   └── sync/                           #  Синхронизация
│       ├── SyncEngine.kt
│       ├── GlobalTarget.kt
│       └── CoherenceCalculator.kt
│
├── audio/
│   ├── binaural/                       #  Генерация бинауралки
│   │   ├── BinauralGenerator.kt
│   │   └── FrequencyAdapter.kt
│   └── tts/                            #  TTS установка
│       ├── TtsPlayer.kt
│       └── AffirmationLibrary.kt
│
├── alarm/                              #  Доработка будильников
│   ├── HardAlarm.kt
│   └── SmartAlarm.kt
│
├── export/                             #  Экспорт данных
│   ├── SnapshotExporter.kt
│   ├── JsonSerializer.kt
│   └── SnapshotUploader.kt
│
└── util/
    ├── Geolocation.kt                  #  Геолокация
    ├── UserId.kt                       #  Генерация ID
    └── Geocell.kt                      #  Geocells для MQTT
```

---

### Жизненный цикл session (детальный)
```
[19:00] Пользователь открывает приложение
     ↓
[19:05] Выбирает тип будильника:
        - Hard: 07:00 точно
        - Smart: 07:00 ±30 мин
     ↓
[23:00] Кладет телефон (тумбочка/кровать/грудь)
     ↓
[23:00] Нажимает "Start Sleep Session"
     ↓ [SleepForegroundService запускается]
     ↓
[23:00-23:15] ЗАСЫПАНИЕ
     │ • AudioEngine начинает играть ocean_performance_soft_looped.wav
     │ • BinauralGenerator: 10 Hz (Alpha → Theta)
     │ • NoiseSensor + MotionSensor → SensorFusion
     │ • SleepPhaseClassifier: AWAKE → LIGHT
     ↓
[23:15-01:00] ЛЕГКИЙ СОН (Light Sleep)
     │ • Binaural: 7 Hz (Theta)
     │ • WaveBreathCoupler подстраивает частоту под дыхание
     │ • Каждые 30 сек: публикация телеметрии в MQTT
     │   (если DataQuality >= FAIR)
     │ • SyncEngine получает телеметрию других → адаптирует частоту
     ↓
[01:00-03:30] ГЛУБОКИЙ СОН (Deep Sleep, циклы)
     │ • Binaural: 3-4 Hz (Delta)
     │ • DataQuality обычно EXCELLENT (стабильное дыхание)
     │ • WaveQuality score > 0.8
     │ • MQTT: активная публикация
     ↓
[04:00-04:15] ПОДГОТОВКА К TTS
     │ • NightTargetModel: phaseOffsetNorm близок к 0
     │ • Binaural плавно переходит на 7.83 Hz (Schumann)
     │ • Проверяем условия:
     │   - SleepPhase == DEEP? ✓
     │   - Binaural == 7.83 Hz? ✓
     │   - Breathing < 10 BPM? ✓
     │   - DataQuality >= GOOD? ✓
     ↓
[04:23] TTS УСТАНОВКА (окно 04:15-04:45)
     │ • OneShotGuard предотвращает повтор
     │ • TtsPlayer.speak("I am for health and longevity")
     │ • Volume: 30%
     │ • 3 повтора с паузой 15 сек
     │ • Логируем: tts_delivered = true, timestamp
     ↓
[04:30-06:30] ПРОДОЛЖЕНИЕ СНА
     │ • Binaural возвращается к адаптивному режиму
     │ • REM циклы
     │ • Light sleep
     ↓
[06:30] SMART WAKE WINDOW НАЧИНАЕТСЯ
     │ • AlarmWindow: [06:30 - 07:30]
     │ • SmartWakeEngine активируется
     │ • Каждые 30 сек проверяет:
     │   - SleepPhase == LIGHT или REM?
     │   - Movement > threshold?
     │   - HR повышен?
     ↓
[07:12] НАЙДЕНО ОКНО ПРОСЫПАНИЯ
     │ • SleepPhase: LIGHT
     │ • Movement: 8.5 (небольшое ворочание)
     │ • SmartWakeEngine → WakeDecision(shouldWake=true)
     ↓
[07:12] БУДИЛЬНИК СРАБАТЫВАЕТ
     │ • AudioEngine fade out бинауралку (10 сек)
     │ • AlarmPlayer fade in thunder_rain_looped.wav (30 сек)
     │ • Вибрация
     │ • Notification: [Snooze] [Dismiss]
     ↓
[07:15] ПОЛЬЗОВАТЕЛЬ ПРОСЫПАЕТСЯ
     │ • Нажимает "Dismiss"
     │ • SleepRecorder завершает сессию
     │ • SleepReportBuilder генерирует отчет
     ↓
[07:15] ЭКСПОРТ СЛЕПКА
     │ • SnapshotExporter создает JSON
     │ • Сохраняет локально: sleep_2026-03-05.json
     │ • Публикует в MQTT: biokey/user/{id}/snapshot
     │ • (Опционально) Загружает на OSF
     ↓
[07:16] УТРЕННИЙ ОТЧЕТ
     │ • UI: SleepFinishedScreen
     │ • Показывает:
     │   - Sleep stages (graph)
     │   - HRV, breathing
     │   - Sync stats (23 users, coherence 87%)
     │   - Wave quality: EXCELLENT
     ↓
[07:20] SESSION ЗАВЕРШЕНА
     │ • SleepForegroundService останавливается
     │ • Пользователь может:
     │   - Посмотреть детали
     │   - Экспортировать в CSV
     │   - Поделиться в соцсетях
```

---

## ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Android
- **Язык:** Kotlin
- **Min SDK:** 26 (Android 8.0 Oreo) - для Foreground Services
- **Target SDK:** 34 (Android 14)
- **Architecture:** MVVM + Clean Architecture
- **DI:** Koin (легковесная альтернатива Dagger)

### Библиотеки
```gradle
dependencies {
    // Existing (v0.3.9.3)
    implementation "androidx.core:core-ktx:1.12.0"
    implementation "androidx.compose.ui:ui:1.5.4"
    
    // Sensors
    implementation "androidx.core:core-sensing:1.0.0-alpha01"
    
    // Audio
    implementation "androidx.media3:media3-exoplayer:1.2.0"
    
    // MQTT
    implementation "org.eclipse.paho:org.eclipse.paho.client.mqttv3:1.2.5"
    implementation "org.eclipse.paho:org.eclipse.paho.android.service:1.1.1"
    
    // JSON
    implementation "org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0"
    
    // Bluetooth LE (для фитнес-трекеров)
    implementation "no.nordicsemi.android:ble:2.6.1"
    
    // Smartwatch Integration
    // Wear OS / Health Services
    implementation "androidx.health:health-services-client:1.0.0-beta03"
    implementation "androidx.health.connect:connect-client:1.1.0-alpha07"
    
    // Bluetooth GATT (generic HR devices)
    // (Built-in Android, no extra libs)
    
    // Fitbit API (если нужно cloud)
    implementation "com.squareup.retrofit2:retrofit:2.9.0"
    implementation "com.squareup.retrofit2:converter-gson:2.9.0"
    
    // Math/DSP (для бинауралки)
    implementation "org.apache.commons:commons-math3:3.6.1"
    
    // Testing
    testImplementation "junit:junit:4.13.2"
    testImplementation "org.mockito.kotlin:mockito-kotlin:5.1.0"
    androidTestImplementation "androidx.test.ext:junit:1.1.5"
}
```

### Smartwatch SDK / API матрица

| Device | Protocol | Library | Notes |
|--------|----------|---------|-------|
| **Wear OS** (Samsung, Pixel) | Health Services | `androidx.health:health-services-client` | Realtime HR, steps |
| **Fitbit** | Cloud API | Retrofit + OAuth | Polling (1 min resolution) |
| **Garmin** | Cloud API | Retrofit + OAuth | Polling |
| **Polar H10** | Bluetooth LE | `no.nordicsemi.android:ble` | Realtime HR, HRV |
| **Oura Ring** | Cloud API | Retrofit + OAuth | Sleep data next day |
| **Whoop** | Cloud API | Retrofit + OAuth | Recovery data |
| **Generic HR** | Bluetooth GATT | Built-in Android | Standard HR service |

**Приоритет для MVP:**
1.  Wear OS (Health Services) - прямое подключение
2.  Generic Bluetooth HR - работает со многими страпами
3.  Cloud APIs - требуют OAuth, но polling задержка

### Backend (MQTT Broker)
**Опция для MVP:** HiveMQ Cloud
- **Free tier:** 100 concurrent connections
- **URL:** `ssl://broker.hivemq.com:8883`
- **TLS:** Enabled
- **QoS:** Level 1 (at least once)

**Credentials:** Anonymous (для MVP)

**Альтернатива (если нужно больше):**
- Eclipse IoT (mqtt://mqtt.eclipseprojects.io:1883) - unlimited, но менее надежен

---

---

## ПЛАН РАЗРАБОТКИ

### Что уже есть vs что нужно добавить

| Модуль | Статус | Действие | Приоритет |
|--------|--------|----------|-----------|
| **Core & Engine** |
| WaveCore.kt | Есть | Использовать как есть | - |
| NightTargetModel.kt | Есть | Использовать (целевая точка 04:30) | - |
| OneShotGuard.kt | Есть | Использовать (защита TTS) | - |
| **Sleep Detection** |
| SleepPhaseDetector.kt | Есть | Доработать (добавить DataQuality) | HIGH |
| SleepPhaseClassifier.kt | Есть | Доработать (EnhancedClassifier) | HIGH |
| BreathAnalyzer.kt | Есть | Доработать (для fusion) | HIGH |
| **Sensors** |
| MotionSensor.kt | Есть | Использовать как есть | - |
| NoiseSensor.kt | Есть | Использовать как есть | - |
| SensorAggregator.kt | Есть | Доработать (fusion logic) | HIGH |
| SensorFusion.kt | Нет | **Создать** (микрофон + акселерометр) | HIGH |
| **Audio** |
| AudioEngine.kt | Есть | Использовать | - |
| BioAudioEngine.kt | Есть | Использовать | - |
| BrainWaveLibrary.kt | Есть | Использовать | - |
| WaveBreathCoupler.kt | Есть | Использовать (адаптация к дыханию) | - |
| AudioFFTAnalyzer.kt | Есть | Использовать (для микрофона) | - |
| BinauralGenerator.kt | Нет | **Создать** (если нет в BrainWave*) | MED |
| TtsPlayer.kt | Нет | **Создать** (TTS установка) | HIGH |
| **Alarm** |
| SmartWakeEngine.kt | Есть | Доработать (проверить логику) | MED |
| AlarmEngine.kt | Есть | Доработать (hard alarm) | MED |
| **Network** |
| IPeerNetwork.kt | Интерфейс | Реализовать MQTT | HIGH |
| LocalMeshStub.kt | Заглушка | Заменить на MQTT | HIGH |
| MqttManager.kt | Нет | **Создать** | HIGH |
| TelemetryPublisher.kt | Нет | **Создать** | HIGH |
| **Sync** |
| BioSyncManager.kt | Есть | Доработать (MQTT sync) | HIGH |
| SyncEngine.kt | Нет | **Создать** (адаптация к глобальной волне) | HIGH |
| CoherenceCalculator.kt | Нет | **Создать** | MED |
| **Wave Quality** |
| WaveQualityCalculator.kt | Нет | **Создать** | HIGH |
| DataQualityMonitor.kt | Нет | **Создать** | MED |
| **Export** |
| SleepRecorder.kt | Есть | Проверить формат | LOW |
| SnapshotExporter.kt | Нет | **Создать** (JSON export) | MED |
| **Geo** |
| Geolocation.kt | Нет | **Создать** | MED |
| UserId.kt | Нет | **Создать** | MED |
| Geocell.kt | Нет | **Создать** | MED |
| **Service** |
| SleepForegroundService.kt | Есть | Использовать | - |
| **UI** |
| SleepIdleScreen.kt  Есть | Использовать | - |
| ActiveSleepScreen.kt | Есть | Доработать (показывать quality) | LOW |
| SleepFinishedScreen.kt | Есть | Доработать (sync stats) | LOW |

**Легенда:**
- Есть - работает, использовать как есть
- Есть - требует доработки
- Нет - создать с нуля
- HIGH - критично для MVP
- MED - важно, но не блокирует
- LOW - можно отложить

---

### Фаза 1: Core Features + Sensor Fusion (2-3 недели)

**Цель:** Надежная детекция сна с расчетом качества

**Задачи:**
1. **SensorFusion.kt** - объединение микрофон + акселерометр
   - AudioBreathDetector (использовать AudioFFTAnalyzer)
   - MotionBreathDetector
   - Fusion logic с весами
   - DataQuality calculation

2. **Доработка SleepPhaseClassifier**
   - Добавить поддержку DataQuality
   - Улучшить эвристику с учетом микрофона
   - Интеграция с SensorFusion

3. **Доработка BreathAnalyzer**
   - Адаптация для fusion
   - Расчет regularity

4. **WaveQualityCalculator.kt**
   - Score calculation
   - Rating system
   - Integration с BrainWaveLibrary

5. **TtsPlayer.kt**
   - Android TTS API
   - Multi-language support
   - Volume control
   - OneShotGuard integration

6. **Доработка AlarmEngine**
   - Проверить hard alarm
   - Интеграция со SmartWakeEngine

**Результат:** Работающее приложение для 1 пользователя с надежной детекцией и TTS

---

### Фаза 2: Network Sync (2-3 недели)

**Цель:** P2P сеть через MQTT

**Задачи:**
1. **MqttManager.kt** - Eclipse Paho
   - Connection handling
   - Auto-reconnect
   - Topic subscriptions

2. **TelemetryPublisher.kt**
   - JSON serialization
   - Quality filtering (only FAIR+)
   - Geocell-based topics

3. **TelemetrySubscriber.kt**
   - Parse incoming telemetry
   - Store in buffer

4. **SyncEngine.kt**
   - Global target calculation
   - Binaural frequency adaptation
   - Coherence tracking

5. **Доработка BioSyncManager**
   - Integration с MqttManager
   - Integration с SyncEngine

6. **Геолокация**
   - Geolocation.kt
   - UserId.kt
   - Geocell.kt

**Результат:** P2P сеть работает, синхронизация между пользователями

---

### Фаза 3: Export & Polish (1-2 недели)

**Задачи:**
1. **SnapshotExporter.kt**
   - JSON format
   - Local storage
   - MQTT publish

2. **UI доработка**
   - Показывать DataQuality
   - Показывать sync stats
   - Утренний отчет с coherence

3. **Оптимизация батареи**
   - Duty cycle для микрофона
   - Adaptive sensor sampling

4. **Тестирование**
   - Unit tests
   - Integration tests
   - Multi-device testing

**Результат:** v0.4.0_SYNC готов к релизу

---

### Timeline: 5-8 недель (оптимистично)

**Реалистичный план:**
- Фаза 1: 3 недели
- Фаза 2: 3 недели
- Фаза 3: 2 недели
- **TOTAL: 8 недель** (~2 месяца)

**Aggressive план (если все идет гладко):**
- Фаза 1: 2 недели
- Фаза 2: 2 недели
- Фаза 3: 1 неделя
- **TOTAL: 5 недель** (~1.5 месяца)

---

## ТЕСТИРОВАНИЕ

### Unit Tests
- WaveEngine (существующий)
- SleepDetector (классификация фаз)
- BinauralGenerator (проверка частот)
- SyncEngine (алгоритм адаптации)

### Integration Tests
- MQTT pub/sub
- Будильник (AlarmManager)
- TTS + Audio Pipeline

### Manual Testing
**Сценарии:**
1. **Одна ночь без сети:**
   - Засыпаем с приложением
   - Проверяем: бинауралка играет, TTS сработал, будильник разбудил
   
2. **Одна ночь с 5 пользователями:**
   - 5 телефонов в одной комнате (или эмуляция через MQTT инжектор)
   - Проверяем: синхронизация работает, когерентность растет

3. **Стресс-тест:**
   - 100 виртуальных клиентов через скрипт
   - MQTT broker не падает, задержки < 1 сек

---

## ДОПОЛНИТЕЛЬНЫЕ ИДЕИ (Post-MVP)

### Терминал (Command Interface)
**Концепция:** Hidden feature для power users

**Команды:**
```
> stats                  # Глобальная статистика
Active users: 1247
Global coherence: 0.73
Your coherence: 0.87

> geocell                # Информация о твоей зоне
Geocell: geo_990_1005
Users in cell: 23
Avg coherence: 0.82

> wave                   # Параметры волны
Dominant frequency: 7.81 Hz
Phase: 142°
Amplitude: 0.89

> users nearby           # Пользователи в радиусе 10 км
geo_990_1005_a3f9c2d8: coherence=0.91, deep_sleep
geo_990_1005_f2b7d1a3: coherence=0.85, light_sleep
...

> export [date]          # Экспорт данных
Exporting 2026-03-05.json...
Done. Saved to /sdcard/...

> help                   # Список команд
Available commands: stats, geocell, wave, users, export, help
```

**UI:**
- Скрытая кнопка в Settings (тап 7 раз на лого)
- Текстовый интерфейс (Terminal Emulator)

### ML Sleep Staging
**Вместо эвристики → Neural Network**
- Обучение на данных пользователей (opt-in)
- LSTM или Transformer
- Точность > 90% (сравнимо с PSG)

### Интеграция с фитнес-трекерами
**Поддержка:**
- Fitbit API
- Garmin Connect
- Oura Ring
- Apple HealthKit (для iOS версии)

---

## ОТКРЫТОСТЬ И ЗАЩИТА ОТ ПАТЕНТОВАНИЯ

### Стратегия
1. **Публикация кода:** GitHub, GPL-3.0 (copyleft)
2. **Публикация протокола:** OSF preregistration (до сбора данных)
3. **Prior Art:** Эти документы + timestamp → невозможно запатентовать после
4. **Citizen Science:** Открытые данные → все могут реплицировать

### Лицензия GPL-3.0
**Что означает:**
- Любой может использовать
- Любой может модифицировать
- Любой может распространять
- НО: Производные работы тоже должны быть GPL (copyleft)
- Нельзя сделать проприетарный форк

**Защита от Levin/компаний:**
- Если кто-то попытается запатентовать → у нас есть Prior Art
- Если кто-то сделает проприетарный форк → нарушение GPL
- Если кто-то использует для коммерческого продукта → обязан открыть исходники

### Что НЕ патентуемо после публикации:
- Концепция синхронизации через MQTT
- Алгоритм адаптации бинауралки
- Формула когерентности
- Протокол телеметрии
- Любые идеи, описанные в этом документе

**Дата публикации техзадания:** 2026-02-14
**Автор:** Sergey Tmenov, Maria Tmenova, Maya Tmenova
**License:** CC-BY 4.0 (документация), GPL-3.0 (код)

---

## АЛЬТЕРНАТИВЫ И УЛУЧШЕНИЯ

### Альтернатива MQTT: WebRTC Data Channels
**Плюсы:**
- Прямой P2P (без сервера)
- Низкая задержка (<50ms)
- Зашифровано из коробки (DTLS)

**Минусы:**
- Сложнее реализация (нужен signaling server)
- Не работает оффлайн (нужен STUN/TURN)
- Меньше подходит для broadcast

**Рекомендация:** Оставить MQTT для MVP, WebRTC рассмотреть в v0.5

### Альтернатива геолокации: IP-based
**Плюсы:**
- Не нужно GPS permission
- Работает без Location Services

**Минусы:**
- Менее точно (~50 км)
- VPN ломает

**Рекомендация:** Комбо - IP fallback если Location denied

### Улучшение: Blockchain для transparency
**Концепция:** Хэши слепков в публичный блокчейн
- Пользователь публикует SHA256(snapshot)
- Нельзя подделать данные задним числом
- Полная прозрачность

**Блокчейн:**
- Ethereum (дорого, $1-5 за транзакцию)
- Polygon (дешевле, $0.01)
- IPFS + Filecoin (хранение)

**Рекомендация:** Post-MVP feature, не критично

---

## ВОПРОСЫ К ОБСУЖДЕНИЮ

1. **MQTT Broker:** Использовать публичный (HiveMQ) или поднять свой?
   - Публичный: Быстрее старт, но ограничения
   - Свой: Полный контроль, но нужен сервер ($5-10/мес)

2. **Детекция фаз сна:** Эвристика или ML?
   - Эвристика: Быстрее, проще, работает сейчас
   - ML: Точнее, но нужны данные для обучения

3. **UI:** Минимализм или rich visualization?
   - Минимализм: Фокус на функционале
   - Rich: Красиво, но больше времени на разработку

4. **Терминал:** Включать в MVP или post-MVP?
   - MVP: Полезно для отладки + wow-factor
   - Post-MVP: Не отвлекает от core features

5. **iOS версия:** Когда?
   - После Android MVP (v0.4.0)
   - Или параллельно (если есть iOS разработчик)

---

## ЗАКЛЮЧЕНИЕ

Это техзадание описывает минимальный функциональный набор для запуска BioKey v0.4.0_SYNC - первой версии с P2P синхронизацией и эффектом "умножения волн".

**Ключевые принципы:**
- Открытость (GPL-3.0)
- P2P (MQTT)
- Научность (резонанс Шумана, биоэлектричество)
- Простота (MVP, без излишеств)
- Защита от патентования (Prior Art)

**Следующий шаг:** Начать разработку с Фазы 1 (Core Features)

---

**Версия:** 1.0  
**Дата:** 2026-02-14  
**Авторы:** Sergey Tmenov, Maria Tmenova, Maya Tmenova  
**Лицензия:** CC-BY 4.0 (документ), GPL-3.0 (будущий код)  
**Контакт:** dr.tmenov@gmail.com

---

END OF TECHNICAL SPECIFICATION
