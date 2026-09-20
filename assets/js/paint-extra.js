const STORE_KEY = 'bthq-paint-schemes';
let undoStack = [];
let activeFaction = '';

function snapshot(){
    return {
        scheme: Object.assign({}, scheme),
        planMap: planMap.slice(),
        planPattern: planPattern, planShade: planShade, planPips: planPips, planSel: planSel,
        name: (document.getElementById('scheme-name')||{}).value || 'Custom scheme'
    };
}
function pushUndo(){
    undoStack.push(snapshot());
    if(undoStack.length > 25) undoStack.shift();
    var b = document.getElementById('undo-btn');
    if(b) b.disabled = false;
}
function applySnap(s){
    scheme = Object.assign({}, s.scheme);
    planMap = s.planMap.slice();
    planPattern = s.planPattern; planShade = s.planShade; planPips = s.planPips; planSel = s.planSel;
    var n = document.getElementById('scheme-name');
    if(n) n.value = s.name || 'Custom scheme';
    document.getElementById('plan-sel-name').textContent = LOC[planSel].label;
    rebuildAll();
}
function undoLast(){
    var s = undoStack.pop();
    if(!s) return;
    applySnap(s);
    var b = document.getElementById('undo-btn');
    if(b) b.disabled = !undoStack.length;
}
function nativeColorChanged(val){
    if(!/^#[0-9a-fA-F]{6}$/i.test(val)) return;
    pushUndo();
    activeFaction = '';
    markFaction();
    var hsl = hexToHsl(val);
    currentHue=hsl[0]; currentSat=hsl[1]; wheelBrightness=hsl[2];
    document.getElementById('brightness-slider').value=hsl[2];
    drawWheel();
    setActiveColour(val);
}
function schemeTitle(){
    var el = document.getElementById('scheme-name');
    return (el && el.value.trim()) ? el.value.trim() : 'Custom scheme';
}
function updateSchemeName(name){
    var el = document.getElementById('scheme-name');
    if(el && name) el.value = name.replace(/\bScheme\b/i,'').trim() || name;
}
function rebuildAll(){
    buildZoneButtons(); buildSchemeDisplay();
    buildPaintPlan(); buildPlanChips(); buildPatternChips();
    syncPickerToZone(); refreshShop(); markFaction();
}
function refreshShop(){
    var el = document.getElementById('shop-list');
    if(!el) return;
    var seen = {};
    var rows = [];
    ZONES.forEach(function(z){
        var col = scheme[z.id] || z.default;
        var match = findPaintMatch(col);
        var key = (match ? match.citadel : col).toLowerCase();
        if(seen[key]) return;
        seen[key] = 1;
        rows.push({z:z, col:col, match:match});
    });
    el.innerHTML = rows.map(function(r){
        var cit = r.match ? r.match.citadel : 'No close match';
        var val = r.match ? r.match.vallejo : 'mix from the hex';
        return '<li><span class="shop-dot" style="background:'+r.col+'"></span><div>'+cit+'<small>Vallejo '+val+' \u00b7 '+r.col+'</small></div></li>';
    }).join('');
}
function shopText(){
    var lines = [schemeTitle(), ''];
    ZONES.forEach(function(z){
        var col = scheme[z.id] || z.default;
        var match = findPaintMatch(col);
        lines.push(z.label + '  ' + col);
        lines.push(match ? '  Citadel ' + match.citadel + '  /  Vallejo ' + match.vallejo : '  (no close match)');
    });
    return lines.join('\n');
}
function copyShop(){
    var t = shopText();
    var btn = (typeof event!=='undefined') ? event.target : null;
    navigator.clipboard.writeText(t).then(function(){ flashBtn(btn, 'Copied'); }).catch(function(){ prompt('Shopping list', t); });
}
function flashBtn(btn, label){
    if(!btn) return;
    var orig = btn.textContent;
    btn.textContent = label;
    setTimeout(function(){ btn.textContent = orig; }, 1600);
}
function copySchemeURL(){
    var p = new URLSearchParams();
    ZONES.forEach(function(z){ if(scheme[z.id]) p.set(z.id, scheme[z.id].replace('#','')); });
    p.set('map', planMap.map(function(z){ return ZCODE[z]||'p'; }).join(''));
    if(planPattern!=='flat') p.set('pat', planPattern);
    if(!planShade) p.set('sh','0');
    if(!planPips) p.set('pip','0');
    var n = schemeTitle();
    if(n && n.toLowerCase()!=='custom scheme') p.set('n', n);
    var url = location.origin + location.pathname + '?' + p.toString();
    var btn = (typeof event!=='undefined') ? event.target : null;
    navigator.clipboard.writeText(url).then(function(){ flashBtn(btn, 'Copied'); }).catch(function(){ prompt('Share link:', url); });
}
function loadFromURL(){
    scheme = defaultScheme();
    var p = new URLSearchParams(location.search);
    ZONES.forEach(function(z){ if(p.has(z.id)) scheme[z.id] = '#' + p.get(z.id); });
    var m = p.get('map');
    if(m && m.length===LOC.length && m.split('').every(function(ch){ return ZFROM[ch]; }))
        planMap = m.split('').map(function(ch){ return ZFROM[ch]; });
    var pat = p.get('pat');
    if(pat && PATTERNS.some(function(x){ return x.id===pat; })) planPattern = pat;
    if(p.get('sh')==='0') planShade = false;
    if(p.get('pip')==='0') planPips = false;
    if(p.get('n')) updateSchemeName(p.get('n'));
}
function readSaved(){
    try { return JSON.parse(localStorage.getItem(STORE_KEY)||'[]'); }
    catch(e){ return []; }
}
function writeSaved(list){
    localStorage.setItem(STORE_KEY, JSON.stringify(list.slice(0,12)));
}
function saveScheme(){
    var list = readSaved();
    var entry = Object.assign(snapshot(), { id: Date.now() });
    var i = list.findIndex(function(x){ return x.name.toLowerCase()===entry.name.toLowerCase(); });
    if(i>=0) list[i] = entry; else list.unshift(entry);
    writeSaved(list);
    renderSaved();
    flashBtn((typeof event!=='undefined') ? event.target : null, 'Saved');
}
function loadSaved(id){
    var s = readSaved().find(function(x){ return x.id===id; });
    if(!s) return;
    pushUndo();
    applySnap(s);
}
function deleteSaved(id, ev){
    if(ev) ev.stopPropagation();
    writeSaved(readSaved().filter(function(x){ return x.id!==id; }));
    renderSaved();
}
function renderSaved(){
    var el = document.getElementById('saved-list');
    if(!el) return;
    var list = readSaved();
    if(!list.length){ el.innerHTML = '<span style="color:#6f6b64;font-size:.75rem;">None yet \u2014 Save keeps a scheme here.</span>'; return; }
    el.innerHTML = list.map(function(s){
        return '<span class="saved-chip" onclick="loadSaved('+s.id+')">'+escapeHtml(s.name)+'<button type="button" aria-label="Delete" onclick="deleteSaved('+s.id+',event)">\u00d7</button></span>';
    }).join('');
}
function escapeHtml(s){
    return String(s).replace(/[&<>"']/g, function(c){
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]);
    });
}
function downloadPNG(){
    var svg = document.getElementById('paint-plan');
    var clone = svg.cloneNode(true);
    clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
    clone.setAttribute('width','896');
    clone.setAttribute('height','956');
    var xml = new XMLSerializer().serializeToString(clone);
    var blob = new Blob([xml], {type:'image/svg+xml;charset=utf-8'});
    var url = URL.createObjectURL(blob);
    var img = new Image();
    img.onload = function(){
        var c = document.createElement('canvas');
        c.width = 896; c.height = 956;
        var ctx = c.getContext('2d');
        ctx.fillStyle = '#0a0a0b';
        ctx.fillRect(0,0,c.width,c.height);
        ctx.drawImage(img,0,0,c.width,c.height);
        URL.revokeObjectURL(url);
        c.toBlob(function(b){
            var a = document.createElement('a');
            a.href = URL.createObjectURL(b);
            a.download = (schemeTitle().replace(/[^\w]+/g,'-').replace(/^-|-$/g,'') || 'scheme') + '.png';
            a.click();
        }, 'image/png');
    };
    img.onerror = function(){
        var a = document.createElement('a');
        a.href = url; a.download = 'scheme.svg'; a.click();
    };
    img.src = url;
}
function randomScheme(){
    pushUndo();
    var f = FACTIONS[Math.floor(Math.random()*FACTIONS.length)];
    var L = LAYOUTS[Math.floor(Math.random()*LAYOUTS.length)];
    var P = PATTERNS[Math.floor(Math.random()*PATTERNS.length)];
    Object.assign(scheme, f.c);
    planMap = L.map.slice();
    planPattern = P.id;
    activeFaction = f.name;
    updateSchemeName(f.name);
    rebuildAll();
    buildPatternChips();
}
function markFaction(){
    document.querySelectorAll('.faction-btn').forEach(function(b){
        b.classList.toggle('is-on', b.dataset.name===activeFaction);
    });
}
function buildFactionGrid(){
    var el = document.getElementById('faction-grid');
    if(!el) return;
    el.innerHTML = '';
    var groups = [
        { id:'is', label:'Great Houses' },
        { id:'clan', label:'Clans' },
        { id:'merc', label:'Mercs & other' }
    ];
    groups.forEach(function(g){
        var wrap = document.createElement('div');
        wrap.className = 'faction-group';
        wrap.innerHTML = '<b>'+g.label+'</b>';
        var grid = document.createElement('div');
        grid.className = 'faction-grid';
        FACTIONS.filter(function(f){ return f.g===g.id; }).forEach(function(f){
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'faction-btn'+(activeFaction===f.name?' is-on':'');
            btn.dataset.name = f.name;
            btn.style.cssText = 'background:'+f.bg+';color:'+f.fg+';border-color:'+f.bg+';';
            btn.textContent = f.name;
            btn.onclick = function(){ pushUndo(); activeFaction=f.name; applyFaction(f); markFaction(); };
            grid.appendChild(btn);
        });
        wrap.appendChild(grid);
        el.appendChild(wrap);
    });
}
var _setActiveColour = setActiveColour;
setActiveColour = function(hex, updateHex){
    if(updateHex===undefined) updateHex = true;
    _setActiveColour(hex, updateHex);
    var native = document.getElementById('native-color');
    if(native) native.value = hex;
    refreshShop();
};
var _applyFaction = applyFaction;
applyFaction = function(f){ _applyFaction(f); refreshShop(); };
var _resetScheme = resetScheme;
resetScheme = function(){
    pushUndo();
    activeFaction = '';
    _resetScheme();
    var n = document.getElementById('scheme-name');
    if(n) n.value = 'Custom scheme';
    refreshShop(); markFaction(); renderSaved();
};
var _assignZone = assignZone;
assignZone = function(zid){ pushUndo(); _assignZone(zid); };
var _syncPickerToZone = syncPickerToZone;
syncPickerToZone = function(){
    _syncPickerToZone();
    var native = document.getElementById('native-color');
    var col = scheme[currentZone] || '#7a7a7a';
    if(native) native.value = col;
};
wheelPick = function(e){
    var rect=wheelCanvas.getBoundingClientRect();
    var sx=wheelCanvas.width/rect.width, sy=wheelCanvas.height/rect.height;
    var x=(e.clientX-rect.left)*sx-wheelRadius;
    var y=(e.clientY-rect.top)*sy-wheelRadius;
    var dist=Math.sqrt(x*x+y*y), r=wheelRadius-2;
    if(dist>r)return;
    currentHue=Math.round(Math.atan2(y,x)*180/Math.PI); if(currentHue<0)currentHue+=360;
    currentSat=Math.round((dist/r)*100);
    drawWheel();
    setActiveColour(hslToHex(currentHue,currentSat,wheelBrightness));
};
var _initWheel = initWheel;
initWheel = function(){
    _initWheel();
    if(wheelCanvas){
        wheelCanvas.addEventListener('mousedown', function(){ pushUndo(); activeFaction=''; markFaction(); });
        wheelCanvas.addEventListener('touchstart', function(){ pushUndo(); activeFaction=''; markFaction(); }, {passive:true});
    }
};
var _hexInputChanged = hexInputChanged;
hexInputChanged = function(val){
    if(/^#[0-9a-fA-F]{6}$/.test(val)){ pushUndo(); activeFaction=''; markFaction(); }
    _hexInputChanged(val);
};
var _buildLayoutChips = buildLayoutChips;
buildLayoutChips = function(){
    _buildLayoutChips();
    document.querySelectorAll('#plan-layouts .zone-chip').forEach(function(b,i){
        b.onclick = function(){
            pushUndo();
            planMap = LAYOUTS[i].map.slice();
            buildPaintPlan();
            buildPlanChips();
        };
    });
};
window.addEventListener('DOMContentLoaded', function(){
    renderSaved();
    refreshShop();
    markFaction();
    document.addEventListener('keydown', function(e){
        if(e.target && /input|textarea/i.test(e.target.tagName)) return;
        if((e.metaKey||e.ctrlKey) && e.key.toLowerCase()==='z'){ e.preventDefault(); undoLast(); }
        var n = parseInt(e.key,10);
        if(n>=1 && n<=ZONES.length){ selectZone(ZONES[n-1].id); }
    });
});
