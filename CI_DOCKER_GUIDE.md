# Docker-Based CI Guide

This document explains the Docker-based CI strategy for mkquartodocs, designed to solve Quarto port conflicts while being resource-conscious for open-source infrastructure.

## Problem Statement

Quarto occasionally hangs in GitHub Actions with the error "Couldn't find open server", likely due to:
- Port conflicts with other processes on the runner
- Chromium browser issues when rendering mermaid diagrams
- Race conditions in Quarto's internal server management

The tests were timing out after 6 hours, consuming significant OSS resources.

## Solution: Containerized Tests with Aggressive Caching

### Key Features

1. **Multi-stage Dockerfile** - Optimized for layer caching
2. **Docker BuildKit caching** - Leverages GitHub Container Registry
3. **Test timeout protection** - Prevents individual test hangs
4. **Multi-version matrix** - Tests Python 3.10, 3.12 with Quarto 1.8.25, 1.9.9

### Caching Strategy

The solution minimizes CI resource usage through multiple caching layers:

#### 1. Docker Layer Caching

The Dockerfile is structured in stages to maximize cache hits:

```dockerfile
# Stage 1: Base (rarely changes)
- Quarto image
- System packages (chromium, python, xvfb)
- Quarto chromium installation

# Stage 2: Python environment (changes only when dependencies change)
- uv installation
- Project dependencies (from requirements.txt)
```

**Key architectural decision**: Source code is NOT copied into the image. It's mounted at runtime via `-v` flag. This means:
- Docker layers only rebuild when dependencies actually change
- Code changes don't invalidate the Docker cache
- Version bumps in pyproject.toml don't trigger rebuilds (only actual dependency changes do)

#### 2. External Dependency Resolution

**IMPORTANT**: Dependencies are exported to `requirements.txt` BEFORE building the Docker image:

```bash
uv export --no-hashes --python ${PYTHON_VERSION} --all-groups > requirements.txt
```

This approach provides fine-grained cache invalidation:
- Cache only invalidates when actual dependencies change
- Version bumps in pyproject.toml (patch/minor/major) don't trigger rebuilds
- More explicit and predictable than using pyproject.toml + uv.lock directly

#### 3. GitHub Container Registry Caching

The workflow uses `docker/build-push-action@v5` with:
- `cache-from`: Pulls cached layers from GHCR
- `cache-to`: Pushes new layers to GHCR with `mode=max`

Cache keys are based on:
- Python version (e.g., `3.12`)
- Quarto version (e.g., `1.9.9`)
- Dependency hash (`hashFiles('requirements.txt')`)

This means:
- First run: ~5-10 minutes (full build)
- Subsequent runs with no changes: ~30 seconds (pure cache)
- After dependency update: ~2-3 minutes (only rebuild Python environment layer)
- After code change: ~30 seconds (no rebuild needed - code is mounted at runtime)

#### 4. Fallback Cache Keys

The workflow tries multiple cache keys in order:
1. Exact match: `py3.12-quarto1.9.9-<requirements.txt hash>`
2. Same versions, different dependencies: `py3.12-quarto1.9.9-`
3. Same Python, any Quarto: `py3.12-`

This ensures partial cache hits even when dependencies change.

### Resource Usage Comparison

**Before (native runner):**
- 6 hours timeout per job × 3 Python versions = 18 hours wasted
- No isolation, unpredictable failures

**After (containerized with caching):**
- First run: ~10 minutes per job × 4 combinations = 40 minutes
- Subsequent runs: ~2-3 minutes per job × 4 combinations = ~10 minutes
- Predictable, isolated environment

**Monthly scheduled run:**
- Cache likely still valid from recent PRs
- ~10-15 minutes total

## Testing Locally

To test the Docker setup locally, you must first generate `requirements.txt`:

