import spidev
import time
import threading


def convertToStripData(colors):
    for color in colors:
        # If it comes with the brightness bytes, use it, otherwise use full brightness 0xff
        yield 0xff if color.bit_length() != 32 else int(color >> 24)
        color = int(color % 0x1000000)
        yield color & 0x0000FF  # blue
        yield (color & 0x00FF00) >> 8  # green
        yield color >> 16  # red


def adjust_brightness(color, amount):
    if color.bit_length() == 32:
        brightness = color >> 24
        brightness = min(max(0xE0, brightness + amount), 0xFF)
        return (color % 0x1000000) | (brightness << 24)
    else:
        return color

def getColors():
    for i in xrange(20):
        yield 0xFFff0000
        yield 0xFF00ff00
        yield 0xFF0000ff


def getSteep():
    brightness = 0xE0
    for i in xrange(60):
        if i % 2 == 0:
            brightness += 1
        yield (brightness << 24) + 0xff55ff


class RotateThread(threading.Thread):
    def __init__(self, strip):
        threading.Thread.__init__(self)
        self.strip = strip

    def run(self):
        self.strip.is_rotating = True
        while self.strip.is_rotating:
            self.strip.colorCache = self.strip.colorCache[-1:] + self.strip.colorCache[:-1]
            self.strip.show()
            time.sleep(1.0 / 4)


class LEDStrip:
    start_frame = [0x00, 0x00, 0x00, 0x00]
    stop_frame = [0xFF, 0xFF, 0xFF, 0xFF]

    def __init__(self, pixelNum):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 8000000
        self.colorCache = [0xff000000] * pixelNum
        self.rotateThread = RotateThread(self)
        self.is_rotating = False
        self.pixelNum = pixelNum

    def start_rotate(self):
        self.rotateThread = RotateThread(self)
        self.rotateThread.start()

    def stop_rotate(self):
        self.is_rotating = False
        self.rotateThread.join()

    def show(self):
        self.spi.xfer2(LEDStrip.start_frame)
        self.spi.xfer2(list(convertToStripData(self.colorCache)))
        self.spi.xfer2(LEDStrip.stop_frame)

    def set_color(self, pixel, color):
        self.colorCache[pixel] = color

    def show_colors(self, colors):
        self.colorCache = colors[:self.pixelNum] + self.colorCache[self.pixelNum:]
        self.show()

    def fill(self, length, color):
        self.colorCache = [color] * min(self.pixelNum, length) + [0x000000] * (self.pixelNum - length)
        self.show()

    def fill_range(self, start, end, colors):
        offset = abs(start - end)
        step = 1 if start < end else -1
        j = 0
        for i in range(start, end, step):
            self.colorCache[i] = colors[j]
            j += 1

    def fill_smooth(self, length, start, speed, color):
        for i in xrange(start, length, 1 if start < length else -1):
            self.fill(i, color)
            time.sleep(1.0 / speed)
        self.fill(length, color)

    def dim(self, length):
        self.colorCache = map(lambda c: adjust_brightness(c, -1), self.colorCache[:length]) + self.colorCache[length:]
        self.show()

    def brighten(self, length):
        self.colorCache = map(lambda c: adjust_brightness(c, 1), self.colorCache[:length]) + self.colorCache[length:]
        self.show()

    def dark(self):
        self.colorCache = [0x000000] * self.pixelNum
        self.show()

    def set_dark(self):
        self.colorCache = [0x000000] * self.pixelNum

    def getColor(self, index):
        return self.colorCache[index]

    def get_brightness(self, index):
        color = self.colorCache[index]
        return color >> 24

class LEDScreen:
    # row * column <= ledStrip.pixelNum
    def __init__(self, ledStrip, row, column):
        self.strip = ledStrip
        self.row = row
        self.column = column

    def show(self, pixelArray):
        for index in range(0, len(pixelArray)):
            row = pixelArray[index]
            self.showRow(index, row)

    def showRow(self, index, colors):
        if index % 2 == 0:
            start = index * self.column
            end = start + len(colors)
        else:
            start = (index + 1) * self.column - 1
            end = start - len(colors)
        self.strip.fill_range(start, end, colors)

    def refresh(self):
        self.strip.show()

if __name__ == '__main__':
    c = 0xffff0000
    print hex()