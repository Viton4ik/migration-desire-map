// node render/emblem.js -> assets/theme_suitcase.png (transparent, 1024x1024) from assets/theme_suitcase_source.html
const path = require('path'); const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1024, height: 1024 } });
  await p.goto('file://' + path.resolve(__dirname, '../assets/theme_suitcase_source.html'));
  await p.locator('#s').screenshot({ path: path.resolve(__dirname, '../assets/theme_suitcase.png'), omitBackground: true });
  await b.close();
})();
