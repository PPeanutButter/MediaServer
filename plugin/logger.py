import os
import time
from threading import Timer
from tensorboardX import SummaryWriter
runs = "Raspberry Pi 4 Model B"
writer = SummaryWriter(log_dir=f"{runs}", max_queue=6)


def write_log():
    epoch = int(time.time())
    _, cpu, mem = get_cpu_and_mem()
    writer.add_scalar(tag='rpi4/Cpu', display_name='Cpu.', scalar_value=cpu, global_step=epoch)
    writer.add_scalar(tag='rpi4/Mem', display_name='MB', scalar_value=mem, global_step=epoch)
    writer.add_scalar(tag='rpi4/Temp', display_name='℃', scalar_value=get_temp_value(), global_step=epoch)
    Timer(60, write_log).start()


def get_temp_value():
    return float(f'{cat_temp() / 1000:.1f}')


def cat_temp():
    with open('/sys/class/thermal/thermal_zone0/temp', mode='r') as f:
        return int(f.read())


def get_cpu_and_mem():
    top_info = ''.join(os.popen("top -bn 1 -i -c").readlines()).replace('\n', '')
    regex = r"%Cpu\(s\).*\s(.*)\sid.*MiB\sMem.*\s(.*)\sused.*buff"
    import re
    matches = re.finditer(regex, top_info)
    for matchNum, match in enumerate(matches, start=1):
        return top_info, float('%.1f' % (100 - float(match.group(1)))), float('%.1f' % float(match.group(2)))


write_log()
