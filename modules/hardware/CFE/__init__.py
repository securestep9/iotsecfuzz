from core.ISFFramework import ISFContainer, submodule, Param
import serial,binascii,time,re

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
    uart_class = ''

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.debug = in_params['Debug']
        self.params = in_params
        self.uart_class = self.get_container_class("hardware/TTLTalker")

    def __del__(self):
        if self.connected:
            self.ser.close()

    @submodule(name="initConsole",
               description="Initiate CFE UART console.",
               in_params={
                   "init_cmd": Param("Init string in hex. Example: a1c4c6", value_type=str, required=False, default_value=str(binascii.hexlify(b'stop'),'ascii')),
                },
               out_params={})
    def initConnect(self,params):
        print("Turn off your device! Waiting for 5 seconds")
        time.sleep(5)
        print("Turn on your device!")
        uart_container = self.uart_class(params)
        start_time = time.time()
        end_time = time.time()
        while end_time - start_time < 10:
            out = uart_container.sendRawCMD({"raw_message": params["init_cmd"]})
            end_time = time.time()
            if 'CFE>' in out['response']:
                params["init_cmd"]=str(binascii.hexlify(b'\r\n'*3),'ascii')
                uart_container.sendRawCMD({"raw_message": params["init_cmd"]})
                return {"status":0}
        #out1.update(uart_container.test_two({"T2": 10}))

        return {"status":1}


    @submodule(name="cmdList",
               description="Get list of commands with description.",
               in_params={
                   "Need2Open": Param("Need to initiate U-Boot CLI", value_type=str, required=False,default_value=True),
                   "init_cmd": Param("Init string in hex. Example: a1c4c6", value_type=str, required=False,
                                    default_value=str(binascii.hexlify(b'stop'), 'ascii')),
               },
               out_params={"commands": Param("CMD dictionary", value_type=dict)}
              )
    def getCMDList(self,params):
        if params["Need2Open"]:
            self.initConnect(params)
        uart_container = self.uart_class(params)
        out = uart_container.sendRawCMD({"raw_message": str(binascii.hexlify(b'help\r\n'), 'ascii')})
        m = out["response"].replace('\r','').split('\n')
        if self.debug:
            print(m)
        i = m.index('Available commands:')
        reg_cmds = "(.+[^ ])[ ]{2,}(.+)"
        d = {}
        for x in range(i,len(m)):
            if m[x].startswith('For more information'):
                return {"commands":d}
            if bool(re.match(reg_cmds, m[x])):
                res = re.match(reg_cmds, m[x])
                d[res.groups()[0]] = res.groups()[1]
                if self.debug:
                    print(res)
        return {"commands": d}

    @submodule(name="DeviceList",
               description="Get list of connected devices.",
               in_params={
                   "Need2Open": Param("Need to initiate U-Boot CLI", value_type=str, required=False,
                                      default_value=True),
                   "init_cmd": Param("Init string in hex. Example: a1c4c6", value_type=str, required=False,
                                     default_value=str(binascii.hexlify(b'stop'), 'ascii')),
               },
               out_params={"devices": Param("Device list(dictionary)", value_type=dict)}
               )
    def getDevice(self, params):
        if params["Need2Open"]:
            self.initConnect(params)
        uart_container = self.uart_class(params)
        out = uart_container.sendRawCMD({"raw_message": str(binascii.hexlify(b'show devices\r\n'), 'ascii')})
        m = out["response"].replace('\r','').split('\n')
        if self.debug:
            print(m)
        start = 0
        reg_devices = reg_cmds = "(.+[^ ])[ ]{2,}(.+)"
        devices = {}
        for x in m:
            if start==0:
                if x.startswith('-'*5): start=1
            elif start==1 and not x.startswith('***'):
                if bool(re.match(reg_devices, x)):
                    if self.debug:
                        print(re.match(reg_devices, x).groups())
                    devices[re.match(reg_devices, x).groups()[0]] = re.match(reg_devices, x).groups()[1]

        return {'devices':devices}