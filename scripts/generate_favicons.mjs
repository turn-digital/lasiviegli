// Ģenerē favikonus visos formātos no "Aa" flīzes dizaina.
//
//   node scripts/generate_favicons.mjs
//
// Izveido public/: favicon.svg, favicon.ico (16+32+48), apple-touch-icon.png (180),
// icon-192.png, icon-512.png, site.webmanifest

import sharp from 'sharp';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const PUBLIC = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'public');

// rx — stūru rādiuss 32px koordinātēs; pārlūka favikonam noapaļots,
// apple-touch-icon un PWA ikonām pilns kvadrāts (iOS/Android maskē paši)
const tile = (rx) => `<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" rx="${rx}" fill="#9E3039"/>
  <text x="16" y="22" text-anchor="middle"
    font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700"
    fill="#fff">Aa</text>
</svg>`;

const png = (svg, size) =>
  sharp(Buffer.from(svg), { density: (72 * size) / 32 }).resize(size, size).png().toBuffer();

// ICO konteiners ar iegultiem PNG (derīgs no Windows Vista)
function packIco(images) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0); // rezervēts
  header.writeUInt16LE(1, 2); // tips: ikona
  header.writeUInt16LE(images.length, 4);

  const entries = [];
  let offset = 6 + images.length * 16;
  for (const { size, buf } of images) {
    const e = Buffer.alloc(16);
    e.writeUInt8(size >= 256 ? 0 : size, 0); // platums
    e.writeUInt8(size >= 256 ? 0 : size, 1); // augstums
    e.writeUInt8(0, 2); // krāsu palete
    e.writeUInt8(0, 3); // rezervēts
    e.writeUInt16LE(1, 4); // krāsu plaknes
    e.writeUInt16LE(32, 6); // biti uz pikseli
    e.writeUInt32LE(buf.length, 8);
    e.writeUInt32LE(offset, 12);
    entries.push(e);
    offset += buf.length;
  }
  return Buffer.concat([header, ...entries, ...images.map((i) => i.buf)]);
}

const rounded = tile(6);
const square = tile(0);

writeFileSync(path.join(PUBLIC, 'favicon.svg'), rounded + '\n');

const icoImages = [];
for (const size of [16, 32, 48]) {
  icoImages.push({ size, buf: await png(rounded, size) });
}
writeFileSync(path.join(PUBLIC, 'favicon.ico'), packIco(icoImages));

writeFileSync(path.join(PUBLIC, 'apple-touch-icon.png'), await png(square, 180));
writeFileSync(path.join(PUBLIC, 'icon-192.png'), await png(square, 192));
writeFileSync(path.join(PUBLIC, 'icon-512.png'), await png(square, 512));

writeFileSync(
  path.join(PUBLIC, 'site.webmanifest'),
  JSON.stringify(
    {
      name: 'Lasi viegli',
      short_name: 'Lasi viegli',
      icons: [
        { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
      ],
      theme_color: '#9E3039',
      background_color: '#f8f6f3',
    },
    null,
    2,
  ) + '\n',
);

console.log('OK: favicon.svg, favicon.ico, apple-touch-icon.png, icon-192/512.png, site.webmanifest');
