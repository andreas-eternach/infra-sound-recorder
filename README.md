sudo apt install i2c-tools

cc i2c_read_test.c -li2c

cc i2c_read_test.c -lwiringPi -li2c
rsync -v --remove-source-files -r -d pi@raspberrypi:/home/pi/i2c/data/ . 

autoconf
autoreconf --install

