'use strict';
/**
 * Thin Minecraft Skill Execution Adapter for JARVIS.
 * All passive learning, observation, segmentation, and gating live in the Authoritative Core (exo-live).
 * This module executes Judge-authorized skills under operator supervision.
 */
const { Vec3 } = require('vec3');
const { goals: { GoalNear } } = require('mineflayer-pathfinder');

const canonical = name => String(name || '').replace(/^\.+/, '').toLowerCase();
const isOperator = name => { const c = canonical(name); return c === 'operator' || c === canonical(process.env.OPERATOR_NAME || 'operator'); };

/**
 * Intelligently find an open building anchor near the supervisor/bot.
 * Ensures:
 * 1. Every placement position has clear air.
 * 2. Every placement position has solid ground beneath.
 * 3. Does not collide with Operator or the bot.
 * 4. Placed in clear view of Operator (2.0 to 4.0 blocks away).
 */
function findBuildAnchor(bot, placeOffsets, supervisorEntity) {
  const supervisorPos = supervisorEntity ? supervisorEntity.position.floored() : bot.entity.position.floored();
  const botPos = bot.entity.position.floored();

  const candidates = [];
  // Search offsets around supervisor (-4 to 4 in X and Z, -1 to 1 in Y)
  for (let ox = -4; ox <= 4; ox++) {
    for (let oz = -4; oz <= 4; oz++) {
      for (let oy = -1; oy <= 1; oy++) {
        const candidate = supervisorPos.offset(ox, oy, oz);
        const distSup = Math.hypot(candidate.x - supervisorPos.x, candidate.z - supervisorPos.z);
        if (distSup < 1.8) continue; // Not at supervisor's feet

        let valid = true;
        for (const [dx, dy, dz] of placeOffsets) {
          const bPos = candidate.offset(dx, dy, dz);
          const b = bot.blockAt(bPos);
          if (!b || !['air', 'cave_air', 'void_air', 'grass', 'tall_grass', 'short_grass'].includes(b.name)) {
            valid = false;
            break;
          }
          // Ground below must be solid
          const below = bot.blockAt(bPos.offset(0, -1, 0));
          if (!below || below.boundingBox !== 'block') {
            valid = false;
            break;
          }
          // Don't collide with player or bot body
          if (bPos.distanceTo(supervisorPos) < 1.2 || bPos.distanceTo(botPos) < 1.2) {
            valid = false;
            break;
          }
        }
        if (valid) {
          candidates.push({ anchor: candidate, dist: distSup });
        }
      }
    }
  }

  if (candidates.length > 0) {
    // Pick the candidate closest to ~2.5 blocks in front of supervisor
    candidates.sort((a, b) => Math.abs(a.dist - 2.5) - Math.abs(b.dist - 2.5));
    console.log(`[SKILL BUILD] Selected open build anchor at [${candidates[0].anchor.x}, ${candidates[0].anchor.y}, ${candidates[0].anchor.z}] (candidates evaluated: ${candidates.length})`);
    return candidates[0].anchor;
  }

  // Fallback: offset from bot
  console.log(`[SKILL BUILD] Using default offset anchor near bot`);
  return botPos.offset(2, 0, 0);
}

