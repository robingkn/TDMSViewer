# TDMS Viewer

A desktop GUI tool built with Python and Tkinter to **browse, inspect, and visualize** National Instruments' `.tdms` files. This viewer supports **large files** with **incremental loading** and **page-based navigation** of channel data.

## ✨ Features

- Open and read `.tdms` files using `nptdms`
- Interactive tree structure for File → Group → Channel navigation
- Property panel for file, group, and channel metadata
- Channel data preview table (100 points per page, paginated)
- Line plot of channel data with auto-refresh
- Navigation controls:
  - Page forward (`>`), backward (`<`), and jump to a specific page
  - Fixed position, stays visible on window resize

## 📦 Installation

Make sure you have Python 3.7 or later installed.

```bash
pip install nptdms matplotlib
