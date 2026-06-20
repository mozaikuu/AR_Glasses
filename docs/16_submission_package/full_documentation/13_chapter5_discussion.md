# Chapter 5 — DISCUSSION

## 5.1 Interpretation of results

The modular monolith structure enabled rapid iteration: failures localized to services rather than opaque client crashes. Cloud LLM dependence
remains the dominant operational risk—mitigated partially by warmup threads and sentence caps but not eliminated.

## 5.2 Threats to validity

- **Construct validity:** Navigation steps are template-based unless enriched with real building graphs.
- **Internal validity:** Single-machine demos may not reflect Wi-Fi contention in lecture halls.
- **External validity:** Campus-specific aliases in `navigation_service` may not transfer without data edits.

## 5.3 Ethical and privacy considerations

Voice and optional camera paths must be deployed with consent signage and least-privilege API keys. QR telemetry can link to location traces—document retention.

### 5.4 Comparison back to related work claims

Related work claimed broader indoor positioning accuracy than this project attempts. The discussion should honestly separate literature capabilities from implemented scope.

Emphasize engineering contributions: explicit REST contracts, multimodal orchestration, embedded audio fetch path, and automated tests.

Future citations should prioritize peer-reviewed sources over blog posts when advisors demand rigor.
