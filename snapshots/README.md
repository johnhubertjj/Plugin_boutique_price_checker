# Snapshot Artifacts

This folder contains reproducible repository state snapshots:

- `000_head_baseline_eb245da.tar.gz`: tracked files at commit `eb245da` (before uncommitted worktree changes).
- `001_current_working_tree.tar.gz`: current working tree snapshot (includes tracked + untracked files, excluding `.git`, `.venv`, caches, and this `snapshots/` folder).
- `SHA256SUMS.txt`: checksums for snapshot verification.

## Verify

```bash
cd /Users/johnjoseph/PycharmProjects/plugin_boutique_price_checker
shasum -a 256 -c snapshots/SHA256SUMS.txt
```

## Restore baseline snapshot into a new folder

```bash
mkdir -p /tmp/plugin_boutique_state_000
tar -xzf snapshots/000_head_baseline_eb245da.tar.gz -C /tmp/plugin_boutique_state_000
```

## Restore current working snapshot into a new folder

```bash
mkdir -p /tmp/plugin_boutique_state_001
tar -xzf snapshots/001_current_working_tree.tar.gz -C /tmp/plugin_boutique_state_001
```

## Important limitation

Exact per-prompt intermediate filesystem states cannot be reconstructed perfectly without commits/tags made at those times.
These snapshots provide the two reliable states available now: baseline `HEAD` and current workspace.

