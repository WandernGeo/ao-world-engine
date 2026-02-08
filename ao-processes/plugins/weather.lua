-- ============================================================================
-- WEATHER PLUGIN
-- Dynamic weather system with NPC behavior impact
-- Plugin 1 of 3 for AO World Engine audit
-- ============================================================================

local Weather = {}

-- Weather types with effects
Weather.TYPES = {
    clear     = { id = "W01", temp_modifier = 0,   mood_modifier = 0.05,  movement_speed = 1.0, outdoor_activity = 1.0 },
    cloudy    = { id = "W02", temp_modifier = -2,  mood_modifier = 0.0,   movement_speed = 1.0, outdoor_activity = 0.8 },
    rain      = { id = "W03", temp_modifier = -5,  mood_modifier = -0.05, movement_speed = 0.7, outdoor_activity = 0.3 },
    storm     = { id = "W04", temp_modifier = -8,  mood_modifier = -0.10, movement_speed = 0.4, outdoor_activity = 0.1 },
    fog       = { id = "W05", temp_modifier = -3,  mood_modifier = -0.02, movement_speed = 0.6, outdoor_activity = 0.5 },
    heatwave  = { id = "W06", temp_modifier = 12,  mood_modifier = -0.08, movement_speed = 0.8, outdoor_activity = 0.4 },
    smog      = { id = "W07", temp_modifier = 2,   mood_modifier = -0.12, movement_speed = 0.9, outdoor_activity = 0.2 },
    acid_rain = { id = "W08", temp_modifier = -4,  mood_modifier = -0.15, movement_speed = 0.3, outdoor_activity = 0.0 },
}

-- Seasonal temperature baselines (Celsius, cyberpunk city ~2087)
Weather.SEASON_TEMPS = {
    spring = 14,
    summer = 28,
    autumn = 12,
    winter = 2
}

-- State
Weather.State = {
    current = "clear",
    temperature = 18,
    humidity = 0.5,
    wind_speed = 10,      -- km/h
    air_quality = 0.7,    -- 0=toxic, 1=clean
    forecast = {},        -- next 3 periods
    streak = 0,           -- consecutive ticks of same weather
    last_change_tick = 0
}

-- Initialize weather
function Weather.init(tick)
    Weather.State.current = "clear"
    Weather.State.temperature = 18
    Weather.State.last_change_tick = tick or 0
    Weather.generate_forecast(tick or 0)
end

-- Deterministic weather selection based on tick
function Weather.select_weather(tick, season)
    -- Use tick as seed for deterministic selection
    local seed = tick * 7 + 13
    local roll = seed % 100

    -- Probability table varies by season
    local probabilities = {
        spring = { clear = 35, cloudy = 25, rain = 20, fog = 10, storm = 5, smog = 3, heatwave = 2, acid_rain = 0 },
        summer = { clear = 40, cloudy = 15, heatwave = 20, storm = 10, smog = 10, rain = 5, fog = 0, acid_rain = 0 },
        autumn = { cloudy = 30, rain = 25, fog = 20, clear = 15, storm = 5, smog = 3, acid_rain = 2, heatwave = 0 },
        winter = { cloudy = 30, clear = 20, fog = 20, rain = 15, storm = 10, smog = 3, acid_rain = 2, heatwave = 0 }
    }

    local probs = probabilities[season] or probabilities.spring
    local cumulative = 0

    for weather_type, prob in pairs(probs) do
        cumulative = cumulative + prob
        if roll < cumulative then
            return weather_type
        end
    end

    return "clear"  -- fallback
end

-- Get current season from tick
function Weather.get_season(tick)
    local ticks_per_day = 240
    local days_per_season = 90
    local ticks_per_season = ticks_per_day * days_per_season
    local season_idx = math.floor(tick / ticks_per_season) % 4

    local seasons = { "spring", "summer", "autumn", "winter" }
    return seasons[season_idx + 1]
end

