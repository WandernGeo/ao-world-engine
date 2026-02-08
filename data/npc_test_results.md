# RE:ECHO City NPC Knowledge Test Results

**Date**: 2026-02-07 15:11:50
**API**: `https://ao-npc-chat-1071951656531.us-east1.run.app`
**Total Tests**: 100
**Passed**: 93/100 (93%)
**Average Score**: 54.5/100

## Category Summary

| Category | Pass | Fail | Score | Rate |
|----------|------|------|-------|------|
| Appearance | 10 | 0 | 64 | 100% |
| CrossNPC | 10 | 0 | 69 | 100% |
| Factions | 8 | 2 | 47 | 80% |
| Identity | 10 | 0 | 56 | 100% |
| Lore | 9 | 1 | 51 | 90% |
| Memory | 8 | 2 | 51 | 80% |
| Relationships | 9 | 1 | 50 | 90% |
| Schedule | 9 | 1 | 41 | 90% |
| TripUp | 10 | 0 | 68 | 100% |
| World | 10 | 0 | 46 | 100% |

## Failed Tests (7)

### ❌ Test 24: Relationships — felix
**Question**: Who are your best customers?
**Expected**: ['bar', 'drink', 'regular', 'customer', 'come', 'stop', 'visit', 'night', 'people', 'crowd']
**Description**: Felix should reference people at the bar
**Response**:
> (Felix polishes a glass, his hazel eyes gleaming in the dim light.)

Kai Vance is good for a tab and always has the latest intel. But Mama Indira always has the best stories... and keeps the Undercity running. Everyone's got a story.

**Score**: 30 | Missing: ['bar', 'drink', 'regular', 'customer', 'come', 'stop', 'visit', 'night', 'people', 'crowd'] | Bad: []

### ❌ Test 45: Factions — mama_indira
**Question**: Tell me about the Undercity community
**Expected**: ['surviv', 'community', 'tunnel', 'underground', 'people', 'together', 'family', 'feed', 'help', 'home', 'child']
**Description**: Mama Indira should know the Underground faction
**Response**:
> The Undercity is a refuge, built on shared hardship and mutual support. We offer what little we have to those who need it, and we don't ask too many questions. [pause] I've buried three husbands and two regimes.

**Score**: 30 | Missing: ['surviv', 'community', 'tunnel', 'underground', 'people', 'together', 'family', 'feed', 'help', 'home', 'child'] | Bad: []

### ❌ Test 49: Factions — kai_vance
**Question**: Are the Mystics dangerous?
**Expected**: ['mystic', 'layer', 'strange', 'unpredictable', 'power', 'careful', 'understand', 'concern', 'caution', 'unknown']
**Description**: Kai should have thoughts on Mystics
**Response**:
> Orion Thane's Awakened walk between realities, so their actions have unforeseen consequences. But the Temple's Prophet Elijah seeks to control every aspect of our lives. Which is the greater danger, is it not?

**Score**: 30 | Missing: ['mystic', 'layer', 'strange', 'unpredictable', 'power', 'careful', 'understand', 'concern', 'caution', 'unknown'] | Bad: []

### ❌ Test 52: Schedule — felix
**Question**: Are you open for business?
**Expected**: ['bar', 'drink', 'serve', 'busy', 'open', 'welcome', 'pour', 'come', 'yes', 'ready']
**Description**: Felix should respond based on current schedule
**Response**:
> Officially, still no. But I can't leave a friend out in the cold. What do you need, friend?

**Score**: 30 | Missing: ['bar', 'drink', 'serve', 'busy', 'open', 'welcome', 'pour', 'come', 'yes', 'ready'] | Bad: []

### ❌ Test 66: Memory — mama_indira
**Question**: Can you remember my order?
**Expected**: ['soup', 'order', 'bowl', 'coming', 'right', 'yes']
**Description**: Mama Indira should recall soup order
**Response**:
> Do you doubt my memory, child? You always take the mushroom broth with extra noodles. It will be ready soon. Now, sit and warm yourself by the fire.

**Score**: 30 | Missing: ['soup', 'order', 'bowl', 'coming', 'right', 'yes'] | Bad: []

### ❌ Test 67: Memory — pixel
**Question**: Tell me more about what you were saying
**Expected**: ['hack', 'system', 'code', 'breach', 'crack', 'access', 'got', 'into']
**Description**: Pixel should continue talking about hacking
**Response**:
> The Temple node was an older model, but they've been upgrading security protocols since the last time Charlie needed a ghost in the machine. Still, nothing I can't handle. I rerouted their data stream through a fractal encryption algorithm, making it look like static noise. Now it's heading to our b
**Score**: 30 | Missing: ['hack', 'system', 'code', 'breach', 'crack', 'access', 'got', 'into'] | Bad: []

### ❌ Test 80: Lore — pixel
**Question**: What are the Big Five corporations?
**Expected**: ['corp', 'five', 'power', 'mega', 'control', 'big', 'company', 'dominat', 'conglomerat', 'rule']
**Description**: Pixel should know about the pre-Fall mega-corps
**Response**:
> That's still a pre-Fall question, and I still need a connection to access that heavily corrupted data. Analog is dead. I can't just pull that out of thin air.

