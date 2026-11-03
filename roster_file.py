"""NBA 2K27 roster records, decoded using the schema inside the same save.

No executable patches, injected libraries, or guessed memory addresses are used.
The schema and field values are checked against a read-only live-game export.
"""

from i18n import localize
from dataclasses import dataclass
from pathlib import Path
import struct
import zlib
from save_container import Container
from app_runtime import load_profile

NULL_POINTER = (1 << 64) - 1

def read_bits(data, position, length):
    start, shift = divmod(position, 8)
    count = (shift + length + 7) // 8
    if position < 0 or position + length > len(data)*8:
        raise ValueError(localize('字段读取越界'))
    return (int.from_bytes(data[start:start+count], 'big') >> (count*8-shift-length)) & ((1 << length)-1)

def write_bits(data, position, length, value):
    if not 0 <= value < 1 << length:
        raise ValueError(localize('字段值超过位数'))
    start, shift = divmod(position, 8)
    count = (shift + length + 7) // 8
    if position < 0 or position + length > len(data)*8:
        raise ValueError(localize('字段写入越界'))
    trailing = count*8-shift-length
    mask = ((1 << length)-1) << trailing
    old = int.from_bytes(data[start:start+count], 'big')
    data[start:start+count] = ((old & ~mask) | (value << trailing)).to_bytes(count, 'big')

@dataclass(frozen=True)
class Field:
    bit: int
    size: int
    kind: int
    hash: int
    count: int

class Table:
    def __init__(self, container, name):
        self.name = name
        self.id = zlib.crc32(name.encode())
        self.node = next(n for n in container.nodes if n.chunk_id == self.id)
        offset, size = struct.unpack_from('<II', self.node.header, 12)
        raw = container.plain[self.node.offset+60+offset:self.node.offset+60+offset+size]
        if zlib.crc32(raw + b"$!/UiZ133tHax0r@SRSLY!") != struct.unpack_from('<I', self.node.header, 24)[0]:
            raise ValueError(localize('名单附带结构定义校验失败'))
        schema = zlib.decompress(raw) if container.schemas_compressed else raw
        root = struct.unpack_from('>19I', schema)
        self.count = root[15]
        total_bits = (root[0] << 32) | root[1]
        if not self.count or total_bits % self.count:
            raise ValueError(localize('不能确认记录长度'))
        self.stride = total_bits // self.count
        if (total_bits+7)//8 != len(self.node.data):
            raise ValueError(localize('数据长度与附带结构定义不一致'))
        self.fields = {}
        for offset in range(76, len(schema)-75, 76):
            row = struct.unpack_from('>19I', schema, offset)
            if row[0]+row[1] <= self.stride and row[1] and row[6] != 0xFFFFFFFF:
                f = Field(row[0], row[1], row[2], row[4], row[15] if row[7] else 0)
                if f.hash not in self.fields:
                    self.fields[f.hash] = f
        self.data = bytearray(self.node.data)

    def field(self, name, size=None):
        key = name if isinstance(name, int) else zlib.crc32(name.encode())
        field = self.fields[key]
        if size is not None and field.size != size:
            raise ValueError(localize(f'{self.name}: 字段 {name} 的结构已改变'))
        return field

    def get(self, index, name, size=None):
        if not 0 <= index < self.count:
            raise ValueError(localize('记录编号越界'))
        f = self.field(name, size)
        return read_bits(self.data, index*self.stride+f.bit, f.size)

    def set(self, index, name, value, size=None):
        if not 0 <= index < self.count:
            raise ValueError(localize('记录编号越界'))
        f = self.field(name, size)
        write_bits(self.data, index*self.stride+f.bit, f.size, value)

    def string(self, index, name):
        f = self.field(name)
        raw = self.get(index, name).to_bytes((f.size+7)//8, 'big')
        return raw.decode('utf-16be').split('\0',1)[0].strip()

    def pointers(self, index, name):
        f = self.field(name)
        if f.kind != 21 or not f.count or f.size != f.count*64:
            raise ValueError(localize('不是支持的指针数组'))
        return [read_bits(self.data,index*self.stride+f.bit+j*64,64) for j in range(f.count)]

    def set_pointers(self, index, name, values):
        f = self.field(name)
        if f.kind != 21 or f.size != f.count*64 or len(values) > f.count:
            raise ValueError(localize('指针数组容量不足'))
        for j in range(f.count):
            write_bits(self.data,index*self.stride+f.bit+j*64,64,
                       values[j] if j<len(values) else NULL_POINTER)

class Roster:
    def __init__(self, path, profile=None):
        self.container = Container(Path(path))
        self.players = Table(self.container, 'PlayerData')
        self.teams = Table(self.container, 'TeamData')
        self.free_agents = Table(self.container, 'FreeAgentData')
        profile = profile or load_profile()
        actual = dict(PlayerData=self.players.stride, TeamData=self.teams.stride,
                      FreeAgentData=self.free_agents.stride)
        if actual != profile['record_bits']:
            raise ValueError(localize('名单布局与兼容档案不符：'+str(actual)+'；请选择对应版本档案，已停止写入'))
        if self.teams.count < 30:
            raise ValueError(localize('名单缺少完整的 NBA 球队表'))
        for index, expected in enumerate(profile['team_names']):
            if self.teams.string(index, 'UnlocalizedTeamName') != expected:
                raise ValueError(localize('NBA 球队索引与兼容档案不符，已停止写入'))

    def player(self, index):
        p = self.players
        pointer = p.get(index,'CurrentTeam_Internal',64)
        return dict(index=index, uid=p.get(index,'UniqueId',16),
                    name=(p.string(index,'UnlocalizedFirstName')+' '+p.string(index,'UnlocalizedLastName')).strip(),
                    team_index=None if pointer==NULL_POINTER else pointer >> 32,
                    birth_year=p.get(index,'BirthYear',12),
                    birth_month=p.get(index,'BirthMonth',4), birth_day=p.get(index,'BirthDay',5),
                    injury1=dict(type=p.get(index,'InjuryType1',8),status=p.get(index,'InjuryStatus1',3),
                                 duration=p.get(index,1956514736,20)),
                    injury2=dict(type=p.get(index,'InjuryType2',8),status=p.get(index,'InjuryStatus2',3),
                                 duration=p.get(index,3986119178,20)))

    def rebuild(self):
        tables=[self.players,self.teams,self.free_agents]
        return self.container.rebuild({t.id:bytes(t.data) for t in tables if t.data!=t.node.data})
