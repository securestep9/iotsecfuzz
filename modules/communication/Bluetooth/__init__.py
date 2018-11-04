from core.ISFFramework import ISFContainer, submodule, Param

from pyubertooth.ubertooth import Ubertooth
from pyubertooth.bluetooth_packet import BtbbPacket

import bluetooth
#from bleep import BLEDevice


@ISFContainer(version="1.0",
              author="Not_so_sm4rt_hom3 team")
class Extractor:
    in_params = {
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
    }

    debug = False

    def __init__(self,params):
        self.debug = params['Debug']

    def __del__(self):
        pass

    @submodule(name="UbertoothSniffer",
               description="Sniff packages with ubertooth.",
               in_params={
                   "SavePath": Param("Save sniffed bluetooth dump to..",
                                     value_type=str,
                                     default_value='',
                                     required=False),
                   "Channel": Param("Set channel.", value_type=int, default_value=-1, required=False),
                   "Time": Param("Seconds of sniffing", value_type=int, default_value=10, required=False),
                   "Count": Param("Amount of packages to sniff", value_type=int, default_value=100500, required=False),
               },
               out_params={"Files": Param("List of files with offset", value_type=list)})
    def UbertoothSniffer(self,params):
        ut = Ubertooth()
        if params['SavePath'] != '':
            print('Saving data to: ',params['SavePath'])
            f = open(params['SavePath'], 'wb')

        if params['Channel'] != -1:
            ut.set_channel(params['Channel'])

        if params['Count'] != 100500:

            for data in ut.rx_stream(count=params['Count']):

                if f:
                    f.write(data)
                print(BtbbPacket(data=data))
        else:

            for data in ut.rx_stream(secs=params['Time']):
                if f:
                    f.write(data)
                print(BtbbPacket(data=data))
        if f:
            f.close()
        ut.close()


    #https://github.com/pybluez/pybluez
    @submodule(name="BluetoothFinder",
               description="Find bluetooth devices with build-in bluetooth module",
               in_params={},
               out_params={"Devices": Param("List of bluetooth devices with addresses", value_type=list)})
    def BluetoothDiscovery(self,params):

        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        print("found %d devices" % len(nearby_devices))
        devices = []
        for addr, name in nearby_devices:
            if self.debug:
                print("  %s - %s" % (addr, name))
            arr = [name,addr.decode('ascii')]
            devices.append(arr)

        return {'Devices': devices}

    '''
    #https://github.com/matthewelse/bleep
    @submodule(name="BLEfinder",
               description="Find Bluetooth-Low-Energy devices with build-in bluetooth module",
               in_params={},
               out_params={"Devices": Param("List of BLE devices with addresses", value_type=list)})
    def BLEdiscowery(self,params):
        devices = BLEDevice.discoverDevices()
        print(devices)
    '''

