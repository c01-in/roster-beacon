"""Generate our own small basketball icon without external artwork or fonts."""
import math
from pathlib import Path
import struct
import zlib

root = Path(__file__).resolve().parents[1]
folder = root/'assets'
folder.mkdir(exist_ok=True)
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" rx="13" fill="#14243b"/><circle cx="32" cy="32" r="23" fill="#ff9238" stroke="#14243b" stroke-width="2"/><path d="M9 32h46M32 9v46M16 14q25 18 0 36M48 14q-25 18 0 36" fill="none" stroke="#14243b" stroke-width="2.5"/></svg>\n'
(folder/'app.svg').write_text(svg,encoding='utf-8')
size = 64
scan = bytearray()
for y in range(size):
    scan.append(0)
    for x in range(size):
        dx,dy=x-31.5,y-31.5
        color=(20,36,59,255)
        if abs(dx)>19 and abs(dy)>19 and math.hypot(abs(dx)-19,abs(dy)-19)>12:
            color=(0,0,0,0)
        radius=math.hypot(dx,dy)
        if radius<23:
            color=(255,146,56,255)
            curve=16-0.028*(dy*dy)
            if abs(dx)<1.2 or abs(dy)<1.2 or abs(abs(dx)-curve)<1.2:
                color=(20,36,59,255)
        scan.extend(color)
def chunk(name,data):
    return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(scan),9))+chunk(b'IEND',b'')
ico=struct.pack('<3H',0,1,1)+struct.pack('<4B2H2I',size,size,0,0,1,32,len(png),22)+png
(folder/'app.ico').write_bytes(ico)
