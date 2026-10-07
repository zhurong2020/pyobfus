# Case studies: how we collect and publish usage reports

pyobfus is maintained by one person and its claims are only as good as the
evidence behind them. Reports from people who used it on real projects,
including the ones where it failed, are the most useful evidence we can get.

## Share a report

Open a [Show and tell discussion](https://github.com/zhurong2020/pyobfus/discussions/new?category=show-and-tell).
The form asks what you protected, how it is delivered, the versions, how you
checked the output, and what went wrong. Do not include proprietary source,
mapping files, licence keys or customer data. Bugs are better filed as
[issues](https://github.com/zhurong2020/pyobfus/issues).

## What counts as what

We keep four kinds of signal apart and do not present one as another:

| Kind | Example | What it shows |
|---|---|---|
| Maintainer content | Posts and benchmarks written by the maintainer | Our own account, not independent |
| Listings and mirrors | Package indexes, MCP directories, security scanners | That pyobfus can be found, not that anyone uses it |
| External trial | Someone ran it and reported back | That it was tried, and what happened |
| Verifiable adoption | A public project that pins pyobfus in its build or CI, or a user who describes their production use on the record | Real use, within the scope they describe |

## Publishing rules

- We publish a report as a case study only with the reporter's explicit
  consent, and only the parts they agreed to.
- Anonymous reports can inform our work but are not presented as verifiable
  adoption.
- If the maintainer gave the reporter a free licence, payment or hands-on
  help, the case study says so.
- We never ask for a positive review, a star or a recommendation in exchange
  for help, and we do not write reports on anyone's behalf.
- Our own projects that use pyobfus are described as the maintainer's own
  use, not as external adoption.

## Case study template

Each published case study covers: the task; why the code ships locally; the
pyobfus, Python and OS versions; the delivery method; the `--check` findings;
the preset or configuration; how the original and obfuscated builds were
compared; problems met and how they were resolved; how the mapping file is
kept; where it runs now; limitations; links to public evidence; and any
licence, payment or help received.

No case studies have been published yet.
