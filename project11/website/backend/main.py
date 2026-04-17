"""
Backend сервер для емоційного трекера
Приймає дані пульсу від ESP32, обробляє емоційні записи, надає аналітику
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3
import os
from pathlib import Path

from dotenv import load_dotenv

from database import init_db, get_db_connection
from models import PulseData, EmotionEntry, create_tables
import analytics  # Модуль із аналітикою (статистика, звіти)
from ai_advice import generate_ai_advice

# Завантажуємо змінні середовища з кореневого .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Емоційний трекер API", version="1.0.0")

# CORS для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшені обмежити до конкретних доменів
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ініціалізація бази даних
@app.on_event("startup")
async def startup_event():
    init_db()
    create_tables()


# ============= МОДЕЛІ ДАНИХ =============

class PulseDataInput(BaseModel):
    bpm: int
    timestamp: Optional[int] = None
    resting_hr: Optional[int] = None


class EmotionEntryInput(BaseModel):
    emotion: str
    intensity: int  # 1-10
    description: Optional[str] = None


class EmotionEntryResponse(BaseModel):
    id: int
    emotion: str
    intensity: int
    description: Optional[str]
    timestamp: datetime
    pulse_bpm: Optional[int] = None

    class Config:
        from_attributes = True


# ============= API ENDPOINTS =============

@app.get("/")
async def root():
    return {"message": "Емоційний трекер API", "status": "running"}


@app.post("/api/pulse")
async def receive_pulse_data(data: PulseDataInput):
    """Приймає дані пульсу від ESP32 пристрою"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Використовуємо поточний час якщо timestamp не надано
        timestamp = datetime.now()
        if data.timestamp:
            timestamp = datetime.fromtimestamp(data.timestamp)
        
        cursor.execute("""
            INSERT INTO pulse_data (bpm, timestamp, resting_hr)
            VALUES (?, ?, ?)
        """, (data.bpm, timestamp.isoformat(), data.resting_hr))
        
        conn.commit()
        pulse_id = cursor.lastrowid
        conn.close()
        
        return {"status": "success", "pulse_id": pulse_id, "bpm": data.bpm}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pulse/latest")
async def get_latest_pulse():
    """Отримує останні дані пульсу"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, bpm, timestamp, resting_hr
            FROM pulse_data
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "bpm": row[1],
                "timestamp": row[2],
                "resting_hr": row[3]
            }
        return {"message": "No data available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pulse/history")
async def get_pulse_history(hours: int = 24):
    """Отримує історію пульсу за останні N годин"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT id, bpm, timestamp, resting_hr
            FROM pulse_data
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (since.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "bpm": row[1],
                "timestamp": row[2],
                "resting_hr": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/emotions")
async def create_emotion_entry(emotion: EmotionEntryInput):
    """Створює новий запис емоції"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now()
        
        # Знаходимо найближчий пульс до цього моменту (в межах 5 хвилин)
        cursor.execute("""
            SELECT id, bpm FROM pulse_data
            WHERE ABS(julianday(timestamp) - julianday(?)) * 24 * 60 <= 5
            ORDER BY ABS(julianday(timestamp) - julianday(?))
            LIMIT 1
        """, (timestamp.isoformat(), timestamp.isoformat()))
        
        pulse_row = cursor.fetchone()
        pulse_id = pulse_row[0] if pulse_row else None
        pulse_bpm = pulse_row[1] if pulse_row else None
        
        cursor.execute("""
            INSERT INTO emotion_entries (emotion, intensity, description, timestamp, pulse_id)
            VALUES (?, ?, ?, ?, ?)
        """, (emotion.emotion, emotion.intensity, emotion.description, timestamp.isoformat(), pulse_id))
        
        conn.commit()
        entry_id = cursor.lastrowid
        conn.close()
        
        return {
            "status": "success",
            "id": entry_id,
            "emotion": emotion.emotion,
            "intensity": emotion.intensity,
            "pulse_bpm": pulse_bpm
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emotions")
async def get_emotion_entries(limit: int = 50):
    """Отримує список записів емоцій"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.emotion, e.intensity, e.description, e.timestamp, p.bpm
            FROM emotion_entries e
            LEFT JOIN pulse_data p ON e.pulse_id = p.id
            ORDER BY e.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "emotion": row[1],
                "intensity": row[2],
                "description": row[3],
                "timestamp": row[4],
                "pulse_bpm": row[5]
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emotions/{emotion_id}")
async def get_emotion_entry(emotion_id: int):
    """Отримує конкретний запис емоції"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.emotion, e.intensity, e.description, e.timestamp, p.bpm
            FROM emotion_entries e
            LEFT JOIN pulse_data p ON e.pulse_id = p.id
            WHERE e.id = ?
        """, (emotion_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Emotion entry not found")
        
        return {
            "id": row[0],
            "emotion": row[1],
            "intensity": row[2],
            "description": row[3],
            "timestamp": row[4],
            "pulse_bpm": row[5]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/emotions/{emotion_id}")
async def delete_emotion_entry(emotion_id: int):
    """Видаляє запис емоції"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM emotion_entries WHERE id = ?", (emotion_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Emotion entry not found")
        
        conn.close()
        return {"status": "success", "message": "Entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/pulse")
async def get_pulse_statistics(hours: int = 24):
    """Отримує статистику пульсу"""
    try:
        stats = analytics.get_pulse_stats(hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/emotions")
async def get_emotion_statistics(days: int = 7):
    """Отримує статистику емоцій"""
    try:
        stats = analytics.get_emotion_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/correlation")
async def get_correlation_analysis_endpoint(days: int = 7):
    """Аналіз кореляції між емоціями та пульсом"""
    try:
        analysis = analytics.get_correlation_analysis(days)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report")
async def generate_report_endpoint(days: int = 7, format: str = "json"):
    """Генерує звіт за період"""
    try:
        report = analytics.generate_report(days)
        
        if format == "json":
            return report
        else:
            # Тут можна додати генерацію PDF
            raise HTTPException(status_code=400, detail="Only JSON format supported")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/advice")
async def get_ai_advice(days: int = 7):
    """
    Генерує поради за допомогою ШІ.
    """
    try:
        # Готуємо контекст для ШІ на основі поточних даних
        pulse_stats = analytics.get_pulse_stats(hours=days * 24)
        emotion_stats = analytics.get_emotion_stats(days=days)
        correlation = analytics.get_correlation_analysis(days=days)
        report = analytics.generate_report(days=days)

        context = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "pulse_statistics": pulse_stats,
            "emotion_statistics": emotion_stats,
            "correlation_summary": correlation.get("correlation_data", {}),
            "peak_moments": report.get("peak_moments", {}),
        }

        advice_payload = generate_ai_advice(context)
        return advice_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    import asyncio
    
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    
    asyncio.run(serve(app, config))

