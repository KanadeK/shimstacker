# Security policy

## Supported versions

Security fixes are provided for the latest release.

## Reporting

Please report vulnerabilities through [GitHub's private security advisory form](https://github.com/KanadeK/shimstacker/security/advisories/new). Do not include customer plans, equipment identifiers, or other sensitive production data in a public issue.

## Security boundary

ShimStacker reads a local JSON file and writes a new local report directory. It does not execute plan content, invoke a shell, connect to equipment, access credentials, or make network requests. Authored text is escaped in HTML and Markdown-facing contexts; CSV uses the standard library writer. The generated HTML contains no JavaScript or remote assets.

Resource use is bounded by schema limits and `max_states`. Treat reports as calculation evidence, not safety certification. Incorrect source measurements or omitted physical constraints remain outside the software boundary.

