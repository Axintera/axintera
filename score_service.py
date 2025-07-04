from fastapi import FastAPI, HTTPException
import reputation, sqlite3, os

app = FastAPI(title="Axintera Score API")

@app.on_event("startup")
async def boot():
    reputation.init_db()

@app.get("/score/{provider_id}")
def get_score(provider_id: str):
    with sqlite3.connect(reputation.DB_PATH) as c:
        row = c.execute(
            "SELECT served, success, score FROM providerstat WHERE provider_id=?",
            (provider_id.lower(),),
        ).fetchone()
    if not row:
        raise HTTPException(404, "provider not found")
    served, success, score = row
    return {"provider_id": provider_id, "served": served, "success": success, "score": score}
