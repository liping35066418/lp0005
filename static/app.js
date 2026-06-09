const STYLE_EMOJIS = {
    anime: '🌸',
    sketch: '✏️',
    vintage: '📷',
    cartoon: '🎨',
    oil_paint: '🖼️',
    watercolor: '💧',
    pixel: '👾',
    cyberpunk: '🌆',
};

const state = {
    styles: [],
    singleFile: null,
    selectedStyle: 'anime',
    intensity: 0.8,
    batchFiles: [],
    batchStyle: 'anime',
    batchIntensity: 0.8,
    batchResults: [],
};

const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, children = []) => {
    const e = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
        if (k === 'class') e.className = v;
        else if (k === 'style') Object.assign(e.style, v);
        else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
        else if (v !== null && v !== undefined) e.setAttribute(k, v);
    });
    if (!Array.isArray(children)) children = [children];
    children.filter(c => c !== null && c !== undefined).forEach(c => {
        if (typeof c === 'string') {
            e.appendChild(document.createTextNode(c));
        } else if (c instanceof Node) {
            e.appendChild(c);
        }
    });
    return e;
};

function showToast(msg, type = 'info') {
    const toast = $('toast');
    toast.textContent = msg;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

async function loadStyles() {
    try {
        const res = await fetch('/api/styles');
        const data = await res.json();
        state.styles = data.styles;
        renderStyleGrid();
        renderBatchStyleGrid();
        renderStyleDetails();
    } catch (e) {
        showToast('加载风格列表失败', 'error');
    }
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        renderStats(data.stats);
    } catch (e) {
        console.error('加载统计失败', e);
    }
}

function renderStyleGrid() {
    const grid = $('style-grid');
    grid.innerHTML = '';
    state.styles.forEach(s => {
        const card = el('div', {
            class: `style-card ${state.selectedStyle === s.id ? 'active' : ''}`,
            onclick: () => selectStyle(s.id),
        }, [
            el('span', { class: 'emoji' }, STYLE_EMOJIS[s.id] || '🎨'),
            el('div', { class: 'name' }, s.name),
            el('div', { class: 'desc' }, s.description),
        ]);
        grid.appendChild(card);
    });
}

function renderBatchStyleGrid() {
    const grid = $('batch-style-grid');
    grid.innerHTML = '';
    state.styles.forEach(s => {
        const card = el('div', {
            class: `style-card ${state.batchStyle === s.id ? 'active' : ''}`,
            onclick: () => selectBatchStyle(s.id),
        }, [
            el('span', { class: 'emoji' }, STYLE_EMOJIS[s.id] || '🎨'),
            el('div', { class: 'name' }, s.name),
            el('div', { class: 'desc' }, s.description),
        ]);
        grid.appendChild(card);
    });
}

function renderStyleDetails() {
    const container = $('style-details');
    container.innerHTML = '';
    const statsData = { style_usage: {} };
    try {
        Object.assign(statsData, window.__statsCache || {});
    } catch (e) {}

    const total = Object.values(statsData.style_usage || {}).reduce((a, b) => a + b, 0) || 1;

    state.styles.forEach(s => {
        const usage = statsData.style_usage?.[s.id] || 0;
        const percent = ((usage / total) * 100).toFixed(1);
        const card = el('div', { class: 'style-detail-card' }, [
            el('div', { class: 'style-detail-header' }, [
                el('span', { class: 'style-detail-emoji' }, STYLE_EMOJIS[s.id] || '🎨'),
                el('div', {}, [
                    el('div', { class: 'style-detail-name' }, s.name),
                ]),
            ]),
            el('div', { class: 'style-detail-desc' }, s.description),
            el('div', { class: 'style-detail-stats' }, [
                el('div', { class: 'style-detail-stat' }, [
                    el('div', { class: 'style-detail-stat-label' }, '使用次数'),
                    el('div', { class: 'style-detail-stat-value' }, String(usage)),
                ]),
                el('div', { class: 'style-detail-stat' }, [
                    el('div', { class: 'style-detail-stat-label' }, '占比'),
                    el('div', { class: 'style-detail-stat-value' }, `${percent}%`),
                ]),
            ]),
        ]);
        container.appendChild(card);
    });
}

