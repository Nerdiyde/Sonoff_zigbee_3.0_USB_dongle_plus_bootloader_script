#!/usr/bin/env python
# -*-coding:UTF-8-*-
import logging
# import loggingCfg
import time
import os
import sys
from threading import Thread
import queue
import serial                   # to install this dependency execute: pip install pyserial
import datetime                 # to install this dependency execute: pip install gevent
import struct
import serial.tools.list_ports
import asyncio
import gevent
import re

# Test Data
znp_edScanReq = [0xfe, 5, 0x23, 0x1f, 0x00, 0xf8, 0xff, 0x07, 0x03]

# display setting
DISPLAY_FORMATE_CFG_HEX_BIT = 1
DISPLAY_FORMATE_CFG_STR_BIT = 2
DISPLAY_FORMATE_CFG = DISPLAY_FORMATE_CFG_HEX_BIT | DISPLAY_FORMATE_CFG_STR_BIT

# Set output format
# logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
# datefmt='%d-%m-%Y:%H:%M:%S')
logging.basicConfig(format='%(message)s', datefmt='%d-%m-%Y:%H:%M:%S')

# Set the name of the log output device, you can configure multiple different log output devices in the project
# Set log printing level
logging.getLogger(__name__).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


def uart_refresh():
    """
    Serial port detection
    """
    # Detect all existing serial ports and store the information in the list
    i = 0

    port_list = list(serial.tools.list_ports.comports())
    for port in port_list:
        if port:
            i += 1
            uart_list.append(port)
            print(uart_list[i])

    if len(uart_list) is None:
        return "uart_list = NULL"


# Save log data to file
handler = logging.FileHandler('%s.txt' % time.strftime("%Y-%m-%d %H_%M"))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def sendDataToSerialPort(sp, data):
    # data.append(fcsCheck(data,1))

    binaryData = struct.pack('B' * len(data), *data)
    wrt = sp.write(binaryData)
    # data.pop()
    # logger.debug(">>>>>>>>>>>>>>>>>>>>>>>>>>>>{}", decTohexStr(data))


def sendStrToSerialPort(sp, data):
    wrt = sp.write(data.encode("utf-8"))


def decTohexStr(argv):
    result = ''
    hLen = len(argv)
    for i in range(hLen):
        if (argv[i] <= 15):
            result += ' 0%x' % argv[i]
        else:
            result += ' %x' % argv[i]

    return result


def start_evt_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def readDataFromSerial(sp):
    print('Read')

    while True:
        await asyncio.sleep(0.2)

        try:
            # logger.debug("+++++++++++++++")

            if sp.isOpen() and sp.inWaiting():
                tmpLen = sp.inWaiting()
                recv = sp.read(tmpLen)
                q.put(recv, block=True, timeout=5)

                # recv = sp.read(1)

                # head = struct.unpack('B',recv)[0];

                logger.debug(" 0x%x " % (head))

            # logger.debug("---------------")
        except:
            logger.error('serial port is recv excp!!!!')

        # await asyncio.sleep(1)
        logger.debug('R Done after s')


async def writeDataFromSerial(sp):
    print('Write')
    cnt = 0

    while True:
        cnt = cnt + 1
        print("write %d" % (cnt))
        if sp.isOpen():
            if not q.empty():
                sendData = q.get()
                sendDataToSerialPort(sp, list(sendData))

            # sendDataToSerialPort(sp, list(znp_edScanReq) )
        await asyncio.sleep(0.5)
        print('W Done after s')


async def create_task(event_loop):
    i = 0
    while i < 3:
        # A task is generated every second and submitted to the loop in the thread with event_loop as a parameter
        asyncio.run_coroutine_threadsafe(production(i), event_loop)
        await asyncio.sleep(1)
        i += 1


async def production(i):
    while True:
        logger.debug("%d coroutine" % (i))
        await asyncio.sleep(2)


def splitUartRxStarWithWrap(uartRxStr):
    mRxDataStr = uartRxStr.replace(r'\r', '').replace(r'\n', 'nnnnnn')
    dataStrList = re.split(r'n{6,30}', mRxDataStr)
    # print(dataStrList)
    if dataStrList[-1] == '':
        del dataStrList[-1]
    return dataStrList


