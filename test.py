from pathlib import Path


def test_latency(net, file_name: str, result_dir: Path = Path(".")):
    result_dir = result_dir.expanduser().resolve()
    result_dir.mkdir(parents=True, exist_ok=True)

    isp_user = net["isp_user"]
    isp_vpn = net["isp_vpn"]
    internet_core = net["internet_core"]

    server = net["vpn"]
    client = net["user"]

    out = client.cmd("ping -c 30 service")

    with open(result_dir / file_name, "w") as f:
        f.write(out)