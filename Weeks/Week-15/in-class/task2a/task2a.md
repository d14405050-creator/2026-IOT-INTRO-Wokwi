# Task 2a: 中文點陣加速 & MicroPython 陷阱

在 Task 2 煙火硬體的基礎上，本實作主要探討兩個技術問題：

---

## 1. pixel() vs buffer blit — 速度差距 2000 倍

### 問題

`ILI9341.pixel(x, y, color)` 內部實作：

```python
# ili9341.py
def pixel(self, x, y, color):
    self._window_and_data(x, y, x, y, color.to_bytes(2, 'big'))
```

每次呼叫：12 bytes 命令 + 2 bytes 資料 = **14 bytes SPI 交易**。

放大 2 倍的中文字型（64×64）約有 2000 個亮點 → **2000+ 次獨立 SPI 交易**。

```python
# ❌ pixel-by-pixel — 每個點一次 SPI 交易
for sy in range(32):
    for sx in range(32):
        if font_pixel_on(sx, sy):
            for dy in range(2):
                for dx in range(2):
                    disp.pixel(x + sx*2 + dx, y + sy*2 + dy, color)
```

### 解法：RGB565 buffer 合成 + 一次 blit

先在記憶體中將字元畫到一個 RGB565 的 `FrameBuffer`，再透過 `_window_and_data()` 一次 SPI 交易送出整塊資料：

```python
from framebuf import FrameBuffer, MONO_HLSB, RGB565

def draw_char(disp, char, x, y, color, scale=1):
    data, w, h = CHARS[char]
    fb = FrameBuffer(data, w, h, MONO_HLSB)    # 原始字型 32x32 1bpp

    out_w = w * scale          # 64
    out_h = h * scale          # 64
    buf = bytearray(out_w * out_h * 2)          # 8192 bytes
    out_fb = FrameBuffer(buf, out_w, out_h, RGB565)

    # ILI9341 用 big-endian；framebuf 用 little-endian → 互換
    c = ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8)

    for sy in range(h):
        for sx in range(w):
            if fb.pixel(sx, sy):
                for dy in range(scale):
                    for dx in range(scale):
                        out_fb.pixel(sx*scale+dx, sy*scale+dy, c)

    # 一次 SPI 送出整塊 RGB565 資料
    disp._window_and_data(x, y, x + out_w - 1, y + out_h - 1, buf)
```

### 效果對比

| 方法 | SPI 交易次數 | 總資料量 | 使用者感受 |
|------|-------------|---------|-----------|
| `pixel()` × 2000 | **2000 次** | 28KB（分散） | 明顯閃爍／卡頓 |
| buffer blit × 1 | **1 次** | 8KB（連續） | 瞬間完成 |

### 原理

`ILI9341._window_and_data()` 實作了 LCD 控制器的**硬體視窗模式**：

```
設定 Column Address (2Ah) → 設定 Page Address (2Bh) → 寫入 Memory (2Ch)
```

CS 腳位在過程中全程保持 LOW，整塊 pixel 資料連續 SPI 送出。LCD 控制器自動將後續資料填入設定的矩形範圍，省去每次設定位址的開銷。

### 注意事項

**RGB565 byte order** — MicroPython 的 `framebuf` 以 little-endian 儲存 RGB565（`(g<<5|b<<3)<<8 | (r&0xF8)`），但 ILI9341 預期 big-endian，故需 swap：
```python
c = ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8)
```

**buffer size 限制** — ESP32 MicroPython heap ~160KB：
- 64×64×2 = **8KB** ✅ 安全
- 全螢幕 240×320×2 = **153KB** ❌ 配置失敗

---

## 2. random.shuffle 在 MicroPython 不存在

標準 CPython 的 `random.shuffle(list)` 在 MicroPython 中**沒有實作**：

```python
import random

pool = [YELLOW, CYAN, GREEN, PURPLE, WHITE]

# ❌ AttributeError: 'module' object has no attribute 'shuffle'
random.shuffle(pool)

# ✅ 改用 random.randint + list.pop（隨機抽一個移除一個）
for i, ch in enumerate("花火節"):
    c = pool.pop(random.randint(0, len(pool) - 1))
```

運作原理：
1. `random.randint(0, len(pool)-1)` 隨機選一個 index
2. `list.pop(index)` 取出該元素並從 list 移除
3. 下一次抽時 pool 少一個，保證三字不重複

這是一個 MicroPython 與 CPython 標準函式庫的**相容性差異**。MicroPython 為了精簡韌體體積，移除了部分較少使用的模組功能。類似的差異還有：
- `random.seed()` 行為不同
- `time` 模組沒有 `time.time_ns()`
- `math` 模組部分函式名稱不同

---

## 3. fill_rect 記憶體陷阱

```python
# ❌ 這行會 crash — 配置 240×107×2 ≈ 51KB 暫存器
display.fill_rect(0, 213, 240, 107, BLACK)
```

`ILI9341.fill_rect()` 會先配置 `w * h * 2` bytes 的全彩 buffer 再一次送出。大面積（如半個螢幕）會瞬間吃光 ESP32 的 MicroPython heap。

**解法**：改為只更新變動區域，不要一次清大面積。

## 4. 煙火動畫最佳化

- **升空階段**：只擦掉舊點 + 畫新點（2 次 fill_circle），比 fill() 清全螢幕快
- **爆炸階段**：40 顆彩色粒子，用 `fill_circle()` 直接疊在畫面上
- 不需在煙火前先塗黑文字，煙火粒子自然會蓋過去

## 5. 記憶體管理

- ESP32 MicroPython heap ~160KB，大 buffer 要謹慎配置
- 單次 SPI 交易全螢幕（240×320×2 = 153KB）一定會失敗
- 區域性 buffer（如 64×64×2 = 8KB）則完全沒問題

---

## 對照：本目錄 vs task2

| | `task2/` | `task2a/` |
|--|---------|-----------|
| 目的 | 原始作業範本（MQ2 + 按鈕 + 煙火） | 進階整合：中文字型 + 繪圖加速 |
| `main.py` | 含 TODO 註解，學生填空 | 完整實作，含 `draw_char(scale=2)` |
| `task?.md` | 聚焦 MQ2 非線性校正 | 聚焦 pixel/buffer blit 加速 & MicroPython 相容性 |

## 執行

```bash
make run
```
