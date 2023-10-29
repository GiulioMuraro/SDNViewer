import time
import argparse

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo, SingleSwitchTopo, LinearTopo
from mininet.topolib import TreeTopo
from mininet.log import setLogLevel, info, error

# Topology with 10 hosts and 6 switch
class AssignOneTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1 = self.addHost('host_1')
        h2 = self.addHost('host_2')
        h3 = self.addHost('host_3')
        h4 = self.addHost('host_4')
        h5 = self.addHost('host_5')
        h6 = self.addHost('host_6')
        h7 = self.addHost('host_7')
        h8 = self.addHost('host_8')
        h9 = self.addHost('host_9')
        h10 = self.addHost('host_10')
        s1 = self.addSwitch('switch_1')
        s2 = self.addSwitch('switch_2')
        s3 = self.addSwitch('switch_3')
        s4 = self.addSwitch('switch_4')
        s5 = self.addSwitch('switch_5')
        s6 = self.addSwitch('switch_6')
        self.addLink(h1, s1)
        self.addLink(h7, s1)
        self.addLink(h8, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(h4, s4)
        self.addLink(h9, s4)
        self.addLink(h10, s4)
        self.addLink(h5, s5)
        self.addLink(h6, s6)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s2, s5)
        self.addLink(s3, s6)


# Triangle topology with 3 hosts and 3 switch
class TriangleTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1 = self.addHost('host_1')
        h2 = self.addHost('host_2')
        h3 = self.addHost('host_3')
        s1 = self.addSwitch('switch_1')
        s2 = self.addSwitch('switch_2')
        s3 = self.addSwitch('switch_3')
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s1)

# Topology with some loops to test network
class SomeLoopsTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1 = self.addHost('host_1')
        h2 = self.addHost('host_2')
        h3 = self.addHost('host_3')
        h4 = self.addHost('host_4')
        s1 = self.addSwitch('switch_1')
        s2 = self.addSwitch('switch_2')
        s3 = self.addSwitch('switch_3')
        s4 = self.addSwitch('switch_4')
        s5 = self.addSwitch('switch_5')
        s6 = self.addSwitch('switch_6')
        self.addLink(h1, s1)
        self.addLink(h2, s5)
        self.addLink(h3, s4)
        self.addLink(h4, s6)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s3, s6)
        self.addLink(s2, s5)
        self.addLink(s5, s4)
        self.addLink(s4, s6)
        self.addLink(s6, s1)


# Topology with n hosts and n switches
class MeshTopo(Topo):
    def __init__(self, n=4, **opts):
        Topo.__init__(self, **opts)
        switches = []
        for i in range(1,n+1):
            h = self.addHost('host_%d' % i)
            s = self.addSwitch('switch_%d' % i)
            self.addLink(h, s)
            switches.append(s)
        for i in range(0,n-1):
            for j in range(i+1,n):
                self.addLink(switches[i], switches[j])

# Topology with 4 hosts and 9 switches, with a long path
class LongPathTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1= self.addHost('host_1')
        h2=self.addHost('host_2')
        h3=self.addHost('host_3')
        h4=self.addHost('host_4')
        s1=self.addSwitch('switch_1')
        s2=self.addSwitch('switch_2')
        s3=self.addSwitch('switch_3')
        s4=self.addSwitch('switch_4')
        s5=self.addSwitch('switch_5')
        s6=self.addSwitch('switch_6')
        s7=self.addSwitch('switch_7')
        s8=self.addSwitch('switch_8')
        s9=self.addSwitch('switch_9')
        self.addLink(h1,s1)
        self.addLink(h2,s2)
        self.addLink(h3,s3)
        self.addLink(h4,s4)
        self.addLink(s1,s5)
        self.addLink(s1,s8)
        self.addLink(s1,s9)
        self.addLink(s2,s5)
        self.addLink(s2,s6)
        self.addLink(s2,s9)
        self.addLink(s3,s6)
        self.addLink(s3,s9)
        self.addLink(s3,s7)
        self.addLink(s4,s7)
        self.addLink(s4,s9)
        self.addLink(s4,s8)

TOPOLOGIES = {
    "single": SingleSwitchTopo,
    "tree": TreeTopo,
    "linear": LinearTopo,
    "assign1": AssignOneTopo,
    "triangle": TriangleTopo,
    "mesh": MeshTopo,
    "someloops": SomeLoopsTopo,
    "longpath" : LongPathTopo
}

def send_arping(node):
    """
    Function to send arp from an host to the network
    """
    print('arping -c 1 -A -I {}-eth0 {}'.format(node.name, node.IP()))
    node.cmd('arping -c 1 -A -I {}-eth0 {}'.format(node.name, node.IP()))

def disable_ipv6(node):
    """
    This function disables IPv6 on a given Mininet host.
    It runs sysctl commands to disable IPv6 for all, default, and loopback network interfaces of the host.
    """
    node.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

def main():
    """
    Set up the example topology to test the SDN network
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", type = str, default = "info")
    
    # This line adds subparsers to your main parser. Subparsers allow you to organize your command-line arguments into different groups or subcommands
    subparsers = parser.add_subparsers(dest = "command")
    
    # This line creates subparsers for each key in the TOPOLOGIES dictionary and stores them in the sp_cmds dictionary. 
    # Each subparser corresponds to a different topology type
    sp_cmds = {t: subparsers.add_parser(t) for t in TOPOLOGIES.keys()}
    sp_cmds["single"].add_argument("nodes", type = int)
    sp_cmds["tree"].add_argument("depth", type = int)
    sp_cmds["linear"].add_argument("nodes", type = int)
    sp_cmds["mesh"].add_argument("nodes", type = int)

    # This line parses the command-line arguments provided when running the script and stores the result in the args variable.
    # The arguments provided are based on the subcommands and options you've defined.
    args = parser.parse_args()

    setLogLevel(args.log_level)
    topo = None

    # Select the type of topology
    if args.command == "single":
        topo = TOPOLOGIES["single"](args.nodes)
    elif args.command == "tree":
        topo = TOPOLOGIES["tree"](args.depth)
    elif args.command == "linear":
        topo = TOPOLOGIES["linear"](args.nodes)
    elif args.command == "mesh":
        topo = TOPOLOGIES["mesh"](args.nodes)
    else:
        topo = TOPOLOGIES[args.command]()

    # Create the network
    net = Mininet(topo = topo, autoSetMacs = True, controller = RemoteController)

    # Disable the IPv6 on the hosts and switches
    # This avoid messages from the ICMPv6 that can complicate the link discovery
    for h in net.hosts:
        disable_ipv6(h)
    for s in net.switches:
        disable_ipv6(s)

    # Run network
    net.start()

    # Wait 1 second to let all the devices set themselves up
    time.sleep(1)

    # ARP requests between hosts
    for h in net.hosts:
        # Send a "join message", which is a gratuitous ARP
        info('*** Sending ARPing from host %s\n' % (h.name))
        send_arping(h)  

    CLI(net)

    net.stop()

if __name__ == "__main__":
    main()

