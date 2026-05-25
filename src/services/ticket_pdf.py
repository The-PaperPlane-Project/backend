import os
import struct
from pathlib import Path
from typing import Iterable

from src.models.ticket import Ticket

QR_L_BLOCKS = {
    1: (7, [19]),
    2: (10, [34]),
    3: (15, [55]),
    4: (20, [80]),
    5: (26, [108]),
    6: (18, [68, 68]),
    7: (20, [78, 78]),
    8: (24, [97, 97]),
    9: (30, [116, 116]),
    10: (18, [68, 68, 69, 69]),
    11: (20, [81, 81, 81, 81]),
    12: (24, [92, 92, 93, 93]),
    13: (26, [107, 107, 107, 107]),
    14: (30, [115, 115, 115, 116]),
    15: (22, [87, 87, 87, 87, 87, 88]),
    16: (24, [98, 98, 98, 98, 98, 99]),
    17: (28, [107, 108, 108, 108, 108, 108]),
    18: (30, [120, 120, 120, 120, 120, 121]),
    19: (28, [113, 113, 113, 114, 114, 114, 114]),
    20: (28, [107, 107, 107, 108, 108, 108, 108, 108]),
}

QR_ALIGNMENT_CENTERS = {
    1: [],
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
    5: [6, 30],
    6: [6, 34],
    7: [6, 22, 38],
    8: [6, 24, 42],
    9: [6, 26, 46],
    10: [6, 28, 50],
    11: [6, 30, 54],
    12: [6, 32, 58],
    13: [6, 34, 62],
    14: [6, 26, 46, 66],
    15: [6, 26, 48, 70],
    16: [6, 26, 50, 74],
    17: [6, 30, 54, 78],
    18: [6, 30, 56, 82],
    19: [6, 30, 58, 86],
    20: [6, 34, 62, 90],
}


def _read_uint16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">H", data, offset)[0]


def _read_int16(data: bytes, offset: int) -> int:
    return struct.unpack_from(">h", data, offset)[0]


def _read_uint32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def _find_table(data: bytes, tag: bytes) -> tuple[int, int] | None:
    if len(data) < 12:
        return None

    table_count = _read_uint16(data, 4)
    for index in range(table_count):
        record_offset = 12 + index * 16
        if data[record_offset : record_offset + 4] == tag:
            return _read_uint32(data, record_offset + 8), _read_uint32(data, record_offset + 12)
    return None


def _format_4_cmap(data: bytes, offset: int) -> dict[int, int]:
    seg_count = _read_uint16(data, offset + 6) // 2
    end_offset = offset + 14
    start_offset = end_offset + 2 * seg_count + 2
    delta_offset = start_offset + 2 * seg_count
    range_offset = delta_offset + 2 * seg_count
    glyphs: dict[int, int] = {}

    for index in range(seg_count):
        end_code = _read_uint16(data, end_offset + 2 * index)
        start_code = _read_uint16(data, start_offset + 2 * index)
        delta = _read_int16(data, delta_offset + 2 * index)
        id_range_offset = _read_uint16(data, range_offset + 2 * index)

        if start_code == 0xFFFF and end_code == 0xFFFF:
            continue

        for codepoint in range(start_code, end_code + 1):
            if id_range_offset == 0:
                glyph_id = (codepoint + delta) & 0xFFFF
            else:
                glyph_offset = range_offset + 2 * index + id_range_offset + 2 * (codepoint - start_code)
                if glyph_offset + 2 > len(data):
                    continue
                glyph_id = _read_uint16(data, glyph_offset)
                if glyph_id:
                    glyph_id = (glyph_id + delta) & 0xFFFF

            if glyph_id:
                glyphs[codepoint] = glyph_id

    return glyphs


def _format_12_cmap(data: bytes, offset: int) -> dict[int, int]:
    group_count = _read_uint32(data, offset + 12)
    glyphs: dict[int, int] = {}

    for index in range(group_count):
        group_offset = offset + 16 + index * 12
        start_code = _read_uint32(data, group_offset)
        end_code = _read_uint32(data, group_offset + 4)
        start_glyph = _read_uint32(data, group_offset + 8)

        if start_code > 0xFFFF:
            continue

        for codepoint in range(start_code, min(end_code, 0xFFFF) + 1):
            glyphs[codepoint] = start_glyph + (codepoint - start_code)

    return glyphs


