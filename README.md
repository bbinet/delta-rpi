# Delta RPI M8A RS485 simulator

Thanks to the https://github.com/lvzon/soliviamonitor/ project which has
provided the crc checking code and a little shell-script that will put a device
into raw-mode and will undefine all special control characters on the specified
device, e.g.: `./unset_serial_ctrlchars.sh /dev/ttyRPC0`

## Usage

The `delta-rpi.py` script should be run with Python3 only (as the
script is not compatible with Python2).

The script can either work as an Delta RPI M8A RS485 simulator (slave mode) or
as a simple dataviewer (master mode).

See the usage message below:

```
    $ python3 delta-rpi.py -h
    usage: delta-rpi.py [-h] [-a ADDRESS] [-d DEVICE] [-b BAUDRATE]
                                      [-t TIMEOUT] [--debug]
                                      MODE
    
    Delta inverter simulator (slave mode) or dataviewer (master mode) for RPI M8A
    
    positional arguments:
      MODE         mode can either be "master" or "slave"
    
    optional arguments:
      -h, --help   show this help message and exit
      -a ADDRESS   slave address [default: 1]
      -d DEVICE    serial device port [default: /dev/ttyUSB0]
      -b BAUDRATE  baud rate [default: 9600]
      -t TIMEOUT   timeout, in seconds (can be fractional, such as 1.5) [default:
                   2.0]
      --debug      show debug information
```

So to simulate an inverter on a RaspberryPi with Raspicomm RS485 adapter
(with rs485 address=1, serial port=/dev/ttyRPC0, baud rate=9600), you can run:

```
    $ python3 delta-rpi.py -d /dev/ttyRPC0 -b 9600 -a 1 slave
```

And to act as a dataviewer and retrieve data from an inverter on a RaspberryPi
with Raspicomm RS485 adapter (with rs485 address=1, serial port=/dev/ttyRPC0,
baud rate=9600), you can run:

```
    $ python3 delta-rpi.py -d /dev/ttyRPC0 -b 9600 -a 1 master
```

## Testing both slave and master modes

You can easily test the simulator by using virtual serial ports that you can
create using socat:

```
    $ socat -d -d pty,raw,echo=0 pty,raw,echo=0
    2017/07/05 14:27:51 socat[12075] N PTY is /dev/pts/2
    2017/07/05 14:27:51 socat[12075] N PTY is /dev/pts/3
    2017/07/05 14:27:51 socat[12075] N starting data transfer loop with FDs [3,3] and [5,5]
```

You can now use the `/dev/pts/2` and `/dev/pts/3` virtual serial ports to run
the `delta-rpi.py` script in both master and slave mode.

Run the script in slave mode (inverter simulator) in a first terminal:
```
    $ python3 delta-rpi.py -d /dev/pts/2 -b 9600 -a 1 slave
```

Run the script in master mode in a second terminal:
```
    $ python3 delta-rpi.py -d /dev/pts/3 -b 9600 -a 1 master
```

You should now see the slave and master sending/receiving dummy data.
