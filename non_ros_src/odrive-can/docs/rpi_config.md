# Raspberry Pi Configuration

*Setup on a Raspberry Pi Machine for Waveshare 2-CH CAN HAT*

!!! note
    installation scripts are found in `install` directory

## 1. Prepare system

Prepare freshly installed rpi (docker etc.)

`prepare_system.sh`


## 2. Install CAN hat

**See waveshare docs:** [waveshare hat docs](https://www.waveshare.com/wiki/2-CH_CAN_HAT)

`install_bcm2535.sh`


## 3. install can service

to automatically bringup interface on system startup

`setup_can.sh`


## Test the CAN-bus with the can-utils Program

### Install can-utils:

```bash
sudo apt-get install can-utils
```

### Send a CAN Message:

```bash
cansend [interface] [id HEX]#[DATA 8 bytes HEX]
cansend can0 456#00FF010203040506
```

---


--8<-- "install/README.md"
