-- ============================================================================
-- NEWS GENERATION MODULE
-- Procedural news articles based on world events and NPC actions
-- ============================================================================

local News = {}

local json = json or require("json")

-- ============================================================================
-- STATE
-- ============================================================================

News.Articles = {}           -- Generated articles
News.Headlines = {}          -- Current headlines (last 24 hours)
News.PendingEvents = {}      -- Events waiting to be converted to news

-- News outlet definitions
News.Outlets = {
    temple_herald = {
        id = "NO01",
        name = "Temple Herald",
        bias = "pro_temple",
        censored = true,
        tone = "authoritative"
    },
    chrome_wire = {
        id = "NO02", 
        name = "Chrome Wire",
        bias = "pro_business",
        censored = false,
        tone = "professional"
    },
    neon_underground = {
        id = "NO03",
        name = "Neon Underground",
        bias = "anti_authority",
        censored = false,
        tone = "gritty"
    },
    undercity_voice = {
        id = "NO04",
        name = "The Undercity Voice",
        bias = "pro_cyborg",
        hidden = true,
        tone = "revolutionary"
    }
}

-- ============================================================================
-- HEADLINE TEMPLATES
-- ============================================================================

News.Templates = {
    robbery = {
        "Break-in at %s: %d GEP Stolen",
        "%s Residents Report Theft Wave",
        "Security Breach at %s Leaves Merchants Shaken",
        "Suspect Flees After %s Heist"
    },
    hacking = {
        "Cyberattack Hits %s Systems",
        "Hacker Breaches %s Network",
        "Digital Intrusion at %s: Data Compromised",
        "Unknown Attacker Targets %s Infrastructure"
    },
    police = {
        "Temple Guard Conducts Raid in %s",
        "Inquisitors Apprehend Suspect in %s",
        "Police Chase Through %s Streets",
        "Security Crackdown in %s District"
    },
    cyborg_attack = {
        "Cyborg Resident Attacked in %s",
        "Tensions Rise as Synthetic Citizen Assaulted",
        "Cyborg Justice Society Condemns %s Incident",
        "Human-Cyborg Violence Erupts in %s"
    },
    fire = {
        "Blaze Engulfs %s Building",
        "Fire Crews Battle %s Inferno",
        "Emergency Response to %s Fire",
        "Arson Investigation Launched at %s"
    },
    trade = {
        "%s Market Sees Price Surge",
        "Trade Disruption Affects %s Vendors",
        "Black Market Activity Up in %s",
        "Economic Tensions in %s District"
    }
}

-- ============================================================================
-- ARTICLE BODY TEMPLATES
-- ============================================================================

