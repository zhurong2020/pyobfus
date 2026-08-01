# pyobfus 0.5.4 launch wave

**Prepared**: 2026-07-20

**Canonical release**: pyobfus 0.5.4 / pyobfus-mcp 0.3.1

**Repository**: <https://github.com/zhurong2020/pyobfus>

This folder supersedes the pre-0.5 launch drafts. It uses the real CLI syntax,
the 0.5.4 trust boundary, and current community posting rules.

## Baseline before publication

- GitHub: 1 star, 2 forks, 1 open issue, 0 open pull requests.
- PyPI pyobfus: approximately 1,174 downloads in the prior month on
  2026-07-20. Treat this as directional because automated installs are mixed
  into the count.
- Release CI: 1046 passed, 1 skipped, 90% core coverage; Core, MCP, and
  end-to-end test roots all green.
- Public writing: one older DEV article; no completed Show HN or Reddit launch.

Capture the same fields at +24 hours, +7 days, and +30 days. The decision
metric is not raw downloads alone: count stars, forks, issues, discussion
votes, named third-party uses, and repeated feature requests.

## Sequence

1. ✅ Published `devto.md` as the canonical long-form explanation on
   2026-07-22 at
   <https://dev.to/zhurong2020/i-built-a-python-obfuscator-that-keeps-production-traces-debuggable-1mp8>.
2. ✅ Submitted the Show HN on 2026-08-01. See publication record below.
3. ✅ Added `reddit-python.md` to the current r/Python monthly showcase thread
   on 2026-07-23, ahead of Show HN because of an HN 429; no AutoModerator
   removal. See publication record below.
4. Publish `cn.md`'s 长文版 to arong.eu.org, which already carries two prior
   pyobfus posts (2025-12-27, 2026-05-21) — frame as a third, update-style
   post, not a fresh pitch. V2EX is blocked as of 2026-07-23: the maintainer's
   new Google-registered account needs an invite code or a ≥10,000 $V2EX
   Solana holding to activate, neither of which is worth chasing for one post;
   deferred until an invite code turns up normally. If unblocked, target the
   `开源软件` node specifically, not `分享创造`.
5. Open `github-poll.md` as a GitHub Discussions poll after traffic begins.

Never ask friends to upvote, coordinate engagement, or cross-post the same text
simultaneously. Each channel should invite criticism of the threat model and
specific reports of what users need next.

## External prerequisites

- DEV: API key or interactive login.
- HN: an established account currently eligible to submit Show HN.
- Reddit: interactive login and the current monthly showcase thread.
- GitHub Discussions: interactive GitHub login or a refreshed `gh` token.

No credential is stored in this repository.

## Publication record

### DEV — 2026-07-22

- Published at 2026-07-22 02:22:06 UTC.
- Public URL:
  <https://dev.to/zhurong2020/i-built-a-python-obfuscator-that-keeps-production-traces-debuggable-1mp8>
- Canonical URL: <https://github.com/zhurong2020/pyobfus>
- Immediate visible DEV baseline: 0 reactions and 0 comments.
- Immediate GitHub baseline: 1 star, 2 forks, 0 open issues/pull requests.
- Next measurements: +24 hours, +7 days, and +30 days using the fields listed
  under "Baseline before publication".

### Hacker News participation checkpoint — 2026-07-22

- The existing account is 46 days old and the normal submission form is
  available; no technical account block was observed.
- The maintainer published a first, independently written comment on a relevant
  MCP Show HN discussion:
  <https://news.ycombinator.com/item?id=49001279>
- Do not treat elapsed time or karma as a mechanical promotion gate. Continue
  normal, substantive participation on topics the maintainer would discuss even
  without a pyobfus launch.
- The pyobfus Show HN remains deferred. Its title, submission text, first
  comment, and replies must be written by the maintainer without generated or
  AI-edited text.
- Never copy HN `auth=` query parameters, account email, or other session data
  into this repository.

### Show HN — 2026-08-01

- Submitted title: "Show HN: I built a Python obfuscator that keeps
  production traces debuggable" (76 chars, under the 80-char HN title limit),
  linking to <https://github.com/zhurong2020/pyobfus> (not the DEV article).
- Public URL: <https://news.ycombinator.com/item?id=49130416>
- The maintainer left the submission `text` field blank and posted the
  explanation as the first top-level comment instead — states the mangled-name
  readability problem (both for the developer reading a production traceback
  and for AI coding tools like Claude Code/Cursor), then the `--save-mapping`
  / `--unmap` reverse-mapping mechanism that keeps debuggability local while
  production stays obfuscated. Independently written by the maintainer.
- Immediate baseline (~21 minutes after submission): 1 point, 1 comment (the
  maintainer's own).
- **+9h checkpoint**: karma ticked from 1 to 2 (one incremental signal, source
  not distinguishable — could be the submission or the comment). No comments
  from anyone other than the maintainer visible on the thread yet; the item
  has not surfaced on the front page (expected — front-page ranking needs far
  more points than this within the first few hours; a Show HN not reaching
  the front page is the median outcome, not a failure signal). Confirmed via
  the maintainer's own `/threads` page: the comment is correctly attached, no
  `[flagged]`/`[dead]` marker.
- Next measurements: +24 hours, +7 days, and +30 days using the fields listed
  under "Baseline before publication". Maintainer stays available to reply to
  incoming comments; no vote solicitation, no simultaneous cross-posting of
  the same text.
