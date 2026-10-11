# LeetCode submissions

Accepted SQL and Pandas solutions for [saumya1234](https://leetcode.com/u/saumya1234/) are synced to this repository by GitHub Actions.

- `my-submissions/<problem>/solution.sql` contains the latest accepted MySQL solution.
- `my-submissions/<problem>/solution.py` contains the latest accepted Pandas solution.
- Other SQL dialects have separate `solution.<language>.sql` files.
- `my-submissions/<problem>/submissions/` preserves each accepted submission by its LeetCode ID, including repeated submissions on the same day.
- `.leetcode-sync.json` records archived IDs, source links, timestamps, and file hashes. Each run checks the full submission history and repairs missing archive files.

The **Sync Leetcode** workflow runs hourly at minute 17 UTC. GitHub may delay scheduled jobs. For an immediate update, open **Actions → Sync Leetcode → Run workflow** on `main`.

## Authentication

`LEETCODE_SESSION` is an encrypted repository secret. The script normally obtains a CSRF token automatically from LeetCode. If LeetCode blocks that request, set `LEETCODE_CSRF_TOKEN` to the `csrftoken` cookie from the same signed-in session. Credentials are only sent to `https://leetcode.com`, and are never written to repository files or logged.

LeetCode session cookies can expire or be invalidated. No scheduled sync based on a session cookie can guarantee that it will work indefinitely. When a run reports an expired session or denied access:

1. Sign in to LeetCode as `saumya1234` in Chrome.
2. Open Chrome Developer Tools → Application → Cookies → `https://leetcode.com`.
3. Copy the current `LEETCODE_SESSION` value into **Settings → Secrets and variables → Actions → LEETCODE_SESSION → Edit**. If a CSRF token is needed, save `csrftoken` as `LEETCODE_CSRF_TOKEN` there too.
4. Run **Sync Leetcode** again and verify a green run and its submission count.

Treat both cookie values as credentials. Enter them directly in GitHub's encrypted secret forms; keep them out of chats, issues, commits, screenshots, and logs.

The workflow retries temporary API failures, serializes sync runs, uses normal Git pushes with rebase retries, and fails clearly on authentication or API errors. GitHub Actions failure notifications remain useful because they identify when credentials need attention.

## Verify locally

The sync uses only the Python standard library. Run its offline checks with:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```
