"""Run the demo commands for real and save their output with timing (no secrets are read or printed)."""
import json, os, re, subprocess, sys, time

ROOT = r"C:\dfol\legalhk"
TOKEN = "0xf813c584Fe5e8c86A3F6c7265923CeE0850604aE"
ISSUER = "0xd51E7130B55f10595939f274cCB8c00b52C915b4"
RPC = "https://ethereum-sepolia-rpc.publicnode.com"
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")

env = dict(os.environ, NO_COLOR="1", FORCE_COLOR="0", CI="1")
env["PATH"] = os.path.join(ROOT, "workflow", "node_modules", ".bin") + os.pathsep + env["PATH"]

STEPS = [
    ("forge", "cd contracts; forge test", ["forge", "test"], os.path.join(ROOT, "contracts")),
    ("vitest", "cd workflow; npm test", ["npm.cmd", "test"], os.path.join(ROOT, "workflow")),
    ("cre", "cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0 --broadcast",
     ["cre", "workflow", "simulate", "./workflow", "-T", "staging-settings", "--non-interactive", "--trigger-index", "0", "--broadcast"], ROOT),
    ("restricted", 'cast call 0xf813…04aE "restricted()(bool)" --rpc-url $SEPOLIA',
     ["cast", "call", TOKEN, "restricted()(bool)", "--rpc-url", RPC], ROOT),
    ("transfer", 'cast call 0xf813…04aE "transfer(address,uint256)(bool)" 0x…dEaD 1 --from <issuer> --rpc-url $SEPOLIA',
     ["cast", "call", TOKEN, "transfer(address,uint256)(bool)", "0x000000000000000000000000000000000000dEaD", "1", "--from", ISSUER, "--rpc-url", RPC], ROOT),
]

only = set(sys.argv[1:])
out_path = os.path.join(ROOT, "video", "raw", "terminal.json")
data = json.load(open(out_path)) if os.path.exists(out_path) else {}

for key, shown, cmd, cwd in STEPS:
    if only and key not in only:
        continue
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    lines = []
    for raw in p.stdout:
        txt = ANSI.sub("", raw.rstrip("\r\n"))
        if txt.strip() == "" and (not lines or lines[-1]["t"] == "") :
            continue
        lines.append({"at": round(time.time() - t0, 2), "t": txt})
    code = p.wait()
    data[key] = {"shown": shown, "exit": code, "elapsed": round(time.time() - t0, 2), "lines": lines}
    print(f"{key}: exit={code} lines={len(lines)} elapsed={data[key]['elapsed']}s", flush=True)

json.dump(data, open(out_path, "w"), indent=1)
