# Shared by pre-commit (scan 3) and commit-msg. Sourced, not executed.
#
# Customer / business data that must not enter this PUBLIC repo: Stripe
# object IDs and e-mail addresses outside a short allowlist. See the
# "Public vs private records" rule in AGENTS.md. Origin: 2026-10-29, when a
# plan entry nearly published a customer's payment and invoice details and
# the existing scans (fixed PII words, credential prefixes) could not see it.

# Stripe object IDs: prefix + underscore + 14+ alphanumerics. Underscores are
# excluded from the tail, so ordinary identifiers like `in_place_ops` or
# `pi_value` do not match.
CUSTOMER_STRIPE_ID_RE='(^|[^A-Za-z0-9_])(cs_live|cs_test|pi|ch|pm|pmc|gcus|cus|po|plink|we|in|il|ii|evt|acct|sub|prod|price|txn|re|dp|cn|seti|src)_[A-Za-z0-9]{14,}'

# Any e-mail address.
CUSTOMER_EMAIL_RE='[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'

# E-mail addresses that may appear: documentation/test domains, the
# maintainer's public addresses, project and vendor support addresses, and
# git trailers. Matched against the whole address, case-insensitively.
CUSTOMER_EMAIL_ALLOW_RE='^([^@]+@(example\.(com|org|net)|[^@]*\.example|[^@]*\.invalid|[^@]*\.test|corp\.com|bar\.com|b\.co|users\.noreply\.github\.com|noreply\.github\.com|anthropic\.com|mail\.anthropic\.com|glama\.ai|mcpservers\.org|pulsemcp\.com|microsoft\.com|pyobfus\.dev|arong\.eu\.org)|your@email\.com|zhurong0525@(gmail|icloud)\.com|wuxiami@hotmail\.com|zhurong@7fp1fj\.onmicrosoft\.com)$'

# Skipped by the e-mail check only (Stripe IDs are checked everywhere):
# source files, where decorators such as `x@enum.global_enum` look like
# addresses, and lock files, which carry package-author metadata.
CUSTOMER_EMAIL_SKIP_FILE_RE='\.(py|pyi|ts|js|mjs|cjs)$|(^|/)(package-lock\.json|uv\.lock|poetry\.lock)$'

# customer_scan_records SKIP_EMAIL_FILES(0|1)
# stdin: records "FILE:LINE:CONTENT". stdout: "FILE:LINE: <kind>" per hit.
# Never prints the matched value.
customer_scan_records() {
    local skip="$1" rec loc file content addr
    while IFS= read -r rec || [[ -n "$rec" ]]; do
        file=${rec%%:*}
        content=${rec#*:}
        loc="$file:${content%%:*}"
        content=${content#*:}
        if grep -qE "$CUSTOMER_STRIPE_ID_RE" <<<"$content"; then
            printf '%s: Stripe object ID\n' "$loc"
        fi
        if [[ "$skip" == "1" ]] && grep -qE "$CUSTOMER_EMAIL_SKIP_FILE_RE" <<<"$file"; then
            continue
        fi
        while read -r addr; do
            [[ -z "$addr" ]] && continue
            if ! grep -qiE "$CUSTOMER_EMAIL_ALLOW_RE" <<<"$addr"; then
                printf '%s: e-mail address not on the allowlist\n' "$loc"
                break
            fi
        done < <(grep -oE "$CUSTOMER_EMAIL_RE" <<<"$content" || true)
    done
}

# Pre-filter so the per-record loop only sees lines that can possibly hit.
customer_candidate_filter() {
    grep -E "$CUSTOMER_STRIPE_ID_RE|@" || true
}
