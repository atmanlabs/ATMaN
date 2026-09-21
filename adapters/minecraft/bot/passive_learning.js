'use strict';
const { createHash } = require('crypto');
// A passive sequence is a candidate procedure, never an autonomous instruction.
function passiveLearner({request, token, operator, nearby, paused, log = console.log, now = Date.now}) {
  let cursor=null, busy=false, stopped=false;
  const sessions=new Map(), seen=new Set(), recent=new Map();
  async function save(session) {
    recent.set(session.player, JSON.parse(JSON.stringify(session)));
    if (!session.steps.some(s=>s.action!=='equip')) return;
    const signature=createHash('sha256').update(JSON.stringify(session.steps.map(s=>[s.action,s.params]))).digest('hex').slice(0,10);
    if(seen.has(signature)) return;
    const main=session.steps.find(s=>s.action!=='equip');
    const label=`${main.action}_${main.params.block || main.params.item}`.slice(0,26);
    const skill={name:`seen_${label}_${signature}`,domain:'minecraft',
      description:`Observed ${session.player}: ${session.steps.length} steps; inferred sequence, not a verified goal.`,
      steps:session.steps,preconditions:{requires_nearby_supervisor:true,placement_origin:'bot position at recall'},
      effects:{},governance:{requires_supervision:true,judge_gated:true,auto_authorized:false},
      metadata:{observed_at:session.last,learning_mode:'passive',confidence:'observed_sequence',demonstrated_by:session.player,demonstration_world:session.world}};
    const result=await request('http://127.0.0.1:18790/skills/store',skill,token);
    if(!result.ok) throw Error('Core did not save passive skill');
    seen.add(signature); log(`[PASSIVE LEARN] Saved ${skill.name} (${session.steps.length} steps)`);
  }
  async function tick() {
    if(busy || stopped) return; busy=true;
    try {
      if(cursor===null) {
        const state=await request('http://127.0.0.1:18791/events?since=latest');
        cursor=state.sequence;
        const skills=await request('http://127.0.0.1:18790/skills?domain=minecraft');
        for(const s of skills.skills || []) if(s.metadata?.learning_mode==='passive') seen.add(s.name.slice(-10));
        return;
      }
      const data=await request(`http://127.0.0.1:18791/events?since=${cursor}`);
      if(data.sequence<cursor || data.oldest>cursor+1) { sessions.clear(); cursor=data.sequence; return; }
      cursor=data.sequence;
      if(paused()) { sessions.clear(); return; }
      for(const event of data.events) {
        if(stopped || !operator(event.player) || !nearby(event.player) || !['break','place','equip','craft'].includes(event.action)) continue;
        let session=sessions.get(event.player);
        if(session && (event.world!==session.world || event.time-session.last>8000 || session.steps.length>=32)) {
          await save(session); sessions.delete(event.player); session=null;
        }
        if(!session) {
          const origin=nearby(event.player);
          session={player:event.player,world:event.world,origin:origin.map(Math.floor),last:event.time,steps:[]};
          sessions.set(event.player,session);
        }
        const params={...event.params};
        if(params.position) {params.offset=params.position.map((v,i)=>v-session.origin[i]);delete params.position;}
        if(params.offset?.some(n=>Math.abs(n)>32)) { sessions.delete(event.player); continue; }
        session.last=event.time;
        const previous=session.steps.at(-1);
        if(event.action==='equip' && previous?.action==='equip' && previous.params.item===params.item) continue;
        session.steps.push({step:session.steps.length+1,action:event.action,description:`${event.action} ${params.block || params.item}`,params});
      }
      for(const [player,session] of sessions) if(now()-session.last>=8000) {
        await save(session);sessions.delete(player);
      }
    } catch(err) {log(`[PASSIVE LEARN] ${err.message}`);}
    finally {busy=false;}
  }
  function context(username) {
    const same = value => value.replace(/^\.+/, '').toLowerCase() === username.replace(/^\.+/, '').toLowerCase();
    const active = [...sessions.values()].find(s=>same(s.player));
    const session = active || [...recent.values()].find(s=>same(s.player));
    if (!session || now()-session.last>300000 || !session.steps.some(s=>s.action!=='equip')) return null;
    return {name:'recent_demonstration',domain:'minecraft',description:'The actions this player just demonstrated',
      steps:JSON.parse(JSON.stringify(session.steps)),
      governance:{requires_supervision:true,judge_gated:true,auto_authorized:false},
      metadata:{demonstrated_by:session.player,observed_at:session.last,demonstration_world:session.world}};
  }
  return {tick,context,stop(){stopped=true;sessions.clear();}};
}
module.exports={passiveLearner};

