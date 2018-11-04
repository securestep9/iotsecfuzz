from core.ISFFramework import ISFContainer, submodule, Param
import time, operator

from libraries.nrf.tools.lib import common

@ISFContainer(version="1.0",
              author="Not_so_sm4rt_hom3 team")
class NRF24:
    in_params = {
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
    }

    debug = False

    def __init__(self,params):
        import crazyradio
        self.debug = params['Debug']

    def __del__(self):
        pass

    @submodule(name="NRF24Sender",
               description="Send NRF24 package",
               in_params={},
               out_params={"Response": Param("Response byte sting", value_type=bytearray)})
    def CrazyRadioSniff(self,params):
        cr = crazyradio.Crazyradio()
        cr.set_channel(90)
        cr.set_data_rate(cr.DR_2MPS)

        res = cr.send_packet([0xff, ])
        print(res.ack, res.data)


    #https://github.com/BastilleResearch/nrf-research-firmware/
    @submodule(name="NRF24AddressFinder",
               description="Finding device address",
               in_params={
                   "Channels": Param("Channel sniffing radius. Example: 0-100",
                                     value_type=str, default_value='0-128', required=False),
                   "CRC": Param("Use crc checksum for finding addresses.",
                                value_type=bool, default_value=True),
                   "Delay": Param("Seconds for sniffing any channel",
                                  value_type=float, default_value=0.1, required=False),
                   "AddressPrefix": Param("Sniffing address prefix. Example: 3a:3d",
                                          value_type=str, default_value='', required=False),
                   "Repeat": Param("Repeat sniff N times",
                                   value_type=int, default_value=10, required=False),
                   "SplitByChannels": Param("Important only without CRC param.",
                                            value_type=bool, default_value=False, required=False),
                   "MinPackets": Param("Min address repeat to be shown (CRC=False)",
                                       value_type=int, default_value=10, required=False)
               },
               out_params={"Addresses": Param("Address array", value_type=list)})
    def sniffRadio(self, params):

        prefix = bytes.fromhex(params['AddressPrefix'].replace(':','')).decode('utf-8')
        c = [int(x) for x in params['Channels'].split('-')]
        count = params["Repeat"]

        channels = [x for x in range(c[0],c[1]+1)]

        common.init_args('./nrf24-scanner.py')
        common.parse_and_init()

        if params['CRC']:
            common.radio.enter_promiscuous_mode(prefix)
        else:
            common.radio.enter_promiscuous_mode_generic(prefix)

        common.radio.set_channel(channels[0])

        byte_arr = []
        channel_byte_arr = {}
        result =[]

        for i in range(count):
            print('Repeat №{}'.format(i+1))
            for c in channels:
                print('Changing channel to {}'.format(c))
                t = time.time()
                common.radio.set_channel(c)
                t = time.time()
                channel_addresses = []
                while time.time()-t < params['Delay']:
                    val = common.radio.receive_payload()
                    if len(val) >= 5:
                        if params['CRC']:
                            address = val[:5]
                            address_hex = ':'.join('{:02X}'.format(b) for b in address)
                            if not address_hex in result:
                                print('Found address: ',address_hex)
                                result.append(address_hex)
                        else:
                            if not params['SplitByChannels']:
                                byte_arr += val
                            else:
                                if not c in channel_byte_arr:
                                    channel_byte_arr[c] = []
                                channel_byte_arr[c] += val

                        if self.debug:
                            print(val)

        if not params['SplitByChannels']:
            string_repeat = {}
            for x in range(5,len(byte_arr)):
                s = ''.join([chr(x) for x in byte_arr[x-5:x]])
                if not s in string_repeat:
                    string_repeat[s] = 1
                else:
                    string_repeat[s] += 1
            if self.debug:
                print(string_repeat)

            sorted_address = sorted(string_repeat.items(), key=operator.itemgetter(1))[::-1]
            if self.debug:
                print(sorted_address[:10])
            for x in sorted_address:
                if x[1] >= params['MinPackets']:
                    address_hex = ':'.join('{:02X}'.format(ord(b)) for b in x[0])
                    result.append(address_hex)
        else:
            for c in channels:
                byte_arr = channels[c]
                string_repeat = {}

                for x in range(5, len(byte_arr)):
                    s = ''.join([chr(x) for x in byte_arr[x - 5:x]])
                    if not s in string_repeat:
                        string_repeat[s] = 1
                    else:
                        string_repeat[s] += 1
                if self.debug:
                    print(string_repeat)

                sorted_address = sorted(string_repeat.items(), key=operator.itemgetter(1))[::-1]
                if self.debug:
                    print(sorted_address[:10])
                for x in sorted_address:
                    if x[1] >= params['MinPackets']:
                        address_hex = ':'.join('{:02X}'.format(ord(b)) for b in x[0])
                        result.append(address_hex)

        return {'Addresses': result}

