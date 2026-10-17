# 0003 Read-only enforced in code
Date 2026-10-17. Status: accepted.
Decision: fcat.http.Client allows GET to management.azure.com only (public cloud), and POST only to endpoints listed in ALLOWED_POST (currently ARG query). Anything else raises BlockedRequest before any network call. Tests cover PUT, DELETE, an action POST, foreign hosts and http.
Adding an endpoint requires a decision record explaining why it does not change state.
UNVERIFIED: that every future query-style POST (Cost Management query, Log Analytics query) is side-effect free; confirm on Learn when adding.
