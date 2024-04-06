= Compile Service for Infra-Sound-Recoder

== Install neccessary requirements

sudo apt install i2c-tools

== Manual Install
cc i2c_read_test.c -li2c
cc i2c_read_test.c -lwiringPi -li2c
rsync -v --remove-source-files -r -d pi@raspberrypi:/home/pi/i2c/data/ . 

== Automatic install
cd sensor-control
autoconf
autoreconf --install

= Install service for the geophon

== Install requirements
python3 -m pip numpy matplotlib

== Copy service file to systemd folder
cd geophon/infra-sound-recoder/service
sudo cp infra-service.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable infra-service
sudo systemctl start infra-service

= Install web-service for the geophon

== Install requirements
python3 -m pip numpy matplotlib httpserver

== Copy service file to systemd folder
cd geophon/infra-sound-recoder/web-service
sudo cp web-service.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable web-service
sudo systemctl start web-service
