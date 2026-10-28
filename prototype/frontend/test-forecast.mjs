import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const output=path.resolve(process.env.MOTORLAB_E2E_OUTPUT||'../../data/qa');
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
const page=await browser.newPage({viewport:{width:1440,height:1100}}),checks=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
async function check(name,fn){try{await fn();checks.push({name,status:'PASS'})}catch(e){checks.push({name,status:'FAIL',error:e.message});throw e}}
try{
 await page.goto(process.env.MOTORLAB_URL||'http://127.0.0.1:8765');
 await page.getByLabel('Motor',{exact:true}).waitFor();
 const report=await(await page.request.get(new URL('/api/v1/runs/latest',page.url()).href)).json();
 const nav=page.getByRole('navigation',{name:'Main navigation'});
 await nav.getByRole('button',{name:'Predictive outlook',exact:true}).click();
 await check('Temperature metadata maps to °C and minute axes',async()=>{
  if(report.forecast.feature!=='temperature_degC'||report.forecast.cadence_seconds!==60)throw Error('This semantic regression fixture requires temperature_degC at 60 s cadence');
  await page.getByRole('heading',{name:'Temperature outlook',exact:true}).waitFor();
  await page.getByRole('img',{name:'Temperature / °C by Elapsed time / min',exact:true}).waitFor();
  await page.getByRole('img',{name:'MAE / °C by Horizon / min',exact:true}).waitFor();
  if(await page.locator('.metric small').filter({hasText:'°C'}).count()!==2)throw Error('Both MAE and RMSE must carry °C');
 });
 await check('Forecast and horizon endpoints reflect cadence',async()=>{
  const forecast=page.getByRole('img',{name:'Temperature / °C by Elapsed time / min',exact:true});
  const end=((report.forecast.history.length+report.forecast.models.linear.forecast.length-1)*report.forecast.cadence_seconds/60).toFixed(1);
  if(await forecast.locator('text').last().textContent()!==end)throw Error('Forecast endpoint does not match elapsed minutes');
  const horizon=page.getByRole('img',{name:'MAE / °C by Horizon / min',exact:true});
  const h=(report.forecast.models.linear.mae_by_horizon.length*report.forecast.cadence_seconds/60).toFixed(1);
  if(await horizon.locator('text').last().textContent()!==h)throw Error('Horizon endpoint does not match minutes ahead');
 });
 await check('Forecast method change preserves physical units',async()=>{await page.getByLabel('Forecast model',{exact:true}).selectOption('robust');await page.getByRole('img',{name:'Temperature / °C by Elapsed time / min',exact:true}).waitFor();await page.getByLabel('Forecast model',{exact:true}).selectOption('linear');});
 await page.screenshot({path:path.join(output,'forecast.png'),fullPage:true});
 await check('Comparison metrics carry forecast units',async()=>{await nav.getByRole('button',{name:'Model comparison',exact:true}).click();await page.getByRole('columnheader',{name:'MAE / °C',exact:true}).waitFor();await page.getByRole('columnheader',{name:'RMSE / °C',exact:true}).waitFor();await page.getByRole('columnheader',{name:'Bias / °C',exact:true}).waitFor();});
 await check('Anomaly timeline explicitly uses logarithmic transformation',async()=>{await nav.getByRole('button',{name:'Overview',exact:true}).click();const chart=page.getByRole('img',{name:'log10(1 + score / threshold) by Window',exact:true});await chart.waitFor();if(await chart.locator('polyline').count()!==3)throw Error('Expected all three model traces');await page.getByText(/Timeline uses log10\(1 \+ score \/ threshold\).*without clipping/).waitFor();});
 await page.screenshot({path:path.join(output,'overview.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
 if(errors.length)throw Error(errors.join('; '));
}catch(e){console.error(e);process.exitCode=1}
finally{await writeFile(path.join(output,'forecast-e2e-results.json'),JSON.stringify({checks,browser_errors:errors,created_at:new Date().toISOString()},null,2));await browser.close();console.log(JSON.stringify(checks));}
