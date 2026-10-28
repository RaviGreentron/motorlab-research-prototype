/** Run with NODE_PATH pointing to a directory containing playwright, or install it locally. */
import {createRequire} from 'node:module';
import {writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('playwright');
const base=process.env.MOTORLAB_URL||'http://127.0.0.1:8765';
const output=path.resolve(process.env.MOTORLAB_E2E_OUTPUT||'../../data/ui-verification');
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
page.setDefaultTimeout(90000);
const errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
async function check(name,fn){try{await fn();checks.push({name,status:'PASS'})}catch(e){checks.push({name,status:'FAIL',error:e.message});throw e}}
try{
 await check('Dashboard loads real experiment',async()=>{await page.goto(base);await page.locator('h1').filter({hasText:'Overview'}).waitFor();await page.getByLabel('Motor',{exact:true}).waitFor();if((await page.getByLabel('Motor',{exact:true}).locator('option').count())<1)throw Error('No motors');});
 const nav=page.getByRole('navigation',{name:'Main navigation'});
 await check('Create immutable experiment with seed 43',async()=>{await nav.getByRole('button',{name:'Study configuration',exact:true}).click();await page.getByLabel('Random seed',{exact:true}).fill('43');const created=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/api/v1/runs'));await page.getByRole('button',{name:'Run experiment →',exact:true}).click();const response=await created;const body=await response.json();if(response.status()!==201||body.config.seed!==43)throw Error('Experiment not created with requested seed');await page.locator('h1').filter({hasText:'Overview'}).waitFor();});
 for(const name of ['Waveform analysis','Anomaly investigation','Predictive outlook','Model comparison','Maintenance review','Study configuration','Data quality','Overview']){
  await check(`Navigation: ${name}`,async()=>{await nav.getByRole('button',{name,exact:true}).click();await page.locator('h1').filter({hasText:name}).waitFor();});
 }
 await check('Forecast has temperature units and minute cadence',async()=>{await nav.getByRole('button',{name:'Predictive outlook',exact:true}).click();await page.getByRole('heading',{name:'Temperature outlook',exact:true}).waitFor();await page.getByRole('img',{name:'Temperature / °C by Elapsed time / min',exact:true}).waitFor();await page.getByRole('img',{name:'MAE / °C by Horizon / min',exact:true}).waitFor();});
 await check('Waveform selected record is fetched',async()=>{await nav.getByRole('button',{name:'Waveform analysis',exact:true}).click();const response=page.waitForResponse(r=>r.url().includes('/waveform?')&&r.url().includes('index=170'));await page.getByLabel('Window index',{exact:true}).fill('170');if(!(await response).ok())throw Error('Selected waveform request failed');await page.getByRole('img',{name:'Current / A by Time / seconds',exact:true}).waitFor();});
 await check('Invalid record clears derived spectrum',async()=>{const response=page.waitForResponse(r=>r.url().includes('/waveform?')&&r.url().includes('index=195'));await page.getByLabel('Window index',{exact:true}).fill('195');const body=await(await response).json();if(body.quality.valid)throw Error('Expected dropout rejection');await page.getByText('UNASSESSABLE',{exact:true}).waitFor();const card=page.locator('section').filter({has:page.getByRole('heading',{name:'Current spectrum',exact:true})});await card.getByText('No valid observations available for this chart.',{exact:true}).waitFor();if(await card.locator('polyline').count())throw Error('Invalid spectrum still plotted');});
 await check('Annotation saves and persists across refresh',async()=>{await nav.getByRole('button',{name:'Anomaly investigation',exact:true}).click();const text=`UI verification ${new Date().toISOString()}`;await page.getByLabel('Research note',{exact:true}).fill(text);const saved=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/notes'));await page.getByRole('button',{name:'Save annotation',exact:true}).click();if(!(await saved).ok())throw Error('Save rejected');await page.getByText(text,{exact:true}).waitFor();await page.reload();await page.getByLabel('Motor',{exact:true}).waitFor();await nav.getByRole('button',{name:'Anomaly investigation',exact:true}).click();await page.getByText(text,{exact:true}).waitFor();});
 await check('Study export is valid report',async()=>{const href=await page.getByRole('link',{name:'↓ Export study'}).getAttribute('href');const r=await page.request.get(new URL(href,base).href);const result=await r.json();if(!r.ok()||!result.run_id||!result.motors?.length)throw Error('Export invalid');});
 await check('Responsive mobile navigation',async()=>{await page.setViewportSize({width:390,height:844});await nav.getByRole('button',{name:'Overview',exact:true}).click();await page.locator('h1').filter({hasText:'Overview'}).waitFor();await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});});
 await page.setViewportSize({width:1440,height:1000});
 await page.screenshot({path:path.join(output,'overview.png'),fullPage:true});
 if(errors.length)throw Error(`Browser errors: ${errors.join('; ')}`);
}catch(e){console.error(e);process.exitCode=1}
finally{await writeFile(path.join(output,'e2e-results.json'),JSON.stringify({base,checks,browser_errors:errors,created_at:new Date().toISOString()},null,2));await browser.close();console.log(JSON.stringify(checks));}
