from core.ISFFramework import ISFContainer, submodule, Param
import serial,time

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class UBootWorker:
    in_params = {
        "Device": Param("Path to device. Example: COM14", required=False, default_value='/dev/tty.usbserial-00000000'),
        "Baudrate": Param("Digital baudrate for serial connection", value_type=int, required=False, default_value=115200),
        "Timeout": Param("Timeout between requests",required=False, default_value=1, value_type=float),
        "VERBOSE": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "TEST": Param("Test out parameter")
    }


    baudrate = 115200
    device_path = ''
    ready = 0
    timeout = 0.1
    ser = ''
    verbose = False

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.verbose = in_params['VERBOSE']

        #return {"TEST": "yay"}

    def __del__(self):
        if self.ready:
            self.ser.close()

    def first_connect(self):
        #try:
        self.ser = serial.Serial(port=self.device_path, baudrate=self.baudrate, timeout=self.timeout)
        self.ready = 1
        #except:
        #    pass

    @submodule(name="TTLTalk",
               description="Send and receive UART messages",
               in_params={
                   "message": Param("Message to send.", value_type=str, required=True)
               },
               out_params={"result": Param("Result answer", value_type=str)})
    def sendCMD(self, params):
        if self.ready==0:
            self.first_connect()
        ans = ''
        cmd = params['message']
        if self.verbose:
            print([cmd])
        if self.ready:
            for x in range(10):
                self.ser.write(b'\r\n'*3)
            for x in range(3):
                self.ser.read(100)
            self.ser.write(cmd.encode('ascii'))
            time.sleep(self.timeout)
            ans = self.ser.read(10000)
        return {'result': ans}

    @submodule(name="UbootOnOff",
                   description="Turn on U-Boot console",
                   in_params={},
                   out_params={"Success": Param("Result status", value_type=bool)})
    def consoleInitializer(self, params):
        print('Turn off your device & wait for 5 seconds.')
        time.sleep(5)
        self.sendCMD({'message':'\x03'})
        print('Turn on device & wait for 10 seconds.')
        counter = 0
        answer = ''
        while counter < 10:
            self.sendCMD({'message': '\x03'})
            counter+=1
        version = self.getVersion({})
        print(version)



    @submodule(name="UARTenvReader",
               description="Get list & values of U-Boot environment",
               in_params={},
               out_params={"ValueList": Param("Dictionary of values", value_type=dict)})
    def getEnvs(self,params):
        #TODO: добавить форматирование
        ans = self.sendCMD({'message':'printenv'})
        return ans


    def getVersion(self, params):
        #TODO: добавить форматирование
        ans = self.sendCMD({'message':'version'})
        return ans

    def dumpFirmMD(self,params):
        #TODO: дампить прошивку из output
        return