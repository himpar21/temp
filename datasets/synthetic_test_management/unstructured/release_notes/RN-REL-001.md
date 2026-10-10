---
document_id: RN-REL-001
document_type: release_notes
title: Release Notes — Release 4.1.0
release_id: REL-001
version: 4.1.3
release_date: 2023-01-15
status: Released
---

# Release Notes
## Release 4.1.0 (v4.1.3)

**Release ID:** REL-001
**Release Date:** 2023-01-15
**Status:** Released

---

## 1. Overview

This release delivers stability improvements, security patches, and new feature
capabilities across the enterprise test management platform.

## 2. What's New

- Enhanced **health metric sync** stability.
- Improved **push notification delivery** reliability.
- New **dark mode** capability.

## 3. Defects Fixed

- [BUG-0066] UI Failure in Encryption Module: ElementNotFoundError: XPath '//button *(Component: Encryption Module)*

## 4. Known Issues

- Intermittent **push notification loss** under high network load — workaround available.
- **NFC tap-to-pay** may require a device restart on first use after upgrade.

## 5. Upgrade Notes

- Requires firmware ≥ 5.0.0 on mobile devices.
- Database migration `v4.1.3` will run automatically on first launch.
- Clear app cache after upgrade to avoid stale configuration issues.

## 6. Test Coverage

This release was validated against **1905** test cases across
**11** regression cycles. Pass rate: **97.9%**.

---
*This document is synthetic and created for AI/RAG research purposes only.*
