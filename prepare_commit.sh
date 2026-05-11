#!/bin/bash
# Script to properly stage and commit the harness implementation

cd /workspaces/docs-as-code

# Update .gitignore to exclude sensitive/temporary files
cat >> .gitignore << 'EOF'

# Harness execution history (local only)
score_harness/runs/

# Internal OEM documentation (confidential)
docs/internals/requirements/oem_internal_workstreams.md

# Temporary issue drafts (already created in GitHub)
.tmp_issue_updates/
EOF

# Stage the harness implementation
git add AGENTS.md
git add score_harness/

# Show what will be committed
echo "========================================="
echo "Files to be committed:"
echo "========================================="
git status --short

echo ""
echo "========================================="
echo "Excluded files (not staged):"
echo "========================================="
git status --short | grep "^??" | grep -E "(oem_internal|\.tmp_issue|runs/)"

echo ""
echo "========================================="
echo "Ready to commit! Use:"
echo "========================================="
echo 'git commit -m "feat(harness): Add pilot foundation for docs-as-code assurance harness

- Add outer loop with both metrics_json and needs_json task modes
- Add lightweight candidate validation and query tooling  
- Add baseline + rule-retrieval harness candidates
- Add provenance metadata and responsibility model for audit compliance
- Add tool safety restrictions and compliance documentation
- Create executable seed corpus (4 tasks)

Addresses #518, #524
Part of #520"'
