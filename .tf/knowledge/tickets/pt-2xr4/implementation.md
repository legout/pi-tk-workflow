# Implementation: pt-2xr4

## Summary
Added dark mode support to the Ticketflow web UI using Pico CSS's theme mechanism with `data-theme` attribute and `prefers-color-scheme` media query.

## Files Changed

### 1. `tf_cli/static/web-ui.css`
- Added comprehensive theme system with CSS custom properties
- Defined light theme variables in `:root`
- Defined dark theme variables in `[data-theme="dark"]`
- Added automatic dark mode support via `@media (prefers-color-scheme: dark)`
- Updated all color references to use theme-aware CSS variables:
  - `--text-primary` for headings and primary text
  - `--text-secondary` for meta information
  - `--text-muted` for secondary labels
- Brand colors adjusted for dark mode visibility

### 2. `tf_cli/templates/base.html`
- Added theme toggle button (🌓) in header navigation
- Added inline JavaScript for theme management:
  - Cycles through: auto → dark → light → auto
  - Persists preference to localStorage
  - Respects system preference when set to "auto"
  - Applies `data-theme` attribute to `<html>` element
- Added CSS styles for the theme toggle button

## Key Decisions

1. **Three-state toggle** (auto/dark/light) instead of binary:
   - "auto" respects user's system preference via `prefers-color-scheme`
   - Explicit dark/light overrides for user preference
   - Most flexible approach for users

2. **CSS custom properties approach**:
   - Aligned with Pico CSS v2 theming system
   - Easy to extend with additional themes
   - Minimal JavaScript required

3. **Inline script** for the toggle:
   - No external dependency beyond existing Datastar
   - Immediately executed, prevents flash of wrong theme
   - ~50 lines, minimal maintenance burden

## Dark Mode Color Palette

| Element | Light | Dark |
|---------|-------|------|
| Surface (cards) | `#ffffff` | `#1a1a2e` |
| Surface 2 | `#f6f7f9` | `#16213e` |
| Surface 3 (columns) | `#ecf0f1` | `#0f3460` |
| Text Primary | `#2c3e50` | `#e8e8e8` |
| Text Secondary | `#5f6a6a` | `#b8b8b8` |
| Text Muted | `#7f8c8d` | `#888888` |
| Borders | `#e6e8ee` / `#bdc3c7` | `#2d3748` / `#4a5568` |

## Testing

Manual verification steps:
1. Load the web UI in browser
2. Click 🌓 toggle - should cycle through themes
3. Verify board columns/cards remain readable in dark mode
4. Check that priority badges maintain contrast
5. Test with system dark mode enabled (should auto-switch when in "auto" mode)
6. Verify preference persists across page reloads

## Documentation

The implementation follows the pattern documented in Pico CSS v2:
- `data-theme="dark"` forces dark mode
- `data-theme="light"` forces light mode
- No attribute = automatic (prefers-color-scheme)
