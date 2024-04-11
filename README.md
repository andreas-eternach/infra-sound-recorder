# Compile Service for Infra-Sound-Recoder

This project contains a collection of tools for analyzing infra-sound. It was born when experiencing noise from a distant infra-sound-source.

This project is inspired by the work of many other people (see credits below).

There is a lot of theory about infra-sound and the involved issues, caused by the sound and the vivbrations. Actually infra-sound is in 
most cases a surface acoustic wave (https://en.wikipedia.org/wiki/Surface_acoustic_wave). Therefore measuring it requires measurement of
structure-borne and airborne noise. From these measurements one can estimate the intensity, distance, and direction of the noise.

The ariborne noise is measured with a difference-pressure-sensor, see ...

The strucutre-borne noise is measured with a geophon, see ... 

Both sensors (difference-pressure and geophon) are assembled with Peapberry-PIs. For assembly-instructions check the sub-pages.

When this project evolved, it became especially important to get a near-realtime, portable sensor-kit, which allows to measure
frequencies and their intensity. Also it became important to derive law-consistent sum-ups for third-octave-frequency-bands.

So the largest effort in this project is the mathemetical analyzation and realtime-recording-code.

Work is still in progress, i hope to extend this project over time, i am currently thinking about:

* migrating from I2C to SPI for the geophon
* recording second and third dimension with the geophon
* building a more resilent geophon with less sensitiv sensors and operational amplifiers 

## General Setup

You need for each sensor a Rasperry-PI. It makes sense to set up Bluetooth in PAN-Mode, which allows you to connect to the sensor from your mobile phone and check real-time-data.

It also makes sense to setup Wifi, you know better probably.

After setting up the system, just wire up the devices and perform the following installation steps.

## Install GIT-Repo

```
sudo apt install gh
gh auth login
git clone ...
```

## Install neccessary requirements

```
sudo apt install i2c-tools
```

## Manual Install
```
cc i2c_read_test.c -li2c
cc i2c_read_test.c -lwiringPi -li2c
rsync -v --remove-source-files -r -d pi@raspberrypi:/home/pi/i2c/data/ . 
```
## Automatic install
```
cd sensor-control
autoconf
autoreconf --install
```
# Install recording-service

This is the recording-service, responsible for communicating with te device and recording the data.

## Install requirements
```
python3 -m pip numpy matplotlib
```
## Geophon : Copy service file to systemd folder
```
cd geophon/infra-sound-recoder/service
sudo cp infra-service.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable infra-service
sudo systemctl start infra-service
```

## Pressure-Sensor : Copy service file to systemd folder
```
cd geophon/infra-sound-recoder/service
sudo cp infrasound-recording-service.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable infrasound-recording-service
sudo systemctl start infrasound-recording-service
```

# Install web-service for the geophon

This is the web-service, responsible for providing the web-interface to access the statistics data.

## Install requirements

```
sudo apt-get install libopenblas-dev
python3 -m pip numpy matplotlib httpserver
```
## Copy service file to systemd folder

```
cd geophon/infra-sound-recoder/web-service
sudo cp web-service.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable web-service
sudo systemctl start web-service
```
# Credits

## Geophon

* https://core-electronics.com.au/guides/geophone-raspberry-pi/
* https://www.bayceer.uni-bayreuth.de/infraschall/