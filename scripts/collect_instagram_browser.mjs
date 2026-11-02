/** Read public profile labels through an existing, authorized CUA browser tab.
 * Run in the Codex CUA runtime with a bound tab; never reads application state,
 * cookies, private APIs, feeds, messages, or a follower-list dialog. The DOM
 * selectors reflect the visible profile UI observed November 2, 2026. The
 * caller exports the returned selected fields to a local receipt ledger.
 */
export function readProfileDom() {
  return {
    url: location.href,
    title: document.title,
    followerLinks: Array.from(document.querySelectorAll('a'))
      .filter(a => /^\s*[\d,.]+\s*[KMB]?\s+followers\s*$/i.test(a.innerText))
      .map(a => ({text:a.innerText, href:a.href, title:a.title,
        spans:Array.from(a.querySelectorAll('[title]')).map(s=>s.title)})),
    challenge:!!document.querySelector('iframe[src*="captcha"],iframe[src*="challenge"]')
  };
}

export async function collectProfileBatch(tab, jobs) {
  const observations=[];
  for (const [Sample_Row, username] of jobs) {
    if (!/^[A-Za-z0-9_.]{1,30}$/.test(username)) throw Error('Invalid sourced handle');
    const target='https://www.instagram.com/'+username+'/';
    if (await tab.url()!==target) {
      try { await tab.goto(target); }
      catch(e) { if (!String(e).includes('Timed out')) throw e; }
    }
    // Wait on visible profile data, not merely navigation completion: Instagram
    // can initially expose the new URL while still rendering the prior profile.
    try { await tab.playwright.getByRole('link',{
      name:/^\s*[\d,.]+\s*[KMB]?\s+followers\s*$/i
    }).waitFor({state:'visible',timeoutMs:8000}); } catch(e) { /* retain failure */ }
    const snapshot=await tab.playwright.evaluate(readProfileDom);
    const record={Sample_Row,username,retrieved_at:new Date().toISOString(),snapshot};
    observations.push(record);
    if (snapshot.challenge || snapshot.url.includes('/accounts/')) break;
  }
  return observations;
}

export function receiptsCsv(observations) {
  const latest=new Map();
  for (const r of observations) if(r.snapshot.followerLinks.length===1) latest.set(r.Sample_Row,r);
  const quote=x=>'"'+String(x).replaceAll('"','""')+'"';
  return 'Sample_Row,username,retrieved_at,display_label,integer_tooltip\n'+
    Array.from(latest.values()).sort((a,b)=>a.Sample_Row-b.Sample_Row).map(r=>{
      const f=r.snapshot.followerLinks[0];
      const profile=new URL(r.snapshot.url), link=new URL(f.href);
      if(!['instagram.com','www.instagram.com'].includes(profile.hostname) ||
         profile.pathname.replaceAll('/','').toLowerCase()!==r.username.toLowerCase() ||
         !['instagram.com','www.instagram.com'].includes(link.hostname) ||
         ![r.username.toLowerCase(),r.username.toLowerCase()+'/followers'].includes(link.pathname.replace(/^\/|\/$/g,'').toLowerCase()))
        throw Error('Follower label is not attached to the requested profile');
      const tooltips=[f.title,...f.spans].filter(s=>/^[0-9][0-9,]*$/.test(s));
      if(new Set(tooltips).size!==1)throw Error('Missing/ambiguous integer tooltip; retain rounded source separately');
      return [r.Sample_Row,r.username,r.retrieved_at,f.text.replace(/ followers$/i,''),tooltips[0]].map(quote).join(',');
    }).join('\n')+'\n';
}

// Account discovery was performed in the visible Instagram Search input. Search
// results were candidates only: each new accepted handle additionally required
// a matching school basketball tag or an official source explicitly naming the
// account. Reviewed mappings are stored separately from these count receipts.
