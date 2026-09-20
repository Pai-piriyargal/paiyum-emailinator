import json
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Dashboard")

SUBMISSION_PATH = Path("submission.json")
def load_submission():
    if SUBMISSION_PATH.exists():
        return json.loads(SUBMISSION_PATH.read_text(encoding="utf-8"))
    return {}

def save_submission(data):
    SUBMISSION_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    submission = load_submission()

    total = len(submission)
    needs_review = sum(1 for v in submission.values() if v.get("status") == "NEEDS_REVIEW")
    mismatches = sum(1 for v in submission.values() if v.get("status") == "MISMATCH")
    ok_count = sum(1 for v in submission.values() if v.get("status") == "OK")

    rows_html = ""
    for eid, item in submission.items():
        status = item.get("status")
        badge_cls = "bg-green-100 text-green-800" if status == "OK" else ("bg-amber-100 text-amber-800" if status == "MISMATCH" else "bg-red-100 text-red-800")
        reason = item.get("review_reason") or "-"
        defects = ", ".join(item.get("defect_fields", [])) or "-"

        rows_html += f"""
        <tr class="hover:bg-slate-50 border-b">
            <td class="p-3 font-mono text-sm">{eid}</td>
            <td class="p-3 text-sm">{item.get("category")}</td>
            <td class="p-3"><span class="px-2 py-1 text-xs font-semibold rounded {badge_cls}">{status}</span></td>
            <td class="p-3 text-sm text-slate-600">{reason}</td>
            <td class="p-3 text-sm text-red-600 font-medium">{defects}</td>
            <td class="p-3 text-sm">
                <a href="/review/{eid}" class="text-blue-600 hover:underline">Review & Edit</a>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen p-8">
        <div class="max-w-7xl mx-auto space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                    <h1 class="text-3xl font-bold text-white">Averis Shipping Document Verification</h1>
                    <p class="text-slate-400">Human-in-the-Loop Review Dashboard & Audit Log</p>
                </div>
                <div class="flex gap-4">
                    <div class="bg-slate-800 px-4 py-2 rounded-lg border border-slate-700">
                        <span class="text-xs text-slate-400 block">Total Checked</span>
                        <span class="text-2xl font-bold text-white">{total}</span>
                    </div>
                    <div class="bg-slate-800 px-4 py-2 rounded-lg border border-amber-900/50">
                        <span class="text-xs text-amber-400 block">Needs Review</span>
                        <span class="text-2xl font-bold text-amber-400">{needs_review}</span>
                    </div>
                    <div class="bg-slate-800 px-4 py-2 rounded-lg border border-red-900/50">
                        <span class="text-xs text-red-400 block">Mismatched</span>
                        <span class="text-2xl font-bold text-red-400">{mismatches}</span>
                    </div>
                    <div class="bg-slate-800 px-4 py-2 rounded-lg border border-emerald-900/50">
                        <span class="text-xs text-emerald-400 block">Matched</span>
                        <span class="text-2xl font-bold text-emerald-400">{ok_count}</span>
                    </div>
                </div>
            </div>

            <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-xl">
                <table class="w-full text-left">
                    <thead class="bg-slate-900/50 text-slate-400 text-xs uppercase border-b border-slate-700">
                        <tr>
                            <th class="p-3">Email ID</th>
                            <th class="p-3">Category</th>
                            <th class="p-3">Status</th>
                            <th class="p-3">Review Reason</th>
                            <th class="p-3">Defect Fields</th>
                            <th class="p-3">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-700/50 text-slate-200">
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
