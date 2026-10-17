# Revert procedures
- Undo last commit, keep history: git revert <sha>, push.
- Return to a milestone: git checkout <tag> -b recover/<tag>; compare; do not force push main.
- Bad push of customer data: stop; rotate/redact; follow GitHub's guidance for removing sensitive data (read it first, UNVERIFIED here); log in MISTAKES.
- Lost container, unpushed work: look for bundles/patches listed in HANDOVER.
