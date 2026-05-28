#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ---------------- WIFI ----------------
const char* ssid = "ACT114643224794";
const char* password = "11358643";

// ---------------- MQTT ----------------
const char* mqtt_server = "1164b049982d4ae3a301120d7e27c58b.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "vishwha";
const char* mqtt_pass = "Vish@1310";
const char* topic = "iot/farm/data";

// ---------------- TEMP SENSOR ----------------
#define ONE_WIRE_BUS 2  // D4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ---------------- CLIENTS ----------------
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ---------------- WIFI ----------------
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n WiFi Connected");
}

// ---------------- MQTT ----------------
void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    String clientId = "ESP8266-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println(" MQTT Connected");
    } else {
      Serial.print(" Failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);
  sensors.begin();

  connectWiFi();

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
}

// ---------------- LOOP ----------------
void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();

  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);

  if (tempC != DEVICE_DISCONNECTED_C) {

    String payload = "{";
    payload += "\"temperature\":";
    payload += tempC;
    payload += "}";

    Serial.println("📤 " + payload);

    client.publish(topic, payload.c_str());
  } else {
    Serial.println("❌ Sensor error");
  }

  delay(5000);
}