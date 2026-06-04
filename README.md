# 2026 IOT INTRO Wokwi

本 repository 用於「物聯網概論」課程每週實作與作業提交。

## 開發環境需求（所有週次）

每個 task 都用 `make` 啟動 Wokwi 模擬器（背後呼叫 `tools/wokwi_run.py`）。請先安裝 **Python 3** 與 **make**：

| OS | 安裝方式 |
|----|----------|
| macOS | `brew install python make`（make 通常已內建） |
| Linux | `sudo apt install python3 make`（Debian/Ubuntu） |
| Windows | 1. 至 [python.org](https://www.python.org/downloads/) 安裝 Python（勾選 *Add to PATH*）<br>2. 用 [Chocolatey](https://chocolatey.org/) `choco install make`、[Scoop](https://scoop.sh/) `scoop install make`，或改用 **Git Bash**（內含 make） |

使用方式（在任一 task 資料夾內）：

```bash
make            # 啟動模擬（請先在 VS Code 開啟 Wokwi 模擬器）
```

> Makefile 會自動選用 `python3`（macOS/Linux）或 `python`（Windows）。如需指定直譯器：`make PYTHON=python3.12`。

## 通用規範（所有週次）

### 1. 每週進度放置原則

- 每一週的成果必須放在對應週次資料夾內（例如：`Weeks/Week-12/`、`Weeks/Week-13/`）。
- 不同週的內容不可混放。
- 每週詳細說明請先閱讀該週資料夾內的 `README.md`。

### 2. 學生作業放置規範

- 依各週題目要求，將解答放在該週的 `solutions/<你的學號>/`。
- 範例：`Weeks/Week-12/solutions/<你的學號>/main.py`
- 本課程 Wokwi 實作開發板統一使用 `ESP32`（除非該週 README 另有明確說明）。

### 3. GitHub 提交流程

1. Fork 課程 repository 到自己的 GitHub。
2. Clone 你的 fork 到本機。
3. 建立分支（建議命名：`weekXX/<你的學號>`）。
4. 只提交你本週的作業內容。
5. Push 後發送 Pull Request 到課程 repo 的 `main` 分支。

### 4. PR 命名建議

- `Week XX Solution - <你的學號>`

### 5. 提交前檢查

- 檔案位於正確週次與正確帳號資料夾。
- 程式可執行。
- 未修改他人作業或非本次作業檔案。

---

## Week 15 — ILI9341 彩屏 + MQ2 氣體感測器 + ThingsBoard

從 Week 13 的 OLED + DHT22 出發，升級為 SPI 全彩 LCD，加入 MQ2 氣體感測器與按鈕觸發煙火動畫，最後透過 MQTT 上傳到 ThingsBoard Cloud。

### Tasks

| Task | 主題 | 詳細說明 | 主程式 | 重點 |
|------|------|---------|--------|------|
| 1 | ILI9341 彩屏 + DHT22 基礎 | [`Weeks/Week-15/in-class/task1/`](Weeks/Week-15/in-class/task1/) | `main.py` | SPI 通訊、LCD 文字顯示 |
| 2 | MQ2 氣體感測 + 按鈕煙火 | [`Weeks/Week-15/in-class/task2/`](Weeks/Week-15/in-class/task2/) + [`task2.md`](Weeks/Week-15/in-class/task2/task2.md) | `main.py` | ADC 類比輸入、非線性校正（K=2.60, P=2.467） |
| 2a | 中文點陣字 + Buffer Blit 加速 | [`Weeks/Week-15/in-class/task2a/`](Weeks/Week-15/in-class/task2a/) + [`task2a.md`](Weeks/Week-15/in-class/task2a/task2a.md) | `main.py` | MONO_HLSB framebuffer、RGB565 合成、Byte swap |
| 3 | WiFi + MQTT 上傳 ThingsBoard | [`Weeks/Week-15/in-class/task3/`](Weeks/Week-15/in-class/task3/) + [`task3.md`](Weeks/Week-15/in-class/task3/task3.md) | `main.py` | umqtt.simple、telemetry JSON、firework_trigger 即時推送 |
| 4 | ThingsBoard Dashboard + Alarm | [`Weeks/Week-15/in-class/task4/`](Weeks/Week-15/in-class/task4/) + [`task4.md`](Weeks/Week-15/in-class/task4/task4.md) | `main.py` | 5 個 Widget、Device Profile Alarm Rule、通知設定 |

### 關鍵技術發現

- **MQ2 非線性模型**: `PPM = K × (v/(1-v))^P` 比線性 `MAX_PPM=290` 更接近真實感測器特性
- **Buffer Blit 優化**: 先合成 RGB565 framebuffer（8KB）再單次 SPI transaction，取代 2000+ 次 `pixel()` 呼叫
- **`_window_and_data()`**: ILI9341 私有方法，可直接寫入 framebuffer 資料區塊
- **umqtt.simple auth**: 需同時指定 `user=ACCESS_TOKEN` 與 `password=...`；缺其一會得到 error code 5（not authorized）
- **fill_rect 記憶體陷阱**: `w × h × 2 bytes`，例如 240×107 會分配 51KB 導致失敗


### 解答

參考解答放在 [`Weeks/Week-15/solutions/`](Weeks/Week-15/solutions/)。
