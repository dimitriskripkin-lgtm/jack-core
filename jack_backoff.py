MODULE_VERSION = 1
import time
def sleep(n):
    time.sleep(min(40, 5*(2**min(max(int(n),0),3))))
