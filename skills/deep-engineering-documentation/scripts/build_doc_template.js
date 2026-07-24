/**
 * docx-js assembly template for deep-engineering-documentation.
 *
 * Requires the `docx` npm package. If `require('docx')` fails to resolve in
 * your environment, try setting NODE_PATH to your global node_modules dir, e.g.:
 *   NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules node build_doc.js
 *
 * Page: 12240x15840 DXA (US Letter) with 720 DXA margins on each side =>
 * usable width ~10800 DXA. EVERY table's column widths must sum to <= that,
 * or the rightmost column(s) render cut off in Word/LibreOffice.
 *
 * Diagram placement rule: keep every diagram in the Appendix only (Section 16
 * below). Do NOT also embed it inline in Section 8 — reference it instead with
 * a one-line "See the Appendix for its sequence diagram." in that entry
 * point's Summary paragraph.
 */

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, ImageRun, PageBreak, VerticalAlign, BorderStyle,
} = require("docx");

const NAVY = "1a1a2e";
const ACCENT = "2b4c7e";
const GREY = "555555";
const DIAG = "./diagrams"; // wherever gen_diagrams_template.py wrote its PNGs

// ---------- helpers ----------
function h1(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 420, after: 200 } }); }
function h2(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 150 } }); }
function h3(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 220, after: 110 } }); }
function p(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 160 } });
}
function bullet(text, level = 0) {
  return new Paragraph({ text, bullet: { level }, spacing: { after: 90 } });
}
function numbered(items) {
  return items.map((text, i) => new Paragraph({
    children: [new TextRun({ text: `${i + 1}. `, bold: true }), new TextRun({ text })],
    spacing: { after: 110 },
    indent: { left: 360 },
  }));
}
function fieldLine(label, value) {
  return new Paragraph({
    children: [new TextRun({ text: label + ": ", bold: true, color: ACCENT }), new TextRun({ text: value })],
    spacing: { after: 60 },
  });
}
function note(text) {
  // Use for confirmed findings that need visual emphasis (bugs, security gaps).
  return new Paragraph({
    children: [new TextRun({ text: "⚠ " + text, italics: true, color: "8a1f1f" })],
    spacing: { before: 100, after: 200 },
    shading: { type: ShadingType.CLEAR, fill: "FBEAEA" },
  });
}
function verify(text) {
  // Use ONLY for claims that could not be settled by static reading alone —
  // pairs with Section 15 (Manual Verification Items). Do not use `note()`
  // for these; keeping the two visually distinct preserves the
  // confirmed-vs-flagged distinction that makes the document trustworthy.
  return new Paragraph({
    children: [new TextRun({ text: "✓ Manual verification suggested: " + text, italics: true, color: "1f5a1f" })],
    spacing: { before: 80, after: 160 },
    shading: { type: ShadingType.CLEAR, fill: "EAF7EC" },
  });
}
function cell(text, { header = false, width, shade } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: ACCENT } : (shade ? { type: ShadingType.CLEAR, fill: shade } : undefined),
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({ text: String(text), bold: header, color: header ? "FFFFFF" : "1a1a2e", size: header ? 19 : 17 })],
    })],
  });
}
function makeTable(headers, rows, colWidths) {
  // colWidths MUST sum to <= ~10800 for the page setup below. Check before running.
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((hd, i) => cell(hd, { header: true, width: colWidths[i] })) }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, i) => cell(c, { width: colWidths[i], shade: ri % 2 ? "F5F8FC" : undefined })),
      })),
    ],
  });
}
function imagePara(path, width, height) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 200 },
    children: [new ImageRun({ data, transformation: { width, height }, type: "png" })],
  });
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }
function divider() {
  return new Paragraph({ border: { bottom: { color: "CCCCCC", space: 1, style: BorderStyle.SINGLE, size: 6 } }, spacing: { after: 200 } });
}

const children = [];

