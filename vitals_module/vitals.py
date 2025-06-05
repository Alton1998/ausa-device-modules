import asyncio
from bleak import BleakScanner

async def main():
    devices = await BleakScanner.discover()
    print("Alton")
    for d in devices:
        print("Alton")
        print(d.name)
        print(d.details)

asyncio.run(main())