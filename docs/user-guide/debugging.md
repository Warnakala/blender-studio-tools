# Debugging

Follow these instructions, if Blender crashes immedietley upon opening a file. This is called  “a crash on load” in liboverride resync code.

1. Found and fixed in main a (potentially) related issue.
2. File is still broken, not sure why, but it currently makes auto resync of overrides completely freak out.
3. When this happen, easy work around is to:
- Disable *TEMPORARILY* auto-resync (preferences-> Experimental -> Debugging -> Override Auto Resync)
- Open the broken file
- Manually resync the overrides one by one (right-click on top-level collections in the outliner, Library Override -> Tropubleshoot -> Resync).
- Purge.
- Save.
- Re-enable auto-resync.
- Re-open the file.

This should solve the problems, or at the very least pin-point more what is the problematic override.
