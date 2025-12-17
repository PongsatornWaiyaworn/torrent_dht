# วิธีใช้งาน Torrent DHT

### 1. เปิด Bootstrap Node (โหนดแรก)

เปิด Terminal แล้วรัน:

```bash
python torrent_dht.py --id n1 --port 5000
```

คุณจะเห็น:
```
[NODE n1] bind 0.0.0.0:5000
[NODE n1] public 192.168.1.100:5000
[PEER] file server on 6000
dht>
```

โหนดนี้จะทำหน้าที่เป็น **Bootstrap Node** ที่โหนดอื่นๆ จะเชื่อมต่อเข้ามา

---

### 2. เปิด Node อื่นเข้าร่วมเครือข่าย

เปิด Terminal ใหม่ (หรือเครื่องอื่น) แล้วรัน:

**กรณีเครื่องเดียวกัน:**
```bash
python torrent_dht.py --id n2 --port 5001 --bootstrap 127.0.0.1:5000
```

**กรณีคนละเครื่อง:**
```bash
python torrent_dht.py --id n2 --port 5001 --bootstrap 192.168.1.100:5000
```
> เปลี่ยน `192.168.1.100` เป็น IP ของเครื่องที่รัน bootstrap node

คุณจะเห็น:
```
[NODE n2] bind 0.0.0.0:5001
[NODE n2] public 192.168.1.101:5001
[PEER] file server on 6001
[DHT] node joined ['192.168.1.101', 5001]
dht>
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
[TORRENT] saved as output.txt
```

**เสร็จสิ้น!** ไฟล์ถูกดาวน์โหลดและบันทึกเป็น `output.txt`

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
| `get` | `get <info_hash> <output_filename>` | ดาวน์โหลดไฟล์จาก DHT network |
| `table` | `table` | แสดง DHT storage (info_hash → peers) |

---

## ตัวอย่างการใช้งานจริง

### ตัวอย่าง 1: แชร์ไฟล์ในเครื่องเดียวกัน

**Terminal 1 (Seeder):**
```bash
$ python torrent_dht.py --id n1 --port 5000
dht> share movie.mp4
[HASH] SHA-256 = abc123def456...
```

**Terminal 2 (Leecher):**
```bash
$ python torrent_dht.py --id n2 --port 5001 --bootstrap 127.0.0.1:5000
dht> get abc123def456... downloaded_movie.mp4
[TORRENT] saved as downloaded_movie.mp4
```

---

### ตัวอย่าง 2: แชร์ไฟล์ข้ามเครื่อง

**เครื่อง A (192.168.1.100) - Bootstrap + Seeder:**
```bash
$ python torrent_dht.py --id server --port 5000
dht> share report.pdf
[HASH] SHA-256 = def789ghi012...
```

**เครื่อง B (192.168.1.101) - Leecher:**
```bash
$ python torrent_dht.py --id client1 --port 5000 --bootstrap 192.168.1.100:5000
dht> get def789ghi012... my_report.pdf
```

**เครื่อง C (192.168.1.102) - Leecher:**
```bash
$ python torrent_dht.py --id client2 --port 5000 --bootstrap 192.168.1.100:5000
dht> get def789ghi012... report_copy.pdf
```

---

### ตัวอย่าง 3: หลาย Seeder (ไฟล์เดียวกัน)

**Seeder 1:**
```bash
dht> share file.txt
[HASH] SHA-256 = xyz789...
```

**Seeder 2 (ไฟล์เดียวกัน):**
```bash
dht> share file.txt
[HASH] SHA-256 = xyz789...  # info_hash เดียวกัน
```

**Leecher จะเห็น peers ทั้งคู่:**
```bash
dht> table
{'xyz789...': [('192.168.1.100', 6000), ('192.168.1.101', 6001)]}
```

---

## สิ่งสำคัญที่ต้องรู้

### Ports
- **DHT Port**: พอร์ตสำหรับสื่อสาร DHT (ระบุผ่าน `--port`)
- **File Server Port**: DHT port + 1000 (สร้างอัตโนมัติ)

**ตัวอย่าง:**
- `--port 5000` → DHT: 5000, File Server: 6000
- `--port 5001` → DHT: 5001, File Server: 6001

### IP Address
- ระบบตรวจหา **public IP** อัตโนมัติผ่าน `get_local_ip()`
- ใช้สำหรับประกาศให้ peer อื่นเชื่อมต่อมาดาวน์โหลด

### Info Hash
- คำนวณจาก **SHA-256** ของไฟล์
- ใช้เป็น key ในการค้นหา peers
- ไฟล์เดียวกัน = info_hash เดียวกันเสมอ

---