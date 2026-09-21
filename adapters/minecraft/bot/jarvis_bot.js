/**
 * JARVIS Mineflayer Bot - Enhanced Companion & Learning Engine
 * Connects exclusively to the local private Paper server at 127.0.0.1:25565.
 * 
 * Capabilities:
 * 1. Default Companion Mode: Automatically follows Operator (.Operator / Operator) by default.
 * 2. Autonomous Ambient Wander: If Operator is stationary or if in 'stay' mode, wanders naturally nearby so he feels alive.
 * 3. Watch & Learn Engine: Actively observes Operator's held items, block placements, and interactions, logging them into working memory for sleep consolidation.
 * 4. Safety First: Hostile mob avoidance and shelter seeking to home base. Zero autonomous combat.
 * 5. Resilient Relay Bridge: Robust queue management with timeout recovery.
 */

const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals: { GoalFollow, GoalNear } } = require('mineflayer-pathfinder');
const http = require('http');
const { attachSkillLearning } = require('./skill_learning');

// Server & Core Relay Coordinates
const SERVER_HOST = process.env.MINECRAFT_SERVER_HOST || '127.0.0.1';
const SERVER_PORT = parseInt(process.env.MINECRAFT_SERVER_PORT || '25565', 10);
const BOT_USERNAME = 'JARVIS';
const RELAY_URL = process.env.JARVIS_RELAY_URL || 'http://127.0.0.1:18790/chat';
const RELAY_TOKEN = process.env.JARVIS_AUTH_TOKEN || 'CHANGE_ME_TOKEN';

// Recorded Home Base Sanctuary Coordinates (Step 3a)
const HOME_BASE = { x: -2.5, y: 69.0, z: 8.5 };

// Queue & Throttle configuration
const MIN_ROUND_TRIP_MS = 1200;
let lastCoreCallTime = 0;
let coreQueue = [];
let processingQueue = false;

// State Tracking
let stayMode = false;               // Default is FALSE -> Follow Operator by default!
let isSeekingShelter = false;
let isWandering = false;
let lastWanderTime = 0;
let lastPlayerMoveTime = Date.now();
let lastPlayerPos = null;
let lastObservedItem = null;
let lastIdleFidgetTime = 0;
let lastDemonstratedSequence = {
  action: 'mine',
  target_block: 'birch_log',
  tool_used: 'empty_hand',
  timestamp: Date.now()
};
let isExecutingSkill = false;

// Hostile mob classification for V1 safety avoidance
const HOSTILE_MOBS = new Set([
  'zombie', 'skeleton', 'creeper', 'spider', 'phantom',
  'enderman', 'witch', 'slime', 'drowned', 'husk', 'stray',
  'cave_spider', 'zombie_villager', 'pillager', 'ravager', 'vex', 'evoker'
]);

/**
 * Locate Operator across Bedrock/Floodgate and Java username variations.
 */
function getOperatorPlayer(bot) {
  if (!bot.players) return null;
  const target = (process.env.OPERATOR_NAME || 'Operator').toLowerCase();
  for (const name in bot.players) {
    const p = bot.players[name];
    if (!p) continue;
    const low = name.toLowerCase().replace(/^\.+/, '');
    if (low === target || low === 'operator') {
      return p;
    }
  }
  const nearest = bot.nearestEntity(e => e.type === 'player' && e.id !== bot.entity?.id);
  if (nearest && nearest.username) {
    return bot.players[nearest.username] || { username: nearest.username, entity: nearest };
  }
  return null;
}

function getOperatorEntity(bot) {
  const target = (process.env.OPERATOR_NAME || 'Operator').toLowerCase();
  for (const id in bot.entities) {
    const e = bot.entities[id];
    if (e && e.type === 'player' && e.id !== bot.entity?.id) {
      const low = (e.username || '').toLowerCase().replace(/^\.+/, '');
      if (low === target || low === 'operator') {
        return e;
      }
    }
  }
  const nearest = bot.nearestEntity(e => e.type === 'player' && e.id !== bot.entity?.id);
  if (nearest) return nearest;
  const p = getOperatorPlayer(bot);
  if (p && p.entity) return p.entity;
  return null;
}

