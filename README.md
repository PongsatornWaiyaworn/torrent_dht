# วิธีใช้งาน Torrent DHT

### 1. เปิด Bootstrap Node (โหนดแรก)

เปิด Terminal แล้วรัน:

```bash
python torrent_dht.py --id n1 --port 5000 --announce <IP_ของคุณ>
```

**ตัวอย่าง:**
```bash
# สำหรับทดสอบบนเครื่องเดียวกัน
python torrent_dht.py --id n1 --port 5000 --announce 127.0.0.1

# สำหรับเครื่องอื่นในวง Network เดียวกัน (ใช้ IP จริงของเครื่องคุณ) 
# ในกรณีนี้ขอสมมุติเป็น 192.168.1.100
python torrent_dht.py --id n1 --port 5000 --announce 192.168.1.100
```

คุณจะเห็น:
```
[NODE n1] bind 0.0.0.0:5000
[NODE n1] announce 192.168.1.100:5000
[PEER] file server on 6000
dht>
```

> **หมายเหตุ:** `--announce` คือ IP ที่จะประกาศให้ peer อื่นเชื่อมต่อมา

---

### 2. เปิด Node อื่นเข้าร่วมเครือข่าย

เปิด Terminal ใหม่ (หรือเครื่องอื่น) แล้วรัน:

**กรณีเครื่องเดียวกัน:**
```bash
python torrent_dht.py --id n2 --port 5001 --announce 127.0.0.1 --bootstrap 127.0.0.1:5000
```

**กรณีเครื่องอื่นในวง Network เดียวกัน:**
```bash
python torrent_dht.py --id n2 --port 5001 --announce 192.168.1.101 --bootstrap 192.168.1.100:5000
```

คุณจะเห็น:
```
[NODE n2] bind 0.0.0.0:5001
[NODE n2] announce 192.168.1.101:5001
[PEER] file server on 6001
dht>
```

บน bootstrap node จะแสดง:
```
[DHT] node joined ['192.168.1.101', 5001]
```

---

### 3. แชร์ไฟล์ (Seeder)

บนโหนดที่มีไฟล์ ใช้คำสั่ง:

```bash
dht> share test.txt
```

ระบบจะแสดง:
```
[HASH] reading test.txt
[HASH] SHA-256 = 7ac751a7cf1aff7d0a2dc7157505458c7219ea974ff39161d9e8341f709507be
[TORRENT] sharing test.txt
[TORRENT] seeder at ('192.168.1.100', 6000)
[DHT] STORE 7ac751a7... -> ('192.168.1.100', 6000)
```

**สำเร็จ!** ไฟล์ถูกแชร์แล้ว  
**จดบันทึก info_hash** (7ac751a7...) เพื่อแชร์ให้คนอื่นดาวน์โหลด

---

### 4. ดาวน์โหลดไฟล์ (Leecher)

บนโหนดอื่นที่ต้องการไฟล์ ใช้คำสั่ง:

```bash
dht> get 7ac751a7cf1aff7d0a2dc7157505458c7219ea974ff39161d9e8341f709507be output.txt
```

ระบบจะแสดง:
```
[TORRENT] lookup 7ac751a7...
[DHT] FIND 7ac751a7... -> [('192.168.1.100', 6000)]
[TORRENT] found peers [('192.168.1.100', 6000)]
[TORRENT] downloading from 192.168.1.100:6000
[HASH] reading output.txt
[HASH] SHA-256 = 7ac751a7cf1aff7d0a2dc7157505458c7219ea974ff39161d9e8341f709507be
[TORRENT] saved as output.txt (OK)
```

**เสร็จสิ้น!** ไฟล์ถูกดาวน์โหลดและ**ตรวจสอบ hash แล้ว**

---

### 5. ดูข้อมูลใน DHT

ตรวจสอบ DHT table:

```bash
dht> table
```

จะแสดง:
```python
{
  '7ac751a7cf1aff7d0a2dc7157505458c7219ea974ff39161d9e8341f709507be': 
    [('192.168.1.100', 6000), ('192.168.1.101', 6001)]
}
```

แสดง mapping ระหว่าง **info_hash → รายการ peers**

---

## คำสั่งทั้งหมด

| คำสั่ง | รูปแบบ | คำอธิบาย |
|--------|--------|----------|
| `share` | `share <filename>` | แชร์ไฟล์และประกาศตัวเป็น seeder |
| `get` | `get <info_hash> <output_filename>` | ดาวน์โหลดไฟล์พร้อมตรวจสอบ hash |
| `table` | `table` | แสดง DHT storage (info_hash → peers) |

