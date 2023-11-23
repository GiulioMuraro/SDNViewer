"""
Ryu controller for my SDN, which watches for topology events. 
You can use this framework to collect information about 
the network topology and install rules to implement shortest path switching
"""

from ryu.base import app_manager
from ryu.controller import ofp_event, ofp_handler
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4, ofproto_v1_4_parser

from ryu.topology import event
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import  ethernet, arp

from topology_manager import TopoManager
import socket
import pickle

class CommunicationAPI(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(CommunicationAPI, self).__init__(req, link, data, **config)
        self.controller_app = data['controller_instance']
    
    @route('communication', '/communication/{src_host_ip}/{dst_host_ip}', methods = ['GET'])
    def initiating_comunication(self, req, src_host_ip, dst_host_ip):
        print("Received request to initialize the communication")
        self.controller_app.set_up_rule_for_hosts(src_host_ip, dst_host_ip)



class CustomRyuController(app_manager.RyuApp):
    # Select the version of the OpenFlow protocol
    OFP_VERSION = [ofproto_v1_4.OFP_VERSION]

    # The application will deploy a REST API interface to set the rules and manage the message to the controller from the devices
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(CustomRyuController, self).__init__(*args, **kwargs)

        # Instance variables for the controller to manage the SDN
        self.tm = TopoManager()
        self.mac_to_port = {}   # MAC addresses are used to identify hosts in the network

        # IP and Port of the controller
        self.ipRyuApp = "127.0.0.1"
        self.portRyuApp = 6653

        # Variables for the wsgi application and to provide a REST API interface for the network
        wsgi = kwargs['wsgi']
        wsgi.register(CommunicationAPI, {'controller_instance': self})
        self.controller_instance = self

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating that a switch has come online
        """
        switch = ev.switch
        
        print(f"Trying to add switch! switch_{switch.dp.id} with ports: ")
        for port in switch.ports:
            print(f"\t{port.port_no} : {port.hw_addr}")

        # Add the switch with the method of the topomanager
        self.tm.add_switch(switch)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_remove_switch(self, ev):
        """
        Event handler indicating that a switch is being removed
        """
        switch = ev.switch

        print(f"Trying to remove switch! switch_{switch.dp.id} with ports: ")
        for port in switch.ports:
            print(f"\t{port.port_no} : {port.hw_addr}")

        # Remove the switch from the topology
        self.tm.remove_switch(switch)

    @set_ev_cls(event.EventHostAdd, MAIN_DISPATCHER)
    def handle_add_host(self, ev):
        """
        Event handler to add an host when it has joined the network
        """
        host = ev.host

        print(f"Host added! Host with MAC: {host.mac} and IP: {host.ipv4}, on switch_{host.port.dpid} on port: {host.port.port_no}")

        # Updating topology network
        self.tm.add_host(host)

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

        print(f"Link added! switch_{src_switch_dpid}(port: {src_switch_port}) -> switch_{dst_switch_dpid}(port: {dst_switch_port})")

        # Adding the link to the topology
        self.tm.add_link(src_switch_dpid, src_switch_port, dst_switch_dpid, dst_switch_port)

    @set_ev_cls(event.EventLinkDelete)
    def handle_delete_link(self, ev):
        """
        Event handler to remove a link when a connection is done between two devices
        """
        link = ev.link
        src_switch_dpid = link.src.dpid
        src_switch_port = link.src.port_no
        dst_switch_dpid = link.dst.dpid
        dst_switch_port = link.dst.port_no

        print(f"Trying to remove link! switch_{src_switch_dpid}(port: {src_switch_port}) -> switch_{dst_switch_dpid}(port: {dst_switch_port})")
        
        # Remove the link between two switches in the topology
        self.tm.remove_link_between_switches(link)

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        port = ev.port
        print(f"Port Changed: switch_{port.dpid}/{port.port_no} (MAC: {port.hw_addr}), Status: {'UP' if port.is_live() else 'DOWN'}")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        handler = ofp_handler.OFPHandler(datapath, version = ofproto_v1_4.OFP_VERSION)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install the flow rule to send ARP requests from hosts to the controller
        match = parser.OFPMatch(eth_type = ether_types.ETH_TYPE_ARP)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        self.add_flow(datapath, match, actions, 100)

    def send_to_thread(self):
        """
        Method to send through a Thread the updated network_graph
        """
        graph = self.tm.network_graph 
        
        
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

    def set_up_rule_for_hosts(self, src_host_ip, dst_host_ip):
        """
        Method callable from the CommunicationAPI to set the rules between the switches to let the communication flow between hosts
        Parameters:
            src_host_ip: IP address of the source host
            dst_host_ip: IP address of the destination host
        Returns:
            None
        """
        src_mac = self.tm.get_mac_host_by_ip(src_host_ip)
        dst_mac = self.tm.get_mac_host_by_ip(dst_host_ip)
        src_dpid = self.tm.get_dpid_from_host(src_mac)  # dpid of the datapath connected to the src_host
        dst_dpid = self.tm.get_dpid_from_host(dst_mac)  # dpid of the datapath connected to the dst_host
        
        parser = ofproto_v1_4_parser

        print(f"Setting up the rules between host(IP: {src_host_ip} / MAC: {src_mac}) and host(IP: {dst_host_ip} / MAC: {dst_mac})")

        if src_dpid in self.tm.topoSwitches and dst_dpid in self.tm.topoSwitches:
            path = self.tm.get_shortest_path(src_dpid, dst_dpid)    # Find the list of nodes to get from the source to the destination
            if path is not None and len(path) > 1:
                print(f"The shortest path is: {path}")
                for i in range(0, len(path)):
                    if i == 0:  # If it's the first switch of the hops/steps. Create rule to manage packets from src_host to intranet and from the intranet to src_host
                        first = path[i]
                        second = path[i + 1]
                        firstDatapath = self.tm.get_device_by_name(f"switch_{first}").get_dp()
                        
                        # Extract the in and out port of the first switch
                        out_port = self.tm.get_output_port(first, second)
                        in_port = self.tm.get_host_port_connected_to_switch(src_mac, first)

                        # Creating flow rule from the intranet to the host
                        actions = self.create_actions(out_port = in_port)
                        match = self.create_match(in_port = out_port, src_mac = dst_mac, dst_mac = src_mac)
                        self.add_flow(firstDatapath, match, actions)
                        self.tm.add_rule_to_dict(first, in_port = out_port, dl_src = dst_mac, dl_dst = src_mac, out_port = in_port)

                        # Creating flow rule from the host to the intranet
                        actions = self.create_actions(out_port = out_port)
                        match = self.create_match(in_port = in_port, src_mac = src_mac, dst_mac = dst_mac)
                        self.add_flow(firstDatapath, match, actions)
                        self.tm.add_rule_to_dict(first, in_port = in_port, dl_src = src_mac, dl_dst = dst_mac, out_port = out_port)

                    elif i == len(path) - 1:  # If it's the last switch of the hops/steps. Create rule to manage the packets from the dst_host to the intranet and from the intranet to the dst_host
                        last = path[i]
                        secondToLast = path[i - 1]
                        lastDatapath = self.tm.get_device_by_name(f"switch_{last}").get_dp()

                        # Extracting the in and out port of the last switch
                        out_port = self.tm.get_host_port_connected_to_switch(dst_mac, last)
                        in_port = self.tm.get_output_port(last, secondToLast)

                        # Creating flow rule from the intranet to the host
                        actions = self.create_actions(out_port = out_port)
                        match = self.create_match(in_port = in_port, src_mac = src_mac, dst_mac = dst_mac)
                        self.add_flow(lastDatapath, match, actions)
                        self.tm.add_rule_to_dict(last, in_port = in_port, dl_src = src_mac, dl_dst = dst_mac, out_port = out_port)

                        # Creating flow rule from the host to the intranet
                        actions = self.create_actions(out_port = in_port)
                        match = self.create_match(in_port = out_port, src_mac = dst_mac, dst_mac = src_mac)
                        self.add_flow(lastDatapath, match, actions)
                        self.tm.add_rule_to_dict(last, in_port = out_port, dl_src = dst_mac, dl_dst = src_mac, out_port = in_port)

                    else:   # If it's one of the switches between the first and the last. Connect the n switch with the previous(n - 1) and with the following(n + 1)
                        prev = path[i - 1]
                        current = path[i]
                        next = path[i + 1]
                        currentDatapath = self.tm.get_device_by_name(f"switch_{current}").get_dp()

                        # Extracting the in and out port of the current switch
                        out_port = self.tm.get_output_port(current, next)   # Where the packet is going
                        in_port = self.tm.get_output_port(current, prev)    # Where the packet comes from

                        # Creating flow rule from the previous switch to the current
                        actions = self.create_actions(out_port = out_port)
                        match = self.create_match(in_port = in_port, src_mac = src_mac, dst_mac = dst_mac)
                        self.add_flow(currentDatapath, match, actions)
                        self.tm.add_rule_to_dict(current, in_port = in_port, dl_src = src_mac, dl_dst = dst_mac, out_port = out_port)

                        # Creating flow rule from the current switch to the next
                        actions = self.create_actions(out_port = in_port)
                        match = self.create_match(in_port = out_port, src_mac = dst_mac, dst_mac = src_mac)
                        self.add_flow(currentDatapath, match, actions)
                        self.tm.add_rule_to_dict(current, in_port = out_port, dl_src = dst_mac, dl_dst = src_mac, out_port = in_port)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Event handler for the packet in event. Sets up the proper forwarding rules between the switches
        """
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']   # Port of the switch that received the packet

        pkt = packet.Packet(msg.data)   # Convert the raw packet data into something more manageable
        eth_header = pkt.get_protocols(ethernet.ethernet)[0]   # Extract the Ethernet head from the list of the Ethernet frames
        src = eth_header.src   # MAC address of the source host
        dst = eth_header.dst   # MAC address of the destination host
        dpid = datapath.id    # dpid of the switch that received the packet in and triggered the packet_in event

        if eth_header.ethertype == ether_types.ETH_TYPE_LLDP:
            return  # Ignore the link layer discovery packets from the switches
        
        if eth_header.ethertype == ether_types.ETH_TYPE_ARP:
            print("Ethernet Header: ", eth_header)
            arp_packet = pkt.get_protocol(arp.arp)
            if arp_packet:
                if arp_packet.opcode == arp.ARP_REQUEST:    # Handle ARP request
                    print(f"ARP request received from switch_{dpid} with source MAC: {src}")

                    src_ip = arp_packet.src_ip
                    src_mac = arp_packet.src_mac
                    dst_ip = arp_packet.dst_ip
                    
                    # Obtain the MAC address corresponding to the requested IP address
                    dst_mac = self.tm.get_mac_host_by_ip(dst_ip)
                    
                    # If the dst_mac is None, this isn't an ARP request from a host to a host, but it's a broadcasted ARP request, so it doesn't have a dst_mac
                    if dst_mac is not None:
                        # Construct an ARP reply
                        arp_reply = arp.arp(
                            opcode=arp.ARP_REPLY,
                            src_mac=dst_mac,
                            src_ip=dst_ip,
                            dst_mac=src_mac,
                            dst_ip=src_ip
                        )

                        # Construct the Ethernet frame
                        eth_reply = ethernet.ethernet(
                            ethertype=eth_header.ethertype,
                            dst=eth_header.src,
                            src=dst_mac
                        )

                        # Create the packet
                        pkt = packet.Packet()
                        pkt.add_protocol(eth_reply)
                        pkt.add_protocol(arp_reply)

                        print(str(src_mac) + " / " + str(dst_mac))

                        pkt.serialize()

                        # Create an OpenFlow packet_out message with the OpenFlow 1.4 protocol version
                        actions = [datapath.ofproto_parser.OFPActionOutput(in_port)]
                        out = datapath.ofproto_parser.OFPPacketOut(
                            datapath=datapath,
                            buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                            in_port=datapath.ofproto.OFPP_CONTROLLER,
                            actions=actions,
                            data=pkt.data
                        )

                        # Send the packet_out message to the switch
                        datapath.send_msg(out)

                elif arp_packet.opcode == arp.ARP_REPLY:    # Handle ARP reply
                    print(f"ARP reply received from switch_{dpid} with MAC: {src}")

    def add_flow(self, datapath, match, actions, priority = ofproto_v1_4.OFP_DEFAULT_PRIORITY):
        """
        Method to add a flow on a given datapath(switch), with specific matches and telling to perform a determinate action
        Parameters:
            datapath: the switch on which the rules will be installed
            match: the object that contains useful information and the in_port
            actions: the object containing useful information on the actions to take with the packets, and the out_port
            priority: priority of the evaluation of the flow rule by the switch
        Returns:
            None
        """
        ofproto = ofproto_v1_4
        parser = ofproto_v1_4_parser

        # List of instructions for the flowMod
        instruction = [parser.OFPInstructionActions(type_ = ofproto.OFPIT_APPLY_ACTIONS, actions = actions)]

        flow_to_add_to_switch = parser.OFPFlowMod(
            datapath = datapath, 
            cookie = 0,
            command = ofproto.OFPFC_ADD, 
            idle_timeout = 0, 
            hard_timeout = 0, 
            priority = priority, 
            match = match,
            #actions = actions,
            instructions = instruction)
        
        datapath.send_msg(flow_to_add_to_switch)    # Send the message to set up the flow, from the controller to the switch

    def delete_flow_rule(self, datapath, in_port, out_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Create a match for the existing rule based on in_port and out_port
        match = parser.OFPMatch(in_port=in_port, out_port=out_port)

        # Create a flow mod message to delete the rule
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE_STRICT,  # Use DELETE_STRICT for precise deletion
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match  # Set the match condition
        )

        # Send the flow mod message to the switch
        datapath.send_msg(flow_mod)

    def create_match(self, in_port, src_mac, dst_mac):
        """
        Method to create a match object based on a in_port, source MAC address and destination MAC address
        """
        parser = ofproto_v1_4_parser
        match = parser.OFPMatch(
            in_port = in_port,
            eth_src = src_mac,
            eth_dst = dst_mac
        )
        return match
    
    def create_actions(self, out_port):
        """
        Method to create an actions object based on an out_port
        """
        parser = ofproto_v1_4_parser
        actions = [parser.OFPActionOutput(out_port)]
        return actions
    
