from core.ISFFramework import ISFContainer, submodule, Param
import serial

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class CFEworker:
    in_params = {
        "Device": Param("Path to device. Example: COM14", required=False, default_value='/dev/tty.usbserial-00000000'),
        "Baudrate": Param("Digital baudrate for serial connection", value_type=int, required=False, default_value=115200),
        "Timeout": Param("Timeout between requests",required=False, default_value=0.1, value_type=float),
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Status of result", value_type=int)
    }


    baudrate = 115200
    device_path = ''
    connected = 0
    timeout = 0.1
    ser = ''
    debug = False
    readyConsole = False
    params = ''

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.debug = in_params['Debug']
        self.params = in_params

    def __del__(self):
        if self.connected:
            self.ser.close()

    @submodule(name="CFEinitConsole",
               description="Initiate CFE UART console.",
               in_params={
                   "message": Param("Init string in hex. Example: a1c4c6", value_type=str, required=False),
                },
               out_params={})
    def initConnect(self,params):
        uart_class = self.get_container_class("hardware/TTLTalker/")#sendRawCMDTTL")
        uart_container = uart_class({self.params})
        out1 = uart_container.sendRawCMD({"raw_message": params["message"]})
        out1.update(uart_container.test_two({"T2": 10}))
        return out1