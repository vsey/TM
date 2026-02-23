#!/usr/bin/env python

"""
linuxrouter.py: Example network with Linux IP router

This example converts a Node into a router using IP forwarding
already built into Linux.

The example topology creates a router and three IP subnets:

    - 192.168.1.0/24 (r0-eth1, IP: 192.168.1.1)
    - 172.16.0.0/12 (r0-eth2, IP: 172.16.0.1)
    - 10.0.0.0/8 (r0-eth3, IP: 10.0.0.1)

Each subnet consists of a single host connected to
a single switch:

    r0-eth1 - s1-eth1 - h1-eth0 (IP: 192.168.1.100)
    r0-eth2 - s2-eth1 - h2-eth0 (IP: 172.16.0.100)
    r0-eth3 - s3-eth1 - h3-eth0 (IP: 10.0.0.100)

The example relies on default routing entries that are
automatically created for each router interface, as well
as 'defaultRoute' parameters for the host interfaces.

Additional routes may be added to the router or hosts by
executing 'ip route' or 'route' commands on the router or hosts.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
from functools import partial
from test import test_latency, test_bandwidth, CPUMonitor


class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd("sysctl net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl net.ipv4.ip_forward=0")
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    "A LinuxRouter connecting three IP subnets"

    # pylint: disable=arguments-differ
    def build(self, **_opts):
        # define hosts
        user = self.addHost("user", ip="10.68.1.2/30", defaultRoute="via 10.68.1.1")
        vpn = self.addHost("vpn", ip="10.68.5.2/30", defaultRoute="via 10.68.5.1")
        service = self.addHost("service", ip="10.68.3.2/30", defaultRoute="via 10.68.3.1")

        # define isps
        isp_user = self.addHost("isp_user", ip=None, cls=LinuxRouter)
        isp_vpn = self.addHost("isp_vpn", ip=None, cls=LinuxRouter)

        # internet core
        internet_core = self.addHost("internet_core", ip=None, cls=LinuxRouter)

        # define switches
        s1, s2, s3, s4, s5 = [self.addSwitch(s) for s in ("s1", "s2", "s3", "s4", "s5")]

        # connections
        latency = "10ms"

        # S1
        self.addLink(user, s1, delay=latency)
        self.addLink(isp_user, s1, intfName1="isp_user-s1", params1={"ip": "10.68.1.1/30"}, delay=latency)

        # S2
        self.addLink(internet_core, s2, intfName1="core-s2", params1={"ip": "10.68.2.1/30"}, delay=latency)
        self.addLink(isp_user, s2, intfName1="isp_user-s2", params1={"ip": "10.68.2.2/30"}, delay=latency)

        # S3
        self.addLink(service, s3, delay=latency)
        self.addLink(internet_core, s3, intfName1="core-s3", params1={"ip": "10.68.3.1/30"}, delay=latency)

        # S4
        self.addLink(isp_vpn, s4, intfName1="isp_vpn-s4", params1={"ip": "10.68.4.2/30"}, delay=latency)
        self.addLink(internet_core, s4, intfName1="core-s4", params1={"ip": "10.68.4.1/30"}, delay=latency)

        # S5
        self.addLink(vpn, s5, delay=latency)
        self.addLink(isp_vpn, s5, intfName1="isp_vpn-s5", params1={"ip": "10.68.5.1/30"}, delay=latency)


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(
        topo=topo,
        waitConnected=True,
        switch=partial(OVSSwitch, failMode="standalone"),
        link=TCLink,
    )  # controller is used by s1-s3
    net.start()

    # setup routes after the nodes are initialized
    # Get routers
    isp_user = net["isp_user"]
    isp_vpn = net["isp_vpn"]
    internet_core = net["internet_core"]

    isp_user.cmd("ip route add 10.68.3.0/30 via 10.68.2.1")
    isp_user.cmd("ip route add 10.68.4.0/30 via 10.68.2.1")
    isp_user.cmd("ip route add 10.68.5.0/30 via 10.68.2.1")

    internet_core.cmd("ip route add 10.68.1.0/30 via 10.68.2.2")
    internet_core.cmd("ip route add 10.68.5.0/30 via 10.68.4.2")

    isp_vpn.cmd("ip route add 10.68.1.0/30 via 10.68.4.1")
    isp_vpn.cmd("ip route add 10.68.2.0/30 via 10.68.4.1")
    isp_vpn.cmd("ip route add 10.68.3.0/30 via 10.68.4.1")

    # setup vpn
    server = net["vpn"]
    client = net["user"]

    with CPUMonitor() as latency_bare:
        test_latency(net, "./test/latency-bare")
    test_bandwidth(net, "./test/bw-bare")

    if True:
        client.cmd("wg-quick up ./client.conf")
        server.cmd("wg-quick up ./server.conf")

    test_latency(net, "./test/latency-wg")
    test_bandwidth(net, "./test/bw-wg")

    CLI(net)

    print(latency_bare.results)

    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