def _load_cmap(font_data: bytes) -> dict[int, int]:
    table = _find_table(font_data, b"cmap")
    if not table:
        return {}

    cmap_offset, _ = table
    subtable_count = _read_uint16(font_data, cmap_offset + 2)
    candidates: list[tuple[int, int, int]] = []

    for index in range(subtable_count):
        record_offset = cmap_offset + 4 + index * 8
        platform_id = _read_uint16(font_data, record_offset)
        encoding_id = _read_uint16(font_data, record_offset + 2)
        subtable_offset = cmap_offset + _read_uint32(font_data, record_offset + 4)
        format_id = _read_uint16(font_data, subtable_offset)
        priority = 0

        if platform_id == 3 and encoding_id == 10 and format_id == 12:
            priority = 4
        elif platform_id == 3 and encoding_id in {1, 0} and format_id == 4:
            priority = 3
        elif platform_id == 0 and format_id in {4, 12}:
            priority = 2
        elif format_id in {4, 12}:
            priority = 1

        if priority:
            candidates.append((priority, format_id, subtable_offset))

    for _, format_id, subtable_offset in sorted(candidates, reverse=True):
        if format_id == 12:
            return _format_12_cmap(font_data, subtable_offset)
        if format_id == 4:
            return _format_4_cmap(font_data, subtable_offset)

    return {}


