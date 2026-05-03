document.addEventListener('DOMContentLoaded', function () {

    const numeroEdp = document.getElementById('id_numero_estado_pago');
    const tieneAnticipo = document.getElementById('id_tiene_anticipo');

    const tituloAnticipo = document.getElementById('titulo-anticipo');
    const campoTieneAnticipo = document.getElementById('campo-tiene-anticipo');
    const campoPorcentajeAnticipo = document.getElementById('campo-porcentaje-anticipo');
    const campoDevolucionAnticipo = document.getElementById('campo-devolucion-anticipo');

    function mostrar(el, estado = true) {
        if (!el) return;
        el.style.display = estado ? 'block' : 'none';
    }

    function actualizarCamposAnticipo() {

        const numero = parseInt(numeroEdp.value || '1');
        const checked = tieneAnticipo ? tieneAnticipo.checked : false;

        // EDP 1
        if (numero <= 1) {

            mostrar(tituloAnticipo, true);
            mostrar(campoTieneAnticipo, true);

            mostrar(campoPorcentajeAnticipo, checked);
            mostrar(campoDevolucionAnticipo, checked);

            return;
        }

        // EDP 2 en adelante:
        // ocultar todo bloque anticipo excepto devolución

        mostrar(tituloAnticipo, false);
        mostrar(campoTieneAnticipo, false);
        mostrar(campoPorcentajeAnticipo, false);
        mostrar(campoDevolucionAnticipo, true);
    }

    if (numeroEdp) {
        numeroEdp.addEventListener('input', actualizarCamposAnticipo);
        numeroEdp.addEventListener('change', actualizarCamposAnticipo);
    }

    if (tieneAnticipo) {
        tieneAnticipo.addEventListener('change', actualizarCamposAnticipo);
    }

    actualizarCamposAnticipo();

});