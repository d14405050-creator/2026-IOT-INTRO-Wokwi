# Week 15：ILI9341 彩屏 + MQ2 氣體感測器 + ThingsBoard

> 從 Week 13 的 OLED + DHT22 出發，升級為 SPI 全彩 LCD，加入 MQ2 氣體感測器與按鈕觸發煙火動畫，最後透過 MQTT 上傳到 ThingsBoard Cloud。

### 快速連結

| Task | 說明文件 |
|------|---------|
| 1 — ILI9341 彩屏 + DHT22 | [`in-class/task1/task1.md`](in-class/task1/task1.md) |
| 2 — MQ2 + 按鈕煙火 | [`in-class/task2/task2.md`](in-class/task2/task2.md) |
| 2a — 中文點陣字 + Buffer Blit | [`in-class/task2a/task2a.md`](in-class/task2a/task2a.md) |
| 3 — MQTT ThingsBoard | [`in-class/task3/task3.md`](in-class/task3/task3.md) |
| 4 — Dashboard + Alarm | [`in-class/task4/task4.md`](in-class/task4/task4.md) |

---

## 本週學習路線

```
Week 13 (基礎)               Week 15 (升級)
┌──────────────┐            ┌──────────────────┐
│ SH1107 OLED  │ → 升級 SPI → │ ILI9341 TFT LCD  │ 240×320 全彩
│ I2C 128×128  │            │ SPI, 可畫圖/顏色   │
│ 單色         │            │                   │
├──────────────┤            ├──────────────────┤
│ DHT22        │ → 沿用 →  │ DHT22             │
├──────────────┤            ├──────────────────┤
│              │ → 新增 →  │ MQ2 氣體感測器     │ ADC 類比輸入
│              │ → 新增 →  │ 按鈕               │ GPIO 數位輸入
│              │ → 新增 →  │ 煙火動畫           │ 全彩 LCD 繪圖
│              │ → 新增 →  │ ThingsBoard 儀表板  │ MQTT 上雲端
└──────────────┘            └──────────────────┘
```

---

## 硬體元件

| 元件 | Wokwi 類型 | 通訊介面 |
|------|-----------|---------|
| ESP32 | `board-esp32-devkit-c-v4` | — |
| TFT LCD | `wokwi-ili9341` | SPI（240×320, 全彩 262K 色） |
| 溫濕度感測器 | `wokwi-dht22` | GPIO 1-wire |
| 氣體感測器 | `wokwi-gas-sensor` (MQ2) | ADC 類比輸出 |
| 按鈕 | `wokwi-pushbutton` | GPIO 數位輸入 |

---

## 接線（pin-to-pin）

| ILI9341 | ESP32 | DHT22 |
|---------|-------|-------|
| VCC | 3V3 | VCC |
| GND | GND | GND |
| CS | GPIO5 | — |
| D/C | GPIO17 | — |
| MOSI | GPIO23 | — |
| SCK | GPIO18 | — |
| — | GPIO4 | DATA |
| — | GPIO32 | —（按鈕, Task 2）|
| — | GPIO34 | —（MQ2 AO, Task 2）|
| — | VIN(5V) | —（MQ2 VCC, Task 2）|

> 共使用 **7 個 GPIO + 2 組電源**，ESP32 完全足夠。

---

## 4 步驟課堂流程

| 步驟 | 主題 | 預計時間 | 核心概念 | 資料夾 | 說明文件 |
|------|------|---------|---------|--------|---------|
| Task 1 | 硬體設計 + ILI9341 彩屏 + DHT22 | ~30 min | SPI 通訊、LCD 文字顯示、DHT22 讀值 | [`task1.md`](in-class/task1/task1.md) | — |
| Task 2 | MQ2 氣體感測 + 按鈕煙火動畫 | ~20 min | ADC 類比輸入、數位輸入、全彩動畫 | [`task2.md`](in-class/task2/task2.md) + [`task2a.md`](in-class/task2a/task2a.md) | — |
| Task 3 | WiFi + MQTT 上傳 ThingsBoard | ~15 min | 網路連線、MQTT publish、JSON 格式 | [`task3.md`](in-class/task3/task3.md) | — |
| Task 4 | ThingsBoard 儀表板設計 | ~15 min | Widget 配置、即時資料視覺化 + Alarm 告警 | [`task4.md`](in-class/task4/task4.md) | — |

### 關鍵技術發現

- **MQ2 非線性模型**: `PPM = K × (v/(1-v))^P` 比線性 `MAX_PPM=290` 更接近真實感測器特性
- **Buffer Blit 優化**: 先合成 RGB565 framebuffer（8KB）再單次 SPI transaction，取代 2000+ 次 `pixel()` 呼叫
- **`_window_and_data()`**: ILI9341 私有方法，可直接寫入 framebuffer 資料區塊
- **umqtt.simple auth**: 需同時指定 `user=ACCESS_TOKEN` 與 `password=...`；缺其一會得到 error code 5（not authorized）
- **fill_rect 記憶體陷阱**: `w × h × 2 bytes`，例如 240×107 會分配 51KB 導致失敗

### 相關文件

- [課堂計畫（class-plan-wk15.md）](class-plan-wk15.md)
- [解答資料夾](solutions/)

---

## 與 Week 13 對照

| 項目 | Week 13（OLED） | Week 15（ILI9341） |
|------|----------------|-------------------|
| 顯示器 | SH1107 128×128 單色 OLED | ILI9341 240×320 全彩 TFT |
| 通訊 | I2C | **SPI**（新協定） |
| 顏色 | 1 bit（亮/暗） | **262K 色** |
| 感測器 | DHT22 | DHT22 + **MQ2 + 按鈕** |
| 動畫 | 單色花火節 | **全彩煙火** |
| 雲端 | 無 | **ThingsBoard Cloud** |
