# SDN Viewer and Tester

This repository contains the implementation of an SDN (Software-Defined Networking), I used Ryu as a controller 
(with version 1.4 of the OpenFlow Protocol), utilizing shortest path switching logic. The controller has a topology manager, 
and it's designed to handle different topology.

## Table of contents

- [Overview](#overview)
- [Files and Components](#files-and-components)
- [Usage](#usage)
- [Prerequisites](#prerequisites)
- [Running the Controller](#running-the-controller)
- [Running Mininet](#running-mininet)
- [Running the GUI](#running-the-GUI)
- [Testing communication](#testing-communication)
- [Contributing](#contributing)

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

