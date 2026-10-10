---
document_id: RN-REL-003
document_type: release_notes
title: Release Notes — Release 4.3.0
release_id: REL-003
version: 4.3.2
release_date: 2023-04-15
status: Released
---

# Release Notes
## Release 4.3.0 (v4.3.2)

**Release ID:** REL-003
**Release Date:** 2023-04-15
**Status:** Released

---

## 1. Overview

This release delivers stability improvements, security patches, and new feature
capabilities across the enterprise test management platform.

## 2. What's New

- Enhanced **health metric sync** stability.
- Improved **session token management** reliability.
- New **diagnostics dashboard** capability.

## 3. Defects Fixed

- [BUG-0479] Resource Exhaustion in Media Codec: OOMError: heap exhausted at 1260MB *(Component: Media Codec)*
- [BUG-0131] Synchronization Failure in Notification Handler: SyncError: conflict d *(Component: Notification Handler)*
- [BUG-0439] Performance Degradation in Database: PerformanceViolation: p95 latency *(Component: Database)*

## 4. Known Issues

- Intermittent **UI freeze** under high network load — workaround available.
- **NFC tap-to-pay** may require a device restart on first use after upgrade.

## 5. Upgrade Notes

- Requires firmware ≥ 5.1.0 on mobile devices.
- Database migration `v4.3.2` will run automatically on first launch.
- Clear app cache after upgrade to avoid stale configuration issues.

## 6. Test Coverage

This release was validated against **2032** test cases across
**10** regression cycles. Pass rate: **96.6%**.

---
*This document is synthetic and created for AI/RAG research purposes only.*
