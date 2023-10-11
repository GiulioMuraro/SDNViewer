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
        super(TMSwitch, name).__init__(name)

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
        super(TMHost, name).__init__(name)

        self.host = host
        # Add more attributes if necessary

    def get_mac(self):
        """
        Return the MAC address of the host
        """
        return self.host.mac
    
    def get_ip(self):   # We suppose that a host has only one IP(only one interface with the network)
        """
        Return the IPs v4 of the host for every interface
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
    
    def __init__(self):
        # Initialize data structures to manage the topology
        self.all_devices = []   # Set to collect all the devices(switches, hosts) of the topology
        self.all_links = [] # Set to collect all the links of the topology
        self.network_graph = nx.Graph() #   Graph of networkX to represent the topology
        self.topoSwitches = [] # Set of datapaths
        self.host_to_switch_dpid_port = {} # Nested dictionary to find the corresponding datapath ID(aka. Switch ID) and port to which the host, with the selected MAC address, is connected 
        
        self.flow_rules = [] # Set of rules for the forwarding logic of the Ryu controller

    def add_switch(self, sw):
        """
        Method to handle the add switch event in the topology  
        Parameters:
            switch: instance of the switch to add to the topology
        Returns:
            None
        """
        dpid_str = str(sw.dp.id)

        if dpid_str not in self.topoSwitches:   # If the new switch is not inside the topology, it will be added
            name = "switch_{}".format(str(dpid_str))
            switch = TMSwitch(name, sw)

            self.all_devices.append(switch)
            self.network_graph.add_node(dpid_str)
            self.topoSwitches[dpid_str] = {sw.address, sw.ofproto, sw.ofproto_parser}
            
            print("Added switch to the topology and the graph: ", dpid_str)
            print("Current network_graph nodes: ", self.network_graph.nodes)
        else:
            print("The switch is already inside the topology. Nothing is being added")

    def add_host(self, h):
        """
        Method to handle the add host event in the topology
        Parameters:
            host: instance of the host to add to the topology
        Returns:
            None
        """
        name = "host_{}|{}|{}".format(h.name, h.ipv4, h.mac)
        host = TMHost(name, h)
        dpid_str = str(h.port.dpid)
        
        self.all_devices.append(host)
        self.network_graph.add_node(name)
        self.network_graph.add_edge(dpid_str, name) # Adding the edge from the host to the switch. In the network_graph the hosts are saved as their names, and the switches as their dpid
        self.host_to_switch_dpid_port[h.mac] = {dpid_str, h.port.port_no}    # Saving the dpid and port to which the host is connected

        print("Current mapping of the host_to_switch_dpid_port: ", self.host_to_switch_dpid_port)
