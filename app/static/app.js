const KEY='pharmagraph_syntax_v2';let chats=readChats(),active=chats[0]?.id||null,busy=false;const $=id=>document.getElementById(id);const q=$('question');function readChats(){try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v:[]}catch{return []}}function save(){try{localStorage.setItem(KEY,JSON.stringify(chats))}catch(e){console.warn('History storage unavailable',e)}}function current(){return chats.find(c=>c.id===active)}function create(){if(busy)return;const c={id:((globalThis.crypto && typeof crypto.randomUUID === 'function') ? crypto.randomUUID() : String(Date.now()) + '-' + Math.random().toString(36).slice(2)),title:'New research session',messages:[],created:Date.now()};chats.unshift(c);active=c.id;save();render();q.focus()}function choose(id){if(busy)return;active=id;render()}function remove(id){if(busy)return;chats=chats.filter(c=>c.id!==id);if(active===id)active=chats[0]?.id||null;save();render()}function el(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n}function renderHistory(){const root=$('history');root.replaceChildren();for(const c of chats){const b=el('button','history-item'+(c.id===active?' selected':''));const ico=el('span','', '◷'),title=el('span','history-title',c.title),del=el('button','history-delete','×');del.title='Delete chat';del.addEventListener('click',e=>{e.stopPropagation();if(confirm('Delete this conversation?'))remove(c.id)});b.append(ico,title,del);b.addEventListener('click',()=>choose(c.id));root.append(b)}}function md(text){
    if (!window.marked || !window.DOMPurify) return null;

    // Normalize escaped line breaks returned by the backend.
    const normalized = String(text || '').replace(/\\r\\n|\\n|\\r/g, '\n');

    // Convert evidence references to safe internal links.
    const withLinks = normalized.replace(
        /\[(E\d+)\]/g,
        (_, id) => `[${id}](#evidence-${id})`
    );

    return DOMPurify.sanitize(marked.parse(withLinks));
}function welcome(){const w=el('div','welcome');const icon=el('div','welcome-icon');const img=el('img');img.src='/static/syntax-symbol.jpeg';img.alt='Syntax';icon.append(img);w.append(icon,el('h2','', 'What would you like to research?'),el('p','', 'Ask questions about drug safety, interactions and prescribing information. Every answer is grounded in the local pharmaceutical evidence corpus.'));const grid=el('div','suggestions');const examples=[['Contraindications','What are the main contraindications for warfarin?'],['Drug comparison','Compare the contraindications of warfarin and apixaban.'],['Drug interactions','What is the bleeding risk when combining warfarin and sertraline?'],['Renal safety','Is metformin contraindicated at an eGFR of 25?']];for(const [title,question] of examples){const b=el('button','suggestion');b.append(el('strong','',title),document.createTextNode(question));b.addEventListener('click',()=>{q.value=question;send()});grid.append(b)}w.append(grid);$('messages').append(w)}function message(m){const a=el('article','message '+m.role),avatar=el('div','avatar',m.role==='user'?'●':'✦'),body=el('div','message-body'),name=el('div','message-name',m.role==='user'?'You':'PharmaGraph AI'),content=el('div','message-content');if(m.role==='assistant'){const html=md(m.text);if(html===null)content.textContent=m.text;else content.innerHTML=html}else content.textContent=m.text;body.append(name,content);if(m.role==='assistant'&&m.trace){const meta=el('div','message-meta','✓ Evidence-backed research · View agent details in Evidence Center');body.append(meta)}a.append(avatar,body);$('messages').append(a)}function traceField(t,...names){for(const n of names)if(t&&t[n]!==undefined)return t[n];return undefined}
let activeEvidenceTab = 'sources';

function selectEvidenceTab(tab) {
    activeEvidenceTab = tab;

    document.querySelectorAll('.metric-card').forEach(button => {
        const selected = button.dataset.panel === tab;
        button.classList.toggle('active', selected);
        button.setAttribute('aria-selected', String(selected));
    });

    const panel = $('detail-panel');
    const selectedButton = $('tab-' + tab);
    if (selectedButton) {
        panel.setAttribute('aria-labelledby', selectedButton.id);
    }

    renderEvidenceDetails();
}

function latestResearch() {
    const c = current();
    return [...(c?.messages || [])]
        .reverse()
        .find(m => m.role === 'assistant' && m.trace);
}

