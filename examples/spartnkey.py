"""
spartnkey.py

Example script illustrating how to format current and next
SPARTN keys (e.g. from u-blox PointPerfect service) as a
UBX RXM-SPARTN-KEY message and upload this to a ZED-F9P receiver.

You can find the current and next keys in Thingstream here:

https://thingstream.io/
Location Services \ Location Things \ Thing Details \ Credentials
L-Band + IP Dynamic Keys

Created on 23 Jan 2023

:author: semuadmin
:copyright: SEMU Consulting © 2023
:license: BSD 3-Clause
"""

import sys
from datetime import datetime
from serial import Serial, SerialException
from pyubx2 import UBXMessage, UBXReader, SET, U1, U2, U4, val2bytes

GPSEPOCH0 = datetime(1980, 1, 6)


def get_gpswnotow(dat: datetime) -> tuple:
    """
    Get GPS Week number and Time of Week for midnight on given date.
    GPS Epoch 0 = 6th Jan 1980
    """

    wno = int((dat - GPSEPOCH0).days / 7)
    tow = ((dat.weekday() + 1) % 7) * 86400
    return wno, tow


keys = []
keylens = []
wnos = []
tows = []
print(
    "This utility accepts one or two SPARTN keys and their associated Valid From dates",
    "\nand formats a UBX RXM-SPARTN-KEY message which can be sent to a compatible",
    "\nreceiver e.g. XED-F9P.\n",
)
print("How many SPARTN keys do you want to upload (1 or 2)? (2): ", end="")
val = input() or "2"
numkeys = int(val)
for i in range(numkeys):
    LBL = "second" if i + 1 == 2 else "first"
    print(f"Enter {LBL} key as string (normally 16 chars): ", end="")
    val = input() or "dummyspartnkey01"
    keylens.append(val2bytes(len(val), U1))
    keys.append(bytes(val, "utf-8"))
    print(f"Enter {LBL} valid from date in format YYYYMMDD (Today): ", end="")
    val = input() or ""
    dat = (
        datetime.now()
        if val == ""
        else datetime(int(val[0:4]), int(val[4:6]), int(val[6:8]))
    )
    wno, tow = get_gpswnotow(dat)
    wnos.append(val2bytes(wno, U2))
    tows.append(val2bytes(tow, U4))

version = val2bytes(1, U1)
numKeys = val2bytes(numkeys, U1)
RESERVED0 = b"\x00\x00"
RESERVED1 = b"\x00"

payload = version + numKeys + RESERVED0
for i in range(numkeys):
    payload += RESERVED1 + keylens[i] + wnos[i] + tows[i]
for i in range(numkeys):
    payload += keys[i]

print("\nFormatting UBX RXM-SPARTN-KEY message...\n")
msg = UBXMessage("RXM", "RXM-SPARTN-KEY", SET, payload=payload)
print(msg)
print("\n")
print(msg.serialize())
msg1 = UBXReader.parse(msg.serialize())
CHECKED = str(msg) == str(msg1)
print(f"\nCheck message formatted correctly: {'PASS' if CHECKED else 'FAIL'}")

if not CHECKED:
    sys.exit()

print("Do you want to send this message to the receiver? (y/n) ", end="")
val = input() or "n"

if val == "y":
    print("Enter receiver port: (dev/ttyACM1) ", end="")
    val = input() or "/dev/ttyACM1"
    port = val
    print("Enter receiver baud rate: (38400) ", end="")
    val = input() or "38400"
    baudrate = int(val)
    print("Enter receiver timeout: (3) ", end="")
    val = input() or "3"
    timeout = int(val)

    print(f"Sending message to {port}@{baudrate}...\n")
    try:
        with Serial(port, baudrate, timeout=timeout) as serial:
            serial.write(msg.serialize())
            print("Message sent")
    except (SerialException) as err:
        print(f"\nError sending message! {err}")

print(
    "\nTo make this message a PyGPSClient user preset, the following",
    "\nstring can be cut-and-pasted into PyGPSClient's ubxpresets file:\n",
)
print(f"Send RXM-SPARTN-KEY, RXM, RXM-SPARTN-KEY, {msg.payload.hex()}, 1")
