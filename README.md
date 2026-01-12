# Lineup Guide Generator

Create lineup guide PNGs for LED screens based on screen notes CSVs, Google Sheets, or manual entry.

## App builds

There are two versions in `dist/`:
- Windows: `dist/LineupGenerator.exe`
- macOS: `dist/LineupGenerator.app`

When you run the app, it opens a terminal window and launches the UI in your browser. Keep the terminal open while you use the app. When you are finished, close the terminal window to stop the app.

## macOS install (DMG)

1) Download the DMG from GitHub by opening the file and clicking the "Download raw" button. - /dist/LineupGenerator.dmg
2) Open the DMG and drag `LineupGenerator.app` into your Applications folder.
3) Open the app from Applications.
4) If macOS blocks it, go to `System Settings` -> `Privacy & Security`, scroll to the Security section, and click "Open Anyway" for LineupGenerator. Confirm the prompt.
5) After you do this once, macOS should open the app normally going forward.

## How to use the app

1) Launch the app (Windows EXE or macOS app bundle).
2) In the browser UI, pick a data source:
   - Google Sheets: paste the sheet URL (share it as "Anyone with the link").
   - Upload CSV: upload the screen notes CSV.
   - Manual Entry: type values for a single screen.
3) Select a screen and lineup style (RGB, Greyscale Steps, Circle X Grid).
4) Preview the rendering.
5) Export a PNG (single screen or all screens).

Exports are saved in `outputs/`.

Developer notes live in `DEVELOPERS.md`.
