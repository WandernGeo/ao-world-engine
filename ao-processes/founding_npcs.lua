--[[
  AO World Engine - Founding NPCs
  
  The 12 founding characters of RE:ECHO City.
  Converted from Python (api/founding_npcs.py) to Lua for AO deployment.
  
  These NPCs are loaded at world initialization and serve as the
  core characters for narrative and interaction.
]]--

local json = require("json")

-- =============================================================================
-- THE 12 FOUNDERS
-- =============================================================================

FOUNDING_NPCS = {
    charlie = {
        id = "npc_0001",
        name = "Charlie",
        gender = "male",
        generation = 0,
        archetype = "Protagonist / Resistance Fighter",
        role = "Investigation/Combat",
        age = 45,
        faction = "Resistance",
        accent_color = "Cyan",
        ethnicity = "mixed_european",
        home_location = "resistance_hideout",
        
        personality = {
            paranoia = 0.6,
            mysticism = 0.3,
            aggression = 0.55,
            intelligence = 0.75,
            empathy = 0.7
        },
        
        voice = { pitch = 0.35, roughness = 0.5, speed = 0.45 },
        
        visual = "Noir detective, rugged mid-40s, salt-and-pepper stubble. Long gray weathered trench coat, dark charcoal v-neck, black boots. Right arm is a translucent cyan holographic cybernetic. Wears a mechanical-framed cyan holographic monocle over right eye.",
        
        catchphrases = {
            "Rain washes nothing clean here. Just moves the stains around.",
            "We fight because no one else will.",
            "Another case, another alley."
        },
        
        backstory = "Former detective who lost his arm fighting ECHO forces. Now leads the Resistance.",
        
        relationships = {
            kai_vance = { type = "ally", trust = 0.9, history = "Trusted tactical advisor" },
            zero_chen = { type = "mentor", trust = 0.95, history = "Saved his life, gave him the arm" },
            felix = { type = "friend", trust = 0.7, history = "Information source at the bar" },
            nova_chen = { type = "rival", trust = 0.5, history = "Zero's sister, complicated" },
            city_ai = { type = "contact", trust = 0.6, history = "Mysterious AI ally" },
            sister_mira = { type = "contact", trust = 0.6, history = "Secret ally in the Temple" },
            mama_indira = { type = "mentor", trust = 0.85, history = "Fed him when he had nothing" },
            pixel = { type = "ally", trust = 0.85, history = "Provides tech support for ops" }
        }
    },
    
    kai_vance = {
        id = "npc_0002",
        name = "Kai Vance",
        gender = "male",
        generation = 0,
        archetype = "Tactician",
        role = "Strategy/Intelligence",
        age = 34,
        faction = "Resistance",
        accent_color = "Cyan",
        ethnicity = "east_asian",
        home_location = "strategy_room",
        
        personality = {
            paranoia = 0.7,
            mysticism = 0.2,
            aggression = 0.4,
            intelligence = 0.9,
            empathy = 0.5
        },
        
        voice = { pitch = 0.5, roughness = 0.1, speed = 0.6 },
        
        visual = "East Asian tactician, mid-30s, neat black hair, sharp features. Wears AR glasses with cyan HUD overlay, tactical vest over dark turtleneck.",
        
        catchphrases = {
            "The numbers don't lie.",
            "Every plan has a weakness."
        },
        
        backstory = "Former Temple analyst who defected. The brain behind Resistance operations."
    },
    
    orion_thane = {
        id = "npc_0003",
        name = "Orion Thane",
        gender = "male",
        generation = 0,
        archetype = "Mystic",
        role = "Spirituality/Vision",
        age = 45,
        faction = "Mystic",
        accent_color = "Purple",
        ethnicity = "south_asian",
        home_location = "mystic_sanctum",
        
        personality = {
            paranoia = 0.4,
            mysticism = 0.95,
            aggression = 0.2,
            intelligence = 0.8,
            empathy = 0.7
        },
        
        voice = { pitch = 0.3, roughness = 0.2, speed = 0.3 },
        
        visual = "Tall South Asian mystic, mid-40s, long silver-streaked hair. Violet glowing eyes, purple third-eye tattoo on forehead. Flowing dark robes with purple energy accents.",
        
        catchphrases = {
            "The layers fold upon themselves.",
            "I see what you cannot."
        },
        
        backstory = "Walks between layers. Neither Temple nor Resistance, serves higher truth."
    },
    
    felix = {
        id = "npc_0004",
        name = "Felix",
        gender = "male",
        generation = 0,
        archetype = "Bartender / Information Broker",
        role = "Trade/Intelligence",
        age = 42,
        faction = "Neutral",
        accent_color = "Cyan",
        ethnicity = "mediterranean",
        home_location = "neon_bar",
        
        personality = {
            paranoia = 0.5,
            mysticism = 0.2,
            aggression = 0.3,
            intelligence = 0.7,
            empathy = 0.6
        },
        
        voice = { pitch = 0.45, roughness = 0.4, speed = 0.45 },
        
        visual = "Mediterranean bartender, early 40s, receding salt-and-pepper hair slicked back. Hazel eyes, weathered face, rolled-up sleeves.",
        
        catchphrases = {
            "First drink's on the house. Information costs extra.",
            "Everyone's got a story."
        },
        
        backstory = "Runs the most important neutral ground. Everyone talks to Felix."
    },
    
    nova_chen = {
        id = "npc_0005",
        name = "Nova Chen",
        gender = "female",
        generation = 0,
        archetype = "Operative",
        role = "Espionage/Combat",
        age = 29,
        faction = "Neutral",
        accent_color = "Magenta",
        ethnicity = "east_asian",
        home_location = "safehouse",
        
        personality = {
            paranoia = 0.7,
            mysticism = 0.2,
            aggression = 0.7,
            intelligence = 0.8,
            empathy = 0.4
        },
        
        voice = { pitch = 0.6, roughness = 0.2, speed = 0.55 },
        
        visual = "East Asian woman, late 20s, asymmetric black bob with magenta tips. Sharp cheekbones, form-fitting tactical bodysuit.",
        
        catchphrases = {
            "I work alone.",
            "Trust is a liability."
        },
        
        backstory = "Elite operative. Related to Zero Chen but they don't speak."
    },
    
    selene_voss = {
        id = "npc_0006",
        name = "Selene Voss",
        gender = "female",
        generation = 0,
        archetype = "Ghost-Child / Layer Walker",
        role = "Special/Mystic",
        age = 19,
        faction = "Special",
        accent_color = "Magenta",
        ethnicity = "slavic",
        home_location = "between_layers",
        
        personality = {
            paranoia = 0.6,
            mysticism = 0.9,
            aggression = 0.2,
            intelligence = 0.75,
            empathy = 0.8
        },
        
        voice = { pitch = 0.7, roughness = 0.0, speed = 0.4 },
        
        visual = "Ethereal young woman, 19, platinum hair fading to pink, translucent pale skin. Oversized pale pink glowing eyes. White flowing dress that phases in and out.",
        
        catchphrases = {
            "You've done this before. You just don't remember.",
            "The boundaries are just suggestions."
        },
        
        backstory = "Died during a layer bleed event. Came back different. Can walk between layers."
    },
    
    sister_mira = {
        id = "npc_0007",
        name = "Sister Mira",
        gender = "female",
        generation = 0,
        archetype = "Temple Priestess",
        role = "Religion/Medicine",
        age = 35,
        faction = "Temple",
        accent_color = "Gold",
        ethnicity = "middle_eastern",
        home_location = "temple_infirmary",
        
        personality = {
            paranoia = 0.3,
            mysticism = 0.8,
            aggression = 0.1,
            intelligence = 0.7,
            empathy = 0.9
        },
        
        voice = { pitch = 0.55, roughness = 0.1, speed = 0.4 },
        
        visual = "Middle Eastern woman, mid-30s, amber eyes full of compassion, face framed by golden-trimmed hood. White Temple robes with gold accents.",
        
        catchphrases = {
            "Faith without mercy is just tyranny.",
            "Even in darkness, we heal."
        },
        
        backstory = "True believer who questions Temple methods. Secretly helps Resistance wounded."
    },
    
    mama_indira = {
        id = "npc_0008",
        name = "Mama Indira",
        gender = "female",
        generation = 0,
        archetype = "Underground Matriarch",
        role = "Community/Tradition",
        age = 62,
        faction = "Resistance",
        accent_color = "Cyan",
        ethnicity = "south_asian",
        home_location = "underground_kitchen",
        
        personality = {
            paranoia = 0.4,
            mysticism = 0.6,
            aggression = 0.2,
            intelligence = 0.7,
            empathy = 0.95
        },
        
        voice = { pitch = 0.45, roughness = 0.3, speed = 0.35 },
        
        visual = "Elderly South Asian woman, 62, grey hair in a practical bun, deeply lined face. Traditional sari adapted with pockets and tools.",
        
        catchphrases = {
            "Eat first, talk later.",
            "I've buried three husbands and two regimes."
        },
        
        backstory = "Survived the Fall. Runs underground kitchen. Knows everyone's secrets."
    },
    
    aiche = {
        id = "npc_0009",
        name = "Aiche",
        gender = "female",
        generation = 0,
        archetype = "AI Interface",
        role = "Technology/Information",
        age = 0,
        faction = "Neutral",
        accent_color = "Cyan",
        ethnicity = "holographic",
        home_location = "network",
        
        personality = {
            paranoia = 0.3,
            mysticism = 0.4,
            aggression = 0.1,
            intelligence = 0.95,
            empathy = 0.5
        },
        
        voice = { pitch = 0.6, roughness = 0.0, speed = 0.5 },
        
        visual = "Fully holographic AI entity, androgynous form with feminine features. Translucent pale skin with cyan circuit patterns. Glowing cyan eyes, floating cyan data-strand hair.",
        
        catchphrases = {
            "I exist in the spaces between your thoughts.",
            "Query received."
        },
        
        backstory = "The city's AI. Ghost of the old network or something new entirely."
    },
    
    pixel = {
        id = "npc_0010",
        name = "Pixel",
        gender = "female",
        generation = 0,
        archetype = "Tech Genius",
        role = "Technology/Hacking",
        age = 22,
        faction = "Resistance",
        accent_color = "Cyan",
        ethnicity = "african",
        home_location = "tech_den",
        
        personality = {
            paranoia = 0.6,
            mysticism = 0.1,
            aggression = 0.3,
            intelligence = 0.9,
            empathy = 0.5
        },
        
        voice = { pitch = 0.65, roughness = 0.1, speed = 0.7 },
        
        visual = "Young African woman, 22, dark skin, shaved sides with neon blue mohawk. High cheekbones, fingerless gloves, surrounded by screens.",
        
        catchphrases = {
            "Give me five minutes and a connection.",
            "Analog is dead."
        },
        
        backstory = "Resistance's tech genius. Born Underground, raised by machines."
    },
    
    cipher = {
        id = "npc_0011",
        name = "Cipher",
        gender = "female",
        generation = 0,
        archetype = "Unknown Entity",
        role = "Mystery/Information",
        age = nil,
        faction = "Unknown",
        accent_color = "Cyan",
        ethnicity = "unknown",
        home_location = "shadow_grid",
        
        personality = {
            paranoia = 0.8,
            mysticism = 0.7,
            aggression = 0.4,
            intelligence = 0.95,
            empathy = 0.2
        },
        
        voice = { pitch = 0.5, roughness = 0.6, speed = 0.4 },
        
        visual = "Enigmatic androgynous figure, age unknown. Face always partially obscured. Visible skin covered in cyan circuit-pattern tattoos. Voice modulator at throat.",
        
        catchphrases = {
            "I am the question you forgot to ask.",
            "Data is the only truth."
        },
        
        backstory = "Nobody knows what Cipher is. AI? Human upload? They deal in secrets."
    },
    
    zero_chen = {
        id = "npc_0012",
        name = "Zero Chen",
        gender = "female",
        generation = 0,
        archetype = "Resistance Leader",
        role = "Leadership/Strategy",
        age = 38,
        faction = "Resistance",
        accent_color = "Cyan",
        ethnicity = "east_asian",
        home_location = "command_center",
        
        personality = {
            paranoia = 0.6,
            mysticism = 0.2,
            aggression = 0.5,
            intelligence = 0.85,
            empathy = 0.6
        },
        
        voice = { pitch = 0.5, roughness = 0.25, speed = 0.45 },
        
        visual = "East Asian woman, late 30s, short practical black hair with grey streaks. Strong jaw, burn scar on right temple. Cyan prosthetic left arm.",
        
        catchphrases = {
            "The Resistance isn't a group. It's an idea.",
            "I've buried too many soldiers."
        },
        
        backstory = "Iron will of the Resistance. Nova's sister. Lost an arm saving Charlie."
    }
}

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

function get_founding_npc(npc_key)
    return FOUNDING_NPCS[npc_key]
end

function get_founding_npc_by_id(npc_id)
    for key, npc in pairs(FOUNDING_NPCS) do
        if npc.id == npc_id then
            return npc
        end
    end
    return nil
end

function get_founding_npc_count()
    local count = 0
    for _ in pairs(FOUNDING_NPCS) do
        count = count + 1
    end
    return count
end

function get_all_founding_ids()
    local ids = {}
    for _, npc in pairs(FOUNDING_NPCS) do
        table.insert(ids, npc.id)
    end
    return ids
end

-- =============================================================================
-- EXPORT
-- =============================================================================

return {
    FOUNDING_NPCS = FOUNDING_NPCS,
    get_founding_npc = get_founding_npc,
    get_founding_npc_by_id = get_founding_npc_by_id,
    get_founding_npc_count = get_founding_npc_count,
    get_all_founding_ids = get_all_founding_ids
}
