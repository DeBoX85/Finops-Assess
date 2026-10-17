#!/bin/sh
# Local git hooks are not cloned; run this once per clone (the cloud workspace is ephemeral, so run it each session).
cat > "$(git rev-parse --git-dir)/hooks/pre-push" <<'H'
#!/bin/sh
python3 scripts/docs_check.py || { echo "pre-push: documentation check failed"; exit 1; }
H
chmod +x "$(git rev-parse --git-dir)/hooks/pre-push"; echo "pre-push hook installed"
