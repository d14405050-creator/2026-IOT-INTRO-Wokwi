# Week 15 課程規劃：ILI9341 彩屏 + MQ2 氣體感測器 + ThingsBoard

> 從 Week 13 的 OLED + DHT22 出發，升級為 **SPI 全彩 LCD**、加入 **MQ2 氣體感測器** 與 **按鈕觸發煙火動畫**，最後資料上 ThingsBoard。

---

## 本週學習路線

```
Week 13 (基礎)                  Week 15 (升級)
┌──────────────┐               ┌──────────────────┐
│ SH1107 OLED  │  → 升級 SPI → │ ILI9341 TFT LCD  │ 240x320 全彩
│ I2C 128x128  │               │ SPI, 可畫圖/顏色  │
│ 單色         │               │                  │
├──────────────┤               ├──────────────────┤
│ DHT22        │  → 沿用 →     │ DHT22            │
├──────────────┤               ├──────────────────┤
│              │  → 新增 →     │ MQ2 氣體感測器    │ ADC 類比輸入
│              │  → 新增 →     │ 按鈕              │ GPIO 數位輸入
│              │  → 新增 →     │ 煙火動畫          │ 全彩 LCD 繪圖
│              │  → 新增 →     │ ThingsBoard 儀表板 │ MQTT 上雲端
└──────────────┘               └──────────────────┘
```

---

## 硬體元件

| 元件 | Wokwi 類型 | 通訊介面 |
|------|-----------|---------|
| ESP32 | `board-esp32-devkit-c-v4` | — |
| TFT LCD | **`wokwi-ili9341`** | **SPI**（240x320, 全彩） |
| 溫濕度感測器 | `wokwi-dht22` | GPIO 1-wire |
| 氣體感測器 | **`wokwi-gas-sensor`** (MQ2) | **ADC 類比輸出** + DO 數位 |
| 按鈕 | **`wokwi-pushbutton`** | GPIO 數位輸入 |

---

## 接線表

### ILI9341 TFT LCD（SPI 介面 — 新的！不同於 I2C OLED）

| ILI9341 腳位 | 連到 ESP32 | 說明 |
|-------------|-----------|------|
| VCC | 3V3 或 VIN(5V) | 電源 |
| GND | GND | 接地 |
| CS | **GPIO5** | Chip Select（SPI 片選） |
| D/C | **GPIO17** | Data/Command 選擇 |
| MOSI | **GPIO23** | SPI 資料線（主出從入） |
| SCK | **GPIO18** | SPI 時脈 |
| MISO | (不接) | 顯示器單向通訊，不需要 |
| RST / LED | (模擬中忽略) | Wokwi 不模擬這兩腳 |

> ⚠️ **SPI 跟 I2C 不一樣！** 這是新的通訊協定，需要 4 條線（CS、DC、MOSI、SCK），速度比 I2C 快，適合全彩顯示。

### DHT22（沿用 Week 13，但改 pin）

| DHT22 | 連到 ESP32 |
|-------|-----------|
| DATA | **GPIO4**（← 改了！原本 Week 13 是 GPIO23，但被 SPI MOSI 佔用） |
| VCC | 3V3 |
| GND | GND |

### MQ2 氣體感測器（新的！）

| MQ2 | 連到 ESP32 | 說明 |
|-----|-----------|------|
| **AO** | **GPIO34** | 類比輸出（ADC），濃度越高電壓越高 |
| DO | GPIO33（選配） | 數位輸出，LOW=超過門檻 |
| VCC | **VIN (5V)** | MQ2 需要 5V 電源 |
| GND | GND | 接地 |

### 按鈕（新的！）

| 按鈕 | 連到 ESP32 |
|-----|-----------|
| 一腳 | **GPIO32** |
| 另一腳 | GND |

> 程式端啟用 `PULL_UP`，按下去讀到 `0`。

---

## GPIO 總表