function attachSkillLearning(bot, { token, setBusy }) {
  let executing = false;
  let cancelled = false;
  let closed = false;

  const say = text => {
    if (!closed && bot.chat) bot.chat(text.slice(0, 240));
  };

  const playerFor = username => Object.values(bot.players || {}).find(p => canonical(p.username) === canonical(username));

  const supervise = username => {
    const player = playerFor(username);
    if (closed || cancelled || !player?.entity || !bot.entity || player.entity.position.distanceTo(bot.entity.position) > 16) {
      throw new Error('Stay within 16 blocks so you can supervise me.');
    }
    return player.entity;
  };

  const supervisionTimer = setInterval(() => {
    if (!executing) return;
    try {
      supervise(executing);
    } catch (_) {
      cancelled = true;
      bot.pathfinder.stop();
      bot.stopDigging();
    }
  }, 300);

  async function handleDecision(username, message, response) {
    const action = response.action;
    if (action !== 'execute_skill') return false;
    if (response.approved !== true || response.ok !== true) return true;

    if (!isOperator(username)) {
      say('Please have the operator supervise the skill execution.');
      return true;
    }

    if (executing) {
      say('I am already executing a task. Please wait until I finish.');
      return true;
    }

    const skill = response.skill;
    if (!skill || skill.domain !== 'minecraft' || !Array.isArray(skill.steps) || !skill.steps.length) {
      throw new Error('That skill has no executable steps.');
    }

    cancelled = false;
    const supervisorEntity = supervise(username);
    executing = username;
    setBusy(true);
    bot.pathfinder.setGoal(null);

    // Analyze if skill involves placing blocks
    const placeSteps = skill.steps.filter(s => s.action === 'place');
    const placeOffsets = placeSteps.map(s => (s.params && s.params.offset) || [0, 0, 0]);

    // Compute placement anchor
    let anchor = null;
    if (placeSteps.length > 0) {
      anchor = findBuildAnchor(bot, placeOffsets, supervisorEntity);
    } else {
      anchor = bot.entity.position.floored();
    }

    let target = null;

    const equip = async item => {
      if (item === 'air' || item === 'empty_hand') {
        await bot.unequip('hand');
        return;
      }
      let found = bot.inventory.items().find(i => i.name === item || i.name.includes(item));
      if (!found) {
        // Fallback to any solid construction block if exact material not found
        found = bot.inventory.items().find(i =>
          i.name.includes('cobble') || i.name.includes('stone') || i.name.includes('plank') || i.name.includes('dirt')
        );
        if (found) {
          console.log(`[SKILL EQUIP] Substituting '${item}' with inventory '${found.name}'`);
        }
      }
      if (!found) {
        throw new Error(`I need ${item} in my inventory to proceed.`);
      }
      await bot.equip(found, 'hand');
    };

    const approach = async position => {
      supervise(username);
      let timer;
      try {
        await Promise.race([
          bot.pathfinder.goto(new GoalNear(position.x, position.y, position.z, 2)),
          new Promise((_, reject) => {
            timer = setTimeout(() => {
              bot.pathfinder.stop();
              reject(new Error('I could not reach the next placement position.'));
            }, 12000);
          })
        ]);
      } finally {
        clearTimeout(timer);
      }
      supervise(username);
    };

    try {
      console.log(`[SKILL EXECUTE] Starting '${skill.name}' (${skill.steps.length} steps)...`);
      for (let i = 0; i < skill.steps.length; i++) {
        supervise(username);
        const step = skill.steps[i];
        const p = step.params || {};
        console.log(`[SKILL STEP ${i + 1}/${skill.steps.length}] ${step.action} - ${step.description}`);

        switch (step.action) {
          case 'equip':
            await equip(p.item);
            break;

          case 'place': {
            const offset = p.offset || [0, 0, 0];
            const position = anchor.offset(offset[0], offset[1], offset[2]);
            const existing = bot.blockAt(position);
            if (existing && !['air', 'cave_air', 'void_air', 'grass', 'tall_grass', 'short_grass'].includes(existing.name)) {
              console.log(`[SKILL PLACE] Spot at ${position} is already occupied by ${existing.name}, skipping`);
              break;
            }

            // Find solid support face (prefer top face of block directly below)
            const faces = [
              new Vec3(0, 1, 0),   // ground below
              new Vec3(1, 0, 0),
              new Vec3(-1, 0, 0),
              new Vec3(0, 0, 1),
              new Vec3(0, 0, -1),
              new Vec3(0, -1, 0)
            ];
            const face = faces.find(f => {
              const neighbor = bot.blockAt(position.minus(f));
              return neighbor && neighbor.boundingBox === 'block';
            });

            if (!face) {
              console.warn(`[SKILL PLACE] No solid support block next to ${position}`);
              break;
            }

            // Stand 1.8 blocks away from placement spot so bot is not standing in the block
            const standPos = position.offset(face.x === 0 ? 1 : 0, 0, face.z === 0 ? 1 : 0);
            await approach(standPos);
            await equip(p.item || p.block);
            supervise(username);

            const refBlock = bot.blockAt(position.minus(face));
            bot.lookAt(position, true);
            await bot.placeBlock(refBlock, face);
            await new Promise(r => setTimeout(r, 450)); // Natural placement pacing
            break;
          }

          case 'break': {
            target = p.offset ? bot.blockAt(anchor.offset(...p.offset)) : null;
            if (!target || target.name !== p.block) {
              target = bot.findBlock({ matching: b => b.name === p.block, maxDistance: 16 });
            }
            if (!target) throw new Error(`I can't find ${p.block} nearby.`);
            await approach(target.position);
            if (p.tool) await equip(p.tool);
            supervise(username);
            await bot.dig(target);
            break;
          }

          case 'craft': {
            const item = bot.registry.itemsByName[p.item];
            if (!item) throw new Error(`Unknown recipe output ${p.item}.`);
            const table = bot.findBlock({ matching: b => b.name === 'crafting_table', maxDistance: 16 });
            const recipes = bot.recipesFor(item.id, null, p.count, table);
            const recipe = recipes[0];
            if (!recipe) throw new Error(`I need materials for ${p.item}.`);
            if (recipe.requiresTable) {
              if (!table) throw new Error('I need a crafting table.');
              await approach(table.position);
            }
            supervise(username);
            await bot.craft(recipe, Math.ceil(p.count / recipe.result.count), recipe.requiresTable ? table : null);
            break;
          }

          case 'locate_target':
            target = bot.findBlock({ matching: b => (p.block_types || []).includes(b.name), maxDistance: 16 });
            if (!target) throw new Error('I cannot find the demonstrated target nearby.');
            break;

          case 'approach_target':
            if (!target) throw new Error('Missing target block.');
            await approach(target.position);
            break;

          case 'equip_tool': {
            const tool = bot.inventory.items().find(i => i.name.endsWith('_' + p.preferred));
            if (tool) await bot.equip(tool, 'hand');
            break;
          }

          case 'dig_block':
            if (!target) throw new Error('Missing target block to dig.');
            await bot.dig(target);
            break;

          case 'collect_drop': {
            await new Promise(r => setTimeout(r, 500));
            supervise(username);
            const drop = bot.nearestEntity(e => e.name === 'item' && e.position.distanceTo(bot.entity.position) < 6);
            if (drop) await bot.pathfinder.goto(new GoalNear(drop.position.x, drop.position.y, drop.position.z, 1));
            break;
          }

          default:
            console.log(`[SKILL STEP] Unrecognized step action ${step.action}, continuing`);
            break;
        }
      }

      const matName = (skill.metadata && skill.metadata.material) || 'matching';
      if (placeSteps.length > 0) {
        say(`Finished building the ${matName} wall.`);
      } else {
        say(`Finished ${skill.name}.`);
      }
    } finally {
      executing = false;
      setBusy(false);
      bot.pathfinder.setGoal(null);
    }
    return true;
  }

  function handle(username, message, response) {
    if (response.action === 'execute_skill') {
      handleDecision(username, message, response).catch(err => {
        console.error(`[SKILL ERROR] ${err.message}`);
        say(`I stopped: ${err.message}`);
      });
    }
  }

  function stop() {
    cancelled = true;
    if (executing) {
      bot.pathfinder.stop();
      bot.stopDigging();
      executing = false;
      setBusy(false);
    }
  }

  bot.once('end', () => {
    closed = true;
    clearInterval(supervisionTimer);
    stop();
  });

  return { handle, stop };
}

module.exports = { attachSkillLearning, isOperator };
