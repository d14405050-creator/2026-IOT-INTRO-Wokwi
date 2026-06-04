from machine import Pin, SPI, ADC
import ili9341
import dht
import time
import random
from framebuf import FrameBuffer, MONO_HLSB, RGB565

WHITE  = ili9341.color565(255, 255, 255)
YELLOW = ili9341.color565(255, 255, 0)
CYAN   = ili9341.color565(0, 255, 255)
GREEN  = ili9341.color565(0, 255, 0)
BLUE   = ili9341.color565(0, 0, 255)
GRAY   = ili9341.color565(128, 128, 128)
BLACK  = ili9341.color565(0, 0, 0)
RED    = ili9341.color565(255, 0, 0)
PURPLE = ili9341.color565(255, 0, 255)

# ===== MQ2 設定 =====
K = 2.60
P = 2.467

def raw_to_ppm(raw):
    v = raw / 4095.0
    if v >= 1.0:
        v = 0.999
    if v <= 0.0:
        return 0
    ratio = v / (1.0 - v)
    return int(K * (ratio ** P))
# ===================

# ===== 中文點陣資料（32x32，from Week 13）=====
FONT_82B1 = bytearray(
    b'\x00\x00\x00\x00\x00\x7c\x1e\x00\x00\x78\x1c\x10'
    b'\x00\x78\x1c\x18\x00\x78\x1c\x3c\x7f\xff\xff\xfe'
    b'\x00\x78\x1c\x00\x00\x78\x1c\x00\x00\x78\x1c\x00'
    b'\x00\x00\x00\x00\x00\xf0\xf8\x00\x00\xf8\xf0\x00'
    b'\x01\xf0\xf0\x70\x01\xe0\xf0\xf8\x03\xc0\xf1\xf0'
    b'\x03\xc0\xf1\xe0\x07\xe0\xf3\xc0\x0f\xe0\xf7\x00'
    b'\x0d\xe0\xfc\x00\x19\xe0\xf0\x00\x31\xe0\xf0\x00'
    b'\x41\xe0\xf0\x00\x01\xe0\xf0\x04\x01\xe0\xf0\x04'
    b'\x01\xe0\xf0\x04\x01\xe0\xf0\x0c\x01\xe0\xf0\x0c'
    b'\x01\xe0\xff\xfe\x01\xe0\xff\xfe\x01\xe0\x7f\xfe'
    b'\x01\xc0\x0f\xe0\x00\x00\x00\x00'
)
FONT_706B = bytearray(
    b'\x00\x00\x00\x00\x00\x07\x00\x00\x00\x07\x80\x00'
    b'\x00\x07\x80\x00\x00\x07\x80\x00\x00\x07\x80\x00'
    b'\x00\x07\x80\x00\x01\x07\x80\x60\x01\x07\x80\xf0'
    b'\x01\x87\xc0\xfc\x01\x87\xc1\xf0\x03\x87\xc3\xe0'
    b'\x03\x87\xc3\xc0\x07\x8f\x47\x00\x0f\x8f\x6e\x00'
    b'\x1f\x0f\x68\x00\x1f\x0f\x30\x00\x1e\x0f\x30\x00'
    b'\x00\x1e\x30\x00\x00\x1e\x38\x00\x00\x1e\x1c\x00'
    b'\x00\x3c\x1e\x00\x00\x38\x1e\x00\x00\x78\x0f\x80'
    b'\x00\xf0\x0f\xc0\x01\xe0\x07\xf0\x03\xc0\x03\xfc'
    b'\x07\x00\x01\xfe\x0e\x00\x00\xf8\x18\x00\x00\x70'
    b'\x40\x00\x00\x10\x00\x00\x00\x00'
)
FONT_7BC0 = bytearray(
    b'\x07\x80\x38\x00\x07\x84\x7c\x18\x07\x0e\x78\x3c'
    b'\x0f\xff\x7f\xfe\x0e\xe0\xe7\x00\x1c\x70\xc3\x80'
    b'\x18\x71\x83\xc0\x30\x71\x03\xc0\x60\x74\x01\x90'
    b'\x0c\x0e\x38\x38\x0f\xff\x3f\xfc\x0e\x0f\x38\x3c'
    b'\x0e\x0f\x38\x3c\x0e\x0f\x38\x3c\x0e\x0f\x38\x3c'
    b'\x0f\xff\x38\x3c\x0e\x0f\x38\x3c\x0e\x0f\x38\x3c'
    b'\x0e\x0f\x38\x3c\x0e\x0f\x38\x3c\x0f\xff\x38\x3c'
    b'\x0e\x0e\x38\x3c\x0e\x20\x38\x3c\x0e\x38\x38\x3c'
    b'\x0e\x1c\x38\xf8\x0e\x1e\x38\x78\x1f\xff\x38\x78'
    b'\x7f\xc7\x38\x60\x7f\x07\x38\x00\x3c\x07\x38\x00'
    b'\x20\x00\x38\x00\x00\x00\x30\x00\x00\x00\x00\x00'
)
CHARS = {
    '花': (FONT_82B1, 32, 32),
    '火': (FONT_706B, 32, 32),
    '節': (FONT_7BC0, 32, 32),
}
# ==============================

