from pathlib import Path


def test_latency(net, file_name: str, result_dir: Path = Path(".")):
    result_dir = result_dir.expanduser().resolve()
    result_dir.mkdir(parents=True, exist_ok=True)


    vpn = net["vpn"]
    service = net["service"]
    user = net["user"]

    out = user.cmd(f"ping -c 30 {service.IP()}")

    with open(result_dir / file_name, "w") as f:
        f.write(out)