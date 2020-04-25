const int OUTPIN = 18;

void setup() {
  // put your setup code here, to run once:
  pinMode(OUTPIN, OUTPUT);
  digitalWrite(OUTPIN, HIGH);

  Serial.begin(9600);
}

static int state = 0;

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available() > 1) {
    int a = Serial.read();
    if(a == 0x33){
      digitalWrite(OUTPIN, LOW);
      delay(10);
      digitalWrite(OUTPIN, HIGH);
    }
  }
}