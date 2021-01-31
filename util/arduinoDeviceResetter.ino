/** file: arduinoDeviceResetter.cpp
 *  Descr: 
 *    A super simple arduino script to reset the STM with a usb command
 *    Runs on a sep. USB port. Should have a 3v3 signal. Connect can be direct but 
 *    using a transistor switch would be preferable. 
 * 
 */

const int OUTPIN = 18;

void setup() {
  // put your setup code here, to run once:
  pinMode(OUTPIN, OUTPUT);
  digitalWrite(OUTPIN, HIGH);

  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available() > 1) {
    int a = Serial.read();
    if(a == 0x33){    /* test script calls serial.write(0x33) to reset the stm32 */
      digitalWrite(OUTPIN, LOW);
      delay(10);
      digitalWrite(OUTPIN, HIGH);
    }
  }
}