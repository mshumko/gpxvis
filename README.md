# gpxvis

This project documents my learning experience with the following three topics:

1. organizing a package to share with others, resolve dependencies, and ultimately share the package on PyPI,
2. creating a desktop and a web-based graphical user interface (GUI), and
3. working with plotly and MapBox to plot beautiful maps.

This is a project under construction aimed at analyzing a single gpx track file for endurance athletes to nerd over. The **three main goals** of this project are:
- Plot the track on a topo map (or street map),
- Calculate "Basic Statistics" about the gpx track, and 
- Flexibly analyze various parameters, e.g. heart rate vs speed or heart rate vs. inclination.

The project will be **implemented** with a **web-based** and **browser-based** GUI and I will explore the advantages and disadvantages of each tool.

# Install
To install call these commands:
```
python3.8 -m venv env
source env/bin/activate
pip3.8 install -r requirements.txt
```

# TO-DO
- [ ] 

# Lessons Learned 
## Structuring a Package
1. __init__.py makes this a standard package (a folder with multiple files) and not a module (a single .py file). You can use this file to automatically import the submodules so the user does not have to.
2. The __main__.py file is a special file that only gets called when you call the module specifically. In other words, call gpxvis with ```python3 -m gpxvis```. This file can be used to set up
data file directories and write to a config.json file, for example.
3. Pip can be used to install local packages and not just from PyPi. For example, the requirements.txt file has been organized to install the dependencies from PyPi first, then followed by installing this package with the ```-e``` flag to make it editable without reinstalling gpxvis after every source code update.

