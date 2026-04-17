// Конфігурація API
const API_BASE_URL = 'http://localhost:8000/api';

// Стан додатку
let updateInterval = null;
let pulseUpdateInterval = null;

// Емоції з емодзі
const EMOTIONS = {
    'радість': '😊',
    'спокій': '😌',
    'тривога': '😰',
    'страх': '😨',
    'сум': '😢',
    'злість': '😠',
    'нейтральність': '😐'
};

function getPlotlyThemeLayout(title, xTitle, yTitle) {
    return {
        title,
        xaxis: {
            title: xTitle,
            gridcolor: '#2a3557',
            zerolinecolor: '#2a3557',
            color: '#e5e7eb'
        },
        yaxis: {
            title: yTitle,
            gridcolor: '#2a3557',
            zerolinecolor: '#2a3557',
            color: '#e5e7eb'
        },
        hovermode: 'closest',
        paper_bgcolor: '#141b2f',
        plot_bgcolor: '#141b2f',
        font: {
            color: '#e5e7eb'
        }
    };
}

// Ініціалізація
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Обробка форми емоції
    const emotionForm = document.getElementById('emotion-form');
    emotionForm.addEventListener('submit', handleEmotionSubmit);

    // Обробка інтенсивності
    const intensitySlider = document.getElementById('intensity');
    const intensityValue = document.getElementById('intensity-value');
    intensitySlider.addEventListener('input', (e) => {
        intensityValue.textContent = e.target.value;
    });

    // Таби для графіків
    setupTabs();

    // Завантаження даних
    loadLatestPulse();
    loadJournal();
    loadStats();
    loadPulseHistory();

    // ШІ-поради
    const aiButton = document.getElementById('get-ai-advice');
    if (aiButton) {
        aiButton.addEventListener('click', () => {
            const periodSelect = document.getElementById('ai-period');
            const days = parseInt(periodSelect.value, 10) || 7;
            loadAiAdvice(days);
        });
    }

    // Оновлення пульсу кожні 5 секунд
    pulseUpdateInterval = setInterval(loadLatestPulse, 5000);

    // Оновлення статистики кожну хвилину
    updateInterval = setInterval(() => {
        loadStats();
        loadPulseHistory();
    }, 60000);

    // Генерація звіту
    document.getElementById('generate-report').addEventListener('click', generateReport);
    document.getElementById('refresh-journal').addEventListener('click', loadJournal);
    document.getElementById('journal-filter').addEventListener('change', loadJournal);
}

// ============= ОБРОБКА ФОРМИ ЕМОЦІЇ =============

