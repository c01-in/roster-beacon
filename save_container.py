"""Read and validate the supported unencrypted NBA 2K27 SYNC RDAT v9 container.

Container layout reference: https://github.com/u5ur/2K-Unpack-Save
Only the supported unencrypted native SYNC path is accepted. Encrypted local
saves are explicitly rejected; this module supplies no container decryption.
"""
from __future__ import annotations

from i18n import localize

from dataclasses import dataclass
from pathlib import Path
import struct
import sys
import zlib

NODE_SALT = b"$!/UiZ133tHax0r@SRSLY!"


@dataclass(frozen=True)
class Node:
    offset: int
    capacity: int
    chunk_id: int
    data_offset: int
    stored_size: int
    compressed: bool
    data: bytes
    header: bytes


class Container:
    def __init__(self, path: Path):
        self.path = path
        self.original = path.read_bytes()
        if len(self.original) < 32:
            raise ValueError(localize("名单文件过短"))
        if self.original[:4] == b"EBNH":
            raise ValueError(localize('仅支持未加密的 NBA 2K27 SYNC RDAT v9；加密存档不受支持。'))
        if not (self.original[16:20] == b"BNH(" and
                struct.unpack_from('<QQ', self.original) == (len(self.original)-16, 9)):
            raise ValueError(localize("不是已验证的本地名单或 SYNC RDAT 格式"))
        self.schemas_compressed = False
        self.plain = self.original[16:]
        self.nodes: list[Node] = []
        offset = 0
        while offset < len(self.plain):
            if offset + 24 > len(self.plain):
                raise ValueError(localize("不完整的存档块头"))
            magic, size = struct.unpack_from("<II", self.plain, offset)
            if magic != 0x28484E42:
                raise ValueError(localize(f"未验证的存档格式版本：{magic:#x}"))
            end = offset + 8 + size
            if not offset + 24 <= end <= len(self.plain):
                raise ValueError(localize("存档块长度越界"))
            position = offset + 24
            while position + 60 <= end and self.plain[position:position + 4] == b"BNDL":
                header = self.plain[position:position + 60]
                capacity, chunk_id = struct.unpack_from("<II", header, 4)
                data_offset, stored_size = struct.unpack_from("<II", header, 28)
                if position + 60 + capacity > end or data_offset + stored_size > capacity:
                    raise ValueError(localize("存档节点长度越界"))
                raw = self.plain[position + 60 + data_offset:position + 60 + data_offset + stored_size]
                if zlib.crc32(raw + NODE_SALT) != struct.unpack_from("<I", header, 36)[0]:
                    raise ValueError(localize("存档节点校验和不正确"))
                data, compressed = raw, False
                self.nodes.append(Node(position, capacity, chunk_id, data_offset,
                                       stored_size, compressed, data, header))
                position = (position + 60 + capacity + 7) & ~7
            if position != end:
                raise ValueError(localize("存档块包含未解析的结构"))
            offset = (end + 7) & ~7
        if not self.nodes:
            raise ValueError(localize("存档中未找到有效数据节点"))
    def verify_unchanged_roundtrip(self) -> bool:
        return self.original == self.original[:16] + self.plain

    def rebuild(self, replacements: dict[int, bytes]) -> bytes:
        """Preserve all allocation/layout metadata; refuse growth beyond capacity."""
        if not replacements:
            return self.original
        if len({n.chunk_id for n in self.nodes}) != len(self.nodes):
            raise ValueError(localize("存在重复节点，不能按 ID 修改"))
        if not replacements.keys() <= {n.chunk_id for n in self.nodes}:
            raise ValueError(localize("请求修改的节点不存在"))
        result = bytearray(self.plain)
        for node in self.nodes:
            if node.chunk_id not in replacements:
                continue
            data = replacements[node.chunk_id]
            if len(data) != len(node.data):
                raise ValueError(localize("仅允许相同长度的数据记录修改"))
            raw = data
            aux_offset, aux_size = struct.unpack_from("<II", node.header, 12)
            extra_offset, extra_size = struct.unpack_from("<II", node.header, 40)
            if extra_size or node.data_offset:
                raise ValueError(localize("尚未验证的附加节点布局"))
            auxiliary = self.plain[node.offset + 60 + aux_offset:node.offset + 60 + aux_offset + aux_size]
            if len(raw) + aux_size > node.capacity:
                raise ValueError(localize("修改后的节点超过已有分配空间"))
            offset = node.offset + 60 + node.data_offset
            result[offset:offset + len(raw)] = raw
            if aux_size:
                result[offset + len(raw):offset + len(raw) + aux_size] = auxiliary
                struct.pack_into("<I", result, node.offset + 12, len(raw))
            struct.pack_into("<II", result, node.offset + 32, len(raw), zlib.crc32(raw + NODE_SALT))
        return self.original[:16] + bytes(result)


if __name__ == "__main__":
    import json
    container = Container(Path(sys.argv[1]))
    print(json.dumps(dict(path=str(container.path), unchanged_roundtrip=container.verify_unchanged_roundtrip(),
                          nodes=[dict(chunk_id=hex(node.chunk_id), stored=node.stored_size,
                                      unpacked=len(node.data), compressed=node.compressed)
                                 for node in container.nodes]), indent=2))
