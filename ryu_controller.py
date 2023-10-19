"""
Ryu controller for my SDN, which watches for topology events. 
You can use this framework to collect information about 
the network topology and install rules to implement shortest path switching
"""

from ryu.app import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_5, ofproto_v1_5_parser

from ryu.topology import event
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import  ethernet, arp

from topology_manager import TopoManager
import socket
import pickle

#class CommunicationAPI(ControllerBase):

class CustomRyuController(app_manager.RyuApp):
    # Select the versione of the OpenFlow protocol
    OFP_VERSION = [ofproto_v1_5.OFP_VERSION]

    # The application will deploy a REST API interface to set the rules and manage the message to the controller from the devices
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(CustomRyuController, self).__init__(*args, **kwargs)

        # Instance variables for the controller to manage the SDN
        self.tm = TopoManager()
        self.mac_to_port = {}   # MAC addresses are used to identify hosts in the network

        # IP and Port of the controller
        self.ipRyuApp = "127.0.0.1"
        self.portRyuApp = 6654

        # Variables for the wsgi application and to provide a REST API interface for the network
        # wsgi = kwargs['wsgi']
        # wsgi.register(CommunicationAPI, {'controller_instance': self})
        self.controller_instance = self

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating that a switch has come online
        """
        switch = ev.switch
        
        print("Added switch! switch_%d with ports: ", switch.dp.id)
        for port in switch.ports:
            print("\t%d : %s", port.port_no, port.hw_addr)

        # Add the switch with the method of the topomanager
        self.tm.add_switch(switch)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_remove_switch(self, ev):
        """
        Event handler indicating that a switch is being removed
        """
        switch = ev.switch

        # Remove the switch from the topology
        self.tm.remove_switch(switch)

    @set_ev_cls(event.EventHostAdd)
    def handle_add_host(self, ev):
        """
        Event handler to add an host when it has joined the network
        """
        host = ev.host

        print("Host added! host_%d, with MAC: %s and IP: %s, on switch_%d on port: %d", host.name, host.mac, host.ipv4, host.port.dpid, host.port.port_no)

        # Updating topology network
        self.tm.add_host(host)

        print("Current network_graph: ", self.tm.network_graph)

    @set_ev_cls(event.EventLinkAdd)
    def handle_add_link(self, ev):
        """
        Event handler to add a link when a connection is made between two devices
        """
        link = ev.link
        src_switch_dpid = link.src.dpid
        src_switch_port = link.src.port_no
        dst_switch_dpid = link.dst.dpid
        dst_switch_port = link.dst.port_no

        print("Link added! switch_%d(port: %d) -> switch_%d(port: %d)", src_switch_dpid, src_switch_port, dst_switch_dpid, dst_switch_port)

        # Adding the link to the topology
        self.tm.add_link(src_switch_dpid, src_switch_port, dst_switch_dpid, dst_switch_port)

    @set_ev_cls(event.EventLinkDelete)
    def handle_delete_link(self, ev):
        """
        Event handler to remove a link when a connection is done between two devices
        """
        link = ev.link
        
        # Remove the link between two switches in the topology
        self.tm.remove_link_between_switches(link)

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        port = ev.port
        print("Port Changed:  switch_%d/%d (MAC: %s),  Status: %s", port.dpid, port.port_no, port.hw_addr, "UP" if port.is_live() else "DOWN")

    def send_to_thread(self):
        """
        Method to send through a Thread the updated network_graph
        """
        graph = self.tm.gui_graph 
        
        
        # Serialize the graph using pickle
        serialized_graph = pickle.dumps(graph)

        # Create a socket connection and send the serialized graph
        try:
            print("Sending graph topology")
            self.guiSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.guiSocket.connect((self.ipRyuApp, 7001))   # Using the port 7001 to send the graph. The GUI will receive the graph on this listening port (for the GUI)
            self.guiSocket.send(serialized_graph)
            self.guiSocket.close()
        except Exception as e:
            print("Error sending network_graph:", e)

    def set_up_rule_for_hosts(self, src_ip, dst_ip):
        """
        Method callable from the CommunicationAPI to set the rules between the switches to let the communication flow between hosts
        Parameters:
            src_ip: the IP address of the source host
            dst_ip: the IP address of the destination host
        Returns:
            None
        """
        # ...

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Event handler for the packet in event. Sets up the proper forwarding rules between the switches
        """
        msg = event.msg
        datapath = msg.datapath
        in_port = msg.in_port   # Port of the switch that received the packet

        pkt = packet.Packet(msg.data)   # Convert the raw packet data into something more manageable
        eth_header = pkt.get_protocols(ethernet.ethernet)[0]   # Extract the Ethernet head from the list of the Ethernet frames
        src = eth_header.src   # MAC address of the source host
        dst = eth_header.dst   # MAC address of the destination host
        dpid = datapath.dpid    # dpid of the switch that received the packet in and triggered the packet_in event

        if eth_header.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # Ignore the link layer discovery packets from the switches
        
        if eth_header.ethertype == ether_types.ETH_TYPE_ARP:
            arp_packet = pkt.get_protocol(arp.arp)
            if arp_packet:
                
                if arp_packet.opcode == arp.ARP_REQUEST:    # Handle ARP request
                    # self.handle_arp_request(datapath, in_port, eth_header, arp_packet)
                    print(f"ARP request received from switch_{dpid} with MAC: {src}")

                elif arp_packet.opcode == arp.ARP_REPLY:    # Handle ARP reply
                    print(f"ARP reply received from switch_{dpid} with MAC: {src}")

        src_dpid = self.tm.get_dpid_from_host(src)  # dpid source switch
        dst_dpid = self.tm.get_dpid_from_host(dst)  # dpid destination switch

        if src_dpid is not None and dst_dpid is not None:   # If the retrieving of the switches is succesfull
            print(f"Packet in switch_{dpid}: Ethernet frame from switch_{src_dpid}(MAC: {src}) to switch_{dst_dpid}(MAC: {dst})")

    # def handle_arp_request(self, datapath, in_port, eth_header,  arp_packet):    

    def add_flow(self, datapath, match, actions):
        """
        Method to add a flow on a given datapath(switch), with specific matches and telling to perform a determinate action
        Parameters:
            datapath: the switch on which the rules will be installed
            match: the object that contains useful information and the in_port
            actions: the object containing useful information on the actions to take with the packets, and the out_port
        Returns:
            None
        """
        ofproto = ofproto_v1_5
        parser = ofproto_v1_5_parser

        flow_to_add_to_switch = parser.OFPFlowMod(
            datapath = datapath, 
            cookie = 0,
            command = ofproto.OFPFC_ADD, 
            idle_timeout = 0, 
            hard_timeout = 0, 
            priority = ofproto.OFP_DEFAULT_PRIORITY, 
            match = match,
            actions = actions)
        
        datapath.send_msg(flow_to_add_to_switch)    # Send the message to set up the flow, from the controller to the switch