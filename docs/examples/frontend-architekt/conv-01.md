#### 👤 User
Ich lade dir ein Bild vom UI von unserem neuen Markdown-Editor hoch, einer reinen HTML/CSS/JavaScript-Anwendung sein soll.

Extrahiere zuerst die Design-System-Parameter (Farben, Abstände, Schriftarten). Wir wollen später mit den Daten arbeiten.

#### 🤖 LexData AI
Basierend auf der visuellen Analyse der Benutzeroberfläche (Microsoft 365 / Fluent Design System) habe ich die Design-Tokens und -Parameter extrahiert. Diese sind so aufbereitet, dass sie direkt als CSS-Variablen in ein modernes CSS-Design-System übernommen werden können.

---

### 1. Farbpalette (Color Palette)

```css
:root {
  /* Surface & Backgrounds */
  --color-bg-app: #f3f4f8;             /* App-Header & Ribbon-Hintergrund */
  --color-bg-canvas: #e9eff7;          /* Arbeitsbereich / Hintergrund hinter dem Dokument */
  --color-bg-surface: #ffffff;         /* Dokumentenblatt, Suchleiste, aktive Modale */
  --color-bg-hover: #e5e8ec;           /* Hover-Status für Ribbon-Buttons */
  --color-bg-active: #d8dde5;          /* Pressed/Active-Status für Buttons */
  
  /* Text & Content */
  --color-text-primary: #1e1e1e;       /* Haupttexte, Menüeinträge, Dokumententext */
  --color-text-secondary: #616161;     /* Gruppenbezeichnungen ("Font", "Paragraph"), Status ("Saved") */
  --color-text-muted: #8a8886;         /* Deaktivierte Icons, Platzhalter */

  /* Brand & Accents (Fluent Blue & Highlights) */
  --color-accent-primary: #0f6cbd;     /* Aktiver Tab-Indikator, primäre Icons */
  --color-accent-hover: #115ea3;
  --color-accent-subtle: #ebf3fc;      /* Selektionshintergrund */
  --color-highlight-yellow: #fff100;   /* Textmarker-Gelb */
  --color-highlight-red: #d13438;      /* Textfarbe-Rot */

  /* Borders & Dividers */
  --color-border-subtle: #e0e0e0;      /* Trennlinie unter dem Menüband */
  --color-border-divider: #d1d5db;     /* Vertikale Trennlinien zwischen den Gruppen */
  --color-border-input: #c7c7c7;       /* Rahmen für Dropdowns & Suchfeld */
  --color-border-focus: #0f6cbd;       /* Fokus-Rahmen */
}
```

---

### 2. Typografie (Typography)

* **Schriftfamilie:**
  ```css
  --font-family-base: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", sans-serif;
  --font-family-mono: "Cascadia Code", "Consolas", "Courier New", monospace; /* Empfohlen für Markdown-Rohansicht */
  ```
* **Schriftgrößen & Schriftschnitte:**
  * **App-Titel / Dateiname:** `13px` – `14px` | Regular (`400`) / Semi-Bold (`600`)
  * **Statusanzeige ("Saved"):** `11px` – `12px` | Regular (`400`), Farbe: `--color-text-secondary`
  * **Hauptmenü-Tabs ("Home", "Insert", ...):** `13px` | Regular (`400`), aktiver Tab: Semi-Bold (`600`)
  * **Ribbon-Buttons & Dropdowns:** `12px` – `13px` | Regular (`400`)
  * **Ribbon-Gruppenbeschriftung ("Clipboard", "Font", ...):** `10px` – `11px` | Regular (`400`), Farbe: `--color-text-secondary`
  * **Dokumententext (Standard Body):** `14px` (11pt äquivalent) | Line-Height: `1.5`

---

### 3. Spacing, Radien & Schatten (Spacing & Layout Tokens)

