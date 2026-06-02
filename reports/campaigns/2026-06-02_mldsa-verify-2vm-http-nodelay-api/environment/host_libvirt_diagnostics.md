# Host and VM diagnostics

## Host
RebelMachine.home
Linux RebelMachine.home 7.0.10-201.fc44.x86_64 #1 SMP PREEMPT_DYNAMIC Wed May 27 13:57:41 UTC 2026 x86_64 GNU/Linux

Repo:
main
adc7ad530c148438dbd336f6c33e6b9879edc593

## Libvirt
 Id   Name                     State
----------------------------------------
 1    pqc-fedora-vm-baseline   running
 2    pqc-fedora-vm-loadgen    running


## SERVER VM dominfo
Id:             1
Name:           pqc-fedora-vm-baseline
UUID:           3e66e2e9-0bb5-477f-ba5b-e6ff6676057e
OS Type:        hvm
State:          running
CPU(s):         8
CPU time:       4585.8s
Max memory:     16777216 KiB
Used memory:    16777216 KiB
Persistent:     yes
Autostart:      disable
Autostart Once: disable
Managed save:   no
Security model: selinux
Security DOI:   0
Security label: system_u:system_r:svirt_t:s0:c144,c715 (enforcing)


## LOADGEN VM dominfo
Id:             2
Name:           pqc-fedora-vm-loadgen
UUID:           55ff7ccc-3e51-4b34-a868-4252cc4b6a05
OS Type:        hvm
State:          running
CPU(s):         4
CPU time:       2977.0s
Max memory:     8388608 KiB
Used memory:    8388608 KiB
Persistent:     yes
Autostart:      disable
Autostart Once: disable
Managed save:   no
Security model: selinux
Security DOI:   0
Security label: system_u:system_r:svirt_t:s0:c846,c927 (enforcing)


## SERVER VM address
 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 lo         00:00:00:00:00:00    ipv4         127.0.0.1/8
 -          -                    ipv6         ::1/128
 enp1s0     52:54:00:3e:96:6f    ipv4         192.168.122.194/24
 -          -                    ipv6         fe80::5054:ff:fe3e:966f/64

 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 vnet0      52:54:00:3e:96:6f    ipv4         192.168.122.194/24


## LOADGEN VM address
 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 lo         00:00:00:00:00:00    ipv4         127.0.0.1/8
 -          -                    ipv6         ::1/128
 enp1s0     52:54:00:f2:60:d4    ipv4         192.168.122.99/24
 -          -                    ipv6         fe80::5054:ff:fef2:60d4/64

 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 vnet1      52:54:00:f2:60:d4    ipv4         192.168.122.99/24