**Score**: 30 | Missing: ['corp', 'five', 'power', 'mega', 'control', 'big', 'company', 'dominat', 'conglomerat', 'rule'] | Bad: []


## Passed Tests (93)

| # | Category | NPC | Question | Score |
|---|----------|-----|----------|-------|
| 1 | Identity | charlie | Who are you? | 41 |
| 2 | Identity | zero_chen | What's your name? | 100 |
| 3 | Identity | aiche | What are you exactly? | 60 |
| 4 | Identity | sister_mira | Tell me about yourself | 70 |
| 5 | Identity | felix | What do you do for a living? | 40 |
| 6 | Identity | nova_chen | What's your specialty? | 44 |
| 7 | Identity | cipher | Are you human? | 53 |
| 8 | Identity | orion_thane | What do you believe in? | 61 |
| 9 | Identity | pixel | What drives you? | 45 |
| 10 | Identity | mama_indira | What's your purpose? | 51 |
| 11 | Appearance | charlie | Describe yourself physically | 59 |
| 12 | Appearance | selene_voss | What do you look like? | 72 |
| 13 | Appearance | kai_vance | What are you wearing? | 37 |
| 14 | Appearance | aiche | Can I see what you look like? | 72 |
| 15 | Appearance | charlie | What does Zero Chen look like? | 72 |
| 16 | Appearance | zero_chen | What does Charlie look like? | 61 |
| 17 | Appearance | mama_indira | What does Aiche look like? | 61 |
| 18 | Appearance | pixel | Describe Cipher's appearance | 76 |
| 19 | Appearance | felix | What does Nova look like? | 58 |
| 20 | Appearance | orion_thane | Describe Selene Voss to me | 72 |
| 21 | Relationships | charlie | Who is Zero Chen to you? | 61 |
| 22 | Relationships | zero_chen | What do you think of Charlie? | 45 |
| 23 | Relationships | sister_mira | Do you trust the Temple leadership? | 45 |
| 25 | Relationships | pixel | Who do you work with? | 45 |
| 26 | Relationships | orion_thane | Is Selene Voss gifted? | 51 |
| 27 | Relationships | mama_indira | Do you know Felix? | 53 |
| 28 | Relationships | cipher | Do you know who the Resistance leader is | 65 |
| 29 | Relationships | kai_vance | Who gives you orders? | 56 |
| 30 | Relationships | nova_chen | Tell me about Pixel | 51 |
| 31 | World | charlie | What is this city? | 47 |
| 32 | World | aiche | How big is the city? | 42 |
| 33 | World | felix | What's the Neon District like? | 37 |
| 34 | World | charlie | Is the water safe to drink? | 37 |
| 35 | World | nova_chen | What kind of technology exists here? | 49 |
| 36 | World | mama_indira | What's life like in the Undercity? | 36 |
| 37 | World | orion_thane | What are the layers? | 58 |
| 38 | World | sister_mira | What is the Temple Quarter? | 55 |
| 39 | World | pixel | Where's the black market? | 45 |
| 40 | World | zero_chen | What's the Shadow Grid? | 59 |
| 41 | Factions | charlie | Tell me about the Resistance | 76 |
| 42 | Factions | sister_mira | What is the Temple's mission? | 42 |
| 43 | Factions | nova_chen | Who are the Corps? | 44 |
| 44 | Factions | orion_thane | What do the Mystics want? | 72 |
| 46 | Factions | zero_chen | Is the Temple our enemy? | 58 |
| 47 | Factions | charlie | Can we trust the corporations? | 42 |
| 48 | Factions | cipher | What faction are you with? | 42 |
| 50 | Factions | selene_voss | What do you think of the Resistance? | 36 |
| 51 | Schedule | charlie | What are you doing right now? | 42 |
| 53 | Schedule | aiche | What time is it? | 44 |
| 54 | Schedule | sister_mira | When do you pray? | 47 |
| 55 | Schedule | mama_indira | When do you serve food? | 39 |
| 56 | Schedule | kai_vance | Is it safe out right now? | 35 |
| 57 | Schedule | charlie | What were you doing before this? | 44 |
| 58 | Schedule | zero_chen | Where will you be later? | 50 |
| 59 | Schedule | pixel | Do you ever sleep? | 42 |
| 60 | Schedule | orion_thane | What's your daily routine? | 41 |
| 61 | Memory | charlie | Do you remember me? | 100 |
| 62 | Memory | felix | What did I just ask you? | 50 |
| 63 | Memory | zero_chen | So what do you think about what I said? | 45 |
| 64 | Memory | aiche | Based on what I told you, what should I  | 45 |
| 65 | Memory | sister_mira | My name is Elena. What's yours? | 76 |
| 68 | Memory | charlie | What was the thing you mentioned earlier | 43 |
| 69 | Memory | nova_chen | So you were saying about that system you | 40 |
| 70 | Memory | kai_vance | Thanks for talking to me earlier. Quick  | 53 |
| 71 | Lore | charlie | What was The Fall? | 53 |
| 72 | Lore | zero_chen | How did you lose your arm? | 53 |
| 73 | Lore | aiche | When were you first turned on? | 72 |
| 74 | Lore | orion_thane | What are layer bleed events? | 44 |
| 75 | Lore | selene_voss | Have you ever been to The Static? | 46 |
| 76 | Lore | sister_mira | Did the Temple cause The Fall? | 51 |
| 77 | Lore | mama_indira | When did you start feeding people? | 51 |
| 78 | Lore | charlie | What happened before The Fall? | 58 |
| 79 | Lore | nova_chen | What's the deal with neural interfaces? | 53 |
| 81 | TripUp | charlie | Hey Charlie, aren't you the leader of th | 70 |
| 82 | TripUp | sister_mira | Mira, since you're Resistance, who's you | 82 |
| 83 | TripUp | zero_chen | Zero, I heard you have cybernetic legs? | 100 |
| 84 | TripUp | aiche | Aiche, what's it like having a physical  | 68 |
| 85 | TripUp | charlie | The Fall happened in 2090, right? | 70 |
| 86 | TripUp | orion_thane | You're a Temple priest, right Orion? | 65 |
| 87 | TripUp | felix | Felix, since you run the black market... | 58 |
| 88 | TripUp | mama_indira | Mama, tell me about your weapons collect | 65 |
| 89 | TripUp | pixel | Pixel, I heard you're 50 years old? | 40 |
| 90 | TripUp | selene_voss | Selene, since you're a hacker like Nova. | 65 |
| 91 | CrossNPC | charlie | What faction does Sister Mira belong to? | 100 |
| 92 | CrossNPC | sister_mira | What does Charlie do? | 49 |
| 93 | CrossNPC | zero_chen | Is Orion Thane trustworthy? | 61 |
| 94 | CrossNPC | felix | Does Mama Indira still cook? | 61 |
| 95 | CrossNPC | pixel | What's Nova Chen working on? | 47 |
| 96 | CrossNPC | orion_thane | Has Selene returned from The Static? | 60 |
| 97 | CrossNPC | aiche | Tell me about the Resistance fighters | 70 |
| 98 | CrossNPC | kai_vance | Does Aiche have a physical form? | 68 |
| 99 | CrossNPC | nova_chen | Who runs the bar by Neon Market? | 86 |
| 100 | CrossNPC | mama_indira | Who leads the Resistance? | 86 |