News.Bodies = {
    robbery = {
        neutral = "Authorities report a break-in at %s in the %s district. Approximately %d GEP worth of goods were stolen. Temple Guard forces are investigating, though no arrests have been made.",
        pro_temple = "Swift action by Temple security forces thwarted what could have been a major theft at %s. The perpetrator, described as a %s, fled before apprehension. Citizens are reminded that the Temple protects all.",
        anti_authority = "Another robbery rocks %s, and once again the Temple's vaunted security forces arrive too late. Locals report the theft lasted %d minutes before any response. 'They only protect the Spire,' said one witness."
    },
    hacking = {
        neutral = "A cyberattack targeting %s systems was detected at approximately %s. Technical teams are assessing the damage. Officials urge residents to change their credentials.",
        pro_temple = "An attempted cyber-intrusion against %s was quickly neutralized by Temple cybersecurity protocols. The attack, likely originating from underground networks, serves as a reminder of the threats we face.",
        anti_authority = "Sources confirm that %s was breached for over %d minutes before their 'advanced' security noticed. Data exposure is likely significant. As usual, official statements downplay the severity."
    },
    police = {
        neutral = "Temple Guard units conducted an operation in %s today. Officials cite ongoing investigations. Several individuals were detained for questioning.",
        pro_temple = "In a decisive action against criminal elements, Temple Inquisitors swept through %s, apprehending %d suspects linked to illegal activities. The operation showcases our commitment to public safety.",
        anti_authority = "Witnesses describe a violent crackdown in %s as Temple forces stormed buildings without warning. At least %d injuries reported. 'They don't care who gets hurt,' said a local. The Cyborg Justice Society is demanding an investigation."
    },
    cyborg_attack = {
        neutral = "An incident involving a synthetic citizen occurred in %s. Details remain unclear, and both human and cyborg community leaders have called for calm.",
        pro_temple = "An altercation in %s involving a synthetic individual has been resolved. Authorities remind all residents that proper identification protocols apply equally to organic and synthetic citizens.",
        anti_authority = "BREAKING: Another brutal attack on a cyborg citizen in %s. The victim, %s, was set upon by a group of %d humans. Temple Guards arrived but made NO ARRESTS. These attacks are epidemic and the Temple does NOTHING. The Cyborg Justice Society stated: 'The Temple claims neutrality while our people are beaten in the streets.'"
    },
    fire = {
        neutral = "Fire crews responded to a blaze at %s in %s district. The fire has been contained. Investigators are determining the cause.",
        pro_temple = "Thanks to rapid response by Temple emergency services, a fire at %s was quickly contained. No casualties reported. Citizens are reminded to report fire hazards.",
        anti_authority = "Fire ravaged %s overnight. Residents report waiting %d minutes for emergency response. 'If this was the Spire, they'd have been here in seconds,' said one displaced family. Infrastructure in %s continues to deteriorate while Temple resources flow upward."
    }
}

-- ============================================================================
-- CORE FUNCTIONS
-- ============================================================================

-- Initialize news system
function News.init()
    News.Articles = {}
    News.Headlines = {}
    News.PendingEvents = {}
end

-- Queue an event for news generation
function News.queue_event(event)
    table.insert(News.PendingEvents, event)
end

