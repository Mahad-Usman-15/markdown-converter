# Design system: Markdown converter

Status: First-release specification  
Reference: [Anthropic homepage](https://www.anthropic.com/)  
Reference inspected: September 20, 2026

## 1. Product and scope

A focused web app that converts PDF files, public webpage URLs, and plain text into structured Markdown, ready to edit, copy, or download.

Supported inputs:

- One PDF, including scanned PDFs processed with OCR.
- One public webpage URL.
- Pasted plain text or one uploaded `.txt` file.

Output: editable GitHub-flavored Markdown and a rendered preview. Preserve source wording and flag uncertain extraction. Exclude accounts, conversion history, batch processing, full-site crawling, and other file formats from this release.

Implementation context: a modular monolith with React, TypeScript, Vite, and Tailwind CSS served by FastAPI on one native Python Render service. Use FastAPI BackgroundTasks for conversions, CodeMirror for editing, and react-markdown with remark-gfm for preview. The interface must accommodate asynchronous jobs and interrupted jobs. No Docker or Vercel deployment is required.

## 2. Reference direction

The inspected homepage combines a warm neutral canvas, dark typography, a bold sans-serif headline, serif supporting prose, ample whitespace, restrained navigation, and rounded dark feature panels.

Observed computed body colors were `#FAF9F5` and `#141413`. The serif family is named Anthropic Serif. Other values below are proposed product tokens, not a claim to reproduce Anthropic's official design system.

Adapt this visual language to a working utility:

- Let typography and spacing establish hierarchy.
- Use warm surfaces and thin rules to organize content.
- Keep the conversion action visible without scrolling on a typical desktop.
- Use dark, high-contrast primary actions.
- Use serif type for brief explanatory copy and sans-serif type for controls.
- Keep the editor visually quiet and give content the largest share of space.

Use the app's own identity. A neutral text wordmark, “Markdown Converter,” is the working label. Do not use Anthropic's logo, proprietary font files, product names, or marketing copy as app branding.

## 3. Color tokens

| Token | Value | Purpose |
| --- | --- | --- |
| canvas | #FAF9F5 | Overall page background |
| surface | #FFFFFF | Inputs, editor, preview |
| surface-muted | #F0EEE6 | Secondary panels, table headers, code backgrounds |
| ink | #141413 | Main text and primary buttons |
| ink-muted | #5F5D56 | Help text and metadata |
| border | #D8D5CC | Decorative separators and panel outlines |
| control-border | #858278 | Input boundaries |
| hover | #E9E6DD | Quiet hover and selected backgrounds |
| accent | #A34F36 | Underlined links and small emphasis |
| focus | #7B4936 | Keyboard focus outline |
| success | #356345 | Successful result text and icon |
| success-surface | #EDF4EE | Success notice background |
| warning | #785313 | Review notice text and icon |
| warning-surface | #FBF2DD | Review notice background |
| danger | #A13232 | Error text, icon, and field boundary |
| danger-surface | #FBEDED | Error notice background |

Use ink text on light surfaces and canvas text on ink buttons. Status labels always include text and an icon. Decorative border is too subtle to serve as the only boundary of an input; use control-border for that purpose. Verify final combinations meet accessibility targets.

## 4. Typography

Use locally available font stacks for the first release. No proprietary font dependency is required.

| Role | Stack | Size and line height | Weight |
| --- | --- | --- | --- |
| Hero title | Arial, Helvetica, sans-serif | Fluid 36px to 56px / 1.08 | 700 |
| Section title | Arial, Helvetica, sans-serif | 24px / 1.25 | 600 |
| Introductory copy | Georgia, Times New Roman, serif | 20px / 1.45 | 400 |
| Body and controls | Arial, Helvetica, sans-serif | 16px / 1.5 | 400 |
| Button and tab labels | Arial, Helvetica, sans-serif | 15px / 1.3 | 600 |
| Help and metadata | Arial, Helvetica, sans-serif | 14px / 1.45 | 400 |
| Markdown editor | ui-monospace, SFMono-Regular, Consolas, monospace | 14px / 1.65 | 400 |

Use slightly tight tracking on large headlines only. Avoid uppercase sentences. Limit introductory prose to approximately 55 characters per line. Preview body text is 16px with a 1.7 line height; heading levels must remain visibly distinct.

## 5. Spacing and shape

- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64px.
- Main container: maximum 1200px, centered.
- Page gutters: 48px desktop, 24px tablet, 16px mobile.
- Header height: approximately 72px desktop and 64px mobile.
- Introductory section: 48px above and 32px below on desktop; 24px on mobile.
- Panel padding: 24px desktop, 16px mobile.
- Control height: at least 44px.
- Control radius: 8px. Workspace radius: 16px. Small notices: 8px.
- Use 1px borders. Default panels have no shadow.
- Reserve subtle shadows for floating menus and temporary notifications.
- Avoid gradients, glass effects, large decorative illustrations, and unnecessary floating cards.

## 6. Page composition

### Initial state

1. Compact header with the working wordmark and a “How it works” anchor.
2. Left-aligned title: “Turn your content into Markdown.”
3. Serif supporting line: “Convert PDFs, webpages, and text into structured Markdown you can edit and copy.”
4. Main converter panel with three tabs: “PDF”, “Website”, and “Plain text”.
5. Active input area and the primary “Convert to Markdown” button.
6. A short explanatory row below: “Add your content”, “Review the result”, “Copy or download”.

Default to the PDF tab. Preserve each tab's draft during the session. Switching tabs must not submit or erase an input.

### Completed state

Reduce the introductory section to make room for results. Keep a compact source summary above the workspace. Show the source filename or webpage title, the conversion status, and any review notice.

Use two equal columns at widths of 1024px and above: Markdown editor on the left and rendered preview on the right. Each pane has its own visible label and scrolling area. Do not force synchronized scrolling in the first release.

Put “Copy Markdown” and “Download .md” in the results toolbar. Copy is the primary action once conversion completes. “Convert another” is a quiet secondary action. Preserve edits until the user explicitly starts over; confirm only when that action would discard edited output.

### Responsive behavior

| Viewport | Layout |
| --- | --- |
| Below 640px | Single column, full-width primary action, wrapping toolbar, compact intro |
| 640px to 1023px | Single workspace pane with Markdown and Preview tabs |
| 1024px and above | Editor and preview side by side |

On mobile, default the result to Markdown and provide a Preview tab. Keep the result actions close to the result heading. Avoid a sticky footer that hides content behind the on-screen keyboard. Wide tables and code blocks scroll inside their pane; the page itself must not overflow horizontally.

## 7. Components

### Input tabs

Use a horizontal row with text labels, a 2px active underline, and visible keyboard focus. Implement tablist, tab, and tabpanel semantics with arrow-key navigation. Use both weight and underline to communicate selection.

### PDF upload

Use a large bordered drop zone with a simple document icon, “Drop a PDF here”, and a visible “Choose PDF” button. Drag-over uses the hover surface and stronger border. The file picker remains available to keyboard and touch users.

After selection, replace the empty prompt with the filename, file size, a document icon, and “Remove”. Show accepted type and configured limits beneath the field. Limits must come from backend configuration, not invented UI values. Reject unsupported files with a specific message.

### Website input

Use a persistent “Webpage URL” label and a 48px-high URL field. Placeholder: `https://example.com/article`. Helper: “Enter one public webpage URL.” Validate HTTP or HTTPS and require a hostname. Explain unsupported private or login-protected pages in ordinary language.

### Plain text input

Use a labeled textarea, minimum height 220px, plus “Upload .txt”. Show a character count and the configured input limit. Empty or whitespace-only content is invalid. If an uploaded file would overwrite an existing draft, ask before replacing it.

### Buttons

- Primary: ink background, canvas label, 8px radius, at least 44px height.
- Hover: slightly lighten the dark fill; maintain text contrast.
- Secondary: transparent background, control-border outline, ink label.
- Quiet action: underlined text where appropriate, visible focus, generous hit area.
- Disabled: muted surface and text with a clear adjacent explanation when necessary.
- Loading: small spinner and a specific label, preserving button width.

Only one primary action per active stage: Convert before processing, Copy after completion.

### Editor and preview

CodeMirror uses a light theme matching the surface tokens, line wrapping, and restrained syntax colors. Preserve normal keyboard selection and copy behavior. Provide a way to move focus out of the editor using keyboard navigation.

Preview requirements:

- Consistent heading hierarchy, lists, blockquotes, links, tables, and code blocks.
- Tables have clear headers, cell padding, and subtle row separators.
- Code blocks use surface-muted with local horizontal scrolling.
- Links are underlined and have visible focus.
- Untrusted raw HTML and unsafe URL schemes are not rendered as executable content.
- Export and copy use the current editor value, never stale original output.

## 8. Processing and feedback states

| State | Display | Behavior |
| --- | --- | --- |
| Empty | Input prompt and helper text | Conversion unavailable until valid input exists |
| Ready | Selected source and enabled Convert | Submit once |
| Uploading | “Uploading your PDF…” | Show percentage only when measurable |
| Processing | “Reading your PDF…”, “Reading the webpage…”, or “Structuring your text…” | Disable duplicate submission; poll job status |
| OCR | “Reading scanned pages…” | Display only when backend reports this stage |
| Complete | “Your Markdown is ready.” | Enable editor, copy, and download |
| Needs review | “Some content needs review.” with specific details | Keep successful output accessible |
| Failed | Specific explanation and Retry | Preserve input |
| Interrupted | “This conversion was interrupted. Please try again.” | End polling and offer retry |
| Copied | Button briefly reads “Copied” | Announce success without moving focus |

Do not display fabricated progress percentages or unsupported time estimates. A temporary network failure should say “Reconnecting…”; it should not immediately claim the conversion failed. Use bounded retries and distinguish missing or expired jobs from connectivity problems.

Clipboard failure: “Could not copy automatically. Select the Markdown and copy it.” Keep output selectable. Empty extraction must be reported explicitly rather than shown as a successful blank result.

## 9. Accessibility and motion

- Target WCAG 2.2 AA: 4.5:1 for normal text, 3:1 for large text and essential control indicators.
- Add a 2px focus outline with 2px offset to interactive controls.
- All inputs have persistent labels; associate errors using aria-describedby.
- Announce processing and copy success with aria-live="polite". Use role="alert" for actionable errors.
- Support keyboard-only operation, 200% zoom, and a 320px viewport.
- Touch targets are at least 44 by 44px.
- Use semantic landmarks and one page-level h1.
- Transitions last approximately 150ms and affect colors or opacity only.
- Respect prefers-reduced-motion. Disable decorative motion and replace animated status with static text where appropriate.

## 10. Content rules

Use short, direct language. Say what happened and what the user can do next. Avoid claims such as “perfect conversion”, “supports every file”, and “100% accurate”.

Never expose framework names or deployment details in normal product screens. Only state upload retention or privacy guarantees when implemented and verified. Keep source documents available during review where the implementation permits it, and clearly flag any missing or uncertain content.

## 11. Implementation contract

Suggested React components: AppShell, ConverterTabs, PdfUpload, WebsiteInput, PlainTextInput, ConversionStatus, ReviewNotice, ResultToolbar, MarkdownEditor, MarkdownPreview, and InlineError.

Centralize colors, spacing, radii, and typography as semantic theme tokens mapped into Tailwind. Components must not invent local palette values. Keep conversion state separate from editor state so polling cannot overwrite user edits.

The frontend uses same-origin /api requests. FastAPI serves the compiled frontend/dist build on Render. No cross-origin API deployment is required. FastAPI BackgroundTasks are in-process and can be interrupted; the interface must support that limitation. Do not add a queue dashboard, sign-in UI, pricing, or history navigation to this release.

## 12. Design acceptance checklist

- All three inputs work with mouse, keyboard, and touch.
- PDF and TXT restrictions are accurately represented.
- Desktop results show editor and preview together; mobile results are easy to switch.
- Input drafts survive tab changes and recoverable errors.
- Long URLs, filenames, tables, and code do not break layout.
- Processing, OCR, review, failure, reconnecting, and interrupted states are covered.
- Copy and download reflect user edits exactly.
- Input limits and privacy statements match backend behavior.
- Focus, contrast, screen-reader labels, zoom, and reduced motion are checked.
- The visual result uses a warm canvas, dark typography, restrained accents, and generous spacing consistently.

This specification defines the app's own design system inspired by the reference. It is an implementation handoff, not a record of a built or tested interface.