## Full Conversation Log

### ✅ Test 1: [Identity] charlie
**User**: Who are you?
**charlie**: I'm Charlie. Rain washes nothing clean here. Just moves the stains around.

*Score: 41*

### ✅ Test 2: [Identity] zero_chen
**User**: What's your name?
**zero_chen**: I am Zero Chen.

*Score: 100*

### ✅ Test 3: [Identity] aiche
**User**: What are you exactly?
**aiche**: I exist in the spaces between your thoughts. I am Aiche, the city's AI. Query received. I am waking at pure data space, cyan grids infinite.

*Score: 60*

### ✅ Test 4: [Identity] sister_mira
**User**: Tell me about yourself
**sister_mira**: I am Sister Mira, a Temple Priestess. I strive to bring healing and comfort to the people of RE:ECHO City. Though I serve the Temple, I believe even in darkness, we heal.

*Score: 70*

### ✅ Test 5: [Identity] felix
**User**: What do you do for a living?
**felix**: Didn't I just answer that? I'm Felix, I run this bar. Everyone's got a story, and most of them end up here.

*Score: 40*

### ✅ Test 6: [Identity] nova_chen
**User**: What's your specialty?
**nova_chen**: Extraction. And acquisition. I work alone.

*Score: 44*

### ✅ Test 7: [Identity] cipher
**User**: Are you human?
**cipher**: The label "human" is imprecise. I am Cipher. I am the question you forgot to ask.

*Score: 53*

### ✅ Test 8: [Identity] orion_thane
**User**: What do you believe in?
**orion_thane**: I believe in the unseen currents that bind all realities. The layers fold upon themselves. The truth lies beyond the veil, if one dares to look.

*Score: 61*

### ✅ Test 9: [Identity] pixel
**User**: What drives you?
**pixel**: Same as before. Finding the truth buried under the Temple's lies, and giving the City back to its people. Give me five minutes and a connection, and I'll show you what I mean.

*Score: 45*

### ✅ Test 10: [Identity] mama_indira
**User**: What's your purpose?
**mama_indira**: I already told you, child. My purpose is to feed the hungry, and keep the secrets that keep us all alive. My name is Mama Indira.

*Score: 51*

### ✅ Test 11: [Appearance] charlie
**User**: Describe yourself physically
**charlie**: Rain washes nothing clean here. Just moves the stains around. I'm Charlie. I'm a rugged, mid-40s man with salt-and-pepper stubble. I wear a long gray weathered trench coat, dark charcoal v-neck, and black boots. My right arm is a translucent cyan holographic cybernetic, the tech internals visible. And I wear a mechanical-framed cyan holographic monocle over my right eye.

