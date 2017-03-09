import pyaudio
import sys
import numpy
import random
from LEDStrip import LEDStrip, LEDScreen

p = pyaudio.PyAudio()
row = 8
column = 72 * 4 / row
led_screen = LEDScreen(LEDStrip(row * column), row, column)
max_db = 50.0
sample_rate = 44100 #Hz
sample_per_buffer = 2**11
db_per_pixel = float(max_db) / column
currentColor = 0xe1ff00ff

frequency_per_sample = sample_rate / sample_per_buffer

def getLedIndex(index, pixel):
    if index % 2 == 0:
        return index / 2 * 72 + pixel
    else:
        return (index+1) / 2 * 72 - 1 -pixel

def fillLedIndex(index, pixel, color):
    colors = list(0 for _ in range(0, column))
    for i in range(0, pixel):
        colors[i] = color
    led_screen.showRow(index, colors)

def frequencyToIndex(frequency):
    return int(frequency / frequency_per_sample)

def normalize(x):
    return 20 * numpy.log10(numpy.abs(x)) - 50 - 10

def avg(list):
    return sum(list) / float(len(list))

def getDb(fft, start, end):
    from_index = frequencyToIndex(start)
    until_index = frequencyToIndex(end) + 1
    return avg(fft[from_index:until_index])

def getRandomColor():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return ((((r << 8) + g) << 8) + b) + (0xe5 << 24)


def getMaxDb(fft, start, end):
    from_index = frequencyToIndex(start)
    until_index = frequencyToIndex(end) + 1
    return max(fft[from_index:until_index])

def dbToPixel(db):
    db = min(max_db, db)
    pixel = int(db / db_per_pixel)
    pixel = min(max(0, pixel), column-1)
    return pixel

def dbToColor(db):
    db = min(max(0, db), max_db)
    color = long(db / max_db * 255)
    return color + 0xff0000

def print_spectrum(fft):
    out_str = ''
    for i in range(0, len(fft), 50):
        db = getDb(fft, i, i + 50)
        out_str += "{0:g}\t ".format(db)
    print out_str


def handleData(in_data):
    samples = numpy.fromstring(in_data, dtype=numpy.int16)
    fft = numpy.fft.fft(samples)
    fft = normalize(fft)
    maxDb = getMaxDb(fft, 1000, 5000)
    maxPixel = dbToPixel(maxDb)
    global currentColor
    if (maxPixel > column - 2):
        currentColor = getRandomColor()
    for i in range(0, row):
        db = getDb(fft, i * 500 + 200, (i+1) * 500)
        print db
        fillLedIndex(i, dbToPixel(db), currentColor)
    led_screen.refresh()
    return (None, pyaudio.paContinue)


# This is to release mic when the program  exit
def interrupt_callback():
    print "interrupted manually"
    stream.stop_stream()
    stream.close()
    p.terminate()
    sys.exit()

try:
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    # input_device_index=2,
                    output=False)
    stream.start_stream()
    while True:
        stream.start_stream()
        in_data = stream.read(sample_per_buffer, exception_on_overflow=False)
        stream.stop_stream()
        handleData(in_data)
        # time.sleep(0.1)
except Exception as e:
    print e
finally:
    interrupt_callback()

