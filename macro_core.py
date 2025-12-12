import threading
import time
from pynput import mouse, keyboard
from pynput.keyboard import Key
import input_utils
import random

class MacroCore:
    def __init__(self):
        # Recoil Settings
        self.recoil_enabled = False
        self.recoil_speed_y = 5
        self.recoil_speed_x = 0
        self.recoil_delay = 0.01
        self.recoil_active = False
        self.recoil_mode = 0 # 0: LMB, 1: LMB + RMB
        
        # Auto Clicker Settings
        self.autoclicker_enabled = False
        self.autoclicker_delay = 0.1
        
        # Keyboard Macro Settings
        self.kb_macro_enabled = False
        self.kb_macro_key = 0x1E
        self.kb_macro_delay = 0.1
        self.kb_macro_active = False

        # Anti-AFK Settings
        self.antiafk_enabled = False
        self.antiafk_magnitude = 50  # pixels to move
        self.antiafk_interval = 30.0  # seconds between movements

        # Camera Spin Settings
        self.cameraspin_enabled = False
        self.cameraspin_speed = 5  # pixels per tick
        self.cameraspin_direction = 0  # 0 = right, 1 = left

        # Human Typer Settings
        self.humantyper_active = False
        self.humantyper_wpm_min = 40
        self.humantyper_wpm_max = 80
        self.humantyper_error_rate = 2  # percentage
        self.humantyper_correction_speed = 100  # ms delay for fixing typos
        self.humantyper_max_typos = 1  # max consecutive typos before correction
        self.humantyper_typo_mode = 0  # 0 = adjacent keys, 1 = random letters
        self.humantyper_pause_min = 500  # ms min thinking pause
        self.humantyper_pause_max = 2000  # ms max thinking pause
        self.humantyper_pause_freq = 10  # % chance of pause at word boundary
        self.humantyper_synonym_enabled = False  # synonym swap feature
        self.humantyper_synonym_freq = 5  # % chance of synonym swap per word
        # Sentence pause settings
        self.humantyper_sentence_pause_enabled = True
        self.humantyper_sentence_pause_freq = 80  # % chance to pause after sentence
        self.humantyper_sentence_pause_min = 300  # ms
        self.humantyper_sentence_pause_max = 1000  # ms
        # Paragraph pause settings
        self.humantyper_para_pause_enabled = True
        self.humantyper_para_pause_freq = 90  # % chance to pause after paragraph
        self.humantyper_para_pause_min = 500  # ms
        self.humantyper_para_pause_max = 2000  # ms
        self.humantyper_text = ""
        
        # Synonym dictionary for word swapping (200+ common words)
        self.synonym_dict = {
            # Common adjectives
            'good': ['great', 'nice', 'fine', 'excellent', 'wonderful', 'fantastic'],
            'bad': ['terrible', 'awful', 'poor', 'horrible', 'dreadful', 'lousy'],
            'big': ['large', 'huge', 'massive', 'enormous', 'giant', 'vast'],
            'small': ['tiny', 'little', 'mini', 'compact', 'petite', 'slight'],
            'fast': ['quick', 'rapid', 'speedy', 'swift', 'hasty', 'brisk'],
            'slow': ['sluggish', 'gradual', 'leisurely', 'unhurried', 'lazy'],
            'happy': ['glad', 'joyful', 'pleased', 'delighted', 'cheerful', 'content'],
            'sad': ['unhappy', 'upset', 'down', 'gloomy', 'depressed', 'miserable'],
            'smart': ['clever', 'intelligent', 'bright', 'wise', 'sharp', 'brilliant'],
            'nice': ['pleasant', 'lovely', 'kind', 'friendly', 'agreeable', 'delightful'],
            'easy': ['simple', 'effortless', 'straightforward', 'uncomplicated', 'basic'],
            'hard': ['difficult', 'tough', 'challenging', 'demanding', 'tricky'],
            'new': ['fresh', 'modern', 'recent', 'latest', 'novel', 'current'],
            'old': ['ancient', 'aged', 'vintage', 'outdated', 'antique', 'elderly'],
            'beautiful': ['gorgeous', 'stunning', 'lovely', 'pretty', 'attractive'],
            'ugly': ['unattractive', 'hideous', 'unsightly', 'grotesque', 'plain'],
            'strong': ['powerful', 'mighty', 'sturdy', 'robust', 'tough', 'solid'],
            'weak': ['feeble', 'frail', 'fragile', 'delicate', 'flimsy'],
            'hot': ['warm', 'heated', 'scorching', 'burning', 'boiling'],
            'cold': ['cool', 'chilly', 'freezing', 'icy', 'frigid'],
            'rich': ['wealthy', 'affluent', 'prosperous', 'loaded', 'well-off'],
            'poor': ['broke', 'needy', 'impoverished', 'destitute'],
            'young': ['youthful', 'juvenile', 'teenage', 'adolescent'],
            'angry': ['mad', 'furious', 'irritated', 'annoyed', 'upset', 'enraged'],
            'scared': ['afraid', 'frightened', 'terrified', 'fearful', 'nervous'],
            'brave': ['courageous', 'bold', 'fearless', 'daring', 'valiant'],
            'tired': ['exhausted', 'weary', 'fatigued', 'drained', 'sleepy'],
            'hungry': ['starving', 'famished', 'ravenous', 'peckish'],
            'thirsty': ['parched', 'dehydrated', 'dry'],
            'busy': ['occupied', 'engaged', 'swamped', 'hectic'],
            'quiet': ['silent', 'hushed', 'peaceful', 'calm', 'still'],
            'loud': ['noisy', 'booming', 'deafening', 'thunderous'],
            'clean': ['spotless', 'tidy', 'neat', 'pristine', 'immaculate'],
            'dirty': ['filthy', 'grimy', 'messy', 'unclean', 'soiled'],
            'wet': ['damp', 'moist', 'soaked', 'drenched', 'soggy'],
            'dry': ['arid', 'parched', 'dehydrated', 'barren'],
            'full': ['complete', 'filled', 'packed', 'stuffed', 'loaded'],
            'empty': ['vacant', 'hollow', 'bare', 'blank', 'void'],
            'dark': ['dim', 'shadowy', 'gloomy', 'murky', 'black'],
            'bright': ['brilliant', 'radiant', 'vivid', 'luminous', 'shiny'],
            'safe': ['secure', 'protected', 'guarded', 'sheltered'],
            'dangerous': ['risky', 'hazardous', 'perilous', 'unsafe', 'treacherous'],
            'true': ['correct', 'accurate', 'right', 'factual', 'genuine'],
            'false': ['wrong', 'incorrect', 'untrue', 'fake', 'bogus'],
            'strange': ['weird', 'odd', 'unusual', 'bizarre', 'peculiar'],
            'normal': ['regular', 'ordinary', 'typical', 'standard', 'usual'],
            'perfect': ['flawless', 'ideal', 'excellent', 'impeccable'],
            'terrible': ['awful', 'dreadful', 'horrible', 'atrocious'],
            'amazing': ['incredible', 'astonishing', 'remarkable', 'astounding'],
            'boring': ['dull', 'tedious', 'monotonous', 'uninteresting'],
            'interesting': ['fascinating', 'intriguing', 'engaging', 'captivating'],
            'funny': ['hilarious', 'amusing', 'comical', 'humorous', 'witty'],
            'serious': ['grave', 'solemn', 'earnest', 'stern', 'somber'],
            'simple': ['basic', 'plain', 'straightforward', 'uncomplicated'],
            'complex': ['complicated', 'intricate', 'elaborate', 'sophisticated'],
            'cheap': ['inexpensive', 'affordable', 'economical', 'budget'],
            'expensive': ['costly', 'pricey', 'premium', 'high-end'],
            'important': ['crucial', 'vital', 'essential', 'key', 'significant'],
            'different': ['distinct', 'unique', 'various', 'diverse', 'unlike'],
            'same': ['identical', 'similar', 'equal', 'alike', 'matching'],
            'certain': ['sure', 'confident', 'positive', 'definite'],
            'possible': ['feasible', 'achievable', 'attainable', 'viable'],
            'impossible': ['unachievable', 'unfeasible', 'hopeless'],
            'real': ['genuine', 'authentic', 'actual', 'true', 'legitimate'],
            'fake': ['counterfeit', 'phony', 'bogus', 'false', 'artificial'],
            # Common verbs
            'like': ['enjoy', 'love', 'prefer', 'appreciate', 'fancy', 'adore'],
            'want': ['need', 'desire', 'wish', 'require', 'crave', 'demand'],
            'think': ['believe', 'consider', 'feel', 'suppose', 'reckon', 'assume'],
            'know': ['understand', 'realize', 'recognize', 'comprehend', 'grasp'],
            'see': ['notice', 'observe', 'view', 'spot', 'witness', 'perceive'],
            'make': ['create', 'build', 'produce', 'craft', 'construct', 'form'],
            'use': ['utilize', 'employ', 'apply', 'operate', 'handle'],
            'get': ['obtain', 'acquire', 'receive', 'gain', 'fetch', 'grab'],
            'help': ['assist', 'aid', 'support', 'guide', 'serve'],
            'start': ['begin', 'commence', 'initiate', 'launch', 'kick off'],
            'stop': ['halt', 'cease', 'end', 'quit', 'terminate', 'finish'],
            'work': ['function', 'operate', 'perform', 'labor', 'toil'],
            'change': ['modify', 'alter', 'adjust', 'update', 'revise', 'transform'],
            'go': ['move', 'travel', 'proceed', 'head', 'advance'],
            'come': ['arrive', 'approach', 'reach', 'appear', 'show up'],
            'say': ['state', 'mention', 'declare', 'express', 'announce'],
            'tell': ['inform', 'notify', 'explain', 'describe', 'relate'],
            'ask': ['inquire', 'question', 'request', 'query'],
            'try': ['attempt', 'endeavor', 'strive', 'aim'],
            'give': ['provide', 'offer', 'donate', 'present', 'grant'],
            'take': ['grab', 'seize', 'capture', 'acquire', 'accept'],
            'find': ['discover', 'locate', 'uncover', 'detect', 'spot'],
            'look': ['glance', 'stare', 'gaze', 'peer', 'watch'],
            'put': ['place', 'set', 'position', 'lay', 'deposit'],
            'run': ['sprint', 'dash', 'race', 'jog', 'rush'],
            'walk': ['stroll', 'wander', 'march', 'pace', 'stride'],
            'talk': ['speak', 'chat', 'converse', 'discuss', 'communicate'],
            'eat': ['consume', 'devour', 'munch', 'chew', 'dine'],
            'drink': ['sip', 'gulp', 'swallow', 'consume', 'guzzle'],
            'sleep': ['rest', 'nap', 'doze', 'slumber', 'snooze'],
            'read': ['study', 'browse', 'scan', 'peruse', 'review'],
            'write': ['compose', 'draft', 'pen', 'author', 'inscribe'],
            'buy': ['purchase', 'acquire', 'obtain', 'procure', 'get'],
            'sell': ['trade', 'market', 'vend', 'retail', 'peddle'],
            'pay': ['compensate', 'reimburse', 'remit', 'settle'],
            'send': ['dispatch', 'transmit', 'forward', 'deliver', 'mail'],
            'keep': ['retain', 'hold', 'maintain', 'preserve', 'store'],
            'leave': ['depart', 'exit', 'abandon', 'vacate', 'go'],
            'call': ['phone', 'contact', 'ring', 'dial', 'summon'],
            'wait': ['pause', 'linger', 'stay', 'remain', 'hold on'],
            'meet': ['encounter', 'greet', 'join', 'gather', 'assemble'],
            'show': ['display', 'present', 'demonstrate', 'exhibit', 'reveal'],
            'hide': ['conceal', 'cover', 'mask', 'obscure', 'bury'],
            'break': ['shatter', 'smash', 'crack', 'fracture', 'destroy'],
            'fix': ['repair', 'mend', 'restore', 'correct', 'patch'],
            'hold': ['grasp', 'grip', 'clutch', 'clasp', 'carry'],
            'carry': ['transport', 'haul', 'convey', 'bear', 'lug'],
            'throw': ['toss', 'hurl', 'fling', 'pitch', 'cast'],
            'catch': ['grab', 'snag', 'seize', 'snatch', 'capture'],
            'push': ['shove', 'press', 'thrust', 'propel', 'drive'],
            'pull': ['tug', 'drag', 'yank', 'haul', 'draw'],
            'open': ['unlock', 'unseal', 'unfasten', 'uncover'],
            'close': ['shut', 'seal', 'fasten', 'lock', 'secure'],
            'turn': ['rotate', 'spin', 'twist', 'pivot', 'revolve'],
            'cut': ['slice', 'chop', 'trim', 'carve', 'sever'],
            'move': ['shift', 'transfer', 'relocate', 'budge', 'displace'],
            'sit': ['rest', 'perch', 'settle', 'recline', 'squat'],
            'stand': ['rise', 'erect', 'position', 'halt'],
            'jump': ['leap', 'hop', 'skip', 'bounce', 'spring'],
            'fall': ['drop', 'tumble', 'plunge', 'collapse', 'descend'],
            'hit': ['strike', 'punch', 'slam', 'smack', 'whack'],
            'kill': ['eliminate', 'destroy', 'slay', 'terminate'],
            'die': ['perish', 'expire', 'pass away', 'decease'],
            'live': ['exist', 'reside', 'dwell', 'inhabit', 'survive'],
            'win': ['triumph', 'succeed', 'prevail', 'conquer'],
            'lose': ['misplace', 'forfeit', 'surrender', 'fail'],
            'play': ['perform', 'compete', 'engage', 'participate'],
            'learn': ['study', 'discover', 'master', 'absorb', 'grasp'],
            'teach': ['instruct', 'educate', 'train', 'coach', 'tutor'],
            'grow': ['develop', 'expand', 'increase', 'mature', 'flourish'],
            'build': ['construct', 'create', 'assemble', 'erect', 'establish'],
            'destroy': ['demolish', 'wreck', 'ruin', 'devastate', 'annihilate'],
            'save': ['rescue', 'preserve', 'protect', 'conserve', 'store'],
            'spend': ['use', 'expend', 'consume', 'waste', 'invest'],
            'choose': ['select', 'pick', 'decide', 'opt', 'prefer'],
            'decide': ['determine', 'conclude', 'resolve', 'settle', 'choose'],
            'feel': ['sense', 'perceive', 'experience', 'detect'],
            'remember': ['recall', 'recollect', 'reminisce', 'retain'],
            'forget': ['overlook', 'neglect', 'ignore', 'dismiss'],
            'understand': ['comprehend', 'grasp', 'follow', 'fathom', 'get'],
            'explain': ['describe', 'clarify', 'illustrate', 'elaborate'],
            'agree': ['concur', 'accept', 'consent', 'approve', 'comply'],
            'disagree': ['dispute', 'object', 'oppose', 'differ', 'reject'],
            'allow': ['permit', 'enable', 'authorize', 'let', 'grant'],
            'prevent': ['stop', 'block', 'hinder', 'obstruct', 'prohibit'],
            'increase': ['raise', 'boost', 'enhance', 'expand', 'grow'],
            'decrease': ['reduce', 'lower', 'diminish', 'shrink', 'cut'],
            'improve': ['enhance', 'upgrade', 'better', 'refine', 'advance'],
            'damage': ['harm', 'hurt', 'injure', 'impair', 'wreck'],
            'follow': ['pursue', 'trail', 'track', 'chase', 'accompany'],
            'lead': ['guide', 'direct', 'head', 'conduct', 'steer'],
            'join': ['connect', 'unite', 'combine', 'merge', 'link'],
            'separate': ['divide', 'split', 'detach', 'disconnect', 'part'],
            'enter': ['access', 'join', 'penetrate', 'invade'],
            'exit': ['leave', 'depart', 'withdraw', 'vacate'],
            'attack': ['assault', 'strike', 'charge', 'raid', 'invade'],
            'defend': ['protect', 'guard', 'shield', 'secure', 'safeguard'],
            # Common nouns
            'problem': ['issue', 'trouble', 'difficulty', 'challenge', 'obstacle'],
            'answer': ['response', 'reply', 'solution', 'explanation'],
            'question': ['query', 'inquiry', 'issue', 'concern'],
            'idea': ['thought', 'concept', 'notion', 'plan', 'suggestion'],
            'thing': ['object', 'item', 'stuff', 'matter', 'entity'],
            'place': ['location', 'spot', 'area', 'site', 'position'],
            'time': ['moment', 'period', 'duration', 'occasion', 'instant'],
            'way': ['method', 'manner', 'approach', 'path', 'means'],
            'person': ['individual', 'human', 'someone', 'somebody', 'being'],
            'people': ['individuals', 'folks', 'humans', 'persons', 'citizens'],
            'friend': ['buddy', 'pal', 'companion', 'mate', 'ally'],
            'enemy': ['foe', 'opponent', 'adversary', 'rival', 'nemesis'],
            'money': ['cash', 'funds', 'currency', 'capital', 'wealth'],
            'job': ['work', 'occupation', 'career', 'profession', 'position'],
            'home': ['house', 'residence', 'dwelling', 'abode', 'place'],
            'room': ['chamber', 'space', 'area', 'quarters'],
            'car': ['vehicle', 'automobile', 'auto', 'ride', 'wheels'],
            'food': ['meal', 'cuisine', 'nourishment', 'fare', 'grub'],
            'water': ['liquid', 'fluid', 'beverage', 'drink'],
            'game': ['match', 'contest', 'competition', 'sport', 'activity'],
            'movie': ['film', 'picture', 'flick', 'feature', 'cinema'],
            'book': ['novel', 'publication', 'text', 'volume', 'work'],
            'story': ['tale', 'narrative', 'account', 'report', 'legend'],
            'part': ['piece', 'section', 'portion', 'segment', 'component'],
            'end': ['finish', 'conclusion', 'finale', 'termination', 'close'],
            'beginning': ['start', 'opening', 'onset', 'origin', 'launch'],
            'mistake': ['error', 'blunder', 'slip', 'fault', 'flaw'],
            'chance': ['opportunity', 'possibility', 'occasion', 'shot'],
            'reason': ['cause', 'motive', 'purpose', 'explanation', 'basis'],
            'example': ['instance', 'sample', 'case', 'illustration', 'model'],
            'fact': ['truth', 'reality', 'detail', 'data', 'evidence'],
            'information': ['data', 'details', 'facts', 'intel', 'knowledge'],
            'power': ['strength', 'force', 'energy', 'authority', 'control'],
            'control': ['command', 'authority', 'power', 'dominion', 'rule'],
            'result': ['outcome', 'consequence', 'effect', 'product'],
            'success': ['achievement', 'victory', 'triumph', 'accomplishment'],
            'failure': ['defeat', 'loss', 'flop', 'disaster', 'setback'],
            # Common adverbs
            'very': ['extremely', 'highly', 'really', 'incredibly', 'super'],
            'really': ['truly', 'genuinely', 'actually', 'indeed', 'honestly'],
            'always': ['constantly', 'forever', 'perpetually', 'continually'],
            'never': ['not ever', 'at no time', 'not once'],
            'often': ['frequently', 'regularly', 'commonly', 'repeatedly'],
            'sometimes': ['occasionally', 'periodically', 'at times', 'now and then'],
            'quickly': ['rapidly', 'swiftly', 'speedily', 'hastily', 'promptly'],
            'slowly': ['gradually', 'leisurely', 'unhurriedly', 'steadily'],
            'probably': ['likely', 'possibly', 'perhaps', 'maybe', 'presumably'],
            'definitely': ['certainly', 'absolutely', 'surely', 'positively'],
            'almost': ['nearly', 'practically', 'virtually', 'about', 'approximately'],
            'completely': ['entirely', 'totally', 'fully', 'wholly', 'absolutely'],
            'suddenly': ['abruptly', 'unexpectedly', 'instantly', 'immediately'],
            'finally': ['eventually', 'ultimately', 'lastly', 'at last'],
            'already': ['previously', 'before', 'by now', 'earlier'],
            'still': ['yet', 'even now', 'nevertheless', 'however'],
            'just': ['merely', 'simply', 'only', 'barely', 'exactly'],
            'also': ['too', 'additionally', 'furthermore', 'moreover', 'besides'],
            'only': ['just', 'merely', 'solely', 'simply', 'exclusively'],
            'especially': ['particularly', 'specifically', 'notably', 'mainly'],
            'usually': ['typically', 'normally', 'generally', 'commonly', 'ordinarily'],
            'actually': ['really', 'truly', 'genuinely', 'in fact', 'indeed'],
            'basically': ['essentially', 'fundamentally', 'primarily', 'mainly'],
            'obviously': ['clearly', 'evidently', 'apparently', 'plainly'],
            'exactly': ['precisely', 'accurately', 'specifically', 'correctly'],
            'mainly': ['primarily', 'chiefly', 'mostly', 'largely', 'principally'],
            'mostly': ['mainly', 'largely', 'primarily', 'chiefly', 'generally'],
            'enough': ['sufficiently', 'adequately', 'amply', 'plenty'],
            'together': ['jointly', 'collectively', 'mutually', 'as one'],
            'alone': ['solo', 'independently', 'by oneself', 'solitary'],
        }

        # State
        self.mouse_pressed = False
        self.right_mouse_pressed = False
        
        # Custom Macros
        self.custom_macros = []
        
        # Callbacks
        self.on_recoil_toggle = None
        self.on_autoclick_toggle = None
        self.on_kb_toggle = None
        self.on_antiafk_toggle = None
        self.on_cameraspin_toggle = None
        self.on_humantyper_toggle = None
        self.on_key_bound = None
        self.is_binding = False
        self.on_action_recorded = None
        self.is_recording_action = False
        
        # Key state tracking for debouncing
        self.pressed_keys = set()
        self.active_macro_triggers = set()

        # Threads
        self.running = True
        self.recoil_thread = threading.Thread(target=self._recoil_loop, daemon=True)
        self.autoclicker_thread = threading.Thread(target=self._autoclicker_loop, daemon=True)
        self.kb_macro_thread = threading.Thread(target=self._kb_macro_loop, daemon=True)
        self.antiafk_thread = threading.Thread(target=self._antiafk_loop, daemon=True)
        self.cameraspin_thread = threading.Thread(target=self._cameraspin_loop, daemon=True)
        
        # Listeners
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.key_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)

    def start(self):
        self.recoil_thread.start()
        self.autoclicker_thread.start()
        self.kb_macro_thread.start()
        self.antiafk_thread.start()
        self.cameraspin_thread.start()
        self.mouse_listener.start()
        self.key_listener.start()

    def set_callback(self, autoclick_callback, kb_callback, recoil_callback=None, antiafk_callback=None, cameraspin_callback=None, humantyper_callback=None):
        self.on_autoclick_toggle = autoclick_callback
        self.on_kb_toggle = kb_callback
        self.on_recoil_toggle = recoil_callback
        self.on_antiafk_toggle = antiafk_callback
        self.on_cameraspin_toggle = cameraspin_callback
        self.on_humantyper_toggle = humantyper_callback
        
    def start_key_binding(self, callback):
        self.on_key_bound = callback
        self.is_binding = True

    def start_action_recording(self, callback):
        self.on_action_recorded = callback
        self.is_recording_action = True
        
    def stop_action_recording(self):
        self.is_recording_action = False
        self.on_action_recorded = None

    def stop(self):
        self.running = False
        self._release_all_keys()
        self.mouse_listener.stop()
        self.key_listener.stop()
    
    def _release_all_keys(self):
        # Release any keys from custom macros
        for macro in self.custom_macros:
            for sc in macro.get('actions', []):
                try:
                    input_utils.release_key(int(sc))
                except:
                    pass
        # Release common modifier keys
        common_keys = [0x1D, 0x2A, 0x36, 0x38]  # Ctrl, LShift, RShift, Alt
        for sc in common_keys:
            try:
                input_utils.release_key(sc)
            except:
                pass

    def _update_recoil_active(self):
        if self.recoil_mode == 0: # LMB Only
            self.recoil_active = self.recoil_enabled and self.mouse_pressed
        else: # LMB + RMB
            self.recoil_active = self.recoil_enabled and self.mouse_pressed and self.right_mouse_pressed

    def _on_click(self, x, y, button, pressed):
        if self.is_binding and pressed:
            # Capture Mouse Bind
            btn_name = str(button).split('.')[-1] # "left", "right", "x1", "x2"
            if self.on_key_bound:
                # Store as convenient dict or string, but for UI feedback string is good.
                # The generic callback expects a name.
                self.on_key_bound({'type': 'mouse', 'value': btn_name, 'name': f"Mouse {btn_name.title()}"})
            self.is_binding = False
            return

        # Check Triggers
        if pressed and self.custom_macros:
            btn_name = str(button).split('.')[-1]
            for macro in self.custom_macros:
                trig = macro.get('trigger')
                if trig and trig['type'] == 'mouse' and trig['value'] == btn_name:
                    threading.Thread(target=self.execute_custom_macro, args=(macro['id'], macro['actions'],), daemon=True).start()
        
        # Stop macros when mouse button is released
        if not pressed and self.custom_macros:
            btn_name = str(button).split('.')[-1]
            for macro in self.custom_macros:
                trig = macro.get('trigger')
                if trig and trig['type'] == 'mouse' and trig['value'] == btn_name:
                    self.active_macro_triggers.discard(macro['id'])

        if button == mouse.Button.left:
            self.mouse_pressed = pressed
            self._update_recoil_active()
        elif button == mouse.Button.right:
            self.right_mouse_pressed = pressed
            self._update_recoil_active()

    def _on_press(self, key):
        if self.is_recording_action:
            try:
                if hasattr(key, 'vk'): sc = input_utils.get_scan_code(key.vk)
                else: sc = input_utils.get_scan_code(key.value.vk)
                if self.on_action_recorded:
                     self.on_action_recorded(sc)
            except:
                pass
            return

        if self.is_binding:
            try:
                if hasattr(key, 'vk'):
                    vk = key.vk
                    sc = input_utils.get_scan_code(vk)
                    name = key.char if hasattr(key, 'char') else str(vk)
                else:
                    vk = key.value.vk
                    sc = input_utils.get_scan_code(vk)
                    name = key.name
                
                # Default behavior for single key bind (legacy KB macro support)
                # But now we might be binding a custom macro trigger.
                # The callback determines what to do.
                
                # If it's the specific KB macro binding, we update the internal key.
                # But wait, self.kb_macro_key is specific to the "Keyboard Macro" feature.
                # If we are binding a custom macro, we shouldn't overwrite self.kb_macro_key.
                
                # To distinguish, we can rely on the callback handling the data.
                # Passing a dict gives the callback more info.
                
                trigger_data = {'type': 'key', 'value': sc, 'name': str(name).upper()}
                
                if self.on_key_bound:
                    self.on_key_bound(trigger_data)
                
                self.is_binding = False
            except Exception as e:
                print(f"Binding error: {e}")
                self.is_binding = False
            return

        # Check Triggers
        if self.custom_macros:
            try:
                # Resolve SC for comparison
                if hasattr(key, 'vk'): sc = input_utils.get_scan_code(key.vk)
                else: sc = input_utils.get_scan_code(key.value.vk)
                
                # Only trigger if this key wasn't already pressed (debounce auto-repeat)
                if sc not in self.pressed_keys:
                    self.pressed_keys.add(sc)
                    for macro in self.custom_macros:
                        trig = macro.get('trigger')
                        if trig and trig['type'] == 'key' and int(trig['value']) == sc:
                            threading.Thread(target=self.execute_custom_macro, args=(macro['id'], macro['actions'],), daemon=True).start()
            except:
                pass

        if key == Key.f4: # Recoil toggle
            self.recoil_enabled = not self.recoil_enabled
            self._update_recoil_active()
            if self.on_recoil_toggle:
                self.on_recoil_toggle(self.recoil_enabled)
            return

        if key == Key.f6: # Auto clicker toggle
            self.autoclicker_enabled = not self.autoclicker_enabled
            if self.on_autoclick_toggle:
                self.on_autoclick_toggle(self.autoclicker_enabled)
            return

        if key == Key.f5: # KB Macro toggle
            self.kb_macro_enabled = not self.kb_macro_enabled
            if self.on_kb_toggle:
                self.on_kb_toggle(self.kb_macro_enabled)
            return

        if key == Key.f7: # Anti-AFK toggle
            self.antiafk_enabled = not self.antiafk_enabled
            if self.on_antiafk_toggle:
                self.on_antiafk_toggle(self.antiafk_enabled)
            return

        if key == Key.f8: # Camera Spin toggle
            self.cameraspin_enabled = not self.cameraspin_enabled
            if self.on_cameraspin_toggle:
                self.on_cameraspin_toggle(self.cameraspin_enabled)
            return
            
    def execute_custom_macro(self, macro_id, actions):
        # Repeats actions while trigger is held
        self.active_macro_triggers.add(macro_id)
        try:
            while macro_id in self.active_macro_triggers and self.running:
                for sc in actions:
                    input_utils.press_key(int(sc))
                time.sleep(0.05)
                for sc in actions:
                    input_utils.release_key(int(sc))
                time.sleep(0.05)  # Repeat delay
        finally:
            # Ensure keys are released when stopping
            for sc in actions:
                try:
                    input_utils.release_key(int(sc))
                except:
                    pass

    def update_custom_macros(self, macros):
        self.custom_macros = macros

    def _on_release(self, key):
        try:
            if hasattr(key, 'vk'): sc = input_utils.get_scan_code(key.vk)
            else: sc = input_utils.get_scan_code(key.value.vk)
            self.pressed_keys.discard(sc)
            
            # Stop any macros triggered by this key
            for macro in self.custom_macros:
                trig = macro.get('trigger')
                if trig and trig['type'] == 'key' and int(trig['value']) == sc:
                    self.active_macro_triggers.discard(macro['id'])
        except:
            pass

    def _recoil_loop(self):
        while self.running:
            if self.recoil_active:
                input_utils.move_relative(int(self.recoil_speed_x), int(self.recoil_speed_y))
                time.sleep(self.recoil_delay)
            else:
                time.sleep(0.01)

    def _autoclicker_loop(self):
        while self.running:
            if self.autoclicker_enabled:
                input_utils.click()
                time.sleep(self.autoclicker_delay)
            else:
                time.sleep(0.01)
    
    def _kb_macro_loop(self):
        while self.running:
            if self.kb_macro_enabled:
                input_utils.press_key(self.kb_macro_key)
                time.sleep(0.05)
                input_utils.release_key(self.kb_macro_key)
                time.sleep(self.kb_macro_delay)
            else:
                time.sleep(0.01)

    def _antiafk_loop(self):
        import math
        while self.running:
            if self.antiafk_enabled:
                # Generate random direction using angle
                angle = random.uniform(0, 2 * math.pi)
                magnitude = self.antiafk_magnitude
                
                # Calculate direction vector
                dx_per_step = math.cos(angle)
                dy_per_step = math.sin(angle)
                
                # Move smoothly outward with random variable speed
                step_size = random.randint(1, 3)  # random pixels per step
                steps = int(magnitude / step_size)
                
                for _ in range(steps):
                    if not self.antiafk_enabled or not self.running:
                        break
                    # Randomize delay for harder detection
                    delay_per_step = random.uniform(0.001, 0.005)
                    move_x = int(round(dx_per_step * step_size))
                    move_y = int(round(dy_per_step * step_size))
                    input_utils.move_relative(move_x, move_y)
                    time.sleep(delay_per_step)
                
                time.sleep(random.uniform(0.03, 0.08))  # random pause before returning
                
                # Move smoothly back with random speed
                for _ in range(steps):
                    if not self.running:
                        break
                    delay_per_step = random.uniform(0.001, 0.005)
                    move_x = int(round(-dx_per_step * step_size))
                    move_y = int(round(-dy_per_step * step_size))
                    input_utils.move_relative(move_x, move_y)
                    time.sleep(delay_per_step)
                
                # Wait for interval
                time.sleep(self.antiafk_interval)
            else:
                time.sleep(0.1)

    def _cameraspin_loop(self):
        while self.running:
            if self.cameraspin_enabled:
                # Continuously move mouse horizontally (spinning camera)
                # Direction: 0 = right (positive), 1 = left (negative)
                direction = 1 if self.cameraspin_direction == 0 else -1
                input_utils.move_relative(self.cameraspin_speed * direction, 0)
                time.sleep(0.01)  # 100 ticks per second for smooth spin
            else:
                time.sleep(0.1)


    # Methods for GUI to update settings
    def update_recoil(self, enabled, speed_y, speed_x, delay, mode):
        self.recoil_enabled = enabled
        self.recoil_speed_y = speed_y
        self.recoil_speed_x = speed_x
        self.recoil_delay = delay
        self.recoil_mode = mode
        self._update_recoil_active()

    def update_autoclicker(self, enabled, delay):
        self.autoclicker_enabled = enabled
        self.autoclicker_delay = delay
    
    def update_kb_macro(self, enabled, key_code, delay):
        self.kb_macro_enabled = enabled
        self.kb_macro_key = key_code
        self.kb_macro_delay = delay

    def update_antiafk(self, enabled, magnitude, interval):
        self.antiafk_enabled = enabled
        self.antiafk_magnitude = magnitude
        self.antiafk_interval = interval

    def update_cameraspin(self, enabled, speed, direction):
        self.cameraspin_enabled = enabled
        self.cameraspin_speed = speed
        self.cameraspin_direction = direction

    def update_humantyper(self, wpm_min, wpm_max, error_rate, correction_speed, max_typos, typo_mode, pause_min, pause_max, pause_freq, synonym_enabled, synonym_freq, sentence_pause_enabled, sentence_pause_freq, sentence_pause_min, sentence_pause_max, para_pause_enabled, para_pause_freq, para_pause_min, para_pause_max):
        self.humantyper_wpm_min = wpm_min
        self.humantyper_wpm_max = wpm_max
        self.humantyper_error_rate = error_rate
        self.humantyper_correction_speed = correction_speed
        self.humantyper_max_typos = max_typos
        self.humantyper_typo_mode = typo_mode
        self.humantyper_pause_min = pause_min
        self.humantyper_pause_max = pause_max
        self.humantyper_pause_freq = pause_freq
        self.humantyper_synonym_enabled = synonym_enabled
        self.humantyper_synonym_freq = synonym_freq
        self.humantyper_sentence_pause_enabled = sentence_pause_enabled
        self.humantyper_sentence_pause_freq = sentence_pause_freq
        self.humantyper_sentence_pause_min = sentence_pause_min
        self.humantyper_sentence_pause_max = sentence_pause_max
        self.humantyper_para_pause_enabled = para_pause_enabled
        self.humantyper_para_pause_freq = para_pause_freq
        self.humantyper_para_pause_min = para_pause_min
        self.humantyper_para_pause_max = para_pause_max

    def start_humantyper(self, text):
        if self.humantyper_active:
            return  # Already typing
        self.humantyper_text = text
        self.humantyper_active = True
        threading.Thread(target=self._humantyper_run, daemon=True).start()

    def _humantyper_run(self):
        from pynput.keyboard import Controller as KeyboardController
        kb = KeyboardController()
        
        # Common keyboard typo neighbors
        typo_neighbors = {
            'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'erfcxs', 'e': 'rdsw',
            'f': 'tgvcd', 'g': 'yhbvf', 'h': 'ujnbg', 'i': 'uojk', 'j': 'ikmnh',
            'k': 'olji', 'l': 'pok', 'm': 'njk', 'n': 'bhjm', 'o': 'iplk',
            'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'wazxde', 't': 'ryfg',
            'u': 'yihj', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tugh',
            'z': 'asx'
        }
        
        def type_char_with_delay(char):
            """Type a single character with appropriate delay and potential typos."""
            current_wpm = random.uniform(self.humantyper_wpm_min, self.humantyper_wpm_max)
            chars_per_minute = current_wpm * 5
            base_delay = 60.0 / chars_per_minute
            delay = base_delay * random.uniform(0.7, 1.3)
            
            # Add longer pause at punctuation
            if char in '.!?':
                delay += random.uniform(0.2, 0.5)
                # Sentence pause
                if self.humantyper_sentence_pause_enabled and random.random() * 100 < self.humantyper_sentence_pause_freq:
                    pause_time = random.uniform(
                        self.humantyper_sentence_pause_min / 1000.0,
                        self.humantyper_sentence_pause_max / 1000.0
                    )
                    time.sleep(pause_time)
            elif char in ',;:':
                delay += random.uniform(0.1, 0.2)
            elif char == '\n':
                # Paragraph pause
                if self.humantyper_para_pause_enabled and random.random() * 100 < self.humantyper_para_pause_freq:
                    pause_time = random.uniform(
                        self.humantyper_para_pause_min / 1000.0,
                        self.humantyper_para_pause_max / 1000.0
                    )
                    time.sleep(pause_time)
            elif char == ' ':
                delay += random.uniform(0.01, 0.05)
                # Thinking pause at word boundaries
                if random.random() * 100 < self.humantyper_pause_freq:
                    pause_time = random.uniform(
                        self.humantyper_pause_min / 1000.0,
                        self.humantyper_pause_max / 1000.0
                    )
                    time.sleep(pause_time)
            
            # Simulate typo based on error rate
            if random.random() * 100 < self.humantyper_error_rate:
                lower_char = char.lower()
                num_typos = random.randint(1, max(1, self.humantyper_max_typos))
                
                for _ in range(num_typos):
                    if self.humantyper_typo_mode == 0:
                        if lower_char in typo_neighbors and typo_neighbors[lower_char]:
                            wrong_char = random.choice(typo_neighbors[lower_char])
                        else:
                            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    else:
                        wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    kb.type(wrong_char)
                    time.sleep(delay * 0.5)
                
                correction_delay = self.humantyper_correction_speed / 1000.0
                time.sleep(random.uniform(correction_delay * 0.5, correction_delay * 1.5))
                
                for _ in range(num_typos):
                    kb.press(Key.backspace)
                    kb.release(Key.backspace)
                    time.sleep(random.uniform(0.08, 0.18))
            
            try:
                kb.type(char)
            except Exception:
                pass
            time.sleep(delay)
        
        def type_word(word):
            """Type a word character by character."""
            for char in word:
                if not self.humantyper_active or not self.running:
                    return False
                type_char_with_delay(char)
            return True
        
        def delete_word(word_len):
            """Delete a word by pressing backspace."""
            for _ in range(word_len):
                kb.press(Key.backspace)
                kb.release(Key.backspace)
                time.sleep(random.uniform(0.08, 0.15))
        
        if self.on_humantyper_toggle:
            self.on_humantyper_toggle(True)
        
        # Parse text into tokens (words and non-words)
        import re
        tokens = re.findall(r'\b\w+\b|[^\w]+', self.humantyper_text)
        
        for token in tokens:
            if not self.humantyper_active or not self.running:
                break
            
            # Check if this is a word (alphanumeric)
            if token.isalpha():
                word_lower = token.lower()
                
                # Check for synonym swap
                if (self.humantyper_synonym_enabled and 
                    word_lower in self.synonym_dict and 
                    random.random() * 100 < self.humantyper_synonym_freq):
                    
                    # Pick a random synonym
                    synonym = random.choice(self.synonym_dict[word_lower])
                    
                    # Preserve original case
                    if token.isupper():
                        synonym = synonym.upper()
                    elif token[0].isupper():
                        synonym = synonym.capitalize()
                    
                    # Type the synonym first
                    if not type_word(synonym):
                        break
                    
                    # Pause to "think" about the mistake
                    think_time = random.uniform(0.5, 1.5)
                    time.sleep(think_time)
                    
                    # Delete the synonym
                    delete_word(len(synonym))
                    
                    # Small pause before typing correct word
                    time.sleep(random.uniform(0.1, 0.3))
                    
                    # Type the correct word
                    if not type_word(token):
                        break
                else:
                    # Normal word typing
                    if not type_word(token):
                        break
            else:
                # Type non-word characters (spaces, punctuation, etc.)
                for char in token:
                    if not self.humantyper_active or not self.running:
                        break
                    type_char_with_delay(char)
        
        self.humantyper_active = False
        if self.on_humantyper_toggle:
            self.on_humantyper_toggle(False)

core = MacroCore()
