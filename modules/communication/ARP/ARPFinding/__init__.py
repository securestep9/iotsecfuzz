from core.ISFFramework import ISFModule, Param



@ISFModule(name="ARPFinding",
           version="1.0",
           description="Monitors ARP requests and responses",
           author="Not_so_sm4rt_hom3 team")
class ARPFindingModule:
    in_params = {
        "packet_count": Param("Number of packets to capture", required=False,
                              value_type=int, default_value=10)
    }

    out_params = {
        "requests": Param("ARP requests"),
        "responses": Param("ARP responses")
    }

    def __init__(self):
        self.results = {"requests": [], "responses": []}
        from scapy.layers.l2 import ARP
        from scapy.all import sniff

    def run(self, params):
        sniff(prn=lambda *args, **kwargs:
        ARPFindingModule.arp_display(self, *args, **kwargs),
              filter="arp", store=0, count=params["packet_count"])
        return self.results

    def arp_display(self, pkt):

        if pkt[ARP].op == 1:  # who-has (request)
            self.results["requests"].append({"psrc": pkt[ARP].psrc,
                                             "pdst": pkt[ARP].pdst})
        if pkt[ARP].op == 2:  # is-at (response)
            self.results["responses"].append({"hwsrc": pkt[ARP].hwsrc,
                                              "psrc": pkt[ARP].psrc})