// ---------- Header block ----------
children.push(
  new Paragraph({ text: "", spacing: { before: 600 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "SYSTEM NAME HERE", bold: true, size: 50, color: NAVY })], spacing: { after: 160 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Engineering Documentation", bold: true, size: 30, color: ACCENT })], spacing: { after: 500 } }),
  divider(),
  fieldLine("Document Type", "Engineering / Architecture Documentation"),
  fieldLine("System", "TODO"),
  fieldLine("Module / Entry Points Covered", "TODO"),
  fieldLine("Source", "TODO"),
  fieldLine("Document Version", "1.0"),
  fieldLine("Documentation Scope", "TODO — state explicitly what's included/excluded and why (near-duplicates, dead code, etc.)"),
  fieldLine("Prepared For", "TODO"),
  fieldLine("Date", "TODO"),
  divider(),
  p("This document was produced by direct source-code trace rather than by inference from naming conventions. Every behavioral claim was confirmed by reading the referenced file. Where behavior could not be settled from static reading alone, this is stated explicitly under a Manual Verification callout rather than asserted as fact.", { italics: true, color: GREY }),
  pageBreak(),
);

// ---------- 1-7: overview sections (fill in per system) ----------
children.push(h1("1. System Overview"), p("TODO"));
children.push(h1("2. Business Responsibilities"), bullet("TODO"));
children.push(h1("3. High-Level Architecture"), p("TODO"), makeTable(["Layer", "Responsibility", "Representative code"], [["TODO", "TODO", "TODO"]], [2600, 3800, 3400]));
children.push(h1("4. External Integrations"), makeTable(["Integration", "Direction", "Used by", "Purpose"], [["TODO", "TODO", "TODO", "TODO"]], [2600, 1600, 2500, 3100]));
children.push(h1("5. Persistence Overview"), p("TODO"));
children.push(pageBreak(), h1("6. Endpoint/Entry-Point Summary"), makeTable(["Entry point", "Transport", "Protocol", "Auth", "Direction"], [["TODO", "TODO", "TODO", "TODO", "TODO"]], [1500, 1700, 2600, 2600, 2800]));

// ---------- 8. Per-entry-point sections (repeat this block per endpoint) ----------
children.push(pageBreak(), h1("7. API Documentation"));
children.push(
  h2("7.1 ENTRY POINT NAME"),
  h3("API Overview"), p("TODO"),
  h3("High-Level Flow"), p("TODO — prose only; do not embed the diagram here, it lives in the Appendix."),
  h3("Detailed Code Flow"), ...numbered(["TODO step 1", "TODO step 2"]),
  h3("Database Interactions"), makeTable(["Store", "Operation", "When"], [["TODO", "TODO", "TODO"]], [2900, 4200, 3500]),
  h3("Business Logic"), bullet("TODO"),
  h3("Security & Validation"), bullet("TODO"),
  h3("External Integrations"), bullet("TODO"),
  h3("Exception Handling"), makeTable(["Scenario", "Handling"], [["TODO", "TODO"]], [3300, 6900]),
  h3("Performance Notes"), bullet("TODO"),
  h3("Response Structure"), p("TODO"),
  h3("Summary"), p("TODO. See the Appendix for its sequence diagram."),
);

// ---------- 9-15: cross-cutting sections ----------
children.push(pageBreak(), h1("8. Cross-Cutting Runtime Architecture"), p("TODO"));
children.push(pageBreak(), h1("9. Cross-Cutting Database Design"), p("TODO"));
children.push(pageBreak(), h1("10. Cross-Cutting Security"), h2("Authentication"), p("TODO"), h2("Authorization"), p("TODO"), h2("Rate Limiting"), p("TODO"), h2("Cryptographic Verification"), p("TODO"), h2("Session Handling"), p("TODO"));
children.push(pageBreak(), h1("11. Exception Handling Strategy"), makeTable(["Entry point", "Scenario", "Handling"], [["TODO", "TODO", "TODO"]], [1800, 3400, 4100]));
children.push(pageBreak(), h1("12. Performance Considerations"), bullet("TODO"));
children.push(pageBreak(), h1("13. Risks & Limitations"), ...numbered(["TODO"]));
children.push(pageBreak(), h1("14. Manual Verification Items"), p("Every item below was identified through direct source-code reading but could not be fully settled by static analysis alone."), verify("TODO"));

// ---------- 16. Appendix (ALL diagrams live here, only here) ----------
children.push(
  pageBreak(), h1("15. Appendix"),
  h2("15.1 Component Diagram"), imagePara(`${DIAG}/component_diagram.png`, 610, 405),
  pageBreak(), h2("15.2 Sequence Diagrams"),
  h3("ENTRY POINT NAME"), imagePara(`${DIAG}/seq_example.png`, 600, 348),
);

// ---------- Business Rules Reference ----------
children.push(
  pageBreak(), h1("Business Rules Reference"),
  p("Consolidated list of every business rule / derivation confirmed across the system:"),
  ...numbered(["TODO"]),
  new Paragraph({ text: "", spacing: { before: 400 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "End of Document.", bold: true, italics: true, color: GREY })] }),
);

// ---------- build ----------
const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 900, bottom: 900, left: 720, right: 720 } } },
    children,
  }],
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("./Engineering_Documentation.docx", buf);
  console.log("written, bytes:", buf.length);
});
