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

1. Publish `devto.md` as the canonical long-form explanation.
2. If the maintainer's HN account satisfies the current participation gate,
   submit `show-hn.md` on a weekday and remain available for the first 90
   minutes. Otherwise participate normally before attempting a Show HN.
3. Add `reddit-python.md` to the current r/Python monthly showcase thread;
   current rules do not support the old standalone-showcase plan.
4. Publish `cn.md` to the maintainer-controlled Chinese channel, then adapt its
   short block for V2EX only if current forum rules permit project promotion.
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
