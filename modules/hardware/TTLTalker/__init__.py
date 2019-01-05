from core.ISFFramework import ISFContainer, submodule, Param
import time
import serial


#

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class TTLer:
    in_params = {
        "Device": Param("Path to device. Example: COM14", required=False, default_value='/dev/tty.usbserial-00000000'),
        "Baudrate": Param("Digital baudrate for serial connection", value_type=int, required=False, default_value=115200),
        "Timeout": Param("Timeout between requests",required=False, default_value=1, value_type=float),
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "TEST": Param("Test out parameter")
    }

    baudrate = 115200
    device_path = ''
    connected = 0
    timeout = 0.1
    ser = ''
    debug = False

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.debug = in_params['Debug']

    def __del__(self):
        if self.connected:
            self.ser.close()

    def first_connect(self):
        self.ser = serial.Serial(port=self.device_path, baudrate=self.baudrate, timeout=self.timeout, exclusive=1)
        self.connected = 1

    @submodule(name="sendRawCMDTTL",
               description="Send RAW cmd through ttl",
               in_params={
                   "raw_message": Param("Raw message to send by UART in hex", default_value='', value_type=str, required=True)
               },
               out_params={"Success": Param("Result status", value_type=bool)})
    def sendRawCMD(self, params):
        if self.connected == 0:
            self.first_connect()
        ans = ''
        cmd = bytes.fromhex(params["raw_message"])
        ans = self.ser.write(cmd)
        time.sleep(self.timeout)
        ans = self.ser.read(10000)
        ans = "".join(map(chr, ans))
        if self.debug:
            print('Serial response:', ans)

        return {'response': ans}


