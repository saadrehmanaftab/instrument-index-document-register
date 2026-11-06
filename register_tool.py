"""Database driven instrument index, I/O list and document register for an assumed electrolysis plant.

PERSONAL PROJECT. THE PLANT, ITS INSTRUMENTS, VENDORS AND DOCUMENTS ARE ALL ASSUMED.
Run:  python register_tool.py      (needs pandas, openpyxl; sqlite3 ships with Python)
Outputs: plant.db (SQLite), engineering_lists.xlsx, results.json
"""
import json
import os
import sqlite3
import numpy as np
import pandas as pd

SEED = 2026
N_STACKS = 4
# assumed instrument set per stack: (type, service, signal, count, unit, range)
PER_STACK = [
    ("TT", "lye temperature", "AI", 3, "degC", "0 to 120"),
    ("PT", "gas pressure", "AI", 2, "bar", "0 to 40"),
    ("FT", "lye flow", "AI", 1, "m3/h", "0 to 60"),
    ("LT", "separator level", "AI", 1, "%", "0 to 100"),
    ("AT", "hydrogen in oxygen", "AI", 1, "%", "0 to 4"),
    ("TCV", "cooler valve", "AO", 1, "%", "0 to 100"),
    ("XV", "isolation valve", "DO", 3, "", "open or closed"),
    ("ZS", "valve end position", "DI", 6, "", "open or closed"),
    ("HS", "local emergency stop", "DI", 1, "", "on or off"),
]
SHARED = [  # assumed balance of plant instruments
    ("PT", "header pressure", "AI", 2, "bar", "0 to 40"),
    ("AT", "hydrogen purity", "AI", 2, "%", "95 to 100"),
    ("FT", "demineralized water flow", "AI", 1, "m3/h", "0 to 5"),
    ("XV", "vent valve", "DO", 2, "", "open or closed"),
    ("GD", "gas detector", "DI", 4, "", "alarm"),
]
VENDORS = {"TT": "Vendor A", "PT": "Vendor A", "FT": "Vendor B", "LT": "Vendor B", "AT": "Vendor C",
           "TCV": "Vendor D", "XV": "Vendor D", "ZS": "Vendor D", "HS": "Vendor E", "GD": "Vendor C"}
SPARE = 0.20                        # assumed spare share per I/O type
MISSING = {("AT", "datasheet"), ("GD", "manual")}   # assumed: documents not yet received from the manufacturer


def build_db(path, rng):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE instruments(tag TEXT PRIMARY KEY, type TEXT, area TEXT, service TEXT, signal TEXT,
                             unit TEXT, range TEXT, vendor TEXT);
    CREATE TABLE documents(doc_no TEXT PRIMARY KEY, vendor TEXT, inst_type TEXT, doc_type TEXT,
                           revision INTEGER, review_status TEXT);
    """)
    seq = {}
    rows = []
    areas = ["S%d" % (s + 1) for s in range(N_STACKS)]
    for area in areas:
        for typ, svc, sig, cnt, unit, rng_txt in PER_STACK:
            for _ in range(cnt):
                seq[typ] = seq.get(typ, 100) + 1
                rows.append((f"{area}.{typ}{seq[typ]}", typ, area, svc, sig, unit, rng_txt, VENDORS[typ]))
    for typ, svc, sig, cnt, unit, rng_txt in SHARED:
        for _ in range(cnt):
            seq[typ] = seq.get(typ, 100) + 1
            rows.append((f"BOP.{typ}{seq[typ]}", typ, "BOP", svc, sig, unit, rng_txt, VENDORS[typ]))
    cur.executemany("INSERT INTO instruments VALUES (?,?,?,?,?,?,?,?)", rows)
    # one datasheet and one manual per instrument type; the MISSING set is not yet received (assumed),
    # and the review status of the received ones is drawn at random (assumed)
    docs, n = [], 1
    for typ in sorted({r[1] for r in rows}):
        for dtype in ("datasheet", "manual"):
            if (typ, dtype) in MISSING:
                continue
            status = rng.choice(["approved", "approved", "approved", "in review", "returned with comments"])
            docs.append((f"DOC{n:04d}", VENDORS[typ], typ, dtype, int(rng.integers(0, 3)), str(status)))
            n += 1
    cur.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?)", docs)
    con.commit()
    return con


def main():
    rng = np.random.default_rng(SEED)
    con = build_db("plant.db", rng)
    inst = pd.read_sql("SELECT * FROM instruments ORDER BY area, tag", con)
    docs = pd.read_sql("SELECT * FROM documents ORDER BY doc_no", con)
    io = inst.groupby("signal").size().reindex(["AI", "AO", "DI", "DO"], fill_value=0)
    io_list = pd.DataFrame({"used": io, "spare": np.ceil(io * SPARE).astype(int)})
    io_list["installed"] = io_list["used"] + io_list["spare"]
    ds = docs[docs.doc_type == "datasheet"][["inst_type", "review_status"]]
    merged = inst.merge(ds, left_on="type", right_on="inst_type", how="left")
    no_datasheet = merged[merged.inst_type.isna()]
    open_review = docs[docs.review_status != "approved"]
    expected_docs = 2 * inst["type"].nunique()
    res = dict(instruments=int(len(inst)), stacks=N_STACKS, instrument_types=int(inst["type"].nunique()),
               io_used=io.astype(int).to_dict(), io_installed_with_spare=io_list["installed"].astype(int).to_dict(),
               documents_expected=int(expected_docs), documents_received=int(len(docs)),
               tags_without_datasheet=int(len(no_datasheet)),
               types_without_datasheet=sorted(no_datasheet["type"].unique().tolist()),
               documents_not_approved=int(len(open_review)))
    with pd.ExcelWriter("engineering_lists.xlsx") as xw:
        inst.to_excel(xw, sheet_name="InstrumentIndex", index=False)
        io_list.to_excel(xw, sheet_name="IOList")
        docs.to_excel(xw, sheet_name="DocumentRegister", index=False)
        issues = pd.concat([
            no_datasheet[["tag", "type", "vendor"]].assign(issue="no manufacturer datasheet received"),
            open_review[["doc_no", "inst_type", "vendor"]].rename(columns={"doc_no": "tag", "inst_type": "type"})
            .assign(issue="manufacturer document not yet approved")], ignore_index=True)
        issues.to_excel(xw, sheet_name="Issues", index=False)
    json.dump(res, open("results.json", "w"), indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