def uartRx(sp, q):
    print('Read processing...')

    while True:
        try:
            # logger.debug("+++++++++++++++")
            tmpLen = sp.inWaiting()
            # logger.debug(tmpLen)

            if sp.isOpen() and tmpLen != 0:
                # Data bits read from serial buffer bytes type
                recv = sp.read(tmpLen)
                print("recv sp read tmplen ", recv)
                # cmdData = struct.unpack('B'*(tmpLen),recv)
                # cmdData = list(cmdData)

                print(type(recv))
                # logger.debug("%s [RX] : %s"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), decTohexStr(cmdData)))
                # logger.debug("%s [RX] : %s"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), str(recv)))

                # tmpList = splitUartRxStarWithWrap(str(recv))
                # for info in tmpList:
                # logger.debug("%s [RX] : %s"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), info))

                # print(time.time()," ---  data_recv  --> ", cmdData)
                # # logger.debug("<<<<" + recv)
                q.put(recv, block=True, timeout=1)

                # # recv = sp.read(1)

                # # head = struct.unpack('B',recv)[0];

                # # logger.debug(" 0x%x "%(head))
            # logger.debug("---------------")
        except:
            logger.error('serial port is recv excp!!!!')

        # time.sleep(0.1)
        gevent.sleep(0.005)
        # logger.debug("+++++++++++++++")
        # await asyncio.sleep(1)
        # logger.debug('R Done after s')


def uartTx(sp, q):
    print('Write  processing...')
    cnt = 0

    while True:
        gevent.sleep(0.8)
        # cnt = cnt + 1
        # print("write %d"%(cnt))
        if sp.isOpen():
            if not q.empty():
                sendData = q.get()
                sendDataToSerialPort(sp, list(sendData))
                print('W Done after s')


def bytesToHexString(bytesArr):
    return ''.join(['%02X ' % b for b in bytesArr])


def printUartRxData(q):
    print('Log Print processing...')

    while True:
        gevent.sleep(0.01)
        if not q.empty():
            sendData = q.get()
            print(type(sendData))

            if DISPLAY_FORMATE_CFG == DISPLAY_FORMATE_CFG_HEX_BIT:
                # logger.debug(sendData.hex(" ", -2))
                logger.debug("%s [RX] : %s" % (
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                    bytesToHexString(sendData)))
            elif DISPLAY_FORMATE_CFG == DISPLAY_FORMATE_CFG_STR_BIT:
                tmpList = splitUartRxStarWithWrap(
                    (sendData.decode(encoding="utf-8", errors="ignore")))
                for info in tmpList:
                    logger.debug("%s [RX] : %s" % (
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), info))
            else:
                logger.debug("%s [RX] : %s  %s" % (
                    datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S.%f'), bytesToHexString(sendData),
                    sendData.decode(encoding="utf-8", errors="ignore")))
                break


""" Test mcu into boot """


def setDTRState(serialPort, state):
    serialPort.setDTR(state)


def setRTSState(serialPort, state):
    serialPort.setRTS(state)
    # Work-around for adapters on Windows using the usbser.sys driver:
    # generate a dummy change to DTR so that the set-control-line-state
    # request is sent with the updated RTS state and the same DTR state
    # In order to bypass the driver problem under Windows system, update the RTS and DTR status at the same time
    serialPort.setDTR(serialPort.dtr)


def enterBoot(serialPort, delay=False):
    # delay is a workaround for bugs with the most common auto reset
    # circuit and Windows, if the EN pin on the dev board does not have
    # enough capacitance.
    # If the EN pin on the development board does not have enough capacitance
    last_error = None

    # issue reset-to-bootloader:
    # RTS = either CH_PD/EN or nRESET (both active low = chip in reset
    # DTR = GPIO0 (active low = boot to flasher)
    #
    # DTR & RTS are active low signals,
    # ie True = pin @ 0V, False = pin @ VCC.
    setDTRState(serialPort, False)  # IO0=HIGH
    # setDTRState(serialPort, True)   # IO0=LOW
    setRTSState(serialPort, True)  # EN=LOW, chip in reset
    time.sleep(0.1)
    if delay:
        # Some chips are more likely to trigger the esp32r0
        # watchdog reset silicon bug if they're held with EN=LOW
        # for a longer period
        time.sleep(1.2)

    setDTRState(serialPort, True)  # IO0=LOW
    setRTSState(serialPort, False)  # EN=HIGH, chip out of reset
    if delay:
        # Sleep longer after reset.
        # This workaround only works on revision 0 ESP32 chips,
        # it exploits a silicon bug spurious watchdog reset.
        time.sleep(0.4)  # allow watchdog reset to occur
    time.sleep(1)

    setDTRState(serialPort, False)  # IO0=HIGH, done
    setRTSState(serialPort, False)
    time.sleep(1)

    return last_error


