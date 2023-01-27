# A Nextion driver for Micropython. 
It allows to communicate with Nextion displays and update the TFT content. Tested on ESP32 and Sonoff NSPanel. Some parameters are hardcoded (like TFT update baud rate) but easy to change. Feel free to create a PR and formalize this API. To see this API in action see: https://github.com/tomaszbabiuk/aeplugin-nspanel-firmware

# Prerequisites
1. Flash Micropython firmware on your board (https://micropython.org/download/)
2. Install Adafruit ampy to upload .py and .tft files to the Micropython filesystem

```bash
pip install -U adafruit-ampy
```
3. Upload nextion.py on the board
```bash
ampy --port /dev/my_port put src/nextion.py
```
## Examples
All examples are valid for Sonoff NSPanel (https://blakadder.com/nspanel-teardown/) powered by ESP32.

### Example 1 - enabling Nextion panel on NSPanel
```python
from machine import Pin

tft = Pin(4, Pin.OUT)
```

### Example 2 - sending commands from MCU to Nextion display
```python
from nextion import *

uart = UART(2, 115200)
uart.init(115200, bits=8, parity=None, stop=1, tx=16, rx=17)

writer = NextionWriter(uart)
writer.write("page page2") #changes current page to page2
```

There's no need to send FF FF FF at the end of each command. If you want to send data in chunks use insertDelimeter=False parameter:
```python
from nextion import *

writer.write("page ", insertDelimeter = False)
writer.write("page2")
```

### Example 2 - two-way communication using actions
In this example, MCU replies with "vis loadingBtn,0" every time it gets "01 02 FF FF FF" from the screen. This code is usually in a main.py file

```python
from nextion import *

uart = UART(2, 115200)
uart.init(115200, bits=8, parity=None, stop=1, tx=16, rx=17)

writer = NextionWriter(uart)

class SampleAction(NextionAction):
    # execute this action every time when MCU receives 01 02 FF FF FF, note that the data is stripped from FF FF FF
    def checkMatch(self, data: bytearray):
        return len(data) == 2 and data[0] == 0x01 and data[1] == 0x02 

    def act(self, data: bytearray):
        self.writer.write("vis loadingBtn,0") # hide loadingBtn

actions = []
actions.append(SampleAction(writer))

reader = NextionReader(uart, actionsBag)

while True:
    reader.readAndParse()
    time.sleep_ms(50)
```


### Example 3 - flashing/updating the screen with TFT file
The TFT file must be stored in the Micropython file system space. You can use Adafruit's ampy for that:
```bash
ampy --port /dev/my_port put src/my_custom.tft
```

Run this code in REPL:
```python
from nextion import *

uart = UART(2, 115200)
uart.init(115200, bits=8, parity=None, stop=1, tx=16, rx=17)

writer = NextionWriter(uart)
writer.upload("my_custom.tft")
```

or you can do this in an action

```python
from nextion import *

uart = UART(2, 115200)
uart.init(115200, bits=8, parity=None, stop=1, tx=16, rx=17)

writer = NextionWriter(uart)

class SwitchToSetupAction(NextionAction):
    def checkMatch(self, data: bytearray):
        return len(data) == 2 and data[0] == 0x03 and data[1] == 0x04 # execute this action every time when MCU receives 03 04 FF FF FF

    def act(self, data: bytearray):
        self.writer.update("my_custom.tft") # begins screen update procedure

actions = []
actions.append(SwitchToSetupAction(writer))

reader = NextionReader(uart, actionsBag)

while True:
    reader.readAndParse()
    time.sleep_ms(50)
```