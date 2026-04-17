"""
Моделі бази даних та функції для створення таблиць
"""

from database import get_db_connection


def create_tables():
    """Створює таблиці в базі даних якщо вони не існують"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблиця для даних пульсу
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pulse_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bpm INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            resting_hr INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблиця для записів емоцій
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emotion TEXT NOT NULL,
            intensity INTEGER NOT NULL CHECK (intensity >= 1 AND intensity <= 10),
            description TEXT,
            timestamp TEXT NOT NULL,
            pulse_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pulse_id) REFERENCES pulse_data(id)
        )
    """)
    
    # Індекси для швидкого пошуку
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pulse_timestamp 
        ON pulse_data(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_emotion_timestamp 
        ON emotion_entries(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_emotion_pulse_id 
        ON emotion_entries(pulse_id)
    """)
    
    conn.commit()
    conn.close()
    print("Database tables created successfully")


# Моделі для типізації (опціонально, для документації)
class PulseData:
    def __init__(self, id: int, bpm: int, timestamp: str, resting_hr: int = None):
        self.id = id
        self.bpm = bpm
        self.timestamp = timestamp
        self.resting_hr = resting_hr


class EmotionEntry:
    def __init__(self, id: int, emotion: str, intensity: int, description: str = None, 
                 timestamp: str = None, pulse_id: int = None):
        self.id = id
        self.emotion = emotion
        self.intensity = intensity
        self.description = description
        self.timestamp = timestamp
        self.pulse_id = pulse_id

