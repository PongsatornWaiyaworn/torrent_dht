import socket
import threading
import argparse
import json
import hashlib
import os

BUFFER = 4096
TIMEOUT = 5


# ---------------- Utils ----------------
def file_hash(path):
    print(f"[HASH] reading {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    digest = h.hexdigest()
    print(f"[HASH] SHA-256 = {digest}")
    return digest


# ---------------- DHT Node ----------------
class DHTNode:
    def __init__(self, node_id, bind_host, announce_ip, port):
        self.node_id = node_id
        self.bind_host = bind_host
        self.announce_ip = announce_ip
        self.port = port

        self.routing_table = {}      # node_id -> (host, port)
        self.dht = {}                # info_hash -> [(host, port)]
        self.shared_files = {}       # info_hash -> filename

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((bind_host, port))
        self.sock.listen(5)

        print(f"[NODE {node_id}] bind {bind_host}:{port}")
        print(f"[NODE {node_id}] announce {announce_ip}:{port}")

    # ---------------- Network ----------------
    def start(self):
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            conn, addr = self.sock.accept()
            threading.Thread(
                target=self._handle_conn,
                args=(conn,),
                daemon=True
            ).start()

    def _handle_conn(self, conn):
        try:
            msg = conn.recv(BUFFER).decode()
            req = json.loads(msg)
            resp = self.handle_request(req)
            conn.send(json.dumps(resp).encode())
        except Exception as e:
            conn.send(json.dumps({"error": str(e)}).encode())
        finally:
            conn.close()

    def send(self, host, port, payload):
        s = socket.socket()
        s.settimeout(TIMEOUT)
        try:
            s.connect((host, port))
            s.send(json.dumps(payload).encode())
            return json.loads(s.recv(BUFFER).decode())
        except Exception as e:
            print(f"[NET] failed {host}:{port} -> {e}")
            return {}
        finally:
            s.close()

    # ---------------- DHT ----------------
    def handle_request(self, req):
        t = req.get("type")

        if t == "INTRODUCE":
            self.routing_table[req["id"]] = tuple(req["addr"])
            print(f"[DHT] node joined {req['addr']}")
            return {"status": "OK"}

        if t == "STORE":
            info_hash = req["info_hash"]
            peer = tuple(req["peer"])
            self.dht.setdefault(info_hash, [])
            if peer not in self.dht[info_hash]:
                self.dht[info_hash].append(peer)
            print(f"[DHT] STORE {info_hash[:8]}... -> {peer}")
            return {"status": "STORED"}

        if t == "FIND":
            peers = self.dht.get(req["info_hash"], [])
            print(f"[DHT] FIND {req['info_hash'][:8]}... -> {peers}")
            return {"peers": peers}

        return {"error": "unknown"}

    def join(self, host, port):
        self.routing_table["bootstrap"] = (host, port)
        self.send(host, port, {
            "type": "INTRODUCE",
            "id": self.node_id,
            "addr": [self.announce_ip, self.port]
        })

    # ---------------- Torrent ----------------
    def share(self, filepath):
        info_hash = file_hash(filepath)
        self.shared_files[info_hash] = filepath

        peer = (self.announce_ip, self.port + 1000)

        print(f"[TORRENT] sharing {filepath}")
        print(f"[TORRENT] seeder at {peer}")

        self.dht.setdefault(info_hash, [])
        if peer not in self.dht[info_hash]:
            self.dht[info_hash].append(peer)

        for h, p in self.routing_table.values():
            self.send(h, p, {
                "type": "STORE",
                "info_hash": info_hash,
                "peer": list(peer)
            })

    def lookup(self, info_hash):
        print(f"[TORRENT] lookup {info_hash[:8]}...")
        for h, p in self.routing_table.values():
            resp = self.send(h, p, {
                "type": "FIND",
                "info_hash": info_hash
            })
            if resp.get("peers"):
                print(f"[TORRENT] found peers {resp['peers']}")
                return resp["peers"]
        return []

    # ---------------- File Transfer ----------------
    def serve_file(self):
        port = self.port + 1000

        def server():
            s = socket.socket()
            s.bind(("0.0.0.0", port))
            s.listen(5)
            print(f"[PEER] file server on {port}")

            while True:
                conn, _ = s.accept()
                info_hash = conn.recv(1024).decode()
                path = self.shared_files.get(info_hash)
                if path:
                    with open(path, "rb") as f:
                        conn.sendall(f.read())
                    print(f"[PEER] sent {path}")
                conn.close()

        threading.Thread(target=server, daemon=True).start()

    def download(self, info_hash, save_as):
        peers = self.lookup(info_hash)
        if not peers:
            print("[TORRENT] no peers found")
            return

        host, port = peers[0]
        print(f"[TORRENT] downloading from {host}:{port}")

        s = socket.socket()
        s.settimeout(TIMEOUT)
        s.connect((host, port))
        s.send(info_hash.encode())

        data = b""
        while True:
            chunk = s.recv(BUFFER)
            if not chunk:
                break
            data += chunk

        with open(save_as, "wb") as f:
            f.write(data)

        s.close()

        if file_hash(save_as) == info_hash:
            print(f"[TORRENT] saved as {save_as} (OK)")
        else:
            print("[TORRENT] hash mismatch!")


# ---------------- Main ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--announce", required=True)
    parser.add_argument("--bootstrap")
    args = parser.parse_args()

    node = DHTNode(args.id, "0.0.0.0", args.announce, args.port)
    node.start()
    node.serve_file()

    if args.bootstrap:
        h, p = args.bootstrap.split(":")
        node.join(h, int(p))

    while True:
        cmd = input("dht> ").split()
        if not cmd:
            continue
        if cmd[0] == "share":
            node.share(cmd[1])
        elif cmd[0] == "get":
            node.download(cmd[1], cmd[2])
        elif cmd[0] == "table":
            print(node.dht)
        else:
            print("commands: share <file> | get <info_hash> <out>")