---

## ตัวอย่างการใช้งานจริง

### ตัวอย่าง 1: แชร์ไฟล์ในเครื่องเดียวกัน

**Terminal 1 (Bootstrap + Seeder):**
```bash
$ python torrent_dht.py --id n1 --port 5000 --announce 127.0.0.1
dht> share movie.mp4
[HASH] SHA-256 = abc123def456...
[TORRENT] seeder at ('127.0.0.1', 6000)
```

**Terminal 2 (Leecher):**
```bash
$ python torrent_dht.py --id n2 --port 5001 --announce 127.0.0.1 --bootstrap 127.0.0.1:5000
dht> get abc123def456... downloaded_movie.mp4
[TORRENT] saved as downloaded_movie.mp4 (OK)
```

---

### ตัวอย่าง 2: แชร์ไฟล์ข้ามเครื่อง เครื่องอื่นในวง Network เดียวกัน)

**เครื่อง A (192.168.1.100) - Bootstrap + Seeder:**
```bash
$ python torrent_dht.py --id server --port 5000 --announce 192.168.1.100
dht> share report.pdf
[HASH] SHA-256 = def789ghi012...
```

**เครื่อง B (192.168.1.101) - Leecher:**
```bash
$ python torrent_dht.py --id client1 --port 5000 --announce 192.168.1.101 --bootstrap 192.168.1.100:5000
dht> get def789ghi012... my_report.pdf
[TORRENT] saved as my_report.pdf (OK)
```

**เครื่อง C (192.168.1.102) - Leecher:**
```bash
$ python torrent_dht.py --id client2 --port 5000 --announce 192.168.1.102 --bootstrap 192.168.1.100:5000
dht> get def789ghi012... report_copy.pdf
```

---

### ตัวอย่าง 3: หลาย Seeder (ไฟล์เดียวกัน)

**Seeder 1 (192.168.1.100):**
```bash
$ python torrent_dht.py --id s1 --port 5000 --announce 192.168.1.100
dht> share file.txt
[HASH] SHA-256 = xyz789...
```

**Seeder 2 (192.168.1.101) - ไฟล์เดียวกัน:**
```bash
$ python torrent_dht.py --id s2 --port 5000 --announce 192.168.1.101 --bootstrap 192.168.1.100:5000
dht> share file.txt
[HASH] SHA-256 = xyz789...  # info_hash เดียวกัน!
```

**Leecher จะเห็น peers ทั้งคู่:**
```bash
dht> table
{'xyz789...': [('192.168.1.100', 6000), ('192.168.1.101', 6000)]}
```

---

## พารามิเตอร์ที่สำคัญ

### `--id` (Required)
ชื่อของโหนด ใช้สำหรับ identify ในเครือข่าย DHT

```bash
--id n1
--id server
--id client1
```

---

### `--port` (Required)
พอร์ตสำหรับ DHT communication

```bash
--port 5000
--port 5001
```

> **File Server Port:** จะเป็น DHT port + 1000 อัตโนมัติ

---

### `--announce` (Required)
IP address ที่จะประกาศให้ peer อื่นเชื่อมต่อมาดาวน์โหลดไฟล์

**กรณีเครื่องเดียวกัน:**
```bash
--announce 127.0.0.1
```

**กรณีเครื่องอื่นในวง Network เดียวกัน:**
```bash
--announce 192.168.1.100  # ใช้ IP จริงของเครื่อง
```

> **วิธีหา IP:** ใช้คำสั่ง `ipconfig` (Windows) หรือ `ifconfig` (Mac/Linux)

---

### `--bootstrap` (Optional)
IP:Port ของ bootstrap node ที่จะเชื่อมต่อเข้าไป

```bash
--bootstrap 127.0.0.1:5000
--bootstrap 192.168.1.100:5000
```

> **หมายเหตุ:** โหนดแรก (bootstrap) ไม่ต้องระบุพารามิเตอร์นี้

---

### Ports

| Port Type | ค่า | จุดประสงค์ |
|-----------|-----|-----------|
| **DHT Port** | ระบุเอง (เช่น 5000) | สื่อสาร DHT protocol |
| **File Server Port** | DHT + 1000 (เช่น 6000) | ส่งไฟล์ให้ peers |

**ตัวอย่าง:**
- `--port 5000` → DHT: 5000, File Server: 6000
- `--port 5001` → DHT: 5001, File Server: 6001
