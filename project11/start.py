"""
Скрипт для одночасного запуску frontend та backend серверів
"""
import subprocess
import sys
import os
import time
from pathlib import Path

# Шляхи до папок
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "website" / "backend"
FRONTEND_DIR = PROJECT_ROOT / "website" / "frontend"

def check_backend_dependencies():
    """Перевіряє чи встановлені залежності backend"""
    try:
        import fastapi
        import hypercorn
        return True
    except ImportError:
        print("❌ Backend залежності не встановлені!")
        print("   Запустіть: cd website/backend && pip install -r requirements.txt")
        return False

def start_backend():
    """Запускає backend сервер"""
    print("🚀 Запуск backend сервера...")
    os.chdir(BACKEND_DIR)
    
    # Перевіряємо чи є віртуальне середовище
    if (BACKEND_DIR / "venv" / "Scripts" / "python.exe").exists():
        python_cmd = str(BACKEND_DIR / "venv" / "Scripts" / "python.exe")
    elif (BACKEND_DIR / "venv" / "bin" / "python").exists():
        python_cmd = str(BACKEND_DIR / "venv" / "bin" / "python")
    else:
        python_cmd = sys.executable
    
    try:
        process = subprocess.Popen(
            [python_cmd, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print("✅ Backend запущено на http://localhost:8000")
        return process
    except Exception as e:
        print(f"❌ Помилка запуску backend: {e}")
        return None

def start_frontend():
    """Запускає frontend сервер"""
    print("🚀 Запуск frontend сервера...")
    os.chdir(FRONTEND_DIR)
    
    try:
        # Спробуємо Python http.server
        process = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print("✅ Frontend запущено на http://localhost:8080")
        return process
    except Exception as e:
        print(f"❌ Помилка запуску frontend: {e}")
        return None

def main():
    print("=" * 60)
    print("💓 Емоційний трекер - Запуск серверів")
    print("=" * 60)
    print()
    
    # Перевірка залежностей
    if not check_backend_dependencies():
        sys.exit(1)
    
    # Запуск backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Невелика затримка перед запуском frontend
    time.sleep(2)
    
    # Запуск frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Обидва сервери запущено успішно!")
    print("=" * 60)
    print()
    print("📍 Backend API: http://localhost:8000")
    print("📍 API Docs:    http://localhost:8000/docs")
    print("📍 Frontend:    http://localhost:8080")
    print()
    print("Натисніть Ctrl+C для зупинки серверів")
    print("=" * 60)
    print()
    
    try:
        # Чекаємо поки процеси працюють
        while True:
            # Перевіряємо чи процеси ще працюють
            if backend_process.poll() is not None:
                print("❌ Backend процес завершився неочікувано")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend процес завершився неочікувано")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("⏹️  Зупинка серверів...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Сервери зупинено")

if __name__ == "__main__":
    main()