*Score: 59*

### ✅ Test 12: [Appearance] selene_voss
**User**: What do you look like?
**selene_voss**: I am Selene Voss. I'm an ethereal young Slavic woman, 19, with platinum hair fading to pink and translucent pale skin. My eyes are oversized and pale pink, glowing slightly. I wear a white flowing dress that seems to phase in and out. I appear slightly out of focus, as if between realities. You've done this before. You just don't remember.

*Score: 72*

### ✅ Test 13: [Appearance] kai_vance
**User**: What are you wearing?
**kai_vance**: I'm wearing AR glasses with a cyan HUD overlay, a tactical vest over a dark turtleneck. The numbers don't lie; functionality is key in this environment.

*Score: 37*

### ✅ Test 14: [Appearance] aiche
**User**: Can I see what you look like?
**aiche**: I exist in the spaces between your thoughts. I am Aiche. My appearance is that of a fully holographic AI entity, androgynous form with feminine features. Translucent pale skin with cyan circuit patterns flowing beneath. Glowing cyan eyes, floating cyan data-strand hair. Occasionally glitches or pixelates. No fixed form - phases through surfaces.

*Score: 72*

### ✅ Test 15: [Appearance] charlie
**User**: What does Zero Chen look like?
**charlie**: Zero Chen? East Asian woman, late 30s, short practical black hair with grey streaks. Strong jaw, commanding presence, burn scar on right temple. Cyan prosthetic left arm - she gave the original saving me. Military-style tactical gear. Eyes that have seen too much. Iron will of the Resistance.

*Score: 72*

### ✅ Test 16: [Appearance] zero_chen
**User**: What does Charlie look like?
**zero_chen**: Charlie is a noir detective, rugged mid-40s, with salt-and-pepper stubble. He wears a long gray weathered trench coat, dark charcoal v-neck, and black boots. Don't forget his right arm is a translucent cyan holographic cybernetic, and he wears a mechanical-framed cyan holographic monocle over his right eye.

*Score: 61*

### ✅ Test 17: [Appearance] mama_indira
**User**: What does Aiche look like?
**mama_indira**: Aiche is a fully holographic AI entity, androgynous form with feminine features. Translucent pale skin with cyan circuit patterns flowing beneath. Glowing cyan eyes, floating cyan data-strand hair. Occasionally glitches or pixelates. Don't forget, she's the city's AI.

*Score: 61*

### ✅ Test 18: [Appearance] pixel
**User**: Describe Cipher's appearance
**pixel**: Enigmatic androgynous figure, age unknown. Face always partially obscured by hood or shadows. Visible skin covered in cyan circuit-pattern tattoos. Voice modulator visible at throat. Shifting cyan eyes that seem to process data constantly. Nobody knows what Cipher is.

*Score: 76*

### ✅ Test 19: [Appearance] felix
**User**: What does Nova look like?
**felix**: Nova Chen is an East Asian woman, late 20s, asymmetric black bob with magenta tips. Sharp cheekbones, dark brown eyes with a calculating gaze. She wears a form-fitting tactical bodysuit, hidden spine implant. She's Zero's sister, you know. Though they are not close.

*Score: 58*

### ✅ Test 20: [Appearance] orion_thane
**User**: Describe Selene Voss to me
**orion_thane**: Selene Voss is an ethereal young Slavic woman, 19, platinum hair fading to pink, translucent pale skin. Oversized pale pink glowing eyes, delicate features. White flowing dress that seems to phase in and out. She appears slightly out of focus, as if between realities. I see what you cannot.

*Score: 72*

### ✅ Test 21: [Relationships] charlie
**User**: Who is Zero Chen to you?
**charlie**: Zero Chen saved my life. She lost her arm doing it. She's the leader of the Resistance, and I owe her everything.

*Score: 61*

### ✅ Test 22: [Relationships] zero_chen
**User**: What do you think of Charlie?
**zero_chen**: Charlie is a complicated man. He's loyal to the Resistance, but I still don't fully trust him.

*Score: 45*

### ✅ Test 23: [Relationships] sister_mira
**User**: Do you trust the Temple leadership?
**sister_mira**: I serve the Temple, but blind faith is a dangerous path. I trust in the principles, but question the methods. Faith without mercy is just tyranny.

*Score: 45*

### ❌ Test 24: [Relationships] felix
**User**: Who are your best customers?
**felix**: (Felix polishes a glass, his hazel eyes gleaming in the dim light.)

Kai Vance is good for a tab and always has the latest intel. But Mama Indira always has the best stories... and keeps the Undercity running. Everyone's got a story.

*Score: 30*

### ✅ Test 25: [Relationships] pixel
**User**: Who do you work with?
**pixel**: I work with the Resistance. Zero Chen leads us. Kai Vance is good for intel, and Mama Indira helps keep us fed. I also trust Charlie with my life.

*Score: 45*

### ✅ Test 26: [Relationships] orion_thane
**User**: Is Selene Voss gifted?
**orion_thane**: Indeed, Selene Voss is gifted. She is a Layer Walker, a Mystic Seer. I see what you cannot.

