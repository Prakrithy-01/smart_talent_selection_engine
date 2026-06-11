from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
import json

from parser_engine import ResumeParser
from semantic_mapper import SemanticMapper, NormalizedProfile
from ranking_dashboard import RankingEngine

app = FastAPI(title="Smart Talent Selection Engine")

# Runtime memory datastore representing database tables
CANDIDATE_POOL: List[NormalizedProfile] = []

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Renders the comprehensive landing and review interface overview."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Talent Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f6f9; color: #333; }
            h2, h3 { color: #2c3e50; }
            .container { max-width: 1100px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .section { margin-bottom: 35px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
            textarea { width: 100%; height: 120px; padding: 10px; border-radius: 4px; border: 1px solid #ccc; font-size: 14px; }
            input[type="file"] { margin: 15px 0; }
            button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 15px; }
            button:hover { background: #2980b9; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f8f9fa; }
            .badge { background: #2ecc71; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .justification { font-style: italic; color: #555; font-size: 13.5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🧠 "Smart Talent" Selection Engine</h2>
            <p>System context: Evaluates context semantic meanings instead of basic character matching patterns.</p>
            
            <div class="section">
                <h3>1. Ingestion View (Bulk Upload Resumes)</h3>
                <form action="/upload-resumes" method="post" enctype="multipart/form-data">
                    <input type="file" name="files" multiple required />
                    <br/>
                    <button type="submit">Upload and Parse Batch</button>
                </form>
            </div>

            <div class="section">
                <h3>2. Ranking Dashboard Evaluation</h3>
                <form id="rankingForm">
                    <label><strong>Job Description Criteria:</strong></label>
                    <textarea id="jdInput" placeholder="Paste target requirements description here... e.g., Looking for a Senior Backend Specialist with 5+ years experience inside JVM environments, core Java, and robust API frameworks."></textarea>
                    <br/><br/>
                    <button type="button" onclick="submitPipeline()">Calculate Matches & Rank Pool</button>
                </form>
            </div>

            <div class="section">
                <h3>3. Processed Candidate Results Table</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Rank Score</th>
                            <th>Candidate Name</th>
                            <th>Experience Depth</th>
                            <th>Mapped Top Skills</th>
                            <th>AI Summary of Fit</th>
                        </tr>
                    </thead>
                    <tbody id="resultsGrid">
                        <tr><td colspan="5" style="text-align:center; color:#999;">No pipeline scoring calculated yet. Provide JD requirements above.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            async function submitPipeline() {
                const jdText = document.getElementById('jdInput').value;
                if(!jdText) { alert('Please enter job description requirements first.'); return; }
                
                const response = await fetch('/rank', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ 'job_description': jdText })
                });
                
                const data = await response.json();
                const grid = document.getElementById('resultsGrid');
                grid.innerHTML = '';
                
                if(data.length === 0) {
                    grid.innerHTML = '<tr><td colspan="5" style="text-align:center;">No parsed candidate profiles loaded inside baseline memory pool.</td></tr>';
                    return;
                }

                data.forEach(item => {
                    grid.innerHTML += `
                        <tr>
                            <td><span class="badge">${item.compatibility_score}%</span></td>
                            <td><strong>${item.candidate_name}</strong></td>
                            <td>${item.years_of_experience} Yrs</td>
                            <td>${item.top_skills.join(', ') || 'General Base'}</td>
                            <td class="justification">"${item.ai_justification}"</td>
                        </tr>
                    `;
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload-resumes")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Accepts multiple documents, extracts context text, and maps entities into application cache pools."""
    uploaded_count = 0
    for file in files:
        try:
            body_bytes = await file.read()
            # 1. Ingestion and Multi-Format parsing
            raw_text = ResumeParser.parse(file.filename, body_bytes)
            # 2. Semantic entity mapping normalization
            normalized_profile = SemanticMapper.normalize_profile(raw_text, file.filename)
            
            CANDIDATE_POOL.append(normalized_profile)
            uploaded_count += 1
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing file '{file.filename}': {str(e)}")
            
    # Redirect back immediately to dashboard index view
    return HTMLResponse(content=f"""
        <script>
            alert('Successfully uploaded and normalized {uploaded_count} resume documents!');
            window.location.href = "/";
        </script>
    """)

@app.post("/rank")
async def rank_candidates(job_description: str = Form(...)):
    """Evaluates pool against objective text metrics and outputs weighted rankings."""
    results = RankingEngine.rank_candidates(job_description, CANDIDATE_POOL)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)