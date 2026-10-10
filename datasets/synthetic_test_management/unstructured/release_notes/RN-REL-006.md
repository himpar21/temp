---
document_id: RN-REL-006
document_type: release_notes
title: Release Notes — Release 5.2.0
release_id: REL-006
version: 5.2.7
release_date: 2023-08-28
status: Released
---

# Release Notes
## Release 5.2.0 (v5.2.7)

**Release ID:** REL-006
**Release Date:** 2023-08-28
**Status:** Released

---

## 1. Overview

This release delivers stability improvements, security patches, and new feature
capabilities across the enterprise test management platform.

## 2. What's New

- Enhanced **Bluetooth reconnection** stability.
- Improved **firmware update** reliability.
- New **diagnostics dashboard** capability.

## 3. Defects Fixed

- [BUG-0105] UI Failure in Bluetooth Module: ElementNotFoundError: XPath '//button[ *(Component: Bluetooth Module)*

## 4. Known Issues

- Intermittent **UI freeze** under high network load — workaround available.
- **biometric verification** may require a device restart on first use after upgrade.

## 5. Upgrade Notes

- Requires firmware ≥ 5.2.0 on mobile devices.
- Database migration `v5.2.7` will run automatically on first launch.
- Clear app cache after upgrade to avoid stale configuration issues.

## 6. Test Coverage

This release was validated against **1835** test cases across
**12** regression cycles. Pass rate: **99.5%**.

---
*This document is synthetic and created for AI/RAG research purposes only.*
