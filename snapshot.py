"""snapshot.py — encode and decode a full system state snapshot.

Usage:
    python snapshot.py save [output.snap]   # capture and save (default: snapshot.snap)
    python snapshot.py load <file.snap>     # decode and print a saved snapshot
    python snapshot.py watch [file.snap]    # save a new snapshot every 60s

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
"""
from __future__ import annotations

import base64
import datetime
import gzip
import json
import os
import platform
import sys

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ---------------------------------------------------------------------------
# Encoder
# ---------------------------------------------------------------------------

def encode ( path: str = "snapshot.snap" ) -> str:
    """Capture current system state, compress, base64-encode, and save to file."""
    state = _capture ( )
    raw = json.dumps ( state , indent=2 , default=str ).encode ( "utf-8" )
    compressed = gzip.compress ( raw )
    encoded = base64.b64encode ( compressed ).decode ( "ascii" )
    with open ( path , "w" ) as f:
        f.write ( encoded )
    size_kb = os.path.getsize ( path ) / 1024
    print ( f"Snapshot saved → {path} ({size_kb:.1f} KB)" )
    return encoded


# ---------------------------------------------------------------------------
# Decoder
# ---------------------------------------------------------------------------

def decode ( path: str ) -> dict:
    """Load and decompress a snapshot file into a plain dict."""
    with open ( path ) as f:
        data = f.read ( ).strip ( )
    raw = gzip.decompress ( base64.b64decode ( data ) )
    return json.loads ( raw )


def report ( path: str ) -> None:
    """Print a human-readable report from a snapshot file."""
    state = decode ( path )
    _print_report ( state )


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

def watch ( path: str = "snapshot.snap" , interval: int = 60 ) -> None:
    """Continuously overwrite the snapshot file every `interval` seconds."""
    import time
    print ( f"Watching — saving snapshot to '{path}' every {interval}s. Ctrl-C to stop." )
    try:
        while True:
            encode ( path )
            time.sleep ( interval )
    except KeyboardInterrupt:
        print ( "\nStopped." )


# ---------------------------------------------------------------------------
# State capture
# ---------------------------------------------------------------------------

def _capture ( ) -> dict:
    state: dict = {
        "captured_at": datetime.datetime.now ( datetime.timezone.utc ).isoformat ( ) ,
        "system": _system_info ( ) ,
    }
    if HAS_PSUTIL:
        state[ "cpu" ] = _cpu ( )
        state[ "memory" ] = _memory ( )
        state[ "disk" ] = _disk ( )
        state[ "battery" ] = _battery ( )
        state[ "network" ] = _network ( )
        state[ "processes" ] = _processes ( )
    return state


def _system_info ( ) -> dict:
    return {
        "node": platform.node ( ) ,
        "os": platform.system ( ) ,
        "os_version": platform.version ( ) ,
        "machine": platform.machine ( ) ,
        "python": sys.version ,
        "cwd": os.getcwd ( ) ,
    }


def _cpu ( ) -> dict:
    return {
        "percent_per_core": psutil.cpu_percent ( interval=1 , percpu=True ) ,
        "percent_total": psutil.cpu_percent ( interval=0 ) ,
        "count_logical": psutil.cpu_count ( logical=True ) ,
        "count_physical": psutil.cpu_count ( logical=False ) ,
        "freq_mhz": psutil.cpu_freq ( ).current if psutil.cpu_freq ( ) else None ,
    }


def _memory ( ) -> dict:
    vm = psutil.virtual_memory ( )
    sw = psutil.swap_memory ( )
    return {
        "total_gb": round ( vm.total / 1e9 , 2 ) ,
        "available_gb": round ( vm.available / 1e9 , 2 ) ,
        "used_pct": vm.percent ,
        "swap_used_gb": round ( sw.used / 1e9 , 2 ) ,
        "swap_pct": sw.percent ,
    }


def _disk ( ) -> dict:
    partitions = [ ]
    for p in psutil.disk_partitions ( all=False ):
        try:
            usage = psutil.disk_usage ( p.mountpoint )
            partitions.append ( {
                "mount": p.mountpoint ,
                "fstype": p.fstype ,
                "total_gb": round ( usage.total / 1e9 , 2 ) ,
                "used_gb": round ( usage.used / 1e9 , 2 ) ,
                "free_gb": round ( usage.free / 1e9 , 2 ) ,
                "used_pct": usage.percent ,
            } )
        except PermissionError:
            pass
    return {"partitions": partitions}


def _battery ( ) -> dict | None:
    b = psutil.sensors_battery ( )
    if b is None:
        return None
    return {
        "percent": b.percent ,
        "plugged_in": b.power_plugged ,
        "secs_left": b.secsleft if b.secsleft != psutil.POWER_TIME_UNLIMITED else None ,
    }


