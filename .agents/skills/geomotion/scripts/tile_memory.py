"""Bound source mosaics and decoded tiles by bytes and available runtime memory."""
import os
from pathlib import Path
from config import DEFAULTS

def available_memory_bytes():
    available=os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
    try:
        limit=Path('/sys/fs/cgroup/memory.max').read_text().strip()
        if limit!='max':
            available=min(available,max(0,int(limit)-int(Path('/sys/fs/cgroup/memory.current').read_text())))
    except (OSError,ValueError):
        pass
    return available

def check_tile_memory(bounds,physical_count,available=None):
    # Pillow RGB storage can occupy four bytes per pixel. Both buffers coexist
    # while mosaics are assembled, before decoded tiles are released.
    pixels=sum((b[1]-b[0]+1)*(b[3]-b[2]+1)*256*256 for b in bounds.values())
    estimate=(pixels+physical_count*256*256)*4
    cfg=DEFAULTS['execution'];budget=cfg['max_tile_buffer_mb']*1024**2
    reserve=(cfg['memory_reserve_mb']+cfg['estimated_worker_mb'])*1024**2
    available=available_memory_bytes() if available is None else available
    if estimate>budget or estimate+reserve>available:
        raise ValueError('Source tile buffers exceed memory budget; split the sequence or provide more memory without reducing native source detail')
    return estimate
