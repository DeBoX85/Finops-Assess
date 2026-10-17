# 0001 Language: Python
Date 2026-10-17. Status: accepted (user: "Sure we can go with Python").
Context: azqr is Go, MIT, single binary; checks are mostly ARG queries plus Go rules; no cost category, no commitment analytics (KB note 01). Tool is run only by the owner; customers never receive it.
Options: Go (azqr-like, fork or rewrite), Python, PowerShell.
Decision: Python 3.11+, stdlib-first (urllib, tomllib), azure-identity only for sign-in, REST-first.
Consequences: single-binary distribution is not needed. Checks stay data-like (KQL strings, metadata) so a Go port stays possible. Go resource graph SDK is not stable (v0.10.0); Python SDKs are stable, but we call REST anyway (KB note 08).
Revisit if: tool must be shipped to customer machines, or forking azqr proves cheaper (azqr source structure not yet read).
Sources: KB notes 01, 08.
