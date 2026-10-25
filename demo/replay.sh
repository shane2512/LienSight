#!/usr/bin/env bash
# Re-runs both CRE simulations (needs: cre login, bun on PATH). Run from repo root.
export PATH="$PWD/workflow/node_modules/.bin:$PATH"
cre workflow simulate ./workflow -T staging-settings --non-interactive --trigger-index 0
cre workflow simulate ./workflow -T clean-settings --non-interactive --trigger-index 0
