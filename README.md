# TDMS Viewer

A desktop GUI tool built with Python and Tkinter to **browse, inspect, and visualize** National Instruments' `.tdms` files. This viewer supports **large files** with **incremental loading** and **page-based navigation** of channel data.

## ✨ Features

- Open and read `.tdms` files using `nptdms`
- Interactive tree structure for File → Group → Channel navigation
- Property panel for file, group, and channel metadata
- Channel data preview table (1000 points per page, paginated)
- Line plot of channel data with auto-refresh
- Navigation controls:
  - Page forward (`>`), backward (`<`), and jump to a specific page
  - Fixed position, stays visible on window resize

## 📦 Installation

Download the latest TDMSViewer installer from the Releases page and run the .exe file to install the application.

![TDMSViewer](https://github.com/user-attachments/assets/779f95cf-c10d-4254-9f7a-caa3f93b99b4)
