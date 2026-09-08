/* Integration QA against generated original output, never edits the app. */
const { chromium } = require(process.env.NETWORK_PLAYWRIGHT || 'C:/Users/kcg51/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'), path=require('path'), assert=require('assert');
(async()=>{
const base=process.argv[2]||'http://127.0.0.1:8876';
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const errors=[];
try{
for(const [width,scheme] of [[1440,'light'],[1024,'dark'],[740,'light'],[360,'dark']]){
const page=await browser.newPage({viewport:{width,height:1000},colorScheme:scheme});
page.on('pageerror',e=>errors.push(e.message));
await page.goto(base+'/causal-network.html',{waitUntil:'load'});
await page.locator('#graph canvas').first().waitFor();
await page.selectOption('#node-picker','lt-rate');await page.click('#focus');
await page.locator('#detail').getByRole('heading',{name:'장기국채금리',exact:true}).waitFor();
assert.match(await page.locator('#graph-status').innerText(),/연결/);
await page.selectOption('#view','all');
await page.check('#show-rejected');
assert((await page.locator('#edge-list button').count())>200);
await page.locator('#results button').first().click();
assert((await page.locator('#detail').innerText()).includes('시계열'));
await page.fill('#q','0.1');await page.fill('#reason','브라우저 검증용 민감도 비교');await page.click('#apply');
assert((await page.locator('#feedback').innerText()).includes('초안'));
await page.reload({waitUntil:'load'});assert.strictEqual(await page.inputValue('#q'),'0.1');
await page.click('#restore');assert.strictEqual(await page.inputValue('#q'),'0.05');
const dl=page.waitForEvent('download');await page.click('#export-report');const file=await dl;assert(file.suggestedFilename().startsWith('causal-report-'));
assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
await page.evaluate(()=>scrollTo(0,0));
fs.mkdirSync('artifacts/causal-network',{recursive:true});await page.screenshot({path:`artifacts/causal-network/${width}-${scheme}.png`,fullPage:false});
console.log(JSON.stringify({width,scheme,graph:true,interaction:true,overflow:false}));
await page.close();
}
const page=await browser.newPage();await page.goto(base+'/index.html#search?q='+encodeURIComponent('시계열'),{waitUntil:'load'});
await page.locator('#searchMacro a[href="causal-network.html"]').waitFor();
await page.goto(base+'/macro.html',{waitUntil:'load'});await page.locator('a[href="causal-network.html"]').waitFor();
assert.deepStrictEqual(errors,[]);console.log('Search, return navigation, JS errors: PASS');
}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
