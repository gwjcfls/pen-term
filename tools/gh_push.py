#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh_push.py —— 不用 git，直接用 GitHub REST API 把本地目录建成新仓库并推送

用法:
    python gh_push.py --dir <本地目录> --repo <仓库名> --token <PAT> \
        [--desc "描述"] [--private] [--dry-run]

需要 token 具备 repo 权限（classic PAT 勾 repo；fine-grained 需要 Contents+Administration 写权限）。
流程：建仓库 → 逐个文件建 blob → 建 tree → 建 commit → 建 ref(refs/heads/main)。
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"


def req(method, path, token, payload=None, tries=4):
    url = API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    last = None
    for attempt in range(1, tries + 1):
        r = urllib.request.Request(url, data=data, method=method)
        r.add_header("Authorization", "Bearer " + token)
        r.add_header("Accept", "application/vnd.github+json")
        r.add_header("User-Agent", "ydpen-gh-push")
        if data:
            r.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(r, timeout=180) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")
            if e.code in (500, 502, 503, 504) and attempt < tries:
                last = "%s %s" % (e.code, detail[:200])
                time.sleep(2 * attempt)
                continue
            print("[!] %s %s -> %s %s\n%s" % (method, path, e.code, e.reason, detail[:500]))
            raise
        except Exception as e:                     # 连接被重置/超时 → 重试
            last = str(e)
            if attempt < tries:
                print("[i] %s %s 失败(%s)，第 %d 次重试…" % (method, path, e, attempt))
                time.sleep(2 * attempt)
                continue
            print("[!] %s %s 重试 %d 次仍失败: %s" % (method, path, tries, last))
            raise
    raise RuntimeError(last)


def walk(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "tmp")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            out.append((rel, p))
    return sorted(out)


def ensure_ref(owner, name, tok, files):
    """空仓库不能直接建 blob（409 Git Repository is empty）→ 先用 Contents API 建一个文件拿到首个提交"""
    try:
        r = req("GET", "/repos/%s/%s/git/ref/heads/main" % (owner, name), tok)
        return r["object"]["sha"]
    except urllib.error.HTTPError:
        pass
    seed_rel, seed_path = None, None
    for rel, p in files:
        if rel.lower().startswith("readme"):
            seed_rel, seed_path = rel, p
            break
    if seed_rel is None:
        seed_rel, seed_path = ".gitkeep", None
    content = open(seed_path, "rb").read() if seed_path else b""
    print("[i] 空仓库：先用 Contents API 建 %s 以产生首个提交" % seed_rel)
    req("PUT", "/repos/%s/%s/contents/%s" % (owner, name, seed_rel), tok,
        {"message": "init repository", "content": base64.b64encode(content).decode("ascii")})
    r = req("GET", "/repos/%s/%s/git/ref/heads/main" % (owner, name), tok)
    return r["object"]["sha"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--desc", default="")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    files = walk(root)
    total = sum(os.path.getsize(p) for _, p in files)
    print("目录 %s：%d 个文件，共 %.1f MB" % (root, len(files), total / 1048576.0))
    for rel, p in files:
        print("   %8d  %s" % (os.path.getsize(p), rel))
    if args.dry_run:
        print("[dry-run] 未推送")
        return 0

    tok = args.token
    # 1) 建仓库
    try:
        repo = req("POST", "/user/repos", tok, {
            "name": args.repo, "description": args.desc,
            "private": bool(args.private), "auto_init": False,
        })
    except urllib.error.HTTPError as e:
        if e.code == 422:      # 已存在 → 取现有的
            me = req("GET", "/user", tok)
            repo = req("GET", "/repos/%s/%s" % (me["login"], args.repo), tok)
            print("[i] 仓库已存在，往里面推：%s" % repo["html_url"])
        else:
            raise
    owner, name = repo["owner"]["login"], repo["name"]
    print("[+] 仓库：%s" % repo["html_url"])

    # 1.5) 空仓库要先产生首个提交，否则建 blob 会 409
    parent = ensure_ref(owner, name, tok, files)
    print("[i] 父提交 %s" % parent[:8])

    # 2) 建 blobs
    tree = []
    for rel, p in files:
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        blob = req("POST", "/repos/%s/%s/git/blobs" % (owner, name), tok,
                   {"content": b64, "encoding": "base64"})
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("    blob %s" % rel)

    # 3) tree + commit
    t = req("POST", "/repos/%s/%s/git/trees" % (owner, name), tok, {"tree": tree})
    msg = args.desc or ("add %s" % args.repo)
    c = req("POST", "/repos/%s/%s/git/commits" % (owner, name), tok,
            {"message": msg, "tree": t["sha"], "parents": [parent]})
    print("[+] commit %s" % c["sha"][:8])

    # 4) ref
    try:
        req("POST", "/repos/%s/%s/git/refs" % (owner, name), tok,
            {"ref": "refs/heads/" + args.branch, "sha": c["sha"]})
    except urllib.error.HTTPError:
        req("PATCH", "/repos/%s/%s/git/refs/heads/%s" % (owner, name, args.branch), tok,
            {"sha": c["sha"], "force": True})
    print("[✓] 推送完成：%s/tree/%s" % (repo["html_url"], args.branch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
