import unittest
from minecraft_chat import route_chat
from skills import validate_minecraft_skill
from episode_segmenter import episode_segmenter

class Repo:
    skills = {
        'mine_tree': {'name':'mine_tree','domain':'minecraft','steps':[{'action':'break','params':{'block':'oak_log'}}]},
        'build_wall': {'name':'build_wall','domain':'minecraft','steps':[{'action':'place','params':{'block':'cobblestone','offset':[0,0,0]}}]}
    }
    def get_skill(self, name, domain=None):
        return self.skills.get(name)
    def find_skill(self, name, domain=None):
        return self.skills.get(name)
    def list_skills(self, domain=None):
        return list(self.skills.values())
    def store_skill(self, skill):
        self.skills[skill['name']] = skill
        return skill

class RoutingTests(unittest.TestCase):
    def route(self, text, context=None):
        return route_chat('.Operator said: ' + text, Repo(), ('ambient', {'type': 'respond', 'content': 'Acknowledged.'}, False, ''), context=context)[1]

    def test_referent_resolution_from_buffer(self):
        # Ingest simulated wall placement into episode segmenter
        ev = {'domain': 'minecraft', 'actor': '.Operator', 'action': 'place',
              'params': {'block': 'cobblestone', 'item': 'cobblestone', 'position': [10, 60, 20]}, 'time': 1000}
        episode_segmenter.ingest_event(ev, domain='minecraft')
        a = self.route('see that wall, now you do it', context={'player': '.Operator'})
        self.assertEqual(a['action'], 'execute_skill')
        self.assertIn('Watched you build', a['content'])
        self.assertEqual(a['skill']['name'], 'build_wall')

    def test_buffer_empty_referent_reply(self):
        # Clear segmenter
        episode_segmenter.active_episodes.clear()
        episode_segmenter.rolling_buffer.clear()
        a = self.route('see that wall, now you do it', context={'player': '.Operator'})
        self.assertEqual(a['type'], 'respond')
        self.assertIn("I didn't catch an action sequence in my recent memory buffer", a['content'])

    def test_recall_build_wall(self):
        a = self.route('build a cobblestone wall')
        self.assertEqual(a['action'], 'execute_skill')
        self.assertEqual(a['skill']['name'], 'build_wall')
        self.assertIn('Building a cobblestone wall for you now.', a['content'])

    def test_recall_mine_tree(self):
        a = self.route('mine a tree')
        self.assertEqual(a['action'], 'execute_skill')
        self.assertEqual(a['skill']['name'], 'mine_tree')
        self.assertIn('I\'ll mine that tree while you supervise.', a['content'])

    def test_greeting_no_canned_logs(self):
        a = self.route('hey buddy')
        self.assertEqual(a['type'], 'respond')
        self.assertIn('Hey Operator', a['content'])
        self.assertNotIn('Observation/reflection recorded in memory trace', a['content'])
        self.assertNotIn('learn this as NAME', a['content'])

    def test_validation(self):
        skill = Repo.skills['mine_tree']
        validate_minecraft_skill(skill)
        for step in [{'action':'shell','params':{}},{'action':'place','params':{'block':'stone','offset':[999,0,0]}},{'action':'craft','params':{'item':'stick','count':-1}}]:
            with self.assertRaises(ValueError):
                validate_minecraft_skill({**skill, 'steps': [step]})

if __name__ == '__main__':
    unittest.main()
