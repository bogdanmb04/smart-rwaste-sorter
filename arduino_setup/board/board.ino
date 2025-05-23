#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include <Stepper.h>
#include "arduino_secrets.h"

const int cyanChannel = 9;
const int yellowChannel = 11;
const int magentaChannel = 10;
const int stepsPerRevolution = 384;

enum Position { BLUE = 0, YELLOW = 1, GREEN = 2 };
int currentSlot = BLUE;

const int slotSteps[] = {
  0 * stepsPerRevolution,   // BLUE
  1 * stepsPerRevolution,   // YELLOW
  2 * stepsPerRevolution,   // GREEN
};

String previousResponse = "";

char ssid[] = MY_SECRET_SSID;
char pass[] = MY_SECRET_PASSWORD;
char serverAddress[] = "192.168.139.175";
int port = 5000;

WiFiClient wifi;
HttpClient client = HttpClient(wifi, serverAddress, port);

Stepper myStepper = Stepper(stepsPerRevolution, 4, 5, 6, 7);

void setup()
{
  Serial.begin(9600);
  pinMode(cyanChannel, OUTPUT);
  pinMode(yellowChannel, OUTPUT);
  pinMode(magentaChannel, OUTPUT);
  connectToWiFi();
}

void loop()
{
  if(WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }
  
  myStepper.setSpeed(20);


  Serial.println("Starting GET request:");
  client.beginRequest();
  client.get("/class");
  client.endRequest();
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();
  response.trim();

  Serial.print("Status code: ");
  Serial.println(statusCode);
  Serial.print("Response: ");
  Serial.println(response);

  if (statusCode > 0) {
    if(response != previousResponse) {
      if(response == "paper" || response == "cardboard") {
        setColor(255, 255, 0);
        moveTo(BLUE);
      }
      if(response == "metal" || response == "plastic") {
        setColor(0, 0, 255);
        moveTo(YELLOW);
      }
      if(response == "glass") {
        setColor(255, 0, 255);
        moveTo(GREEN);
      }
    }
    if(response == "idk") {
      setColor(0, 0, 0);
    }

    previousResponse = response;
  }
  else {
    Serial.println("HTTP request failed");
  }
  delay(300);
}

void moveTo(Position target) {
  if (target == currentSlot) return;

  int deltaSlots = int(target) - currentSlot;

  int stepsToMove = deltaSlots * stepsPerRevolution;
  myStepper.step(stepsToMove);
  currentSlot = target;
}

void turnLEDOff() {
  digitalWrite(cyanChannel, LOW);
  digitalWrite(magentaChannel, LOW);
  digitalWrite(yellowChannel, LOW);
}

void setColor(int cyanValue, int magentaValue,  int yellowValue) {
  analogWrite(cyanChannel, cyanValue);
  analogWrite(magentaChannel,  magentaValue);
  analogWrite(yellowChannel, yellowValue);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi...");
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.print("\n");
  Serial.println("Connected to WiFi!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}