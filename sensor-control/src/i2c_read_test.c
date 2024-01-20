#include <string.h>
#include <stdarg.h> 
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <asm/ioctl.h>
#include <fcntl.h>
#include <linux/i2c.h>
#include <stdint.h>
#include <i2c/smbus.h> 
#include <math.h>
#include <time.h>
#include <sys/time.h>
#include <errno.h>
#include <signal.h>

static volatile int keepRunning = 1;

void intHandler(int dummy) {
    keepRunning = 0;
}

#ifndef	TRUE
#  define	TRUE	(1==1)
#  define	FALSE	(!TRUE)
#endif
#define I2C_SMBUS_READ	1
#define I2C_SMBUS_WRITE	0
#define I2C_SMBUS_BYTE_DATA	    2
#define I2C_SMBUS_WORD_DATA	    3
int wiringPiReturnCodes = FALSE ;

#define	WPI_FATAL	(1==1)

/*
 * wiringPiFailure:
 *	Fail. Or not.
 *********************************************************************************
 */

int wiringPiFailure (int fatal, const char *message, ...)
{
  va_list argp ;
  char buffer [1024] ;

  if (!fatal && wiringPiReturnCodes)
    return -1 ;

  va_start (argp, message) ;
    vsnprintf (buffer, 1023, message, argp) ;
  va_end (argp) ;

  fprintf (stderr, "%s", buffer) ;
  exit (1) ;

  return 0 ;
}

/*
 * wiringPiI2CWrite:
 *	Simple device write
 *********************************************************************************
 */

int wiringPiI2CWrite (int fd, int data)
{
  return i2c_smbus_access (fd, I2C_SMBUS_WRITE, data, I2C_SMBUS_BYTE, NULL) ;
}

/*
 * wiringPiI2CRead:
 *	Simple device read
 *********************************************************************************
 */

int wiringPiI2CRead (int fd)
{
  union i2c_smbus_data data ;

  if (i2c_smbus_access (fd, I2C_SMBUS_READ, 0, I2C_SMBUS_BYTE, &data))
    return -1 ;
  else
    return data.byte & 0xFF ;
}

void calcCRC(uint8_t value, uint8_t *crc)
{
  const uint8_t POLY = 0x31;   // Polynomial: x**8 + x**5 + x**4 + 1
  int8_t i;
  *crc ^= value;
  for (i = 8; i > 0; i--)
  {
    if (*crc & 0x80)
      *crc = (*crc << 1) ^ POLY;
    else
      *crc = (*crc << 1);
  }
}

int _scaleFactor = 12;

void setResolution(int handle, uint8_t res){
	uint8_t msb=0b01110001; // bit 2-4 define resolution
	uint8_t lsb=0b10000010;
	if(res<9 || res>16) res=12;
	res-=9;
	msb|=(res<<1); // set bits 2-4 for selected resolution
 printf("#new MSB Resolution: %d\n", msb);
  i2c_smbus_write_word_data(handle, 0xE4, (lsb <<8) | msb);
  _scaleFactor = 14;
}


float measureWord2(int handle) {
  int result = i2c_smbus_read_word_data(handle, 0xe5);
  if (result < 0)
    return NAN;
  return result / 12;
}

float measureWord(int handle) {
  wiringPiI2CWrite(handle, 0xe5);
  int value = wiringPiI2CRead(handle);
  return 1.0/_scaleFactor*value;
}

float measureByte(int handle) {
  wiringPiI2CWrite(handle, 0xe5);
  uint8_t msb = wiringPiI2CRead(handle);
  uint8_t lsb = wiringPiI2CRead(handle);
  uint8_t crc = wiringPiI2CRead(handle);
      uint8_t _crc = 0;// Initialize CRC calculation
            calcCRC(msb, &_crc);
      calcCRC(lsb, &_crc);
if (_crc!=crc){
        printf("CRC calculation failed");
        return NAN;
    }
    short val=(msb<<8)|lsb;
    return 1.0/_scaleFactor*val;
}

