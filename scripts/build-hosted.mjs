import fs from 'node:fs/promises';
const types={'index.html':'text/html; charset=utf-8','app.mjs':'text/javascript; charset=utf-8','engine.mjs':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8'};
const assets={};for(const [name,type]of Object.entries(types))assets['/'+name]={body:await fs.readFile('dist/'+name,'utf8'),type};
const contract=(await fs.readFile('worker/connector-contract.mjs','utf8')).replaceAll('export ','');
const handler=(await fs.readFile('worker/handler.mjs','utf8')).replace(/^import[^\n]+\n/,'').replaceAll('export ','');
await fs.mkdir('dist/server',{recursive:true});await fs.mkdir('dist/.openai',{recursive:true});
await fs.writeFile('dist/server/index.js',contract+'\n'+handler+'\nexport default createWorker('+JSON.stringify(assets)+');\n');
await fs.copyFile('.openai/hosting.json','dist/.openai/hosting.json');
console.log('Hosted Worker built with request-scoped read-only Gmail access. No account data embedded.');
