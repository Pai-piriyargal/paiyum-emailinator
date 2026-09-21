import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Paiyum Emailinator Command Center")

SUBMISSION_PATH = Path("submission.json")

def load_submission():
    target = SUBMISSION_PATH
    if not target.exists() and Path("shipping-verification/output.json").exists():
        target = Path("shipping-verification/output.json")
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if data:
                return data
        except json.JSONDecodeError:
            return {}
    return {}


def save_submission(data):
    SUBMISSION_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    output_alt = Path("shipping-verification/output.json")
    if output_alt.parent.exists():
        output_alt.write_text(json.dumps(data, indent=2), encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    submission = load_submission()

    total = len(submission)
    needs_review = sum(1 for v in submission.values() if v.get("status") == "NEEDS_REVIEW")
    mismatches = sum(1 for v in submission.values() if v.get("status") == "MISMATCH")
    ok_count = sum(1 for v in submission.values() if v.get("status") == "OK")
    
    confidence = int((ok_count / total * 100)) if total > 0 else 0

    rows_html = ""
    if not submission:
        rows_html = """
        <tr>
            <td colspan="6" class="p-12 text-center text-slate-500 italic">
                No submission data found. Run main.py to process the dataset.
            </td>
        </tr>
        """
    else:
        for eid, item in submission.items():
            status = item.get("status", "UNKNOWN")
            urgency = item.get("urgency_score", "LOW")
            category = item.get("category", "GENERAL")
            
            status_styles = {
                "OK": ("bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.15)]", "bg-emerald-500"),
                "MISMATCH": ("bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.15)]", "bg-rose-500"),
                "NEEDS_REVIEW": ("bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.15)]", "bg-amber-500")
            }
            
            urgency_styles = {
                "HIGH": "bg-gradient-to-r from-rose-600 to-rose-400 text-white shadow-[0_0_20px_rgba(244,63,94,0.4)] border-none",
                "MEDIUM": "bg-gradient-to-r from-amber-500 to-amber-400 text-slate-900 font-bold border-none",
                "LOW": "bg-slate-700/50 text-slate-300 border border-slate-600"
            }
            
            s_cls, dot_cls = status_styles.get(status, ("bg-slate-800 text-slate-400 border-slate-700", "bg-slate-500"))
            u_cls = urgency_styles.get(urgency, "bg-slate-700 text-slate-300")
            
            explanation = item.get("review_explanation") or "Neural extraction pending. Awaiting processing cycle."
            defects = item.get("defect_fields", [])
            defects_html = "".join([f'<span class="inline-block px-2 py-0.5 mt-1 mr-1 text-[9px] uppercase tracking-wider bg-rose-900/40 text-rose-300 border border-rose-800/50 rounded">{d.replace("_", " ")}</span>' for d in defects]) if defects else '<span class="text-xs text-slate-500 italic">No defects</span>'

            rows_html += f"""
            <tr class="border-b border-slate-800/50 hover:bg-slate-800/80 transition-all duration-300 table-row group cursor-pointer hover-3d relative overflow-hidden" data-status="{status}" data-urgency="{urgency}" onclick="openModal('{eid}')">
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/5 to-transparent -translate-x-full group-hover:animate-sweep pointer-events-none"></div>
                <td class="p-5 font-mono text-xs text-slate-400 group-hover:text-cyan-400 transition-colors relative z-10">
                    <div class="flex items-center gap-3">
                        <div class="w-1.5 h-1.5 rounded-full {dot_cls} animate-pulse"></div>
                        {eid}
                    </div>
                </td>
                <td class="p-5 text-sm font-medium text-slate-300 tracking-wide relative z-10">{category}</td>
                <td class="p-5 relative z-10">
                    <span class="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-md border backdrop-blur-md {s_cls}">
                        {status}
                    </span>
                </td>
                <td class="p-5 relative z-10">
                    <span class="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-md {u_cls}">
                        {urgency}
                    </span>
                </td>
                <td class="p-5 relative z-10">
                    <div class="text-sm text-slate-300 font-medium truncate max-w-xs">{explanation}</div>
                    <div class="mt-1 flex flex-wrap">{defects_html}</div>
                </td>
                <td class="p-5 text-right relative z-10">
                    <button class="w-8 h-8 rounded-full bg-slate-700/50 flex items-center justify-center text-slate-400 group-hover:bg-cyan-500 group-hover:text-white transition-all duration-300 shadow-lg group-hover:shadow-cyan-500/40">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </button>
                </td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Paiyum Emailinator Core</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #030712; color: #e2e8f0; perspective: 1000px; }}
            .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
            .glass-panel {{ background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }}
            .bg-3d-grid {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background-image: 
                    linear-gradient(rgba(6, 182, 212, 0.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(6, 182, 212, 0.05) 1px, transparent 1px);
                background-size: 40px 40px;
                transform: perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px);
                animation: grid-move 10s linear infinite;
                z-index: -2;
            }}
            #particles-js {{ position: fixed; width: 100%; height: 100%; z-index: -1; pointer-events: none; opacity: 0.4; }}
            @keyframes grid-move {{ 0% {{ background-position: 0 0; }} 100% {{ background-position: 0 40px; }} }}
            @keyframes sweep {{ 0% {{ transform: translateX(-100%); }} 100% {{ transform: translateX(200%); }} }}
            .animate-sweep {{ animation: sweep 1.5s ease-in-out infinite; }}
            .card-3d {{ transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease; transform-style: preserve-3d; }}
            .card-3d:hover {{ transform: translateY(-10px) rotateX(5deg) rotateY(-5deg) scale(1.02); box-shadow: 20px 20px 30px rgba(0,0,0,0.5), 0 0 20px rgba(6,182,212,0.2); }}
            .hover-3d {{ transition: transform 0.2s ease, background-color 0.2s ease; transform-style: preserve-3d; }}
            .hover-3d:hover {{ transform: scale(1.01) translateZ(10px); }}
            #modal-content-box {{ transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }}
            .modal-hidden {{ opacity: 0; transform: scale(0.8) rotateX(-20deg) translateY(50px); }}
            .modal-visible {{ opacity: 1; transform: scale(1) rotateX(0deg) translateY(0); }}
            ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
            ::-webkit-scrollbar-track {{ background: transparent; }}
            ::-webkit-scrollbar-thumb {{ background: #1e293b; border-radius: 10px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: #334155; }}
            @keyframes slideIn {{ to {{ opacity: 1; transform: translateX(0); }} }}
        </style>
        <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    </head>
    <body class="flex h-screen overflow-hidden antialiased selection:bg-cyan-500/30">
        <div class="bg-3d-grid"></div>
        <div id="particles-js"></div>
        <div class="fixed inset-0 bg-gradient-to-t from-[#030712] via-transparent to-transparent pointer-events-none z-[-1]"></div>

        <aside class="w-20 lg:w-64 border-r border-slate-800/50 bg-[#030712]/80 backdrop-blur-xl flex flex-col justify-between transition-all duration-300 z-10 shadow-[5px_0_15px_rgba(0,0,0,0.5)]">
            <div>
                <div class="h-20 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-800/50">
                    <div class="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 shadow-[0_0_20px_rgba(99,102,241,0.5)] transform hover:rotate-12 transition-transform">
                        <svg class="w-6 h-6 text-white drop-shadow-md" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    </div>
                    <div class="hidden lg:block ml-3">
                        <div class="font-bold text-sm text-white tracking-wide">PAIYUM<span class="text-cyan-400">.AI</span></div>
                        <div class="text-[9px] text-slate-500 uppercase tracking-widest font-bold">Team Pai-piriyargal</div>
                    </div>
                </div>
                <nav class="mt-8 px-4 space-y-2">
                    <a href="#" class="flex items-center px-2 lg:px-4 py-3 bg-gradient-to-r from-cyan-900/40 to-indigo-900/40 text-cyan-400 border border-cyan-500/30 rounded-xl group relative overflow-hidden shadow-[0_0_15px_rgba(6,182,212,0.15)]">
                        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                        <span class="hidden lg:block ml-3 text-sm font-medium">Reconciliation</span>
                    </a>
                </nav>
            </div>
        </aside>

        <main class="flex-1 flex flex-col relative bg-transparent z-10">
            <header class="h-28 lg:h-32 px-8 flex items-center justify-between border-b border-slate-800/50 bg-[#030712]/60 backdrop-blur-md shadow-lg">
                <div class="card-3d p-2">
                    <h1 class="text-2xl lg:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 mb-1 drop-shadow-lg">Emailinator Core</h1>
                    <p class="text-sm text-cyan-500 font-medium tracking-wide flex items-center gap-2">
                        <span class="w-2 h-2 bg-cyan-500 rounded-full animate-pulse shadow-[0_0_8px_#06b6d4]"></span> Automated Extractor Engine Active
                    </p>
                </div>
                <div class="flex gap-4 lg:gap-8">
                    <div class="card-3d glass-panel px-4 lg:px-6 py-2 lg:py-3 rounded-2xl border-t border-l border-slate-700/50 flex flex-col items-center justify-center">
                        <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">Match Rate</span>
                        <div class="text-xl lg:text-3xl font-bold text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]">{confidence}%</div>
                    </div>
                    <div class="flex gap-4">
                        <div class="card-3d glass-panel px-4 lg:px-6 py-2 lg:py-3 rounded-2xl border-t border-l border-rose-900/30 flex flex-col items-end">
                            <span class="text-[10px] text-rose-500 font-bold uppercase tracking-wider mb-1">Exceptions</span>
                            <span class="text-xl lg:text-3xl font-bold text-rose-400 drop-shadow-[0_0_10px_rgba(244,63,94,0.5)]">{mismatches}</span>
                        </div>
                        <div class="card-3d glass-panel px-4 lg:px-6 py-2 lg:py-3 rounded-2xl border-t border-l border-amber-900/30 flex flex-col items-end">
                            <span class="text-[10px] text-amber-500 font-bold uppercase tracking-wider mb-1">Queue</span>
                            <span class="text-xl lg:text-3xl font-bold text-amber-400 drop-shadow-[0_0_10px_rgba(251,191,36,0.5)]">{needs_review}</span>
                        </div>
                    </div>
                </div>
            </header>

            <div class="px-8 py-5 flex items-center justify-between">
                <div class="flex gap-2 p-1 bg-slate-900/80 rounded-xl border border-slate-800 shadow-inner">
                    <button onclick="filterTable('all', this)" class="filter-btn active px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-700 text-white shadow-[0_2px_10px_rgba(0,0,0,0.3)] transition-all">Global Feed</button>
                    <button onclick="filterTable('review', this)" class="filter-btn px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider text-slate-500 hover:text-slate-300 transition-all">Pending Review</button>
                    <button onclick="filterTable('high', this)" class="filter-btn px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider text-slate-500 hover:text-rose-400 transition-all flex items-center gap-2">Critical Priority</button>
                </div>
            </div>

            <div class="flex-1 overflow-auto px-8 pb-8">
                <div class="glass-panel rounded-2xl overflow-hidden shadow-[0_15px_30px_rgba(0,0,0,0.6)] border border-slate-700/50 backdrop-blur-2xl">
                    <table class="w-full text-left border-collapse">
                        <thead class="bg-slate-900/80 border-b border-slate-700/80 sticky top-0 z-20">
                            <tr>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest w-48">Trace ID</th>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Document Type</th>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest w-32">Integrity</th>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest w-32">Priority</th>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Diagnostics</th>
                                <th class="p-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right w-24">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800/40" id="table-body">
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <div id="review-modal" class="fixed inset-0 z-50 hidden">
            <div class="absolute inset-0 bg-[#030712]/90 backdrop-blur-md" onclick="closeModal()"></div>
            <div class="absolute inset-0 flex items-center justify-center p-4 pointer-events-none perspective-1000">
                <div class="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-700/50 w-full max-w-6xl rounded-2xl shadow-[0_30px_60px_rgba(0,0,0,0.8),0_0_30px_rgba(6,182,212,0.15)] pointer-events-auto flex flex-col max-h-[90vh] modal-hidden" id="modal-content-box">
                    <div class="flex items-center justify-between p-6 lg:p-8 border-b border-slate-800 shrink-0 bg-slate-900/50 rounded-t-2xl">
                        <div class="card-3d">
                            <div class="flex items-center gap-3 mb-2">
                                <div class="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_15px_#22d3ee] animate-pulse"></div>
                                <h2 class="text-2xl font-bold text-white tracking-wide drop-shadow-md">Holographic Data Audit</h2>
                                <span id="modal-eid" class="ml-2 px-2.5 py-1 bg-slate-800 border border-slate-600 rounded text-xs font-mono text-cyan-300 shadow-inner"></span>
                            </div>
                            <p id="modal-explanation" class="text-sm font-medium text-amber-400"></p>
                        </div>
                        <button onclick="closeModal()" class="text-slate-500 hover:text-white hover:bg-rose-500/20 hover:border-rose-500/50 border border-transparent transition-all p-2 rounded-xl">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                        </button>
                    </div>
                    <div class="flex-1 overflow-auto p-6 lg:p-8 relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-[#0a0f18] to-[#0a0f18]">
                        <div class="absolute left-1/2 top-8 bottom-8 w-px bg-gradient-to-b from-transparent via-cyan-900/50 to-transparent hidden md:block"></div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-16">
                            <div class="space-y-6">
                                <div class="flex items-center justify-between pb-3 border-b border-emerald-900/30">
                                    <h3 class="text-sm font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-2 drop-shadow-[0_0_5px_rgba(52,211,153,0.5)]">Source Document (SI)</h3>
                                    <span class="text-[9px] font-mono text-slate-400 border border-slate-700 px-2 py-0.5 rounded shadow-inner">LOCKED</span>
                                </div>
                                <div id="si-fields" class="space-y-4 perspective-1000"></div>
                            </div>
                            <div class="space-y-6">
                                <div class="flex items-center justify-between pb-3 border-b border-cyan-900/30">
                                    <h3 class="text-sm font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]">Extracted Draft (BL)</h3>
                                    <span class="text-[9px] font-mono text-cyan-900 border border-cyan-800 px-2 py-0.5 rounded bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.4)] font-bold">EDITABLE</span>
                                </div>
                                <div id="bl-fields" class="space-y-4"></div>
                            </div>
                        </div>
                    </div>
                    <div class="p-6 lg:px-8 bg-slate-950 border-t border-slate-800 rounded-b-2xl shrink-0 flex justify-between items-center shadow-[inset_0_10px_20px_rgba(0,0,0,0.5)]">
                        <div class="text-xs font-mono text-slate-500 flex items-center gap-2">
                            <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full inline-block shadow-[0_0_5px_#10b981] animate-pulse"></span> Network Synchronized
                        </div>
                        <div class="flex gap-4">
                            <button onclick="closeModal()" class="px-6 py-2.5 rounded-xl font-bold text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors border border-slate-700">Abort</button>
                            <button onclick="submitCorrections()" class="px-6 py-2.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(34,211,238,0.6)] transform hover:-translate-y-1 transition-all flex items-center gap-2 border border-cyan-400/30">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                Write Overrides
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            particlesJS("particles-js", {{
                "particles": {{"number":{{"value":40,"density":{{"enable":true,"value_area":800}}}},"color":{{"value":"#06b6d4"}},"shape":{{"type":"circle"}},"opacity":{{"value":0.3,"random":true}},"size":{{"value":3,"random":true}},"line_linked":{{"enable":true,"distance":150,"color":"#06b6d4","opacity":0.2,"width":1}},"move":{{"enable":true,"speed":1,"direction":"top","random":true,"straight":false,"out_mode":"out","bounce":false}}}},
                "interactivity":{{"detect_on":"canvas","events":{{"onhover":{{"enable":true,"mode":"grab"}},"onclick":{{"enable":false}},"resize":true}},"modes":{{"grab":{{"distance":140,"line_linked":{{"opacity":0.5}}}}}}}}
            }});

            let currentEid = null;

            function filterTable(filterType, btnElement) {{
                document.querySelectorAll('.filter-btn').forEach(btn => {{
                    btn.classList.remove('active', 'bg-slate-700', 'text-white');
                    btn.classList.add('text-slate-500');
                }});
                btnElement.classList.remove('text-slate-500');
                btnElement.classList.add('active', 'bg-slate-700', 'text-white');

                const rows = document.querySelectorAll('.table-row');
                rows.forEach(row => {{
                    row.style.display = ''; 
                    if (filterType === 'high' && row.getAttribute('data-urgency') !== 'HIGH') {{
                        row.style.display = 'none';
                    }}
                    if (filterType === 'review' && row.getAttribute('data-status') !== 'NEEDS_REVIEW' && row.getAttribute('data-status') !== 'MISMATCH') {{
                        row.style.display = 'none';
                    }}
                }});
            }}

            async function openModal(eid) {{
                currentEid = eid;
                try {{
                    const response = await fetch(`/review/${{eid}}`);
                    const data = await response.json();
                    
                    document.getElementById('modal-eid').innerText = eid;
                    document.getElementById('modal-explanation').innerText = data.review_explanation || "Verify neural extraction targets.";
                    
                    const fieldsToCheck = ["shipper", "consignee", "notify_party", "port_of_loading", "port_of_discharge", "container_count", "gross_weight_kg"];
                    
                    let siHtml = "";
                    let blHtml = "";
                    const defects = data.defect_fields || [];
                    
                    fieldsToCheck.forEach((field, index) => {{
                        const isDefect = defects.includes(field);
                        const siVal = data.si_data ? (data.si_data[field] || "N/A") : "Data pending";
                        const blVal = data.bl_data ? (data.bl_data[field] || "") : "";
                        const label = field.replace(/_/g, ' ').toUpperCase();
                        
                        const delay = index * 50;
                        
                        siHtml += `
                        <div class="relative p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 shadow-inner" style="animation: slideIn 0.3s ease forwards ${{delay}}ms; opacity: 0; transform: translateX(-20px);">
                            <label class="block text-[10px] font-bold text-emerald-500/70 mb-2 tracking-widest">${{label}}</label>
                            <div class="font-mono text-sm text-slate-300 leading-relaxed">${{siVal}}</div>
                        </div>`;
                        
                        const inputBorder = isDefect ? "border-rose-500 focus:border-rose-400 bg-rose-950/30 shadow-[0_0_15px_rgba(244,63,94,0.2)]" : "border-slate-600 focus:border-cyan-400 bg-slate-800/60 focus:shadow-[0_0_15px_rgba(34,211,238,0.2)]";
                        const textStyle = isDefect ? "text-rose-200" : "text-white";
                        const labelClass = isDefect ? "text-rose-400 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]" : "text-cyan-500/70";
                        
                        blHtml += `
                        <div class="relative card-3d" style="animation: slideIn 0.3s ease forwards ${{delay}}ms; opacity: 0; transform: translateX(20px);">
                            <label class="block text-[10px] font-bold ${{labelClass}} mb-2 tracking-widest">${{label}}</label>
                            <textarea id="input-${{field}}" rows="2" 
                                class="w-full ${{inputBorder}} ${{textStyle}} px-4 py-3 rounded-xl font-mono text-sm outline-none transition-all resize-none shadow-inner" 
                                placeholder="Enter corrected value...">${{blVal}}</textarea>
                        </div>`;
                    }});
                    
                    document.getElementById('si-fields').innerHTML = siHtml;
                    document.getElementById('bl-fields').innerHTML = blHtml;

                    const modal = document.getElementById('review-modal');
                    const modalBox = document.getElementById('modal-content-box');
                    modal.classList.remove('hidden');
                    void modal.offsetWidth; 
                    modalBox.classList.remove('modal-hidden');
                    modalBox.classList.add('modal-visible');

                }} catch (error) {{
                    alert("System Error: Failed to retrieve data vectors.");
                }}
            }}

            function closeModal() {{
                const modal = document.getElementById('review-modal');
                const modalBox = document.getElementById('modal-content-box');
                modalBox.classList.remove('modal-visible');
                modalBox.classList.add('modal-hidden');
                setTimeout(() => {{ modal.classList.add('hidden'); }}, 400);
            }}

            async function submitCorrections() {{
                const fieldsToCheck = ["shipper", "consignee", "notify_party", "port_of_loading", "port_of_discharge", "container_count", "gross_weight_kg"];
                const correctedData = {{}};
                
                fieldsToCheck.forEach(field => {{
                    const input = document.getElementById(`input-${{field}}`);
                    if(input) correctedData[field] = input.value;
                }});

                try {{
                    const response = await fetch(`/review/${{currentEid}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(correctedData)
                    }});
                    
                    if(response.ok) {{
                        closeModal();
                        setTimeout(() => window.location.reload(), 400);
                    }}
                }} catch (error) {{
                    alert("Write Error: Failed to commit overrides to datastore.");
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/review/{eid}")
async def get_review_data(eid: str):
    submission = load_submission()
    if eid not in submission:
        raise HTTPException(status_status=404, detail="Trace ID not found in datastore")
    item = submission[eid]
    return JSONResponse(content={
        "review_explanation": item.get("review_explanation", "Manual discrepancy check required."),
        "defect_fields": item.get("defect_fields", []),
        "si_data": item.get("si_data", {}),
        "bl_data": item.get("bl_data", {})
    })

@app.post("/review/{eid}")
async def save_review(eid: str, request: Request):
    corrected_data = await request.json()
    submission = load_submission()
    if eid in submission:
        submission[eid]["status"] = "OK"
        submission[eid]["urgency_score"] = "LOW"
        submission[eid]["review_explanation"] = "Manually corrected and cleared by human auditor."
        submission[eid]["defect_fields"] = []
        if "bl_data" not in submission[eid]:
            submission[eid]["bl_data"] = {}
        for key, val in corrected_data.items():
            submission[eid]["bl_data"][key] = val
        save_submission(submission)
    return JSONResponse(content={"status": "success"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)