float measure(int handle) {
    uint8_t dataArray[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0,0,0,0,0,0,0};
    int32_t val = i2c_smbus_read_i2c_block_data(handle, 0xF1, 3, &dataArray[0]);
    if(val < 0) {
      printf("Error read_block_data %d\n", val);
    return wiringPiFailure (WPI_FATAL, "Error read block data", strerror (errno)) ;
      return NAN;
    } else {
      uint8_t _crc = 0;// Initialize CRC calculation
      calcCRC(dataArray[0], &_crc);
      calcCRC(dataArray[1], &_crc);
      if (_crc!=dataArray[2]) {
        printf("CRC calculation failed");
        return NAN;
      }
    }
    short value=(dataArray[0]<<8)|dataArray[1];
    //printf("value %d -> %u,%u\n", value, dataArray[0], dataArray[1]);
    return 1.0 / _scaleFactor * value;
}

void measureLoop(int handle) {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  unsigned long long millisecondsSinceEpochLast =
        (unsigned long long)(tv.tv_sec) * 1000 +
        (unsigned long long)(tv.tv_usec) / 1000;
 
  while (keepRunning) {
    printf("%f;%llu\n", measure(handle), millisecondsSinceEpochLast);
    gettimeofday(&tv, NULL);
    unsigned long long millisecondsSinceEpoch =
        (unsigned long long)(tv.tv_sec) * 1000 +
        (unsigned long long)(tv.tv_usec) / 1000;
    // printf("%llu\n", millisecondsSinceEpoch);
    long diff = millisecondsSinceEpoch - millisecondsSinceEpochLast;
    if (diff < 10) {
     usleep((10 - diff)*1000);
     millisecondsSinceEpochLast = millisecondsSinceEpoch + 10 - diff; 
    }  else {
      millisecondsSinceEpochLast = millisecondsSinceEpoch;
    }
  }
}

#define	WPI_ALMOST	(1==2)
#define I2C_SLAVE	0x0703
#define I2C_SMBUS	0x0720	/* SMBus-level access */

#define I2C_SMBUS_READ	1
#define I2C_SMBUS_WRITE	0


/*
 * wiringPiI2CSetupInterface:
 *	Undocumented access to set the interface explicitly - might be used
 *	for the Pi's 2nd I2C interface...
 *********************************************************************************
 */

int wiringPiI2CSetupInterface (const char *device, int devId)
{
  int fd ;

  if ((fd = open (device, O_RDWR)) < 0)
    return wiringPiFailure (WPI_ALMOST, "Unable to open I2C device: %s\n", strerror (errno)) ;

  if (ioctl (fd, I2C_SLAVE, devId) < 0)
    return wiringPiFailure (WPI_ALMOST, "Unable to select I2C device: %s\n", strerror (errno)) ;

  return fd ;
}


/*
 * wiringPiI2CSetup:
 *	Open the I2C device, and regsiter the target device
 *********************************************************************************
 */

int wiringPiI2CSetup (const int devId)
{
  const char* device = "/dev/i2c-1" ;

  return wiringPiI2CSetupInterface (device, devId) ;
}

int main(void) {
signal(SIGINT, intHandler);
  char buffer[32]; 
  int handle = wiringPiI2CSetup(0x40) ;
  wiringPiI2CWrite(handle, 0xFE);
  sleep(1);
  setResolution(handle, 12);
  sleep(1);
    wiringPiI2CWrite(handle, 0xe5);
    sprintf(buffer, "#--------\n");
    write(1, buffer, strlen(buffer));
    union i2c_smbus_data data;

    unsigned char dataArray[] = {0,0,0,0,0,0,0,0,0,0,0,0}; 
    int32_t val1 = i2c_smbus_read_i2c_block_data(handle, 0xe5, 3, &dataArray[0]);
    if(val1 < 0) {
      snprintf(buffer, sizeof(buffer), "Error read_block_data %d\n", val1);
    } else {
      uint8_t _crc = 0;// Initialize CRC calculation
      printf("#-------------\n");
      printf("#MSB: %d\n", dataArray[0]);
      printf("#LSB: %d\n", dataArray[1]);
      printf("#CRC-IN: %d\n", dataArray[2]);
      printf("#-------------\n");
      calcCRC(dataArray[0], &_crc);
      calcCRC(dataArray[1], &_crc);
      printf("#CRC:%d\n#------------------------\n", _crc);
    }
  measureLoop(handle);
  return 0;
}
