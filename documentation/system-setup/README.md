# Wifi Setup

For setup of the 8188 Realtek i used the information from the following links.

I ended up with the following driver options:

```
echo "options 8188eu rtw_drv_log_level=4 rtw_led_ctrl=0 rtw_vht_enable=2 rtw_power_mgnt=0 rtw_beamform_cap=10  rtw_dfs_region_domain=0 rtw_sel_p2p_iface=0 rtw_switch_usb_mode=1" > /etc/modprobe.d/wifi-8188.conf
```

Pls keep in mind that the stick consumes up to 500mA which is very much power.

# Bluetooth Setup

# RTC Setup

* https://www.raspberry-pi-geek.de/ausgaben/rpg/2015/03/echtzeituhr-modul-ds3231-sorgt-fuer-genaue-zeitangaben/
* https://forums.freebsd.org/threads/using-both-i2c_arm-and-i2c_vc-on-rpi4b.83516/
* https://forum.arduino.cc/t/cant-get-ds3231-rtc-to-work/384744
* https://pimylifeup.com/raspberry-pi-rtc/
* https://forums.raspberrypi.com/viewtopic.php?t=187092
* https://forums.raspberrypi.com/viewtopic.php?t=334826
* https://forums.raspberrypi.com/viewtopic.php?t=213312