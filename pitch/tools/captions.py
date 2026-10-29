"""Build word-timed caption chunks from the script + Whisper timings and inject them into index.html.

Script text is the source of truth for the words; Whisper only supplies the timing.
Run from pitch/:  python tools/captions.py
"""
import difflib, json, re

# where each voice clip (or part of one) sits on the root timeline: (id, clip_from, clip_to, root_start)
PLACE = [
    ("s1_hook", 0, 99, 1.2), ("s2_problem", 0, 99, 11.1), ("s3_cre", 0, 99, 30.85), ("s4_how", 0, 99, 51.8),
    ("s5a_check", 0, 99, 74.1), ("s5b1_cli", 0, 99, 91.5), ("s5b2_flag", 0, 99, 101.5),
    ("s5c_chain", 0, 5.9, 110.6), ("s5c_chain", 5.9, 99, 118.1), ("s5d_events", 0, 99, 126.7),
    ("s6_fit", 0, 99, 137.3), ("s7_honest", 0, 99, 159.2),
]
SHOW0 = {"A.C.R.I.S.": "ACRIS", "C.R.E.": "CRE", "A.P.I.": "API", "A.I.": "AI", "A.P.I.,": "API,", "A.C.R.I.S.,": "ACRIS,"}
NUM = {"14": "fourteen", "30th": "thirtieth", "16": "sixteen", "35": "thirtyfive"}

import re as _re
class _Show(dict):
    def get(self, w, d=None):
        # dotted acronyms read better without dots: A.C.R.I.S. -> ACRIS, C.R.E.? -> CRE?
        return _re.sub(r"((?:[A-Z]\.){2,})", lambda m: m.group(1).replace(".", ""), w)
SHOW = _Show()
norm = lambda w: NUM.get(re.sub(r"[^a-z0-9]", "", w.lower()), re.sub(r"[^a-z0-9]", "", w.lower()))
script = {n["id"]: n["text"] for n in json.load(open("narration.json", encoding="utf-8"))}
heard = json.load(open("assets/vo/words.json", encoding="utf-8"))


def timed(cid):
    toks, hw = script[cid].split(), heard[cid]
    a, b = [norm(t) for t in toks], [norm(w["w"]) for w in hw]
    t = [None] * len(toks)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            t[blk.a + k] = hw[blk.b + k]["s"]
    # unmatched words: spread evenly between the matched neighbours
    end = hw[-1]["e"]
    i = 0
    while i < len(t):
        if t[i] is None:
            j = i
            while j < len(t) and t[j] is None:
                j += 1
            lo = t[i - 1] if i else 0.0
            hi = t[j] if j < len(t) else end
            for k in range(i, j):
                t[k] = lo + (hi - lo) * (k - i + 1) / (j - i + 1)
            i = j
        i += 1
    return list(zip(toks, t)), end


chunks = []
for cid, c0, c1, at in PLACE:
    words, end = timed(cid)
    words = [(w, s) for w, s in words if c0 <= s < c1]
    # one sentence at a time, split into even lines of at most 7 words
    sent, sents = [], []
    for k, (w, s) in enumerate(words):
        d = SHOW.get(w, w)
        # a bare acronym ending a sentence ("... the C.R.E. C.L.I. It compiles") keeps its full stop
        nxt = words[k + 1][0] if k + 1 < len(words) else ""
        if _re.fullmatch(r"(?:[A-Z]\.){2,}", w) and nxt[:1].isupper() and not _re.match(r"(?:[A-Z]\.){2,}", nxt):
            d += "."
        sent.append([d, round(at + s - c0, 3)])
        if d[-1] in ".?!:" or k == len(words) - 1:
            sents.append(sent); sent = []
    for sent in sents:
        # clauses (split at commas), packed into lines of at most 7 words; long clauses split evenly
        clauses, cl = [], []
        for w in sent:
            cl.append(w)
            if w[0].endswith(","):
                clauses.append(cl); cl = []
        if cl: clauses.append(cl)
        parts = []
        for cl in clauses:
            n = -(-len(cl) // 8); size = -(-len(cl) // n)
            parts += [cl[j:j + size] for j in range(0, len(cl), size)]
        line = []
        for part in parts:
            if line and len(line) + len(part) > 7:
                chunks.append({"w": line}); line = []
            line = line + part
        if line:
            # never leave a one-word tail on its own line
            if len(line) == 1 and chunks and len(chunks[-1]["w"]) <= 7 and "end" not in chunks[-1]:
                chunks[-1]["w"] += line
            else:
                chunks.append({"w": line})
    # end time for this clip's last chunk
    chunks[-1]["end"] = round(at + min(end, c1) - c0 + 0.3, 3)

for k, c in enumerate(chunks):
    if "end" not in c:
        nxt = chunks[k + 1]["w"][0][1]
        c["end"] = nxt
    c["start"] = c["w"][0][1]

js = "const CAPS = " + json.dumps([[c["start"], c["end"], c["w"]] for c in chunks], separators=(",", ":")) + ";"
html = open("index.html", encoding="utf-8").read()
html = re.sub(r"/\*CAPS\*/.*?/\*/CAPS\*/", lambda m: "/*CAPS*/" + js + "/*/CAPS*/", html, flags=re.S)
open("index.html", "w", encoding="utf-8").write(html)
print(len(chunks), "chunks")
for c in chunks[:6] + chunks[-4:]:
    print(c["start"], c["end"], " ".join(w for w, _ in c["w"]))
