#!/usr/bin/env python3

import sys

#
#  Generate X10 RF command in Flipper .sub format
#
# Peter Shipley github.com/evilpete
#
# From pkg https://github.com/evilpete/flipper_toolbox
#

# Usage;
#      ./subghz_x10.py <dst_node_addr><src_node_addr> [On|Off]
# Example:
#      ./subghz_x10.py B10 on
#
#      ./subghz_x10.py B10 Dim Dim Dim
#
# or
#
# Generate a ALL-OFF / ALL-ON for all housecodes
#      ./subghz_x10.py -b
#

# https://www.laser.com/dhouston/rf.html


_debug = 0

# Freq is 310MHz in North America
# 433.92MHz in Europe

rf_freq = 310000000

houseCodes = {
    "A": 0x60,     # 01100000
    "B": 0x70,     # 01110000
    "C": 0x40,     # 01000000
    "D": 0x50,     # 01010000
    "E": 0x80,     # 10000000
    "F": 0x90,     # 10010000
    "G": 0xA0,     # 10100000
    "H": 0xB0,     # 10110000
    "I": 0xE0,     # 11100000
    "J": 0xF0,     # 11110000
    "K": 0xC0,     # 11000000
    "L": 0xD0,     # 11010000
    "M": 0x00,     # 00000000
    "N": 0x10,     # 00010000
    "O": 0x20,     # 00100000
    "P": 0x30,     # 00110000
}

unit_code = {
    0: 0x0000,   # 00000000 00000000
    1: 0x0000,   # 00000000 00000000
    2: 0x0010,   # 00000000 00010000
    3: 0x0008,   # 00000000 00001000
    4: 0x0018,   # 00000000 00011000
    5: 0x0040,   # 00000000 01000000
    6: 0x0050,   # 00000000 01010000
    7: 0x0048,   # 00000000 01001000
    8: 0x0058,   # 00000000 01011000
    9: 0x0400,   # 00000100 00000000
    10: 0x0410,  # 00000100 00010000
    11: 0x0408,  # 00000100 00001000
    12: 0x0400,  # 00000100 00000000
    13: 0x0440,  # 00000100 01000000
    14: 0x0450,  # 00000100 01010000
    15: 0x0448,  # 00000100 01001000
    16: 0x0458,  # 00000100 01011000
}

cmd_code = {
    "ON": 0x00,           # 00000000
    "OFF": 0x20,          # 00100000
    "BRT": 0x88,          # 10001000
    "DIM": 0x98,          # 10011000
    "ALL-OFF": 0x80,      # 10000000
    "ALL-ON": 0x91,       # 10010001
    "ALL-LTS-OFF": 0x84,  # 10000100
    "ALL-LTS-ON": 0x94,   # 10010100
    # All lights on   0x90    10010000
    # All lights off  0xA0    10100000
    # All units off   0x80    10000000
}


# takes args for housecode unit and x10 command
# and returns a string representing bits for X10 RF command
#
# Args: A 10 ON
# returns 01100100100110110001000011101111
#
def gen_x10(targ_house, targ_unit, targ_cmd):

    res = [0, 0]

    if _debug:
        print(targ_house, targ_unit, targ_cmd, file=sys.stderr)

    res[0] = houseCodes[targ_house]

    if targ_unit and not cmd_code[targ_cmd] & 0x80:
        res[0] |= (unit_code[targ_unit] >> 8) & 0xff
        res[1] |= unit_code[targ_unit] & 0xff

    res[1] |= cmd_code[targ_cmd] & 0xff

    if _debug:
        print(f"{res[0]:08b} {res[0]^0xff:08b} {res[1]:08b} {res[1]^0xff:08b}", file=sys.stderr)

    return f"{res[0]:08b}{res[0]^0xff:08b}{res[1]:08b}{res[1]^0xff:08b}"


# Takes a string representing binary bits
# and generates Flipper SubGhz RAW File data
def gen_subfile(pkt_bits, note="x10 command", repeat=1):

    datalines = []
    for bits in pkt_bits:

        data = [9000, -4500]

        for bit in bits:
            if bit == '1':
                data.extend((562, -1688))
            else:
                data.extend((562, -563))

        data.extend((562, -40000))

        for i in range(0, len(data), 510):
            batch = map(str, data[i:i + 510])
            datalines.append(f'RAW_Data: {" ".join(batch)}')

    bb = pkt_bits[0]
    bin_dat = ' '.join([bb[i:i + 8] for i in range(0, len(bb), 8)])

    hdr = f"""Filetype: Flipper SubGhz RAW File
Version: 1
# {note} {bin_dat}
# Generated with subghz_x10.py https://github.com/evilpete/flipper_toolbox
Frequency: {rf_freq}
Preset: FuriHalSubGhzPresetOok650Async
Protocol: RAW
"""

    res = hdr

    res += '\n'.join(datalines) + '\n'
    if repeat > 1:
        for i in range(0, repeat):
            res += '\n'.join(datalines) + '\n'

    return res


