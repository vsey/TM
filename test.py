from pathlib import Path
from typing import Union


def ping(src, dst, count=30):
    out = src.cmd(f"ping -c {count} {dst.IP()}")
    return out

def test_latency(net, result_dir: Union[Path, str] = Path(".")):
    result_dir = result_dir if isinstance(result_dir, Path) else Path(result_dir)
    result_dir = result_dir.expanduser().resolve()
    result_dir.parent.mkdir(parents=True, exist_ok=True)

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

