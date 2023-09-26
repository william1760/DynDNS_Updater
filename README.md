# DynDNS Updater

## Overview

The DynDNS Updater is a Python script that automates the process of updating your DynDNS hostname with your current public IP address. This ensures that your DynDNS hostname always points to the correct IP address, even if it changes over time.

## Features

- Automatic retrieval of current public IP address from configurable DNS resolvers.
- Update DynDNS hostname with the current IP address.
- Flexible scheduling options for periodic updates.
- Key management for secure authentication with DynDNS service.
- Enhance portability, isolation, and reproducibility by running in a Docker image.

## Prerequisites

Before running the script, make sure you have the following dependencies installed:

- Python 3.x
- Docker

## Setup

The DynDNS Updater operates within a Docker image, automatically checking for IP changes every 15 minutes by default. You have the option to manually build the image using the provided `dockerfile`, or utilize `DockerCtrl.py` for streamlined setup.

Configuration settings are defined in the `DockerCtrl.config` file, including the `restart_policy` for the Docker container."

```bash
python DockerCtrl.py --build-image
```

You can also use "DockerCtrl.py" to manage the image

### Command-line Arguments
- `--build-image`: Build the Docker image.
- `--remove-image`: Remove the Docker image and its associated container.
- `--start`: Start the Docker container.
- `--attach`: Attach to the Docker container.
- `--stop`: Stop the Docker container.
- `--interactive`: Start the Docker container in interactive mode.
- `--status`: Show the status of the Docker image and container.
- `--cmd` <command>: Provide a custom command to run inside the Docker container.
- `--setup`: Set up the Docker container with the specified configuration.

### Examples
```bash
#Start Docker Container
python DockerCtrl.py --start

#Start interactive mode to a running Docker Container 
python DockerCtrl.py --attach

#Run Docker Container as interactive mode
python DockerCtrl.py --start --attach

#Run Custom Command
python DockerCtrl.py --cmd "python main.py"

#Set Up Docker Container
python DockerCtrl.py --setup
```

## Configuration

Edit the `main.config` file with your desired dyndns domain.

```bash
- `HOSTNAME`: Your DynDNS hostname.
```

## Usage

### Running the Script

```bash
python main.py
```

### Command-line Arguments

- `--run-now`: Run the update process immediately.
- `--interval <minutes>`: Set the update interval in minutes (default: 5).
- `--force`: Force an update even if the IP address has not changed.
- `--status`: Print the current status without performing an update.
- `--setup`: Set up and manage authentication keys.

### Examples
```bash
# Run an immediate update
python main.py --run-now

# Set a custom update interval of 10 minutes
python main.py --interval 10

# Force an update even if the IP address hasn't changed
python main.py --run-now --force

# Print the current status
python main.py --status

# Set up and manage authentication keys
python main.py --setup
```