def _find_font_path() -> Path | None:
    configured_path = os.getenv("PDF_FONT_PATH", "").strip()
    candidates = [
        configured_path,
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists() and path.is_file():
            return path
    return None


def _sanitize_font_name(value: str) -> str:
    return "".join(char for char in value if char.isalnum()) or "TicketFont"


class _BitBuffer:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def append(self, value: int, length: int) -> None:
        for index in range(length - 1, -1, -1):
            self.bits.append((value >> index) & 1)

    def append_bytes(self, values: bytes) -> None:
        for value in values:
            self.append(value, 8)

    def to_bytes(self) -> list[int]:
        return [
            sum(bit << (7 - index) for index, bit in enumerate(self.bits[offset : offset + 8]))
            for offset in range(0, len(self.bits), 8)
        ]


class QrCodeBuilder:
    def __init__(self, text: str) -> None:
        self.data = text.encode("utf-8")
        self.version = self._select_version()
        self.size = 21 + (self.version - 1) * 4
        self.modules: list[list[bool | None]] = [[None] * self.size for _ in range(self.size)]
        self.reserved: list[list[bool]] = [[False] * self.size for _ in range(self.size)]

    def build(self) -> list[list[bool]]:
        self._draw_function_patterns()
        self._draw_codewords(self._make_codewords())
        self._apply_mask()
        self._draw_format_bits()
        if self.version >= 7:
            self._draw_version_bits()
        return [[bool(value) for value in row] for row in self.modules]

    def _select_version(self) -> int:
        for version, (_, block_sizes) in QR_L_BLOCKS.items():
            capacity = sum(block_sizes)
            count_bits = 8 if version <= 9 else 16
            if 4 + count_bits + len(self.data) * 8 <= capacity * 8:
                return version
        raise ValueError("Ticket QR text is too large")

    def _make_codewords(self) -> list[int]:
        ecc_len, block_sizes = QR_L_BLOCKS[self.version]
        data_len = sum(block_sizes)
        bits = _BitBuffer()
        bits.append(0b0100, 4)
        bits.append(len(self.data), 8 if self.version <= 9 else 16)
        bits.append_bytes(self.data)

        remaining_bits = data_len * 8 - len(bits.bits)
        bits.append(0, min(4, remaining_bits))
        while len(bits.bits) % 8:
            bits.append(0, 1)

        data_codewords = bits.to_bytes()
        for pad_byte in [0xEC, 0x11] * data_len:
            if len(data_codewords) >= data_len:
                break
            data_codewords.append(pad_byte)

        blocks: list[list[int]] = []
        offset = 0
        for size in block_sizes:
            block = data_codewords[offset : offset + size]
            blocks.append(block + self._reed_solomon_remainder(block, ecc_len))
            offset += size

        result: list[int] = []
        for index in range(max(block_sizes)):
            for block_index, size in enumerate(block_sizes):
                if index < size:
                    result.append(blocks[block_index][index])
        for index in range(ecc_len):
            for block_index, size in enumerate(block_sizes):
                result.append(blocks[block_index][size + index])
        return result

    def _reed_solomon_remainder(self, data: list[int], degree: int) -> list[int]:
        generator = [1]
        for index in range(degree):
            generator = self._poly_multiply(generator, [1, self._gf_pow(2, index)])

        remainder = [0] * degree
        for value in data:
            factor = value ^ remainder.pop(0)
            remainder.append(0)
            for index, generator_value in enumerate(generator[1:]):
                remainder[index] ^= self._gf_multiply(generator_value, factor)
        return remainder

    def _poly_multiply(self, left: list[int], right: list[int]) -> list[int]:
        result = [0] * (len(left) + len(right) - 1)
        for left_index, left_value in enumerate(left):
            for right_index, right_value in enumerate(right):
                result[left_index + right_index] ^= self._gf_multiply(left_value, right_value)
        return result

    def _gf_multiply(self, left: int, right: int) -> int:
        result = 0
        while right:
            if right & 1:
                result ^= left
            left <<= 1
            if left & 0x100:
                left ^= 0x11D
            right >>= 1
        return result

    def _gf_pow(self, value: int, power: int) -> int:
        result = 1
        for _ in range(power):
            result = self._gf_multiply(result, value)
        return result

    def _set_module(self, row: int, col: int, value: bool, reserved: bool = True) -> None:
        if 0 <= row < self.size and 0 <= col < self.size:
            self.modules[row][col] = value
            if reserved:
                self.reserved[row][col] = True

    def _draw_function_patterns(self) -> None:
        self._draw_finder(0, 0)
        self._draw_finder(0, self.size - 7)
        self._draw_finder(self.size - 7, 0)

        for index in range(8, self.size - 8):
            self._set_module(6, index, index % 2 == 0)
            self._set_module(index, 6, index % 2 == 0)

        for center_row in QR_ALIGNMENT_CENTERS[self.version]:
            for center_col in QR_ALIGNMENT_CENTERS[self.version]:
                if self.reserved[center_row][center_col]:
                    continue
                self._draw_alignment(center_row, center_col)

        self._set_module(self.size - 8, 8, True)
        for index in range(9):
            if index != 6:
                self._set_module(8, index, False)
                self._set_module(index, 8, False)
        for index in range(8):
            self._set_module(8, self.size - 1 - index, False)
            self._set_module(self.size - 1 - index, 8, False)

    def _draw_finder(self, row: int, col: int) -> None:
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                distance = max(abs(dx - 3), abs(dy - 3))
                self._set_module(row + dy, col + dx, distance <= 3 and distance != 2)

    def _draw_alignment(self, row: int, col: int) -> None:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                self._set_module(row + dy, col + dx, max(abs(dx), abs(dy)) != 1)

    def _draw_codewords(self, codewords: list[int]) -> None:
        bits = [(codeword >> index) & 1 == 1 for codeword in codewords for index in range(7, -1, -1)]
        bit_index = 0
        row = self.size - 1
        direction = -1
        col = self.size - 1

        while col > 0:
            if col == 6:
                col -= 1
            while 0 <= row < self.size:
                for offset in range(2):
                    current_col = col - offset
                    if not self.reserved[row][current_col]:
                        self.modules[row][current_col] = bit_index < len(bits) and bits[bit_index]
                        bit_index += 1
                row += direction
            direction *= -1
            row += direction
            col -= 2

    def _apply_mask(self) -> None:
        for row in range(self.size):
            for col in range(self.size):
                if not self.reserved[row][col] and (row + col) % 2 == 0:
                    self.modules[row][col] = not self.modules[row][col]

    def _draw_format_bits(self) -> None:
        value = self._bch_code(0b01000, 0x537, 10) ^ 0x5412
        for index in range(6):
            self._set_module(8, index, (value >> index) & 1 == 1)
        self._set_module(8, 7, (value >> 6) & 1 == 1)
        self._set_module(8, 8, (value >> 7) & 1 == 1)
        self._set_module(7, 8, (value >> 8) & 1 == 1)
        for index in range(9, 15):
            self._set_module(14 - index, 8, (value >> index) & 1 == 1)

        for index in range(8):
            self._set_module(self.size - 1 - index, 8, (value >> index) & 1 == 1)
        for index in range(8, 15):
            self._set_module(8, self.size - 15 + index, (value >> index) & 1 == 1)
        self._set_module(self.size - 8, 8, True)

    def _draw_version_bits(self) -> None:
        value = self._bch_code(self.version, 0x1F25, 12)
        for index in range(18):
            bit = (value >> index) & 1 == 1
            row = index // 3
            col = index % 3 + self.size - 11
            self._set_module(row, col, bit)
            self._set_module(col, row, bit)

    def _bch_code(self, value: int, polynomial: int, degree: int) -> int:
        result = value << degree
        while result.bit_length() >= polynomial.bit_length():
            result ^= polynomial << (result.bit_length() - polynomial.bit_length())
        return (value << degree) | result


class TicketPdfBuilder:
    cabin_class_labels = {
        "economy": "эконом",
        "business": "бизнес",
        "first": "первый класс",
    }

    def build(self, ticket: Ticket) -> bytes:
        lines = self._ticket_lines(ticket)
        qr_matrix = QrCodeBuilder(self._ticket_qr_text(ticket)).build()
        font_path = _find_font_path()
        if font_path:
            return self._build_unicode_pdf(lines, font_path, qr_matrix)
        return self._build_basic_pdf(lines, qr_matrix)

    def _ticket_lines(self, ticket: Ticket) -> list[str]:
        flight = ticket.flight
        passenger = ticket.passenger
        passenger_name = ""
        if passenger:
            passenger_name = f"{passenger.surname} {passenger.name} {passenger.patronymic or ''}".strip()

        route = "Не указано"
        if flight:
            route = (
                f"{flight.origin_city} ({flight.origin_code}) - "
                f"{flight.destination_city} ({flight.destination_code})"
            )

        ticket_number = self._format_ticket_number(ticket)
        cabin_class = self._format_cabin_class(ticket.cabin_class)

        return [
            "Paper Plane",
            "Электронный билет",
            f"Номер билета: {ticket_number}",
            f"Пассажир: {passenger_name or 'Не указано'}",
            f"Рейс: {flight.flight_number if flight else ticket.flight_id}",
            f"Авиакомпания: {flight.airline if flight else 'Не указано'}",
            f"Маршрут: {route}",
            f"Вылет: {flight.departure_date if flight else ''} {flight.departure_time if flight else ''}".strip(),
            f"Прилет: {flight.arrival_date if flight else ''} {flight.arrival_time if flight else ''}".strip(),
            f"Место: {ticket.seat_number or 'Не указано'}",
            f"Класс: {cabin_class}",
            f"Стоимость: {ticket.price if ticket.price is not None else 'Не указано'}",
            f"Дата оформления: {ticket.created_at or 'Не указано'}",
        ]

    def _format_ticket_number(self, ticket: Ticket) -> str:
        flight_number = ticket.flight.flight_number if ticket.flight else ""
        seat_number = ticket.seat_number or ""
        ticket_number = f"{flight_number} {seat_number}".strip()
        return ticket_number or ticket.id

    def _format_cabin_class(self, cabin_class: str | None) -> str:
        if not cabin_class:
            return "Не указано"
        return self.cabin_class_labels.get(cabin_class.lower(), cabin_class)

    def _ticket_qr_text(self, ticket: Ticket) -> str:
        flight = ticket.flight
        passenger = ticket.passenger
        passenger_name = ""
        if passenger:
            passenger_name = f"{passenger.surname} {passenger.name} {passenger.patronymic or ''}".strip()

        route = "Не указано"
        if flight:
            route = (
                f"{flight.origin_city} ({flight.origin_code}) - "
                f"{flight.destination_city} ({flight.destination_code})"
            )

        return "\n".join(
            [
                "Paper Plane",
                f"Билет: {self._format_ticket_number(ticket)}",
                f"Пассажир: {passenger_name or 'Не указано'}",
                f"Рейс: {flight.flight_number if flight else ticket.flight_id}",
                f"Маршрут: {route}",
                f"Вылет: {flight.departure_date if flight else ''} {flight.departure_time if flight else ''}".strip(),
                f"Прилет: {flight.arrival_date if flight else ''} {flight.arrival_time if flight else ''}".strip(),
                f"Место: {ticket.seat_number or 'Не указано'}",
                f"Класс: {self._format_cabin_class(ticket.cabin_class)}",
            ]
        )

    def _build_unicode_pdf(self, lines: list[str], font_path: Path, qr_matrix: list[list[bool]]) -> bytes:
        font_data = font_path.read_bytes()
        cmap = _load_cmap(font_data)
        if not cmap:
            return self._build_basic_pdf(lines, qr_matrix)

        used_chars = {ord(char) for line in lines for char in line if ord(char) <= 0xFFFF}
        max_cid = max(used_chars | {32})
        cid_to_gid = bytearray((max_cid + 1) * 2)
        for codepoint in used_chars:
            glyph_id = cmap.get(codepoint, 0)
            cid_to_gid[codepoint * 2 : codepoint * 2 + 2] = glyph_id.to_bytes(2, "big")

        text_commands = self._unicode_text_commands(lines, qr_matrix)
        to_unicode = self._to_unicode_cmap(used_chars)
        font_name = _sanitize_font_name(font_path.stem)

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            self._stream(text_commands),
            f"<< /Type /Font /Subtype /Type0 /BaseFont /{font_name} /Encoding /Identity-H /DescendantFonts [6 0 R] /ToUnicode 10 0 R >>".encode(
                "ascii"
            ),
            f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /{font_name} /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor 7 0 R /DW 600 /CIDToGIDMap 9 0 R >>".encode(
                "ascii"
            ),
            b"<< /Type /FontDescriptor /FontName /"
            + font_name.encode("ascii")
            + b" /Flags 32 /FontBBox [0 -250 1200 1000] /ItalicAngle 0 /Ascent 900 /Descent -250 /CapHeight 700 /StemV 80 /FontFile2 8 0 R >>",
            self._stream(font_data),
            self._stream(bytes(cid_to_gid)),
            self._stream(to_unicode),
        ]

        return self._assemble(objects)

    def _build_basic_pdf(self, lines: list[str], qr_matrix: list[list[bool]]) -> bytes:
        content = "\n".join(
            [
                "BT",
                "/F1 18 Tf",
                "50 790 Td",
                *self._basic_text_lines(lines),
                "ET",
                *self._qr_draw_commands(qr_matrix),
            ]
        ).encode("latin-1", errors="replace")

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            self._stream(content),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]

        return self._assemble(objects)

    def _unicode_text_commands(self, lines: list[str], qr_matrix: list[list[bool]]) -> bytes:
        commands = ["BT", "/F1 18 Tf", "50 790 Td"]
        for index, line in enumerate(lines):
            font_size = 22 if index == 0 else 18 if index == 1 else 12
            line_gap = 30 if index < 2 else 22
            if index > 0:
                commands.append(f"0 -{line_gap} Td")
            commands.append(f"/F1 {font_size} Tf")
            commands.append(f"<{line.encode('utf-16-be').hex().upper()}> Tj")
        commands.append("ET")
        commands.extend(self._qr_draw_commands(qr_matrix))
        return "\n".join(commands).encode("ascii")

    def _qr_draw_commands(self, matrix: list[list[bool]]) -> list[str]:
        module_count = len(matrix)
        qr_size = 170
        module_size = qr_size / module_count
        origin_x = 212.5
        origin_y = 70
        commands = [
            "q",
            "1 1 1 rg",
            f"{origin_x - 8:.2f} {origin_y - 8:.2f} {qr_size + 16:.2f} {qr_size + 16:.2f} re f",
            "0 0 0 rg",
        ]

        for row, values in enumerate(matrix):
            for col, is_dark in enumerate(values):
                if not is_dark:
                    continue
                x = origin_x + col * module_size
                y = origin_y + (module_count - 1 - row) * module_size
                commands.append(f"{x:.2f} {y:.2f} {module_size + 0.02:.2f} {module_size + 0.02:.2f} re f")

        commands.append("Q")
        return commands

    def _basic_text_lines(self, lines: Iterable[str]) -> list[str]:
        commands: list[str] = []
        for index, line in enumerate(lines):
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            safe_line = safe_line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if index > 0:
                commands.append("0 -24 Td")
            commands.append(f"({safe_line}) Tj")
        return commands

    def _to_unicode_cmap(self, used_chars: set[int]) -> bytes:
        mappings = "\n".join(f"<{codepoint:04X}> <{codepoint:04X}>" for codepoint in sorted(used_chars))
        return f"""/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /TicketUnicode def
/CMapType 2 def
1 begincodespacerange
<0000> <FFFF>
endcodespacerange
{len(used_chars)} beginbfchar
{mappings}
endbfchar
endcmap
CMapName currentdict /CMap defineresource pop
end
end""".encode("ascii")

    def _stream(self, content: bytes) -> bytes:
        return b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"

    def _assemble(self, objects: list[bytes]) -> bytes:
        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]

        for index, content in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{index} 0 obj\n".encode("ascii"))
            output.extend(content)
            output.extend(b"\nendobj\n")

        xref_offset = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        output.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
                "ascii"
            )
        )
        return bytes(output)
