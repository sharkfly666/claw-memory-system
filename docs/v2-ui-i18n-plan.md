# OpenClaw Memory Console UI & I18N Upgrade Plan

## Goal
Upgrade the current Memory Console from an engineering prototype into a commercial-grade management UI with bilingual support:
- Simplified Chinese (`zh-CN`)
- English (`en`)

## UI principles
- Clear information hierarchy
- Consistent spacing, typography, and interaction states
- Navigation-first layout instead of stacked debug panels
- Dashboard + data browser + inspector + migration studio + skill console
- Built-in empty/loading/error states
- Responsive layout for desktop-first management scenarios

## Main modules
1. Dashboard
2. Memory Explorer
3. Retrieval Inspector
4. Migration Studio
5. Models
6. Skills
7. Skill Proposals
8. Graph
9. Reports / Evaluation

## Visual direction
- Left sidebar navigation
- Top bar with workspace indicator + locale switcher
- Card-based dashboard
- Table/list + detail split views
- Unified action buttons and status badges
- Light theme first, dark theme later

## I18N approach
- Introduce a small translation dictionary in the webapp layer first
- Keys-based rendering, no hardcoded copy in components
- Locale switch persisted in localStorage
- Default locale: `zh-CN`
- English fallback supported everywhere

## Immediate implementation steps
1. Add locale switcher and translation dictionary to current webapp
2. Refactor current page into sidebar + topbar + content sections
3. Replace raw titles/buttons with translation keys
4. Add reusable UI helpers: badges, section headers, action bars
5. Add empty/loading/error states
6. Later upgrade to stronger frontend architecture if needed
