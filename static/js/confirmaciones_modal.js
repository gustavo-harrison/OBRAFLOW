document.addEventListener('DOMContentLoaded', function () {
    const formularios = document.querySelectorAll('.form-confirmacion-modal');
    const modalElement = document.getElementById('modalConfirmacion');
    const modalTitulo = document.getElementById('modalConfirmacionTitulo');
    const modalMensaje = document.getElementById('modalConfirmacionMensaje');
    const btnConfirmar = document.getElementById('btnConfirmarAccion');

    let formularioPendiente = null;
    let bootstrapModal = null;

    if (modalElement) {
        bootstrapModal = new bootstrap.Modal(modalElement);
    }

    formularios.forEach(function (formulario) {
        formulario.addEventListener('submit', function (event) {
            event.preventDefault();

            formularioPendiente = formulario;

            const titulo = formulario.dataset.modalTitulo || 'Confirmar acción';
            const mensaje = formulario.dataset.modalMensaje || '¿Estás seguro de continuar?';

            if (modalTitulo) {
                modalTitulo.textContent = titulo;
            }

            if (modalMensaje) {
                modalMensaje.textContent = mensaje;
            }

            if (bootstrapModal) {
                bootstrapModal.show();
            }
        });
    });

    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function () {
            if (formularioPendiente) {
                formularioPendiente.submit();
            }
        });
    }
});