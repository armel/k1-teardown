# Pinout

<img width="1512" height="1214" alt="SWD" src="https://github.com/user-attachments/assets/66622e95-c0b1-4794-9f59-1c7b598117a5" />

# Backup K1 Internal Flash (PY32F071) using OpenOCD

This command uses OpenOCD with an ST-Link to dump 128 KB of internal flash from a K1 (PY32F071). It first sets the Puya CPUTAPID (0x0bc11477), connects via the STM32F0-compatible target, runs at 1 MHz, halts the MCU, then saves memory from 0x08000000 for 0x00020000 bytes into [K1_PY32F071.bin](https://github.com/armel/k1-teardown/blob/main/openocd/K1_PY32F071.bin), and shuts down:

```
openocd \
  -f interface/stlink.cfg \
  -c "set CPUTAPID 0x0bc11477" \
  -f target/stm32f0x.cfg \
  -c "adapter speed 1000" \
  -c "init; reset halt; dump_image K1_PY32F071.bin 0x08000000 0x00020000; shutdown"
```

## Breakdown

- `-f interface/stlink.cfg` — select ST-Link interface.
- `-c "set CPUTAPID 0x0bc11477"` — override TAP ID for Puya PY32.
- `-f target/stm32f0x.cfg` — use STM32F0-like target (compatible).
- `-c "adapter speed 1000"` — 1 MHz SWD.
- `-c "init; reset halt; dump_image K1_PY32F071.bin 0x08000000 0x00020000; shutdown"` — init, halt MCU, dump and exit.

# View binary contents as HEX + ASCII (paged)

This command shows a canonical hex dump of K1_PY32F071.bin (offsets, hex bytes, and ASCII on the right) and pipes it into a pager so you can scroll through the output.

`hexdump -C K1_PY32F071.bin | more`

Here is the output produced:

```
00000000  80 25 00 20 d5 00 00 08  dd 00 00 08 df 00 00 08  |.%. ............|
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000020  00 00 00 00 00 00 00 00  00 00 00 00 e1 00 00 08  |................|
00000030  00 00 00 00 00 00 00 00  e3 00 00 08 e5 00 00 08  |................|
00000040  e7 00 00 08 dd 0d 00 08  e7 00 00 08 e7 00 00 08  |................|
00000050  e7 00 00 08 e7 00 00 08  e7 00 00 08 e7 00 00 08  |................|
*
000000b0  e7 00 00 08 e7 00 00 08  00 00 00 00 0d 11 00 08  |................|
000000c0  03 48 85 46 00 f0 6e f8  00 48 00 47 29 13 00 08  |.H.F..n..H.G)...|
000000d0  80 25 00 20 04 48 80 47  04 48 00 47 fe e7 fe e7  |.%. .H.G.H.G....|
000000e0  fe e7 fe e7 fe e7 fe e7  85 0f 00 08 c1 00 00 08  |................|
000000f0  30 b5 0b 46 01 46 00 20  20 22 01 24 09 e0 0d 46  |0..F.F.  ".$...F|
00000100  d5 40 9d 42 05 d3 1d 46  95 40 49 1b 25 46 95 40  |.@.B...F.@I.%F.@|
00000110  40 19 15 46 52 1e 00 2d  f1 dc 30 bd 03 46 0b 43  |@..FR..-..0..F.C|
00000120  9b 07 03 d0 09 e0 08 c9  12 1f 08 c0 04 2a fa d2  |.............*..|
00000130  03 e0 0b 78 03 70 40 1c  49 1c 52 1e f9 d2 70 47  |...x.p@.I.R...pG|
00000140  d2 b2 01 e0 02 70 40 1c  49 1e fb d2 70 47 00 22  |.....p@.I...pG."|
00000150  f6 e7 10 b5 13 46 0a 46  04 46 19 46 ff f7 f0 ff  |.....F.F.F.F....|
00000160  20 46 10 bd 30 b5 04 46  00 20 03 46 00 e0 5b 1c  | F..0..F. .F..[.|
00000170  93 42 03 d2 e0 5c cd 5c  40 1b f8 d0 30 bd 03 21  |.B...\.\@...0..!|
00000180  00 1d 40 1e 03 78 12 02  1a 43 49 1e f9 d5 10 46  |..@..x...CI....F|
00000190  70 47 03 46 03 22 08 70  00 0a 49 1c 52 1e fa d5  |pG.F.".p..I.R...|
000001a0  18 46 70 47 06 4c 01 25  06 4e 05 e0 e3 68 07 cc  |.FpG.L.%.N...h..|
000001b0  2b 43 0c 3c 98 47 10 34  b4 42 f7 d3 ff f7 84 ff  |+C.<.G.4.B......|
--More--
```

# Disassemble a raw binary as ARM/Thumb (paged)

This command disassembles the raw binary PY32F071.bin using arm-none-eabi-objdump, forcing Thumb decoding and standard register names, and displays it page by page:

```
arm-none-eabi-objdump \
  -D \
  -b binary \
  -m arm \
  -M force-thumb,reg-names-std \
  --adjust-vma=0x08000000 \
  K1_PY32F071.bin | more
```

Here is the output produced:

```
K1_PY32F071.bin:     file format binary

Disassembly of section .data:

08000000 <.data>:
 8000000: 2580        movs  r5, #128  ; 0x80
 8000002: 2000        movs  r0, #0
 8000004: 00d5        lsls  r5, r2, #3
 8000006: 0800        lsrs  r0, r0, #32
 8000008: 00dd        lsls  r5, r3, #3
 800000a: 0800        lsrs  r0, r0, #32
 800000c: 00df        lsls  r7, r3, #3
 800000e: 0800        lsrs  r0, r0, #32
  ...
 800002c: 00e1        lsls  r1, r4, #3
 800002e: 0800        lsrs  r0, r0, #32
  ...
 8000038: 00e3        lsls  r3, r4, #3
 800003a: 0800        lsrs  r0, r0, #32
 800003c: 00e5        lsls  r5, r4, #3
 800003e: 0800        lsrs  r0, r0, #32
 8000040: 00e7        lsls  r7, r4, #3
--More--
```

## Breakdown

- `-D` — disassemble the entire file.
- `-b binary` — treat input as a raw binary blob (no headers).
- `-m arm` — target architecture family is ARM.
- `-M force-thumb,reg-names-std` — decode as Thumb instructions; use standard reg names (r0–r15).
- `--adjust-vma=0x08000000` — sets the base address for displayed offsets. 
