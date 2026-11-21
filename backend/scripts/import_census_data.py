import argparse,csv,sqlite3
p=argparse.ArgumentParser(); p.add_argument("csv_file"); p.add_argument("--db",default="poupscan.db"); a=p.parse_args()
db=sqlite3.connect(a.db); db.execute("CREATE TABLE IF NOT EXISTS census(area_name TEXT, census_year INTEGER, total_population INTEGER, source_reference TEXT, UNIQUE(area_name,census_year))")
ok=skip=0
with open(a.csv_file,encoding="utf-8-sig",newline="") as f:
 for row in csv.DictReader(f):
  try:
   db.execute("INSERT OR IGNORE INTO census VALUES(?,?,?,?)",(row["area_name"],int(row["census_year"]),int(row["total_population"]),row.get("source_reference",""))); ok+=1
  except Exception: skip+=1
db.commit(); print({"processed":ok,"skipped":skip})