```bash
# Step 1: Generate requirements.txt for the Python version you want to test
uv export --no-hashes --python 3.12 --all-groups > requirements.txt

# Step 2: Build the image (with default Python 3.12 and Quarto 1.9.10)
docker build -t mkquartodocs-test:local .

# Or build with specific versions
uv export --no-hashes --python 3.10 --all-groups > requirements.txt
docker build -t mkquartodocs-test:local \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg QUARTO_VERSION=1.8.25 .

# Step 3: Run tests
docker run --rm \
  -v $(pwd):/work \
  -e DISPLAY=:99 \
  --security-opt seccomp=unconfined \
  mkquartodocs-test:local \
  bash -c "Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & sleep 2 && uv run --all-groups python -m pytest -xs --cov . --cov-report=xml"

# Or run interactively
docker run --rm -it \
  -v $(pwd):/work \
  mkquartodocs-test:local bash
```

**Important notes:**
- You MUST generate `requirements.txt` before building the image
- The `requirements.txt` should match the Python version specified in `--build-arg PYTHON_VERSION`
- Source code is NOT baked into the image - it's mounted at runtime via `-v $(pwd):/work`
- Changes to source code don't require rebuilding the image

## Workflow Configuration

### Matrix Strategy

We test 4 combinations to balance coverage and resource usage:
- Python 3.10 + Quarto 1.8.25
- Python 3.10 + Quarto 1.9.9
- Python 3.12 + Quarto 1.8.25
- Python 3.12 + Quarto 1.9.9

This tests both minimum and current Python versions (3.10, 3.12) against a stable Quarto version (1.8.25) and the latest (1.9.9).

### Timeout Protection

Three layers of timeout protection:
1. **Per-test timeout**: `pytest --timeout=300` (5 minutes)
2. **Test suite timeout**: `timeout 30m` in bash
3. **GitHub Actions job timeout**: `timeout-minutes: 35`

If any test hangs, it will be killed after 5 minutes instead of running for 6 hours.

### Concurrency Control

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This cancels old runs when new commits are pushed, saving resources.

## Troubleshooting

### Cache Miss

If cache misses occur frequently:
1. Check if base image tag changed (e.g., `quarto:latest` updated)
2. Verify cache-key generation in workflow logs
3. Check GHCR permissions for the repository

### Build Timeout

If Docker build times out:
1. Check Docker Hub rate limits
2. Verify GHCR authentication
3. Consider pinning base image to specific version

### Test Failures

If tests fail in Docker but not locally:
1. Check Xvfb display setup
2. Verify Chromium installation in container
3. Check port conflicts (should be isolated)

## Migration Path

To migrate from the old CI:

1. **Test the new workflow**: Use `.github/workflows/CICD-docker.yml`
2. **Monitor first runs**: Check cache effectiveness
3. **Compare timing**: Verify it's faster than native runner
4. **Disable old workflow**: Rename or remove `.github/workflows/CICD.yml`

## Maintenance

### Updating Dependencies

When you add or remove dependencies in `pyproject.toml`:

1. The CI will automatically detect the change (via requirements.txt hash)
2. Only the Python environment layer will rebuild (~2-3 minutes)
3. No manual intervention needed

### Updating Base Image

```dockerfile
# Pin to specific version for stability
FROM ghcr.io/quarto-dev/quarto:1.9.9

# Or use version range
ARG QUARTO_VERSION=1.9.10
FROM ghcr.io/quarto-dev/quarto:${QUARTO_VERSION}
```

### Updating Python Versions

1. Add to matrix in `CICD-docker.yml`
2. Update `requires-python` in `pyproject.toml`
3. Test locally first

### Clearing Cache

If cache becomes corrupt:
1. Go to repository → Actions → Caches
2. Delete relevant caches
3. Next run will rebuild from scratch

## Cost Analysis

GitHub Actions provides 2,000 free minutes/month for public repositories.

**Before**: Could consume 18 hours (1,080 minutes) on a single failed run
**After**: ~40 minutes for cold build, ~10 minutes for cached runs

This reduces resource usage by **~97%** for typical runs.

## Future Improvements

1. **Cache size monitoring**: Track GHCR cache size
2. **Parallel test execution**: Split test suite across containers
3. **ARM builds**: Add ARM64 support for M1/M2 runners
4. **Pre-built images**: Push base images to GHCR for even faster builds