if __name__ == "__main__":
    logger.debug("This is a debug log")
    logger.info("This is an info log")
    logger.critical("This is critical")
    logger.error("An error occurred\n")

    # pyinstaller -i butter.ico -F d:/desktop/seven.py

    uart_list = [0]
    uart_refresh()  # Get the existing serial port information

    try:
        name = input(
            "Select the serial port (just enter the number of the serial port):")

        SERIAL_PORT_CFG = {'name': "COM" + name,
                           'baudrate': 115200,
                           'timeout': 5,
                           'parity': serial.PARITY_NONE,
                           'stopbit': serial.STOPBITS_ONE,
                           'flowcontrol': False}
    except Exception as error:
        print("Serial port configuration error：", error)

    # init serial port
    try:
        SP = serial.Serial(SERIAL_PORT_CFG.get('name'),
                           SERIAL_PORT_CFG.get('baudrate'),
                           timeout=SERIAL_PORT_CFG.get('timeout'),
                           parity=SERIAL_PORT_CFG.get('parity'),
                           stopbits=SERIAL_PORT_CFG.get('stopbit'),
                           rtscts=SERIAL_PORT_CFG.get('flowcontrol'))
    except Exception as error:
        logger.error('open ' + SERIAL_PORT_CFG.get('name') + ' is fail!!!!')
        sys.exit(1)

    logger.info(">>>>>>>>>>>>>>>> %s is opened....." %
                SERIAL_PORT_CFG.get('name'))

    # boot into boot
    enterBoot(SP, delay=False)

    uartRxDataQueue = queue.Queue(1000)
    print(uartRxDataQueue)

    uartTxDataQueue = queue.Queue(1000)
    print(uartTxDataQueue)

    # Send the automatic baud rate calibration byte to 2652 boot
    # cc26xxBuadradeCommunicatonReq = [0x55, 0x55]
    # uartTxDataQueue.put(cc26xxBuadradeCommunicatonReq, block=True, timeout=5)

    startTime = int(round(time.time() * 1000))

    uartTasks = [gevent.spawn(uartTx, SP, uartTxDataQueue)]

    uartTasks = [gevent.spawn(uartTx, SP, uartTxDataQueue),
                 gevent.spawn(uartRx, SP, uartRxDataQueue),
                 gevent.spawn(printUartRxData, uartRxDataQueue)]

    gevent.joinall(uartTasks, 5)  # 3 Close all threads after seconds
    logger.info(">>>>>>>>>>>>>>>> end")

    #    try:
    #
    #        ser = serial.Serial()
    #
    #        gevent.joinall(uartTasks, 3)  # Close all threads after 3 seconds
    #        logger.info(">>>>>>>>>>>>>>>> end")
    #        if ser.isOpen():
    #          ser.close()
    #           print("COM:", name, "Closed successfully")
    #       if not ser.isOpen():
    #           print("no serial port open？")
    #   except Exception as error:
    #       print("COM:", name, "Failed to close")
    #
    #   uart_refresh()  # Get the existing serial port information
    #    print("\n")

    # while True:
    # data_count = SP.inWaiting()
    # if data_count !=0 :
    # recv = SP.read(SP.in_waiting)
    # print(time.time()," ---  data_recv  --> ", recv)
    # time.sleep(0.1)

    # while True:
    # try:
    # # logger.debug("+++++++++++++++")
    # tmpLen = SP.inWaiting()
    # logger.debug(tmpLen)

    # if tmpLen !=0:
    # recv = SP.read(tmpLen)
    # # logger.debug("<<<<" + recv)
    # print(time.time()," ---  data_recv  --> ", recv)
    # except:
    # logger.error('serial port is recv excp!!!!')

    # time.sleep(0.1)

    # uartRx2(SP,uartRxDataQueue)

    # thread_loop = asyncio.new_event_loop()
    # run_loop_thread = Thread(target=start_evt_loop, args=(thread_loop,))
    # run_loop_thread.start()

    # logger.debug("TIME: %d"%(int(round(time.time() * 1000)) - startTime))

    # # main_loop = asyncio.new_event_loop()
    # # main_loop.run_until_complete(create_task(thread_loop))  # 主线程负责create coroutine object

    # asyncio.run_coroutine_threadsafe(writeDataFromSerial(SP), thread_loop)
    # asyncio.run_coroutine_threadsafe(readDataFromSerial(SP), thread_loop)