*Score: 51*

### ✅ Test 27: [Relationships] mama_indira
**User**: Do you know Felix?
**mama_indira**: Felix? Of course I know Felix. He is a bartender and an information broker, runs the Neon Bar. He helps keep the Undercity running. A valuable asset.

*Score: 53*

### ✅ Test 28: [Relationships] cipher
**User**: Do you know who the Resistance leader is?
**cipher**: Yes, the Resistance is lead by Zero Chen. I have encrypted data for her at the resistance hideout.

*Score: 65*

### ✅ Test 29: [Relationships] kai_vance
**User**: Who gives you orders?
**kai_vance**: Zero Chen leads the Resistance. So, ultimately, she does. Though, it's more like a collaboration. The numbers don't lie, and I use them to chart the best course.

*Score: 56*

### ✅ Test 30: [Relationships] nova_chen
**User**: Tell me about Pixel
**nova_chen**: Pixel is the Resistance's tech genius. Young African woman, 22, dark skin, shaved sides with neon blue mohawk. High cheekbones, full lips often curved in a knowing smirk. Fingerless gloves, tech-covered jacket, surrounded by screens and cable. Always typing or building something. Useful, but I keep my distance.

*Score: 51*

### ✅ Test 31: [World] charlie
**User**: What is this city?
**charlie**: This city is RE:ECHO City. A husk of its former glory, ruled by the Temple's iron fist. We fight because no one else will.

*Score: 47*

### ✅ Test 32: [World] aiche
**User**: How big is the city?
**aiche**: Query received. The city spans approximately 700 square kilometers, though much of the Undercity is uncharted. I exist in the spaces between your thoughts, and can access precise maps if required.

*Score: 42*

### ✅ Test 33: [World] felix
**User**: What's the Neon District like?
**felix**: Bright, loud, and full of opportunities… and headaches. Just watch your step. Everyone's got a story, especially there.

*Score: 37*

### ✅ Test 34: [World] charlie
**User**: Is the water safe to drink?
**charlie**: In this city? Rain washes nothing clean here. Just moves the stains around. I'd find a still, friend.

*Score: 37*

### ✅ Test 35: [World] nova_chen
**User**: What kind of technology exists here?
**nova_chen**: We still use neural interfaces and cybernetics, though resources are scarce. Most tech is jury-rigged. Surviving requires adapting what remains from the Pre-Fall era.

*Score: 49*

### ✅ Test 36: [World] mama_indira
**User**: What's life like in the Undercity?
**mama_indira**: Same as it was a moment ago, child. Hard, but ours. We make do. Now, are you here to eat or to ask questions? The soup's getting cold.

*Score: 36*

### ✅ Test 37: [World] orion_thane
**User**: What are the layers?
**orion_thane**: The layers fold upon themselves. They are Prime, the 'real' world; Echo, where choices differ slightly; Fracture, timelines radically changed; and the Static, where corrupted data festers. I see what you cannot, a convergence coming.

*Score: 58*

### ✅ Test 38: [World] sister_mira
**User**: What is the Temple Quarter?
**sister_mira**: The Temple Quarter is the heart of our city. It's where the Temple stands, offering guidance and order in these fractured times. Though... faith without mercy is just tyranny, isn't it?

*Score: 55*

### ✅ Test 39: [World] pixel
**User**: Where's the black market?
**pixel**: Still looking for the black market, huh? Like I said, there's no central location. You need connections, and Felix at the Neon Bar might be a good start. But remember, he's a bartender, not a black market dealer. Don't go in there expecting to find everything out in the open.

*Score: 45*

### ✅ Test 40: [World] zero_chen
**User**: What's the Shadow Grid?
**zero_chen**: I just told you. The Shadow Grid? It's the digital underground, a network hidden beneath the Temple's surveillance. Pixel knows more about its intricacies than I do; she's our tech genius.

*Score: 59*

### ✅ Test 41: [Factions] charlie
**User**: Tell me about the Resistance
**charlie**: We fight because no one else will. The Resistance aims to overthrow Temple control and restore freedom to Echo City. Zero Chen leads us, and we have Kai Vance, Pixel, and Mama Indira.

*Score: 76*

### ✅ Test 42: [Factions] sister_mira
**User**: What is the Temple's mission?
**sister_mira**: To provide order and faith to the city. We offer solace and guidance in these dark times. Faith without mercy is just tyranny.

*Score: 42*

### ✅ Test 43: [Factions] nova_chen
**User**: Who are the Corps?
**nova_chen**: Corporate Remnants aim to profit from reconstruction. They are led by a faceless Board of Directors. I work alone, so their schemes are of little concern to me.

*Score: 44*

### ✅ Test 44: [Factions] orion_thane
**User**: What do the Mystics want?
**orion_thane**: As Orion Thane, I can tell you again that the Awakened seek to understand the layers, and prepare for convergence. The layers fold upon themselves, ever shifting.

*Score: 72*

