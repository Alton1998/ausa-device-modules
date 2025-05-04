# ausa-device-modules
## Overview
This repository has a collection of ausa device modules


You can run this against a simulator or an actual device.
## Setup with Iot Edge Simulator

### Pre-requisites
 - Install Python version 3.7.4
 - Install Docker CE
 - Azure CLI


## Setup an IoT Edge Device

### Pre-requisites
- Install Raspbian OS - [tutorial 1](https://www.tomshardware.com/how-to/set-up-raspberry-pi), [tutorial 2](https://www.pitunnel.com/doc/access-vnc-remote-desktop-raspberry-pi-over-internet)

### Setup
```commandline
curl https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb > ./packages-microsoft-prod.deb
sudo apt install ./packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install moby-engine
```

#### Restarting Docker

Open the daemon file
```commandline
sudo nano /etc/docker/daemon.json
```
```json
{
      "log-driver": "local"
}
```
Close the file up
```commandline
sudo systemctl restart docker
```
Installing IoT Edge Runtime
```commandline
sudo apt-get update
sudo apt-get install aziot-edge
```
Open the config file
```commandline
sudo nano /etc/aziot/config.toml
```

Add the following config:
```commandline
# DPS provisioning with X.509 certificate
[provisioning]
source = "dps"
global_endpoint = "https://global.azure-devices-provisioning.net"
id_scope = "SCOPE_ID_HERE"

# Uncomment to send a custom payload during DPS registration
# payload = { uri = "PATH_TO_JSON_FILE" }

[provisioning.attestation]
method = "x509"
registration_id = "REGISTRATION_ID_HERE"

identity_cert = "DEVICE_IDENTITY_CERTIFICATE_HERE" # For example, "file:///var/aziot/device-id.pem"
identity_pk = "DEVICE_IDENTITY_PRIVATE_KEY_HERE"   # For example, "file:///var/aziot/device-id.key"

# auto_reprovisioning_mode = Dynamic
```
Applying the config
```commandline
sudo iotedge config apply
```
## Generating Certificates

