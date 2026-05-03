document.addEventListener('DOMContentLoaded', function () {
    const obraSelect = document.getElementById('id_obra');
    const tipoActaSelect = document.getElementById('id_tipo_acta');
    const fechaActaInput = document.getElementById('id_fecha_acta');

    const tituloInput = document.getElementById('id_titulo');
    const cuerpoInput = document.getElementById('id_cuerpo_acta');

    const nombreObraInput = document.getElementById('id_nombre_obra');
    const codigoLicitacionInput = document.getElementById('id_codigo_licitacion');
    const nombreEmpresaInput = document.getElementById('id_nombre_empresa');
    const rutEmpresaInput = document.getElementById('id_rut_empresa');
    const nombreInspectorInput = document.getElementById('id_nombre_inspector');
    const ubicacionObraInput = document.getElementById('id_ubicacion_obra');
    const firmaInspectorInput = document.getElementById('id_firma_inspector_texto');
    const firmaEmpresaInput = document.getElementById('id_firma_empresa_texto');

    if (!obraSelect || !tipoActaSelect) return;

    let obrasData = {};

    try {
        obrasData = JSON.parse(obraSelect.dataset.obras || '{}');
    } catch (e) {
        obrasData = {};
    }

    function formatFecha(fechaRaw) {
        if (!fechaRaw) return 'la fecha indicada';

        const [year, month, day] = fechaRaw.split('-');

        if (!year || !month || !day) return fechaRaw;

        return `${day}/${month}/${year}`;
    }

    function completarDatosObra() {
        const obraId = obraSelect.value;
        const data = obrasData[obraId];

        if (!data) return;

        if (nombreObraInput) nombreObraInput.value = data.nombre_obra || '';
        if (codigoLicitacionInput) codigoLicitacionInput.value = data.codigo_licitacion || '';
        if (nombreEmpresaInput) nombreEmpresaInput.value = data.nombre_empresa || '';
        if (rutEmpresaInput) rutEmpresaInput.value = data.rut_empresa || '';
        if (nombreInspectorInput) nombreInspectorInput.value = data.nombre_inspector || '';
        if (ubicacionObraInput) ubicacionObraInput.value = data.ubicacion_obra || '';

        if (firmaInspectorInput) firmaInspectorInput.value = data.firma_inspector_texto || data.nombre_inspector || '';

        /*
            Importante:
            La firma de empresa queda vacía porque no siempre firmará
            la misma persona asociada al usuario empresa.
        */
        if (firmaEmpresaInput) firmaEmpresaInput.value = '';
    }

    function construirTextoBase() {
        const tipo = tipoActaSelect.value;
        const fecha = formatFecha(fechaActaInput ? fechaActaInput.value : '');
        const obra = nombreObraInput ? nombreObraInput.value : '';
        const empresa = nombreEmpresaInput ? nombreEmpresaInput.value : '';

        if (!tipo) return { titulo: '', cuerpo: '' };

        if (tipo === 'ENTREGA_TERRENO') {
            return {
                titulo: 'ACTA DE ENTREGA DE TERRENO',
                cuerpo:
`Con fecha ${fecha}, se realiza la entrega de terreno a la empresa ${empresa}, correspondiente a la obra ${obra}.

Se deja constancia que desde el presente día se contabiliza la entrega de terreno y el inicio del plazo contractual de la obra.`
            };
        }

        if (tipo === 'RECEPCION_OBS') {
            return {
                titulo: 'ACTA DE RECEPCIÓN CON OBSERVACIONES',
                cuerpo:
`Con fecha ${fecha}, se realiza la recepción de la totalidad de las partidas ejecutadas a cargo de la empresa ${empresa}, correspondiente a la obra ${obra}.

Se deja constancia que la recepción se efectúa con observaciones pendientes de subsanar por parte de la empresa contratista.`
            };
        }

        if (tipo === 'RECEPCION_OK') {
            return {
                titulo: 'ACTA DE RECEPCIÓN SIN OBSERVACIONES',
                cuerpo:
`Con fecha ${fecha}, se realiza la recepción de la totalidad de las partidas ejecutadas a cargo de la empresa ${empresa}, correspondiente a la obra ${obra}.

Se deja constancia que la recepción se efectúa sin observaciones pendientes.`
            };
        }

        return { titulo: '', cuerpo: '' };
    }

    function completarTextoActa() {
        const texto = construirTextoBase();

        if (tituloInput && (!tituloInput.value || tituloInput.dataset.autoFill === 'true')) {
            tituloInput.value = texto.titulo;
            tituloInput.dataset.autoFill = 'true';
        }

        if (cuerpoInput && (!cuerpoInput.value || cuerpoInput.dataset.autoFill === 'true')) {
            cuerpoInput.value = texto.cuerpo;
            cuerpoInput.dataset.autoFill = 'true';
        }
    }

    function refrescarAutocompletado() {
        completarDatosObra();
        completarTextoActa();
    }

    if (tituloInput) {
        tituloInput.addEventListener('input', function () {
            tituloInput.dataset.autoFill = 'false';
        });
    }

    if (cuerpoInput) {
        cuerpoInput.addEventListener('input', function () {
            cuerpoInput.dataset.autoFill = 'false';
        });
    }

    obraSelect.addEventListener('change', refrescarAutocompletado);
    tipoActaSelect.addEventListener('change', completarTextoActa);

    if (fechaActaInput) {
        fechaActaInput.addEventListener('change', completarTextoActa);
    }

    refrescarAutocompletado();
});