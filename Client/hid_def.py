import time

import hid
from loguru import logger

product_id = 0x2107
vendor_id = 0x413D
usage_page = 0xFF00

DEBUG = False
VERBOSE = False


def set_debug(debug):
    global DEBUG
    DEBUG = debug


def set_verbose(verbose):
    global VERBOSE
    VERBOSE = verbose


h = hid.device()


# 初始化HID设备
def init_usb(vendor_id, usage_page):
    if DEBUG:
        logger.debug(f"init_usb(vendor_id={vendor_id}, usage_page={usage_page})")
        return 0

    global h

    try:
        h.close()
    except Exception:
        pass

    h = hid.device()

    try:
        # Linux hidapi/libusb may report usage_page as 0,
        # so identify KVM Card Mini directly by VID/PID.
        h.open(vendor_id, product_id)
        h.set_nonblocking(1)
        logger.info(
            f"KVM Card Mini opened: {vendor_id:04x}:{product_id:04x}"
        )
        return 0
    except OSError as e:
        logger.error(f"Device open failed: {e}")
        return 1


def check_connection() -> bool:
    try:
        h.read(1)
        return True
    except Exception:
        return False
    return False


# 读写HID设备
def hid_report(buffer=[], r_mode=False, report=0):
    if DEBUG:
        logger.debug(f"hid_report(buffer={buffer}, r_mode={r_mode}, report={report})")
        return 0
    buffer = buffer[-1:] + buffer[:-1]
    buffer[0] = 0
    if VERBOSE:
        logger.debug(f"hid < {buffer}")
    try:
        h.write(buffer)
    except (OSError, ValueError):
        logger.error("Error writing data to device")
        return 1
    except NameError:
        logger.error("Uninitialized device")
        return 4
    if r_mode:  # 读取回复
        time_start = time.perf_counter()
        while 1:
            try:
                d = h.read(64)
            except (OSError, ValueError):
                logger.error("Error reading data from device")
                return 2
            if d:
                if VERBOSE:
                    logger.debug(f"hid > {d}")
                break
            if time.perf_counter() - time_start > 2:
                logger.error("Device response timeout")
                d = 3
                break
    else:
        d = 0
    return d