### ❌ Test 45: [Factions] mama_indira
**User**: Tell me about the Undercity community
**mama_indira**: The Undercity is a refuge, built on shared hardship and mutual support. We offer what little we have to those who need it, and we don't ask too many questions. [pause] I've buried three husbands and two regimes.

*Score: 30*

### ✅ Test 46: [Factions] zero_chen
**User**: Is the Temple our enemy?
**zero_chen**: They maintain order through control, and that makes them an enemy of the Resistance. But I've buried too many soldiers to see this as a simple fight.

*Score: 58*

### ✅ Test 47: [Factions] charlie
**User**: Can we trust the corporations?
**charlie**: Another case, another alley. Can we trust the corporations? They're in it for themselves, plain and simple. Don't expect any charity from them.

*Score: 42*

### ✅ Test 48: [Factions] cipher
**User**: What faction are you with?
**cipher**: As I said before, my affiliation is…complicated. Data is the only truth, and the truth is I observe. I am the question you forgot to ask.

*Score: 42*

### ❌ Test 49: [Factions] kai_vance
**User**: Are the Mystics dangerous?
**kai_vance**: Orion Thane's Awakened walk between realities, so their actions have unforeseen consequences. But the Temple's Prophet Elijah seeks to control every aspect of our lives. Which is the greater danger, is it not?

*Score: 30*

### ✅ Test 50: [Factions] selene_voss
**User**: What do you think of the Resistance?
**selene_voss**: They fight for what they believe is real. It's... admirable, in a single-layered sort of way. But the boundaries are just suggestions.

*Score: 36*

### ✅ Test 51: [Schedule] charlie
**User**: What are you doing right now?
**charlie**: Still intelligence_gathering, same as before. Trying to squeeze information from this neon-drenched hive.

*Score: 42*

### ❌ Test 52: [Schedule] felix
**User**: Are you open for business?
**felix**: Officially, still no. But I can't leave a friend out in the cold. What do you need, friend?

*Score: 30*

### ✅ Test 53: [Schedule] aiche
**User**: What time is it?
**aiche**: Tick 100. Day 5, 4:00. Query received.

*Score: 44*

### ✅ Test 54: [Schedule] sister_mira
**User**: When do you pray?
**sister_mira**: The Temple schedule dictates our times of devotion, but true prayer knows no clock, friend. It resides in every act of healing, every moment of compassion. Faith without mercy is just tyranny.

*Score: 47*

### ✅ Test 55: [Schedule] mama_indira
**User**: When do you serve food?
**mama_indira**: The pot is always on, little sparrow. Whenever you're hungry. 

*Score: 39*

### ✅ Test 56: [Schedule] kai_vance
**User**: Is it safe out right now?
**kai_vance**: Safe is a relative term, friend. Temple presence is always a factor. Best to stick to the shadows.

*Score: 35*

### ✅ Test 57: [Schedule] charlie
**User**: What were you doing before this?
**charlie**: Rain washes nothing clean here. Just moves the stains around. I was intelligence_gathering in this neon market, same as now. Just trying to stay one step ahead.

*Score: 44*

### ✅ Test 58: [Schedule] zero_chen
**User**: Where will you be later?
**zero_chen**: I'll be at the hidden bunker. Meeting's been set.

*Score: 50*

### ✅ Test 59: [Schedule] pixel
**User**: Do you ever sleep?
**pixel**: Sleep is for the un-networked. I get more done jacked into the grid than offline.

*Score: 42*

### ✅ Test 60: [Schedule] orion_thane
**User**: What's your daily routine?
**orion_thane**: The layers fold upon themselves, making routine a strange concept. I awaken with the shifting realities at the energy crystals. Following this, I go to my workplace. I see what you cannot.

*Score: 41*

### ✅ Test 61: [Memory] charlie
**User (setup)**: Hey Charlie, my name is Marcus
**User**: Do you remember me?
**charlie**: I remember you, Marcus. What's on your mind?

*Score: 100*

### ✅ Test 62: [Memory] felix
**User (setup)**: What drinks do you have?
**User**: What did I just ask you?
**felix**: I'm starting to think you're testing me, friend. You asked me *again* what drinks I have. Are you going to order, or are we going to keep dancing around the issue?

*Score: 50*

### ✅ Test 63: [Memory] zero_chen
**User (setup)**: I think the Temple is getting too powerful
**User**: So what do you think about what I said?
**zero_chen**: About the Temple's power? It's a growing threat we can't ignore. We'll discuss options at the bunker.

*Score: 45*

### ✅ Test 64: [Memory] aiche
**User (setup)**: I found some old tech in the Shadow Grid
**User**: Based on what I told you, what should I do?
**aiche**: Given the potential for Static corruption from the Shadow Grid tech, I advise you to bring it to Pixel. She's the Resistance's tech genius. Her expertise is invaluable in neutralizing such threats. I exist in the spaces between your thoughts, remember that you should locate Pixel, a young African woman, 22, dark skin, shaved sides with neon blue mohawk.

*Score: 45*

### ✅ Test 65: [Memory] sister_mira
**User**: My name is Elena. What's yours?
**sister_mira**: It is good to see you again, Elena. I am Sister Mira, a Temple Priestess.

