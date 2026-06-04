from machine import Pin, SPI, ADC
import ili9341
import dht
import time
import random

WHITE  = ili9341.color565(255, 255, 255)
YELLOW = ili9341.color565(255, 255, 0)
CYAN   = ili9341.color565(0, 255, 255)
GREEN  = ili9341.color565(0, 255, 0)
GRAY   = ili9341.color565(128, 128, 128)
BLACK  = ili9341.color565(0, 0, 0)
RED    = ili9341.color565(255, 0, 0)
BLUE   = ili9341.color565(0, 0, 255)
PURPLE = ili9341.color565(255, 0, 255)

# ===== MQ2 設定（線性模型）=====
MAX_PPM = 290

def raw_to_ppm(raw):
    return int(raw * MAX_PPM // 4095)
# ==============================

# SPI + ILI9341（沿用 Task 1）
spi = SPI(2, baudrate=40_000_000, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
dc = Pin(17, Pin.OUT)
display = ili9341.ILI9341(spi, cs=cs, dc=dc)

# DHT22（沿用 Task 1）
dht22 = dht.DHT22(Pin(4))


# === TODO 1: MQ2 ADC 初始化 ===
gas_adc = None
# gas_adc = ADC(Pin(??))          # 填入腳位
# gas_adc.atten(ADC.ATTN_11DB)    # 0~3.3V 範圍
# ===============================

# === TODO 2: 按鈕初始化 ===
btn = None
# btn = Pin(??, Pin.IN, Pin.PULL_UP)   # 填入腳位
# ===========================


def draw_static():
    display.fill(BLACK)
    display.text((240 - 16 * 8) // 2, 10, "Week 15 Monitor", WHITE)
    display.text(20, 90, "Temperature", GRAY)
    display.text(140, 90, "Humidity", GRAY)
    display.hline(10, 125, 220, GRAY)
    display.text(20, 150, "GAS: ---- ppm", RED)
    display.text(20, 200, "[BUTTON] -> Fireworks!", GRAY)


draw_static()


def launch_fireworks():
    # TODO 6: 煙火動畫（升空 + 爆炸）
    colors = [RED, GREEN, BLUE, YELLOW, PURPLE]
    # 1. fill_circle 從底部升空
    # 2. 隨機粒子爆炸
    pass


while True:
    try:
        dht22.measure()
        t = dht22.temperature()
        h = dht22.humidity()

        # === TODO 3: 讀取氣體濃度 ===
        raw = 0
        ppm = 0
        # raw = gas_adc.read()
        # ppm = raw_to_ppm(raw)
        # =============================

        print("[DEBUG] t={:.1f}C h={:.1f}% raw={} gas={}ppm".format(t, h, raw, ppm))

        # 更新溫度（左）
        display.fill_rect(20, 60, 72, 8, BLACK)
        display.text(20, 60, "{:.1f} C".format(t), YELLOW)

        # 更新濕度（右）
        display.fill_rect(140, 60, 72, 8, BLACK)
        display.text(140, 60, "{:.1f} %".format(h), CYAN)

        # === TODO 4: 顯示氣體數值 ===
        # display.fill_rect(20, 150, 130, 8, BLACK)
        # display.text(20, 150, "GAS: {} ppm".format(ppm), RED)

        # 每 50ms 檢查按鈕，同時維持 2 秒更新週期
        for _ in range(40):
            # === TODO 5: 按鈕觸發煙火 ===
            # if btn.value() == 0:    # 按下 = LOW
            #     launch_fireworks()
            #     draw_static()
            #     break
            time.sleep_ms(50)

    except Exception as e:
        print("[ERROR]", e)
        time.sleep(2)
