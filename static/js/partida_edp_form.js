function controlarCamposPartidaEDP() {
    const tipoFila = document.getElementById('id_tipo_fila');

    const camposValorizados = [
        'campo-unidad',
        'campo-cantidad',
        'campo-precio-unitario',
        'campo-avance-periodo',
        'campo-avance-acumulado'
    ];

    if (!tipoFila) return;

    function actualizarCampos() {
        const esTitulo = tipoFila.value === 'TITULO';

        camposValorizados.forEach(function (campoId) {
            const campo = document.getElementById(campoId);

            if (campo) {
                campo.style.display = esTitulo ? 'none' : 'block';
            }
        });
    }

    tipoFila.addEventListener('change', actualizarCampos);
    actualizarCampos();
}

document.addEventListener('DOMContentLoaded', controlarCamposPartidaEDP);