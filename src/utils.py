import time
from datetime import datetime, timedelta


def count_down(weeks=0, days=0, hours=0, minutes=0, seconds=0):
    remain_time = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    while remain_time.total_seconds() > 0:
        time.sleep(1)
        remain_time -= timedelta(seconds=1)
        print("\r 剩余时间：{}".format(remain_time), end="", flush=True)
    print("")
