import os
import json
import threading
import time
import asyncio
import google.generativeai as genai
import paho.mqtt.client as mqtt

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from sklearn.ensemble import IsolationForest

from database import get_db, SessionLocal, SensorData, User
from auth import get_password_hash, verify_password, create_access_token, get_current_user

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="AI IoT Backend 🚀")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- CONFIG ----------------
BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", 8883))
TOPIC_SUB = "iot/farm/data"
TOPIC_PUB = "iot/processed"
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")

# AI Config (Google Gemini - Cloud Based, Low Resource)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-2.0-flash')

# ---------------- AI MEMORY ----------------
temp_buffer = []
iso_model = IsolationForest(contamination=0.1)
model_trained = False

# ---------------- WEBSOCKET ----------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
main_loop = None

# ---------------- AI FUNCTIONS ----------------

def detect_anomaly(temp):
    global temp_buffer, iso_model, model_trained
    if temp is None: return "ERROR"
    
    temp_buffer.append([temp])
    if len(temp_buffer) >= 20 and not model_trained:
        iso_model.fit(temp_buffer)
        model_trained = True

    if model_trained:
        pred = iso_model.predict([[temp]])
        return "ANOMALY" if pred[0] == -1 else "NORMAL"
    return "LEARNING"

def detect_trend(temp):
    if len(temp_buffer) < 5: return "STABLE"
    temps = [t[0] for t in temp_buffer[-5:]]
    diff = temps[-1] - temps[0]
    if diff > 2: return "RISING" # Adjusted sensitivity
    elif diff < -2: return "FALLING"
    return "STABLE"

def get_gemini_insight(temp, status, trend):
    """Generates human-like advice using Cloud AI"""
    if status == "LEARNING":
        return "🤖 AI is calibrating patterns. Keep sending data..."
    
    try:
        # Prompting the AI with context
        prompt = (f"Act as a smart farm assistant. Current temp: {temp}C. "
                  f"Status: {status}. Trend: {trend}. "
                  "Give one short, helpful advice for the farmer (max 15 words).")
        
        response = ai_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "✅ Monitoring active. Temperature stable."

# ---------------- MQTT ----------------
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(USERNAME, PASSWORD)
mqtt_client.tls_set()

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected:", rc)
    client.subscribe(TOPIC_SUB)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temp = data.get("temperature")

        # 1. Local AI (Statistical)
        status = detect_anomaly(temp)
        trend = detect_trend(temp)

        # 2. Generative AI (Cloud Reasoning)
        ai_msg = get_gemini_insight(temp, status, trend)

        # 3. Save to DB
        db = SessionLocal()
        new_entry = SensorData(temperature=temp, status=status, trend=trend, ai_message=ai_msg)
        db.add(new_entry)
        db.commit()
        db.close()

        processed_data = {
            "temperature": temp,
            "status": status,
            "trend": trend,
            "ai_message": ai_msg,
            "timestamp": time.time()
        }

        # 4. Publish & Broadcast
        mqtt_client.publish(TOPIC_PUB, json.dumps(processed_data))
        if main_loop:
            asyncio.run_coroutine_threadsafe(manager.broadcast(processed_data), main_loop)

    except Exception as e:
        print("❌ Error processing MQTT message:", e)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    try:
        mqtt_client.connect(BROKER, PORT)
        mqtt_client.loop_forever()
    except Exception as e:
        print("❌ MQTT Thread Error:", e)

threading.Thread(target=start_mqtt, daemon=True).start()

# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup():
    global main_loop
    main_loop = asyncio.get_running_loop()

# ---------------- ROUTES ----------------
@app.get("/")
def home():
    return {"message": "AI IoT Backend with Gemini Integration is Live 🚀"}

@app.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    username, password = data.get("username"), data.get("password")
    if not username or not password: raise HTTPException(status_code=400, detail="Invalid data")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="User exists")
    
    user = User(username=username, password=get_password_hash(password))
    db.add(user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.get("username")).first()
    if not user or not verify_password(data.get("password"), user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_access_token({"id": user.id})}

@app.get("/latest")
def latest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SensorData).order_by(SensorData.created_at.desc()).first()

# ---------------- WEBSOCKET ----------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)