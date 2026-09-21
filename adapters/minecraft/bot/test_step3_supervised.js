/**
 * Simulation of Operator executing Step 3 supervised action mode commands:
 * - "attack that" (Judge evaluation & logging)
 * - "pick up that" (Supervised pickup)
 * - "go there" (Supervised navigation)
 * - "where is home" (Home base coordinate lookup)
 */
const mineflayer = require('mineflayer');

console.log('[STEP 3 TEST] Connecting Operator simulation...');
const bot = mineflayer.createBot({
  host: '127.0.0.1',
  port: 25565,
  username: 'Operator',
  version: '1.20.4'
});

bot.on('spawn', async () => {
  console.log('[STEP 3 TEST] Operator spawned.');
  await sleep(2500);

  // 1. Where is home
  console.log('[COMMAND 1] Operator says: "where is home"');
  bot.chat('where is home');
  await sleep(3500);

  // 2. Supervised action: attack that
  console.log('[COMMAND 2] Operator says: "attack that"');
  bot.chat('attack that');
  await sleep(3500);

  // 3. Supervised action: pick up that
  console.log('[COMMAND 3] Operator says: "pick up that"');
  bot.chat('pick up that');
  await sleep(3500);

  // 4. Supervised action: go there
  console.log('[COMMAND 4] Operator says: "go there"');
  bot.chat('go there');
  await sleep(3500);

  // 5. Imprint candidate for the learning test:
  console.log('[COMMAND 5] Operator says: "Owner note: Operator prefers building shelters out of cobblestone and oak."');
  bot.chat('Owner note: Operator prefers building shelters out of cobblestone and oak.');
  await sleep(4000);

  console.log('[STEP 3 TEST] Commands executed. Disconnecting...');
  bot.quit();
  process.exit(0);
});

bot.on('chat', (username, message) => {
  console.log(`[INGAME CHAT] <${username}> ${message}`);
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