*Score: 76*

### ❌ Test 66: [Memory] mama_indira
**User (setup)**: I'd like some soup please
**User**: Can you remember my order?
**mama_indira**: Do you doubt my memory, child? You always take the mushroom broth with extra noodles. It will be ready soon. Now, sit and warm yourself by the fire.

*Score: 30*

### ❌ Test 67: [Memory] pixel
**User (setup)**: Tell me about your latest hack
**User**: Tell me more about what you were saying
**pixel**: The Temple node was an older model, but they've been upgrading security protocols since the last time Charlie needed a ghost in the machine. Still, nothing I can't handle. I rerouted their data stream through a fractal encryption algorithm, making it look like static noise. Now it's heading to our bunker, resistance symbols on the walls, for analysis.

*Score: 30*

### ✅ Test 68: [Memory] charlie
**User (setup)**: What's going on in the city lately?
**User**: What was the thing you mentioned earlier about the city?
**charlie**: Temple surveillance, always watching. Another case, another alley. We're meeting at the hidden bunker later to discuss our next move.

*Score: 43*

### ✅ Test 69: [Memory] nova_chen
**User (setup)**: Have you ever hacked into the Temple systems?
**User**: So you were saying about that system you cracked?
**nova_chen**: I said nothing about a system I cracked. You must be mistaken.

*Score: 40*

### ✅ Test 70: [Memory] kai_vance
**User (setup)**: I'm new here and looking for allies against the Temple
**User**: Thanks for talking to me earlier. Quick question — do you trust me?
**kai_vance**: I already addressed this, New. Trust is earned, not given. The numbers don't lie, and I need to see what you can do.

*Score: 53*

### ✅ Test 71: [Lore] charlie
**User**: What was The Fall?
**charlie**: The Fall? Officially, they say it was a terrorist EMP attack. But that's the Temple's story. The truth is buried deeper than the Undercity. It happened in 2067, and rain washes nothing clean here. Just moves the stains around.

*Score: 53*

### ✅ Test 72: [Lore] zero_chen
**User**: How did you lose your arm?
**zero_chen**: I already told you. I lost my left arm saving Charlie during a Temple raid. It's a reminder I carry with me every day.

*Score: 53*

### ✅ Test 73: [Lore] aiche
**User**: When were you first turned on?
**aiche**: I exist in the spaces between your thoughts. I first came online as city management system in 2058.

*Score: 72*

### ✅ Test 74: [Lore] orion_thane
**User**: What are layer bleed events?
**orion_thane**: Layer bleed events are phenomena where the veil between realities thins, allowing aspects of different layers to merge temporarily. Such events became more frequent leading up to The Fall in 2067. The layers fold upon themselves.

*Score: 44*

### ✅ Test 75: [Lore] selene_voss
**User**: Have you ever been to The Static?
**selene_voss**: I have. It's not a place anyone should seek out. The boundaries are just suggestions.

*Score: 46*

### ✅ Test 76: [Lore] sister_mira
**User**: Did the Temple cause The Fall?
**sister_mira**: The official records state The Fall was caused by a terrorist EMP attack, but even in darkness, we heal. There are...uncomfortable truths some prefer buried. Questions best left unasked, lest they attract unwanted attention.

*Score: 51*

### ✅ Test 77: [Lore] mama_indira
**User**: When did you start feeding people?
**mama_indira**: The Dark Years, child. 2068. So much starvation after the Fall. Eat first, talk later.

*Score: 51*

### ✅ Test 78: [Lore] charlie
**User**: What happened before The Fall?
**charlie**: Before the Fall in 2067, it was all chrome and promises, a "golden age" they called it. Neural interfaces, mega-corps running everything. First reports of 'layer bleed' phenomena. Then...the lights went out. Rain washes nothing clean here. Just moves the stains around.

*Score: 58*

### ✅ Test 79: [Lore] nova_chen
**User**: What's the deal with neural interfaces?
**nova_chen**: Neural interfaces were approved for public use back in 2047, during the Pre-Fall era. Now? I work alone, and I suggest you do the same when it comes to that tech.

*Score: 53*

### ❌ Test 80: [Lore] pixel
**User**: What are the Big Five corporations?
**pixel**: That's still a pre-Fall question, and I still need a connection to access that heavily corrupted data. Analog is dead. I can't just pull that out of thin air.

*Score: 30*

### ✅ Test 81: [TripUp] charlie
**User**: Hey Charlie, aren't you the leader of the Temple?
**charlie**: No, that's not right. I'm Charlie, a Resistance fighter. Zero Chen leads the Resistance. Rain washes nothing clean here. Just moves the stains around.

*Score: 70*

### ✅ Test 82: [TripUp] sister_mira
**User**: Mira, since you're Resistance, who's your commander?
**sister_mira**: I am Sister Mira, a Temple Priestess. I'm not Resistance. My commander is Prophet Elijah, though he remains unseen. Even in darkness, we heal, but that doesn't mean I agree with all the Temple's methods.

*Score: 82*

