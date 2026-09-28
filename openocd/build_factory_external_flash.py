#!/usr/bin/env python3
"""Build the reconstructed UV-K1 and UV-K5 V3 factory external images."""

from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path


FLASH_SIZE = 0x200000
CONFIG_END = 0x010000
CALIBRATION_START = 0x010000
CALIBRATION_END = 0x011000
LOGO_START = 0x011000
LOGO_SECTOR_SIZE = 0x1000
LOGO_WIDTH = 128
LOGO_HEIGHT = 64
LOGO_BITMAP_SIZE = LOGO_WIDTH * LOGO_HEIGHT // 8
LOGO_HEADER = struct.pack("<IHH", 0x9ABC5A5A, LOGO_BITMAP_SIZE, 0)
AUDIO_START = 0x100000
AUDIO_END = 0x197000
BOOT_MESSAGE_LINE2_START = 0x7030
BOOT_MESSAGE_LINE_SIZE = 16

SPI_DUMP_SHA256 = "3fafeea9f0ebc2ee20899100722bcac04e864d15c64626d7aaf5d5fcc93bb91a"
SPI_CONFIG_SHA256 = "43b9b51e73bc793cfa921806d2a9d68cab3c4d7fafb1f3e555ee2d0bf92f6e43"
PRISTINE_DUMP_SHA256 = "05a8b92247e8c3ee69a74f236f70f325c7af7f7bc28eb308fee418fd452582d4"
LOGO_PNG_SHA256 = "a5b4277efb5f78986bcdb22e4132b62b68aee5f4637a1798164ecc230a935848"

ROOT = Path(__file__).resolve().parent
SPI_DUMP = ROOT / "K1_SPI_Flash.bin"
PRISTINE_DUMP = ROOT / "K1_External_Flash_Pristine.bin"
LOGO_PNG = ROOT / "quansheng.stock.logo.png"
K1_OUTPUT = ROOT / "K1_External_Flash_Factory_Reconstructed.bin"
K5V3_OUTPUT = ROOT / "K5V3_External_Flash_Factory_Reconstructed.bin"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_verified(path: Path, expected_hash: str) -> bytes:
    data = path.read_bytes()
    if len(data) != FLASH_SIZE:
        raise ValueError(f"{path.name}: expected {FLASH_SIZE} bytes, got {len(data)}")
    actual_hash = sha256(data)
    if actual_hash != expected_hash:
        raise ValueError(f"{path.name}: unexpected SHA-256 {actual_hash}")
    return data


