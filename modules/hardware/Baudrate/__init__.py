from core.ISFFramework import ISFContainer, submodule, Param
import time,string

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")

class Baudrate:
    in_params = {
        "Device": Param("Path to arduino. Example: COM14", required=False, default_value='/dev/tty.usbserial-00000000'),
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
    }


    baudrate_arr = [
        #110,
        300,
        600,
        1200,
        2400,
        4800,
        9600,
        14400,
        19200,
        38400,
        57600,
        115200,
        128000,
        256000
    ]
    device_path = ''
    connected = 0
    timeout = 1
    debug = False
    ser = ''


    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.debug = in_params['Debug']

    def __del__(self):
        if self.connected:
            self.ser.close()

    @submodule(name="ClassicBruteforce",
               description="Bruteforce of device UART baudrate",
               in_params={
                   "Time": Param("Time for any baudrate", default_value=1, value_type=int, required=False)
               },
               out_params={"Baudrate": Param("Baudrate list with the most ascii-readable chars.", value_type=list)})
    def baudrateBruteforce(self,params):
        import serial
        best_percent = -1
        percents = []

        for baudrate in self.baudrate_arr:
            print('Baudrate: ',baudrate)
            ans = b'\x00'
            printable = ''
            t = int(time.time())
            self.ser = serial.Serial(port=self.device_path, baudrate=baudrate, timeout=self.timeout, parity=serial.PARITY_NONE)
            self.connected = 1
            while time.time() - t < params['Time']:
                if self.debug:
                    print('Time :', time.time() - t)
                ans += self.ser.read(10000)
            self.ser.close()
            self.connected = 0
            if self.debug:
                print(ans)
            printable = ''.join([chr(x) for x in ans if chr(x) in string.printable])
            if self.debug:
                print(printable)

            percent = int(len(printable)/len(ans)*100)

            print('Readable chars: {}%'.format(int(len(printable)/len(ans)*100)))

            if percent > best_percent:
                best_percent = percent
                percents = [baudrate]
            elif percent==best_percent:
                percents.append(baudrate)

        print('Best baudrates with {}% readable chars:'.format(best_percent),','.join([str(x) for x in percents]))
        return {'Baudrate': percents}