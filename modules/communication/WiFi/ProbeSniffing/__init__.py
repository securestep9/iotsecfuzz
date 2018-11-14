from scapy.all import *
from scapy.layers.dot11 import Dot11ProbeReq, Dot11Elt

from core.ISFFramework import ISFModule, Param


@ISFModule(name="ProbeSniffing",
           version="1.0",
           description="802.11 probe packet sniffing",
           author="Not_so_sm4rt_hom3 team")
class ProbeSniffingModule:

    in_params = {
        "iface": Param("Target network interface", required=True)
    }

    out_params = {
        "clients": Param("List of SSIDs requested during probing"),
        "mac_list": Param("List of MAC addresses of devices which performed probing"),
    }

    def __init__(self):
        self.clients = []
        self.uni = 0
        self.mach = []

    def phandle(self, p):
        if p.haslayer(Dot11ProbeReq):
            mac = str(p.addr2)
            if p.haslayer(Dot11Elt):
                if p.ID == 0:
                    ssid = p.info
                    if ssid not in self.clients and ssid != "":
                        self.clients.append(ssid)
                        print(str(len(
                            self.clients)) + ".  " + mac + " <--Probing--> " + ssid)
                        self.mach.append(mac)
                        self.uni += 1

    def run(self, params):
        try:
            sniff(iface=params["iface"], prn=lambda x: self.phandle(x), store=0)
        except KeyboardInterrupt:
            pass
        return {"clients": self.clients, "mac_list": self.mach}
