# Verification

Updated on 2026-10-16 for the complete-home edition.

- 23 backend integration tests passed, including home save/read, internal room bounds, balcony furniture, unknown room finishes and the 160-piece limit.
- 26 frontend/domain tests passed, including every starting home layout, legacy draft migration, room-specific placement and finishes, room selection, catalog search, add/delete/undo/redo, 2D plan and expanded workspace.
- Vite production build completed. The lazy Three.js chunk has a large-chunk advisory.
- The preview health endpoint returned HTTP 200 on port 8981. The existing user server on 8980 was left running; its in-memory catalog still has 12 pieces and needs a restart to load the updated backend.
- Browser checks confirmed the furnished seven-zone home, balcony railings, curtains, expanded view, perspective/top cameras and editable SVG plan.
- Changed the bathroom wall and floor finish and successfully saved the full home through the UI.
- Generated a valid 2560 × 2014 pixel PNG preview from the top camera at the inspected viewport.
- No browser error logs were observed.
- docs/studio.jpg and docs/floor-plan.jpg are actual browser captures of this edition.

Native file saving, direct canvas drag gestures, all mobile/touch devices and Docker have not been exhaustively tested. The Windows launcher has not been run end-to-end in a separate user desktop session. Pointer placement/bounds logic is covered by domain tests; the browser checks do not replace device testing.

The 120 m² structural layout is fixed. Room finishes, furnishings, lighting and ceiling height are editable; walls are not a CAD drafting system. Overlapping furnishings are permitted and flagged rather than physically resolved. Dimensions and prices are conceptual.
