# ТЕХНИЧЕСКОЕ ЗАДАНИЕ
## BioKey v0.3.9.3_ME → v0.4.0_SYNC (Базовая версия для запуска)

---

## КОНЦЕПТУАЛЬНАЯ ОСНОВА

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

#### FR-4.1: Входные данные
**Акселерометр (главный сенсор):**
- Частота: 50 Hz (достаточно для детекции движений)
- Оси: X, Y, Z
- Детектируем: Движения тела, ворочание, дыхание

**Микрофон (опционально):**
- Детектируем: Храп, дыхание, звуки окружения
- Только если пользователь дал разрешение

**Heart Rate (если доступен из wearable):**
- Bluetooth LE подключение к фитнес-трекеру
- Или камера телефона (photoplethysmography, PPG)

#### FR-4.2: Алгоритм классификации фаз

**Упрощенная модель (4 фазы):**
1. **Awake (Бодрствование):**
   - Высокая двигательная активность
   - ЧСС близок к дневному
   - Частые изменения положения тела

2. **Light Sleep (Легкий сон, N1+N2):**
   - Низкая двигательная активность
   - ЧСС снижен на 5-10 bpm
   - Периодические мелкие движения

3. **Deep Sleep (Глубокий сон, N3):**
   - Минимальная двигательная активность
   - ЧСС минимальный (ниже на 10-15 bpm)
   - Дыхание глубокое и ритмичное
   - Длительная неподвижность (>5 минут)

4. **REM (Быстрый сон):**
   - Очень низкая активность тела (атония)
   - ЧСС вариативный (скачки)
   - Мелкие подергивания
   - Возникает циклично (~90 мин цикл)

**Признаки (features):**
```kotlin
data class SleepFeatures(
    val movementIntensity: Float,      // Суммарная активность за 1 мин
    val movementVariance: Float,       // Вариабельность движений
    val heartRate: Float,              // ЧСС (если доступен)
    val heartRateVariability: Float,   // HRV (RMSSD)
    val breathingRate: Float,          // Частота дыхания (из акселерометра)
    val timeInCurrentStage: Int        // Минут в текущей фазе
)
```

**Классификатор (простая эвристика для MVP):**
```kotlin
fun classifySleepStage(features: SleepFeatures): SleepStage {
    return when {
        // Awake
        features.movementIntensity > 50 -> SleepStage.AWAKE
        
        // Deep Sleep
        features.movementIntensity < 5 && 
        features.heartRate < baselineHR - 10 &&
        features.timeInCurrentStage > 5 -> SleepStage.DEEP
        
        // REM (эвристика: после deep sleep, низкая активность, вариативный HR)
        features.movementIntensity < 10 &&
        features.heartRateVariability > 50 &&
        lastStage == SleepStage.DEEP -> SleepStage.REM
        
        // Light Sleep (все остальное)
        else -> SleepStage.LIGHT
    }
}
```

**Улучшение в будущем:**
- ML модель (Random Forest, LSTM)
- Обучение на данных пользователя
- Но для MVP — эвристика достаточна

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

### FR-9: ВИЗУАЛИЗАЦИЯ (ОПЦИОНАЛЬНО ДЛЯ MVP)

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
│  ♥ Avg HR:  58 BPM                  │
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

### Модульная структура
```
app/
├── core/
│   ├── WaveEngine.kt              # Существующий движок (v0.3.9.3)
│   ├── SleepDetector.kt           # Новый: детекция фаз сна
│   ├── BinauralGenerator.kt       # Новый: генерация бинауралки
│   └── SyncEngine.kt              # Новый: синхронизация
│
├── network/
│   ├── MqttManager.kt             # MQTT клиент
│   └── TelemetryPublisher.kt      # Публикация данных
│
├── sensors/
│   ├── AccelerometerReader.kt     # Читает акселерометр
│   ├── MicrophoneReader.kt        # Опционально: микрофон
│   └── HeartRateReader.kt         # Bluetooth LE + фитнес-трекер
│
├── audio/
│   ├── BinauralPlayer.kt          # Проигрывание бинауралки
│   ├── AlarmPlayer.kt             # Будильник
│   └── TtsPlayer.kt               # TTS установка
│
├── storage/
│   ├── SessionLogger.kt           # Логирование сессии
│   └── SnapshotExporter.kt        # Экспорт утреннего слепка
│
├── ui/
│   ├── SleepSessionScreen.kt      # Главный экран (во время сна)
│   ├── MorningReportScreen.kt     # Утренний отчет
│   └── SettingsScreen.kt          # Настройки
│
└── utils/
    ├── Geolocation.kt             # Геолокация + geocells
    └── UserId.kt                  # Генерация user ID
```

