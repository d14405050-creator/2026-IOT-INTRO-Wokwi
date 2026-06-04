from machine import Pin, SPI
import ili9341
import dht
import time

WHITE  = ili9341.color565(255, 255, 255)
YELLOW = ili9341.color565(255, 255, 0)
CYAN   = ili9341.color565(0, 255, 255)
GRAY   = ili9341.color565(128, 128, 128)
BLACK  = ili9341.color565(0, 0, 0)
RED    = ili9341.color565(255, 0, 0)

spi = SPI(2, baudrate=40_000_000, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)
dc = Pin(17, Pin.OUT)
display = ili9341.ILI9341(spi, cs=cs, dc=dc)

dht22 = dht.DHT22(Pin(4))

# Static layout — draw once
display.fill(BLACK)
display.text((240 - 16 * 8) // 2, 10, "Week 15 Monitor", WHITE)
display.text(20, 90, "Temperature", GRAY)
display.text(140, 90, "Humidity", GRAY)
display.hline(10, 125, 220, GRAY)
display.text(20, 150, "Gas: ----  V: ----", RED)

# Value area dimensions
VAL_W = 64   # enough for 7 chars e.g. "100.0 C"
VAL_H = 8
VAL_Y = 60

while True:
    try:
        dht22.measure()
        t = dht22.temperature()
        h = dht22.humidity()
        print("[DEBUG] temperature = {:.1f}C, humidity = {:.1f}%".format(t, h))

        # Erase old value + draw new — left side
        display.fill_rect(20, VAL_Y, VAL_W, VAL_H, BLACK)
        display.text(20, VAL_Y, "{:.1f} C".format(t), YELLOW)

        # Right side
        display.fill_rect(140, VAL_Y, VAL_W, VAL_H, BLACK)
        display.text(140, VAL_Y, "{:.1f} %".format(h), CYAN)

    except Exception as e:
        print("[ERROR] DHT22 read failed:", e)
        display.fill_rect(20, VAL_Y, 200, VAL_H, BLACK)
        display.text(20, VAL_Y, "Sensor Error", RED)

    time.sleep(2)
