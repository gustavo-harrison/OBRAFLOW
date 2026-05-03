function updateEmpresaClock() {
    const now = new Date();

    const time = now.toLocaleTimeString('es-CL');

    const date = now.toLocaleDateString('es-CL', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    const clock = document.getElementById('liveClockEmpresa');
    const dateEl = document.getElementById('liveDateEmpresa');

    if (clock) clock.textContent = time;
    if (dateEl) dateEl.textContent = date;
}

updateEmpresaClock();
setInterval(updateEmpresaClock, 1000);