async function handleEmotionSubmit(e) {
    e.preventDefault();

    const emotion = document.getElementById('emotion-select').value;
    const intensity = parseInt(document.getElementById('intensity').value);
    const description = document.getElementById('description').value;

    try {
        const response = await fetch(`${API_BASE_URL}/emotions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                emotion,
                intensity,
                description: description || null
            })
        });

        if (!response.ok) {
            throw new Error('Помилка при збереженні запису');
        }

        const data = await response.json();
        
        // Показуємо повідомлення про успіх
        showNotification('Запис успішно додано!', 'success');
        
        // Очищаємо форму
        document.getElementById('emotion-form').reset();
        document.getElementById('intensity-value').textContent = '5';
        
        // Оновлюємо дані
        loadJournal();
        loadStats();
        loadPulseHistory();
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Помилка: ' + error.message, 'error');
    }
}

// ============= ЗАВАНТАЖЕННЯ ПУЛЬСУ =============

async function loadLatestPulse() {
    try {
        const response = await fetch(`${API_BASE_URL}/pulse/latest`);
        const data = await response.json();

        if (data.bpm) {
            document.getElementById('current-pulse').textContent = data.bpm;
            document.getElementById('current-pulse').classList.remove('loading');
            
            const timestamp = new Date(data.timestamp);
            document.getElementById('pulse-timestamp').textContent = 
                `Оновлено: ${timestamp.toLocaleTimeString('uk-UA')}`;
            
            // Оновлюємо статус пристрою
            updateDeviceStatus(true);
        } else {
            document.getElementById('current-pulse').textContent = '--';
            document.getElementById('pulse-timestamp').textContent = 'Очікування даних...';
            updateDeviceStatus(false);
        }
    } catch (error) {
        console.error('Error loading pulse:', error);
        document.getElementById('current-pulse').textContent = '--';
        updateDeviceStatus(false);
    }
}

async function loadPulseHistory(hours = 24) {
    try {
        const response = await fetch(`${API_BASE_URL}/pulse/history?hours=${hours}`);
        const data = await response.json();

        if (data.length > 0) {
            updatePulseChart(data);
        }
    } catch (error) {
        console.error('Error loading pulse history:', error);
    }
}

function updatePulseChart(data) {
    const timestamps = data.map(d => new Date(d.timestamp));
    const bpmValues = data.map(d => d.bpm);

    const trace = {
        x: timestamps,
        y: bpmValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Пульс (BPM)',
        line: {
            color: '#6B46C1',
            width: 2
        },
        marker: {
            size: 4
        }
    };

    const layout = getPlotlyThemeLayout('Динаміка пульсу', 'Час', 'BPM');

    Plotly.newPlot('pulse-chart', [trace], layout, {responsive: true});
}

// ============= ЖУРНАЛ ЕМОЦІЙ =============

async function loadJournal() {
    try {
        const response = await fetch(`${API_BASE_URL}/emotions?limit=50`);
        const entries = await response.json();

        const filter = document.getElementById('journal-filter').value;
        const filteredEntries = filter === 'all' 
            ? entries 
            : entries.filter(e => e.emotion === filter);

        displayJournalEntries(filteredEntries);
    } catch (error) {
        console.error('Error loading journal:', error);
        document.getElementById('journal-entries').innerHTML = 
            '<p class="empty-state">Помилка завантаження записів</p>';
    }
}

function displayJournalEntries(entries) {
    const container = document.getElementById('journal-entries');

    if (entries.length === 0) {
        container.innerHTML = '<p class="empty-state">Немає записів</p>';
        return;
    }

    container.innerHTML = entries.map(entry => {
        const emotionEmoji = EMOTIONS[entry.emotion] || '😐';
        const timestamp = new Date(entry.timestamp);
        const pulseInfo = entry.pulse_bpm 
            ? `<div class="entry-pulse">Пульс: ${entry.pulse_bpm} BPM</div>`
            : '';

        return `
            <div class="journal-entry">
                <div class="entry-header">
                    <span class="entry-emotion">${emotionEmoji} ${entry.emotion}</span>
                    <span class="entry-time">${timestamp.toLocaleString('uk-UA')}</span>
                </div>
                <div>
                    <span class="entry-intensity">Інтенсивність: ${entry.intensity}/10</span>
                </div>
                ${entry.description ? `<div class="entry-description">${entry.description}</div>` : ''}
                ${pulseInfo}
            </div>
        `;
    }).join('');
}

// ============= СТАТИСТИКА =============

async function loadStats() {
    try {
        // Статистика пульсу
        const pulseStatsResponse = await fetch(`${API_BASE_URL}/stats/pulse?hours=24`);
        const pulseStats = await pulseStatsResponse.json();
        
        if (pulseStats.average_bpm) {
            document.getElementById('avg-pulse').textContent = Math.round(pulseStats.average_bpm);
        }

        // Статистика емоцій
        const emotionStatsResponse = await fetch(`${API_BASE_URL}/stats/emotions?days=7`);
        const emotionStats = await emotionStatsResponse.json();
        
        if (emotionStats.most_common_emotion) {
            const emoji = EMOTIONS[emotionStats.most_common_emotion] || '';
            document.getElementById('most-common-emotion').textContent = 
                `${emoji} ${emotionStats.most_common_emotion}`;
        }
        
        if (emotionStats.average_intensity) {
            document.getElementById('avg-intensity').textContent = 
                emotionStats.average_intensity.toFixed(1);
        }
        
        if (emotionStats.total_entries !== undefined) {
            document.getElementById('total-entries').textContent = emotionStats.total_entries;
        }

        // Оновлюємо графіки емоцій
        updateEmotionsChart(emotionStats);
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateEmotionsChart(stats) {
    if (!stats.emotion_distribution) return;

    const emotions = Object.keys(stats.emotion_distribution);
    const counts = emotions.map(e => stats.emotion_distribution[e].count);
    const colors = emotions.map(e => getEmotionColor(e));

    const trace = {
        x: emotions.map(e => EMOTIONS[e] + ' ' + e),
        y: counts,
        type: 'bar',
        marker: {
            color: colors
        }
    };

    const layout = getPlotlyThemeLayout('Розподіл емоцій', 'Емоції', 'Кількість записів');

    Plotly.newPlot('emotions-chart', [trace], layout, {responsive: true});
}

function getEmotionColor(emotion) {
    const colors = {
        'радість': '#10B981',
        'спокій': '#3B82F6',
        'тривога': '#F59E0B',
        'страх': '#EF4444',
        'сум': '#6366F1',
        'злість': '#DC2626',
        'нейтральність': '#9CA3AF'
    };
    return colors[emotion] || '#9CA3AF';
}

// ============= КОРЕЛЯЦІЯ =============

async function loadCorrelation() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/correlation?days=7`);
        const data = await response.json();

        if (data.correlation_data && Object.keys(data.correlation_data).length > 0) {
            updateCorrelationChart(data.correlation_data);
        }
    } catch (error) {
        console.error('Error loading correlation:', error);
    }
}

