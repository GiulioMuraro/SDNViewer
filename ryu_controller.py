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
        wsgi = kwargs['wsgi']
        wsgi.register(CommunicationAPI, {'controller_instance': self})
        self.controller_instance = self