| GPIO | 連到 | 功能 |
|------|------|------|
| GPIO4 | DHT22 DATA | 溫濕度 |
| GPIO5 | ILI9341 CS | SPI 片選 |
| GPIO17 | ILI9341 DC | SPI 資料/命令 |
| GPIO18 | ILI9341 SCK | SPI 時脈 |
| GPIO23 | ILI9341 MOSI | SPI 資料 |
| GPIO32 | 按鈕 | 數位輸入（煙火觸發） |
| GPIO33 | MQ2 DO（選配） | 數位門檻 |
| GPIO34 | MQ2 AO | ADC 類比輸入 |
VIN(5V) | MQ2 VCC | 電源 |
3V3 | ILI9341 VCC | 電源 |

**共 7 個 GPIO + 2 個電源**，ESP32 完全足夠。

---

## 4 步驟教學（課堂實作）

### Step 1：硬體設計（~10 min）

開啟 `diagram.json`，學生觀察：
- ILI9341 接在 SPI 腳位（不同於 OLED 的 I2C）
- MQ2 的 AO 接在 ADC 專用腳（GPIO34）
- 按鈕接 GPIO32（啟用內部上拉）

不需從頭畫，直接使用提供的 diagram.json。

### Step 2：ILI9341 彩屏顯示 + DHT22 → **task1/**（~20 min）

**第一個挑戰：從 I2C OLED 換成 SPI TFT。**

MicroPython ILI9341 驅動（使用 `mip` 安裝或內含 library）：

```python
from machine import Pin, SPI
import ili9341  # 需安裝或放在 lib/ 下

# SPI 初始化（跟 OLED 的 I2C 完全不同！）
spi = SPI(2, baudrate=40000000, sck=Pin(18), mosi=Pin(23))
dc = Pin(17, Pin.OUT)
cs = Pin(5, Pin.OUT)

# ILI9341 初始化
display = ili9341.ILI9341(spi, cs=cs, dc=dc)
display.fill(ili9341.color565(0, 0, 0))  # 填黑

# 畫彩色的文字
display.text(display.width//2-40, 10, "Week 15", 
             ili9341.color565(255, 255, 0))  # 黃色
display.text(display.width//2-60, 30, "Temperature: 24.5C",
             ili9341.color565(0, 255, 0))    # 綠色
display.text(display.width//2-60, 50, "Humidity: 60.0%",
             ili9341.color565(0, 255, 255))  # 青色
```

**LCD 畫面配置：**
```
┌──────────────────────────────────────┐
│  🌡️ Week 15 Monitor    [●]  Cloud OK  │  ← 白色標題 + 連線狀態
│                                        │
│  ╔═══╗   ┌────┐                       │
│  ║24.5║   │ 60 │%                      │  ← 大字溫度 + 濕度
│  ╚═══╝   └────┘                       │
│  Temp C   Humidity                     │
│                                        │
│  ┌──────────────┐                      │
│  │  Gas: 450    │  ← 氣體濃度數值      │
│  │  Status: OK  │                      │
│  └──────────────┘                      │
│                                        │
│  ╭──────────────────╮                  │
│  │ [BUTTON] Press   │                  │
│  │ for Fireworks!   │                  │  ← 按鈕提示
│  ╰──────────────────╯                  │
└──────────────────────────────────────┘
```

### Step 3：MQ2 氣體 + 按鈕煙火動畫（~20 min）

#### task2/ — 基礎（學生用 skeleton）

`task2/main.py` 含 6 個 TODO，學生自行填入：
- TODO 1: MQ2 ADC 初始化（GPIO34）
- TODO 2: 按鈕初始化（GPIO32, PULL_UP）
- TODO 3: 讀取氣體濃度
- TODO 4: 顯示氣體數值
- TODO 5: 按鈕觸發煙火
- TODO 6: 煙火動畫函式

完整解答在 `task2/main_done.py`。

```python
from machine import ADC, Pin

# MQ2 ADC 初始化
gas_adc = ADC(Pin(34))
gas_adc.atten(ADC.ATTN_11DB)  # 0~3.3V 範圍

# 按鈕初始化
btn = Pin(32, Pin.IN, Pin.PULL_UP)

# 讀取氣體濃度
raw = gas_adc.read()           # 0~4095
ppm = raw_to_ppm(raw)

# 檢查按鈕
if btn.value() == 0:           # 按下（LOW）
    launch_fireworks()
    draw_static()
```

#### task2a/ — 進階：中文花火節 + 繪圖加速