def paeth_predictor(left: int, above: int, upper_left: int) -> int:
    prediction = left + above - upper_left
    left_distance = abs(prediction - left)
    above_distance = abs(prediction - above)
    upper_left_distance = abs(prediction - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def decode_logo_png(data: bytes) -> bytes:
    if sha256(data) != LOGO_PNG_SHA256:
        raise ValueError(f"{LOGO_PNG.name}: unexpected SHA-256 {sha256(data)}")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{LOGO_PNG.name}: invalid PNG signature")

    position = 8
    idat = bytearray()
    image_header = None
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError(f"{LOGO_PNG.name}: truncated PNG chunk")
        chunk_length = struct.unpack(">I", data[position:position + 4])[0]
        chunk_type = data[position + 4:position + 8]
        chunk_start = position + 8
        chunk_end = chunk_start + chunk_length
        if chunk_end + 4 > len(data):
            raise ValueError(f"{LOGO_PNG.name}: truncated PNG payload")
        chunk_data = data[chunk_start:chunk_end]
        expected_crc = struct.unpack(">I", data[chunk_end:chunk_end + 4])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"{LOGO_PNG.name}: invalid PNG chunk CRC")
        if chunk_type == b"IHDR":
            image_header = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
        position = chunk_end + 4

    expected_header = (LOGO_WIDTH, LOGO_HEIGHT, 8, 6, 0, 0, 0)
    if image_header != expected_header:
        raise ValueError(f"{LOGO_PNG.name}: expected a 128x64 RGBA8 non-interlaced PNG")

    bytes_per_pixel = 4
    stride = LOGO_WIDTH * bytes_per_pixel
    filtered = zlib.decompress(bytes(idat))
    if len(filtered) != LOGO_HEIGHT * (stride + 1):
        raise ValueError(f"{LOGO_PNG.name}: unexpected decompressed size")

    pixels = bytearray(LOGO_HEIGHT * stride)
    source_position = 0
    for y in range(LOGO_HEIGHT):
        filter_type = filtered[source_position]
        source_position += 1
        row_start = y * stride
        for x in range(stride):
            value = filtered[source_position]
            source_position += 1
            left = pixels[row_start + x - bytes_per_pixel] if x >= bytes_per_pixel else 0
            above = pixels[row_start - stride + x] if y > 0 else 0
            upper_left = (
                pixels[row_start - stride + x - bytes_per_pixel]
                if y > 0 and x >= bytes_per_pixel
                else 0
            )
            if filter_type == 0:
                reconstructed = value
            elif filter_type == 1:
                reconstructed = value + left
            elif filter_type == 2:
                reconstructed = value + above
            elif filter_type == 3:
                reconstructed = value + ((left + above) // 2)
            elif filter_type == 4:
                reconstructed = value + paeth_predictor(left, above, upper_left)
            else:
                raise ValueError(f"{LOGO_PNG.name}: unsupported PNG filter {filter_type}")
            pixels[row_start + x] = reconstructed & 0xFF
    return bytes(pixels)


def build_logo_sector(png_data: bytes) -> bytes:
    pixels = decode_logo_png(png_data)
    bitmap = bytearray(LOGO_BITMAP_SIZE)
    for page in range(LOGO_HEIGHT // 8):
        for x in range(LOGO_WIDTH):
            value = 0
            for bit in range(8):
                y = page * 8 + bit
                pixel_start = (y * LOGO_WIDTH + x) * 4
                red, green, blue, alpha = pixels[pixel_start:pixel_start + 4]
                red = (red * alpha + 255 * (255 - alpha) + 127) // 255
                green = (green * alpha + 255 * (255 - alpha) + 127) // 255
                blue = (blue * alpha + 255 * (255 - alpha) + 127) // 255
                if 299 * red + 587 * green + 114 * blue < 128000:
                    value |= 1 << bit
            bitmap[page * LOGO_WIDTH + x] = value

    sector = bytearray(b"\xff" * LOGO_SECTOR_SIZE)
    sector[:len(LOGO_HEADER)] = LOGO_HEADER
    sector[len(LOGO_HEADER):len(LOGO_HEADER) + LOGO_BITMAP_SIZE] = bitmap
    return bytes(sector)


def main() -> None:
    spi_dump = read_verified(SPI_DUMP, SPI_DUMP_SHA256)
    pristine_dump = read_verified(PRISTINE_DUMP, PRISTINE_DUMP_SHA256)

    config = spi_dump[:CONFIG_END]
    if sha256(config) != SPI_CONFIG_SHA256:
        raise ValueError("K1_SPI_Flash.bin: first 64 KiB block is not the expected factory configuration")

    image = bytearray(b"\xff" * FLASH_SIZE)
    image[:CONFIG_END] = config
    image[LOGO_START:LOGO_START + LOGO_SECTOR_SIZE] = build_logo_sector(LOGO_PNG.read_bytes())
    image[AUDIO_START:AUDIO_END] = pristine_dump[AUDIO_START:AUDIO_END]

    # The calibration sector intentionally remains erased in the artifact.
    # UV Studio and the firmware both skip/protect it during restoration.
    assert all(value == 0xFF for value in image[CALIBRATION_START:CALIBRATION_END])

    k1_image = bytes(image)
    K1_OUTPUT.write_bytes(k1_image)
    print(f"{K1_OUTPUT.name}: {len(k1_image)} bytes")
    print(f"SHA-256: {sha256(k1_image)}")

    # The factory boot-message line 2 is the only model-specific byte range in
    # the reconstructed external image. Keep its 16-byte, null-padded layout.
    line_end = BOOT_MESSAGE_LINE2_START + BOOT_MESSAGE_LINE_SIZE
    if image[BOOT_MESSAGE_LINE2_START:line_end].rstrip(b"\0") != b"UV-K1":
        raise ValueError("unexpected factory boot-message line 2")
    image[BOOT_MESSAGE_LINE2_START:line_end] = b"UV-K5".ljust(BOOT_MESSAGE_LINE_SIZE, b"\0")

    k5v3_image = bytes(image)
    K5V3_OUTPUT.write_bytes(k5v3_image)
    print(f"{K5V3_OUTPUT.name}: {len(k5v3_image)} bytes")
    print(f"SHA-256: {sha256(k5v3_image)}")


if __name__ == "__main__":
    main()