-- Generate article from event
function News.generate_article(event, tick, outlet_id)
    local outlet = News.Outlets[outlet_id] or News.Outlets.neon_underground
    local article_type = News.get_article_type(event)
    
    if not article_type then return nil end
    
    -- Select headline template
    local headlines = News.Templates[article_type]
    if not headlines then return nil end
    
    local headline_template = headlines[(tick % #headlines) + 1]
    local location = event.location or event.district or "Unknown Location"
    local headline = string.format(headline_template, location)
    
    -- Select body template based on outlet bias
    local bodies = News.Bodies[article_type]
    local body_key = "neutral"
    if outlet.bias == "pro_temple" then
        body_key = "pro_temple"
    elseif outlet.bias == "anti_authority" or outlet.bias == "pro_cyborg" then
        body_key = "anti_authority"
    end
    
    local body_template = bodies[body_key] or bodies.neutral
    local district = event.district or "the district"
    local amount = event.amount or event.value or math.random(100, 5000)
    local count = event.count or math.random(1, 5)
    local time = string.format("%02d:%02d", math.floor((tick % 240) / 10), ((tick % 240) % 10) * 6)
    
    -- Format body with available data
    local body = body_template
    body = body:gsub("%%s", location, 1)
    body = body:gsub("%%s", district, 1)
    body = body:gsub("%%d", tostring(amount), 1)
    body = body:gsub("%%d", tostring(count), 1)
    body = body:gsub("%%s", time, 1)
    
    -- Apply censorship for Temple Herald
    if outlet.censored then
        body = News.apply_censorship(body)
        headline = News.apply_censorship(headline)
    end
    
    local article = {
        id = "NEWS_" .. tick .. "_" .. #News.Articles,
        tick = tick,
        day = math.floor(tick / 240) + 1,
        outlet = outlet.name,
        outlet_id = outlet_id,
        headline = headline,
        body = body,
        event_type = event.type or article_type,
        district = district,
        npcs_mentioned = event.participants or {}
    }
    
    table.insert(News.Articles, article)
    table.insert(News.Headlines, { headline = headline, tick = tick, outlet = outlet.name })
    
    -- Trim old headlines (keep last 50)
    while #News.Headlines > 50 do
        table.remove(News.Headlines, 1)
    end
    
    return article
end

-- Determine article type from event
function News.get_article_type(event)
    local type = event.type or event.action
    
    if type == "theft" or type == "robbery" or type == "A05" then
        return "robbery"
    elseif type == "hack" or type == "hacking" or type == "A04" then
        return "hacking"
    elseif type == "police" or type == "raid" or type == "arrest" or type == "A53" then
        return "police"
    elseif type == "cyborg_attack" or type == "discrimination" then
        return "cyborg_attack"
    elseif type == "fire" or type == "explosion" then
        return "fire"
    elseif type == "trade" or type == "market" or type == "A02" then
        return "trade"
    end
    
    return nil
end

-- Apply Temple censorship
function News.apply_censorship(text)
    local replacements = {
        ["police brutality"] = "enforcement action",
        ["attack"] = "incident",
        ["victim"] = "individual",
        ["brutal"] = "",
        ["violence"] = "disturbance",
        ["Temple does nothing"] = "Temple is investigating",
        ["no arrests"] = "investigation ongoing",
        ["crackdown"] = "security operation"
    }
    
    for original, replacement in pairs(replacements) do
        text = text:gsub(original, replacement)
        text = text:gsub(original:gsub("^%l", string.upper), replacement:gsub("^%l", string.upper))
    end
    
    return text
end

-- Process pending events into news
function News.process_tick(tick)
    local generated = {}
    
    for i, event in ipairs(News.PendingEvents) do
        -- Generate for multiple outlets with different perspectives
        local outlets_to_use = {"neon_underground"}
        
        -- Major events go to all outlets
        if event.severity == "major" then
            outlets_to_use = {"temple_herald", "chrome_wire", "neon_underground"}
        end
        
        -- Cyborg-related goes to Undercity Voice
        if event.type == "cyborg_attack" or event.involves_cyborg then
            table.insert(outlets_to_use, "undercity_voice")
        end
        
        for _, outlet_id in ipairs(outlets_to_use) do
            local article = News.generate_article(event, tick, outlet_id)
            if article then
                table.insert(generated, article)
            end
        end
    end
    
    -- Clear pending
    News.PendingEvents = {}
    
    return generated
end

-- Get latest headlines
function News.get_headlines(count, outlet_filter)
    local result = {}
    local max = math.min(count or 10, #News.Headlines)
    
    for i = #News.Headlines, #News.Headlines - max + 1, -1 do
        if i > 0 then
            local h = News.Headlines[i]
            if not outlet_filter or h.outlet == outlet_filter then
                table.insert(result, h)
            end
        end
    end
    
    return result
end

-- Get full article by ID
function News.get_article(article_id)
    for _, article in ipairs(News.Articles) do
        if article.id == article_id then
            return article
        end
    end
    return nil
end

-- Generate sample news for testing
function News.generate_sample(tick)
    local sample_events = {
        { type = "robbery", location = "Neon Motel", district = "neon_district", value = 2500, severity = "minor" },
        { type = "cyborg_attack", location = "Market Square", district = "market", involves_cyborg = true, count = 1, severity = "major" },
        { type = "police", location = "Undercity Alley", district = "undercity", count = 3, severity = "major" },
        { type = "hacking", location = "OmniConnect Hub", district = "chrome_district", duration = 45, severity = "minor" },
        { type = "fire", location = "Warehouse 7", district = "industrial_ring", severity = "major" }
    }
    
    local event = sample_events[(tick % #sample_events) + 1]
    News.queue_event(event)
    return News.process_tick(tick)
end

-- Export module
return News