```css
:root {
  /* Spacing Grid (4px / 8px Basis) */
  --space-2xs: 2px;
  --space-xs: 4px;
  --space-sm: 6px;
  --space-md: 8px;
  --space-lg: 12px;
  --space-xl: 16px;
  --space-2xl: 24px;

  /* Höhen der UI-Zonen */
  --header-height: 44px;               /* Titelleiste inkl. Suche */
  --tabbar-height: 32px;               /* Menü-Reiter */
  --ribbon-height: 88px;               /* Ribbon-Werkzeugleiste */

  /* Border-Radius */
  --radius-xs: 2px;                    /* Tool-Buttons */
  --radius-sm: 4px;                    /* Dropdown-Felder, Suchleiste */
  --radius-md: 6px;                    /* Sub-Container, Dokumentenseiten */
  --radius-window: 10px;               /* App-Fenster oben */

  /* Schatten & Tiefen (Elevations) */
  --shadow-window: 0 8px 24px rgba(0, 0, 0, 0.12);
  --shadow-sheet: 0 2px 10px rgba(0, 0, 0, 0.08); /* Schatten des Editor-Blattes auf Canvas */
  --shadow-dropdown: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

---

### 4. Layout-Strukturkomponenten

1. **Header-Bar (Top):**
   * Linksbündig: Icon, Dokumentenname, Status (`Saved`).
   * Rechtsbündig / Mittig: Suchleiste (Input mit Lupe, abgerundet mit subtiler Outline).
2. **Tab-Bar:**
   * Horizontale Reiterliste (`File`, `Home`, `Insert`, `Draw`, ...).
   * Aktiver Reiter (`Home`) besitzt eine blaue Unterstreichung (`height: 2px; background: var(--color-accent-primary); width: 100%`).
3. **Ribbon-Toolbar:**
   * Horizontales Flex-Container-Layout mit Spaltengruppierungen (`Undo`, `Clipboard`, `Font`, `Paragraph`, `Style`).
   * Vertikale Trennlinien (`border-right: 1px solid var(--color-border-divider); margin: 6px 4px;`).
   * Gruppenbeschriftung zentriert am unteren Rand mit optionalem Launcher-Icon.
4. **Editor Canvas (Dokumentenbereich):**
   * Zentrierter Bereich (`margin: 0 auto; max-width: 816px;` – typisches A4/Letter-Format).
   * Weißes Blatt mit leicht abgerundeten oberen Kanten auf leicht bläulich-grauem Hintergrund (`--color-bg-canvas`).

---

Sobald du bereit bist, können wir die HTML5-Struktur, die SCSS/CSS-Komponenten oder die Markdown-Editor-Funktionalität auf dieser Basis umsetzen.

#### 👤 User
Danke, ich lade dir das Bild nun noch einmal hoch.

Unterteile die Anwendung in verschieden Haupt- und Unterkomponenten, die wir in einem späteren Schritt entwerfen wollen.

#### 🤖 LexData AI
Basierend auf der visuellen Analyse der Benutzeroberfläche ist hier die modulare Strukturierung in **Hauptkomponenten**, **Unterkomponenten** und **wiederverwendbare UI-Atome**. Diese Aufteilung folgt modernen Component-Driven-Design-Prinzipien (Atomic Design), optimal für die spätere Implementierung in HTML5/CSS/JavaScript.

---

```
App-Root (<div class="app-root">)
│
├── 1. App-Header (<header class="app-header">)
├── 2. Tab-Navigation (<nav class="tab-navigation">)
├── 3. Ribbon-Toolbar (<section class="ribbon-toolbar">)
└── 4. Editor-Workspace (<main class="editor-workspace">)
```

---

### 1. Hauptkomponente: `AppHeader` (Titelleiste & Globale Suche)
Verantwortlich für Metadaten, Dokumentenstatus und die universelle Suche.

* **Unterkomponenten:**
  * `AppBrandBadge`: Anwendungs-Icon (z. B. Word-/Dokumenten-Symbol).
  * `DocumentTitleController`:
    * `DocumentTitleInput`: Editierbarer Name des aktuellen Dokuments (*"Power & Simplicity"*).
    * `SaveStatusIndicator`: Status-Badge (*"Saved"* / *"Saving..."* / *"Offline"*).
  * `GlobalSearchBar`: 
    * `SearchInput`: Pill-förmiges Eingabefeld mit integrierter Such-Lupe und Placeholder (*"Search"*).

---

### 2. Hauptkomponente: `TabNavigation` (Menüband-Reiter)
Horizontale Umschaltung der Funktionsbereiche.

* **Unterkomponenten:**
  * `TabList`: Horizontale Reiterleiste mit den Menüpunkten:
    * `TabItem`: Einzelner Reiter (*File*, *Home*, *Insert*, *Draw*, *Design*, *Layout*, *References*, *Mailings*, *Review*, *View*, *Help*).
    * `TabActiveIndicator`: Der visuelle blaue Unterstrich unter dem aktuell ausgewählten Tab (*Home*).

---

### 3. Hauptkomponente: `RibbonToolbar` (Werkzeugleiste)
Der interaktive Befehlsbereich. Jede Gruppe ist als eigenständige Modulbox mit Inhalt, vertikalem Trennstrich (`Divider`) und Gruppenfußzeile aufgebaut.

* **3.1 `UndoGroup` (Rückgängig & Wiederholen):**
  * `ActionButton` für *Undo* und *Redo*.
  * `GroupFooter`: Label *"Undo"*.

* **3.2 `ClipboardGroup` (Zwischenablage):**
  * `LargeSplitButton`: Großer *Paste*-Button mit Icon oben und Dropdown-Pfeil.
  * `ActionStack`: 3-zeiliger Block mit kompakten Text-Buttons:
    * *Cut* (Ausschneiden)
    * *Copy* (Kopieren)
    * *Format Paint* (Format übertragen)
  * `GroupFooter`: Label *"Clipboard"* + `DialogLauncherButton` (kleines Eck-Icon).

* **3.3 `FontGroup` (Zeichen- & Textformatierung):**
  * **Zeile 1 (Auswahlfelder & Schrittweiten):**
    * `FontFamilySelect`: Dropdown für Schriftart (*Calibri (Body)*).
    * `FontSizeSelect`: Dropdown/Input für Schriftgröße (*11*).
    * `ButtonGroup`: *Font Increase* ($A^{\wedge}$), *Font Decrease* ($A_{\vee}$), *Change Case* ($Aa$), *Clear Formatting* ($A\backslash$).
  * **Zeile 2 (Format-Toggles & Farben):**
    * `ToggleGroup`: *Bold* (**B**), *Italic* (*I*), *Underline* (<u>U</u> mit Menüpfeil), *Strikethrough* (~~ab~~), *Subscript* ($x_2$), *Superscript* ($x^2$).
    * `ColorPickerGroup`: *Text Effects* (A-Outline), *Text Highlight Color* (Textmarker mit Gelbbalken), *Font Color* (Textfarbe mit Rotbalken und Dropdown).
  * `GroupFooter`: Label *"Font"* + `DialogLauncherButton`.

* **3.4 `ParagraphGroup` (Absatz- & Listenformatierung):**
  * **Zeile 1 (Listen & Einzüge):**
    * `ListButtonGroup`: *Bullet List*, *Numbered List*, *Multilevel List* (jeweils mit Split-Chevron).
    * `IndentButtonGroup`: *Decrease Indent*, *Increase Indent*, *Sort (A-Z)*, *Paragraph Marks (¶)*.
  * **Zeile 2 (Ausrichtung & Rahmen):**
    * `AlignmentGroup`: *Align Left*, *Center*, *Align Right*, *Justify*.
    * `SpacingAndBordersGroup`: *Line Spacing*, *Fill/Shading (Farbeimer)*, *Border Grid*.
  * `GroupFooter`: Label *"Paragraph"* + `DialogLauncherButton`.

* **3.5 `StylesGalleryGroup` (Formatvorlagen-Katalog):**
  * `StyleCarousel` / `StyleGrid`: Horizontale Vorschaukarten für Stile:
    * `StyleCard`: Einzelne Karte mit typografischer Vorschau und Label (*Normal*, *No Spacing*, *Heading 1*, etc.).
    * `GalleryScrollControls`: Up-/Down-/Expand-Schaltflächen für weitere Styles.
  * `GroupFooter`: Label *"Style"*.

---

### 4. Hauptkomponente: `EditorWorkspace` (Dokumentenbereich & Canvas)
Der scrollbare Arbeitsbereich, in dem das Dokument dargestellt und editiert wird.

* **Unterkomponenten:**
  * `CanvasViewport`: Außenbereich mit bläulich-grauer Arbeitsfläche (`--color-bg-canvas`).
  * `DocumentSheet`: Weißes "A4/Letter"-Blatt mit Schatten und definierten Seitenrändern (Padding).
  * `ContentArea` (Markdown-/Rich-Text-Core):
    * `DocumentHeaderRegion`: Optionaler Kopfzeilenbereich (hier das Firmenlogo *"VanArsdel"* und der Subtitel *"VA Shared Design"*).
    * `DocumentBodyRegion`: Haupttextbereich mit `contenteditable="true"` oder Markdown-Editor-View.

---

### 5. Wiederverwendbare Basis-Komponenten (Atoms / Primitives)

Für einen sauberen Code-Aufbau nutzen alle Komponenten folgende Standard-Elemente:

1. **`IconButton`**: Kompakter Button für Icons mit Hover-, Active- und Disabled-Zuständen.
2. **`SplitButton`**: Geteilter Button (Klick auf Icon = Standardaktion, Klick auf Pfeil = Dropdown-Menü).
3. **`DropdownSelect`**: Stilisiertes Fluent-Dropdown mit Pfeil nach unten.
4. **`ToggleButton`**: Zustandsbehafteter Button (Aktiv/Inaktiv für Bold, Italic etc.).
5. **`Divider`**: Vertikale und horizontale 1px-Trennlinien.
6. **`Tooltip`**: Zugängliche Tooltips (`aria-label` / `title`) mit Tastaturkürzel-Hinweisen (z. B. *"Bold (Ctrl+B)"*).

---

Welche dieser Komponenten (z. B. das **HTML-Grundgerüst der gesamten Shell**, die **Ribbon-Toolbar** oder die **CSS/SCSS-Implementierung**) wollen wir als Nächstes im Detail ausarbeiten?

#### 👤 User
Perfekt, dann erstelle nun das HTML-Gerüst für die Grundanwendung selbst und den oberen Teil des UI.

Lasse aber einen Container für den unteren Teil, da wo sich die Seite und der Eingabebereich befindet.

#### 🤖 LexData AI
Hier ist das semantische und barrierefreie **HTML5-Grundgerüst** für die gesamte App-Shell sowie den vollständigen oberen Bereich (Header, Tab-Navigation und das detaillierte Ribbon-Menüband). 

Am Ende ist der reservierte `<main id="editor-workspace">`-Container für den Dokumenten- und Eingabebereich integriert.

---

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Power & Simplicity - Markdown Editor</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body class="app-body">

  <!-- ==========================================
       APP ROOT SHELL
       ========================================== -->
  <div class="app-root" role="application" aria-label="Markdown Editor">

    <!-- ==========================================
         1. APP HEADER (Titel, Status & Suche)
         ========================================== -->
    <header class="app-header" role="banner">
      <div class="app-header-left">
        <!-- App / Document Brand Icon -->
        <div class="app-brand-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect width="24" height="24" rx="4" fill="#0f6cbd"/>
            <path d="M6 7H9L12 15L15 7H18L13.5 17H10.5L6 7Z" fill="#ffffff"/>
          </svg>
        </div>

        <!-- Editable Title & Save Status -->
        <div class="document-meta">
          <input 
            type="text" 
            class="document-title-input" 
            value="Power & Simplicity" 
            aria-label="Dokumentname" 
            title="Dokumentname bearbeiten"
          />
          <span class="save-status" aria-live="polite">Saved</span>
        </div>
      </div>

      <!-- Global Search Bar -->
      <div class="app-header-center">
        <div class="search-bar" role="search">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="search" 
            class="search-input" 
            placeholder="Search" 
            aria-label="Funktionen oder Text suchen"
          />
        </div>
      </div>

      <div class="app-header-right">
        <!-- Optionaler Platzhalter für Window-Controls / Profil -->
      </div>
    </header>

    <!-- ==========================================
         2. TAB NAVIGATION (Menüband-Reiter)
         ========================================== -->
    <nav class="tab-navigation" role="tablist" aria-label="Hauptmenü">
      <button role="tab" aria-selected="false" class="tab-item">File</button>
      <button role="tab" aria-selected="true" class="tab-item is-active">Home</button>
      <button role="tab" aria-selected="false" class="tab-item">Insert</button>
      <button role="tab" aria-selected="false" class="tab-item">Draw</button>
      <button role="tab" aria-selected="false" class="tab-item">Design</button>
      <button role="tab" aria-selected="false" class="tab-item">Layout</button>
      <button role="tab" aria-selected="false" class="tab-item">References</button>
      <button role="tab" aria-selected="false" class="tab-item">Mailings</button>
      <button role="tab" aria-selected="false" class="tab-item">Review</button>
      <button role="tab" aria-selected="false" class="tab-item">View</button>
      <button role="tab" aria-selected="false" class="tab-item">Help</button>
    </nav>

    <!-- ==========================================
         3. RIBBON TOOLBAR (Werkzeugleiste)
         ========================================== -->
    <section class="ribbon-toolbar" role="toolbar" aria-label="Home Werkzeuge">

      <!-- 3.1 Undo Group -->
      <div class="ribbon-group" role="group" aria-label="Rückgängig">
        <div class="group-content undo-group-content">
          <button type="button" class="btn-icon" title="Undo (Strg+Z)" aria-label="Rückgängig">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v6h6"></path>
              <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>
            </svg>
          </button>
          <button type="button" class="btn-icon is-disabled" disabled title="Redo (Strg+Y)" aria-label="Wiederholen">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 7v6h-6"></path>
              <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path>
            </svg>
          </button>
        </div>
        <div class="group-footer">
          <span class="group-title">Undo</span>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.2 Clipboard Group -->
      <div class="ribbon-group" role="group" aria-label="Zwischenablage">
        <div class="group-content clipboard-group-content">
          <!-- Large Paste Split Button -->
          <div class="split-button-vertical">
            <button type="button" class="btn-paste-main" title="Paste (Strg+V)">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b8860b" stroke-width="1.8">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              <span class="btn-text">Paste</span>
            </button>
            <button type="button" class="btn-paste-arrow" aria-label="Weitere Einfügeoptionen">
              <span class="chevron-down"></span>
            </button>
          </div>

          <!-- Stack Actions (Cut, Copy, Format Paint) -->
          <div class="actions-stack">
            <button type="button" class="btn-compact" title="Cut (Strg+X)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="6" cy="6" r="3"></circle>
                <circle cx="6" cy="18" r="3"></circle>
                <line x1="20" y1="4" x2="8.12" y2="15.88"></line>
                <line x1="14.47" y1="14.48" x2="20" y2="20"></line>
                <line x1="8.12" y1="8.12" x2="12" y2="12"></line>
              </svg>
              <span>Cut</span>
            </button>

            <button type="button" class="btn-compact" title="Copy (Strg+C)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>

            <button type="button" class="btn-compact" title="Format Painter">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                <path d="M19 11V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h1v12a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-5"></path>
                <path d="M14 17l4 4 4-4"></path>
              </svg>
              <span>Format Paint</span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Clipboard</span>
          <button type="button" class="btn-dialog-launcher" title="Zwischenablage-Optionen" aria-label="Zwischenablage Optionen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.3 Font Group -->
      <div class="ribbon-group" role="group" aria-label="Schriftart">
        <div class="group-content font-group-content">
          
          <!-- Font Row 1: Selects & Steppers -->
          <div class="toolbar-row">
            <div class="select-wrapper font-family-wrapper">
              <select class="ribbon-select font-family-select" aria-label="Schriftart wählen">
                <option value="Calibri" selected>Calibri (Body)</option>
                <option value="Arial">Arial</option>
                <option value="Segoe UI">Segoe UI</option>
                <option value="Times New Roman">Times New Roman</option>
              </select>
            </div>

            <div class="select-wrapper font-size-wrapper">
              <select class="ribbon-select font-size-select" aria-label="Schriftgröße wählen">
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11" selected>11</option>
                <option value="12">12</option>
                <option value="14">14</option>
                <option value="16">16</option>
                <option value="18">18</option>
              </select>
            </div>

            <button type="button" class="btn-icon" title="Schriftgröße vergrößern" aria-label="Schrift vergrößern">
              <span class="icon-text">A<sup>▲</sup></span>
            </button>
            <button type="button" class="btn-icon" title="Schriftgröße verkleinern" aria-label="Schrift verkleinern">
              <span class="icon-text">A<sup>▼</sup></span>
            </button>
            
            <button type="button" class="btn-icon" title="Groß-/Kleinschreibung ändern" aria-label="Groß-/Kleinschreibung">
              <span class="icon-text">Aa</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Alle Formatierungen löschen" aria-label="Formatierung löschen">
              <span class="icon-text">A<small>⌫</small></span>
            </button>
          </div>

          <!-- Font Row 2: Styles, Indices & Colors -->
          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle" title="Bold (Strg+B)" aria-pressed="false">
              <strong>B</strong>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Italic (Strg+I)" aria-pressed="false">
              <em>I</em>
            </button>
            <button type="button" class="btn-icon is-toggle has-dropdown" title="Underline (Strg+U)" aria-pressed="false">
              <u>U</u>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Durchgestrichen" aria-pressed="false">
              <s>ab</s>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Tiefgestellt" aria-pressed="false">
              x<sub>2</sub>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Hochgestellt" aria-pressed="false">
              x<sup>2</sup>
            </button>

            <!-- Text Effects & Colors -->
            <button type="button" class="btn-icon has-dropdown" title="Texteffekte und Typografie">
              <span class="icon-effect-a">A</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Textmarkerfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-marker">🖊</span>
                <span class="color-bar color-bar-yellow"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Schriftfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-font-color">A</span>
                <span class="color-bar color-bar-red"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>
          </div>

        </div>

        <div class="group-footer">
          <span class="group-title">Font</span>
          <button type="button" class="btn-dialog-launcher" title="Schriftart-Einstellungen" aria-label="Schriftart Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.4 Paragraph Group -->
      <div class="ribbon-group" role="group" aria-label="Absatz">
        <div class="group-content paragraph-group-content">
          
          <!-- Paragraph Row 1: Lists & Indents -->
          <div class="toolbar-row">
            <button type="button" class="btn-icon has-dropdown" title="Aufzählungszeichen">
              <span>•=</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Nummerierung">
              <span>123</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Liste mit mehreren Ebenen">
              <span>𝌆</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Einzug verkleinern">
              <span>⇤</span>
            </button>
            <button type="button" class="btn-icon" title="Einzug vergrößern">
              <span>⇥</span>
            </button>
            <button type="button" class="btn-icon" title="Sortieren">
              <span>A↓Z</span>
            </button>
            <button type="button" class="btn-icon" title="Alle anzeigen (¶)">
              <span>¶</span>
            </button>
          </div>

          <!-- Paragraph Row 2: Alignment, Spacing, Borders -->
          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle is-active" title="Linksbündig" aria-pressed="true">
              <span>≡</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Zentriert" aria-pressed="false">
              <span>≍</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Rechtsbündig" aria-pressed="false">
              <span>≣</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Blocksatz" aria-pressed="false">
              <span>☷</span>
            </button>

            <button type="button" class="btn-icon has-dropdown" title="Zeilen- und Absatzabstand">
              <span>↕</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Schattierung">
              <span>🪣</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Rahmen">
              <span>⊞</span>
              <span class="chevron-down-mini"></span>
            </button>
          </div>

        </div>

        <div class="group-footer">
          <span class="group-title">Paragraph</span>
          <button type="button" class="btn-dialog-launcher" title="Absatz-Einstellungen" aria-label="Absatz Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.5 Styles Group -->
      <div class="ribbon-group styles-group" role="group" aria-label="Formatvorlagen">
        <div class="group-content styles-group-content">
          
          <!-- Quick Styles Gallery -->
          <div class="styles-gallery" role="listbox" aria-label="Formatvorlagen-Katalog">
            <button type="button" class="style-card is-active" role="option" aria-selected="true" title="Standard">
              <span class="style-preview font-normal">AaBbCc</span>
              <span class="style-name">Normal</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Kein Leerraum">
              <span class="style-preview font-nospacing">AaBbCc</span>
              <span class="style-name">No Spacing</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Überschrift 1">
              <span class="style-preview font-heading1">AaB</span>
              <span class="style-name">Heading 1</span>
            </button>
          </div>

          <!-- Gallery Scroll / Dropdown Controls -->
          <div class="gallery-controls">
            <button type="button" class="btn-gallery-nav" title="Nach oben scrollen" aria-label="Nach oben">▲</button>
            <button type="button" class="btn-gallery-nav" title="Nach unten scrollen" aria-label="Nach unten">▼</button>
            <button type="button" class="btn-gallery-nav" title="Weitere Formatvorlagen" aria-label="Mehr">▾</button>
          </div>

        </div>

        <div class="group-footer">
          <span class="group-title">Style</span>
        </div>
      </div>

    </section>

    <!-- ==========================================
         4. EDITOR WORKSPACE (Dokumentenbereich)
         ========================================== -->
    <!-- Dieser Container dient als Montagepunkt für das Dokumentenblatt & den Editor -->
    <main id="editor-workspace" class="editor-workspace" role="main">
      <!-- Der Inhalt (Dokumentenseite, Markdown-/Wysiwyg-View) wird hier integriert -->
    </main>

  </div>

</body>
</html>
```

---

### Was in dieser Struktur enthalten ist:
1. **App Header (`.app-header`)**:
   * Brand-Icon links.
   * Editierbares Eingabefeld für den Dateinamen (`Power & Simplicity`) + Live-Status (`Saved`).
   * Zentrierte Suchleiste mit Such-Icon (`Search`).
2. **Tab-Bar (`.tab-navigation`)**:
   * Alle Menüpunkte (`File`, `Home`, `Insert`, ...) mit ARIA-Tab-Rollen und dem aktiven Status auf `Home`.
3. **Ribbon-Leiste (`.ribbon-toolbar`)**:
   * Vollständig strukturiert in die Gruppen **Undo**, **Clipboard**, **Font**, **Paragraph** und **Styles**.
   * Dialog-Launcher-Buttons (`.btn-dialog-launcher`) am unteren rechten Rand jeder Gruppe.
   * Dropdowns, Farbmarkierungs-Buttons mit Farbbalken und Toggle-Buttons für Formatierungen.
4. **Workspace Placeholder (`#editor-workspace`)**:
   * Ein semantisches `<main>`-Element, das exakt den scrollbaren Canvas-Bereich für das Blatt abbildet.

#### 👤 User
Super! Erstelle nun für die eben erstellte HTML-Grundanwendung und den oberen Teil des UI das Basis- und Komponenten-CSS.

#### 🤖 LexData AI
Hier ist das vollständige, modulare **Basis- und Komponenten-CSS** (`styles.css`), abgestimmt auf das zuvor erstellte HTML5-Gerüst und das Fluent-Design der visuellen Vorlage.

---

