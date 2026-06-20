# Chapter 6 — CONCLUSIONS

Smart Glasses Distilled demonstrates that a **single FastAPI gateway** with explicit service modules can support multimodal campus assistance
across Expo, Android, and ESP-class clients while remaining testable with pytest. Navigation sessions, QR flows, and ESP TTS fetch paths are
first-class HTTP concerns rather than ad-hoc sockets.

Future work should prioritize durable session storage, richer building models feeding `navigation_service`, and expanded user studies beyond lab pilots.

## Team contribution statement

This graduation project was completed as a team effort under the Faculty of Computer Science and Engineering, New Mansoura University.
**Ahmed Mohamed Moussa (222101392)**, **Sandy Samy Samir (222101524)**, and **Basma Ahmed Elmorsy (221101164)** jointly contributed to
architecture discussions, implementation, testing, documentation, and demonstration materials. Individual file-level authorship can be
annotated in Git history and in the advisor-approved contribution form required by the faculty.

### 6.1 Closing reflections

The team learned that integration and validation are first-class deliverables, not polish at the end. A working gateway with tests outlives a flashy one-off demo that cannot be reproduced the next semester.

Wearables are one presentation layer; maintainability lives in services, models, and documentation.

Future teams should start measurement notebooks early rather than adding metrics after the final demo week.
