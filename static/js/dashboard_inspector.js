function updateInspectorClock() {
    const now = new Date();

    const time = now.toLocaleTimeString('es-CL');

    const date = now.toLocaleDateString('es-CL', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    const clock = document.getElementById('liveClockInspector');
    const dateEl = document.getElementById('liveDateInspector');

    if (clock) clock.textContent = time;
    if (dateEl) dateEl.textContent = date;
}

function formatCLP(value) {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        maximumFractionDigits: 0
    }).format(value);
}

function formatDate(fecha) {
    const d = new Date(fecha);

    return d.toLocaleDateString('es-CL', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

async function cargarIndicadores() {
    try {
        const [ufRes, utmRes] = await Promise.all([
            fetch('https://mindicador.cl/api/uf'),
            fetch('https://mindicador.cl/api/utm')
        ]);

        const ufData = await ufRes.json();
        const utmData = await utmRes.json();

        const uf = ufData.serie[0];
        const utm = utmData.serie[0];

        document.getElementById('valorUF').textContent = formatCLP(uf.valor);
        document.getElementById('fechaUF').textContent = formatDate(uf.fecha);

        document.getElementById('valorUTM').textContent = formatCLP(utm.valor);
        document.getElementById('fechaUTM').textContent = formatDate(utm.fecha);

    } catch (error) {
        document.getElementById('valorUF').textContent = 'Error';
        document.getElementById('valorUTM').textContent = 'Error';
    }
}

updateInspectorClock();
setInterval(updateInspectorClock, 1000);
cargarIndicadores();