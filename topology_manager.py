from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
import networkx as nx

class Device():
    """
    A base class to represent a generic device in the network

    A Host or Switch has a name and a set of neighbours
    """

    def __init__(self, name):
        self.name = name
        self.neighbours = set()
    
    def add_neighbours(self, device):
        self.neighbours.add(device)
    
    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

class TMSwitch(Device):
    """
    A switch, extends the class Device

    An object of this class is a wrapper of a Ryu Switch object,
    which contains information about the switch ports and others
    """

    def __init__(self, name, switch):
        super(TMSwitch, self).__init__(name)

        self.switch = switch
        # If necessary add others attributes
    
    def get_dpid(self):
        """
        Return the datapath ID of the Switch
        """
        return self.switch.dp.id
    
    def get_ports(self):
        """
        Return list of Ryu port objects for the switch
        """
        return self.switch.ports
    
    def get_dp(self):
        """
        Return switch datapath object
        """
        return self.switch.dp
    
class TMHost(Device):
    """
    A Host, extends the class Device

    An object of this class is a wrapper of a Ryu Host object,
    which contains information about the switch port to which the host is connected
    """

    def __init__(self, name, host):
        super(TMHost, self).__init__(name)

        self.host = host
        # Add more attributes if necessary

    def get_mac(self):
        """
        Return the MAC address of the host
        """
        return self.host.mac
    
    def get_ip(self):
        """
        Return the IP v4 of the host
        """
        return self.host.ipv4
    
    def get_port(self):
        """
        Return the Ryu port object of the Host to which the switch is connected
        """
        return self.host.port
    
class TopoManager():
    """
    Class to manage the network topology, with Switches, Hosts and Controller
    """
    
