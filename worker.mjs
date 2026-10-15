#!/usr/bin/env node
// Offline intake worker: no account access, network calls, email sends or calendar writes.
import fs from 'node:fs';
import path from 'node:path';
import {seed,triage,uid} from './dist/engine.mjs';
const args=process.argv.slice(2);
if(args.length!==2){console.error('Usage: node worker.mjs intake.json workspace-backup.json');process.exit(1)}
const [input,output]=args;
try{
 const records=JSON.parse(fs.readFileSync(input,'utf8'));
 if(!Array.isArray(records)||records.length>1000)throw new Error('Intake must be an array of at most 1000 messages.');
 if(path.resolve(input)===path.resolve(output))throw new Error('Input and output must be different files.');
 const state=fs.existsSync(output)?JSON.parse(fs.readFileSync(output,'utf8')):seed(false);
 if(state.version!==1||!Array.isArray(state.messages)||!Array.isArray(state.approvals)||!Array.isArray(state.activity))throw new Error('Invalid workspace backup.');
 let added=0;
 for(const m of records){
  if(typeof m.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(m.id)||typeof m.from!=='string'||typeof m.subject!=='string'||typeof m.body!=='string')throw new Error('Each intake record needs a stable alphanumeric ID, from, subject and body.');
  if(state.messages.some(x=>x.id===m.id))continue;
  state.messages.push({id:m.id,from:m.from.slice(0,1000),subject:m.subject.slice(0,2000),body:m.body.slice(0,20000),received:new Date().toISOString(),processed:false,category:'Unprocessed'});added++;
 }
 const processed=triage(state);
 state.activity.unshift({id:uid(),at:new Date().toISOString(),text:`Offline worker imported ${added} messages and classified ${processed}. No external actions.`,kind:'offline worker'});
 const tmp=output+'.tmp-'+process.pid;
 fs.writeFileSync(tmp,JSON.stringify(state,null,2),{mode:0o600,flag:'wx'});
 fs.renameSync(tmp,output);
 console.log(`Imported ${added}; classified ${processed}; ${state.approvals.filter(a=>a.status==='pending').length} pending local drafts. Output: ${output}`);
}catch(e){console.error(e.message);process.exit(1)}