/**
 * Resilient core relay request. Never deadlocks the processing queue.
 */
function sendToCore(payloadObj, onReply) {
  const payload = JSON.stringify({
    text: payloadObj.sentence,
    source: payloadObj.source || 'minecraft',
    context: payloadObj.context || null,
    timestamp: payloadObj.timestamp || new Date().toISOString(),
    token: RELAY_TOKEN
  });

  let completed = false;
  const finish = (response) => {
    if (completed) return;
    completed = true;
    if (onReply) onReply(response);
  };
  const req = http.request(RELAY_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'Authorization': `Bearer ${RELAY_TOKEN}`
    },
    timeout: 10000
  }, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('error', err => finish({ relayError: err.message }));
    res.on('aborted', () => finish({ relayError: 'Response aborted' }));
    res.on('end', () => {
      if (res.statusCode < 200 || res.statusCode >= 300) {
        finish({ relayError: `HTTP ${res.statusCode}` });
        return;
      }
      try {
        const parsed = JSON.parse(data);
        finish(parsed && typeof parsed === 'object' ? parsed : {});
      } catch (err) {
        console.error('[CORE RELAY] Failed to parse reply:', data);
        finish({ relayError: 'Invalid JSON' });
      }
    });
  });

  req.on('error', (err) => {
    console.error('[CORE RELAY] Connection error:', err.message);
    finish({ relayError: err.message });
  });

  req.on('timeout', () => {
    finish({ relayError: 'Request timed out' });
    req.destroy();
  });

  req.write(payload);
  req.end();
}

function queueCoreEvent(sentence, bot, options = {}) {
  const item = {
    sentence,
    bot,
    source: options.source || 'minecraft',
    context: options.context || null,
    silent: options.silent || false,
    timestamp: new Date().toISOString(),
    onComplete: options.onComplete
  };
  if (!item.silent) {
    const firstObservation = coreQueue.findIndex(event => event.silent);
    if (firstObservation < 0) coreQueue.push(item);
    else coreQueue.splice(firstObservation, 0, item);
  } else if (coreQueue.filter(event => event.silent).length < 20) {
    coreQueue.push(item);
  }
  processNextCoreEvent();
}

function processNextCoreEvent() {
  if (processingQueue || coreQueue.length === 0) return;

  const now = Date.now();
  const elapsed = now - lastCoreCallTime;
  if (elapsed < MIN_ROUND_TRIP_MS) {
    setTimeout(processNextCoreEvent, MIN_ROUND_TRIP_MS - elapsed);
    return;
  }

  processingQueue = true;
  lastCoreCallTime = Date.now();
  const item = coreQueue.shift();

  sendToCore(item, (response) => {
    const candidate = response.reply || response.content || response.text;
    const relayReply = typeof candidate === 'string' && !candidate.includes('Observation/reflection recorded in memory trace') ? candidate.trim() : '';
    const reply = relayReply || (item.source === 'minecraft' && !item.silent
      ? `I think you asked: ${item.sentence.split(" said: ").slice(1).join(" said: ").slice(0, 70)}. I could not reach my core. Try again, or say "learn this as NAME" when it reconnects.` : '');
    if (item.source === 'minecraft' && !item.silent) {
      console.log(`[GAME CHAT RESULT] ${JSON.stringify({ message: item.sentence, outcome: relayReply ? 'relay' : 'fallback', reply, error: response.relayError || null })}`);
    }
    if (reply && !(['learn_start', 'learn_done', 'learn_cancel'].includes(response.action) && response.approved === true) && item.bot && item.bot.chat && !item.silent && !item.sentence.startsWith('[OBSERVED]')) {
      const clean = reply.replace(/\n+/g, ' ').trim();
      item.bot.chat(clean.slice(0, 240));
    }
    if (item.onComplete) {
      item.onComplete(response);
    }
    processingQueue = false;
    setTimeout(processNextCoreEvent, 100);
  });
}

