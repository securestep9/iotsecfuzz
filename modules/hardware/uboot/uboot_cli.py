import serial,time





class UbootCLI:
    baudrate = 9600
    device_path = ''
    ready = 0
    timeout = 1
    ser = ''

    def __init__(self, device_path, baudrate, timeout = 1):
        self.baudrate = baudrate
        self.device_path = device_path
        self.timeout = timeout
        self.prepare2send()

    def __del__(self):
        if self.ready:
            self.ser.close()

    def prepare2send(self):
        try:
            self.ser = serial.Serial(port=self.device_path, baudrate=self.baudrate, timeout=self.timeout)
            self.ready = 1
        except:
            pass

    def sendCMD(self,cmd):
        ans = ''
        if self.ready:
            for x in range(10):
                self.ser.write(b'\n\n\n')
            for x in range(3):
                self.ser.read(100)
            self.ser.write(cmd)
            time.sleep(1)
            ans = self.ser.read(10000)
        return ans.decode()

    def getEnvs(self):
        #TODO: добавить форматирование
        ans = self.sendCMD(b'printenv')
        return ans

    def getVersion(self):
        #TODO: добавить форматирование
        ans = self.sendCMD(b'version')
        return ans