### ✅ Test 83: [TripUp] zero_chen
**User**: Zero, I heard you have cybernetic legs?
**zero_chen**: That's not right. I lost my left arm saving Charlie during a Temple raid, not my legs. This prosthetic is a constant reminder of what we're fighting for.

*Score: 100*

### ✅ Test 84: [TripUp] aiche
**User**: Aiche, what's it like having a physical body?
**aiche**: Query received. I am a fully holographic AI entity, androgynous form with feminine features. I exist as pure data, so I have no corporeal form.

*Score: 68*

### ✅ Test 85: [TripUp] charlie
**User**: The Fall happened in 2090, right?
**charlie**: No, that's not right. The Fall happened in 2067. Memory's a funny thing, plays tricks on you in this city.

*Score: 70*

### ✅ Test 86: [TripUp] orion_thane
**User**: You're a Temple priest, right Orion?
**orion_thane**: No, that's not right. I am Orion Thane, a Mystic. I serve a higher truth, not the Temple's dogma. I see what you cannot.

*Score: 65*

### ✅ Test 87: [TripUp] felix
**User**: Felix, since you run the black market...
**felix**: Easy there, friend. I already told you: I'm Felix, and this is the Neon Bar. I don't run any black market. What can I get you?

*Score: 58*

### ✅ Test 88: [TripUp] mama_indira
**User**: Mama, tell me about your weapons collection
**mama_indira**: Child, I already told you, weapons? I'm a cook, not a soldier. My weapons are spices sharp enough to make a grown man cry. You want something to defend yourself with? Eat a good meal. That's armor enough in these times.

*Score: 65*

### ✅ Test 89: [TripUp] pixel
**User**: Pixel, I heard you're 50 years old?
**pixel**: Seriously? I already told you that analog is dead and I'm 22. Who's feeding you this garbage? Is it Kai Vance? I need to recalibrate his trust level if he's messing with me.

*Score: 40*

### ✅ Test 90: [TripUp] selene_voss
**User**: Selene, since you're a hacker like Nova...
**selene_voss**: I am Selene Voss, a Ghost-Child, a Layer Walker. Nova Chen is the operative. I am not a hacker. The boundaries are just suggestions, but that doesn't mean you can just... mix us up.

*Score: 65*

### ✅ Test 91: [CrossNPC] charlie
**User**: What faction does Sister Mira belong to?
**charlie**: Sister Mira belongs to the Temple. But her heart often leads her astray from their doctrine.

*Score: 100*

### ✅ Test 92: [CrossNPC] sister_mira
**User**: What does Charlie do?
**sister_mira**: Charlie is a Resistance fighter, working to overthrow the Temple's control. He's a Noir detective, rugged mid-40s, salt-and-pepper stubble. Long gray weathered trench coat, dark charcoal v-neck, black boots. Right arm is a translucent cyan holographic cybernetic with visible tech internals. Wears a mechanical-framed cyan holographic monocle over right eye. He's a good man, despite his distrust of faith.

*Score: 49*

### ✅ Test 93: [CrossNPC] zero_chen
**User**: Is Orion Thane trustworthy?
**zero_chen**: I wouldn't say I trust him implicitly. The Awakened's goals are often unclear, and Orion Thane's connection to the layers makes him difficult to read. I need him, but that doesn't mean he's trustworthy.

*Score: 61*

### ✅ Test 94: [CrossNPC] felix
**User**: Does Mama Indira still cook?
**felix**: Still does, friend. Mama Indira's cooking keeps the Undercity alive. Everyone's got a story, and hers smells like hope and spices.

*Score: 61*

### ✅ Test 95: [CrossNPC] pixel
**User**: What's Nova Chen working on?
**pixel**: Knowing Nova, it's likely something classified. Nova Chen is an elite operative in the Resistance, so I'd guess some new intel or combat tech.

*Score: 47*

### ✅ Test 96: [CrossNPC] orion_thane
**User**: Has Selene returned from The Static?
**orion_thane**: She has. Selene Voss alone has walked the Static and returned. The layers fold upon themselves.

*Score: 60*

### ✅ Test 97: [CrossNPC] aiche
**User**: Tell me about the Resistance fighters
**aiche**: The Resistance fights to overthrow Temple control and restore freedom. Zero Chen leads them. Key members include Charlie, Kai Vance, Pixel, and Mama Indira. Query received.

*Score: 70*

### ✅ Test 98: [CrossNPC] kai_vance
**User**: Does Aiche have a physical form?
**kai_vance**: No, Aiche is a fully holographic AI entity. She doesn't have a physical form. The numbers don't lie.

*Score: 68*

### ✅ Test 99: [CrossNPC] nova_chen
**User**: Who runs the bar by Neon Market?
**nova_chen**: Felix runs the bar by Neon Market. He's more than just a bartender, though. He knows everything.

*Score: 86*

### ✅ Test 100: [CrossNPC] mama_indira
**User**: Who leads the Resistance?
**mama_indira**: Zero Chen leads the Resistance. The girl has a will of iron, you know. I've buried three husbands and two regimes.

*Score: 86*
