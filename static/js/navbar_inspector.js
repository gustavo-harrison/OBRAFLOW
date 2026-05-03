function updateTopbarInspectorClock() {
    const now = new Date();

    const time = now.toLocaleTimeString('es-CL', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    const date = now.toLocaleDateString('es-CL', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    const clock = document.getElementById('topbarClockInspector');
    const dateEl = document.getElementById('topbarDateInspector');

    if (clock) clock.textContent = time;
    if (dateEl) dateEl.textContent = date;
}

updateTopbarInspectorClock();
setInterval(updateTopbarInspectorClock, 1000);