# CI licensing

Pro builds in CI now need `PYOBFUS_LICENSE_KEY` or a registered runner. Community
builds remain available without activation. CI use does not consume device slots.
The environment variable is the only CI key input; there is no CLI key flag.

A non-empty variable takes precedence over cached registration and trials.
Each build verifies online once, including its parallel workers. No registration,
key, device identifier or approval is persisted locally. Invalid, revoked,
expired, rate-limited or unreachable verification denies Pro access. An older
server reports that it does not support CI activation yet; update the server
before releasing the client. Air-gapped builds use normal registration and cache
instead, with the CI variable unset. See [license activation](LICENSE_ACTIVATION_GUIDE.md).

## GitHub Actions

Store the license as an Actions secret named `PYOBFUS_LICENSE_KEY`:

```yaml
- name: Protect project
  env:
    PYOBFUS_LICENSE_KEY: ${{ secrets.PYOBFUS_LICENSE_KEY }}
  run: pyobfus src -o dist --preset commercial
```

Fork pull requests normally cannot access secrets. Run Community checks for
untrusted contributions and reserve licensed packaging for trusted branches.
Do not expose secrets to untrusted pull-request code.

## GitLab CI

Create a **masked**, protected CI/CD variable named `PYOBFUS_LICENSE_KEY` in the
project settings, limited to trusted protected refs. The job inherits it:

```yaml
protect:
  script:
    - pyobfus src -o dist --preset commercial
```

Do not echo the variable or enable shell tracing around secret handling.
MCP `protect_project` inherits the same variable in its CLI subprocess.

## Docker BuildKit

Pass the variable as a build secret:

```bash
docker build --secret id=pyobfus_license,env=PYOBFUS_LICENSE_KEY .
```

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=pyobfus_license,required=true \
    PYOBFUS_LICENSE_KEY="$(cat /run/secrets/pyobfus_license)" \
    pyobfus src -o dist --preset commercial
```

Never bake the key into `ARG`, `ENV`, copied files or image layers. Restrict
access to the build context, builder and build logs.

## Leaked key and service operation

If a key leaks, contact support to revoke/reissue it, replace the CI secret,
and remove exposed copies and logs. Deleting a log alone does not revoke a key.

CI use is rate-limited per license and does not consume device slots.
A 429 response means retry later. The CI response omits email and the license key.
