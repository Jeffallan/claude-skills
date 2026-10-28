// og:image cards with astro-og-canvas: one 1200×630 PNG per page at <base>/og/<page>.png.
// The logo is a lockup of the monogram (site-style) and the site name, drawn once per build.
// A site's src/pages/og/[...route].ts:
//
//   import { getCollection } from 'astro:content';
//   import { docsPages, ogRoute } from '../../components/site-seo/og.mjs';
//   export const { getStaticPaths, GET } = await ogRoute({
//     name: 'Claude Skills',
//     pages: docsPages(await getCollection('docs')),
//   });
//
// Needs astro-og-canvas, @fontsource/outfit and @fontsource/source-sans-3 in the site.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { OGImageRoute } from 'astro-og-canvas';

import { LOCKUP_FONT, cardOptions } from './card.mjs';

// Astro builds from the site folder; the fonts and the monogram are read from there
const root = process.cwd();
const require = createRequire(path.join(root, 'package.json'));
const MONOGRAM = path.join(root, 'public', 'site-style', 'monogram.png');

async function drawLockup(name, file) {
  const CanvasKitInit = require('canvaskit-wasm');
  const CK = await CanvasKitInit({
    locateFile: (f) => require.resolve(`canvaskit-wasm/bin/${f}`),
  });
  const fonts = CK.TypefaceFontProvider.Make();
  fonts.registerFont(fs.readFileSync(path.join(root, LOCKUP_FONT)), 'Lockup');
  const builder = CK.ParagraphBuilder.MakeFromFontProvider(
    new CK.ParagraphStyle({
      textStyle: { color: CK.Color(230, 241, 243, 1), fontFamilies: ['Lockup'], fontSize: 44 },
    }),
    fonts,
  );
  builder.addText(name);
  const text = builder.build();
  text.layout(2000);

  const size = 96;
  const gap = 28;
  const surface = CK.MakeSurface(size + gap + Math.ceil(text.getMaxIntrinsicWidth()), size);
  const canvas = surface.getCanvas();
  canvas.clear(CK.TRANSPARENT);
  const mark = CK.MakeImageFromEncoded(fs.readFileSync(MONOGRAM));
  canvas.drawImageRect(
    mark,
    CK.XYWHRect(0, 0, mark.width(), mark.height()),
    CK.XYWHRect(0, 0, size, size),
    new CK.Paint(),
  );
  canvas.drawParagraph(text, size + gap, (size - text.getHeight()) / 2);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, surface.makeImageSnapshot().encodeToBytes());
}

/** The site's lockup PNG, drawn on first use in a build. */
export async function lockup(name) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const file = path.join(root, 'node_modules', '.cache', 'site-seo', `lockup-${slug}.png`);
  if (!fs.existsSync(file)) await drawLockup(name, file);
  return file;
}

/** Starlight docs entries as { id: { title, description } }; skill pages use their sidebar label. */
export function docsPages(entries) {
  return Object.fromEntries(
    entries.map(({ id, data }) => [
      id || 'index',
      { title: data.sidebar?.label ?? data.title, description: data.description },
    ]),
  );
}

/** getStaticPaths and GET for src/pages/og/[...route].ts. pages: { key: { title, description } }. */
export async function ogRoute({ name, pages }) {
  const logo = await lockup(name);
  return OGImageRoute({
    param: 'route',
    pages,
    getImageOptions: (_path, page) => cardOptions({ ...page, logo }),
  });
}
