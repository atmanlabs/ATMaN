const assert=require('assert');const {passiveLearner}=require('./passive_learning');
(async()=>{
let time=1000,sequence=0,events=[],saved=[],paused=false;
const request=async(url,body)=>{
 if(body){saved.push(body);return {ok:true};}
 if(url.includes('/skills?'))return {skills:[]};
 if(url.includes('latest'))return {sequence};
 return {sequence,oldest:1,events:events.filter(e=>e.sequence>Number(url.split('=').at(-1)))};
};
const p=passiveLearner({request,token:'test',operator:n=>n==='Operator',nearby:()=>[0,64,0],paused:()=>paused,now:()=>time,log:()=>{}});
await p.tick();
function event(player='Operator'){events.push({sequence:++sequence,player,time,world:'world',action:'break',params:{block:'oak_log',position:[1,64,0],tool:'iron_axe'}})}
event();event('Other');await p.tick();time+=9000;await p.tick();assert.equal(saved.length,1);assert.equal(saved[0].steps.length,1);assert.equal(saved[0].governance.auto_authorized,false);assert.deepEqual(saved[0].steps[0].params.offset,[1,0,0]);
event();await p.tick();time+=9000;await p.tick();assert.equal(saved.length,1);
paused=true;event();await p.tick();paused=false;time+=9000;await p.tick();assert.equal(saved.length,1);
p.stop();console.log('PASS: passive saving, correct player, relative positions, deduplication, explicit-learning pause, no auto-execution');
})().catch(e=>{console.error(e);process.exit(1)});
