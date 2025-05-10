#include <WiFiS3.h>
#include <ArduinoHttpClient.h>
#include "arduino_secrets.h"

const int cyanChannel = 11;
const int yellowChannel = 9;
const int magentaChannel = 10;

String previousResponse = " ";

char ssid[] = MY_SECRET_SSID;
char pass[] = MY_SECRET_PASSWORD;
char serverAddress[] = "192.168.74.175";
int port = 5000;

WiFiClient wifi;
HttpClient client = HttpClient(wifi, serverAddress, port);

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
      }
      if(response == "metal" || response == "plastic") {
        setColor(0, 0, 255);
      }
      if(response == "glass") {
        setColor(255, 0, 255);
      }
    }
    previousResponse = response;
  }
  else {
    Serial.println("HTTP request failed");
  }
  delay(300);
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