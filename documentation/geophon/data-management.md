# Backup to Device

```
rsync -v -r pi@raspberrypi:/home/pi/geophon/infra-sound-recorder/data /media/andreas/Volume/geophon/geophon/data
find /media/andreas/Volume/geophon/geophon/data -name \*.csv -exec gzip {} \;
rsync -v -r pi@raspberrypi:/home/pi/geophon/infra-sound-recorder/images /media/andreas/Volume/geophon/geophon/images
```