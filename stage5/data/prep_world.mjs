import fs from 'fs';
import {geoNaturalEarth1, geoPath, geoArea} from 'd3-geo';
import {feature} from 'topojson-client';
import polylabel from 'polylabel';
const topo = JSON.parse(fs.readFileSync('node_modules/world-atlas/countries-10m.json'));
const fc = feature(topo, topo.objects.countries);
const feats = fc.features.filter(f => f.id !== '010'); // composition without Antarctica
// some source rings (e.g. Maldives) have the wrong spherical winding and d3 reads them as "whole globe minus island": rewind those
for (const f of feats) if (f.geometry) {
  const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
  for (const p of polys) if (geoArea({type: 'Polygon', coordinates: p}) > 2 * Math.PI) { for (const r of p) r.reverse(); console.log('rewound polygon of', f.id, f.properties.name); }
}
const W0 = 4000;
const proj = geoNaturalEarth1().fitWidth(W0, {type:'FeatureCollection', features: feats});
const [[x0,y0],[x1,y1]] = geoPath(proj).bounds({type:'FeatureCollection', features: feats});
// collect rings through d3's own antimeridian cutting/clipping
function rings(f){ const out=[]; let cur=null, lx, ly;
  const ctx={ moveTo(x,y){ cur=[]; out.push(cur); lx=1e9; this.lineTo(x,y);}, lineTo(x,y){ x=+(x-x0).toFixed(2); y=+(y-y0).toFixed(2); if(Math.hypot(x-lx,y-ly)<0.25) return; cur.push(x,y); lx=x; ly=y; }, closePath(){}, arc(){} };
  geoPath(proj, ctx)(f); return out.filter(r=>r.length>=6); }
const area = r => { let a=0; for(let i=0;i<r.length;i+=2){const j=(i+2)%r.length;a+=r[i]*r[j+1]-r[j]*r[i+1];} return a/2; };
const bb = r => { let b=[1e9,1e9,-1e9,-1e9]; for(let i=0;i<r.length;i+=2){b[0]=Math.min(b[0],r[i]);b[2]=Math.max(b[2],r[i]);b[1]=Math.min(b[1],r[i+1]);b[3]=Math.max(b[3],r[i+1]);} return b; };
function pip(x,y,r){ let c=false; for(let i=0,j=r.length-2;i<r.length;j=i,i+=2){ const xi=r[i],yi=r[i+1],xj=r[j],yj=r[j+1]; if(((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi)) c=!c; } return c; }
const out=[];
for (const f of feats) {
  if (!f.geometry) continue;
  const R = rings(f); if (!R.length) continue;
  // outer rings = sign of the largest ring; holes = opposite sign
  let big = R.reduce((m,r)=>Math.abs(area(r))>Math.abs(area(m))?r:m, R[0]); const sgn = Math.sign(area(big));
  const outers = R.filter(r=>Math.sign(area(r))===sgn), holes = R.filter(r=>Math.sign(area(r))!==sgn);
  const P = outers.map(o=>({r:[o], b:bb(o), a:Math.abs(area(o))}));
  for (const h of holes) { const p = P.find(p=>pip(h[0],h[1],p.r[0])); if (p) p.r.push(h); }
  let mi=0; P.forEach((p,i)=>{ if(p.a>P[mi].a) mi=i; });
  const pl = polylabel(P[mi].r.map(r=>{const a=[];for(let i=0;i<r.length;i+=2)a.push([r[i],r[i+1]]);return a;}), 0.5);
  out.push({id:f.id, name:f.properties.name, polys:P.map(p=>({r:p.r,b:p.b.map(v=>+v.toFixed(1)),a:Math.round(p.a)})), main:mi, label:[+pl[0].toFixed(1),+pl[1].toFixed(1),+pl.distance.toFixed(1)]});
}
const meta = {W:+(x1-x0).toFixed(1), H:+(y1-y0).toFixed(1), projection:'d3.geoNaturalEarth1, fitWidth 4000, Antarctica excluded, antimeridian cut by d3-geo', source:'Natural Earth 1:10m Admin 0 countries via world-atlas@2.0.2 (topojson), public domain'};
fs.writeFileSync('gen/world.js', 'window.WORLD='+JSON.stringify({meta, countries: out})+';');
console.log(meta, out.length, (fs.statSync('gen/world.js').size/1e6).toFixed(1)+'MB');
for (const id of ['124','484','320','840','710','780','140','070','643','242']) { const c=out.find(c=>c.id===id); console.log(id, c.name, c.polys.length, c.polys[c.main].r.length, c.label); }
