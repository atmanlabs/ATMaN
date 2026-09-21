const fs=require('fs'),Module=require('module'),assert=require('assert'),{EventEmitter}=require('events');
const botRoot = __dirname;
const m=new Module(botRoot+'/skill_learning.js');m.paths=Module._nodeModulePaths(botRoot);
m._compile(fs.readFileSync(__dirname+'/skill_learning.js','utf8'),botRoot+'/skill_learning.js');
const {attachSkillLearning}=m.exports;
const {Vec3}=m.require('vec3');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const bot=new EventEmitter(),said=[],calls=[],stored=[];
 bot.players={'Operator':{username:'Operator',entity:{position:new Vec3(0,64,0)}}};
 bot.entity={position:new Vec3(0,64,0)};bot.chat=s=>said.push(s);
 bot.pathfinder={setGoal(){},stop(){},goto:async()=>{}};bot.stopDigging=()=>{};
 bot.inventory={items:()=>[{name:'oak_log'},{name:'oak_planks'}]};
 bot.equip=async i=>calls.push('equip:'+i.name);bot.unequip=async()=>calls.push('empty');
 bot.findBlock=()=>({name:'oak_log',position:new Vec3(1,64,0)});
 bot.blockAt=p=>({name:'oak_log',position:p,boundingBox:'block'});
 bot.dig=async()=>calls.push('break');
 bot.registry={itemsByName:{oak_planks:{id:1}}};bot.recipesFor=()=>[{result:{count:4},requiresTable:false}];
 bot.craft=async(_,n)=>calls.push('craft:'+n);
 let seq=0,events=[];
 const request=async(url,body)=>{
  if(url.includes('/skills/store')) {stored.push(body);return {ok:true,skill:body};}
  if(url.includes('latest'))return {sequence:seq,players:[{name:'Operator',world:'world',position:[0,64,0],item:'air'}]};
  return {sequence:seq,oldest:1,events:events.filter(e=>e.sequence>Number(url.split('=').at(-1)))};
 };
 const learner=attachSkillLearning(bot,{token:'test',setBusy(){},request});
 const decision=(action,skill)=>({ok:true,approved:true,action,skill,reply:'Recording now.'});
 learner.handle('Operator','learn this as test',decision('learn_start',{name:'test'}));await delay(20);
 for(const [action,params] of [['break',{block:'oak_log',position:[1,64,0]}],['place',{block:'oak_planks',item:'oak_planks',position:[2,64,0]}],['equip',{item:'oak_log'}],['craft',{item:'oak_planks',count:4}]])events.push({sequence:++seq,time:Date.now(),player:'Operator',world:'world',action,params});
 events.push({sequence:++seq,time:Date.now(),player:'OtherPlayer',world:'world',action:'break',params:{block:'dirt'}});
 learner.handle('Operator','done',decision('learn_done',{}));await delay(40);
 assert.equal(stored.length,1);assert.deepEqual(stored[0].steps.map(s=>s.action),['break','place','equip','craft']);
 assert.deepEqual(stored[0].steps[0].params.offset,[1,0,0]);assert.equal(stored[0].domain,'minecraft');assert.equal(stored[0].governance.auto_authorized,false);
 const replay={...stored[0],steps:stored[0].steps.filter(s=>s.action!=='place')};
 learner.handle('Operator','do test',decision('execute_skill',replay));await delay(40);
 assert(calls.includes('break'));assert(calls.includes('craft:1'));assert(said.includes('Finished test.'));
 const before=calls.length;
 learner.handle('Operator','do test',{...decision('execute_skill',replay),approved:false});await delay(20);assert.equal(calls.length,before);
 bot.players={};learner.handle('Operator','do test',decision('execute_skill',replay));await delay(20);assert.equal(calls.length,before);assert(said.at(-1).includes('supervise'));
 bot.emit('end');console.log('PASS: attributed four-action recording, persistence, stored-step replay, Judge rejection, missing supervisor');
})().catch(e=>{console.error(e);process.exit(1)});

