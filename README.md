# Delta RPI M8A RS485 simulator

Thanks to the https://github.com/lvzon/soliviamonitor/ project which helped
in the protocol understanding and crc checking algorithm.

## Usage

The `delta_rpi_m8a_simulator.py` script should be run with Python3 only (as the
script is not compatible with Python2).

The script can either work as an Delta RPI M8A RS485 simulator (slave mode) or
as a simple datalogger (master mode).

See the usage message below:

```
    $ python3 delta_rpi_m8a_simulator.py -h
    usage: delta_rpi_m8a_simulator.py [-h] [-a ADDRESS] [-d DEVICE] [-b BAUDRATE]
                                      [-t TIMEOUT] [--debug]
                                      MODE
    
    Delta inverter simulator (slave mode) or datalogger (master mode) for RPI M8A
    
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

So to simulate an inverter (with rs485 address=1, serial port=/dev/ttyUSB0,
baud rate=9600), you can run:

```
    $ python3 delta_rpi_m8a_simulator.py -d /dev/ttyUSB0 -b 9600 -a 1 slave
```

And to act as a datalogger and retrieve data of an inverter (with rs485
address=1, serial port=/dev/ttyUSB0, baud rate=9600), you can run:

```
    $ python3 delta_rpi_m8a_simulator.py -d /dev/ttyUSB0 -b 9600 -a 1 master
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
the `delta_rpi_m8a_simulator.py` script in both master and slave mode.

Run the script in slave mode (inverter simulator) in a first terminal:
```
    $ python3 delta_rpi_m8a_simulator.py -d /dev/pts/2 -b 9600 -a 1 slave
```

Run the script in master mode in a second terminal:
```
    $ python3 delta_rpi_m8a_simulator.py -d /dev/pts/3 -b 9600 -a 1 master
```

You should now see the slave and master sending/receiving dummy data.
