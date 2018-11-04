void setup() {
 Serial.begin(115200);
}

void loop() {
  int sensorValue0 = analogRead(A0);
  int sensorValue1 = analogRead(A1);
  int sensorValue2 = analogRead(A2);
  int sensorValue3 = analogRead(A3);
  int sensorValue4 = analogRead(A4);
  int sensorValue5 = analogRead(A5);
  char buffer[100];

  sprintf (buffer, "%i %i %i %i %i %i\n",sensorValue0,sensorValue1,sensorValue2,sensorValue3,sensorValue4,sensorValue5);
  Serial.print( buffer );
  delay(1);

}