function selectStyle(id) {
    state.selectedStyle = id;
    renderStyleGrid();
}

function selectBatchStyle(id) {
    state.batchStyle = id;
    renderBatchStyleGrid();
}

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            $(`tab-${tab}`).classList.add('active');
            if (tab === 'stats') {
                loadStats();
            }
        });
    });
}

function setupSingleUpload() {
    const dropZone = $('drop-zone');
    const fileInput = $('file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleSingleFile(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSingleFile(e.target.files[0]);
        }
    });
}

function handleSingleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('请上传图片文件', 'error');
        return;
    }
    if (file.size > 50 * 1024 * 1024) {
        showToast('文件超过 50MB 限制', 'error');
        return;
    }
    state.singleFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = $('original-preview');
        preview.innerHTML = '';
        const img = el('img', { src: e.target.result, alt: '原图' });
        preview.appendChild(img);

        const result = $('result-preview');
        result.innerHTML = '';
        result.appendChild(
            el('div', { class: 'placeholder' }, [
                el('span', { class: 'placeholder-icon' }, '🎬'),
                el('p', {}, '点击「开始转换」查看效果'),
            ])
        );
        $('download-btn').classList.add('hidden');
    };
    reader.readAsDataURL(file);
    $('convert-btn').disabled = false;
    showToast(`已选择: ${file.name}`, 'success');
}

function setupIntensitySlider() {
    const slider = $('intensity-slider');
    const num = $('intensity-num');
    slider.addEventListener('input', () => {
        state.intensity = slider.value / 100;
        num.textContent = slider.value;
    });

    const bSlider = $('batch-intensity-slider');
    const bNum = $('batch-intensity-num');
    bSlider.addEventListener('input', () => {
        state.batchIntensity = bSlider.value / 100;
        bNum.textContent = bSlider.value;
    });
}

function setupConvertBtn() {
    $('convert-btn').addEventListener('click', async () => {
        if (!state.singleFile) {
            showToast('请先上传图片', 'error');
            return;
        }

        const btn = $('convert-btn');
        btn.disabled = true;
        $('loading-overlay').classList.remove('hidden');

        try {
            const formData = new FormData();
            formData.append('file', state.singleFile);
            formData.append('style', state.selectedStyle);
            formData.append('intensity', state.intensity);

            const res = await fetch('/api/process', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || '转换失败');
            }

            const result = $('result-preview');
            result.innerHTML = '';
            const img = el('img', { src: data.url, alt: '转换结果' });
            result.appendChild(img);

            const dl = $('download-btn');
            dl.classList.remove('hidden');
            dl.onclick = () => downloadImage(data.url, `${state.singleFile.name.split('.')[0]}_${data.style}.png`);

            await loadStats();
            showToast('转换成功！', 'success');
        } catch (e) {
            showToast(e.message || '转换失败', 'error');
        } finally {
            $('loading-overlay').classList.add('hidden');
            btn.disabled = false;
        }
    });
}

function downloadImage(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function setupBatchUpload() {
    const dropZone = $('batch-drop-zone');
    const fileInput = $('batch-file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addBatchFiles(Array.from(e.dataTransfer.files));
    });
    fileInput.addEventListener('change', (e) => {
        addBatchFiles(Array.from(e.target.files));
        fileInput.value = '';
    });

    $('batch-clear-btn').addEventListener('click', () => {
        state.batchFiles = [];
        state.batchResults = [];
        renderBatchFileList();
        renderBatchResults();
        $('batch-convert-btn').disabled = true;
        $('batch-download-all').classList.add('hidden');
        showToast('已清空列表');
    });

    $('batch-convert-btn').addEventListener('click', handleBatchConvert);

    $('batch-download-all').addEventListener('click', handleBatchDownload);
}