function updateCorrelationChart(correlationData) {
    const emotions = Object.keys(correlationData);
    const pulses = emotions.map(e => correlationData[e].average_pulse);
    const colors = emotions.map(e => getEmotionColor(e));

    const trace = {
        x: emotions.map(e => EMOTIONS[e] + ' ' + e),
        y: pulses,
        type: 'bar',
        marker: {
            color: colors
        }
    };

    const layout = getPlotlyThemeLayout('Кореляція: Емоції та Пульс', 'Емоції', 'Середній пульс (BPM)');

    Plotly.newPlot('correlation-chart', [trace], layout, {responsive: true});
}

// ============= ЗВІТИ =============

async function generateReport() {
    const days = parseInt(document.getElementById('report-period').value);
    const reportContent = document.getElementById('report-content');
    
    reportContent.innerHTML = '<p class="loading">Генерація звіту...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/report?days=${days}&format=json`);
        const report = await response.json();

        // Форматуємо звіт для відображення
        reportContent.innerHTML = formatReport(report);
    } catch (error) {
        console.error('Error generating report:', error);
        reportContent.innerHTML = '<p class="empty-state">Помилка генерації звіту</p>';
    }
}

function formatReport(report) {
    let html = '<div style="font-family: sans-serif;">';
    html += `<h3>Звіт за ${report.period_days} днів</h3>`;
    html += `<p><strong>Згенеровано:</strong> ${new Date(report.generated_at).toLocaleString('uk-UA')}</p>`;
    
    // Статистика пульсу
    html += '<h4>Статистика пульсу</h4>';
    html += `<ul>`;
    html += `<li>Середній: ${report.pulse_statistics.average_bpm || 'N/A'} BPM</li>`;
    html += `<li>Мінімальний: ${report.pulse_statistics.min_bpm || 'N/A'} BPM</li>`;
    html += `<li>Максимальний: ${report.pulse_statistics.max_bpm || 'N/A'} BPM</li>`;
    html += `</ul>`;

    // Статистика емоцій
    html += '<h4>Статистика емоцій</h4>';
    html += `<p>Загальна кількість записів: ${report.emotion_statistics.total_entries}</p>`;
    html += `<p>Найчастіша емоція: ${report.emotion_statistics.most_common_emotion}</p>`;
    html += `<p>Середня інтенсивність: ${report.emotion_statistics.average_intensity}</p>`;

    // Рекомендації
    html += '<h4>Рекомендації</h4>';
    html += '<ul>';
    report.recommendations.forEach(rec => {
        html += `<li>${rec}</li>`;
    });
    html += '</ul>';

    html += '</div>';
    return html;
}

// ============= ПОРАДИ ШІ =============

async function loadAiAdvice(days = 7) {
    const container = document.getElementById('ai-advice');
    if (!container) return;

    container.innerHTML = '<p class="loading">Генерація порад ШІ...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/ai/advice?days=${days}`);
        if (!response.ok) {
            throw new Error('Помилка при отриманні порад ШІ');
        }

        const data = await response.json();
        const adviceText = (data.advice || '').trim();

        if (!adviceText) {
            container.innerHTML = '<p class="empty-state">Поки що немає порад. Спробуйте пізніше.</p>';
            return;
        }

        // Перетворюємо переноси рядків на <br> для красивого відображення
        const htmlAdvice = adviceText
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .map(line => `<p>${line}</p>`)
            .join('');

        container.innerHTML = htmlAdvice;
    } catch (error) {
        console.error('Error loading AI advice:', error);
        container.innerHTML = '<p class="empty-state">Не вдалося отримати пораду ШІ. Перевірте підключення до серверу.</p>';
    }
}

// ============= УТИЛІТИ =============

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Видаляємо активний клас з усіх табів
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Додаємо активний клас до вибраного табу
            button.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');

            // Завантажуємо дані для графіка кореляції при переключенні
            if (tabName === 'correlation') {
                loadCorrelation();
            }
        });
    });
}

function updateDeviceStatus(isOnline) {
    const statusElement = document.getElementById('device-status');
    if (isOnline) {
        statusElement.textContent = 'Пристрій підключено';
        statusElement.classList.remove('offline');
        statusElement.classList.add('online');
    } else {
        statusElement.textContent = 'Пристрій не підключено';
        statusElement.classList.remove('online');
        statusElement.classList.add('offline');
    }
}

function showNotification(message, type = 'info') {
    // Проста реалізація повідомлення
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10B981' : '#EF4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Додаємо стилі для анімацій
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