```css
/* ==========================================================================
   1. CSS RESET & BASIS-TOKENS
   ========================================================================== */

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  /* Surface & Backgrounds */
  --color-bg-app: #f3f5f8;
  --color-bg-canvas: #dfe7f2;
  --color-bg-surface: #ffffff;
  --color-bg-hover: #e5e8ee;
  --color-bg-active: #d6dbe4;
  --color-bg-selected: #e0e6f0;

  /* Text & Content */
  --color-text-primary: #1b1b1b;
  --color-text-secondary: #5c5c5c;
  --color-text-muted: #8c8c8c;

  /* Brand & Accents (Fluent Blue & Highlights) */
  --color-accent-primary: #0f6cbd;
  --color-accent-hover: #115ea3;
  --color-accent-subtle: #ebf3fc;
  --color-highlight-yellow: #fff100;
  --color-highlight-red: #c42b1c;

  /* Borders & Dividers */
  --color-border-subtle: #e5e7eb;
  --color-border-divider: #d2d6dc;
  --color-border-input: #c8c8c8;
  --color-border-focus: #0f6cbd;

  /* Typography */
  --font-family-base: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", sans-serif;
  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-base: 13px;
  --font-size-md: 14px;

  /* Spacing */
  --space-2xs: 2px;
  --space-xs: 4px;
  --space-sm: 6px;
  --space-md: 8px;
  --space-lg: 12px;
  --space-xl: 16px;

  /* Radii & Elevations */
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-pill: 20px;
  --radius-window: 10px;
  
  --shadow-window: 0 10px 30px rgba(0, 0, 0, 0.12);
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-sheet: 0 4px 16px rgba(0, 0, 0, 0.1);
}

body.app-body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background-color: var(--color-bg-canvas);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 16px;
  -webkit-font-smoothing: antialiased;
}

/* ==========================================================================
   2. APP ROOT SHELL
   ========================================================================== */

.app-root {
  width: 100%;
  max-width: 1400px;
  min-height: 94vh;
  background-color: var(--color-bg-app);
  border-radius: var(--radius-window);
  box-shadow: var(--shadow-window);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* ==========================================================================
   3. APP HEADER (Titel, Status & Suche)
   ========================================================================== */

.app-header {
  height: 44px;
  padding: 0 var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--color-bg-app);
}

.app-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
}

.app-brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.document-title-input {
  border: 1px solid transparent;
  background: transparent;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  outline: none;
  font-family: inherit;
  transition: all 0.15s ease;
}

.document-title-input:hover {
  background-color: var(--color-bg-hover);
}

.document-title-input:focus {
  background-color: var(--color-bg-surface);
  border-color: var(--color-border-focus);
}

.save-status {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  user-select: none;
}

/* Globale Suchleiste */
.app-header-center {
  flex: 1.5;
  display: flex;
  justify-content: center;
}

.search-bar {
  width: 100%;
  max-width: 480px;
  height: 30px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  padding: 0 var(--space-md);
  gap: var(--space-xs);
  transition: border-color 0.15s ease;
}

.search-bar:focus-within {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 1px var(--color-border-focus);
}

.search-icon {
  color: var(--color-text-secondary);
}

.search-input {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  font-size: var(--font-size-sm);
  font-family: inherit;
  color: var(--color-text-primary);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.app-header-right {
  flex: 1;
}

/* ==========================================================================
   4. TAB NAVIGATION (Menüband-Reiter)
   ========================================================================== */

.tab-navigation {
  display: flex;
  align-items: center;
  height: 32px;
  padding: 0 var(--space-lg);
  background-color: var(--color-bg-app);
  gap: 2px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.tab-item {
  position: relative;
  background: transparent;
  border: none;
  padding: 6px 10px;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-family: inherit;
  cursor: pointer;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background-color 0.1s ease;
}

.tab-item:hover {
  background-color: var(--color-bg-hover);
}

.tab-item.is-active {
  font-weight: 600;
}

/* Der charakteristische blaue Unterstrich für den aktiven Reiter */
.tab-item.is-active::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 8px;
  right: 8px;
  height: 2.5px;
  background-color: var(--color-accent-primary);
  border-radius: 2px 2px 0 0;
}

/* ==========================================================================
   5. RIBBON TOOLBAR (Werkzeugleiste)
   ========================================================================== */

.ribbon-toolbar {
  height: 92px;
  background-color: var(--color-bg-app);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: stretch;
  padding: 4px var(--space-lg);
  overflow-x: auto;
}

/* Gruppenaufteilung */
.ribbon-group {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2px 6px 4px 6px;
  flex-shrink: 0;
}

.group-content {
  display: flex;
  align-items: center;
  height: 60px;
  gap: 4px;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 2px;
}

.group-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 16px;
}

.group-title {
  font-size: 10px;
  color: var(--color-text-secondary);
  user-select: none;
}

/* Kleines Launcher-Icon rechts unten */
.btn-dialog-launcher {
  position: absolute;
  right: 0;
  bottom: 1px;
  width: 12px;
  height: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0.65;
}

.btn-dialog-launcher::after {
  content: "↗";
  font-size: 9px;
  color: var(--color-text-secondary);
}

.btn-dialog-launcher:hover {
  opacity: 1;
}

/* Vertikaler Trennstrich zwischen den Gruppen */
.ribbon-divider {
  width: 1px;
  background-color: var(--color-border-divider);
  margin: 6px 4px 10px 4px;
}

/* ==========================================================================
   6. RIBBON CONTROLS & BUTTON ATOMS
   ========================================================================== */

/* Standard Icon-Button */
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  padding: 0 4px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-xs);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  cursor: pointer;
  user-select: none;
  transition: all 0.1s ease;
}

.btn-icon:hover:not(:disabled) {
  background-color: var(--color-bg-hover);
}

.btn-icon:active:not(:disabled) {
  background-color: var(--color-bg-active);
}

.btn-icon.is-active,
.btn-icon[aria-pressed="true"] {
  background-color: var(--color-bg-selected);
  border-color: var(--color-border-input);
}

.btn-icon:disabled,
.btn-icon.is-disabled {
  opacity: 0.35;
  cursor: default;
}

/* Mini Chevron Icon */
.chevron-down-mini {
  display: inline-block;
  width: 0;
  height: 0;
  margin-left: 3px;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
  border-top: 3.5px solid var(--color-text-secondary);
}

/* Dropdown Selects */
.select-wrapper {
  position: relative;
}

.ribbon-select {
  appearance: none;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-xs);
  height: 24px;
  padding: 0 18px 0 6px;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-family: inherit;
  outline: none;
  cursor: pointer;
}

.select-wrapper::after {
  content: "";
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
  border-top: 3.5px solid var(--color-text-secondary);
  pointer-events: none;
}

.font-family-select {
  width: 120px;
}

.font-size-select {
  width: 48px;
}

/* ==========================================================================
   7. SPEZIELLE GRUPPEN-LAYOUTS
   ========================================================================== */

/* 7.1 Undo Group */
.undo-group-content {
  align-items: flex-start;
  padding-top: 2px;
}

/* 7.2 Clipboard Group */
.clipboard-group-content {
  gap: 6px;
}

.split-button-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: var(--radius-xs);
}

.btn-paste-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  cursor: pointer;
  font-family: inherit;
}

.btn-paste-main .btn-text {
  font-size: 11px;
  color: var(--color-text-primary);
  margin-top: 1px;
}

.btn-paste-arrow {
  background: transparent;
  border: none;
  width: 100%;
  height: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.split-button-vertical:hover {
  background-color: var(--color-bg-hover);
}

.actions-stack {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.btn-compact {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  padding: 2px 6px;
  font-size: 11px;
  color: var(--color-text-primary);
  border-radius: var(--radius-xs);
  cursor: pointer;
  font-family: inherit;
  height: 18px;
}

.btn-compact:hover {
  background-color: var(--color-bg-hover);
}

/* 7.3 Font & Paragraph 2-Reihen Layout */
.font-group-content,
.paragraph-group-content {
  flex-direction: column;
  justify-content: center;
  gap: 3px;
}

/* Color Picker Button mit Farbbalken */
.btn-color-picker {
  display: inline-flex;
  align-items: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-xs);
  padding: 1px 3px;
  cursor: pointer;
  height: 26px;
}

.btn-color-picker:hover {
  background-color: var(--color-bg-hover);
}

.color-picker-icon-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.icon-font-color {
  font-weight: 700;
  font-size: 13px;
  line-height: 1;
}

.color-bar {
  width: 13px;
  height: 3px;
  margin-top: 1px;
  border-radius: 0.5px;
}

.color-bar-yellow {
  background-color: var(--color-highlight-yellow);
}

.color-bar-red {
  background-color: var(--color-highlight-red);
}

/* 7.4 Styles Quick Gallery */
.styles-group-content {
  gap: 4px;
}

.styles-gallery {
  display: flex;
  gap: 4px;
  height: 54px;
}

.style-card {
  width: 68px;
  height: 54px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xs);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 6px 2px 4px 2px;
  cursor: pointer;
  transition: all 0.1s ease;
}

.style-card:hover {
  border-color: var(--color-border-input);
  background-color: #fafafa;
}

.style-card.is-active {
  border-color: var(--color-accent-primary);
  background-color: var(--color-accent-subtle);
}

.style-preview {
  font-size: 14px;
  line-height: 1.2;
}

.font-normal {
  font-family: inherit;
}

.font-nospacing {
  letter-spacing: -0.8px;
}

.font-heading1 {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-accent-primary);
}

.style-name {
  font-size: 9.5px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.gallery-controls {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 54px;
}

.btn-gallery-nav {
  width: 16px;
  height: 17px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border-subtle);
  font-size: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 1px;
}

.btn-gallery-nav:hover {
  background-color: var(--color-bg-hover);
}

/* ==========================================================================
   8. EDITOR WORKSPACE (Dokumentenbereich / Montagepunkt)
   ========================================================================== */

.editor-workspace {
  flex: 1;
  background-color: var(--color-bg-canvas);
  overflow-y: auto;
  padding: 24px var(--space-xl);
  display: flex;
  justify-content: center;
}
```

---

### Was dieses CSS leistet:
1. **Design Tokens & Fluent-Stil:** Saubere CSS-Variablen für Farben, Hover-Zustände, Radien und Schattierungen.
2. **Kompaktes Ribbon-Raster:** Exakte Nachbildung der 2-zeiligen Anordnung in der **Font-** und **Paragraph-Gruppe** inklusive Trennstrichen und Gruppenbezeichnungen.
3. **Detailtreue UI-Elemente:** 
   * Der blaue **Active Tab Indicator**.
   * Die **Styles-Gallery** Vorschaukarten (*Normal*, *No Spacing*, *Heading 1*).
   * Die **Farbbalken-Indikatoren** für Textmarker und Schriftfarbe.
4. **Vorbereitet für den Content-Bereich:** `.editor-workspace` ist bereits als scrollbare, zentrierte Arbeitsfläche ausgelegt, in die als Nächstes das Blatt und der Eingabebereich eingefügt werden können.

#### 👤 User
Danke, erstelle nun basierend auf dem HTML-Teil den unteren Bereich für das UI.

#### 🤖 LexData AI
Hier ist die Implementierung des **unteren Bereichs der Benutzeroberfläche** (das zentrierte Dokumentenblatt, der Header-Bereich des Dokuments mit Firmenbranding, der editierbare Inhaltsbereich und eine optionale Fluent-Statusleiste am unteren App-Rand).

---

### 1. HTML-Struktur für den unteren Bereich

Ersetze den Platzhalter `<main id="editor-workspace">...</main>` in deiner `index.html` und füge am Ende der `.app-root` die Statusleiste ein:

```html
    <!-- ==========================================
         4. EDITOR WORKSPACE (Dokumentenbereich & Canvas)
         ========================================== -->
    <main id="editor-workspace" class="editor-workspace" role="main">
      
      <!-- Dokumenten-Blatt (A4 / Letter Format mit Elevation) -->
      <article class="document-sheet" role="document" aria-label="Dokumentinhalt">
        
        <!-- Dokument-Kopfzeile (Branding & Metadaten) -->
        <header class="doc-header">
          <div class="doc-brand">
            <div class="doc-logo-mark">
              <!-- Geometrisches Logo-Icon (VanArsdel) -->
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M4 4L12 20L20 4H15L12 11L9 4H4Z" fill="#1b1b1b"/>
              </svg>
            </div>
            <div class="doc-brand-text">
              <span class="brand-title">VanArsdel</span>
              <span class="brand-subtitle">VA Shared Design</span>
            </div>
          </div>

          <div class="doc-meta-date">
            <time datetime="2026-08-29">August 29, 2026</time>
          </div>
        </header>

        <hr class="doc-divider">

        <!-- Haupttitel des Dokuments -->
        <h1 class="doc-main-heading" contenteditable="true" spellcheck="false" data-placeholder="Dokumenttitel eingeben...">
          Power &amp; Simplicity
        </h1>

        <p class="doc-lead" contenteditable="true" spellcheck="false">
          A minimalist, distraction-free markdown and rich-text editing experience designed for modern web applications.
        </p>

        <!-- Editierbarer Inhaltsbereich (Markdown / Rich-Text) -->
        <div 
          id="editor-content" 
          class="doc-content-area" 
          contenteditable="true" 
          spellcheck="true"
          aria-multiline="true"
          role="textbox"
          data-placeholder="Beginnen Sie mit der Eingabe oder tippen Sie '/' für Befehle...">
          
          <h2>1. Introduction</h2>
          <p>
            The interface combines the familiar aesthetics of modern productivity suites with the velocity and lightweight nature of plain text Markdown formatting.
          </p>

          <blockquote>
            "Simplicity is prerequisite for reliability." — Edsger W. Dijkstra
          </blockquote>

          <h2>2. Key Features</h2>
          <ul>
            <li><strong>Full Typography Control:</strong> Real-time font scaling, weights, and heading hierarchisation.</li>
            <li><strong>Fluid Grid Canvas:</strong> Perfectly centered A4 sheet with realistic paper elevation.</li>
            <li><strong>Zero-Friction Toolbar:</strong> Fluent Design Ribbon with instant accessibility cues.</li>
          </ul>

        </div>

      </article>

    </main>

    <!-- ==========================================
         5. APP STATUS BAR (Fußzeile)
         ========================================== -->
    <footer class="app-statusbar" role="contentinfo">
      <div class="statusbar-left">
        <span class="status-item">Page 1 of 1</span>
        <span class="status-divider"></span>
        <span class="status-item" id="word-count">142 words</span>
        <span class="status-divider"></span>
        <span class="status-item">English (US)</span>
      </div>

      <div class="statusbar-right">
        <button type="button" class="btn-status-view is-active" title="Drucklayout">📄</button>
        <button type="button" class="btn-status-view" title="Weblayout">🌐</button>
        <button type="button" class="btn-status-view" title="Fokusmodus">🔲</button>
        
        <span class="status-divider"></span>
        
        <div class="zoom-controller">
          <button type="button" class="btn-zoom-step" aria-label="Verkleinern">−</button>
          <input type="range" class="zoom-slider" min="50" max="200" value="100" aria-label="Zoomstufe">
          <button type="button" class="btn-zoom-step" aria-label="Vergrößern">+</button>
          <span class="zoom-value">100%</span>
        </div>
      </div>
    </footer>
```

