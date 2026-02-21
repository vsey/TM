from pathlib import Path
from typing import Union
import time


def ping(src, dst, count=5):
    out = src.cmd(f"ping -c {count} {dst.IP()}")
    return out

def test_latency(net, result_dir: Union[Path, str] = Path(".")):
    result_dir = result_dir if isinstance(result_dir, Path) else Path(result_dir)
    result_dir = result_dir.expanduser().resolve()
    result_dir.mkdir(parents=True, exist_ok=True)

    vpn = net["vpn"]
    service = net["service"]
    user = net["user"]

    vpn_service = ping(vpn, service)
    user_vpn = ping(user, vpn)
    user_service = ping(user, service)

    with open(result_dir / "vpn_service", "w") as f:
        f.write(vpn_service)

    with open(result_dir / "user_vpn", "w") as f:
        f.write(user_vpn)

    with open(result_dir / "user_service", "w") as f:
        f.write(user_service)


def test_bandwidth(net, file_name: str, result_dir: Union[Path, str] = Path(".")):
    result_dir = result_dir if isinstance(result_dir, Path) else Path(result_dir)
    result_dir = Path(result_dir).expanduser().resolve()
    result_dir.mkdir(parents=True, exist_ok=True)

    vpn = net["service"]
    user = net["user"]

    server_ip = vpn.IP()

    # Start iperf3 server
    vpn.cmd("iperf3 -s -D")
    time.sleep(1)

    output = user.cmd(f"iperf3 -c {server_ip} -t 10 -J")

    result_file = result_dir / f"{file_name}.json"
    with open(result_file, "w") as f:
        f.write(output)

    vpn.cmd("kill %iperf3")

    return output
