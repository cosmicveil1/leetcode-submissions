import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sync_leetcode import Client, SyncError, all_submissions, archive


def submission(sid, timestamp, language="pythondata", status="Accepted"):
    return {"id": sid, "timestamp": str(timestamp), "lang": language,
            "statusDisplay": status, "titleSlug": "invalid-tweets", "title": "Invalid Tweets"}


class FakeClient:
    def __init__(self, pages=None):
        self.pages = iter(pages or [])
        self.detail_calls = []

    def query(self, query, variables=None):
        if "submissionList" in query:
            return {"submissionList": next(self.pages)}
        self.detail_calls.append(variables["submissionId"])
        return {"submissionDetails": {"code": "code " + str(variables["submissionId"]), "question": {"questionId": "1827"}}}


class SyncTests(unittest.TestCase):
    def test_missing_session_fails(self):
        with self.assertRaisesRegex(SyncError, "Missing LEETCODE_SESSION"):
            Client("")

    def test_auth_checks_username(self):
        client = Client("private-session", "private-csrf")
        self.assertEqual({cookie.name for cookie in client.jar}, {"LEETCODE_SESSION", "csrftoken"})
        with patch.object(client, "query", return_value={"userStatus": {"isSignedIn": True, "username": "someone-else"}}):
            with self.assertRaisesRegex(SyncError, "different username"):
                client.authenticate("saumya1234")

    def test_null_list_is_a_clear_failure(self):
        client = FakeClient([None])
        with self.assertRaisesRegex(SyncError, "no submission list"):
            all_submissions(client)

    @patch("sync_leetcode.time.sleep")
    def test_pagination_and_language_filter(self, sleep):
        client = FakeClient([
            {"hasNext": True, "submissions": [submission(3, 3, "mysql"), submission(4, 4, "cpp"), submission(5, 5, status="Wrong Answer")]},
            {"hasNext": False, "submissions": [submission(2, 2), submission(3, 3, "mysql")]},
        ])
        self.assertEqual([s["id"] for s in all_submissions(client)], [2, 3])

    @patch("sync_leetcode.time.sleep")
    def test_every_attempt_archived_and_repeat_is_idempotent(self, sleep):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "my-submissions" / "1827-invalid-tweets"
            folder.mkdir(parents=True)
            (folder / "README.md").write_text("existing problem statement")
            client = FakeClient()
            rows = [submission(2, 2), submission(1, 1), submission(3, 3, "mysql")]
            self.assertEqual(archive(root, client, rows), (3, 3, 2))
            self.assertEqual((folder / "solution.py").read_text(), "code 2\n")
            self.assertEqual((folder / "solution.sql").read_text(), "code 3\n")
            self.assertEqual((folder / "README.md").read_text(), "existing problem statement")
            records = json.loads((root / ".leetcode-sync.json").read_text())["submissions"]
            self.assertEqual(len(records), 3)
            self.assertEqual(archive(root, client, rows), (0, 3, 2))
            self.assertEqual(client.detail_calls, [2, 1, 3, 3])
            records["2"]["timestamp"] = 0
            records["2"]["timestamp_precision"] = "minute"
            (root / ".leetcode-sync.json").write_text(json.dumps({"version": 1, "submissions": records}))
            self.assertEqual(archive(root, client, rows), (0, 3, 2))
            refreshed = json.loads((root / ".leetcode-sync.json").read_text())["submissions"]["2"]
            self.assertEqual(refreshed["timestamp"], 2)
            self.assertNotIn("timestamp_precision", refreshed)
            self.assertEqual((folder / "solution.py").read_text(), "code 2\n")
            missing = root / records["1"]["archive_path"]
            missing.unlink()
            self.assertEqual(archive(root, client, rows)[0], 1)
            self.assertTrue(missing.exists())

    @patch("sync_leetcode.time.sleep")
    def test_unsafe_slug_and_manifest_paths_fail(self, sleep):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = submission(1, 1)
            bad["titleSlug"] = "../outside"
            with self.assertRaisesRegex(SyncError, "invalid problem slug"):
                archive(root, FakeClient(), [bad])
            (root / ".leetcode-sync.json").write_text(json.dumps({"version": 1, "submissions": {"1": {"archive_path": "../outside.py"}}}))
            with self.assertRaisesRegex(SyncError, "outside my-submissions"):
                archive(root, FakeClient(), [submission(1, 1)])


if __name__ == "__main__":
    unittest.main()
