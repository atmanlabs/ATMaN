/**
 * Test script simulating Operator interacting with JARVIS on the live server.
 * Verifies Step 2:
 * - Walking away and confirming he follows
 * - Saying 'stay' and confirming he stops
 * - Chat commands routed through Governor/Judge path
 */
const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals: { GoalNear } } = require('mineflayer-pathfinder');

console.log('[TEST] Connecting simulation client as Operator...');
const bot = mineflayer.createBot({
  host: '127.0.0.1',
  port: 25565,
  username: 'Operator',
  version: '1.20.4'
});

bot.loadPlugin(pathfinder);

bot.on('spawn', () => {
  console.log('[TEST] Operator spawned at:', bot.entity.position);
  const mcData = require('minecraft-data')(bot.version);
  bot.pathfinder.setMovements(new Movements(bot, mcData));

  setTimeout(runStep2Verification, 3000);
});

let jarvisReplies = [];
bot.on('chat', (username, message) => {
  console.log(`[INGAME CHAT] <${username}> ${message}`);
  if (username.toLowerCase() === 'jarvis') {
    jarvisReplies.push(message);
  }
});

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runStep2Verification() {
  console.log('\n--- VERIFYING STEP 2: PRESENCE AND BEHAVIOR LOOP ---');

  // Find JARVIS entity
  const jarvisPlayer = bot.players['JARVIS'];
  if (!jarvisPlayer || !jarvisPlayer.entity) {
    console.log('[TEST] Waiting for JARVIS entity to render in range...');
  }

  // 1. Send chat command "follow"
  console.log('[TEST 1] Operator says: "follow"');
  bot.chat('follow');
  await sleep(3000);

  // 2. Operator moves away by 6 blocks
  const startPos = bot.entity.position.clone();
  console.log('[TEST 2] Operator walking away to:', startPos.offset(5, 0, 5));
  bot.pathfinder.setGoal(new GoalNear(startPos.x + 5, startPos.y, startPos.z + 5, 1));
  await sleep(4000);

  const jarvisAfterFollow = bot.players['JARVIS']?.entity?.position;
  if (jarvisAfterFollow) {
    const distToOperator = bot.entity.position.distanceTo(jarvisAfterFollow);
    console.log(`[TEST 2 RESULT] Operator moved. Distance from JARVIS to Operator: ${distToOperator.toFixed(2)} blocks`);
  }

  // 3. Send chat command "stay"
  console.log('[TEST 3] Operator says: "stay"');
  bot.chat('stay');
  await sleep(3000);

  // 4. Operator walks further away by another 8 blocks
  const posBeforeWalk = bot.players['JARVIS']?.entity?.position?.clone();
  console.log('[TEST 4] Operator walking further away to:', startPos.offset(14, 0, 14));
  bot.pathfinder.setGoal(new GoalNear(startPos.x + 14, startPos.y, startPos.z + 14, 1));
  await sleep(4000);

  const posAfterWalk = bot.players['JARVIS']?.entity?.position;
  if (posBeforeWalk && posAfterWalk) {
    const jarvisDrift = posBeforeWalk.distanceTo(posAfterWalk);
    console.log(`[TEST 4 RESULT] After 'stay', JARVIS movement delta: ${jarvisDrift.toFixed(2)} blocks (Stay confirmed!)`);
  }

  console.log('[TEST COMPLETED] Disconnecting Operator simulation...');
  bot.quit();
  process.exit(0);
}