-- Generate 3-period forecast
function Weather.generate_forecast(tick)
    local season = Weather.get_season(tick)
    Weather.State.forecast = {}

    for i = 1, 3 do
        local future_tick = tick + (i * 80)  -- ~8 hours per period
        local weather = Weather.select_weather(future_tick, season)
        table.insert(Weather.State.forecast, {
            period = i,
            weather = weather,
            eta_ticks = i * 80
        })
    end
end

-- Process weather tick - called from world.lua CRON
function Weather.on_tick(tick)
    local season = Weather.get_season(tick)
    local base_temp = Weather.SEASON_TEMPS[season] or 18

    -- Weather changes every 40-80 ticks (4-8 hours in-game)
    local change_interval = 40 + (tick % 40)
    if tick - Weather.State.last_change_tick >= change_interval then
        local new_weather = Weather.select_weather(tick, season)

        if new_weather ~= Weather.State.current then
            Weather.State.current = new_weather
            Weather.State.streak = 0
            Weather.State.last_change_tick = tick
            Weather.generate_forecast(tick)
        else
            Weather.State.streak = Weather.State.streak + 1
        end
    end

    -- Update temperature based on weather type and time of day
    local weather_data = Weather.TYPES[Weather.State.current]
    local hour = math.floor((tick % 240) / 10)
    local time_of_day_mod = -3 + (6 * math.sin((hour - 6) * math.pi / 12))  -- peak at noon

    Weather.State.temperature = math.floor(base_temp + (weather_data.temp_modifier or 0) + time_of_day_mod)

    -- Update humidity
    if Weather.State.current == "rain" or Weather.State.current == "storm" then
        Weather.State.humidity = math.min(1.0, Weather.State.humidity + 0.05)
    else
        Weather.State.humidity = math.max(0.2, Weather.State.humidity - 0.02)
    end

    -- Update air quality (smog, acid_rain degrade it)
    if Weather.State.current == "smog" then
        Weather.State.air_quality = math.max(0.1, Weather.State.air_quality - 0.05)
    elseif Weather.State.current == "acid_rain" then
        Weather.State.air_quality = math.max(0.0, Weather.State.air_quality - 0.10)
    elseif Weather.State.current == "rain" then
        Weather.State.air_quality = math.min(1.0, Weather.State.air_quality + 0.03)  -- rain cleans air
    end

    -- Generate events for extreme weather
    local events = {}
    if Weather.State.current == "acid_rain" and Weather.State.streak > 5 then
        table.insert(events, {
            type = "weather_hazard",
            subtype = "acid_rain_damage",
            tick = tick,
            severity = 0.3 + (Weather.State.streak * 0.05),
            effects = { building_damage = 0.02, health_risk = 0.10 }
        })
    end

    if Weather.State.temperature > 38 then
        table.insert(events, {
            type = "weather_hazard",
            subtype = "extreme_heat",
            tick = tick,
            effects = { water_demand = 1.5, power_demand = 1.3, health_risk = 0.05 }
        })
    end

    return {
        state = Weather.State,
        effects = weather_data,
        season = season,
        events = events
    }
end

-- Get NPC behavior modifiers based on current weather
function Weather.get_npc_modifiers()
    local weather_data = Weather.TYPES[Weather.State.current]
    return {
        mood_delta = weather_data.mood_modifier,
        movement_speed = weather_data.movement_speed,
        outdoor_probability = weather_data.outdoor_activity,
        should_seek_shelter = Weather.State.current == "storm" or Weather.State.current == "acid_rain",
        clothing_needed = Weather.State.temperature < 10
    }
end

-- Get weather state for API responses
function Weather.get_state()
    return {
        current = Weather.State.current,
        temperature = Weather.State.temperature,
        humidity = Weather.State.humidity,
        wind_speed = Weather.State.wind_speed,
        air_quality = Weather.State.air_quality,
        forecast = Weather.State.forecast,
        season = Weather.get_season(Weather.State.last_change_tick),
        effects = Weather.TYPES[Weather.State.current]
    }
end

-- Export module
return Weather
