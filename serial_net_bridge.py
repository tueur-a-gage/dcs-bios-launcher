import socket
import struct
import threading
import time
import serial  # important: tu utilises serial.Serial dans run()
from error_mgt import ConfigError, CommunicationError

class SerialNetBridge:
    """
    Bridge COM <-> Network
    - UDP mode:
        * RX multicast 239.255.50.10:5010 -> COM
        * TX COM -> 127.0.0.1:7778 (UDP)
    - TCP mode:
        * RX/TX COM <-> 127.0.0.1:7778 (TCP client)
    """
    def __init__(self, port: int, protocol: str = "UDP", silent: bool = False):
        self.port = port
        self.com_name = f"COM{port}"
        self.protocol = protocol.upper()
        self.silent = silent

        self.stop_event = threading.Event()
        self.threads = []
        self.ser = None
        self.tcp_sock = None

        # network parameters (reprennent ton socat actuel)
        self.mcast_group = "239.255.50.10"
        self.mcast_port = 5010
        self.out_host = "127.0.0.1"
        self.out_port = 7778

    def _log(self, msg: str):
        if not self.silent:
            print(msg)

    def start(self):
        # Ouvre et valide le port série
        self.ser = serial.Serial(
            self.com_name,
            baudrate=250000,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=0.1
        )
        self._log(f"{self.com_name} ouvert (250000 8N1)")

        if self.protocol == "UDP":
            t1 = threading.Thread(target=self._udp_to_serial_loop, daemon=True)
            t2 = threading.Thread(target=self._serial_to_udp_loop, daemon=True)
            t1.start()
            t2.start()
            self.threads.extend([t1, t2])

        elif self.protocol == "TCP":
            # thread qui maintient la connexion TCP et transfère bidirectionnellement
            t = threading.Thread(target=self._tcp_bridge_loop, daemon=True)
            t.start()
            self.threads.append(t)
        else:
            self.ser.close()
            raise ConfigError(f"Invalid protocol {self.protocol}.")

        self._log(f"Bridge {self.protocol} démarré sur {self.com_name}")

    def stop(self):
        self.stop_event.set()

        # ferme socket TCP si ouverte
        try:
            if self.tcp_sock:
                self.tcp_sock.close()
        except Exception:
            pass

        for t in self.threads:
            t.join(timeout=1.0)

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

        self._log(f"Bridge arrêté sur {self.com_name}")

    # ---------------- UDP ----------------
    def _udp_to_serial_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.mcast_port))

        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(self.mcast_group),
            socket.inet_aton("0.0.0.0")
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(0.2)

        while not self.stop_event.is_set():
            try:
                data, _ = sock.recvfrom(65535)
                if data:
                    self.ser.write(data)
            except socket.timeout:
                continue
            except Exception as e:
                self._log(f"[{self.com_name}] UDP->SER erreur: {e}")
                time.sleep(0.2)

        sock.close()

    def _serial_to_udp_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while not self.stop_event.is_set():
            try:
                data = self.ser.read(4096)
                if data:
                    sock.sendto(data, (self.out_host, self.out_port))
            except Exception as e:
                self._log(f"[{self.com_name}] SER->UDP erreur: {e}")
                time.sleep(0.2)
        sock.close()

    # ---------------- TCP ----------------
    def _tcp_bridge_loop(self):
        while not self.stop_event.is_set():
            try:
                self._log(f"[{self.com_name}] Connexion TCP {self.out_host}:{self.out_port}...")
                sock = socket.create_connection((self.out_host, self.out_port), timeout=2.0)
                sock.settimeout(0.1)
                self.tcp_sock = sock
                self._log(f"[{self.com_name}] TCP connecté.")

                t_rx = threading.Thread(target=self._tcp_to_serial_loop, args=(sock,), daemon=True)
                t_tx = threading.Thread(target=self._serial_to_tcp_loop, args=(sock,), daemon=True)
                t_rx.start()
                t_tx.start()

                # attend tant qu'un des threads est vivant
                while not self.stop_event.is_set() and t_rx.is_alive() and t_tx.is_alive():
                    time.sleep(0.1)

            except Exception as e:
                self._log(f"[{self.com_name}] TCP erreur: {e}")
                time.sleep(1.0)
            finally:
                try:
                    if self.tcp_sock:
                        self.tcp_sock.close()
                except Exception:
                    pass
                self.tcp_sock = None

    def _tcp_to_serial_loop(self, sock: socket.socket):
        while not self.stop_event.is_set():
            try:
                data = sock.recv(4096)
                if not data:
                    break
                self.ser.write(data)
            except socket.timeout:
                continue
            except Exception:
                break

    def _serial_to_tcp_loop(self, sock: socket.socket):
        while not self.stop_event.is_set():
            try:
                data = self.ser.read(4096)
                if data:
                    sock.sendall(data)
            except Exception:
                break
