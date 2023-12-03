# SDN Viewer and Tester

This repository contains the implementation of an SDN (Software-Defined Networking), I used Ryu as a controller 
(with version 1.4 of the OpenFlow Protocol), utilizing shortest path switching logic. The controller has a topology manager, 
and it's designed to handle different topology.

## Table of contents

- [Overview](#overview)
- [Files and Components](#files-and-components)
- [Usage](#usage)
- [Prerequisites](#prerequisites)
- [Running the controller](#running-the-controller)
- [Running Mininet](#running-mininet)
- [Running the GUI](#running-the-GUI)
- [HTTP requests to controller](#http-requests-to-controller)

## Overview

The SDN Viewer project is a software-defined networking solution designed to provide a graphical user-friendly interface, 
to visualize, manage and analyze SDN deployments. The components utilized are Ryu SDN controller, 
Mininet SDN emulator,and everything is based on the OpenFlow Protocol 1.4. The SDN GUI is a
graphical user interface designed for managing and visualizing Software-Defined Networking (SDN) environments. 
Developed using the Tkinter library for the GUI components, the application integrates various modules 
and functionalities to provide a user-friendly platform for network administrators and testers. 
These are the key features/components: Graph Display section, Details View section, Topology loading section, 
Ryu-controller output section, Mininet CLI Terminal section and HTTP requests to controller section.

## Files and Components

This project consists of the following key files:

1. 'ryu_controller.py': This file contains the Ryu controller logic responsible for managing the network topology. It uses the shortest path switching to let the hosts communicate.
2. 'topology_manager.py': The topoManager app is designed to manage the adding,removing of devices in the topology. It manages the storing of flow rules for the switches, and the mapping of the hosts, with their IPs and switches to which they are connected.
3. 'mininet_runner.py': This file contains the emulation of the SDN topologies using Mininet as emulator.
4. 'sdn_GUI.py': This file contains the GUI to test the SDN deployment.

## Prerequisites

Before using the SDN ensure you have the following mandatory modules installed:

- Ryu Framework
- Mininet
- NetworkX
- Arping
- Matplotlib
- Tkinter

## Usage

To use the SDN Viewer and simulate nwtwork topologies:

1. Clone this repository to your local machine.
2. Install the required dependencies mentioned in the [Prerequisites](#prerequisites) section

Since you need to run Mininet as root user, I advise you to install this project inside comnetsemu.

## Running the controller

Run the ryu controller by executing the following command:

```bash
ryu-manager --observe-links ryu_controller.py
```

## Running Mininet

Run mininet by executing the following command:

```bash
sudo python3 mininet_runner.py "topology type" "additional number of hosts"
```

## Running the GUI

Running the GUI by executing the following command:

```bash
python3 sdn_GUI.py
```

## HTTP requests to controller

The controller extends the ControllerBase class and is designed to manage and manipulate network rules through a RESTful API.
Key Features:

1. Initialization of Communication:
        Method: initiating_comunication
        Route: /communication/{src_host_ip}/{dst_host_ip}
        HTTP Method: POST
        Description: Handles incoming requests to initialize communication between specified source and                  destination hosts. Invokes the set_up_rule_for_hosts method in the underlying controller application.

2. Termination of Communication:
        Method: stop_communication
        Route: /communication/{src_host_ip}/{dst_host_ip}
        HTTP Method: DELETE
        Description: Processes requests to stop communication between specified source and destination hosts.            Utilizes the delete_rule_for_hosts method in the controller application.

3. Graph Topology Retrieval:
        Method: get_graph_topology
        Route: /topology/graph
        HTTP Method: GET
        Description: Responds to requests seeking the NetworkX Graph representation of the SDN topology. Invokes         the get_topology_graph method in the controller application and returns the serialized graph in JSON             format.

4. Device Information Retrieval:
        Method: get_host_information
        Route: /topology/node/{device_name}
        HTTP Method: GET
        Description: Handles requests for retrieving information about a specific network device. Invokes the            get_device_info method in the controller application and returns the serialized device information in            JSON format.

5. Debug Information Display:
        Method: get_debug_info
        Route: /debug/show_information
        HTTP Method: GET
        Description: Responds to requests for displaying debug information. Invokes the debug_show_topology              method in the controller application, showcasing relevant debugging details.
