let world; 
let activeDisasters = []; // Local persistence

document.addEventListener('DOMContentLoaded', () => {
    initGlobe();
    setupUI();
    setupChat();
});

function setupUI() {

    const downloadBtn = document.getElementById('downloadReportBtn');
    if(downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            window.location.href = '/api/download-report';
        });
    }
    
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
        setTimeout(() => window.dispatchEvent(new Event('resize')), 350);
    });

    const refresh = () => updateGlobe();
    document.getElementById('regionFilter').addEventListener('change', refresh);
    document.getElementById('productFilter').addEventListener('change', refresh);

    document.getElementById('toggleGodMode').addEventListener('click', () => {
        document.getElementById('godModeControls').classList.toggle('hidden');
    });

    document.getElementById('confirmDisaster').addEventListener('click', executeDisaster);

    // Modal
    const modal = document.getElementById('chatModal');
    document.getElementById('expandChat').addEventListener('click', () => {
        modal.classList.remove('hidden');
        document.getElementById('modalChatMessages').scrollTop = 99999;
    });
    document.getElementById('closeChatModal').addEventListener('click', () => modal.classList.add('hidden'));
}

function initGlobe() {
    const elem = document.getElementById('globeContainer');
    world = Globe()
        (elem)
        .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')

        .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
        .atmosphereColor('#00f3ff')
        .atmosphereAltitude(0.15)
        .pointLat('lat').pointLng('lon').pointColor('color')
        .pointAltitude(0.02).pointRadius(0.4)
        .pointLabel(d => `
            <div style="background: rgba(0,0,0,0.9); padding: 8px; border: 1px solid ${d.color}; border-radius: 4px; font-family: sans-serif;">
                <b style="color:${d.color}">${d.name}</b><br/>
                ${d.status === 'Disrupted' ? '<b style="color:red">⚠ SYSTEM FAILURE</b><br>' : ''}
                ${d.city}, ${d.country}
            </div>
        `)
        .onPointClick(node => {
            world.pointOfView({ lat: node.lat, lng: node.lon, altitude: 1.5 }, 1000);
            askTitan(`Analyze risk for ${node.name}`);
        })
        .arcStartLat('startLat').arcStartLng('startLng').arcEndLat('endLat').arcEndLng('endLng')
        .arcColor('color').arcDashLength(0.4).arcDashGap(0.2).arcDashAnimateTime(2000).arcStroke(0.3)
        .ringLat('lat').ringLng('lon').ringColor('color').ringMaxRadius('maxR')
        .ringPropagationSpeed('propagationSpeed').ringRepeatPeriod(1000);

    updateGlobe();
}

function updateGlobe() {
    const region = document.getElementById('regionFilter').value;
    const product = document.getElementById('productFilter').value;
    const loader = document.getElementById('loadingOverlay');
    
    if(loader) loader.style.display = 'flex';

    fetch(`/api/globe-data?region=${region}&product=${product}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) return;

            world.pointsData(data.nodes || []); 
            world.arcsData(data.routes || []);
            
            // MERGE Backend Disasters with Local Disasters to prevent flickering
            // We use the local ones for immediate visual feedback
            const backendDisasters = data.disasters || [];
            
            // Add backend ones to local if not exists (simple dedupe)
            backendDisasters.forEach(bd => {
                const exists = activeDisasters.find(ad => Math.abs(ad.lat - bd.lat) < 0.1 && Math.abs(ad.lon - bd.lon) < 0.1);
                if (!exists) activeDisasters.push(bd);
            });

            world.ringsData(activeDisasters);
            
            safeSetText('totalFacilities', data.nodes ? data.nodes.length : 0);
            safeSetText('totalRoutes', data.routes ? data.routes.length : 0);
            safeSetText('totalDisasters', activeDisasters.length);
            
            if(loader) loader.style.display = 'none';
        });
}

function safeSetText(id, val) {
    const el = document.getElementById(id);
    if(el) el.innerText = val;
}

function executeDisaster() {
    const type = document.getElementById('disasterType').value;
    const lat = parseFloat(document.getElementById('godLat').value);
    const lon = parseFloat(document.getElementById('godLon').value);
    
    if(!lat || !lon) { alert("Enter Coords"); return; }
    
    const btn = document.getElementById('confirmDisaster');
    btn.innerText = "Simulating...";
    
    // 1. Immediate Visual Update (The 3-second fix)
    const newDisaster = { lat: lat, lon: lon, color: "red", maxR: 15, propagationSpeed: 4 };
    activeDisasters.push(newDisaster);
    world.ringsData(activeDisasters);
    world.pointOfView({ lat: lat, lng: lon, altitude: 1.0 }, 1500);

    fetch('/api/god-mode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type, lat, lon})
    })
    .then(r => r.json())
    .then(data => {
        btn.innerText = "💥 EXECUTE IMPACT";
        if(data.status === 'success') {
            if(data.sitrep) {
                const html = marked.parse(data.sitrep);
                addMessage('TITAN', html, 'bot');
            }
            // Update globe to show Broken Nodes (Black/Red)
            setTimeout(updateGlobe, 1000); 
        }
    });
}

// --- CHAT ---
function setupChat() {
    const btn = document.getElementById('chatSend');
    const input = document.getElementById('chatInput');
    const modalBtn = document.getElementById('modalChatSend');
    const modalInput = document.getElementById('modalChatInput');

    function send(txt) {
        if(!txt) return;
        addMessage('You', txt, 'user');
        input.value = '';
        modalInput.value = '';
        askTitan(txt);
    }

    if(btn) btn.onclick = () => send(input.value);
    if(input) input.onkeypress = (e) => { if(e.key === 'Enter') send(input.value); };
    if(modalBtn) modalBtn.onclick = () => send(modalInput.value);
}

function askTitan(query) {
    addMessage('TITAN', 'Analyzing...', 'bot loading');
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: query})
    })
    .then(r => r.json())
    .then(data => {
        removeLoading();
        const html = marked.parse(data.response);
        addMessage('TITAN', html, 'bot');
    });
}

function addMessage(sender, content, type) {
    ['chatMessages', 'modalChatMessages'].forEach(id => {
        const box = document.getElementById(id);
        if(!box) return;
        
        if (type.includes('loading')) {
            const d = document.createElement('div');
            d.className = 'message bot loading-msg';
            d.innerText = content;
            box.appendChild(d);
        } else {
            const d = document.createElement('div');
            d.className = `message ${type === 'user' ? 'user' : 'bot'}`;
            if(type === 'user') d.innerText = content;
            else d.innerHTML = content;
            box.appendChild(d);
        }
        box.scrollTop = box.scrollHeight;
    });
}

function removeLoading() {
    document.querySelectorAll('.loading-msg').forEach(el => el.remove());
}