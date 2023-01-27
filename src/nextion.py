from machine import UART
import os
import time

class NextionWriter:
    def __init__(self, uart: UART) -> None:
        self.uart = uart

    def write(self, buf, insertDelimeter = True):
        self.uart.write(buf)
        if insertDelimeter:
            self.uart.write(bytearray([0xff, 0xff, 0xff]))

    def _waitForACK(self):
        while True:
            time.sleep_ms(10)
            b = self.uart.read()
            if b != None:
                if len(b) == 1 and b[0] == 0x05:
                    break

    def _beginUpdate(self, fileSize: int):
        self.write("whmi-wri {},115200,res0".format(fileSize))
        self._waitForACK()

    def _writeChunkAndWait(self, chunk: bytes):
        self.uart.write(chunk)
        self._waitForACK()

    def update(self, fileName: str):
        try:
            fileInfo = os.stat(fileName)
            fileSize = fileInfo[6]
            if (fileSize == 0):
                print("File {} is empty".format(fileName))
            else:
                print("File found: {}, {} bytes".format(fileName, fileSize))
                self._beginUpdate(fileSize)
                total = 0
                with open(fileName, "rb") as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        total += len(chunk)
                        self._writeChunkAndWait(chunk)
        except OSError:
            print("File does not exist")


class NextionReader:
    buffer = bytearray()

    def __init__(self, uart: UART, actions):
        self.uart = uart
        self.actions = actions

    def process(self, command: bytearray):
        hasMatch = False
        for action in self.actions:
            match = action.checkMatch(command)
            if (match):
                print("Action selected {}".format(action.__class__))
                action.act(command)
                hasMatch = True
                break
            
        if not hasMatch:
            print("No match")

    def hasFullCommand(self):
        bufLen = len(self.buffer)
        if bufLen >= 3 and self.buffer[-1] == self.buffer[-2] == self.buffer[-3] == 0xff:
            print("Got data from Nextion display")
            print(self.buffer)
            self.process(self.buffer[:(bufLen-3)])

            return True
        return False

    def readAndParse(self):
        x  = self.uart.read()
        if x is not None:
            for byte in x:
                self.buffer.append(byte)
                clear = self.hasFullCommand()
                if clear:
                    self.buffer = bytearray()

class NextionAction:
    def __init__(self, writer: NextionWriter):
        self.writer = writer

    def checkMatch(self, data: bytearray):
        return False

    def act(self, data: bytearray):
        pass