function addBatchFiles(files) {
    const images = files.filter(f => f.type.startsWith('image/'));
    if (images.length === 0) {
        showToast('请选择图片文件', 'error');
        return;
    }
    const remaining = 20 - state.batchFiles.length;
    const toAdd = images.slice(0, remaining);
    state.batchFiles.push(...toAdd);

    if (images.length > remaining) {
        showToast(`最多处理 20 张，已截取前 ${remaining} 张`, 'error');
    }

    renderBatchFileList();
    $('batch-convert-btn').disabled = state.batchFiles.length === 0;
    showToast(`已添加 ${toAdd.length} 张图片`, 'success');
}

function renderBatchFileList() {
    const container = $('batch-file-list');
    container.innerHTML = '';
    state.batchFiles.forEach((file, idx) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const item = el('div', { class: 'batch-file-item' }, [
                el('img', { src: e.target.result }),
                el('div', { class: 'batch-file-info' }, [
                    el('div', { class: 'batch-file-name' }, file.name),
                ]),
                el('button', {
                    class: 'batch-file-remove',
                    title: '移除',
                    onclick: (evt) => {
                        evt.stopPropagation();
                        state.batchFiles.splice(idx, 1);
                        renderBatchFileList();
                        $('batch-convert-btn').disabled = state.batchFiles.length === 0;
                    },
                }, '✕'),
            ]);
            container.appendChild(item);
        };
        reader.readAsDataURL(file);
    });
}

async function handleBatchConvert() {
    if (state.batchFiles.length === 0) {
        showToast('请先上传图片', 'error');
        return;
    }

    const btn = $('batch-convert-btn');
    btn.disabled = true;
    $('batch-progress').classList.remove('hidden');

    const formData = new FormData();
    state.batchFiles.forEach(f => formData.append('files', f));
    formData.append('style', state.batchStyle);
    formData.append('intensity', state.batchIntensity);

    const total = state.batchFiles.length;
    let done = 0;
    $('progress-fill').style.width = '5%';
    $('progress-text').textContent = `正在上传...`;

    try {
        const res = await fetch('/api/batch', {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || '批量处理失败');
        }

        const interval = setInterval(() => {
            done = Math.min(done + 1, total);
            const pct = Math.round((done / total) * 100);
            $('progress-fill').style.width = `${pct}%`;
            $('progress-text').textContent = `处理中... ${done}/${total}`;
            if (done >= total) {
                clearInterval(interval);
                $('progress-text').textContent = `完成！成功 ${data.success_count}，失败 ${data.error_count}`;
            }
        }, 200);

        state.batchResults = data.results;

        setTimeout(() => {
            renderBatchResults();
            if (data.success_count > 0) {
                $('batch-download-all').classList.remove('hidden');
            }
            loadStats();
            showToast(`批量处理完成！成功 ${data.success_count} 张`, 'success');
        }, total * 200 + 300);
    } catch (e) {
        showToast(e.message || '批量处理失败', 'error');
        $('batch-progress').classList.add('hidden');
    } finally {
        btn.disabled = false;
    }
}

function renderBatchResults() {
    const container = $('batch-results');
    container.innerHTML = '';
    state.batchResults.forEach((r, idx) => {
        const file = state.batchFiles[idx];
        const origUrl = file ? URL.createObjectURL(file) : '';
        const hasError = !!r.error;

        const card = el('div', { class: 'batch-result-card' }, [
            el('div', { class: 'batch-result-images' }, [
                origUrl ? el('img', { src: origUrl, title: '原图' }) : el('div'),
                r.url ? el('img', { src: r.url, title: '转换后' }) : el('div'),
            ]),
            el('div', { class: 'batch-result-info' }, [
                el('div', { class: 'batch-result-name' }, r.name || `图片 ${idx + 1}`),
                el('div', { class: 'batch-result-status' }, [
                    hasError
                        ? el('span', { class: 'status-error' }, `❌ ${r.error}`)
                        : el('span', { class: 'status-success' }, '✅ 转换成功'),
                    !hasError && r.url
                        ? el('button', {
                            class: 'mini-btn',
                            onclick: () => downloadImage(r.url, `${(r.name || 'image').split('.')[0]}_styled.png`),
                        }, '下载')
                        : null,
                ]),
            ]),
        ]);
        container.appendChild(card);
    });
}

