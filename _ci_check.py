import json, os, subprocess

creds = open("/opt/data/.git-credentials").read().strip()
tok = creds.split(":")[-1].replace("@github.com", "")

def gh(method, path, data=None, extra_headers=None):
    cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: token {tok}",
           f"https://api.github.com{path}"]
    if extra_headers:
        for h in extra_headers:
            cmd += ["-H", h]
    if data:
        cmd += ["-d", json.dumps(data)]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout, r.stderr

# try the logs endpoint with explicit Accept and see the raw body
run_id = "32479764191"
body, err = gh("GET",
    f"/repos/BasedNUKEM/dejavu-sibyl-memory/actions/runs/{run_id}/logs",
    extra_headers=["Accept: application/vnd.github+json"])
print("RAW bytes:", len(body))
print("RAW head:", body[:300])
print("STDERR:", err[:200])
