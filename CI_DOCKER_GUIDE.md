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
4. **Multi-version matrix** - Tests Python 3.10, 3.11, 3.12 with Quarto latest/1.4

### Caching Strategy

The solution minimizes CI resource usage through multiple caching layers:

#### 1. Docker Layer Caching

The Dockerfile is structured in stages to maximize cache hits:

```dockerfile
# Stage 1: Base (rarely changes)
- Quarto image
- System packages (chromium, python)
- Quarto chromium installation

# Stage 2: Python environment (changes on uv updates)
- uv installation
- Common packages (jupyter, matplotlib, pandas, numpy)

# Stage 3: Development (changes on dependency updates)
- Project dependencies (from pyproject.toml)
- Source code (changes most frequently)
```

Each layer only rebuilds when its inputs change.

#### 2. GitHub Container Registry Caching

The workflow uses `docker/build-push-action@v5` with:
- `cache-from`: Pulls cached layers from GHCR
- `cache-to`: Pushes new layers to GHCR with `mode=max`

Cache keys are based on:
- Python version (e.g., `3.12`)
- Quarto version (e.g., `latest`)
- Dependency hash (`hashFiles('pyproject.toml', 'uv.lock')`)

This means:
- First run: ~5-10 minutes (full build)
- Subsequent runs with no changes: ~30 seconds (pure cache)
- After dependency update: ~2-3 minutes (only rebuild affected layers)
- After code change: ~10 seconds (only copy source)

#### 3. Fallback Cache Keys

The workflow tries multiple cache keys in order:
1. Exact match: `py3.12-quarto-latest-<hash>`
2. Same versions, different hash: `py3.12-quarto-latest-`
3. Same Python, any Quarto: `py3.12-`

This ensures cache hits even when dependencies change.

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

To test the Docker setup locally:

```bash
# Build the image
docker build -t mkquartodocs-test:local .

# Run tests
docker run --rm -v $(pwd):/work mkquartodocs-test:local

# Or run interactively
docker run --rm -it -v $(pwd):/work mkquartodocs-test:local bash
```

## Workflow Configuration

### Matrix Strategy

We test 4 combinations to balance coverage and resource usage:
- Python 3.10 + Quarto latest
- Python 3.11 + Quarto latest
- Python 3.12 + Quarto latest
- Python 3.12 + Quarto 1.4

We exclude older Python × older Quarto combinations to reduce the matrix from 6 to 4 jobs.

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

### Updating Base Image

```dockerfile
# Pin to specific version for stability
FROM ghcr.io/quarto-dev/quarto:1.4.0

# Or use latest for newest features
FROM ghcr.io/quarto-dev/quarto:latest
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
