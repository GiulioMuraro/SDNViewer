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
