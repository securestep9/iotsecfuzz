from core.ISFFramework import ISFContainer, submodule, Param
import time, serial, re
import matplotlib.pyplot as plt
import numpy as np
from mpld3 import fig_to_html

# from modules.hardware.TTLTalker import TTLer

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class LogicAnalyzer:
    in_params = {
        "Device": Param("Path to arduino. Example: COM14", required=False, default_value='/dev/tty.usbserial-00000000'),
        "Baudrate": Param("Digital baudrate for arduino connection", value_type=int, required=False, default_value=115200),
        "Timeout": Param("Timeout between requests",required=False, default_value=0.1, value_type=float),
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
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


    @submodule(name="oscilloscopeUNO",
               description="Arduino UNO as oscilloscope (5 channels). ",
               in_params={
                    "Channels": Param("Arduino channels A(..). Default: 012345", required=False, default_value='012345', value_type=str),
                    "ImagePath": Param("Path to save image",required=False, default_value='/tmp/1.svg', value_type=str),
                    "Time": Param("Time to monitoring channels", required=False, default_value=100, value_type=int),
                    "NeedToOpen": Param("Need to open graph after sniffing", required=False, default_value=True, value_type=bool)
               },
               out_params={"Amount": Param("Amount of found accounts", value_type=int)})
    def oscilloscopeUNO(self,params):

        print('''First need to upload modules/hardware/LogicAnalyzer/arduino.ino''')


        self.ser = serial.Serial(port=self.device_path, baudrate=self.baudrate, timeout=self.timeout, exclusive=1)

        success = 0

        start_time = time.time()

        coords = []
        time_arr = []

        r = '([\d]+) ([\d]+) ([\d]+) ([\d]+) ([\d]+) ([\d]+)'

        while time.time() - start_time < params['Time']:
            ans = self.ser.read(10000).decode('ascii')
            m = ans.split('\n')
            for x in m:
                if bool(re.match(r,x)):
                    res = re.match(r, x)
                    time_arr.append(time.time() - start_time)
                    arr = res.groups()
                    if self.debug:
                        print(arr)
                    coords.append([int(y) for y in arr])

        print(len(coords))

        colors = ['r','g','b','y','b','c']

        for i in range(6):
            plt.plot(np.array(time_arr), np.array([x[i] for x in coords]),colors[i])


        plt.savefig(params['ImagePath'])
        print('Image was saved to: {}'.format(params['ImagePath']))

        if params['NeedToOpen']:
            plt.show()

