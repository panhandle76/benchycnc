# benchycnc
linuxcnc configuration for Avid benchtop CNC

Testing with simulated limit switches/probes
user@debian:~$ sim_pin axis.0.home-sw-in axis.1.home-sw-in axis.2 axis.2.home-sw-in motion.probe-input

Run showport to set the EPP mode after linuxcnc is running
sudo ./showport e010 e000 e
