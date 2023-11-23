from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class Device():
    """
    A base class to represent a generic device in the network

    A Host or Switch has a name and a set of neighbours
    """

    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name
    
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
        self.neighbours = set()
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
    
    def add_neighbours(self, switch_neighbour):
        self.neighbours.add(switch_neighbour)
    
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
        self.topoSwitches = {} # Dictionary of dictionary with the dpid and outport for every switch to communicate with another switch
        self.host_to_switch_dpid_port = {} # Nested dictionary to find the corresponding datapath ID(aka. Switch ID) and port to which the host, with the selected MAC address, is connected 
        
        self.flow_rules = {} # Set of rules for the forwarding logic of the Ryu controller

        self.counter = 0

    def add_switch(self, sw):
        """
        Method to handle the add switch event in the topology  
        Parameters:
            switch: instance of the switch to add to the topology
        Returns:
            None
        """
        dpid = sw.dp.id
        if dpid not in self.topoSwitches:   # If the new switch is not inside the topology, it will be added
            name = "switch_{}".format(str(dpid))
            switch = TMSwitch(name, sw)

            self.all_devices.append(switch)
            self.network_graph.add_node(dpid)
            self.topoSwitches[dpid] = {}    # Later with a add_link() method this dictionary will be populated
            
            print("Added switch to the topology and the graph: ", dpid)
        else:
            print(f"The switch_{dpid} is already inside the topology. Nothing is being added")

        self.debug_show_topology()

    def remove_switch(self, sw):
        """
        Method to handle the removal of a switch event in the topology.
        Parameters:
            sw: The instance of the switch to be removed from the topology.
        Returns:
            None
        """
        dpid = sw.dp.id
        if dpid in self.topoSwitches:  # Check if the switch is in the topology
            # Clean up any associated data or connections here

            # Remove the switch from the list of all devices
            self.all_devices = [device for device in self.all_devices if device.name != "switch_{}".format(dpid)]

            # Remove the switch from the network graph
            self.network_graph.remove_node(dpid)

            # Remove the switch from the topoSwitches dictionary
            del self.topoSwitches[dpid]

            print("Removed switch from the topology and the graph: switch_", dpid)
        else:
            print("The switch is not in the topology. Nothing to remove.")

        self.debug_show_topology()


    def add_host(self, h):
        """
        Method to handle the add host event in the topology
        Parameters:
            host: instance of the host to add to the topology
        Returns:
            None
        """
        name = "host_{}".format(h.mac)
        host = TMHost(name, h)
        dpid = h.port.dpid
        
        self.all_devices.append(host)
        self.network_graph.add_node(name)
        self.network_graph.add_edge(dpid, name) # Adding the edge from the host to the switch. In the network_graph the hosts are saved as their names, and the switches as their dpid
        self.host_to_switch_dpid_port[h.mac] = {"dpid": dpid, "port_no": h.port.port_no}    # Saving the dpid and port to which the host is connected

        self.debug_show_topology()

        pos = nx.spring_layout(self.network_graph)
        nx.draw(self.network_graph, pos, with_labels=True, node_size=500, font_size=10, font_color='black')
    
        '''# Create a Matplotlib figure and draw the graph on it
        fig = plt.figure(figsize=(3, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_axis_off()
        nx.draw(self.network_graph, pos, ax=ax, with_labels=True, node_size=500, font_size=10, font_color='black')
    
        # Save the figure to an image file
        canvas.print_png("graph_image" + str(self.counter) + ".png")
        self.counter+=1'''

    def add_link(self, src_switch_dpid, src_port_no, dst_switch_dpid, dst_port_no):
        """
        Method to handle the add of the link between two switches, and setting the output port of each
        Parameters:
            src_switch_dpid: dpid of the source switch
            src_port_no: port number of the source switch
            dst_switch_dpid: dpid of the destination switch
            dst_port_no: port number of the destination switch
        Returns:
            None
        """
        # Retrieving the switches from the topology
        src_dev = self.get_device_by_port(src_switch_dpid, src_port_no)
        dst_dev = self.get_device_by_port(dst_switch_dpid, dst_port_no)
        
        # Adding the two switches to each other as the neighbours
        if src_dev and dst_dev and isinstance(src_dev, TMSwitch) and isinstance(dst_dev, TMSwitch):
            src_dev.add_neighbours(dst_dev)
            dst_dev.add_neighbours(src_dev)
        
        # Add the link in the network_graph
        self.network_graph.add_edge(src_switch_dpid, dst_switch_dpid)

        # Check and create entries for source switch if they don't exist
        if src_switch_dpid not in self.topoSwitches:
            self.topoSwitches[src_switch_dpid] = {}

        # Check and create entries for destination switch if they don't exist
        if dst_switch_dpid not in self.topoSwitches:
            self.topoSwitches[dst_switch_dpid] = {}

        # Add the output port for each switch
        self.topoSwitches[src_switch_dpid][dst_switch_dpid] = src_port_no   # The switch src to send something to the switch dst has to use the port src_port_no
        self.topoSwitches[dst_switch_dpid][src_switch_dpid] = dst_port_no

        self.debug_show_topology()

    def remove_link_between_switches(self, link):
        """
        Method to delete a link between two switches
        Parameters:
            link: The link to be removed between two switches
        Returns:
            None
        """
        src_switch_dpid = link.src.dpid
        dst_switch_dpid = link.dst.dpid

        # Delete the edge from the graph, only if the edges are in the graph
        if self.network_graph.has_edge(src_switch_dpid, dst_switch_dpid):
            self.network_graph.remove_edge(src_switch_dpid, dst_switch_dpid)

        # Delete the output port in the topoSwitches list
        if src_switch_dpid in self.topoSwitches and dst_switch_dpid in self.topoSwitches[src_switch_dpid]:
            del self.topoSwitches[src_switch_dpid][dst_switch_dpid]
        if dst_switch_dpid in self.topoSwitches and src_switch_dpid in self.topoSwitches[dst_switch_dpid]:
            del self.topoSwitches[dst_switch_dpid][src_switch_dpid]

    def get_mac_host_by_ip(self, ip_host):
        """
        Method to get the MAC address of an host by its IP address
        Parameters:
            ip_host: IP address of the host you want to get the MAC address of
        Returns:
            MAC address of the host
        """
        for dev in self.all_devices:
            if isinstance(dev, TMHost) and dev.get_ip()[0] == ip_host:
                return dev.get_mac()

    def get_device_by_port(self, dpid, port_no):
        """
        Method to obtain the device(host or switch) with the sepcified dpid and port_no
        Parameters:
            dpid: dpid of the switch specified, if dev is a switch
            port_no: the number of the port, if dev is a switch, else if the port_no is of the host, it will return the host as dev
        Returns:
            An instance of the device found, else None
        """
        for dev in self.all_devices:
            if isinstance(dev, TMSwitch):
                for port in dev.get_ports():
                    if port.port_no == port_no and dev.get_dpid() == dpid:
                        return dev
            elif isinstance(dev, TMHost):
                if port_no == dev.get_port().port_no:
                    return dev
        return None
    
    def get_device_by_name(self, name):
        """
        Method to retrieve a device by its name
        Parameters:
            name: the name of the device, so for example "switch_1" or "host_1" or "host_2"
        Returns:
            Instance of device switch or host
        """
        for dev in self.all_devices:
            if name == str(dev.get_name()):
                return dev
    
    def get_host_by_mac(self, mac):
        """
        Method to retrieve an host by its MAC address
        Parameters:
            mac: MAC address of the host
        Returns:
            Instance of the host with the selected MAC address        
        """
        for dev in self.all_devices:
            if isinstance(dev, TMHost) and mac == dev.get_mac():
                return dev
    
    def get_host_port_connected_to_switch(self, host_mac, switch_dpid):
        """
        Method to retrieve the port of the switch(dpid) to which a selected host with a MAC address is connected to
        Parameters:
            host_mac: MAC address of the host to which the port of the switch is connected
            switch_dpid: the ID of the switch to which the host with host_mac is connected
        Returns:
            switch_port: the port of the switch connected to the host
        """
        switch_port = None
        if host_mac in self.host_to_switch_dpid_port and switch_dpid == self.host_to_switch_dpid_port[host_mac]['dpid']:
            switch_port = self.host_to_switch_dpid_port[host_mac]['port_no']
            return switch_port
        else:
            return None

    def get_shortest_path(self, src_switch_dpid, dst_switch_dpid):
        """
        Method to get the shortest path (using Dijkstra's algorithm) between two switch
        Parameters:
            src_switch_dpid: Source switch dpid
            dst_switch_dpid: Destination switch dpid
        Returns:
            List containing the shortest path between the 2 switch
        """
        print(f"Getting the shortest path between {src_switch_dpid} and {dst_switch_dpid}")
        try:
            shortest_path = nx.shortest_path(self.network_graph, source = src_switch_dpid, target = dst_switch_dpid)
            return shortest_path
        except nx.NetworkXNoPath:
            print("Not finding a path between the switches")
            return None
        except nx.NodeNotFound:
            print("Not finding one or both of the passed nodes")
            return None

    def get_dpid_from_host(self, host_mac):
        """
        Method to retrieve the dpid of the switch to which the host with the host_mac address is connected
        Parameters:
            host_mac: MAC address of the host
        Returns:
            dpid of the switch to which the host is connected
        """
        if host_mac in self.host_to_switch_dpid_port:
            inner_dict = self.host_to_switch_dpid_port[host_mac]
            return inner_dict['dpid']   #This first key is the dpid of the switch
    
    def get_output_port(self, src_switch_dpid, dst_switch_dpid):
        """
        Method to retrieve the output port for the src_switch to send data to dst_switch(The output port is of the src_switch)
        Parameters:
            src_switch_dpid: dpid of the source switch
            dst_switch_dpid: dpid of the destination switch
        Returns:
            The int value of the output port of the src_switch, None if there isn't
        """
        path = self.get_shortest_path(src_switch_dpid, dst_switch_dpid)

        # If the path is existent and is longer than 1 hop
        if path is not None and len(path) > 1:
            if src_switch_dpid in self.topoSwitches and dst_switch_dpid in self.topoSwitches[src_switch_dpid]:  # If the output port for the src_switch to the dst_switch is set
                return self.topoSwitches[src_switch_dpid][dst_switch_dpid]
    
    def add_rule_to_dict(self, dpid, in_port, dl_src, dl_dst, out_port):
        """
        Method to add a forwarding rule to the topology manager, regarding a switch(datapath)
        Parameters:
            dpid: switch to add a forwarding rule to
            in_port: in_port of the switch where it receives the packet
            dl_src: MAC address of the source host
            dl_dst: MAC address of the destination host
            out_port: out_port where the packet has to be sent from the datapath
        Returns:
            None
        """
        # Create the flow_key using in_port, dl_src, and dl_dst
        flow_key = (in_port, dl_src, dl_dst)
        
        # Check if the dpid is already in the flow_rules dictionary
        if dpid not in self.flow_rules:
            # If not, add the dpid as a key with an empty dictionary as the value
            self.flow_rules[dpid] = {}
        
        # Add the out_port to the corresponding flow_key for the specific dpid
        self.flow_rules[dpid][flow_key] = out_port

        self.debug_show_topology()

    def get_rule_from_dict(self, dpid, in_port, dl_src, dl_dst):
        """
        Method to retrieve the out_port from the flow_rules dictionary based on the provided parameters.
        Parameters:
            dpid: dpid of the switch
            in_port: in_port of the switch where it receives the packet
            dl_src: MAC address of the source host
            dl_dst: MAC address of the destination host
        Returns:
            out_port: the out_port where the packet should be sent from the datapath
        """
        # Check if the dpid is present in the flow_rules dictionary
        if dpid in self.flow_rules:
            flow_key = (in_port, dl_src, dl_dst)
            try:
                # Attempt to retrieve the out_port for the given key
                out_port = self.flow_rules[dpid][flow_key]
                return out_port
            except KeyError:
                # Handle the case when the key is not in the dictionary
                print(f"No entry flow found for dpid {dpid} with match fields: {flow_key}")
                return None
        else:
            print(f"No entry flow found for dpid {dpid}")
            return None

    def get_rules_from_dict(self, dpid, in_port):
        """
        Method to retrieve all rules with a specific in_port from the flow_rules dictionary for a given DPID.
        Parameters:
            dpid: DPID of the switch
            in_port: in_port of the switch where it receives the packet
        Returns:
            rules: a dictionary containing all rules associated with the provided in_port for the given DPID
        """
        rules = {}  # Initialize an empty dictionary to store the rules
        
        # Check if the dpid is present in the flow_rules dictionary
        if dpid in self.flow_rules:
            for flow_key, out_port in self.flow_rules[dpid].items():
                # Check if the in_port in the flow_key matches the provided in_port
                if flow_key[0] == in_port:
                    # Add the rule to the rules dictionary
                    rules[flow_key] = out_port
        else:
            print(f"No entry flow found for dpid {dpid}")
        
        return rules

    def debug_show_topology(self):
        """
        Method to retrieve all kinds of information based on the current topology of the SDN, to check that everything works fine
        """
        print("DEVICES: ")
        print(self.all_devices)
        
        print("LINKS: ")
        print(self.all_links)
        
        print("DATAPATHS: ")
        print(self.topoSwitches)

        print("DATAPATH TO HOST LOOKUP: ")
        print(self.host_to_switch_dpid_port)

        print("NETWORK GRAPH: ")
        print(self.network_graph)
        print("Nodes: ", self.network_graph.nodes)
        print("Edges: ", self.network_graph.edges)

        print("FLOW RULES: ")
        print(self.flow_rules)
