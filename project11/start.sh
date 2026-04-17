#!/bin/bash
# Скрипт для запуску frontend та backend (Linux/Mac)

echo "============================================================"
echo "💓 Емоційний трекер - Запуск серверів"
echo "============================================================"
echo ""

# Перевірка чи існує віртуальне середовище
if [ -f "website/backend/venv/bin/activate" ]; then
    echo "✅ Знайдено віртуальне середовище"
    source website/backend/venv/bin/activate
else
    echo "⚠️  Віртуальне середовище не знайдено, створюємо..."
    cd website/backend
    python -m venv venv
    source venv/bin/activate
    cd ../..
fi

echo "📦 Встановлюємо залежності backend (включно з python-dotenv)..."
pip install -r website/backend/requirements.txt >/dev/null 2>&1
echo ""

# Запуск backend у фоновому режимі
echo "🚀 Запуск backend сервера..."
cd website/backend
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ../..

# Затримка
sleep 3

# Запуск frontend у фоновому режимі
echo "🚀 Запуск frontend сервера..."
cd website/frontend
python -m http.server 8080 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo ""
echo "============================================================"
echo "✅ Сервери запущено!"
echo "============================================================"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs:    http://localhost:8000/docs"
echo "📍 Frontend:    http://localhost:8080"
echo ""
echo "PID Backend:  $BACKEND_PID"
echo "PID Frontend: $FRONTEND_PID"
echo ""
echo "Натисніть Ctrl+C для зупинки серверів"
echo ""

# Функція для очищення при завершенні
cleanup() {
    echo ""
    echo "⏹️  Зупинка серверів..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Сервери зупинено"
    exit 0
}

# Обробка сигналу завершення
trap cleanup SIGINT SIGTERM

# Чекаємо поки процеси працюють
wait

