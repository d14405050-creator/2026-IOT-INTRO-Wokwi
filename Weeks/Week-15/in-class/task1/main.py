from machine import Pin, SPI
import ili9341
import dht
import time

# 顏色常數
WHITE  = ili9341.color565(255, 255, 255)
YELLOW = ili9341.color565(255, 255, 0)
CYAN   = ili9341.color565(0, 255, 255)
GRAY   = ili9341.color565(128, 128, 128)
BLACK  = ili9341.color565(0, 0, 0)
RED    = ili9341.color565(255, 0, 0)

# SPI + ILI9341 初始化
spi = SPI(2, baudrate=40_000_000, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
dc = Pin(17, Pin.OUT)
display = ili9341.ILI9341(spi, cs=cs, dc=dc)

# DHT22 初始化（GPIO4）
dht22 = dht.DHT22(Pin(4))

while True:
    try:
        dht22.measure()
        t = dht22.temperature()
        h = dht22.humidity()
        print("[DEBUG] temperature = {:.1f}C, humidity = {:.1f}%".format(t, h))

        # TODO 1: 用 display.fill() 清除畫面（使用 BLACK）

        # TODO 2: 顯示 "Week 15 Monitor" 白色標題
        #         display.text((240 - 16 * 8) // 2, 10, "Week 15 Monitor", 顏色)

        # TODO 3: 顯示溫度數值（黃色）
        #         位置：x=20, y=60  顯示格式："{:.1f} C".format(t)

        # TODO 4: 顯示濕度數值（青色）
        #         位置：x=140, y=60  顯示格式："{:.1f} %".format(h)

        # TODO 5: 顯示 "Temperature" 和 "Humidity" 標籤（灰色）
        #         Temperature 在 x=20, y=90
        #         Humidity    在 x=140, y=90

    except Exception as e:
        print("[ERROR] DHT22 read failed:", e)

    time.sleep(2)