---

### 2. Ergänzendes CSS (`styles.css`)

Füge diesen Block am Ende deiner bestehenden `styles.css` an:

```css
/* ==========================================================================
   9. DOKUMENTENBLATT & INHALTSBEREICH (Canvas & Sheet)
   ========================================================================== */

/* Arbeitsfläche / Canvas */
.editor-workspace {
  flex: 1;
  background-color: var(--color-bg-canvas);
  overflow-y: auto;
  padding: 32px 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* Das A4/Letter Dokumentenblatt */
.document-sheet {
  width: 100%;
  max-width: 816px; /* Standard A4 / Letter Breite bei 96 DPI */
  min-height: 1056px;
  background-color: var(--color-bg-surface);
  border-radius: var(--radius-xs);
  box-shadow: var(--shadow-sheet);
  padding: 64px 72px; /* Großzügige Word-Seitenränder */
  outline: none;
  display: flex;
  flex-direction: column;
}

/* Dokument-Kopfzeile (Header-Region) */
.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.doc-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: var(--color-text-primary);
  line-height: 1.1;
}

.brand-subtitle {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.doc-meta-date {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.doc-divider {
  border: none;
  height: 1px;
  background-color: var(--color-border-subtle);
  margin-bottom: 32px;
}

/* Typografie im Dokumentenblatt */
.doc-main-heading {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.25;
  margin-bottom: 12px;
  outline: none;
  border-radius: var(--radius-xs);
}

.doc-lead {
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin-bottom: 28px;
  outline: none;
}

.doc-content-area {
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-primary);
  outline: none;
  flex: 1;
}

.doc-content-area h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-accent-primary);
  margin-top: 24px;
  margin-bottom: 10px;
}

.doc-content-area p {
  margin-bottom: 14px;
}

.doc-content-area blockquote {
  border-left: 3px solid var(--color-accent-primary);
  padding-left: 14px;
  margin: 18px 0;
  color: var(--color-text-secondary);
  font-style: italic;
}

.doc-content-area ul {
  padding-left: 24px;
  margin-bottom: 14px;
}

.doc-content-area li {
  margin-bottom: 6px;
}

/* Editier-Fokus-Effekte */
[contenteditable="true"]:focus-visible {
  outline: 1px dashed var(--color-border-input);
  outline-offset: 2px;
}

/* Placeholder-Unterstützung für leere Edit-Zonen */
[contenteditable="true"]:empty::before {
  content: attr(data-placeholder);
  color: var(--color-text-muted);
  pointer-events: none;
}

/* ==========================================================================
   10. STATUS BAR (Fußzeile)
   ========================================================================== */

.app-statusbar {
  height: 26px;
  background-color: var(--color-bg-app);
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-md);
  font-size: 11px;
  color: var(--color-text-secondary);
  user-select: none;
}

.statusbar-left,
.statusbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-divider {
  width: 1px;
  height: 12px;
  background-color: var(--color-border-divider);
}

.btn-status-view {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-xs);
  font-size: 11px;
  opacity: 0.7;
}

.btn-status-view:hover {
  background-color: var(--color-bg-hover);
  opacity: 1;
}

.btn-status-view.is-active {
  background-color: var(--color-bg-active);
  opacity: 1;
}

/* Zoom Controls */
.zoom-controller {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-zoom-step {
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: bold;
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 0 4px;
}

.btn-zoom-step:hover {
  color: var(--color-text-primary);
}

.zoom-slider {
  width: 80px;
  height: 3px;
  accent-color: var(--color-accent-primary);
  cursor: pointer;
}

.zoom-value {
  width: 32px;
  text-align: right;
  font-size: 11px;
}
```

---

### Highlights dieser Ergänzung:
1. **Realistische Blatt-Projektion (`.document-sheet`):** Exakte A4/Letter-Proportionen (816px Breite), Papier-Elevation (`box-shadow`) und zentriertes Verhalten im Canvas.
2. **Branding & Header (`.doc-header`):** Enthält das aus der Vorlage bekannte *VanArsdel*-Branding sowie Metadaten (Datum) und Trennlinie.
3. **Direkt editierbar (`contenteditable="true"`):** Überschrift, Lead-Text und Hauptbereich können sofort im Browser angeklickt und bearbeitet werden.
4. **Desktop-Statusleiste (`.app-statusbar`):** Word-Count-Anzeige, Dokumentseiten-Zähler, View-Modi und Zoom-Slider runden die Office-Applikationserfahrung ab.

#### 👤 User
Gibt es kostenlose dienste wo ich die html und css hosten könnte?

#### 🤖 LexData AI
Ja, es gibt hervorragende kostenlose Dienste, die sich perfekt für reine HTML-, CSS- und JavaScript-Projekte eignen. Sie bieten alle kostenlose SSL-Zertifikate (HTTPS) und globale CDNs für extrem schnelle Ladezeiten.

Hier sind die besten Optionen, unterteilt nach Einstiegslevel:

---

### 1. Die einfachsten Optionen (Keine Git-Kenntnisse erforderlich)

