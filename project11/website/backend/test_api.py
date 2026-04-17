"""
Простий скрипт для тестування API
Використання: python test_api.py
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"

def test_pulse_endpoint():
    """Тест відправки даних пульсу"""
    print("Тестування POST /api/pulse...")
    data = {
        "bpm": 72,
        "timestamp": int(datetime.now().timestamp()),
        "resting_hr": 65
    }
    response = requests.post(f"{API_BASE_URL}/pulse", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_emotion_endpoint():
    """Тест створення запису емоції"""
    print("Тестування POST /api/emotions...")
    data = {
        "emotion": "радість",
        "intensity": 7,
        "description": "Тестовий запис"
    }
    response = requests.post(f"{API_BASE_URL}/emotions", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_get_endpoints():
    """Тест отримання даних"""
    print("Тестування GET endpoints...")
    
    # Останній пульс
    response = requests.get(f"{API_BASE_URL}/pulse/latest")
    print(f"GET /api/pulse/latest: {response.status_code}")
    if response.status_code == 200:
        print(f"  Data: {response.json()}\n")
    
    # Історія пульсу
    response = requests.get(f"{API_BASE_URL}/pulse/history?hours=24")
    print(f"GET /api/pulse/history: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Records: {len(data)}\n")
    
    # Емоції
    response = requests.get(f"{API_BASE_URL}/emotions?limit=10")
    print(f"GET /api/emotions: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Records: {len(data)}\n")

def test_stats():
    """Тест статистики"""
    print("Тестування статистики...")
    
    # Статистика пульсу
    response = requests.get(f"{API_BASE_URL}/stats/pulse?hours=24")
    print(f"GET /api/stats/pulse: {response.status_code}")
    if response.status_code == 200:
        print(f"  Stats: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    
    # Статистика емоцій
    response = requests.get(f"{API_BASE_URL}/stats/emotions?days=7")
    print(f"GET /api/stats/emotions: {response.status_code}")
    if response.status_code == 200:
        print(f"  Stats: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

def main():
    print("=" * 50)
    print("Тестування API емоційного трекера")
    print("=" * 50)
    print()
    
    try:
        # Тест базових endpoints
        test_pulse_endpoint()
        test_emotion_endpoint()
        test_get_endpoints()
        test_stats()
        
        print("=" * 50)
        print("Тестування завершено!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Помилка: не вдалося підключитися до сервера")
        print("Переконайтеся, що backend сервер запущено на http://localhost:8000")
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    main()

