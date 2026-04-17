"""
Модуль аналітики та обробки даних
Обчислює статистику, кореляції, генерує звіти
"""

from database import get_db_connection
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from ai_advice import generate_ai_advice


def get_pulse_stats(hours: int = 24) -> Dict[str, Any]:
    """Обчислює статистику пульсу за період"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since = datetime.now() - timedelta(hours=hours)
    cursor.execute("""
        SELECT 
            AVG(bpm) as avg_bpm,
            MIN(bpm) as min_bpm,
            MAX(bpm) as max_bpm,
            COUNT(*) as count
        FROM pulse_data
        WHERE timestamp >= ?
    """, (since.isoformat(),))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[3] > 0:  # count > 0
        return {
            "period_hours": hours,
            "average_bpm": round(row[0], 2) if row[0] else None,
            "min_bpm": row[1],
            "max_bpm": row[2],
            "data_points": row[3]
        }
    return {
        "period_hours": hours,
        "average_bpm": None,
        "min_bpm": None,
        "max_bpm": None,
        "data_points": 0
    }


def get_emotion_stats(days: int = 7) -> Dict[str, Any]:
    """Обчислює статистику емоцій за період"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since = datetime.now() - timedelta(days=days)
    cursor.execute("""
        SELECT 
            emotion,
            COUNT(*) as count,
            AVG(intensity) as avg_intensity
        FROM emotion_entries
        WHERE timestamp >= ?
        GROUP BY emotion
        ORDER BY count DESC
    """, (since.isoformat(),))
    
    rows = cursor.fetchall()
    conn.close()
    
    emotion_counts = {}
    for row in rows:
        emotion_counts[row[0]] = {
            "count": row[1],
            "average_intensity": round(row[2], 2)
        }
    
    # Загальна статистика
    total_entries = sum(e["count"] for e in emotion_counts.values())
    avg_intensity = sum(e["average_intensity"] * e["count"] for e in emotion_counts.values()) / total_entries if total_entries > 0 else 0
    
    most_common = max(emotion_counts.items(), key=lambda x: x[1]["count"])[0] if emotion_counts else None
    
    return {
        "period_days": days,
        "total_entries": total_entries,
        "average_intensity": round(avg_intensity, 2),
        "most_common_emotion": most_common,
        "emotion_distribution": emotion_counts
    }


def get_correlation_analysis(days: int = 7) -> Dict[str, Any]:
    """Аналізує кореляцію між емоціями та пульсом"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since = datetime.now() - timedelta(days=days)
    
    # Отримуємо записи з пов'язаним пульсом
    cursor.execute("""
        SELECT 
            e.emotion,
            e.intensity,
            p.bpm
        FROM emotion_entries e
        INNER JOIN pulse_data p ON e.pulse_id = p.id
        WHERE e.timestamp >= ?
    """, (since.isoformat(),))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {
            "period_days": days,
            "correlation_data": {},
            "message": "Insufficient data for correlation analysis"
        }
    
    # Групуємо по емоціях
    emotion_data = {}
    for row in rows:
        emotion = row[0]
        if emotion not in emotion_data:
            emotion_data[emotion] = {"pulses": [], "intensities": []}
        emotion_data[emotion]["pulses"].append(row[2])
        emotion_data[emotion]["intensities"].append(row[1])
    
    # Обчислюємо середні значення
    correlation_results = {}
    for emotion, data in emotion_data.items():
        avg_pulse = sum(data["pulses"]) / len(data["pulses"])
        avg_intensity = sum(data["intensities"]) / len(data["intensities"])
        correlation_results[emotion] = {
            "average_pulse": round(avg_pulse, 2),
            "average_intensity": round(avg_intensity, 2),
            "data_points": len(data["pulses"])
        }
    
    return {
        "period_days": days,
        "correlation_data": correlation_results
    }


def generate_report(days: int = 7) -> Dict[str, Any]:
    """Генерує комплексний звіт за період"""
    pulse_stats = get_pulse_stats(hours=days * 24)
    emotion_stats = get_emotion_stats(days=days)
    correlation = get_correlation_analysis(days=days)
    
    # Додатково: пікові моменти стресу
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since = datetime.now() - timedelta(days=days)
    
    # Знаходимо моменти з найвищим пульсом
    cursor.execute("""
        SELECT bpm, timestamp
        FROM pulse_data
        WHERE timestamp >= ?
        ORDER BY bpm DESC
        LIMIT 5
    """, (since.isoformat(),))
    
    peak_pulses = [{"bpm": row[0], "timestamp": row[1]} for row in cursor.fetchall()]
    
    # Знаходимо найбільш інтенсивні емоції
    cursor.execute("""
        SELECT emotion, intensity, description, timestamp
        FROM emotion_entries
        WHERE timestamp >= ?
        ORDER BY intensity DESC
        LIMIT 5
    """, (since.isoformat(),))
    
    peak_emotions = [
        {
            "emotion": row[0],
            "intensity": row[1],
            "description": row[2],
            "timestamp": row[3]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    # Викликаємо ШІ для генерації рекомендацій на основі цього ж контексту
    ai_context = {
        "generated_at": datetime.now().isoformat(),
        "period_days": days,
        "pulse_statistics": pulse_stats,
        "emotion_statistics": emotion_stats,
        "correlation_summary": correlation.get("correlation_data", {}),
        "peak_moments": {
            "highest_pulses": peak_pulses,
            "most_intense_emotions": peak_emotions,
        },
    }

    ai_payload = generate_ai_advice(ai_context)
    advice_text = ai_payload.get("advice", "") or ""
    # Розбиваємо текст по рядках, щоб показати як список у звіті
    recommendations: List[str] = [
        line.strip(" •-\t")
        for line in advice_text.split("\n")
        if line.strip()
    ]

    report = {
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
        "pulse_statistics": pulse_stats,
        "emotion_statistics": emotion_stats,
        "correlation_analysis": correlation,
        "peak_moments": {
            "highest_pulses": peak_pulses,
            "most_intense_emotions": peak_emotions
        },
        "recommendations": recommendations,
        "ai_meta": {
            "source": ai_payload.get("source"),
            "has_ai": ai_payload.get("has_ai"),
            "model": ai_payload.get("model"),
        },
    }
    
    return report