function renderEvidenceDetails() {
    const m = latestResearch();
    const t = m?.trace || {};
    const sources = m?.sources || [];
    const tools = traceField(t, 'tools_executed', 'toolsExecuted') || [];
    const retries = traceField(t, 'retries', 'retry_count') ?? 0;
    const approved = traceField(t, 'critic_approved', 'approved');
    const feedback = traceField(t, 'critic_feedback', 'feedback');

    const root = $('detail-panel');
    root.replaceChildren();

    const titles = {
        sources: 'CITED EVIDENCE',
        tools: 'EXECUTED TOOLS',
        retries: 'ADAPTIVE CRITIC'
    };

    $('detail-title').textContent = titles[activeEvidenceTab];

    if (activeEvidenceTab === 'sources') {
        $('evidence-label').textContent = sources.length + ' excerpts';

        const evidence = el('div', 'evidence');
        evidence.id = 'evidence';

        if (!sources.length) {
            evidence.append(
                el('p', 'muted', 'No evidence available for this answer.')
            );
        }

        for (const s of sources) {
            const card = el('div', 'source-card');
            card.id = 'evidence-' + String(s.id || '');

            card.append(
                el('strong', '', `[${s.id ?? '?'}] ${s.source || 'Unknown source'}`),
                el('small', '', s.section || '')
            );

            const details = el('details');
            const summary = el('summary', '', 'View supporting excerpt');
            const quote = el('blockquote', '', s.excerpt || '');

            details.append(summary, quote);
            card.append(details);
            evidence.append(card);
        }

        root.append(evidence);
    }

    if (activeEvidenceTab === 'tools') {
        $('evidence-label').textContent = tools.length + ' tools';

        if (!tools.length) {
            root.append(el('p', 'muted', 'No tools executed yet.'));
            return;
        }

        const descriptions = {
            contraindication_lookup:
                'Identifies formal contraindications from prescribing information.',
            renal_safety_check:
                'Checks renal impairment restrictions and eGFR thresholds.',
            interaction_analysis:
                'Investigates medication interactions and associated risks.',
            evidence_comparison:
                'Compares evidence across pharmaceutical documents.'
        };

        for (const tool of tools) {
            const card = el('div', 'tool-card');

            card.append(
                el('strong', '', '✓ ' + tool),
                el('p', 'muted',
                    descriptions[tool] || 'Specialized research tool.')
            );

            root.append(card);
        }
    }

    if (activeEvidenceTab === 'retries') {
        $('evidence-label').textContent = retries + ' retries';

        const card = el('div', 'review-detail-card');

        card.append(
            el('strong', '', 'Review status'),
            el(
                'p',
                approved === true ? 'review-success' : 'review-warning',
                !m
                    ? 'Awaiting research'
                    : approved === true
                        ? '✓ Approved'
                        : 'Review not approved'
            ),
            el('strong', '', 'Revision attempts'),
            el('p', 'muted', String(retries)),
            el('strong', '', 'Critic feedback'),
            el('p', 'muted',
                feedback || 'No review feedback available.')
        );

        root.append(card);
    }
}

function evidencePanel() {
    const m = latestResearch();
    const t = m?.trace || {};
    const sources = m?.sources || [];
    const tools = traceField(t, 'tools_executed', 'toolsExecuted') || [];
    const retries = traceField(t, 'retries', 'retry_count') ?? 0;
    const approved = traceField(t, 'critic_approved', 'approved');
    const feedback = traceField(t, 'critic_feedback', 'feedback');

    $('source-count').textContent = m ? sources.length : '—';
    $('tool-count').textContent = m ? tools.length : '—';
    $('review-count').textContent = m ? retries : '—';

    const badge = $('critic-status');

    badge.className = 'badge ' +
        (!m ? 'neutral' : approved === true ? 'good' : 'bad');

    badge.textContent = !m
        ? 'Awaiting research'
        : approved === true
            ? '✓ Approved'
            : 'Review not approved';

    $('critic-feedback').textContent =
        feedback || 'Run a research question to see the agent’s review.';

    renderEvidenceDetails();
}

document.querySelectorAll('.metric-card').forEach(button => {
    button.addEventListener('click', () => {
        selectEvidenceTab(button.dataset.panel);
    });
});
function render(){renderHistory();const c=current();$('conversation-title').textContent=c&&c.messages.length?c.title:'Research Assistant';$('messages').replaceChildren();if(!c||!c.messages.length)welcome();else c.messages.forEach(message);evidencePanel();$('chat-scroll').scrollTop=$('chat-scroll').scrollHeight}async function send(){if(busy)return;const question=q.value.trim();if(!question)return;if(!current())create();const c=current(),id=c.id;c.messages.push({role:'user',text:question});if(c.title==='New research session')c.title=question.slice(0,54);q.value='';busy=true;$('send').disabled=true;save();render();const loader=el('div','loading','✦ PharmaGraph AI is planning, retrieving evidence and reviewing the answer…');$('messages').append(loader);$('chat-scroll').scrollTop=$('chat-scroll').scrollHeight;try{const response=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Request failed');const target=chats.find(c=>c.id===id);target?.messages.push({role:'assistant',text:data.answer||'No answer was returned.',sources:data.sources||[],trace:data.agent_trace||data.trace||null})}catch(e){const target=chats.find(c=>c.id===id);target?.messages.push({role:'assistant',text:'The research request could not be completed: '+e.message,sources:[],trace:null})}finally{busy=false;$('send').disabled=false;save();render();q.focus()}}$('composer').addEventListener('submit',e=>{e.preventDefault();send()});q.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});q.addEventListener('input',()=>{q.style.height='27px';q.style.height=Math.min(q.scrollHeight,130)+'px'});$('new-chat').addEventListener('click',create);$('toggle-right').addEventListener('click',()=>{$('insights').classList.toggle('visible')});if(!active)create();else render();


// Evidence citation navigation
document.addEventListener('click', function(event) {
    const link = event.target.closest('a[href^="#evidence-"]');
    if (!link) return;

    event.preventDefault();

    const id = link.getAttribute('href').slice(1);
    selectEvidenceTab('sources');

    const target = document.getElementById(id);

    if (!target) return;

    const panel = document.getElementById('insights');
    if (panel) panel.classList.add('visible');

    target.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });

    target.classList.add('evidence-highlight');

    setTimeout(() => {
        target.classList.remove('evidence-highlight');
    }, 2500);
});
