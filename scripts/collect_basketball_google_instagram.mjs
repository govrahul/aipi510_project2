/** Public browser workflow used November 3, 2026.
 * Import/copy these functions into the authorized CUA runtime with an existing
 * Chrome tab. This module launches no browser and reads no cookies, application
 * state, private API, feeds, DMs, or follower-list contents. No account guessing.
 *
 * 1. Draw/freeze TOP 1000 first (prepare_basketball_top1000_social.py).
 * 2. Run googleLookups(tab, [[Sample_Row, playerName, school], ...]).
 * 3. Open first Instagram result. For school/team posts, review the named
 *    athlete's tags/coauthors; use the visible Tagged users control if needed.
 *    Reject an unrelated first result; never assume a handle from spelling.
 * 4. Read sourced profile URLs with readProfiles. Review identity manually.
 * 5. Export selected count receipts and identity evidence, then run the offline
 *    finalizer. Leave unavailable accounts missing in the original 100 rows.
 *
 * Keep batches short. Stop for login, CAPTCHA, challenge, or rate limiting;
 * do not solve/bypass them. Never persist unrelated comments/account details.
 */
export async function googleLookups(tab,jobs) {
  const records=[];
  for(const [Sample_Row,name,school] of jobs) {
    const query=name+' '+school+' instagram';
    const target='https://www.google.com/search?q='+encodeURIComponent(query);
    if(await tab.url()!==target)await tab.goto(target);
    try {await tab.playwright.locator('a[href*="instagram.com"] h3').first().waitFor({state:'visible',timeoutMs:8000});}catch{}
    const result=await tab.playwright.evaluate(()=>({
      url:location.href,
      results:Array.from(document.querySelectorAll('a[href]')).filter(a=>{
        try{return /(^|\.)instagram.com$/.test(new URL(a.href).hostname)&&a.querySelector('h3')&&a.getBoundingClientRect().height>0;}catch{return false;}
      }).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top).slice(0,4)
        .map(a=>({url:a.href,title:a.querySelector('h3').innerText}))
    }));
    if(result.url.includes('/sorry/'))throw Error('Google challenge: stop collection');
    records.push({Sample_Row,name,school,query,retrieved_at:new Date().toISOString(),...result});
  }
  return records;
}

export function readCountDom() {
  const f=Array.from(document.querySelectorAll('a')).find(a=>/^\s*[\d,.]+\s*[KMB]?\s+followers\s*$/i.test(a.innerText));
  return {url:location.href,
    challenge:/\/(challenge|checkpoint|accounts)\//.test(location.pathname)||!!document.querySelector('iframe[src*="captcha"],iframe[src*="challenge"]'),
    followerLinks:f?[{href:f.href,text:f.innerText,title:f.title,spans:Array.from(f.querySelectorAll('[title]')).map(s=>s.title)}]:[]};
}

export async function readProfiles(tab,jobs) {
  const observations=[];
  for(const [Sample_Row,url] of jobs) {
    const u=new URL(url);
    if(u.hostname!=='www.instagram.com'||!/^\/[A-Za-z0-9_.]+\/(reels\/)?$/.test(u.pathname))throw Error('Use a reviewed profile URL');
    if(await tab.url()!==url)await tab.goto(url);
    try {await tab.playwright.getByRole('link',{name:/^[\d,.KMB]+ followers$/i}).waitFor({state:'visible',timeoutMs:6000});}catch{}
    const snapshot=await tab.playwright.evaluate(readCountDom);
    if(snapshot.challenge)throw Error('Instagram login/challenge: stop collection');
    observations.push({Sample_Row,visited_url:url,retrieved_at:new Date().toISOString(),snapshot});
  }
  return observations;
}

export function exactReceipt(record) {
  if(record.snapshot.followerLinks.length!==1)throw Error('No unique follower label');
  const f=record.snapshot.followerLinks[0],p=new URL(record.snapshot.url),a=new URL(f.href);
  if(p.hostname!=='www.instagram.com'||a.hostname!=='www.instagram.com'||p.pathname.split('/')[1]!==a.pathname.split('/')[1])throw Error('Stale or different profile');
  const labels=[f.title,...f.spans].filter(x=>/^[\d,]+$/.test(x));
  if(!labels.length||new Set(labels).size!==1)throw Error('No unambiguous exact integer tooltip; retain as missing');
  return {Sample_Row:record.Sample_Row,username:p.pathname.split('/')[1],followers:Number(labels[0].replaceAll(',','')),
    raw_label:f.text.replace(/ followers$/i,''),observed_at:record.retrieved_at};
}
