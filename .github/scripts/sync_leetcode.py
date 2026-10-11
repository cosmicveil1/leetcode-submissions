"""Archive every accepted SQL/Pandas submission using an existing LeetCode session."""

import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://leetcode.com"
LANGUAGES = {"mysql", "mssql", "oraclesql", "postgresql", "pythondata"}
LIST_QUERY = """query($offset: Int!, $limit: Int!) {
  submissionList(offset: $offset, limit: $limit) {
    hasNext submissions { id lang timestamp statusDisplay runtime title memory titleSlug }
  }
}"""
DETAIL_QUERY = """query($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    code question { questionId }
  }
}"""


class SyncError(Exception):
    pass


class SameSiteRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(BASE + "/"):
            raise SyncError("LeetCode redirected outside leetcode.com; sync stopped.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self, session, csrf=""):
        if not session:
            raise SyncError("Missing LEETCODE_SESSION repository secret.")
        self.jar = http.cookiejar.CookieJar()
        self.jar.set_cookie(http.cookiejar.Cookie(
            version=0, name="LEETCODE_SESSION", value=session, port=None,
            port_specified=False, domain=".leetcode.com", domain_specified=True,
            domain_initial_dot=True, path="/", path_specified=True, secure=True,
            expires=None, discard=True, comment=None, comment_url=None,
            rest={"HttpOnly": None}, rfc2109=False,
        ))
        if csrf:
            self.jar.set_cookie(http.cookiejar.Cookie(
                version=0, name="csrftoken", value=csrf, port=None,
                port_specified=False, domain=".leetcode.com", domain_specified=True,
                domain_initial_dot=True, path="/", path_specified=True, secure=True,
                expires=None, discard=True, comment=None, comment_url=None,
                rest={}, rfc2109=False,
            ))
        self.opener = urllib.request.build_opener(
            SameSiteRedirects(), urllib.request.HTTPCookieProcessor(self.jar)
        )
        self.csrf = csrf

    def request(self, path, payload=None):
        for attempt in range(4):
            headers = {
                "User-Agent": "Mozilla/5.0 LeetCodeSubmissionArchive/1.0",
                "Referer": BASE + "/", "Origin": BASE,
            }
            data = None
            if payload is not None:
                headers.update({"Content-Type": "application/json", "X-CSRFToken": self.csrf})
                data = json.dumps(payload).encode()
            req = urllib.request.Request(BASE + path, data=data, headers=headers)
            try:
                with self.opener.open(req, timeout=30) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                if exc.code in {401, 403}:
                    raise SyncError(
                        "LeetCode denied access. Refresh LEETCODE_SESSION and, if needed, "
                        "LEETCODE_CSRF_TOKEN from the same signed-in browser session."
                    ) from None
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                    raise SyncError(f"LeetCode returned HTTP {exc.code}; no credentials were logged.") from None
            except (urllib.error.URLError, TimeoutError):
                if attempt == 3:
                    raise SyncError("LeetCode could not be reached after four attempts.") from None
            time.sleep(2 ** attempt)
        raise SyncError("LeetCode request did not complete.")

    def authenticate(self, expected_username):
        if not self.csrf:
            self.request("/")
            self.csrf = next((c.value for c in self.jar if c.name == "csrftoken"), "")
        if not self.csrf:
            raise SyncError("LeetCode did not issue a CSRF token. Add LEETCODE_CSRF_TOKEN from the same browser session.")
        status = self.query("query { userStatus { isSignedIn username } }").get("userStatus")
        if not isinstance(status, dict) or not status.get("isSignedIn"):
            raise SyncError("LEETCODE_SESSION is expired or invalid. Update that repository secret from your signed-in browser.")
        if status.get("username") != expected_username:
            raise SyncError("The stored LeetCode session belongs to a different username. Sync stopped.")

    def query(self, query, variables=None):
        try:
            response = json.loads(self.request("/graphql/", {"query": query, "variables": variables or {}}))
        except (ValueError, UnicodeDecodeError):
            raise SyncError("LeetCode returned a non-JSON response; no submissions were marked synced.") from None
        if response.get("errors") or not isinstance(response.get("data"), dict):
            raise SyncError("LeetCode returned a GraphQL error. Check session validity and API availability; no submissions were marked synced.")
        return response["data"]


def all_submissions(client):
    found = {}
    offset = 0
    for _ in range(1000):
        page = client.query(LIST_QUERY, {"offset": offset, "limit": 50}).get("submissionList")
        if not isinstance(page, dict) or not isinstance(page.get("submissions"), list):
            raise SyncError("LeetCode returned no submission list. Refresh the session; no submissions were marked synced.")
        rows = page["submissions"]
        if page.get("hasNext") and not rows:
            raise SyncError("LeetCode returned an empty page with more pages pending. Sync stopped.")
        for row in rows:
            if row.get("statusDisplay") == "Accepted" and row.get("lang") in LANGUAGES:
                found[str(row["id"])] = row
        if not page.get("hasNext"):
            return sorted(found.values(), key=lambda s: (int(s["timestamp"]), int(s["id"])))
        offset += len(rows)
        time.sleep(1)
    raise SyncError("Submission pagination exceeded the safety limit; sync stopped.")


def folder_for(root, slug, question_id):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SyncError("LeetCode returned an invalid problem slug.")
    destination = root / "my-submissions"
    matches = sorted(p for p in destination.glob("*") if p.is_dir() and p.name.endswith("-" + slug))
    if len(matches) > 1:
        raise SyncError(f"Multiple existing folders match {slug}; sync stopped to avoid overwriting files.")
    if matches:
        return matches[0]
    if not str(question_id).isdigit():
        raise SyncError("LeetCode returned an invalid question ID.")
    return destination / f"{int(question_id):04d}-{slug}"


def archive(root, client, submissions):
    root = Path(root)
    manifest_path = root / ".leetcode-sync.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"version": 1, "submissions": {}}
    if manifest.get("version") != 1 or not isinstance(manifest.get("submissions"), dict):
        raise SyncError("The submission manifest has an unsupported format.")
    records = manifest["submissions"]
    added = 0
    latest = {}
    for submission in submissions:
        sid, language, slug = str(submission["id"]), submission["lang"], submission["titleSlug"]
        if not sid.isdigit() or language not in LANGUAGES:
            raise SyncError("LeetCode returned an invalid submission ID or language.")
        record = records.get(sid)
        archive_path = root / record["archive_path"] if record else None
        if archive_path and not archive_path.resolve().is_relative_to((root / "my-submissions").resolve()):
            raise SyncError("The manifest contains an archive path outside my-submissions.")
        valid = bool(archive_path and archive_path.is_file() and hashlib.sha256(archive_path.read_bytes()).hexdigest() == record.get("sha256"))
        if not valid:
            details = client.query(DETAIL_QUERY, {"submissionId": int(sid)}).get("submissionDetails")
            if not isinstance(details, dict) or not isinstance(details.get("code"), str):
                raise SyncError(f"Could not retrieve accepted submission {sid}; no submissions were marked synced.")
            folder = folder_for(root, slug, (details.get("question") or {}).get("questionId"))
            extension = "py" if language == "pythondata" else "sql"
            archive_path = folder / "submissions" / f"{sid}.{language}.{extension}"
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            code = details["code"]
            code += "" if code.endswith("\n") else "\n"
            archive_path.write_bytes(code.encode())
            if not (folder / "README.md").exists():
                (folder / "README.md").write_text(f"# {submission['title']}\n\n[Problem on LeetCode]({BASE}/problems/{slug}/)\n\nAccepted submissions are archived in `submissions/`.\n", encoding="utf-8")
            record = {
                "id": sid, "problem": slug, "language": language,
                "timestamp": int(submission["timestamp"]),
                "source_url": f"{BASE}/problems/{slug}/submissions/{sid}/",
                "archive_path": archive_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            }
            records[sid] = record
            added += 1
            time.sleep(0.5)
        key = (slug, language)
        previous = latest.get(key)
        if previous is None or (record["timestamp"], int(sid)) > (previous["timestamp"], int(previous["id"])):
            latest[key] = record
    for (_, language), record in latest.items():
        archive_path = root / record["archive_path"]
        filename = "solution.py" if language == "pythondata" else "solution.sql" if language == "mysql" else f"solution.{language}.sql"
        (archive_path.parent.parent / filename).write_bytes(archive_path.read_bytes())
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return added, len(submissions), len(latest)


def main():
    client = Client(os.environ.get("LEETCODE_SESSION", ""), os.environ.get("LEETCODE_CSRF_TOKEN", ""))
    client.authenticate(os.environ.get("LEETCODE_USERNAME", "saumya1234"))
    submissions = all_submissions(client)
    added, total, solutions = archive(Path.cwd(), client, submissions)
    summary = f"Checked {total} accepted SQL/Pandas submissions; archived {added} new submissions; {solutions} current solutions."
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(summary + "\n")


if __name__ == "__main__":
    try:
        main()
    except (SyncError, OSError, KeyError, ValueError):
        error = sys.exc_info()[1]
        message = str(error) if isinstance(error, SyncError) else "Invalid local manifest or submission data; no sync commit was created."
        print("::error::" + message)
        print("See repository Settings > Secrets and variables > Actions. Never put session cookies in code, logs, issues, or chat.")
        sys.exit(1)
