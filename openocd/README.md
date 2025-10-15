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