#
# Generates fikes for the commands
# ALL-ON  ALL-OFF ALL-LTS-ON ALL-LTS-OFF
# for for every housecode
#
def gen_brute_all():

    cmd_off = []
    cmd_on = []
    cmd_lts_off = []
    cmd_lts_on = []
    for h in houseCodes:
        xoff = gen_x10(h, "", "ALL-OFF")
        cmd_off.append(xoff)  # repeat 3 times
        cmd_off.append(xoff)
        cmd_off.append(xoff)

        xon = gen_x10(h, "", "ALL-ON")
        cmd_on.append(xon)  # repeat 3 times
        cmd_on.append(xon)
        cmd_on.append(xon)

        xloff = gen_x10(h, "", "ALL-LTS-OFF")
        cmd_lts_off.append(xloff)  # repeat 3 times
        cmd_lts_off.append(xloff)
        cmd_lts_off.append(xloff)

        xlon = gen_x10(h, "", "ALL-LTS-ON")
        cmd_lts_on.append(xlon)  # repeat 3 times
        cmd_lts_on.append(xlon)
        cmd_lts_on.append(xlon)

    if _debug > 2:
        print("cmd_off", cmd_off)

    filenam = "X10_All-OFF"
    xdata = gen_subfile(cmd_off, note=filenam, repeat=1)
    with open(filenam + ".sub", "w", encoding="utf-8") as fdd:
        print(xdata, file=fdd)

    if _debug > 2:
        print("cmd_on", cmd_on)

    filenam = "X10_All-ON"
    xdata = gen_subfile(cmd_on, note=filenam, repeat=1)
    with open(filenam + ".sub", "w", encoding="utf-8") as fdd:
        print(xdata, file=fdd)

    filenam = "X10_All-LIGHTS-OFF"
    xdata = gen_subfile(cmd_lts_off, note=filenam, repeat=1)
    with open(filenam + ".sub", "w", encoding="utf-8") as fdd:
        print(xdata, file=fdd)

    filenam = "X10_All-LIGHTS-ON"
    xdata = gen_subfile(cmd_lts_on, note=filenam, repeat=1)
    with open(filenam + ".sub", "w", encoding="utf-8") as fdd:
        print(xdata, file=fdd)


if __name__ == '__main__':

    args = sys.argv[1:]

    options = "Valid options:\n" + \
        "\tsubghz_x10.py <housecode>[unit] <command>\n" + \
        "or\n" + \
        "\tsubghz_x10.py -b"

    if args and args[0][0] == '-':
        if args[0] == '-b':
            gen_brute_all()
            sys.exit()
        else:
            print("unlknown arg {args[0]}")
            print(options)

    if len(args) < 2:
        print("requires 2 or more args")
        sys.exit()

    node_targ = args.pop(0).upper()
    node_house = node_targ[0]
    node_unit = node_targ[1:]
    node_cmd = args.pop(0).upper()

    if node_cmd in cmd_code:
        pass
    elif node_cmd == "BRIGHT":
        node_cmd = "BRT"
    elif node_cmd in ["ALL_OFF", "ALLOFF"]:
        node_cmd = "ALL-OFF"
    elif node_cmd in ["ALL_ON", "ALLON"]:
        node_cmd = "ALL-ON"
    else:
        print("Unknown command code:", node_cmd)
        print("\tValid command are:", " ".join(cmd_code))
        print(options)
        sys.exit()

    if not (node_house and node_house in houseCodes):
        print("Unknown House code:", node_house)
        sys.exit()

    if not node_unit:
        node_unit = 0
    elif node_unit.isdigit():
        node_unit = int(node_unit)
    else:
        print("Invalid House unit:", node_unit)
        sys.exit()

    if int(node_unit) > 16:
        print("Invalid House unit:", node_house)
        print("\tValid values are 1 -> 16")
        sys.exit()

#     rr = gen_x10(node_house, node_unit, node_cmd)
#     pkt_data = f"{rr[0]:08b}{rr[0]^0xff:08b}{rr[1]:08b}{rr[1]^0xff:08b}"

    pkt_data = []
    if node_cmd in ["ON", "OFF"]:
        pkt_data.append(gen_x10(node_house, node_unit, node_cmd))
        pkt_data += pkt_data * 3
    elif node_cmd in ['BRT', 'DIM']:
        if node_unit:
            pkt_data.append(gen_x10(node_house, node_unit, "ON"))
            pkt_data += pkt_data * 2
        pkt_data.append(gen_x10(node_house, None, node_cmd))
    elif node_cmd.startswith("ALL"):
        node_unit = None
        pkt_data.append(gen_x10(node_house, None, node_cmd))
        pkt_data += pkt_data * 3
    else:  # should never get here..
        print("Unknown command code:", node_cmd)

    if _debug:
        print(node_house, node_unit, node_cmd, file=sys.stderr)

    while args:
        node_cmd = args.pop(0).upper()
        if node_cmd in ['BRT', 'DIM']:
            pkt_data.append(gen_x10(node_house, None, node_cmd))
        else:
            print("Skipping unknown command code:", node_cmd)

    if _debug:
        print("pkt_data", pkt_data, file=sys.stderr)

    if node_unit:
        filen = f"{node_house}{node_unit:02d}_{node_cmd}"
    else:
        filen = f"{node_house}_{node_cmd}"

    fdata = gen_subfile(pkt_data, note=filen)

    with open(filen + ".sub", "w", encoding="utf-8") as fd:
        print(fdata, file=fd)

    sys.exit()
