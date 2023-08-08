from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sqlite3

app = FastAPI()

# Define the static folder path
static_folder = Path(__file__).parent / "static"
templates = Jinja2Templates(directory="templates")


# Define the database path
db_file = Path(__file__).parent / "sloleks.db"


# Mount the static files to the root of the app
app.mount("/static", StaticFiles(directory=static_folder, html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index(req: Request):
    return templates.TemplateResponse("index.html", {"request": req})

@app.get("/search", response_class=HTMLResponse)
async def search_word_forms(request: Request, query: str):
    # Connect to the database
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Search for entries that match the user's entry for zapis_oblike
    cursor.execute("SELECT * FROM word_forms WHERE zapis_oblike LIKE ? LIMIT 1000", (query,))
    result = cursor.fetchall()

    # Close the database connection
    conn.close()

    return templates.TemplateResponse(
        "search_result.html",
        {"request": request, "query": query, "result": result},
    )

@app.get("/search_lemma", response_class=HTMLResponse)
async def search_lemma(request: Request, query: str):
    # Connect to the database
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Search for entries that match the user's entry for zapis_oblike
    cursor.execute("SELECT * FROM lexical_entries WHERE pronaunciation IS NOT NULL and lemma LIKE ? LIMIT 1000", (query,))
    result = cursor.fetchall()

    # Close the database connection
    conn.close()

    return templates.TemplateResponse(
        "search_result_lemma.html",
        {"request": request, "query": query, "result": result},
    )

@app.get("/lemma", response_class=HTMLResponse)
async def lemma(request: Request, query: str):
    # Connect to the database
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Search for entries that match the user's entry for zapis_oblike
    cursor.execute("SELECT id, type, lemma FROM lexical_entries WHERE id=?", (query,))
    result = cursor.fetchall()

    # Close the database connection
    conn.close()

    if len(result) == 0:
        return templates.TemplateResponse(
            "lemma_not_found.html",
            {"request": request, "query": query, "result": result},
        )

    result = result[0]

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Search for entries that match the user's entry for zapis_oblike
    cursor.execute("SELECT id, zapis_oblike, IPA_1, SAMPA_1, msd, spol, stevilo, sklon, oblika, oseba  FROM word_forms WHERE lexical_entry_id=?", (query,))
    forms = cursor.fetchall()

    # Close the database connection
    conn.close()

   

    


    template = "lemma_unknown.html"
    if result[1] == "verb":
        parsed_forms = {
            "infinitive": { 
                'none': {}
            },
            "present": {
                "singular": {},
                "dual": {},
                "plural": {},
            },
            "participle": {
                "singular": {},
                "dual": {},
                "plural": {},
            },
            "imperative": {
                "singular": {},
                "dual": {},
                "plural": {},
            },
            "supine": {
                "none": {}
            },
        }
        for form in forms:
            parsed_forms[form[8]][form[6] if form[6] is not None else "none"][form[9] if form[9] is not None else form[5]]= {
                "ipa": form[2],
                "sampa": form[3],
                "form": form[1],
                "msd": form[4],
            }
        
        print (parsed_forms)
        template = "lemma_verb.html"
    elif result[1] == "noun":
        parsed_forms = {
            "singular": {},
            "dual": {},
            "plural": {},
            None: {},
        }
        for form in forms:
            parsed_forms[form[6]][form[7]] = {
                "ipa": form[2],
                "sampa": form[3],
                "form": form[1],
                "msd": form[4],
            }
            
        template = "lemma_noun.html"
    elif result[1] == "adverb" or result[1] == "conjunction" or result[1] == "preposition" or result[1] == "particle":
        parsed_forms = {}

        for form in forms:
            parsed_forms = {
                "ipa": form[2],
                "sampa": form[3],
                "form": form[1],
                "msd": form[4],
            }

        template = "lemma_adverb.html"
    elif result[1] == "adjective" or result[1] == "pronoun":
        parsed_forms = {
            "masculine": {
                "singular": {},
                "dual": {},
                "plural": {},
                None: {},
            },
            "feminine": {
                "singular": {},
                "dual": {},
                "plural": {},
                None: {},
            },
            "neuter": {
                "singular": {},
                "dual": {},
                "plural": {},
                None: {},
            },
            None: {
                "singular": {},
                "dual": {},
                "plural": {},
                None: {},
            },
        }
        for form in forms:
            parsed_forms[form[5]][form[6]][form[7]] = {
                "ipa": form[2],
                "sampa": form[3],
                "form": form[1],
                "msd": form[4],
            }

        template = "lemma_adjective.html"
    elif result[1] == "numeral":
        template = "lemma_numeral.html"
    
    print (template)
    return templates.TemplateResponse(
        template,
        {"request": request, "query": query, "result": result, "forms": parsed_forms},
    )

@app.post("/update")
async def update_word_forms(ipa_data: dict):
    # Connect to the database
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    for row_id, ipa in ipa_data.items():
        # Update the database with the modified IPA data for each row ID
        # Assuming you have a unique identifier in your table, use it in the WHERE clause
        cursor.execute("UPDATE word_forms SET IPA_1=? WHERE id=?", (ipa, row_id))

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

    return {"status": "Database updated successfully"}

if __name__ == "__main__":
    import uvicorn

    # Start the server on port 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)