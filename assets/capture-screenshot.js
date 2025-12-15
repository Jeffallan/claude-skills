const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  await page.setViewport({ width: 1280, height: 640 });

  const htmlPath = path.join(__dirname, 'social-preview.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

  // Wait for fonts to load
  await new Promise(resolve => setTimeout(resolve, 2000));

  await page.screenshot({
    path: path.join(__dirname, 'social-preview.png'),
    type: 'png',
    clip: { x: 0, y: 0, width: 1280, height: 640 }
  });

  console.log('Screenshot saved to assets/social-preview.png');
  await browser.close();
})();
