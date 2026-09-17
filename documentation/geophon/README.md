# General Information

A Geophon measures in three dimensions, so fo a clear picture 

# Technical components

I use a 16bit ADC for I2C. This brings several limitations so it would be better to use a 32bit ADC with SPI.

The limitations are especially:
* limited frequency range due to limited I2C-bandwidth and measurement speed.
* limited accuracy due to limited realime accuracy of python
* only two geophons can be connected due to support of two I2C-Channels in Raspberry-PI (could be improved) 

Component list:
* ADC
* Geophon

# Legislation Background

* Big M
* Tables from the Norm

# Usefaull Formulas

* 80 V/m/s -> 0.08V/mm/s
* 0,1 mm/s equals to 0.008 V
* with a scale or 0,256V / 32700 this corresponds to 1000 units 