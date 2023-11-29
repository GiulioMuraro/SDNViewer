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

# Socket communication modules
import socket
import pickle
import threading

# IP and port of Ryu App
ipRyuApp = '127.0.0.1'
portRyuApp = 6653

# Function to change the graph displayer
def create_graph_image(netGraph, graphLabel):
    pos = nx.spring_layout(netGraph)

    print(netGraph.nodes)
    
    nx.draw(netGraph, pos, with_labels=True, node_size=500, font_size=10, font_color='black')
    
    # Create a Matplotlib figure and draw the graph on it
    fig = plt.figure(figsize=(3, 3))
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
    
    return photo

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
def button1():
    """ TODO """

def button2():
    """ TODO """


# Main function to execute the SDN GUI
def main():
    # To access global variables
    global wid_mininet
    global wid_output

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
    graphFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 1100)
    graphFrame.grid(row = 0, column = 0, sticky = 'nw')

    # The title of graph section
    titleLabelGraph = ttk.Label(graphFrame, text="Network Graph", background = "lightgray", font=("Helvetica", 14))
    titleLabelGraph.pack(side='top', padx = 5, pady = 5, fill = 'none', expand = False)

    graphLabel = tk.Label(graphFrame, bg = "#C2C2A3", height = 400, width = 1100)
    graphLabel.pack(side = 'top', fill = 'none', expand = False)

    graphFrame.propagate(False)



    ### Top right corner
    detailsViewFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 500, width = 700)
    detailsViewFrame.grid(row = 0, column = 0, sticky = 'ne')

    # The title of the outputTextBox of Ryu
    titleLabelDetails = ttk.Label(detailsViewFrame, text="Details View", background = "lightgray", font=("Helvetica", 14))
    titleLabelDetails.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    detailsTextBox = tk.Text(detailsViewFrame, bg = "#C2C2A3", height = 400, width = 700)
    detailsTextBox.pack(side = 'top', fill = 'none', expand = False)

    #stop the propagation of pack() because the outputRyuFrame resize itself as it wants. It doesn't listen to my will
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

    buttonLoadTopology = ttk.Button(loadTopologyFrame, text = "Load & Run topology", style = "RoundedButton.TButton", command=button1)
    buttonLoadTopology.pack(side = 'left', padx=5, pady=5, anchor = 'center', expand=False)

    loadTopologyFrame.propagate(False)



    ### Ryu output Logs
    ryuFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 300, width = 900)
    ryuFrame.grid(row = 2, column = 0, sticky = 'w')

    # The title of the terminal
    titleLabelRyu = ttk.Label(ryuFrame, text="Ryu controller output", background = "lightgray", font=("Helvetica", 14))
    titleLabelRyu.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    # The actual frame of the terminal
    termf1 = ttk.Frame(ryuFrame, height=300, width=900)
    termf1.pack(side = 'top')
    # To add the controller Ryu output logs
    wid_ryu = termf1.winfo_id()

    ryuFrame.propagate(False)



    ### Mininet CLI terminal
    mininetFrame = ttk.Frame(window, style = 'RoundedFrame.TFrame', height = 300, width = 900)
    mininetFrame.grid(row = 2, column = 0, sticky = 'e')

    # The title of the terminal
    titleLabelMininet = ttk.Label(mininetFrame, text="Mininet CLI", background = "lightgray", font=("Helvetica", 14))
    titleLabelMininet.pack(side='top', fill = 'none', expand = False, padx = 5, pady = 5)

    # The actual frame of the terminal
    termf2 = ttk.Frame(mininetFrame, height=300, width=900)
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
    options = ["http://127.0.0.1:8080/communication/[src_host]/[dst_host]", "Mesh topology", "Long path topology", "AssignOne topology"]
    selected_option = tk.StringVar()
    comboboxHTTP = ttk.Combobox(httpRequestsFrame, values=options, textvariable=selected_option, height=6, width=100, font = custom_font_for_combobox)
    comboboxHTTP.pack(side='left', padx=5, pady=5, anchor = 'center')

    # Button to send an HTTP request
    buttonSendRequest = ttk.Button(httpRequestsFrame, text = "Send HTTP Request", style = "RoundedButton.TButton", command=button2)
    buttonSendRequest.pack(side = "left", anchor = 'w', fill = "none", expand = False, padx = 5, pady = 5)

    httpRequestsFrame.propagate(False)

    window.mainloop()

if __name__ == '__main__':
    main()