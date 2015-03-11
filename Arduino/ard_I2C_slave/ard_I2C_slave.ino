#include <Wire.h>

//Define slave unique address
#define SLAVE_ADDRESS 0x04

//leds used
#define LED_PIN 13
#define PWM_LED_PIN 3
#define sensor_PIN 0
#define Potentiometer_PIN 1

//Define the length of the message received (add 1 extra for the cmd)
#define DIM 1
boolean ledon = HIGH;
int number = 0;
int read_value;

void setup() {
    
    pinMode(LED_PIN, OUTPUT);
    pinMode(PWM_LED_PIN, OUTPUT);

   Serial.begin(9600);         // start serial for output
    // initialize i2c as slave
    Wire.begin(SLAVE_ADDRESS);
    
    // define callbacks for i2c communication
    Wire.onReceive(receiveData);
    Wire.onRequest(sendData);
    Serial.println("Ready!");
}

void loop() {
    delay(50);
}
 
// callback for received data
void receiveData(int byteCount){
  
  int numOfBytes = Wire.available();
  //display number of bytes and cmd received, as bytes
  Serial.print("len: ");
  Serial.println(numOfBytes);
  
  byte b = Wire.read(); //cmd
  Serial.print("cmd: ");
  Serial.println(b);
  
  int dataBuffer[numOfBytes-1];
  
  //display message received: [pin, R/W, A/D, value]
  for(int i=0; i<numOfBytes-1; i++){
    dataBuffer[i] = Wire.read();
    Serial.println(dataBuffer[i]);
  }
  
  if (dataBuffer[1] == 1){ //that means WRITE
      if(dataBuffer[2] == 0){  //ANALOG write
          analogWrite(dataBuffer[0], dataBuffer[3]);
      }else if(dataBuffer[2] == 1){  //DIGITAL write
          if(dataBuffer[3] == 1) digitalWrite(dataBuffer[0], HIGH); //write [value] in [pin]
          if(dataBuffer[3] == 0) digitalWrite(dataBuffer[0], LOW);
      }
      
      
  }else if(dataBuffer[1] == 0){  //means READ
      if(dataBuffer[2] == 0){  //then ANALOG read
          read_value = analogRead(dataBuffer[0]);
          read_value = map(read_value, 0, 1023, 0, 255);
          Serial.print("sensor: ");
          Serial.println(read_value);
      }else if(dataBuffer[2] == 1){  //then DIGITAL read
          read_value = digitalRead(dataBuffer[0]); //read [pin]
      }  
   } 
}
  

// callback for sending data
void sendData(){
    Wire.write(read_value);
}


void blinkLED(){
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
}