def _network ( ) -> dict:
    addrs = {}
    for iface , snics in psutil.net_if_addrs ( ).items ( ):
        addrs[ iface ] = [ {"family": str ( s.family ) , "address": s.address} for s in snics ]
    stats = {}
    for iface , s in psutil.net_if_stats ( ).items ( ):
        stats[ iface ] = {"up": s.isup , "speed_mb": s.speed}
    return {"interfaces": addrs , "stats": stats}


def _processes ( ) -> list[ dict ]:
    procs = [ ]
    for p in psutil.process_iter ( [ "pid" , "name" , "status" , "cpu_percent" , "memory_percent" ] ):
        try:
            procs.append ( p.info )
        except (psutil.NoSuchProcess , psutil.AccessDenied):
            pass
    return sorted ( procs , key=lambda x: x.get ( "memory_percent" ) or 0 , reverse=True )[ :50 ]


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def _print_report ( s: dict ) -> None:
    def hr ( title: str = "" ) -> None:
        print ( f"\n{'─' * 50}" )
        if title:
            print ( f"  {title}" )
            print ( f"{'─' * 50}" )

    hr ( )
    print ( f"  SNAPSHOT — {s[ 'captured_at' ]}" )
    hr ( )

    sys_ = s.get ( "system" , {} )
    print ( f"  Host    : {sys_.get ( 'node' )}" )
    print ( f"  OS      : {sys_.get ( 'os' )} {sys_.get ( 'os_version' )}" )
    print ( f"  Python  : {sys_.get ( 'python' , '' ).splitlines ( )[ 0 ]}" )
    print ( f"  CWD     : {sys_.get ( 'cwd' )}" )

    if "cpu" in s:
        hr ( "CPU" )
        cpu = s[ "cpu" ]
        print ( f"  Total   : {cpu[ 'percent_total' ]}%" )
        print ( f"  Cores   : {cpu[ 'count_physical' ]} physical / {cpu[ 'count_logical' ]} logical" )
        if cpu.get ( "freq_mhz" ):
            print ( f"  Freq    : {cpu[ 'freq_mhz' ]:.0f} MHz" )

    if "memory" in s:
        hr ( "MEMORY" )
        mem = s[ "memory" ]
        print ( f"  Total   : {mem[ 'total_gb' ]} GB" )
        print ( f"  Used    : {mem[ 'used_pct' ]}%  ({mem[ 'total_gb' ] - mem[ 'available_gb' ]:.2f} GB used)" )
        print ( f"  Swap    : {mem[ 'swap_pct' ]}%  ({mem[ 'swap_used_gb' ]} GB)" )

    if "disk" in s:
        hr ( "DISK" )
        for p in s[ "disk" ].get ( "partitions" , [ ] ):
            print ( f"  {p[ 'mount' ]:20s}  {p[ 'used_pct' ]:5.1f}% used  "
                    f"({p[ 'used_gb' ]:.1f} / {p[ 'total_gb' ]:.1f} GB)" )

    if "battery" in s and s[ "battery" ]:
        hr ( "BATTERY" )
        bat = s[ "battery" ]
        plug = "plugged in" if bat[ "plugged_in" ] else "on battery"
        mins = f"{bat[ 'secs_left' ] // 60}m left" if bat.get ( "secs_left" ) else ""
        print ( f"  {bat[ 'percent' ]}%  {plug}  {mins}" )

    if "processes" in s:
        hr ( "TOP PROCESSES (by memory)" )
        print ( f"  {'PID':>7}  {'MEM%':>6}  {'CPU%':>6}  NAME" )
        for p in s[ "processes" ][ :15 ]:
            print ( f"  {p[ 'pid' ]:>7}  {(p.get ( 'memory_percent' ) or 0):>6.2f}  "
                    f"{(p.get ( 'cpu_percent' ) or 0):>6.1f}  {p.get ( 'name' , '?' )}" )

    hr ( )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[ 1: ]

    if not args or args[ 0 ] == "save":
        path = args[ 1 ] if len ( args ) > 1 else "snapshot.snap"
        encode ( path )

    elif args[ 0 ] == "load":
        if len ( args ) < 2:
            print ( "Usage: python snapshot.py load <file.snap>" )
            sys.exit ( 1 )
        report ( args[ 1 ] )

    elif args[ 0 ] == "watch":
        path = args[ 1 ] if len ( args ) > 1 else "snapshot.snap"
        watch ( path )

    else:
        print ( __doc__ )
        sys.exit ( 1 )
