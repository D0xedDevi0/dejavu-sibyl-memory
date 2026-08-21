import json, os, subprocess

creds = open("/opt/data/.git-credentials").read().strip()
tok = creds.split(":")[-1].replace("@github.com", "")

def gh(path):
    r = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: token {tok}",
         f"https://api.github.com{path}"],
        capture_output=True, text=True)
    return json.loads(r.stdout)

# the failing CI run
run_id = "32475735757"
jobs = gh(f"/repos/BasedNUKEM/dejavu-sibyl-memory/actions/runs/{run_id}/jobs")
for j in jobs["jobs"]:
    print("JOB", j["name"], j["conclusion"])
    for s in j["steps"]:
        print("  STEP:", s["name"], "->", s["conclusion"])
    # get log for failed job
    log = subprocess.run(
        ["curl", "-sL", "-H", f"Authorization: token {tok}",
         f"https://api.github.com/repos/BasedNUKEM/dejavu-sibyl-memory/actions/jobs/{j['id']}/logs"],
        capture_output=True, text=True)
    # print tail of log
    lines = log.stdout.splitlines()
    print("  === LOG TAIL (40 lines) ===")
    for line in lines[-40:]:
        print("   ", line[:200])
