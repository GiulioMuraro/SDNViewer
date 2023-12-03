''' Graphic User Interface for the SDN '''

# Graphic modules
import tkinter as tk
from tkinter import ttk
import os
from time import sleep
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas

# Network graph modules
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from PIL import Image, ImageTk

import threading
import requests
from networkx.readwrite import json_graph

# IP and port of Ryu App
ipRyuApp = '127.0.0.1'
portRyuApp = 6653

"""
Ctrl + S: Stop the xterm buffer to read better the log outputs
Ctrl + Q: Resume the xterm buffer to let the program print the logs
"""

# Function to change the graph displayer
def create_graph_image(netGraph):
    pos = nx.spring_layout(netGraph)
    
    nx.draw(netGraph, pos, with_labels=True, node_size=500, font_size=10, font_color='black')
    
    # Create a Matplotlib figure and draw the graph on it
    fig = plt.figure(figsize=(8, 4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.set_axis_off()
    nx.draw(netGraph, pos, ax=ax, with_labels=True, node_size=500, font_size=10, font_color='black')
    
    # Save the figure to an image file
    image_path = "graph_image.png"
    canvas.print_png(image_path)
    
    # Load the image using PIL
    image = Image.open(image_path)
    photo = ImageTk.PhotoImage(image)

    # Closing figure to avoid creating too much figures with matplotlib
    plt.close(fig)
    
    return photo

def retrieve_graph():
    url = "http://localhost:8080/topology/graph"

    while True:
        try:
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # The data received are the networkX graph serialized
                graph_data = response.json()
                
                # Convert from Json Data to NetworkX graph
                graph = json_graph.node_link_graph(graph_data)

                # Now the graph will be converted into a photo, and then added to the frame, periodically
                imgGraph = create_graph_image(graph)
                
                # Add the img to the label
                graphLabel.config(image=imgGraph)
                graphLabel.image = imgGraph

            else:
                print(f"Error: Unable to retrieve graph. Status code: {response.status_code}")

        except requests.RequestException as e:
            print(f"Error: {e}")
            return None
        sleep(12)

# Launch a xterminal with a defined width and height
def launch_xterm(wid, width, height, strg):
    os.system(f'xterm -fa "Monospace" -fs 13 -into {wid} -geometry {width}x{height} -sb -hold -e "{strg}"  &')


# Keeping the text box for the Ryu output disable for the user, so it's a read-only logger
def add_log(outputTextBox, outputLog):
    outputTextBox.configure(state='normal')  # Enable the text box temporarily for modification
    outputTextBox.insert('end', outputLog + '\n')
    outputTextBox.configure(state='disabled')  # Disable the text box again
    outputTextBox.see('end')  # Scroll to the end to show the latest log entry

# Define functions of buttons to load topology
def buttonLoad():
    """ 
    Function to load the topology 
    """
    selected_topology = comboboxTopology.get()
    topology = None
    if selected_topology == "Triangle topology":
        topology = "triangle"
    elif selected_topology == "Mesh topology":
        topology = "mesh 5" # For simplicity we use 5 nodes
    elif selected_topology == "Long path topology":
        topology = "longpath"
    elif selected_topology == "AssignOne topology":
        topology = "assign1"

    launch_xterm(wid_ryu, 900, 400, f"sudo mn -c && ryu-manager --observe-links ryu_controller.py")
    sleep(2)
    launch_xterm(wid_mininet, 900, 400, f"sudo python3 mininet_runner.py {topology}")

    # Sleep to wait everything is set up and then the thread is started
    sleep(5)
    # The thread is started to retrieve the graph every 2 seconds
    start_listening_thread()

def buttonSendHTTPRequest():
    """ Function to send HTTP request to RESTfull API of ryu """
    selected_request = comboboxHTTP.get()
    method, url = selected_request.split('-')
    method = method.replace(" ", "")
    url = url.replace(" ", "")

    # Send the HTTP request
    try:
        response = None
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url)
        elif method == "DELETE":
            response = requests.delete(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Check what request is being sent
            if "http://localhost:8080/topology/node/" in url:   # Request to retrieve node information
                device_info = response.json()
                detailsTextBox.config(state = tk.NORMAL)
                detailsTextBox.delete(1.0, tk.END)
                if device_info['type'] == "Host":
                    detailsTextBox.insert(tk.END, "Host\n")
                    detailsTextBox.insert(tk.END, "Name: " + device_info['name'] + "\n")
                    detailsTextBox.insert(tk.END, "IPv4: " + device_info['ipv4'][0] + "\n")
                    detailsTextBox.insert(tk.END, "MAC address: " + device_info['mac'] + "\n")
                    detailsTextBox.insert(tk.END, "Port:\n")
                    detailsTextBox.insert(tk.END, "    Port number: " + str(device_info['port']['port_no']) + "\n")
                    detailsTextBox.insert(tk.END, "    Datapath to which the host is connected: switch_" + str(device_info['port']['dpid']) + "\n")
                elif device_info['type'] == "Switch":
                    detailsTextBox.insert(tk.END, "Switch\n")
                    detailsTextBox.insert(tk.END, "Name: " + device_info['name'] + "\n")
                    detailsTextBox.insert(tk.END, "Dpid: " + str(device_info['dpid']) + "\n")
                    ports = device_info['ports']
                    detailsTextBox.insert(tk.END, "Ports:\n")
                    for port in ports:
                        detailsTextBox.insert(tk.END, "    Port number: " + str(port['port_no']) + "\n")
                        detailsTextBox.insert(tk.END, "    Port name: " + port['port_name'] + "\n")
                        detailsTextBox.insert(tk.END, "    Port MAC address: " + port['port_hw_addr'] + "\n")
                detailsTextBox.configure(state = 'disabled')
            elif "http://localhost:8080/communication/" in url and method == "POST":    # Request to enable communication between hosts
                pass
            elif "http://localhost:8080/communication/" in url and method == "DELETE":  # Request to disable communication between hosts
                pass
            elif "http://localhost:8080/debug/show_information" in url: # Request to print information logs in the ryu frame
                pass
        else:
            print(f"Error: Unable to send the request. Status code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error: {e}")
        return None
    

# Function to start the thread for the logs management
def start_listening_thread():
    listening_thread = threading.Thread(target=retrieve_graph)
    listening_thread.daemon = True
    listening_thread.start()

# Main function to execute the SDN GUI
def main():
    # To access global variables
    global wid_mininet
    global wid_ryu

    global comboboxTopology
    global comboboxHTTP

    ### Creating the main window
    window = tk.Tk()
    window.title("SDN viewer and tester")

    # Edit the dimensions of the main window
    new_width = 1800
    new_height = 1000
    window.geometry(f"{new_width}x{new_height}")

    # The main window is not resizable and is not opened fullscreen
    window.resizable(width = False, height = False)

    # Configure the main window to have two columns with equal weight
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)
    # Add row configuration if needed
    window.rowconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)
    window.rowconfigure(2, weight=1)

    # Create the style for the rounded frames
    style = ttk.Style()
    style.configure('RoundedFrame.TFrame', borderwidth=3, relief='raised', padding=0, padx = 0, pady = 0, background='lightgrey')

    # Create a custom style for the rounded buttons
    styleButton = ttk.Style()
    styleButton.configure("RoundedButton.TButton",
                        borderwidth=10,
                        focuscolor="red",
                        bordercolor="black",
                        relief="flat",
                        background="#007acc",
                        foreground="white",
                        padding=(10, 5),  # Set padding for button size
                        font=("Helvetica", 10))

    # Change the hover color for the buttons
    styleButton.map("RoundedButton.TButton",
                     background=[("active", "#0055a0")])
    
    # Create a custom font with a specific size
    custom_font_for_combobox = ("Helvetica", 15)  # Adjust the font family and size as needed

    


    ### Top left corner
    global graphLabel
    graphFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 400, width = 1100)
    graphFrame.grid(row = 0, column = 0, sticky = 'nw')

    # The title of graph section
    titleLabelGraph = ttk.Label(graphFrame, text="Network Graph", background = "lightgray", font=("Helvetica", 14))
    titleLabelGraph.pack(side='top', padx = 5, pady = 5, fill = 'none', expand = False)

    graphLabel = tk.Label(graphFrame, bg = "#C2C2A3", height = 400, width = 1100)
    graphLabel.pack(side = 'top', fill = 'none', expand = False)

    graphFrame.propagate(False)



    ### Top right corner
    global detailsTextBox
    detailsViewFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 400, width = 700)
    detailsViewFrame.grid(row = 0, column = 0, sticky = 'ne')

    # The title of the outputTextBox of Ryu
    titleLabelDetails = ttk.Label(detailsViewFrame, text="Details View", background = "lightgray", font=("Helvetica", 14))
    titleLabelDetails.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    detailsTextBox = tk.Text(detailsViewFrame, bg = "#C2C2A3", height = 400, width = 700, font=("Helvetica", 14))
    detailsTextBox.pack(side = 'top', fill = 'none', expand = False)
    detailsTextBox.configure(state = 'disabled')

    detailsViewFrame.propagate(False)


    
    ### Load and Run topology
    loadTopologyFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 100, width = 1800)
    loadTopologyFrame.grid(row = 1, column = 0, sticky = 'we')

    # The title of button section
    titleLabelLoadTopo = ttk.Label(loadTopologyFrame, text="Topology loading", background = "lightgray", font=("Helvetica", 14))
    titleLabelLoadTopo.pack(side='top', padx = 5, pady = 5, fill = 'none', expand = False)

    # Combobox to select the topology
    options = ["Triangle topology", "Mesh topology", "Long path topology", "AssignOne topology"]
    selected_option = tk.StringVar()
    comboboxTopology = ttk.Combobox(loadTopologyFrame, values=options, textvariable=selected_option, height=6, width=100, font = custom_font_for_combobox)
    comboboxTopology.pack(side='left', padx=5, pady=5, anchor = 'center')

    buttonLoadTopology = ttk.Button(loadTopologyFrame, text = "Load & Run topology", style = "RoundedButton.TButton", command=buttonLoad)
    buttonLoadTopology.pack(side = 'left', padx=5, pady=5, anchor = 'center', expand=False)

    loadTopologyFrame.propagate(False)



    ### Ryu output Logs
    ryuFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 400, width = 900)
    ryuFrame.grid(row = 2, column = 0, sticky = 'w')

    # The title of the terminal
    titleLabelRyu = ttk.Label(ryuFrame, text="Ryu controller output", background = "lightgray", font=("Helvetica", 14))
    titleLabelRyu.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    # The actual frame of the terminal
    termf1 = ttk.Frame(ryuFrame, height=400, width=900)
    termf1.pack(side = 'top')
    # To add the controller Ryu output logs
    wid_ryu = termf1.winfo_id()

    ryuFrame.propagate(False)



    ### Mininet CLI terminal
    mininetFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 400, width = 900)
    mininetFrame.grid(row = 2, column = 0, sticky = 'e')

    # The title of the terminal
    titleLabelMininet = ttk.Label(mininetFrame, text="Mininet CLI", background = "lightgray", font=("Helvetica", 14))
    titleLabelMininet.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    # The actual frame of the terminal
    termf2 = ttk.Frame(mininetFrame, height=400, width=900)
    termf2.pack(side = 'top')
    # To add the controller Ryu output logs
    wid_mininet = termf2.winfo_id()

    mininetFrame.propagate(False)


    ### HTTP requests to the controller
    httpRequestsFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 100, width = 1800)
    httpRequestsFrame.grid(row = 3, column = 0, sticky = 'we')

    # The title of the terminal
    titleLabelHTTPRequests = ttk.Label(httpRequestsFrame, text="HTTP request to controller", background = "lightgray", font=("Helvetica", 14))
    titleLabelHTTPRequests.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    # Combo Box for selecting the HTTP Requests
    options = ["POST - http://localhost:8080/communication/[src_host]/[dst_host]", "DELETE - http://localhost:8080/communication/[src_host]/[dst_host]", "GET - http://localhost:8080/topology/node/[device]", "GET - http://localhost:8080/debug/show_information"]
    selected_option = tk.StringVar()
    comboboxHTTP = ttk.Combobox(httpRequestsFrame, values=options, textvariable=selected_option, height=6, width=100, font = custom_font_for_combobox)
    comboboxHTTP.pack(side='left', padx=5, pady=5, anchor = 'center')

    # Button to send an HTTP request
    buttonSendRequest = ttk.Button(httpRequestsFrame, text = "Send HTTP Request", style = "RoundedButton.TButton", command=buttonSendHTTPRequest)
    buttonSendRequest.pack(side = "left", anchor = 'w', fill = "none", expand = False, padx = 5, pady = 5)

    httpRequestsFrame.propagate(False)

    window.mainloop()

if __name__ == '__main__':
    main()