async function handleBatchDownload() {
    const filenames = state.batchResults.filter(r => !r.error && r.filename).map(r => r.filename);
    if (filenames.length === 0) {
        showToast('没有可下载的文件', 'error');
        return;
    }

    try {
        const res = await fetch('/api/batch/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filenames }),
        });
        if (!res.ok) throw new Error('打包失败');

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `styled_images_${Date.now()}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('打包下载开始', 'success');
    } catch (e) {
        showToast(e.message || '下载失败', 'error');
    }
}

function renderStats(stats) {
    window.__statsCache = stats || {};

    $('stat-total').textContent = stats?.total_processed || 0;

    const usage = stats?.style_usage || {};
    const sortedStyles = Object.entries(usage).sort((a, b) => b[1] - a[1]);
    const topStyleId = sortedStyles[0]?.[0];
    const topStyleName = state.styles.find(s => s.id === topStyleId)?.name || '-';
    $('stat-top-style').textContent = topStyleName;

    const today = new Date().toISOString().slice(0, 10);
    $('stat-today').textContent = stats?.daily_processed?.[today] || 0;

    $('stat-style-count').textContent = state.styles.length;

    renderUsageChart(usage);
    renderTrendChart(stats?.daily_processed || {});
    renderStyleDetails();
}

function renderUsageChart(usage) {
    const container = $('usage-chart');
    container.innerHTML = '';
    const total = Object.values(usage).reduce((a, b) => a + b, 0) || 1;

    if (Object.keys(usage).length === 0) {
        container.innerHTML = '<p style="color:var(--text-dim);text-align:center;padding:40px 0;">暂无使用数据，快去转换一张图片吧！</p>';
        return;
    }

    const sorted = state.styles.map(s => ({
        id: s.id,
        name: s.name,
        count: usage[s.id] || 0,
        emoji: STYLE_EMOJIS[s.id] || '🎨',
    })).sort((a, b) => b.count - a.count);

    sorted.forEach(item => {
        const pct = Math.round((item.count / total) * 100);
        const row = el('div', { class: 'usage-bar-item' }, [
            el('div', { class: 'usage-bar-label' }, [
                el('span', {}, item.emoji),
                el('span', {}, item.name),
            ]),
            el('div', { class: 'usage-bar-track' }, [
                el('div', {
                    class: 'usage-bar-fill',
                    style: { width: `${Math.max(pct, item.count > 0 ? 5 : 0)}%` },
                }),
            ]),
            el('div', { class: 'usage-bar-value' }, `${item.count} 次`),
        ]);
        container.appendChild(row);
    });
}

function renderTrendChart(dailyData) {
    const container = $('trend-chart');
    container.innerHTML = '';

    const days = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const key = d.toISOString().slice(0, 10);
        days.push({
            date: key,
            label: `${d.getMonth() + 1}/${d.getDate()}`,
            count: dailyData[key] || 0,
        });
    }

    const max = Math.max(...days.map(d => d.count), 1);
    const hasData = days.some(d => d.count > 0);

    if (!hasData) {
        container.innerHTML = '<p style="color:var(--text-dim);text-align:center;flex:1;display:flex;align-items:center;justify-content:center;">近7日暂无处理数据</p>';
        return;
    }

    days.forEach(day => {
        const h = Math.max(4, Math.round((day.count / max) * 240));
        const wrap = el('div', { class: 'trend-bar-wrap' }, [
            el('div', { class: 'trend-bar', style: { height: `${h}px` } }, [
                day.count > 0 ? el('span', { class: 'trend-bar-value' }, String(day.count)) : null,
            ]),
            el('div', { class: 'trend-bar-label' }, day.label),
        ]);
        container.appendChild(wrap);
    });
}

function init() {
    setupTabs();
    setupSingleUpload();
    setupBatchUpload();
    setupIntensitySlider();
    setupConvertBtn();
    loadStyles();
    loadStats();
}

document.addEventListener('DOMContentLoaded', init);
