import urllib.request, urllib.error, json, time

dois = [
    "10.5555/slop.zxua1o",
    "10.5555/slop.xg98oi",
    "10.5555/slop.a1hnm0",
    "10.5555/slop.fw3hoa",
    "10.5555/slop.c1shzy",
    "10.5555/slop.4qpuqz",
    "10.5555/slop.1nlzjm",
    "10.5555/slop.ldoad5",
    "10.5555/slop.24ft4m",
    "10.5555/slop.ce3dwm",
]

results = {}
client = httpx.Client(timeout=15)

for doi in dois:
    row = {}
    # Crossref
    try:
        r = client.get(f"https://api.crossref.org/works/{doi}")
        row["crossref"] = "FOUND" if r.status_code == 200 else f"not found ({r.status_code})"
    except Exception as e:
        row["crossref"] = f"error: {e}"
    # OpenAlex
    try:
        r = client.get(f"https://api.openalex.org/works?filter=doi:{doi}")
        d = r.json()
        row["openalex"] = "FOUND" if d.get("meta", {}).get("count", 0) > 0 else "not found"
    except Exception as e:
        row["openalex"] = f"error: {e}"
    # DataCite
    try:
        r = client.get(f"https://api.datacite.org/dois/{doi}")
        row["datacite"] = "FOUND" if r.status_code == 200 else f"not found ({r.status_code})"
    except Exception as e:
        row["datacite"] = f"error: {e}"
    # Semantic Scholar direct DOI lookup
    try:
        r = client.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}")
        if r.status_code == 200:
            row["semanticscholar"] = "FOUND"
        elif r.status_code == 404:
            row["semanticscholar"] = "not found (404)"
        elif r.status_code == 429:
            row["semanticscholar"] = "rate limited (429)"
        else:
            row["semanticscholar"] = f"status {r.status_code}"
    except Exception as e:
        row["semanticscholar"] = f"error: {e}"
    results[doi] = row
    print(doi, row)
    time.sleep(1.2)

json.dump(results, open("doi_check_results.json", "w"), indent=2)