在 task2 的基礎上整合 Week 13 的中文點陣字型，並解決繪圖效能瓶頸：

| 問題 | 解決方案 |
|------|---------|
| `fill_rect()` 大面積 → 51KB 配置失敗 | 只更新變動區域，不一次清大面積 |
| `pixel()` 逐點繪製 → 2000+ SPI 交易 | RGB565 buffer 合成 + `_window_and_data()` 一次 blit |
| `random.shuffle` MicroPython 不存在 | `random.randint` + `list.pop` 替代 |
| 線性 MQ2 模型誤差大 | 非線性功率模型 `PPM = K×(v/(1-v))^P` |

詳細實作與說明見 `task2a/task2a.md`。

---

### Step 4：MQTT 上雲端 + ThingsBoard 儀表板 → **task3/**（已完成）

#### ThingsBoard 操作步驟

1. 登入 [thingsboard.cloud](https://thingsboard.cloud)
2. 右側 **Get started** 點 **Devices**（或左側 **Entities → Devices**）
3. 按右上角 **＋** → **Add device**
4. Name：`test-mqtt`，Profile：`default`，按 **Add**
5. 點進 device → 找 **Access token**（在 Details 分頁或 Manage credentials）
6. 複製 token
7. 在本機用 mosquitto_pub 驗證：
   ```bash
   mosquitto_pub -h thingsboard.cloud -p 1883 \
     -u "你的_ACCESS_TOKEN" \
     -t "v1/devices/me/telemetry" \
     -m '{"temp":28.3}'
   ```
8. 回 ThingsBoard → Latest telemetry 確認收到資料
9. 將 token 填入 `task3/main.py` 的 `ACCESS_TOKEN`

#### MQTT Telemetry 資料格式

```python
telemetry = ujson.dumps({
    "temperature": t,              # DHT22 溫度
    "humidity": h,                 # DHT22 濕度
    "gas_raw": raw,                # MQ2 ADC 原始值
    "gas_ppm": ppm,                # MQ2 換算 PPM
    "firework_trigger": triggered  # 布林值：該筆資料是否觸發過煙火
})
```

| 欄位 | 來源 | 型態 | 用途 |
|------|------|------|------|
| `temperature` | DHT22 | float | 溫度即時監控 |
| `humidity` | DHT22 | float | 濕度即時監控 |
| `gas_raw` | MQ2 ADC | int (0~4095) | 原始 ADC 數值 |
| `gas_ppm` | MQ2 換算 | int | 氣體濃度 PPM |
| `firework_trigger` | 按鈕事件 | bool (0/1) | 標記該筆資料是否伴隨煙火觸發 |

#### ThingsBoard 儀表板 Widget 建議

| Widget | 顯示資料 | 說明 |
|--------|---------|------|
| **Digital display** | `temperature` | 大字當前溫度 |
| **Gauge** | `humidity` | 濕度 0~100% |
| **Timeseries chart** | `temperature` + `humidity` | 雙曲線趨勢 |
| **Timeseries chart** | `gas_raw` 或 `gas_voltage` | 氣體濃度歷史 |

---

## 實際目錄結構

```
Week-15/in-class/
├── imgs/
├── task1/              # Step 2: ILI9341 + DHT22 基本顯示
├── task2/              # Step 3 (基礎): MQ2 + 按鈕 + 煙火
│   ├── main.py         ← 學生用 skeleton（含 TODO）
│   ├── main_done.py    ← 完整解答
│   └── task2.md        ← MQ2 非線性校正說明
├── task2a/             # Step 3 (進階): 中文花火節 + 繪圖加速
│   ├── main.py         ← 完整實作（字型 + buffer blit）
│   └── task2a.md       ← 加速技巧 & MicroPython 相容性
└── task3/              # Step 4: MQTT → ThingsBoard（已建立）
    ├── main.py         ← 完整實作（含 WiFi + MQTT + telemetry）
    ├── task3.md
    └── ...config
```

## 課堂中發現的技術問題

### 1. fill_rect 大面積配置失敗
`ILI9341.fill_rect()` 內部配置 `w * h * 2` bytes 的 buffer。240×107 = **51KB**，會吃光 ESP32 MicroPython heap。

### 2. pixel() 逐點繪製極慢
每個 `pixel()` = 一次 SPI 交易（14 bytes）。64×64 字元約 2000 亮點 → 2000+ 次交易。
**解法**：合成 RGB565 framebuffer，`_window_and_data()` 一次 SPI 送出。

### 3. random.shuffle 不存在
MicroPython 精簡版沒有 `random.shuffle()`，改用 `random.randint + list.pop`。

### 4. MQ2 非線性校正
線性比例換算誤差大，改用功率模型：`PPM = K × (raw/4095 / (1 - raw/4095))^P`

---

## task3 實作規劃

Task 3 在 Task 2 的感測資料基礎上，加入 MQTT 上雲功能：

### 需要整合的項目

1. **WiFi 連線** — `network` 模組
2. **MQTT Client** — `umqtt.simple.MQTTClient`
3. **定時 publish** — 每 N 秒上傳 `temperature`、`humidity`、`gas_raw` 到 ThingsBoard
4. **LCD 顯示連線狀態** — 標題列顯示 `[●] Cloud OK` 或 `[✗] No Cloud`
5. **完整的 main.py** — 合併 Task 2 所有功能 + MQTT

### 預計檔案結構

```
task3/
├── diagram.json      ← 同 task2（硬體不變）
├── main.py           ← 完整實作（含 MQTT）
├── task3.md          ← MQTT 說明文件
└── ...config
```

### MQTT 關鍵程式碼

```python
import network
import ujson
from umqtt.simple import MQTTClient

ACCESS_TOKEN = "YOUR_DEVICE_TOKEN"
TB_HOST = "thingsboard.cloud"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect("SSID", "PASSWORD")
while not wifi.isconnected():
    time.sleep_ms(500)

client = MQTTClient(client_id=b"esp32-001",
                    server=TB_HOST,
                    port=1883,
                    user=ACCESS_TOKEN)
client.connect()

# 在 main loop 中定時 publish
telemetry = ujson.dumps({
    "temperature": t,
    "humidity": h,
    "gas_raw": raw,
    "gas_ppm": ppm,
    "firework_trigger": triggered
})
client.publish(b"v1/devices/me/telemetry", telemetry)
```

### 整合重點

1. **WiFi 連線狀態**顯示在 LCD 標題列：`[●] Cloud OK` / `[✗] No Cloud`
2. **定時 publish**（每 10 秒）正常感測資料 + `firework_trigger: 0`
3. **按鈕觸發煙火時**該次 publish 帶 `firework_trigger: 1`
4. ThingsBoard 可建立儀表板監控五個欄位的歷史趨勢

---

## 課堂中發現的技術問題

---

## 期末考可能出題方向

考題可以設計為**變形題**，抽換其中一個元素：

| 變化 | 考題範例 |
|------|---------|
| 換感測器 | 把 MQ2 換成可變電阻（ADC 概念相同） |
| 換觸發方式 | 按鈕觸發煙火 → 改成氣體超標自動觸發 |
| 加功能 | 在 LCD 上畫出氣體濃度直條圖（bar chart） |
| 抽元件 | 不給 ILI9341 driver，要求學生自己裝 |
| 整合題 | DHT22 + MQ2 + ThingsBoard，LCD 顯示歷史曲線 |

---

## 與舊方案比較

| 項目 | 舊方案（OLED） | 新方案（ILI9341） |
|------|--------------|------------------|
| 顯示器 | SH1107 128x128 單色 OLED | ILI9341 240x320 全彩 TFT |
| 通訊 | I2C | **SPI**（新的協定） |
| 解析度 | 128x128 | **240x320** |
| 顏色 | 1 bit（亮/暗） | **262K 色** |
| 感測器 | DHT22 單一 | DHT22 + **MQ2 + 按鈕** |
| 動畫 | 單色花火節 | **全彩煙火** |
| SPI 概念 | 無 | **新教 SPI 通訊** |
| ADC 概念 | 無 | **新教 ADC 類比讀取** |
| 程式行數 | ~100 行 | ~180 行 |
| 適合期末考 | 變化少 | **可抽換元件多，彈性大** |
