/**
 * Генератор чертежей котлов — клиентская логика
 * Поддержка 4 типов: горизонтальный, вертикальный, паровой, твёрдотопливный
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('boilerForm');
    const boilerType = document.getElementById('boiler_type');
    const btnPreview = document.getElementById('btnPreview');
    const btnExportSVG = document.getElementById('btnExportSVG');
    const btnExportDXF = document.getElementById('btnExportDXF');
    const btnExportPDF = document.getElementById('btnExportPDF');
    const previewContainer = document.getElementById('previewContainer');

    // Переключение параметров по типу котла
    boilerType.addEventListener('change', () => {
        document.querySelectorAll('.type-params').forEach(el => el.style.display = 'none');
        const selected = boilerType.value;
        const panel = document.getElementById('params_' + selected);
        if (panel) panel.style.display = 'block';
    });

    // Собираем параметры из формы
    function getParams() {
        const params = {};
        const activeType = boilerType.value;

        // Общие поля
        params.boiler_type = activeType;
        params.name = document.getElementById('name').value;
        params.fuel_type = document.getElementById('fuel_type').value;
        params.power_kw = parseFloat(document.getElementById('power_kw').value);

        // Поля из активной панели типа
        const panel = document.getElementById('params_' + activeType);
        if (panel) {
            panel.querySelectorAll('input, select').forEach(el => {
                const name = el.name;
                if (!name) return;
                if (el.type === 'number') {
                    params[name] = parseFloat(el.value);
                } else if (el.tagName === 'SELECT') {
                    // Boolean select
                    if (el.value === 'true') params[name] = true;
                    else if (el.value === 'false') params[name] = false;
                    else params[name] = el.value;
                } else {
                    params[name] = el.value;
                }
            });
        }

        // Целые числа
        const intFields = ['smoke_tube_count', 'smoke_tube_rows', 'support_count',
                          'safety_valve_count', 'boiler_count', 'chimney_count',
                          'expansion_tank_count', 'pump_winter_count', 'pump_summer_count',
                          'pump_gvs_count', 'pump_makeup_count', 'louver_count',
                          'mud_filter_dn', 'water_meter_dn'];
        for (const f of intFields) {
            if (f in params) params[f] = Math.round(params[f]);
        }

        return params;
    }

    // Предпросмотр
    btnPreview.addEventListener('click', async () => {
        const params = getParams();
        btnPreview.disabled = true;
        previewContainer.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch('/api/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const err = await response.text();
                throw new Error(err);
            }

            const svgText = await response.text();
            previewContainer.innerHTML = svgText;
        } catch (error) {
            previewContainer.innerHTML = `
                <div style="color: #dc2626; text-align: center; padding: 20px;">
                    <p style="font-weight: 600;">Ошибка генерации:</p>
                    <p style="font-size: 0.85rem; margin-top: 8px;">${error.message}</p>
                </div>
            `;
        } finally {
            btnPreview.disabled = false;
        }
    });

    // Экспорт SVG
    btnExportSVG.addEventListener('click', async () => {
        const params = getParams();
        btnExportSVG.disabled = true;
        try {
            const response = await fetch('/api/export/svg', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            if (!response.ok) throw new Error('Ошибка экспорта');
            const blob = await response.blob();
            downloadBlob(blob, `${params.name || 'boiler'}.svg`);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        } finally {
            btnExportSVG.disabled = false;
        }
    });

    // Экспорт DXF
    btnExportDXF.addEventListener('click', async () => {
        const params = getParams();
        btnExportDXF.disabled = true;
        try {
            const response = await fetch('/api/export/dxf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            if (!response.ok) throw new Error('Ошибка экспорта');
            const blob = await response.blob();
            downloadBlob(blob, `${params.name || 'boiler'}.dxf`);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        } finally {
            btnExportDXF.disabled = false;
        }
    });

    // Экспорт PDF
    btnExportPDF.addEventListener('click', async () => {
        const params = getParams();
        btnExportPDF.disabled = true;
        try {
            const response = await fetch('/api/export/pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            if (!response.ok) throw new Error('Ошибка экспорта PDF');
            const blob = await response.blob();
            downloadBlob(blob, `${params.name || 'boiler'}.pdf`);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        } finally {
            btnExportPDF.disabled = false;
        }
    });

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Автообновление при изменении (debounce)
    let debounceTimer;
    form.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (previewContainer.querySelector('svg')) {
                btnPreview.click();
            }
        }, 1000);
    });
});