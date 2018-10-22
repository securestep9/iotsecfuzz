from core.ISFFramework import ISFContainer, submodule, Param
import serial,time,string,re

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class UBootWorker:
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
    readyConsole = False

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.debug = in_params['Debug']

        #return {"TEST": "yay"}

    def __del__(self):
        if self.connected:
            self.ser.close()

    def first_connect(self):
        #try:
        self.ser = serial.Serial(port=self.device_path, baudrate=self.baudrate, timeout=self.timeout, exclusive=1)
        self.connected = 1
        #except:
        #    pass

    @submodule(name="TTLTalk",
               description="Send and receive UART messages",
               in_params={
                   "message": Param("Message to send.", value_type=str, required=True)
               },
               out_params={"result": Param("Result answer", value_type=str)})
    def sendCMD(self, params):
        if self.connected==0:
            self.first_connect()
        ans = ''
        cmd = params['message']
        if self.debug:
            print([cmd])
        if self.connected:
            for x in range(10):
                self.ser.write(b'\r\n'*3)
            for x in range(3):
                self.ser.read(100)
            self.ser.write(cmd.encode('ascii')+b'\r\n')
            time.sleep(self.timeout)
            ans = self.ser.read(10000)
            if self.debug:
                print('Serial response:',ans.decode('ascii'))
        return {'result': ans.decode('ascii')}

    @submodule(name="UbootOnOff",
                   description="Turn on U-Boot console",
                   in_params={

                   },
                   out_params={"Success": Param("Result status", value_type=bool)})
    def consoleInitializer(self, params):
        print('Turn off your device & wait for 5 seconds.')
        time.sleep(5)
        self.sendCMD({'message':'\x03'})
        print('Turn on device & wait for 10 seconds.')
        counter = 0
        answer = ''
        while counter < 20:
            self.sendCMD({'message': '\x03'})
            counter+=1
        self.readyConsole = 1
        version = self.getVersion({'Need2Open':False})['version']
        if not version!='':
            print('Can\'t create connection to Serial CLI!')
        return {'Success':version != ''}


    @submodule(name="UARTenvReader",
               description="Get list & values of U-Boot environment",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"ValueList": Param("Dictionary of values", value_type=dict)})
    def getEnvs(self,params):

        if params['Need2Open'] and self.readyConsole==0:
            self.consoleInitializer({})
        result = self.sendCMD({'message': 'printenv'})['result']
        if self.debug:
            print(result)
        ans = result.split('U-Boot>')[0].split('printenv\r\n')[1]
        arr = ans.split('\r\n')
        vec = {}
        if self.debug:
            print(arr)
        for x in arr:
            vec[x.split('=')[0]] = '='.join(x.split('=')[1:])
        return {'ValueList':vec}

    @submodule(name="UbootVersion",
               description="Get version of U-Boot loader",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"version": Param("U-Boot version", value_type=str)})
    def getVersion(self, params):
        if params['Need2Open']:
            self.consoleInitializer({})
        ans = ''
        if self.readyConsole:
            result = self.sendCMD({'message':'version'})['result']
            if self.debug:
                print('Result:',result)
            ans = result.split('U-Boot>')[0].split('version\r\n\r\n')[1]
        return {'version':ans}


    @submodule(name="UbootDumper",
               description="Dump firmware with U-Boot CLI output",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=int, required=False, default_value=1),
                   "DumpType": Param("tftp, microsd, serial. Default: serial", value_type=str, required=False, default_value='serial'),
                   "Path": Param("Save dump to.", value_type=str, required=True),
                   "Offset": Param("Offset of firmware data in memory", value_type=int, required=False, default_value=0x40000),
                   "Length": Param("Length of firmware in bytes", value_type=int, required=False, default_value=1024*50)
               },
               out_params={"Size": Param("Size of downloaded firmware", value_type=int)})
    def dumpFirmMD(self,params):
        #TODO: дампить прошивку из output

        if params['Need2Open']:
            self.consoleInitializer({})

        varibles = self.getEnvs(params)['ValueList']
        if self.debug:
            print(varibles)
        runcmd = ';'.join(varibles['bootcmd'].split(';')[0:-1])

        val2replace = re.findall(r'\$[\d\w]*',runcmd)
        for x in val2replace:
            if x in runcmd and x[1:] in varibles:
                runcmd = runcmd.replace(x,varibles[x[1:]])

        #запускаем все кроме последней команды (разделены ;)

        result = self.sendCMD({'message': runcmd})['result']

        if self.debug:
            print(result)

        print('Wait for loading firmware! (10 sec)')

        time.sleep(10)

        offset = params['Offset']
        firmware_bytes = b''
        #считываем
        while offset-params['Offset'] < params['Length']:
            print("Reading memory from {} to {}".format(hex(offset),hex(offset+0x100)))
            runcmd = 'md.l '+hex(offset)

            if self.debug:
                print(runcmd)

            result = self.sendCMD({'message': runcmd})['result']
            if self.debug:

                print('====DEBUG====')
                print(result)

            result_arr = [ x for x in result.split('\r\n') if not x.startswith('U-Boot>') and x != '' and x != runcmd]
            if self.debug:
                print('====DEBUG====')
                print(result_arr)
            r_get_values = "([0-9a-fA-F]{8}): ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8})    (.{16})"
            for x in result_arr:
                if bool(re.match(r_get_values, x)):
                    res = re.match(r_get_values,x)
                    firmware_bytes += b''.join([bytes.fromhex(x)[::-1] for x in res.groups()[1:5]])

                    if self.debug:
                        print(x)
                        print(res.groups())
                        print(firmware_bytes)
                else:
                    print('Found exception at device while dumping.')
                    break
            offset += 0x100
        print('Saving downloaded firmware of size {} bytes to {}'.format(len(firmware_bytes),params['Path']))

        f = open(params['Path'],'wb')
        f.write(firmware_bytes)
        f.close()
        return {'Size': len(firmware_bytes)}