* **[Netlify Drop](https://app.netlify.com/drop)**
  * **Ablauf:** Du ziehst deinen Projektordner (mit `index.html` und `styles.css`) einfach per **Drag & Drop** in das Browserfenster.
  * **Vorteile:** Sofort in 5 Sekunden online, kostenlose Subdomain (`dein-projekt.netlify.app`), später mit Git verknüpfbar.
* **[Vercel](https://vercel.com/)**
  * Ähnlich wie Netlify, extrem schnell und modern. Unterstützt Drag & Drop über das Dashboard oder automatische Deployments via GitHub/GitLab.

---

### 2. Die Standard-Entwickler-Optionen (Via Git/Repository)

* **[GitHub Pages](https://pages.github.com/)**
  * **Ablauf:** Erstelle ein GitHub-Repository, lade deine Dateien hoch und aktiviere in den Repository-Einstellungen unter *Pages* den Branch `main`.
  * **Vorteile:** Direkte Versionskontrolle, Domain nach dem Muster `benutzername.github.io/projektname`, unbegrenzte Laufzeit.
* **[Cloudflare Pages](https://pages.cloudflare.com/)**
  * **Ablauf:** Verknüpfung mit deinem GitHub-/GitLab-Konto.
  * **Vorteile:** Extrem großzügiges Free-Tier, unbegrenzte Bandbreite, weltweites Hochleistungs-CDN.

---

### 3. Für schnelles Testen & Teilen über das Terminal (CLI)

* **[Surge.sh](https://surge.sh/)**
  * **Ablauf:** Im Terminal im Projektordner einfach den Befehl `npx surge` ausführen.
  * **Vorteile:** Kein Web-Dashboard nötig, URL wird direkt im Terminal ausgegeben.

---

### 4. Interaktive Online-Playgrounds (Code direkt im Browser teilen)

Falls du den Code Kollegen oder Testern direkt als interaktiven Editor zeigen möchtest, ohne Dateien hochzuladen:
* **[CodePen](https://codepen.io/)** (HTML & CSS getrennt einfügen)
* **[StackBlitz](https://stackblitz.com/)** oder **[CodeSandbox](https://codesandbox.io/)** (Komplette Online-IDE)

---

### 💡 Empfehlung für den Start:
Wenn du es **sofort und ohne Installation** ausprobieren möchtest: Nutze **[Netlify Drop](https://app.netlify.com/drop)**. Ziehe einfach deinen Ordner mit der `index.html` und `styles.css` hinein, und deine Office-UI ist in wenigen Sekunden unter einer echten Webadresse erreichbar.

#### 👤 User
Kannst du die html datei und css datei in eine datei packen und sie unter index.html speichern?

#### 🤖 LexData AI
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Power & Simplicity - Markdown Editor</title>
  <style>
    /* ==========================================================================
       1. CSS RESET & BASIS-TOKENS
       ========================================================================== */
    *,
    *::before,
    *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    :root {
      /* Surface & Backgrounds */
      --color-bg-app: #f3f5f8;
      --color-bg-canvas: #dfe7f2;
      --color-bg-surface: #ffffff;
      --color-bg-hover: #e5e8ee;
      --color-bg-active: #d6dbe4;
      --color-bg-selected: #e0e6f0;

      /* Text & Content */
      --color-text-primary: #1b1b1b;
      --color-text-secondary: #5c5c5c;
      --color-text-muted: #8c8c8c;

      /* Brand & Accents (Fluent Blue & Highlights) */
      --color-accent-primary: #0f6cbd;
      --color-accent-hover: #115ea3;
      --color-accent-subtle: #ebf3fc;
      --color-highlight-yellow: #fff100;
      --color-highlight-red: #c42b1c;

      /* Borders & Dividers */
      --color-border-subtle: #e5e7eb;
      --color-border-divider: #d2d6dc;
      --color-border-input: #c8c8c8;
      --color-border-focus: #0f6cbd;

      /* Typography */
      --font-family-base: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", sans-serif;
      --font-size-xs: 11px;
      --font-size-sm: 12px;
      --font-size-base: 13px;
      --font-size-md: 14px;

      /* Spacing */
      --space-2xs: 2px;
      --space-xs: 4px;
      --space-sm: 6px;
      --space-md: 8px;
      --space-lg: 12px;
      --space-xl: 16px;

      /* Radii & Elevations */
      --radius-xs: 2px;
      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-pill: 20px;
      --radius-window: 10px;
      
      --shadow-window: 0 10px 30px rgba(0, 0, 0, 0.12);
      --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.08);
      --shadow-sheet: 0 4px 16px rgba(0, 0, 0, 0.1);
    }

    body.app-body {
      font-family: var(--font-family-base);
      font-size: var(--font-size-base);
      color: var(--color-text-primary);
      background-color: var(--color-bg-canvas);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 16px;
      -webkit-font-smoothing: antialiased;
    }

    /* ==========================================================================
       2. APP ROOT SHELL
       ========================================================================== */
    .app-root {
      width: 100%;
      max-width: 1400px;
      min-height: 94vh;
      background-color: var(--color-bg-app);
      border-radius: var(--radius-window);
      box-shadow: var(--shadow-window);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid rgba(0, 0, 0, 0.06);
    }

    /* ==========================================================================
       3. APP HEADER (Titel, Status & Suche)
       ========================================================================== */
    .app-header {
      height: 44px;
      padding: 0 var(--space-lg);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: var(--color-bg-app);
    }

    .app-header-left {
      display: flex;
      align-items: center;
      gap: var(--space-md);
      flex: 1;
    }

    .app-brand-icon {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .document-meta {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .document-title-input {
      border: 1px solid transparent;
      background: transparent;
      font-size: var(--font-size-base);
      font-weight: 600;
      color: var(--color-text-primary);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      outline: none;
      font-family: inherit;
      transition: all 0.15s ease;
    }

    .document-title-input:hover {
      background-color: var(--color-bg-hover);
    }

    .document-title-input:focus {
      background-color: var(--color-bg-surface);
      border-color: var(--color-border-focus);
    }

    .save-status {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
      user-select: none;
    }

    .app-header-center {
      flex: 1.5;
      display: flex;
      justify-content: center;
    }

    .search-bar {
      width: 100%;
      max-width: 480px;
      height: 30px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-input);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      padding: 0 var(--space-md);
      gap: var(--space-xs);
      transition: border-color 0.15s ease;
    }

    .search-bar:focus-within {
      border-color: var(--color-border-focus);
      box-shadow: 0 0 0 1px var(--color-border-focus);
    }

    .search-icon {
      color: var(--color-text-secondary);
    }

    .search-input {
      width: 100%;
      border: none;
      background: transparent;
      outline: none;
      font-size: var(--font-size-sm);
      font-family: inherit;
      color: var(--color-text-primary);
    }

    .search-input::placeholder {
      color: var(--color-text-muted);
    }

    .app-header-right {
      flex: 1;
    }

    /* ==========================================================================
       4. TAB NAVIGATION (Menüband-Reiter)
       ========================================================================== */
    .tab-navigation {
      display: flex;
      align-items: center;
      height: 32px;
      padding: 0 var(--space-lg);
      background-color: var(--color-bg-app);
      gap: 2px;
      border-bottom: 1px solid var(--color-border-subtle);
    }

    .tab-item {
      position: relative;
      background: transparent;
      border: none;
      padding: 6px 10px;
      font-size: var(--font-size-base);
      color: var(--color-text-primary);
      font-family: inherit;
      cursor: pointer;
      border-radius: var(--radius-sm) var(--radius-sm) 0 0;
      transition: background-color 0.1s ease;
    }

    .tab-item:hover {
      background-color: var(--color-bg-hover);
    }

    .tab-item.is-active {
      font-weight: 600;
    }

    .tab-item.is-active::after {
      content: "";
      position: absolute;
      bottom: -1px;
      left: 8px;
      right: 8px;
      height: 2.5px;
      background-color: var(--color-accent-primary);
      border-radius: 2px 2px 0 0;
    }

    /* ==========================================================================
       5. RIBBON TOOLBAR (Werkzeugleiste)
       ========================================================================== */
    .ribbon-toolbar {
      height: 92px;
      background-color: var(--color-bg-app);
      border-bottom: 1px solid var(--color-border-subtle);
      display: flex;
      align-items: stretch;
      padding: 4px var(--space-lg);
      overflow-x: auto;
    }

    .ribbon-group {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 2px 6px 4px 6px;
      flex-shrink: 0;
    }

    .group-content {
      display: flex;
      align-items: center;
      height: 60px;
      gap: 4px;
    }

    .toolbar-row {
      display: flex;
      align-items: center;
      gap: 2px;
    }

    .group-footer {
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      height: 16px;
    }

    .group-title {
      font-size: 10px;
      color: var(--color-text-secondary);
      user-select: none;
    }

    .btn-dialog-launcher {
      position: absolute;
      right: 0;
      bottom: 1px;
      width: 12px;
      height: 12px;
      border: none;
      background: transparent;
      cursor: pointer;
      opacity: 0.65;
    }

    .btn-dialog-launcher::after {
      content: "↗";
      font-size: 9px;
      color: var(--color-text-secondary);
    }

    .btn-dialog-launcher:hover {
      opacity: 1;
    }

    .ribbon-divider {
      width: 1px;
      background-color: var(--color-border-divider);
      margin: 6px 4px 10px 4px;
    }

    /* ==========================================================================
       6. RIBBON CONTROLS & BUTTON ATOMS
       ========================================================================== */
    .btn-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 26px;
      padding: 0 4px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-xs);
      color: var(--color-text-primary);
      font-size: var(--font-size-base);
      cursor: pointer;
      user-select: none;
      transition: all 0.1s ease;
    }

    .btn-icon:hover:not(:disabled) {
      background-color: var(--color-bg-hover);
    }

    .btn-icon:active:not(:disabled) {
      background-color: var(--color-bg-active);
    }

    .btn-icon.is-active,
    .btn-icon[aria-pressed="true"] {
      background-color: var(--color-bg-selected);
      border-color: var(--color-border-input);
    }

    .btn-icon:disabled,
    .btn-icon.is-disabled {
      opacity: 0.35;
      cursor: default;
    }

    .chevron-down-mini {
      display: inline-block;
      width: 0;
      height: 0;
      margin-left: 3px;
      border-left: 3px solid transparent;
      border-right: 3px solid transparent;
      border-top: 3.5px solid var(--color-text-secondary);
    }

    .select-wrapper {
      position: relative;
    }

    .ribbon-select {
      appearance: none;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-input);
      border-radius: var(--radius-xs);
      height: 24px;
      padding: 0 18px 0 6px;
      font-size: var(--font-size-sm);
      color: var(--color-text-primary);
      font-family: inherit;
      outline: none;
      cursor: pointer;
    }

    .select-wrapper::after {
      content: "";
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      width: 0;
      height: 0;
      border-left: 3px solid transparent;
      border-right: 3px solid transparent;
      border-top: 3.5px solid var(--color-text-secondary);
      pointer-events: none;
    }

    .font-family-select {
      width: 120px;
    }

    .font-size-select {
      width: 48px;
    }

    /* Undo */
    .undo-group-content {
      align-items: flex-start;
      padding-top: 2px;
    }

    /* Clipboard */
    .clipboard-group-content {
      gap: 6px;
    }

    .split-button-vertical {
      display: flex;
      flex-direction: column;
      align-items: center;
      border-radius: var(--radius-xs);
    }

    .btn-paste-main {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      padding: 2px 8px;
      border-radius: var(--radius-xs);
      cursor: pointer;
      font-family: inherit;
    }

    .btn-paste-main .btn-text {
      font-size: 11px;
      color: var(--color-text-primary);
      margin-top: 1px;
    }

    .btn-paste-arrow {
      background: transparent;
      border: none;
      width: 100%;
      height: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .split-button-vertical:hover {
      background-color: var(--color-bg-hover);
    }

    .actions-stack {
      display: flex;
      flex-direction: column;
      gap: 1px;
    }

    .btn-compact {
      display: flex;
      align-items: center;
      gap: 5px;
      background: transparent;
      border: none;
      padding: 2px 6px;
      font-size: 11px;
      color: var(--color-text-primary);
      border-radius: var(--radius-xs);
      cursor: pointer;
      font-family: inherit;
      height: 18px;
    }

    .btn-compact:hover {
      background-color: var(--color-bg-hover);
    }

    /* Font & Paragraph Layout */
    .font-group-content,
    .paragraph-group-content {
      flex-direction: column;
      justify-content: center;
      gap: 3px;
    }

    .btn-color-picker {
      display: inline-flex;
      align-items: center;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-xs);
      padding: 1px 3px;
      cursor: pointer;
      height: 26px;
    }

    .btn-color-picker:hover {
      background-color: var(--color-bg-hover);
    }

    .color-picker-icon-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .icon-font-color {
      font-weight: 700;
      font-size: 13px;
      line-height: 1;
    }

    .color-bar {
      width: 13px;
      height: 3px;
      margin-top: 1px;
      border-radius: 0.5px;
    }

    .color-bar-yellow {
      background-color: var(--color-highlight-yellow);
    }

    .color-bar-red {
      background-color: var(--color-highlight-red);
    }

    /* Styles Gallery */
    .styles-group-content {
      gap: 4px;
    }

    .styles-gallery {
      display: flex;
      gap: 4px;
      height: 54px;
    }

    .style-card {
      width: 68px;
      height: 54px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-subtle);
      border-radius: var(--radius-xs);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 6px 2px 4px 2px;
      cursor: pointer;
      transition: all 0.1s ease;
    }

    .style-card:hover {
      border-color: var(--color-border-input);
      background-color: #fafafa;
    }

    .style-card.is-active {
      border-color: var(--color-accent-primary);
      background-color: var(--color-accent-subtle);
    }

    .style-preview {
      font-size: 14px;
      line-height: 1.2;
    }

    .font-normal {
      font-family: inherit;
    }

    .font-nospacing {
      letter-spacing: -0.8px;
    }

    .font-heading1 {
      font-size: 15px;
      font-weight: 600;
      color: var(--color-accent-primary);
    }

    .style-name {
      font-size: 9.5px;
      color: var(--color-text-secondary);
      white-space: nowrap;
    }

    .gallery-controls {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 54px;
    }

    .btn-gallery-nav {
      width: 16px;
      height: 17px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-subtle);
      font-size: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      border-radius: 1px;
    }

    .btn-gallery-nav:hover {
      background-color: var(--color-bg-hover);
    }

    /* ==========================================================================
       7. DOKUMENTENBLATT & INHALTSBEREICH (Canvas & Sheet)
       ========================================================================== */
    .editor-workspace {
      flex: 1;
      background-color: var(--color-bg-canvas);
      overflow-y: auto;
      padding: 32px 16px;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }

    .document-sheet {
      width: 100%;
      max-width: 816px;
      min-height: 1056px;
      background-color: var(--color-bg-surface);
      border-radius: var(--radius-xs);
      box-shadow: var(--shadow-sheet);
      padding: 64px 72px;
      outline: none;
      display: flex;
      flex-direction: column;
    }

    .doc-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }

    .doc-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .doc-brand-text {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.2px;
      color: var(--color-text-primary);
      line-height: 1.1;
    }

    .brand-subtitle {
      font-size: 11px;
      color: var(--color-text-secondary);
      font-weight: 500;
    }

    .doc-meta-date {
      font-size: 12px;
      color: var(--color-text-secondary);
    }

    .doc-divider {
      border: none;
      height: 1px;
      background-color: var(--color-border-subtle);
      margin-bottom: 32px;
    }

    .doc-main-heading {
      font-size: 28px;
      font-weight: 700;
      color: var(--color-text-primary);
      line-height: 1.25;
      margin-bottom: 12px;
      outline: none;
      border-radius: var(--radius-xs);
    }

    .doc-lead {
      font-size: 15px;
      line-height: 1.6;
      color: var(--color-text-secondary);
      margin-bottom: 28px;
      outline: none;
    }

    .doc-content-area {
      font-size: 14px;
      line-height: 1.65;
      color: var(--color-text-primary);
      outline: none;
      flex: 1;
    }

    .doc-content-area h2 {
      font-size: 18px;
      font-weight: 600;
      color: var(--color-accent-primary);
      margin-top: 24px;
      margin-bottom: 10px;
    }

    .doc-content-area p {
      margin-bottom: 14px;
    }

    .doc-content-area blockquote {
      border-left: 3px solid var(--color-accent-primary);
      padding-left: 14px;
      margin: 18px 0;
      color: var(--color-text-secondary);
      font-style: italic;
    }

    .doc-content-area ul {
      padding-left: 24px;
      margin-bottom: 14px;
    }

    .doc-content-area li {
      margin-bottom: 6px;
    }

    [contenteditable="true"]:focus-visible {
      outline: 1px dashed var(--color-border-input);
      outline-offset: 2px;
    }

    [contenteditable="true"]:empty::before {
      content: attr(data-placeholder);
      color: var(--color-text-muted);
      pointer-events: none;
    }

    /* ==========================================================================
       8. STATUS BAR (Fußzeile)
       ========================================================================== */
    .app-statusbar {
      height: 26px;
      background-color: var(--color-bg-app);
      border-top: 1px solid var(--color-border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 var(--space-md);
      font-size: 11px;
      color: var(--color-text-secondary);
      user-select: none;
    }

    .statusbar-left,
    .statusbar-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .status-divider {
      width: 1px;
      height: 12px;
      background-color: var(--color-border-divider);
    }

    .btn-status-view {
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: var(--radius-xs);
      font-size: 11px;
      opacity: 0.7;
    }

    .btn-status-view:hover {
      background-color: var(--color-bg-hover);
      opacity: 1;
    }

    .btn-status-view.is-active {
      background-color: var(--color-bg-active);
      opacity: 1;
    }

    .zoom-controller {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .btn-zoom-step {
      background: transparent;
      border: none;
      cursor: pointer;
      font-weight: bold;
      font-size: 12px;
      color: var(--color-text-secondary);
      padding: 0 4px;
    }

    .btn-zoom-step:hover {
      color: var(--color-text-primary);
    }

    .zoom-slider {
      width: 80px;
      height: 3px;
      accent-color: var(--color-accent-primary);
      cursor: pointer;
    }

    .zoom-value {
      width: 32px;
      text-align: right;
      font-size: 11px;
    }
  </style>
</head>
<body class="app-body">

  <!-- APP ROOT SHELL -->
  <div class="app-root" role="application" aria-label="Markdown Editor">

    <!-- 1. APP HEADER -->
    <header class="app-header" role="banner">
      <div class="app-header-left">
        <div class="app-brand-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect width="24" height="24" rx="4" fill="#0f6cbd"/>
            <path d="M6 7H9L12 15L15 7H18L13.5 17H10.5L6 7Z" fill="#ffffff"/>
          </svg>
        </div>

        <div class="document-meta">
          <input 
            type="text" 
            class="document-title-input" 
            value="Power & Simplicity" 
            aria-label="Dokumentname" 
            title="Dokumentname bearbeiten"
          />
          <span class="save-status" aria-live="polite">Saved</span>
        </div>
      </div>

      <div class="app-header-center">
        <div class="search-bar" role="search">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="search" 
            class="search-input" 
            placeholder="Search" 
            aria-label="Funktionen oder Text suchen"
          />
        </div>
      </div>

      <div class="app-header-right"></div>
    </header>

    <!-- 2. TAB NAVIGATION -->
    <nav class="tab-navigation" role="tablist" aria-label="Hauptmenü">
      <button role="tab" aria-selected="false" class="tab-item">File</button>
      <button role="tab" aria-selected="true" class="tab-item is-active">Home</button>
      <button role="tab" aria-selected="false" class="tab-item">Insert</button>
      <button role="tab" aria-selected="false" class="tab-item">Draw</button>
      <button role="tab" aria-selected="false" class="tab-item">Design</button>
      <button role="tab" aria-selected="false" class="tab-item">Layout</button>
      <button role="tab" aria-selected="false" class="tab-item">References</button>
      <button role="tab" aria-selected="false" class="tab-item">Mailings</button>
      <button role="tab" aria-selected="false" class="tab-item">Review</button>
      <button role="tab" aria-selected="false" class="tab-item">View</button>
      <button role="tab" aria-selected="false" class="tab-item">Help</button>
    </nav>

    <!-- 3. RIBBON TOOLBAR -->
    <section class="ribbon-toolbar" role="toolbar" aria-label="Home Werkzeuge">

      <!-- 3.1 Undo Group -->
      <div class="ribbon-group" role="group" aria-label="Rückgängig">
        <div class="group-content undo-group-content">
          <button type="button" class="btn-icon" title="Undo (Strg+Z)" aria-label="Rückgängig">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v6h6"></path>
              <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>
            </svg>
          </button>
          <button type="button" class="btn-icon is-disabled" disabled title="Redo (Strg+Y)" aria-label="Wiederholen">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 7v6h-6"></path>
              <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path>
            </svg>
          </button>
        </div>
        <div class="group-footer">
          <span class="group-title">Undo</span>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.2 Clipboard Group -->
      <div class="ribbon-group" role="group" aria-label="Zwischenablage">
        <div class="group-content clipboard-group-content">
          <div class="split-button-vertical">
            <button type="button" class="btn-paste-main" title="Paste (Strg+V)">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b8860b" stroke-width="1.8">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              <span class="btn-text">Paste</span>
            </button>
            <button type="button" class="btn-paste-arrow" aria-label="Weitere Einfügeoptionen">
              <span class="chevron-down-mini"></span>
            </button>
          </div>

          <div class="actions-stack">
            <button type="button" class="btn-compact" title="Cut (Strg+X)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="6" cy="6" r="3"></circle>
                <circle cx="6" cy="18" r="3"></circle>
                <line x1="20" y1="4" x2="8.12" y2="15.88"></line>
                <line x1="14.47" y1="14.48" x2="20" y2="20"></line>
                <line x1="8.12" y1="8.12" x2="12" y2="12"></line>
              </svg>
              <span>Cut</span>
            </button>

            <button type="button" class="btn-compact" title="Copy (Strg+C)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>

            <button type="button" class="btn-compact" title="Format Painter">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                <path d="M19 11V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h1v12a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-5"></path>
                <path d="M14 17l4 4 4-4"></path>
              </svg>
              <span>Format Paint</span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Clipboard</span>
          <button type="button" class="btn-dialog-launcher" title="Zwischenablage-Optionen" aria-label="Zwischenablage Optionen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.3 Font Group -->
      <div class="ribbon-group" role="group" aria-label="Schriftart">
        <div class="group-content font-group-content">
          <div class="toolbar-row">
            <div class="select-wrapper font-family-wrapper">
              <select class="ribbon-select font-family-select" aria-label="Schriftart wählen">
                <option value="Calibri" selected>Calibri (Body)</option>
                <option value="Arial">Arial</option>
                <option value="Segoe UI">Segoe UI</option>
                <option value="Times New Roman">Times New Roman</option>
              </select>
            </div>

            <div class="select-wrapper font-size-wrapper">
              <select class="ribbon-select font-size-select" aria-label="Schriftgröße wählen">
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11" selected>11</option>
                <option value="12">12</option>
                <option value="14">14</option>
                <option value="16">16</option>
                <option value="18">18</option>
              </select>
            </div>

            <button type="button" class="btn-icon" title="Schriftgröße vergrößern" aria-label="Schrift vergrößern">
              <span class="icon-text">A<sup>▲</sup></span>
            </button>
            <button type="button" class="btn-icon" title="Schriftgröße verkleinern" aria-label="Schrift verkleinern">
              <span class="icon-text">A<sup>▼</sup></span>
            </button>
            
            <button type="button" class="btn-icon" title="Groß-/Kleinschreibung ändern" aria-label="Groß-/Kleinschreibung">
              <span class="icon-text">Aa</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Alle Formatierungen löschen" aria-label="Formatierung löschen">
              <span class="icon-text">A<small>⌫</small></span>
            </button>
          </div>

          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle" title="Bold (Strg+B)" aria-pressed="false">
              <strong>B</strong>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Italic (Strg+I)" aria-pressed="false">
              <em>I</em>
            </button>
            <button type="button" class="btn-icon is-toggle has-dropdown" title="Underline (Strg+U)" aria-pressed="false">
              <u>U</u>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Durchgestrichen" aria-pressed="false">
              <s>ab</s>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Tiefgestellt" aria-pressed="false">
              x<sub>2</sub>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Hochgestellt" aria-pressed="false">
              x<sup>2</sup>
            </button>

            <button type="button" class="btn-icon has-dropdown" title="Texteffekte und Typografie">
              <span class="icon-effect-a">A</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Textmarkerfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-marker">🖊</span>
                <span class="color-bar color-bar-yellow"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Schriftfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-font-color">A</span>
                <span class="color-bar color-bar-red"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Font</span>
          <button type="button" class="btn-dialog-launcher" title="Schriftart-Einstellungen" aria-label="Schriftart Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.4 Paragraph Group -->
      <div class="ribbon-group" role="group" aria-label="Absatz">
        <div class="group-content paragraph-group-content">
          <div class="toolbar-row">
            <button type="button" class="btn-icon has-dropdown" title="Aufzählungszeichen">
              <span>•=</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Nummerierung">
              <span>123</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Liste mit mehreren Ebenen">
              <span>𝌆</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Einzug verkleinern">
              <span>⇤</span>
            </button>
            <button type="button" class="btn-icon" title="Einzug vergrößern">
              <span>⇥</span>
            </button>
            <button type="button" class="btn-icon" title="Sortieren">
              <span>A↓Z</span>
            </button>
            <button type="button" class="btn-icon" title="Alle anzeigen (¶)">
              <span>¶</span>
            </button>
          </div>

          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle is-active" title="Linksbündig" aria-pressed="true">
              <span>≡</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Zentriert" aria-pressed="false">
              <span>≍</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Rechtsbündig" aria-pressed="false">
              <span>≣</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Blocksatz" aria-pressed="false">
              <span>☷</span>
            </button>

            <button type="button" class="btn-icon has-dropdown" title="Zeilen- und Absatzabstand">
              <span>↕</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Schattierung">
              <span>🪣</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Rahmen">
              <span>⊞</span>
              <span class="chevron-down-mini"></span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Paragraph</span>
          <button type="button" class="btn-dialog-launcher" title="Absatz-Einstellungen" aria-label="Absatz Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.5 Styles Group -->
      <div class="ribbon-group styles-group" role="group" aria-label="Formatvorlagen">
        <div class="group-content styles-group-content">
          <div class="styles-gallery" role="listbox" aria-label="Formatvorlagen-Katalog">
            <button type="button" class="style-card is-active" role="option" aria-selected="true" title="Standard">
              <span class="style-preview font-normal">AaBbCc</span>
              <span class="style-name">Normal</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Kein Leerraum">
              <span class="style-preview font-nospacing">AaBbCc</span>
              <span class="style-name">No Spacing</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Überschrift 1">
              <span class="style-preview font-heading1">AaB</span>
              <span class="style-name">Heading 1</span>
            </button>
          </div>

          <div class="gallery-controls">
            <button type="button" class="btn-gallery-nav" title="Nach oben scrollen" aria-label="Nach oben">▲</button>
            <button type="button" class="btn-gallery-nav" title="Nach unten scrollen" aria-label="Nach unten">▼</button>
            <button type="button" class="btn-gallery-nav" title="Weitere Formatvorlagen" aria-label="Mehr">▾</button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Style</span>
        </div>
      </div>

    </section>

    <!-- 4. EDITOR WORKSPACE -->
    <main id="editor-workspace" class="editor-workspace" role="main">
      <article class="document-sheet" role="document" aria-label="Dokumentinhalt">
        
        <header class="doc-header">
          <div class="doc-brand">
            <div class="doc-logo-mark">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M4 4L12 20L20 4H15L12 11L9 4H4Z" fill="#1b1b1b"/>
              </svg>
            </div>
            <div class="doc-brand-text">
              <span class="brand-title">VanArsdel</span>
              <span class="brand-subtitle">VA Shared Design</span>
            </div>
          </div>

          <div class="doc-meta-date">
            <time datetime="2026-08-29">August 29, 2026</time>
          </div>
        </header>

        <hr class="doc-divider">

        <h1 class="doc-main-heading" contenteditable="true" spellcheck="false" data-placeholder="Dokumenttitel eingeben...">
          Power &amp; Simplicity
        </h1>

        <p class="doc-lead" contenteditable="true" spellcheck="false">
          A minimalist, distraction-free markdown and rich-text editing experience designed for modern web applications.
        </p>

        <div 
          id="editor-content" 
          class="doc-content-area" 
          contenteditable="true" 
          spellcheck="true"
          aria-multiline="true"
          role="textbox"
          data-placeholder="Beginnen Sie mit der Eingabe oder tippen Sie '/' für Befehle...">
          
          <h2>1. Introduction</h2>
          <p>
            The interface combines the familiar aesthetics of modern productivity suites with the velocity and lightweight nature of plain text Markdown formatting.
          </p>

          <blockquote>
            "Simplicity is prerequisite for reliability." — Edsger W. Dijkstra
          </blockquote>

          <h2>2. Key Features</h2>
          <ul>
            <li><strong>Full Typography Control:</strong> Real-time font scaling, weights, and heading hierarchisation.</li>
            <li><strong>Fluid Grid Canvas:</strong> Perfectly centered A4 sheet with realistic paper elevation.</li>
            <li><strong>Zero-Friction Toolbar:</strong> Fluent Design Ribbon with instant accessibility cues.</li>
          </ul>

        </div>

      </article>
    </main>

    <!-- 5. APP STATUS BAR -->
    <footer class="app-statusbar" role="contentinfo">
      <div class="statusbar-left">
        <span class="status-item">Page 1 of 1</span>
        <span class="status-divider"></span>
        <span class="status-item" id="word-count">142 words</span>
        <span class="status-divider"></span>
        <span class="status-item">English (US)</span>
      </div>

      <div class="statusbar-right">
        <button type="button" class="btn-status-view is-active" title="Drucklayout">📄</button>
        <button type="button" class="btn-status-view" title="Weblayout">🌐</button>
        <button type="button" class="btn-status-view" title="Fokusmodus">🔲</button>
        
        <span class="status-divider"></span>
        
        <div class="zoom-controller">
          <button type="button" class="btn-zoom-step" aria-label="Verkleinern">−</button>
          <input type="range" class="zoom-slider" min="50" max="200" value="100" aria-label="Zoomstufe">
          <button type="button" class="btn-zoom-step" aria-label="Vergrößern">+</button>
          <span class="zoom-value">100%</span>
        </div>
      </div>
    </footer>

  </div>

</body>
</html>

#### 👤 User
Kannst du in das html bitte noch einen css teil für einen dark mode entwerfen und schreiben? Speichere die Datei anschließend wieder unter index.html.

#### 🤖 LexData AI
<!DOCTYPE html>
<html lang="de" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Power & Simplicity - Markdown Editor</title>
  <style>
    /* ==========================================================================
       1. CSS RESET & BASIS-TOKENS (LIGHT THEME)
       ========================================================================== */
    *,
    *::before,
    *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    :root {
      /* Surface & Backgrounds */
      --color-bg-app: #f3f5f8;
      --color-bg-canvas: #dfe7f2;
      --color-bg-surface: #ffffff;
      --color-bg-sheet: #ffffff;
      --color-bg-hover: #e5e8ee;
      --color-bg-active: #d6dbe4;
      --color-bg-selected: #e0e6f0;

      /* Text & Content */
      --color-text-primary: #1b1b1b;
      --color-text-secondary: #5c5c5c;
      --color-text-muted: #8c8c8c;

      /* Brand & Accents (Fluent Blue & Highlights) */
      --color-accent-primary: #0f6cbd;
      --color-accent-hover: #115ea3;
      --color-accent-subtle: #ebf3fc;
      --color-highlight-yellow: #fff100;
      --color-highlight-red: #c42b1c;

      /* Borders & Dividers */
      --color-border-subtle: #e5e7eb;
      --color-border-divider: #d2d6dc;
      --color-border-input: #c8c8c8;
      --color-border-focus: #0f6cbd;

      /* Typography */
      --font-family-base: "Segoe UI Variable", "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", sans-serif;
      --font-size-xs: 11px;
      --font-size-sm: 12px;
      --font-size-base: 13px;
      --font-size-md: 14px;

      /* Spacing */
      --space-2xs: 2px;
      --space-xs: 4px;
      --space-sm: 6px;
      --space-md: 8px;
      --space-lg: 12px;
      --space-xl: 16px;

      /* Radii & Elevations */
      --radius-xs: 2px;
      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-pill: 20px;
      --radius-window: 10px;
      
      --shadow-window: 0 10px 30px rgba(0, 0, 0, 0.12);
      --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.08);
      --shadow-sheet: 0 4px 16px rgba(0, 0, 0, 0.1);

      /* Icon & SVG Colors */
      --logo-fill: #1b1b1b;
    }

    /* ==========================================================================
       DARK THEME DEFINITIONS
       ========================================================================== */
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme="light"]) {
        --color-bg-app: #202020;
        --color-bg-canvas: #181818;
        --color-bg-surface: #2b2b2b;
        --color-bg-sheet: #252525;
        --color-bg-hover: #333333;
        --color-bg-active: #3a3a3a;
        --color-bg-selected: #374151;

        --color-text-primary: #f3f3f3;
        --color-text-secondary: #adadad;
        --color-text-muted: #737373;

        --color-accent-primary: #479ef5;
        --color-accent-hover: #60a5fa;
        --color-accent-subtle: #1e3a5f;

        --color-border-subtle: #383838;
        --color-border-divider: #444444;
        --color-border-input: #505050;
        --color-border-focus: #479ef5;

        --shadow-window: 0 12px 36px rgba(0, 0, 0, 0.5);
        --shadow-sheet: 0 4px 20px rgba(0, 0, 0, 0.4);
        --logo-fill: #f3f3f3;
      }
    }

    :root[data-theme="dark"] {
      --color-bg-app: #202020;
      --color-bg-canvas: #181818;
      --color-bg-surface: #2b2b2b;
      --color-bg-sheet: #252525;
      --color-bg-hover: #333333;
      --color-bg-active: #3a3a3a;
      --color-bg-selected: #374151;

      --color-text-primary: #f3f3f3;
      --color-text-secondary: #adadad;
      --color-text-muted: #737373;

      --color-accent-primary: #479ef5;
      --color-accent-hover: #60a5fa;
      --color-accent-subtle: #1e3a5f;

      --color-border-subtle: #383838;
      --color-border-divider: #444444;
      --color-border-input: #505050;
      --color-border-focus: #479ef5;

      --shadow-window: 0 12px 36px rgba(0, 0, 0, 0.5);
      --shadow-sheet: 0 4px 20px rgba(0, 0, 0, 0.4);
      --logo-fill: #f3f3f3;
    }

    body.app-body {
      font-family: var(--font-family-base);
      font-size: var(--font-size-base);
      color: var(--color-text-primary);
      background-color: var(--color-bg-canvas);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 16px;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.2s ease, color 0.2s ease;
    }

    /* ==========================================================================
       2. APP ROOT SHELL
       ========================================================================== */
    .app-root {
      width: 100%;
      max-width: 1400px;
      min-height: 94vh;
      background-color: var(--color-bg-app);
      border-radius: var(--radius-window);
      box-shadow: var(--shadow-window);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid var(--color-border-subtle);
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }

    /* ==========================================================================
       3. APP HEADER (Titel, Status & Suche)
       ========================================================================== */
    .app-header {
      height: 44px;
      padding: 0 var(--space-lg);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: var(--color-bg-app);
    }

    .app-header-left {
      display: flex;
      align-items: center;
      gap: var(--space-md);
      flex: 1;
    }

    .app-brand-icon {
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .document-meta {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .document-title-input {
      border: 1px solid transparent;
      background: transparent;
      font-size: var(--font-size-base);
      font-weight: 600;
      color: var(--color-text-primary);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      outline: none;
      font-family: inherit;
      transition: all 0.15s ease;
    }

    .document-title-input:hover {
      background-color: var(--color-bg-hover);
    }

    .document-title-input:focus {
      background-color: var(--color-bg-surface);
      border-color: var(--color-border-focus);
    }

    .save-status {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
      user-select: none;
    }

    .app-header-center {
      flex: 1.5;
      display: flex;
      justify-content: center;
    }

    .search-bar {
      width: 100%;
      max-width: 480px;
      height: 30px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-input);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      padding: 0 var(--space-md);
      gap: var(--space-xs);
      transition: border-color 0.15s ease, background-color 0.2s ease;
    }

    .search-bar:focus-within {
      border-color: var(--color-border-focus);
      box-shadow: 0 0 0 1px var(--color-border-focus);
    }

    .search-icon {
      color: var(--color-text-secondary);
    }

    .search-input {
      width: 100%;
      border: none;
      background: transparent;
      outline: none;
      font-size: var(--font-size-sm);
      font-family: inherit;
      color: var(--color-text-primary);
    }

    .search-input::placeholder {
      color: var(--color-text-muted);
    }

    .app-header-right {
      flex: 1;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: var(--space-sm);
    }

    /* Theme Toggle Button */
    .btn-theme-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 30px;
      height: 30px;
      border-radius: var(--radius-sm);
      background: transparent;
      border: 1px solid transparent;
      color: var(--color-text-secondary);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-theme-toggle:hover {
      background-color: var(--color-bg-hover);
      color: var(--color-text-primary);
    }

    /* ==========================================================================
       4. TAB NAVIGATION (Menüband-Reiter)
       ========================================================================== */
    .tab-navigation {
      display: flex;
      align-items: center;
      height: 32px;
      padding: 0 var(--space-lg);
      background-color: var(--color-bg-app);
      gap: 2px;
      border-bottom: 1px solid var(--color-border-subtle);
    }

    .tab-item {
      position: relative;
      background: transparent;
      border: none;
      padding: 6px 10px;
      font-size: var(--font-size-base);
      color: var(--color-text-primary);
      font-family: inherit;
      cursor: pointer;
      border-radius: var(--radius-sm) var(--radius-sm) 0 0;
      transition: background-color 0.1s ease, color 0.1s ease;
    }

    .tab-item:hover {
      background-color: var(--color-bg-hover);
    }

    .tab-item.is-active {
      font-weight: 600;
    }

    .tab-item.is-active::after {
      content: "";
      position: absolute;
      bottom: -1px;
      left: 8px;
      right: 8px;
      height: 2.5px;
      background-color: var(--color-accent-primary);
      border-radius: 2px 2px 0 0;
    }

    /* ==========================================================================
       5. RIBBON TOOLBAR (Werkzeugleiste)
       ========================================================================== */
    .ribbon-toolbar {
      height: 92px;
      background-color: var(--color-bg-app);
      border-bottom: 1px solid var(--color-border-subtle);
      display: flex;
      align-items: stretch;
      padding: 4px var(--space-lg);
      overflow-x: auto;
    }

    .ribbon-group {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 2px 6px 4px 6px;
      flex-shrink: 0;
    }

    .group-content {
      display: flex;
      align-items: center;
      height: 60px;
      gap: 4px;
    }

    .toolbar-row {
      display: flex;
      align-items: center;
      gap: 2px;
    }

    .group-footer {
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      height: 16px;
    }

    .group-title {
      font-size: 10px;
      color: var(--color-text-secondary);
      user-select: none;
    }

    .btn-dialog-launcher {
      position: absolute;
      right: 0;
      bottom: 1px;
      width: 12px;
      height: 12px;
      border: none;
      background: transparent;
      cursor: pointer;
      opacity: 0.65;
    }

    .btn-dialog-launcher::after {
      content: "↗";
      font-size: 9px;
      color: var(--color-text-secondary);
    }

    .btn-dialog-launcher:hover {
      opacity: 1;
    }

    .ribbon-divider {
      width: 1px;
      background-color: var(--color-border-divider);
      margin: 6px 4px 10px 4px;
    }

    /* ==========================================================================
       6. RIBBON CONTROLS & BUTTON ATOMS
       ========================================================================== */
    .btn-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 26px;
      padding: 0 4px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-xs);
      color: var(--color-text-primary);
      font-size: var(--font-size-base);
      cursor: pointer;
      user-select: none;
      transition: all 0.1s ease;
    }

    .btn-icon:hover:not(:disabled) {
      background-color: var(--color-bg-hover);
    }

    .btn-icon:active:not(:disabled) {
      background-color: var(--color-bg-active);
    }

    .btn-icon.is-active,
    .btn-icon[aria-pressed="true"] {
      background-color: var(--color-bg-selected);
      border-color: var(--color-border-input);
    }

    .btn-icon:disabled,
    .btn-icon.is-disabled {
      opacity: 0.35;
      cursor: default;
    }

    .chevron-down-mini {
      display: inline-block;
      width: 0;
      height: 0;
      margin-left: 3px;
      border-left: 3px solid transparent;
      border-right: 3px solid transparent;
      border-top: 3.5px solid var(--color-text-secondary);
    }

    .select-wrapper {
      position: relative;
    }

    .ribbon-select {
      appearance: none;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-input);
      border-radius: var(--radius-xs);
      height: 24px;
      padding: 0 18px 0 6px;
      font-size: var(--font-size-sm);
      color: var(--color-text-primary);
      font-family: inherit;
      outline: none;
      cursor: pointer;
    }

    .select-wrapper::after {
      content: "";
      position: absolute;
      right: 6px;
      top: 50%;
      transform: translateY(-50%);
      width: 0;
      height: 0;
      border-left: 3px solid transparent;
      border-right: 3px solid transparent;
      border-top: 3.5px solid var(--color-text-secondary);
      pointer-events: none;
    }

    .font-family-select {
      width: 120px;
    }

    .font-size-select {
      width: 48px;
    }

    /* Undo */
    .undo-group-content {
      align-items: flex-start;
      padding-top: 2px;
    }

    /* Clipboard */
    .clipboard-group-content {
      gap: 6px;
    }

    .split-button-vertical {
      display: flex;
      flex-direction: column;
      align-items: center;
      border-radius: var(--radius-xs);
    }

    .btn-paste-main {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      padding: 2px 8px;
      border-radius: var(--radius-xs);
      cursor: pointer;
      font-family: inherit;
    }

    .btn-paste-main .btn-text {
      font-size: 11px;
      color: var(--color-text-primary);
      margin-top: 1px;
    }

    .btn-paste-arrow {
      background: transparent;
      border: none;
      width: 100%;
      height: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .split-button-vertical:hover {
      background-color: var(--color-bg-hover);
    }

    .actions-stack {
      display: flex;
      flex-direction: column;
      gap: 1px;
    }

    .btn-compact {
      display: flex;
      align-items: center;
      gap: 5px;
      background: transparent;
      border: none;
      padding: 2px 6px;
      font-size: 11px;
      color: var(--color-text-primary);
      border-radius: var(--radius-xs);
      cursor: pointer;
      font-family: inherit;
      height: 18px;
    }

    .btn-compact:hover {
      background-color: var(--color-bg-hover);
    }

    /* Font & Paragraph Layout */
    .font-group-content,
    .paragraph-group-content {
      flex-direction: column;
      justify-content: center;
      gap: 3px;
    }

    .btn-color-picker {
      display: inline-flex;
      align-items: center;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-xs);
      padding: 1px 3px;
      cursor: pointer;
      height: 26px;
    }

    .btn-color-picker:hover {
      background-color: var(--color-bg-hover);
    }

    .color-picker-icon-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .icon-font-color {
      font-weight: 700;
      font-size: 13px;
      line-height: 1;
    }

    .color-bar {
      width: 13px;
      height: 3px;
      margin-top: 1px;
      border-radius: 0.5px;
    }

    .color-bar-yellow {
      background-color: var(--color-highlight-yellow);
    }

    .color-bar-red {
      background-color: var(--color-highlight-red);
    }

    /* Styles Gallery */
    .styles-group-content {
      gap: 4px;
    }

    .styles-gallery {
      display: flex;
      gap: 4px;
      height: 54px;
    }

    .style-card {
      width: 68px;
      height: 54px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-subtle);
      border-radius: var(--radius-xs);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 6px 2px 4px 2px;
      cursor: pointer;
      transition: all 0.1s ease;
    }

    .style-card:hover {
      border-color: var(--color-border-input);
      background-color: var(--color-bg-hover);
    }

    .style-card.is-active {
      border-color: var(--color-accent-primary);
      background-color: var(--color-accent-subtle);
    }

    .style-preview {
      font-size: 14px;
      line-height: 1.2;
    }

    .font-normal {
      font-family: inherit;
    }

    .font-nospacing {
      letter-spacing: -0.8px;
    }

    .font-heading1 {
      font-size: 15px;
      font-weight: 600;
      color: var(--color-accent-primary);
    }

    .style-name {
      font-size: 9.5px;
      color: var(--color-text-secondary);
      white-space: nowrap;
    }

    .gallery-controls {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 54px;
    }

    .btn-gallery-nav {
      width: 16px;
      height: 17px;
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border-subtle);
      color: var(--color-text-primary);
      font-size: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      border-radius: 1px;
    }

    .btn-gallery-nav:hover {
      background-color: var(--color-bg-hover);
    }

    /* ==========================================================================
       7. DOKUMENTENBLATT & INHALTSBEREICH (Canvas & Sheet)
       ========================================================================== */
    .editor-workspace {
      flex: 1;
      background-color: var(--color-bg-canvas);
      overflow-y: auto;
      padding: 32px 16px;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      transition: background-color 0.2s ease;
    }

    .document-sheet {
      width: 100%;
      max-width: 816px;
      min-height: 1056px;
      background-color: var(--color-bg-sheet);
      border-radius: var(--radius-xs);
      box-shadow: var(--shadow-sheet);
      padding: 64px 72px;
      outline: none;
      display: flex;
      flex-direction: column;
      transition: background-color 0.2s ease, box-shadow 0.2s ease;
    }

    .doc-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }

    .doc-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .doc-logo-mark svg path {
      fill: var(--logo-fill);
      transition: fill 0.2s ease;
    }

    .doc-brand-text {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: -0.2px;
      color: var(--color-text-primary);
      line-height: 1.1;
    }

    .brand-subtitle {
      font-size: 11px;
      color: var(--color-text-secondary);
      font-weight: 500;
    }

    .doc-meta-date {
      font-size: 12px;
      color: var(--color-text-secondary);
    }

    .doc-divider {
      border: none;
      height: 1px;
      background-color: var(--color-border-subtle);
      margin-bottom: 32px;
    }

    .doc-main-heading {
      font-size: 28px;
      font-weight: 700;
      color: var(--color-text-primary);
      line-height: 1.25;
      margin-bottom: 12px;
      outline: none;
      border-radius: var(--radius-xs);
    }

    .doc-lead {
      font-size: 15px;
      line-height: 1.6;
      color: var(--color-text-secondary);
      margin-bottom: 28px;
      outline: none;
    }

    .doc-content-area {
      font-size: 14px;
      line-height: 1.65;
      color: var(--color-text-primary);
      outline: none;
      flex: 1;
    }

    .doc-content-area h2 {
      font-size: 18px;
      font-weight: 600;
      color: var(--color-accent-primary);
      margin-top: 24px;
      margin-bottom: 10px;
    }

    .doc-content-area p {
      margin-bottom: 14px;
    }

    .doc-content-area blockquote {
      border-left: 3px solid var(--color-accent-primary);
      padding-left: 14px;
      margin: 18px 0;
      color: var(--color-text-secondary);
      font-style: italic;
    }

    .doc-content-area ul {
      padding-left: 24px;
      margin-bottom: 14px;
    }

    .doc-content-area li {
      margin-bottom: 6px;
    }

    [contenteditable="true"]:focus-visible {
      outline: 1px dashed var(--color-border-input);
      outline-offset: 2px;
    }

    [contenteditable="true"]:empty::before {
      content: attr(data-placeholder);
      color: var(--color-text-muted);
      pointer-events: none;
    }

    /* ==========================================================================
       8. STATUS BAR (Fußzeile)
       ========================================================================== */
    .app-statusbar {
      height: 26px;
      background-color: var(--color-bg-app);
      border-top: 1px solid var(--color-border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 var(--space-md);
      font-size: 11px;
      color: var(--color-text-secondary);
      user-select: none;
    }

    .statusbar-left,
    .statusbar-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .status-divider {
      width: 1px;
      height: 12px;
      background-color: var(--color-border-divider);
    }

    .btn-status-view {
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: var(--radius-xs);
      font-size: 11px;
      opacity: 0.7;
    }

    .btn-status-view:hover {
      background-color: var(--color-bg-hover);
      opacity: 1;
    }

    .btn-status-view.is-active {
      background-color: var(--color-bg-active);
      opacity: 1;
    }

    .zoom-controller {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .btn-zoom-step {
      background: transparent;
      border: none;
      cursor: pointer;
      font-weight: bold;
      font-size: 12px;
      color: var(--color-text-secondary);
      padding: 0 4px;
    }

    .btn-zoom-step:hover {
      color: var(--color-text-primary);
    }

    .zoom-slider {
      width: 80px;
      height: 3px;
      accent-color: var(--color-accent-primary);
      cursor: pointer;
    }

    .zoom-value {
      width: 32px;
      text-align: right;
      font-size: 11px;
    }
  </style>
</head>
<body class="app-body">

  <!-- APP ROOT SHELL -->
  <div class="app-root" role="application" aria-label="Markdown Editor">

    <!-- 1. APP HEADER -->
    <header class="app-header" role="banner">
      <div class="app-header-left">
        <div class="app-brand-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect width="24" height="24" rx="4" fill="#0f6cbd"/>
            <path d="M6 7H9L12 15L15 7H18L13.5 17H10.5L6 7Z" fill="#ffffff"/>
          </svg>
        </div>

        <div class="document-meta">
          <input 
            type="text" 
            class="document-title-input" 
            value="Power & Simplicity" 
            aria-label="Dokumentname" 
            title="Dokumentname bearbeiten"
          />
          <span class="save-status" aria-live="polite">Saved</span>
        </div>
      </div>

      <div class="app-header-center">
        <div class="search-bar" role="search">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="search" 
            class="search-input" 
            placeholder="Search" 
            aria-label="Funktionen oder Text suchen"
          />
        </div>
      </div>

      <div class="app-header-right">
        <!-- Theme Toggle Button -->
        <button type="button" id="theme-toggle" class="btn-theme-toggle" title="Design umschalten (Hell/Dunkel)" aria-label="Design umschalten">
          <svg id="theme-icon-sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <svg id="theme-icon-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </header>

    <!-- 2. TAB NAVIGATION -->
    <nav class="tab-navigation" role="tablist" aria-label="Hauptmenü">
      <button role="tab" aria-selected="false" class="tab-item">File</button>
      <button role="tab" aria-selected="true" class="tab-item is-active">Home</button>
      <button role="tab" aria-selected="false" class="tab-item">Insert</button>
      <button role="tab" aria-selected="false" class="tab-item">Draw</button>
      <button role="tab" aria-selected="false" class="tab-item">Design</button>
      <button role="tab" aria-selected="false" class="tab-item">Layout</button>
      <button role="tab" aria-selected="false" class="tab-item">References</button>
      <button role="tab" aria-selected="false" class="tab-item">Mailings</button>
      <button role="tab" aria-selected="false" class="tab-item">Review</button>
      <button role="tab" aria-selected="false" class="tab-item">View</button>
      <button role="tab" aria-selected="false" class="tab-item">Help</button>
    </nav>

    <!-- 3. RIBBON TOOLBAR -->
    <section class="ribbon-toolbar" role="toolbar" aria-label="Home Werkzeuge">

      <!-- 3.1 Undo Group -->
      <div class="ribbon-group" role="group" aria-label="Rückgängig">
        <div class="group-content undo-group-content">
          <button type="button" class="btn-icon" title="Undo (Strg+Z)" aria-label="Rückgängig">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 7v6h6"></path>
              <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>
            </svg>
          </button>
          <button type="button" class="btn-icon is-disabled" disabled title="Redo (Strg+Y)" aria-label="Wiederholen">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 7v6h-6"></path>
              <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path>
            </svg>
          </button>
        </div>
        <div class="group-footer">
          <span class="group-title">Undo</span>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.2 Clipboard Group -->
      <div class="ribbon-group" role="group" aria-label="Zwischenablage">
        <div class="group-content clipboard-group-content">
          <div class="split-button-vertical">
            <button type="button" class="btn-paste-main" title="Paste (Strg+V)">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b8860b" stroke-width="1.8">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              <span class="btn-text">Paste</span>
            </button>
            <button type="button" class="btn-paste-arrow" aria-label="Weitere Einfügeoptionen">
              <span class="chevron-down-mini"></span>
            </button>
          </div>

          <div class="actions-stack">
            <button type="button" class="btn-compact" title="Cut (Strg+X)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="6" cy="6" r="3"></circle>
                <circle cx="6" cy="18" r="3"></circle>
                <line x1="20" y1="4" x2="8.12" y2="15.88"></line>
                <line x1="14.47" y1="14.48" x2="20" y2="20"></line>
                <line x1="8.12" y1="8.12" x2="12" y2="12"></line>
              </svg>
              <span>Cut</span>
            </button>

            <button type="button" class="btn-compact" title="Copy (Strg+C)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>

            <button type="button" class="btn-compact" title="Format Painter">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                <path d="M19 11V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h1v12a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-5"></path>
                <path d="M14 17l4 4 4-4"></path>
              </svg>
              <span>Format Paint</span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Clipboard</span>
          <button type="button" class="btn-dialog-launcher" title="Zwischenablage-Optionen" aria-label="Zwischenablage Optionen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.3 Font Group -->
      <div class="ribbon-group" role="group" aria-label="Schriftart">
        <div class="group-content font-group-content">
          <div class="toolbar-row">
            <div class="select-wrapper font-family-wrapper">
              <select class="ribbon-select font-family-select" aria-label="Schriftart wählen">
                <option value="Calibri" selected>Calibri (Body)</option>
                <option value="Arial">Arial</option>
                <option value="Segoe UI">Segoe UI</option>
                <option value="Times New Roman">Times New Roman</option>
              </select>
            </div>

            <div class="select-wrapper font-size-wrapper">
              <select class="ribbon-select font-size-select" aria-label="Schriftgröße wählen">
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11" selected>11</option>
                <option value="12">12</option>
                <option value="14">14</option>
                <option value="16">16</option>
                <option value="18">18</option>
              </select>
            </div>

            <button type="button" class="btn-icon" title="Schriftgröße vergrößern" aria-label="Schrift vergrößern">
              <span class="icon-text">A<sup>▲</sup></span>
            </button>
            <button type="button" class="btn-icon" title="Schriftgröße verkleinern" aria-label="Schrift verkleinern">
              <span class="icon-text">A<sup>▼</sup></span>
            </button>
            
            <button type="button" class="btn-icon" title="Groß-/Kleinschreibung ändern" aria-label="Groß-/Kleinschreibung">
              <span class="icon-text">Aa</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Alle Formatierungen löschen" aria-label="Formatierung löschen">
              <span class="icon-text">A<small>⌫</small></span>
            </button>
          </div>

          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle" title="Bold (Strg+B)" aria-pressed="false">
              <strong>B</strong>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Italic (Strg+I)" aria-pressed="false">
              <em>I</em>
            </button>
            <button type="button" class="btn-icon is-toggle has-dropdown" title="Underline (Strg+U)" aria-pressed="false">
              <u>U</u>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Durchgestrichen" aria-pressed="false">
              <s>ab</s>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Tiefgestellt" aria-pressed="false">
              x<sub>2</sub>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Hochgestellt" aria-pressed="false">
              x<sup>2</sup>
            </button>

            <button type="button" class="btn-icon has-dropdown" title="Texteffekte und Typografie">
              <span class="icon-effect-a">A</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Textmarkerfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-marker">🖊</span>
                <span class="color-bar color-bar-yellow"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-color-picker" title="Schriftfarbe">
              <div class="color-picker-icon-wrapper">
                <span class="icon-font-color">A</span>
                <span class="color-bar color-bar-red"></span>
              </div>
              <span class="chevron-down-mini"></span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Font</span>
          <button type="button" class="btn-dialog-launcher" title="Schriftart-Einstellungen" aria-label="Schriftart Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.4 Paragraph Group -->
      <div class="ribbon-group" role="group" aria-label="Absatz">
        <div class="group-content paragraph-group-content">
          <div class="toolbar-row">
            <button type="button" class="btn-icon has-dropdown" title="Aufzählungszeichen">
              <span>•=</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Nummerierung">
              <span>123</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Liste mit mehreren Ebenen">
              <span>𝌆</span>
              <span class="chevron-down-mini"></span>
            </button>

            <button type="button" class="btn-icon" title="Einzug verkleinern">
              <span>⇤</span>
            </button>
            <button type="button" class="btn-icon" title="Einzug vergrößern">
              <span>⇥</span>
            </button>
            <button type="button" class="btn-icon" title="Sortieren">
              <span>A↓Z</span>
            </button>
            <button type="button" class="btn-icon" title="Alle anzeigen (¶)">
              <span>¶</span>
            </button>
          </div>

          <div class="toolbar-row">
            <button type="button" class="btn-icon is-toggle is-active" title="Linksbündig" aria-pressed="true">
              <span>≡</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Zentriert" aria-pressed="false">
              <span>≍</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Rechtsbündig" aria-pressed="false">
              <span>≣</span>
            </button>
            <button type="button" class="btn-icon is-toggle" title="Blocksatz" aria-pressed="false">
              <span>☷</span>
            </button>

            <button type="button" class="btn-icon has-dropdown" title="Zeilen- und Absatzabstand">
              <span>↕</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Schattierung">
              <span>🪣</span>
              <span class="chevron-down-mini"></span>
            </button>
            <button type="button" class="btn-icon has-dropdown" title="Rahmen">
              <span>⊞</span>
              <span class="chevron-down-mini"></span>
            </button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Paragraph</span>
          <button type="button" class="btn-dialog-launcher" title="Absatz-Einstellungen" aria-label="Absatz Einstellungen"></button>
        </div>
      </div>

      <div class="ribbon-divider" role="separator" aria-orientation="vertical"></div>

      <!-- 3.5 Styles Group -->
      <div class="ribbon-group styles-group" role="group" aria-label="Formatvorlagen">
        <div class="group-content styles-group-content">
          <div class="styles-gallery" role="listbox" aria-label="Formatvorlagen-Katalog">
            <button type="button" class="style-card is-active" role="option" aria-selected="true" title="Standard">
              <span class="style-preview font-normal">AaBbCc</span>
              <span class="style-name">Normal</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Kein Leerraum">
              <span class="style-preview font-nospacing">AaBbCc</span>
              <span class="style-name">No Spacing</span>
            </button>

            <button type="button" class="style-card" role="option" aria-selected="false" title="Überschrift 1">
              <span class="style-preview font-heading1">AaB</span>
              <span class="style-name">Heading 1</span>
            </button>
          </div>

          <div class="gallery-controls">
            <button type="button" class="btn-gallery-nav" title="Nach oben scrollen" aria-label="Nach oben">▲</button>
            <button type="button" class="btn-gallery-nav" title="Nach unten scrollen" aria-label="Nach unten">▼</button>
            <button type="button" class="btn-gallery-nav" title="Weitere Formatvorlagen" aria-label="Mehr">▾</button>
          </div>
        </div>

        <div class="group-footer">
          <span class="group-title">Style</span>
        </div>
      </div>

    </section>

    <!-- 4. EDITOR WORKSPACE -->
    <main id="editor-workspace" class="editor-workspace" role="main">
      <article class="document-sheet" role="document" aria-label="Dokumentinhalt">
        
        <header class="doc-header">
          <div class="doc-brand">
            <div class="doc-logo-mark">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M4 4L12 20L20 4H15L12 11L9 4H4Z" fill="var(--logo-fill)"/>
              </svg>
            </div>
            <div class="doc-brand-text">
              <span class="brand-title">VanArsdel</span>
              <span class="brand-subtitle">VA Shared Design</span>
            </div>
          </div>

          <div class="doc-meta-date">
            <time datetime="2026-08-29">August 29, 2026</time>
          </div>
        </header>

        <hr class="doc-divider">

        <h1 class="doc-main-heading" contenteditable="true" spellcheck="false" data-placeholder="Dokumenttitel eingeben...">
          Power &amp; Simplicity
        </h1>

        <p class="doc-lead" contenteditable="true" spellcheck="false">
          A minimalist, distraction-free markdown and rich-text editing experience designed for modern web applications.
        </p>

        <div 
          id="editor-content" 
          class="doc-content-area" 
          contenteditable="true" 
          spellcheck="true"
          aria-multiline="true"
          role="textbox"
          data-placeholder="Beginnen Sie mit der Eingabe oder tippen Sie '/' für Befehle...">
          
          <h2>1. Introduction</h2>
          <p>
            The interface combines the familiar aesthetics of modern productivity suites with the velocity and lightweight nature of plain text Markdown formatting.
          </p>

          <blockquote>
            "Simplicity is prerequisite for reliability." — Edsger W. Dijkstra
          </blockquote>

          <h2>2. Key Features</h2>
          <ul>
            <li><strong>Full Typography Control:</strong> Real-time font scaling, weights, and heading hierarchisation.</li>
            <li><strong>Fluid Grid Canvas:</strong> Perfectly centered A4 sheet with realistic paper elevation.</li>
            <li><strong>Zero-Friction Toolbar:</strong> Fluent Design Ribbon with instant accessibility cues.</li>
          </ul>

        </div>

      </article>
    </main>

    <!-- 5. APP STATUS BAR -->
    <footer class="app-statusbar" role="contentinfo">
      <div class="statusbar-left">
        <span class="status-item">Page 1 of 1</span>
        <span class="status-divider"></span>
        <span class="status-item" id="word-count">142 words</span>
        <span class="status-divider"></span>
        <span class="status-item">English (US)</span>
      </div>

      <div class="statusbar-right">
        <button type="button" class="btn-status-view is-active" title="Drucklayout">📄</button>
        <button type="button" class="btn-status-view" title="Weblayout">🌐</button>
        <button type="button" class="btn-status-view" title="Fokusmodus">🔲</button>
        
        <span class="status-divider"></span>
        
        <div class="zoom-controller">
          <button type="button" class="btn-zoom-step" aria-label="Verkleinern">−</button>
          <input type="range" class="zoom-slider" min="50" max="200" value="100" aria-label="Zoomstufe">
          <button type="button" class="btn-zoom-step" aria-label="Vergrößern">+</button>
          <span class="zoom-value">100%</span>
        </div>
      </div>
    </footer>

  </div>

  <!-- THEME TOGGLE & INTERACTION SCRIPT -->
  <script>
    (function () {
      const themeToggleBtn = document.getElementById('theme-toggle');
      const sunIcon = document.getElementById('theme-icon-sun');
      const moonIcon = document.getElementById('theme-icon-moon');
      const root = document.documentElement;

      function updateThemeIcons(theme) {
        if (theme === 'dark') {
          sunIcon.style.display = 'none';
          moonIcon.style.display = 'block';
        } else {
          sunIcon.style.display = 'block';
          moonIcon.style.display = 'none';
        }
      }

      function getInitialTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
          return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }

      function setTheme(theme) {
        root.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        updateThemeIcons(theme);
      }

      const initialTheme = getInitialTheme();
      setTheme(initialTheme);

      themeToggleBtn.addEventListener('click', () => {
        const currentTheme = root.getAttribute('data-theme') || 'light';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(nextTheme);
      });

      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          setTheme(e.matches ? 'dark' : 'light');
        }
      });
    })();
  </script>
</body>
</html>