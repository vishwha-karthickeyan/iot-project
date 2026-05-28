# AI IoT Backend

This project is an AI-powered IoT backend for a temperature sensor system. It collects temperature data over MQTT, analyzes it using local anomaly detection and Google Gemini generative AI, stores results in a MySQL database, publishes processed data back to MQTT, and exposes a FastAPI HTTP/WebSocket interface.

## Project Structure

- `main.py` - FastAPI backend, MQTT subscriber, AI processing pipeline, WebSocket broadcast, and REST endpoints.
- `database.py` - SQLAlchemy models and database setup.
- `auth.py` - JWT authentication and password hashing utilities.
- `requirements.txt` - Python dependencies.
- `Simple_temp_sensor_project/Simple_temp_sensor_project.ino` - ESP8266 Arduino sketch that reads a DS18B20 temperature sensor and publishes to MQTT.

## Features

- MQTT ingestion of temperature readings from the ESP8266 sensor client.
- Local anomaly detection with `IsolationForest`.
- Trend analysis for temperature changes.
- Cloud AI insights via Google Gemini.
- Secure user registration and login with JWT.
- Database storage of sensor readings and AI messages.
- WebSocket broadcast for real-time updates.

## Requirements

- Python 3.10+ (recommended)
- MySQL-compatible database
- MQTT broker with TLS support
- Google Gemini API key
- ESP8266-compatible hardware and DS18B20 temperature sensor for the Arduino client

## Installation

1. Clone the repository or copy the project files.
2. Create and activate a Python virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following values:

```env
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>
MQTT_BROKER=<mqtt-broker-host>
MQTT_PORT=8883
MQTT_USERNAME=<mqtt-username>
MQTT_PASSWORD=<mqtt-password>
JWT_SECRET=<your-jwt-secret>
GEMINI_API_KEY=<your-google-gemini-api-key>
```

## Running the Backend

Start the API server with Uvicorn:

```powershell
uvicorn main:app --reload
```

The backend should be available at `http://127.0.0.1:8000`.

## Available Endpoints

- `GET /` - Health check.
- `POST /register` - Register a new user.
- `POST /login` - Authenticate and receive a JWT token.
- `GET /latest` - Retrieve the latest sensor data (requires authentication).

## MQTT Topics

- Subscribe topic: `iot/farm/data` - raw sensor payloads from the ESP8266.
- Publish topic: `iot/processed` - processed output including anomaly status, trend, and AI message.

## Arduino Client

The `Simple_temp_sensor_project/Simple_temp_sensor_project.ino` sketch connects an ESP8266 to WiFi and publishes JSON temperature payloads to the MQTT broker. Update the WiFi and MQTT credentials before uploading.

## Notes

- Keep sensitive values out of source control by using `.env`.
- The project currently uses the Google Gemini generative AI service for natural language insights.
- Database schema is created automatically on startup using SQLAlchemy.

## Troubleshooting

- Verify `DATABASE_URL` is correct and reachable.
- Confirm MQTT broker credentials and TLS settings are valid.
- Ensure the Google Gemini API key is enabled and has quota.
- Check the Arduino sketch WiFi/MQTT settings before flashing.
