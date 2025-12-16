# project_rules.md — AI Tools & Commands for Trae

## Purpose
Codified rules for deterministic, error‑resistant AI changes in this project.

---

# 🔧 TOOLS / COMMANDS

## tool.ssot_enforce
**Description:** Enforces Single Source of Truth for all UI-related logic.

**Rules:**
- All membership, visibility, and decision logic must come from one centralized index.
- Cached/prefetched data is always authoritative.
- Do not introduce secondary data sources.

---

## tool.clean_responsibility
**Description:** Ensures UI, service, and index layers have clean, non-overlapping responsibilities.

**Rules:**
- UI = rendering & events only.
- Services = orchestration only.
- Index/model = only authority for canonical state.
- No business logic in UI files.
- No side effects across layers.

---

## tool.error_resistant_flow
**Description:** Forces safe, consistent, self-validating updates.

**Rules:**
- Validate code with ruff & mypy simulation before output.
- No incomplete refactors.
- No missing imports, broken types, or phantom variables.
- No new files unless explicitly required.

---

## tool.change_scope_control
**Description:** Limits changes to avoid drift.

**Rules:**
- Only modify explicitly requested files.
- Only add files if user explicitly asks OR required for consistency.
- Ensure all updates remain DRY.

---

## tool.docs_update
**Description:** Keeps documentation aligned.

**Target File:** `docs/media-index-consistency.md`

**Rules:**
- Update architecture impact, validation checklist, rollback plan when relevant.
- Document any architecture-altering change.

---

## tool.validation_checklist
**Description:** Final internal validation before responding.

**Checklist:**
- [ ] Uses centralized index
- [ ] No duplicated state
- [ ] Clean layer responsibilities
- [ ] Error-resistant logic
- [ ] Ruff-style compliant
- [ ] Mypy-type consistent
- [ ] No implicit file creation
- [ ] All modified files consistent
- [ ] Documentation updated

---

# 🧭 Output Requirements
- Deterministic
- Minimal and correct diffs
- No circular dependencies
- No state duplication
- Predictable & safe behavior

---