### Жизненный цикл session
```
1. [19:00] Пользователь ставит будильник на 07:00 (smart, ±30 мин)
     ↓
2. [23:00] Ложится спать, нажимает "Start Sleep Session"
     ↓
3. [23:00-04:15] Бинауральные ритмы (адаптация к дыханию + синхронизация с сетью)
     ↓ (каждые 30 сек)
4. Публикация телеметрии в MQTT → другие приложения видят
     ↓
5. [04:15-04:45] Окно для TTS установки
     ↓
6. [04:23] TTS сработал (условия выполнены: deep sleep + 7.83 Hz)
     ↓
7. [06:30-07:30] Умный будильник ищет окно просыпания
     ↓
8. [07:12] Нашли light sleep → будильник срабатывает
     ↓
9. [07:12] Пользователь просыпается, видит утренний отчет
     ↓
10. [07:15] Слепок сна экспортируется в JSON + публикуется в MQTT
     ↓
11. [07:15] Session завершен
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
    
    // Alarm
    // (Built-in AlarmManager, no extra libs)
    
    // Math/DSP (для бинауралки)
    implementation "org.apache.commons:commons-math3:3.6.1"
    
    // Testing
    testImplementation "junit:junit:4.13.2"
    androidTestImplementation "androidx.test.ext:junit:1.1.5"
}
```

### Backend (MQTT Broker)
**Опция 1: Публичный broker (для MVP)**
- HiveMQ Cloud (Free tier: 100 клиентов)
- Eclipse IoT (Free, unlimited)
- Mosquitto Test Server (mqtt://test.mosquitto.org)

**Опция 2: Собственный сервер (для production)**
- Eclipse Mosquitto на VPS
- Docker контейнер
- Стоимость: $5-10/месяц (DigitalOcean, Hetzner)

---

## ПЛАН РАЗРАБОТКИ

### Фаза 1: Core Features (2-3 недели)
**Задачи:**
- [ ] Рефакторинг v0.3.9.3 (очистка, документация)
- [ ] Детекция фаз сна (акселерометр)
- [ ] Генератор бинауральных ритмов
- [ ] Жесткий будильник
- [ ] TTS установка

**Результат:** Работающее solo-приложение без сети

### Фаза 2: Smart Features (1-2 недели)
**Задачи:**
- [ ] Умный будильник (поиск окна просыпания)
- [ ] Адаптация бинауралки к дыханию
- [ ] Геолокация + User ID
- [ ] Экспорт слепка сна

**Результат:** Полнофункциональное приложение для 1 пользователя

### Фаза 3: Network Sync (2-3 недели)
**Задачи:**
- [ ] MQTT интеграция
- [ ] Публикация телеметрии
- [ ] Подписка на других пользователей
- [ ] Алгоритм синхронизации
- [ ] Расчет когерентности

**Результат:** P2P сеть работает, эффект синхронизации тестируется

### Фаза 4: Polish & Testing (1-2 недели)
**Задачи:**
- [ ] UI/UX доработка
- [ ] Оптимизация батареи
- [ ] Тестирование на разных устройствах
- [ ] Документация (README, CONTRIBUTING)
- [ ] Подготовка к релизу

**Результат:** v0.4.0_SYNC готов к публикации

**Общий Timeline:** 6-10 недель (1.5-2.5 месяца)

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
-  Любой может использовать
-  Любой может модифицировать
-  Любой может распространять
-  НО: Производные работы тоже должны быть GPL (copyleft)
-  Нельзя сделать проприетарный форк

**Защита от Levin/компаний:**
- Если кто-то попытается запатентовать → у нас есть Prior Art
- Если кто-то сделает проприетарный форк → нарушение GPL
- Если кто-то использует для коммерческого продукта → обязан открыть исходники

### Что НЕ патентуемо после публикации:
-  Концепция синхронизации через MQTT
-  Алгоритм адаптации бинауралки
-  Формула когерентности
-  Протокол телеметрии
-  Любые идеи, описанные в этом документе

**Дата публикации техзадания:** 2026-02-15
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
-  Открытость (GPL-3.0)
-  P2P (MQTT)
-  Научность (резонанс Шумана, биоэлектричество)
-  Простота (MVP, без излишеств)
-  Защита от патентования (Prior Art)

**Следующий шаг:** Начать разработку с Фазы 1 (Core Features)

---

**Версия:** 1.0  
**Дата:** 2026-02-15  
**Авторы:** Sergey Tmenov, Maria Tmenova, Maya Tmenova  
**Лицензия:** CC-BY 4.0 (документ), GPL-3.0 (будущий код)  
**Контакт:** dr.tmenov@gmail.com

---

END OF TECHNICAL SPECIFICATION