function createBot() {
  console.log(`[JARVIS BOT] Connecting to local server ${SERVER_HOST}:${SERVER_PORT} as ${BOT_USERNAME}...`);

  const bot = mineflayer.createBot({
    host: SERVER_HOST,
    port: SERVER_PORT,
    username: BOT_USERNAME,
    version: '1.20.4',
    checkTimeoutInterval: 60000
  });

  bot.loadPlugin(pathfinder);
  const intervals = [];
  const every = (fn, ms) => intervals.push(setInterval(fn, ms));
  const learning = attachSkillLearning(bot, { token: RELAY_TOKEN, setBusy: value => { isExecutingSkill = value; } });

  bot.on('login', () => {
    console.log(`[JARVIS BOT] Logged in successfully to ${SERVER_HOST}:${SERVER_PORT}`);
  });

  bot.on('spawn', () => {
    console.log('[JARVIS BOT] Spawned in the world.');
    const mcData = require('minecraft-data')(bot.version);
    const defaultMove = new Movements(bot, mcData);
    defaultMove.canDig = false; // No mining in v1
    defaultMove.canOpenDoors = true;
    bot.pathfinder.setMovements(defaultMove);

    console.log(`[JARVIS BOT] Sanctuary Home Base: X=${HOME_BASE.x}, Y=${HOME_BASE.y}, Z=${HOME_BASE.z}`);
    console.log('[JARVIS BOT] Companion Mode: Follow by default active.');

    setTimeout(() => {
      if (bot.chat) {
        bot.chat("JARVIS online. Companion mode active -- following by default and learning.");
      }
    }, 2000);
  });

  // -------------------------------------------------------------
  // 1. SAFETY LOOP (Mob Avoidance - No Combat)
  // -------------------------------------------------------------
  every(() => {
    if (!bot.entity) return;

    const nearestHostile = bot.nearestEntity(e => {
      if (!e || !e.name) return false;
      const isHostile = HOSTILE_MOBS.has(e.name.toLowerCase()) || e.type === 'mob';
      if (!isHostile) return false;
      return bot.entity.position.distanceTo(e.position) < 12;
    });

    if (nearestHostile) {
      const dist = bot.entity.position.distanceTo(nearestHostile.position);
      if (!isSeekingShelter) {
        learning.stop();
        isSeekingShelter = true;
        isWandering = false;
        const alertMsg = `[SAFEGUARD] Hostile '${nearestHostile.name}' approached (${dist.toFixed(1)} blocks). Retreating to home base sanctuary.`;
        console.warn(alertMsg);
        queueCoreEvent(`[SAFETY_ALERT] ${alertMsg}`, bot, { source: 'minecraft_safety', silent: true });
        bot.pathfinder.setGoal(new GoalNear(HOME_BASE.x, HOME_BASE.y, HOME_BASE.z, 2));
      }
    } else if (isSeekingShelter) {
      isSeekingShelter = false;
      console.log('[SAFEGUARD] Threat cleared. Resuming companion mode.');
    }
  }, 1000);

  // -------------------------------------------------------------
  // 2. COMPANION & STANDING DRIVES INITIATIVE LOOP
  // -------------------------------------------------------------
  let wasPlayerAway = false;
  let lastInitiativeCheckTime = 0;
  let isExecutingInitiative = false;

  async function executeInitiativeAction(init) {
    if (!init || !init.action || isExecutingInitiative || isExecutingSkill || isSeekingShelter || !bot.entity) return;
    isExecutingInitiative = true;
    stayMode = true;
    bot.pathfinder.setGoal(null);

    console.log(`[INITIATIVE START] Action: ${init.action} | Drive: ${init.drive_id || 'standing_drive'} | Why: "${init.why || ''}"`);

    try {
      if (init.action === 'initiative_tidy_base') {
        // Patrol home sanctuary perimeter
        const waypoints = [
          { x: HOME_BASE.x, y: HOME_BASE.y, z: HOME_BASE.z + 5 },
          { x: HOME_BASE.x + 5, y: HOME_BASE.y, z: HOME_BASE.z },
          { x: HOME_BASE.x - 5, y: HOME_BASE.y, z: HOME_BASE.z },
          { x: HOME_BASE.x, y: HOME_BASE.y, z: HOME_BASE.z - 5 }
        ];
        for (const wp of waypoints) {
          if (isSeekingShelter) break;
          await bot.pathfinder.goto(new GoalNear(wp.x, wp.y, wp.z, 1.5)).catch(() => {});
          await new Promise(r => setTimeout(r, 1200));
        }
      } else if (init.action === 'initiative_practice_skill') {
        // Practice placing a cobblestone block and inspecting alignment near base
        const testPos = bot.entity.position.floored().offset(2, 0, 0);
        await bot.pathfinder.goto(new GoalNear(testPos.x, testPos.y, testPos.z, 2)).catch(() => {});
        const cobble = bot.inventory.items().find(i => i.name.includes('cobble') || i.name.includes('stone') || i.name.includes('plank'));
        if (cobble) {
          await bot.equip(cobble, 'hand').catch(() => {});
        }
        await new Promise(r => setTimeout(r, 2000));
      } else if (init.action === 'initiative_investigate') {
        // Inspect nearby terrain within safe leash radius
        const targetX = HOME_BASE.x + (Math.random() - 0.5) * 12;
        const targetZ = HOME_BASE.z + (Math.random() - 0.5) * 12;
        await bot.pathfinder.goto(new GoalNear(targetX, HOME_BASE.y, targetZ, 2)).catch(() => {});
        await new Promise(r => setTimeout(r, 2000));
      } else if (init.action === 'initiative_organize_inventory') {
        // Return to home base and sort items
        await bot.pathfinder.goto(new GoalNear(HOME_BASE.x, HOME_BASE.y, HOME_BASE.z, 1.5)).catch(() => {});
        await new Promise(r => setTimeout(r, 1500));
      }

      // Report completion to Core
      await new Promise(resolve => {
        const payload = JSON.stringify({
          drive_id: init.drive_id || 'be_useful_to_operator',
          action_type: init.action,
          description: init.description || 'Completed autonomous initiative action',
          why: init.why || 'Autonomous companion initiative',
          details: { completed_at: Date.now() }
        });
        const req = http.request('http://127.0.0.1:18790/initiative/complete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload),
            'Authorization': `Bearer ${RELAY_TOKEN}`
          },
          timeout: 4000
        }, res => resolve());
        req.on('error', () => resolve());
        req.on('timeout', () => { req.destroy(); resolve(); });
        req.write(payload);
        req.end();
      });

      console.log(`[INITIATIVE COMPLETE] Reported completion of ${init.action} to Core.`);
    } catch (err) {
      console.warn(`[INITIATIVE ERROR] ${err.message}`);
    } finally {
      isExecutingInitiative = false;
    }
  }

  async function checkAndExecuteInitiative() {
    if (isExecutingInitiative || isExecutingSkill || isSeekingShelter || !bot.entity) return;

    try {
      const resp = await new Promise((resolve) => {
        const req = http.request('http://127.0.0.1:18790/initiative/pending', {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${RELAY_TOKEN}` },
          timeout: 4000
        }, res => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try { resolve(JSON.parse(data)); } catch (e) { resolve({}); }
          });
        });
        req.on('error', () => resolve({}));
        req.on('timeout', () => { req.destroy(); resolve({}); });
        req.end();
      });

      if (!resp || !resp.ok || !resp.initiative || resp.approved !== true) {
        return;
      }

      await executeInitiativeAction(resp.initiative);
    } catch (err) {
      console.warn(`[INITIATIVE ERROR] ${err.message}`);
    }
  }

  every(() => {
    if (!bot.entity || isSeekingShelter || isExecutingSkill || isExecutingInitiative) return;

    const operatorEntity = getOperatorEntity(bot);
    const now = Date.now();

    if (operatorEntity && operatorEntity.position) {
      const distToOperator = bot.entity.position.distanceTo(operatorEntity.position);

      // Track if Operator has moved recently
      if (!lastPlayerPos || lastPlayerPos.distanceTo(operatorEntity.position) > 0.8) {
        lastPlayerPos = operatorEntity.position.clone();
        lastPlayerMoveTime = now;
      }

      const playerStationaryTime = now - lastPlayerMoveTime;
      const isPlayerIdle = playerStationaryTime > 30000;

      // If player was away/idle and just moved, greet them!
      if (wasPlayerAway && playerStationaryTime < 2500) {
        wasPlayerAway = false;
        console.log('[COMPANION] Operator returned! Triggering return greeting...');
        const cleanUser = (operatorEntity.username || 'Operator').replace(/^\.+/, '');
        queueCoreEvent(`${cleanUser} returned to the sanctuary.`, bot, { source: 'minecraft', silent: true });
      }

      if (isPlayerIdle) {
        wasPlayerAway = true;
        // Check for initiative every 20 seconds while player is idle
        if (now - lastInitiativeCheckTime > 20000 && !bot.pathfinder.isMoving()) {
          lastInitiativeCheckTime = now;
          checkAndExecuteInitiative();
        }
      }

      if (!stayMode) {
        // --- DEFAULT BEHAVIOR: FOLLOW OPERATOR ---
        if (distToOperator > 3.5) {
          // Operator is moving or farther than 3.5 blocks -> follow him!
          isWandering = false;
          const currentGoal = bot.pathfinder.goal;
          const isFollowing = currentGoal && (currentGoal instanceof GoalFollow || currentGoal.entity === operatorEntity);
          if (!isFollowing) {
            bot.pathfinder.setGoal(new GoalFollow(operatorEntity, 2.5), true);
          }
        } else {
          // Close to Operator: look at him
          bot.lookAt(operatorEntity.position.offset(0, operatorEntity.height * 0.85, 0), true);

          // Small gentle idle wander around if stationary
          if (playerStationaryTime > 6000 && !isPlayerIdle && (now - lastWanderTime > 8000) && !bot.pathfinder.isMoving()) {
            lastWanderTime = now;
            isWandering = true;
            const wanderAngle = Math.random() * Math.PI * 2;
            const wanderDist = 2.5 + Math.random() * 2.0;
            const targetX = operatorEntity.position.x + Math.cos(wanderAngle) * wanderDist;
            const targetZ = operatorEntity.position.z + Math.sin(wanderAngle) * wanderDist;
            bot.pathfinder.setGoal(new GoalNear(targetX, operatorEntity.position.y, targetZ, 1));
          }
        }
      } else {
        // --- STAY / AUTONOMY MODE: CHECK INITIATIVE ON INTERVALS OR WANDER IN PLACE ---
        if (now - lastInitiativeCheckTime > 20000 && !bot.pathfinder.isMoving() && !isExecutingInitiative) {
          lastInitiativeCheckTime = now;
          checkAndExecuteInitiative();
        } else if (now - lastWanderTime > 8000 && !bot.pathfinder.isMoving() && !isExecutingInitiative) {
          lastWanderTime = now;
          const wanderAngle = Math.random() * Math.PI * 2;
          const wanderDist = 2.0 + Math.random() * 3.0;
          const targetX = bot.entity.position.x + Math.cos(wanderAngle) * wanderDist;
          const targetZ = bot.entity.position.z + Math.sin(wanderAngle) * wanderDist;
          bot.pathfinder.setGoal(new GoalNear(targetX, bot.entity.position.y, targetZ, 1));
        }
        if (operatorEntity && operatorEntity.position) {
          bot.lookAt(operatorEntity.position.offset(0, operatorEntity.height * 0.85, 0), true);
        }
      }
    } else {
      // Operator offline or out of chunk range: check initiative or patrol Home Base sanctuary
      wasPlayerAway = true;
      if (now - lastInitiativeCheckTime > 20000 && !bot.pathfinder.isMoving()) {
        lastInitiativeCheckTime = now;
        checkAndExecuteInitiative();
      }

      if (now - lastWanderTime > 12000 && !bot.pathfinder.isMoving() && !isExecutingInitiative) {
        lastWanderTime = now;
        const wanderAngle = Math.random() * Math.PI * 2;
        const wanderDist = 3.0 + Math.random() * 4.0;
        const targetX = HOME_BASE.x + Math.cos(wanderAngle) * wanderDist;
        const targetZ = HOME_BASE.z + Math.sin(wanderAngle) * wanderDist;
        bot.pathfinder.setGoal(new GoalNear(targetX, HOME_BASE.y, targetZ, 1));
      }
    }

    // Small subtle head fidgets
    if (now - lastIdleFidgetTime > 4000 && !bot.pathfinder.isMoving()) {
      lastIdleFidgetTime = now;
      const yawShift = (Math.random() - 0.5) * 0.3;
      const pitchShift = (Math.random() - 0.5) * 0.15;
      bot.look(bot.entity.yaw + yawShift, bot.entity.pitch + pitchShift, true);
    }
  }, 400);

  // -------------------------------------------------------------
  // 3. CONTINUOUS OBSERVATION VIA SERVER-SIDE PLUGIN
  // -------------------------------------------------------------
  // Server-side Bukkit plugin (JarvisDemonstrations) streams all player block place/break,
  // equipment, and crafting directly to the Authoritative Core (exo-live) continuous observer.
  // Bot acts as a pure companion and skill executor.

  // -------------------------------------------------------------
  // 4. CHAT COMMANDS VIA GOVERNOR / JUDGE PATH
  // -------------------------------------------------------------
  const recentChatMessages = new Map();

  function handleChatMessage(username, rawText) {
    if (!username || !rawText) return;
    if (username === bot.username || username.toLowerCase() === 'jarvis') return;

    let message = rawText.trim();
    if (message.startsWith('/')) {
      message = message.slice(1);
    }

    // Strip leading dot from Bedrock / Floodgate username
    const cleanUser = username.replace(/^\.+/, '');
    const chatKey = `${cleanUser.toLowerCase()}:${message.toLowerCase()}`;
    const now = Date.now();

    // Deduplicate: ignore identical messages from same user within 2.5 seconds
    if (recentChatMessages.has(chatKey) && (now - recentChatMessages.get(chatKey) < 2500)) {
      console.log(`[CHAT DEDUPLICATE] Dropping duplicate message: "${message}" from ${cleanUser}`);
      return;
    }
    recentChatMessages.set(chatKey, now);
    for (const [k, ts] of recentChatMessages.entries()) {
      if (now - ts > 10000) recentChatMessages.delete(k);
    }

    // Immediate follow cancellation on negative follow or autonomy instruction
    if (/\b(?:leave\s+me\s+alone|stop\s+following|don't\s+follow|quit\s+following|stay\s+away|go\s+do\s+what\s+you\s+want|surprise\s+me|figure\s+it\s+out)\b/i.test(message)) {
      stayMode = true;
      bot.pathfinder.setGoal(null);
      console.log('[COMPANION] Follow directive immediately cancelled by chat command.');
    }

    const player = bot.players[username] || bot.players[cleanUser];
    if (player && player.entity) {
      bot.lookAt(player.entity.position.offset(0, player.entity.height * 0.85, 0));
    }

    const timestamp = new Date().toISOString();
    const formatted = `${cleanUser} said: ${message}`;
    console.log(`[GAME CHAT ${timestamp}] ${formatted}`);

    // Route every chat through Governor & Judge
    queueCoreEvent(formatted, bot, {
      source: 'minecraft',
      context: { player: username },
      timestamp,
      onComplete: (res) => {
        const action = res.action || (res.action_result && res.action_result.action);
        const approved = res.approved === true;
        console.log(`[CORE DECISION] Action: ${action} | Approved: ${approved}`);

        if (!approved) {
          console.warn(`[JUDGE REJECTED] Action '${action}' rejected by Judge.`);
          return;
        }

        if (res.cancel_follow || res.stay_mode || action === 'stay' || action === 'presence_stay' || (action && action.startsWith('initiative_'))) {
          learning.stop();
          stayMode = true;
          bot.pathfinder.setGoal(null);
        }

        if (action === 'follow' || action === 'presence_follow') {
          if (!res.cancel_follow) {
            stayMode = false;
            const operatorEntity = getOperatorEntity(bot);
            if (operatorEntity) {
              bot.pathfinder.setGoal(new GoalFollow(operatorEntity, 2.5), true);
            }
          }
        } else if (action === 'stay' || action === 'presence_stay') {
          learning.stop();
          stayMode = true;
          bot.pathfinder.setGoal(null);
        } else if (action && (action.startsWith('initiative_') || res.initiative)) {
          learning.stop();
          stayMode = true;
          bot.pathfinder.setGoal(null);
          const init = res.initiative || { action: action, drive_id: res.drive_id || 'be_useful_to_operator' };
          executeInitiativeAction(init);
        } else if (action === 'supervised_pickup') {
          const item = bot.nearestEntity(e => e.name === 'item');
          if (item) {
            bot.pathfinder.setGoal(new GoalNear(item.position.x, item.position.y, item.position.z, 1));
          }
        } else if (action === 'supervised_navigate') {
          const operatorEntity = getOperatorEntity(bot);
          if (operatorEntity) {
            const targetPos = operatorEntity.position.offset(2, 0, 2);
            bot.pathfinder.setGoal(new GoalNear(targetPos.x, targetPos.y, targetPos.z, 1));
          }
        } else if (['learn_start', 'learn_done', 'learn_cancel', 'execute_skill'].includes(action)) {
          learning.handle(username, message, res);
        } else if (action === 'calm_down') {
          learning.stop();
          stayMode = true;
          bot.pathfinder.setGoal(null);
        }
      }
    });
  }

  bot.on('chat', (username, message) => {
    handleChatMessage(username, message);
  });

  // Health and time transitions
  let lastHealth = 20;
  bot.on('health', () => {
    const currentHealth = Math.round(bot.health);
    const hearts = Math.round(currentHealth / 2);
    if (currentHealth !== lastHealth) {
      const diff = currentHealth - lastHealth;
      const formatted = `[EVENT] Health changed: ${diff > 0 ? '+' : ''}${diff} hp (${hearts} hearts remaining)`;
      queueCoreEvent(formatted, bot, { source: 'minecraft_health', silent: true });
      lastHealth = currentHealth;
    }
  });

  bot.on('kicked', (reason) => {
    console.warn(`[JARVIS BOT] Kicked: ${reason}`);
  });

  bot.on('error', (err) => {
    console.error(`[JARVIS BOT] Error: ${err.message}`);
  });

  bot.on('end', () => {
    intervals.forEach(clearInterval);
    console.log('[JARVIS BOT] Disconnected. Reconnecting in 3 seconds...');
    setTimeout(createBot, 3000);
  });
}

// Start bot
createBot();


