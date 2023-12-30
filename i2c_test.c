#include <wiringPiI2C.h>
#include <stdio.h>
#include <string.h>

int main(void) {
  int handle = wiringPiI2CSetup(0x40) ;
  fprintf( stdout, "hello world\n" );
  while (1) {
    sleep(1);  
    int test = 10000;
    char buffer[16];
    snprintf(buffer, sizeof(buffer), "%d\n", test);
    write(1, buffer, strlen(buffer)); 
    wiringPiI2CWrite(handle, 0xF1);
    sprintf(buffer, "--------\n");
    write(1, buffer, strlen(buffer));
    snprintf(buffer, sizeof(buffer), "%d\n",wiringPiI2CRead(handle));
    write(1, buffer, strlen(buffer));  
    snprintf(buffer, sizeof(buffer), "%d\n",wiringPiI2CRead(handle));
    write(1, buffer, strlen(buffer));
    snprintf(buffer, sizeof(buffer), "%d\n",wiringPiI2CRead(handle));
    write(1, buffer, strlen(buffer));
  } 
  return 0;
}