def draw_char(disp, char, x, y, color, shrink=1, scale=1):
    """畫中文字元。scale>1 時用 RGB565 buffer 合成後一次 SPI blit（加速）。"""
    if char not in CHARS:
        return
    data, w, h = CHARS[char]
    fb = FrameBuffer(data, w, h, MONO_HLSB)
    if scale > 1:
        out_w = w * scale
        out_h = h * scale
        buf = bytearray(out_w * out_h * 2)
        out_fb = FrameBuffer(buf, out_w, out_h, RGB565)
        # ILI9341 用 big-endian RGB565；framebuf 用 little-endian
        c = ((color & 0xFF) << 8) | ((color & 0xFF00) >> 8)
        for sy in range(h):
            for sx in range(w):
                if fb.pixel(sx, sy):
                    for dy in range(scale):
                        for dx in range(scale):
                            out_fb.pixel(sx * scale + dx, sy * scale + dy, c)
        disp._window_and_data(x, y, x + out_w - 1, y + out_h - 1, buf)
    else:
        out_w = (w + shrink - 1) // shrink
        for oy in range(out_h := (h + shrink - 1) // shrink):
            sy = oy * shrink
            for ox in range(out_w):
                sx = ox * shrink
                if fb.pixel(sx, sy):
                    disp.pixel(x + ox, y + oy, color)

def draw_text_vertical(disp, text, x, y, color, spacing=0, shrink=1):
    cy = y
    for ch in text:
        if ch in CHARS:
            _, _, h = CHARS[ch]
            draw_char(disp, ch, x, cy, color, shrink=shrink)
            draw_h = (h + shrink - 1) // shrink
            cy += draw_h + spacing
# ==============================

# SPI + ILI9341
spi = SPI(2, baudrate=40_000_000, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
dc = Pin(17, Pin.OUT)
display = ili9341.ILI9341(spi, cs=cs, dc=dc)

# DHT22
dht22 = dht.DHT22(Pin(4))

gas_adc = ADC(Pin(34))
gas_adc.atten(ADC.ATTN_11DB)

btn = Pin(32, Pin.IN, Pin.PULL_UP)

VAL_W = 72
VAL_H = 8
TMP_Y = 60
HUM_Y = 60
GAS_Y = 150


def draw_static():
    display.fill(BLACK)
    display.text((240 - 16 * 8) // 2, 10, "Week 15 Monitor", WHITE)
    pool = [YELLOW, CYAN, GREEN, PURPLE, WHITE]
    for i, ch in enumerate("花火節"):
        c = pool.pop(random.randint(0, len(pool) - 1))
        draw_char(display, ch, 20 + i * 68, 250, c, scale=2)
    display.text(20, 90, "Temperature", GRAY)
    display.text(140, 90, "Humidity", GRAY)
    display.hline(10, 125, 220, GRAY)
    display.text(20, 150, "GAS: ---- ppm", RED)
    display.text(20, 200, "[BUTTON] -> Fireworks!", GRAY)


draw_static()


def launch_fireworks():
    colors = [RED, GREEN, BLUE, YELLOW, PURPLE]

    display.fill_circle(120, 315, 4, WHITE)
    for y in range(310, 240, -5):
        display.fill_circle(120, y + 5, 4, BLACK)
        display.fill_circle(120, y, 4, WHITE)
        time.sleep_ms(3)
    display.fill_circle(120, 240, 4, BLACK)

    for _ in range(40):
        x = 120 + random.randint(-60, 60)
        y = 245 + random.randint(-40, 40)
        c = random.choice(colors)
        s = random.randint(2, 5)
        display.fill_circle(x, y, s, c)

    time.sleep(1)


while True:
    try:
        dht22.measure()
        t = dht22.temperature()
        h = dht22.humidity()

        raw = gas_adc.read()
        ppm = raw_to_ppm(raw)

        print("[DEBUG] t={:.1f}C h={:.1f}% raw={} gas={}ppm".format(t, h, raw, ppm))

        display.fill_rect(20, TMP_Y, VAL_W, VAL_H, BLACK)
        display.text(20, TMP_Y, "{:.1f} C".format(t), YELLOW)

        display.fill_rect(140, HUM_Y, VAL_W, VAL_H, BLACK)
        display.text(140, HUM_Y, "{:.1f} %".format(h), CYAN)

        display.fill_rect(20, GAS_Y, 130, VAL_H, BLACK)
        display.text(20, GAS_Y, "GAS: {} ppm".format(ppm), RED)

        for _ in range(40):
            if btn.value() == 0:
                launch_fireworks()
                draw_static()
                break
            time.sleep_ms(50)

    except Exception as e:
        print("[ERROR]", e)
        time.sleep(2)
