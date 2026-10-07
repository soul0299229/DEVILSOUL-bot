# bot.py — Devil Menu bot (single-file, no local imports)
# Python 3.10+ | python-telegram-bot v20+
import os, io, time, random
from string import Template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_NAME  = os.environ.get("BOT_NAME", "devil_menu")

# ============================================================
# PRESETS
# ============================================================
PROFILES = {
    "full":   {"aimbot": 85, "mb_on": True,  "mb_range": 20, "mb_chance": 100,
               "esp_style": "auto", "esp_rotate": 30, "esp_name": True,
               "loot_esp": True,  "crosshair": "cross"},
    "safe":   {"aimbot": 35, "mb_on": True,  "mb_range": 15, "mb_chance": 15,
               "esp_style": "auto", "esp_rotate": 60, "esp_name": True,
               "loot_esp": False, "crosshair": "dot"},
    "random": {"aimbot": 30, "mb_on": True,  "mb_range": 18, "mb_chance": 25,
               "esp_style": "auto", "esp_rotate": 30, "esp_name": True,
               "loot_esp": True,  "crosshair": "circle_cross"},
}

ESP_STYLES = ["box", "line", "circle", "skeleton", "head", "distance", "name", "health"]
CROSSHAIRS = ["cross", "dot", "circle_cross", "chevron", "cross_gap", "dot_circle", "t_shape"]

# ============================================================
# SECURITY LAYERS
# ============================================================
L_SYSCALL_MASK = r"""
-- [S1] SYSCALL INDIRECTION
local _s1_cache = {}
_G._S1_IMPORT = function(name)
    local hit = _s1_cache[name]
    if hit ~= nil then return hit end
    local ok, cls = pcall(import, name)
    _s1_cache[name] = ok and cls or nil
    return _s1_cache[name]
end
"""

L_STRING_CRYPT = r"""
-- [S2] STRING CRYPT
local _s2_k = {0x4D, 0x21, 0x7A, 0x03, 0x1E}
local function _s2_dec(bytes)
    local out = {}
    for i = 1, #bytes do out[i] = string.char(bit32.bxor(bytes[i], _s2_k[(i - 1) % #_s2_k + 1])) end
    return table.concat(out)
end
_G._S2 = {
    rwh = _s2_dec({0x0E,0x05,0x0B,0x3F,0x77,0x4D,0x1F,0x3E,0x2A,0x32,0x6F,0x22,0x5B,0x12}),
    rab = _s2_dec({0x0E,0x05,0x0B,0x3F,0x77,0x40,0x10,0x22,0x30,0x22,0x6F}),
    ikc = _s2_dec({0x05,0x0F,0x77,0x0A,0x0E,0x1F,0x0E,0x02,0x0A,0x77,0x22,0x31,0x2B,0x7A}),
    imc = _s2_dec({0x05,0x0F,0x77,0x18,0x1E,0x18,0x7C,0x1A,0x2A,0x77,0x22,0x31,0x2B,0x7A}),
}
"""

L_RPC_NORMALIZE = r"""
-- [S3] RPC NORMALIZE
do
    local _orig = _G.SendRPC
    if _orig then
        _G.SendRPC = function(name, ...)
            local jitter = 0.020 + math.random() * 0.180
            local args = {...}
            args[#args + 1] = string.rep("\0", math.random(4, 32))
            local t = 0
            local function fire()
                t = t + 0.016
                if t >= jitter then return _orig(name, table.unpack(args)) end
                local tk = package.loaded["common.time_ticker"]
                if tk then tk.AddTimerOnce(0.016, fire) end
            end
            fire()
        end
    end
end
"""

L_BEHAVIOR_DRIFT = r"""
-- [S4] BEHAVIOR DRIFT
local _s4 = {
    accuracy = 0.55 + math.random() * 0.10,
    headshot = 0.22 + math.random() * 0.08,
    reaction = 0.28 + math.random() * 0.10,
    seen     = 0.72 + math.random() * 0.10,
}
local function _s4_step(v, lo, hi, step)
    v = v + (math.random() - 0.5) * step
    if v < lo then v = lo + math.random() * step end
    if v > hi then v = hi - math.random() * step end
    return v
end
_G._S4_TICK = function()
    _s4.accuracy = _s4_step(_s4.accuracy, 0.42, 0.72, 0.010)
    _s4.headshot = _s4_step(_s4.headshot, 0.14, 0.34, 0.005)
    _s4.reaction = _s4_step(_s4.reaction, 0.20, 0.42, 0.008)
    _s4.seen     = _s4_step(_s4.seen,     0.60, 0.88, 0.010)
end
_G._S4_GET = function()
    return { accuracy = _s4.accuracy, headshotRate = _s4.headshot,
             reactionTime = _s4.reaction, visibilityRate = _s4.seen }
end
"""

L_STAT_THROTTLE = r"""
-- [S5] STAT THROTTLE
local _s5 = { window = 60, kills = {}, hs = 0, hits = 0, last = os.time() }
local _caps = { hs = 0.45, kpm = 3.5 }
function _G._S5_ON_SHOT(is_head, is_kill)
    local now = os.time()
    if now - _s5.last >= _s5.window then
        _s5.kills = {}; _s5.hs = 0; _s5.hits = 0; _s5.last = now
    end
    _s5.hits = _s5.hits + 1
    if is_head then _s5.hs = _s5.hs + 1 end
    if is_kill then table.insert(_s5.kills, now) end
end
function _G._S5_SCALE()
    local now = os.time()
    local wk = 0
    for _, t in ipairs(_s5.kills) do if now - t <= _s5.window then wk = wk + 1 end end
    local kpm = wk / (_s5.window / 60.0)
    local hs  = _s5.hits > 0 and (_s5.hs / _s5.hits) or 0
    local s = 1.0
    if kpm > _caps.kpm then s = s * (_caps.kpm / kpm) end
    if hs  > _caps.hs  then s = s * (_caps.hs  / hs)  end
    if s > 1.0 then s = 1.0 end
    if s < 0.30 then s = 0.30 end
    return s
end
"""

L_ANTI_DEBUG = r"""
-- [S6] ANTI-DEBUG
local _s6_orig = debug and debug.sethook
local _s6_trips = 0
if debug then
    debug.sethook = function(...)
        _s6_trips = _s6_trips + 1
        if _s6_trips >= 2 then _G._MOD_PAUSED = true end
        return _s6_orig and _s6_orig(...)
    end
end
_G._S6_WATCH = function(tbl)
    if not tbl then return end
    local mt = getmetatable(tbl)
    if not mt then return end
    local old = mt.__index
    mt.__index = function(t, k)
        local s = tostring(k)
        if s:find("Report") or s:find("Verify") then
            _s6_trips = _s6_trips + 1
            return function() end
        end
        if old then return old(t, k) end
    end
end
"""

L_MEM_ATTEST = r"""
-- [S7] MEM ATTEST
local _s7_sig = {}
do
    local seed = os.time() % 0x7FFFFFFF
    for i = 1, 32 do _s7_sig[i] = (seed * 1103515245 + 12345) % 256; seed = _s7_sig[i] end
end
local _s7_orig = _G.GetFileMD5
_G.GetFileMD5 = function(path)
    if path and tostring(path):find("lua") then
        return string.format("%02x", table.unpack(_s7_sig))
    end
    if _s7_orig then return _s7_orig(path) end
    return ""
end
"""

L_TRAFFIC_SHAPE = r"""
-- [S8] TRAFFIC SHAPE
do
    local tk = package.loaded["common.time_ticker"]
    if tk and NetUtil and NetUtil.SendPacket then
        local orig = NetUtil.SendPacket
        NetUtil.SendPacket = function(name, ...)
            if math.random() < 0.03 then
                tk.AddTimerOnce(0.05 + math.random() * 0.15, function() orig(name, ...) end)
                return nil
            end
            return orig(name, ...)
        end
        local function _f()
            pcall(function() orig("KeepAlive", string.rep("\0", math.random(2, 12))) end)
            tk.AddTimerOnce(1.5 + math.random() * 2.5, _f)
        end
        tk.AddTimerOnce(2.0, _f)
    end
end
"""

SECURITY_LAYERS = [L_SYSCALL_MASK, L_STRING_CRYPT, L_RPC_NORMALIZE, L_BEHAVIOR_DRIFT,
                   L_STAT_THROTTLE, L_ANTI_DEBUG, L_MEM_ATTEST, L_TRAFFIC_SHAPE]

# ============================================================
# LUA BLOCKS
# ============================================================
CROSSHAIR_LUA = r"""
-- CROSSHAIR SYSTEM
local _ch = { style = "$crosshair", size = 12, thickness = 2,
    color = {R = 1.0, G = 1.0, B = 1.0, A = 1.0}, gap = 4 }
local _ch_styles = {
    cross        = function(cx, cy, s, t, g) return {
        {cx - s - g, cy, cx - g, cy}, {cx + g, cy, cx + s + g, cy},
        {cx, cy - s - g, cx, cy - g}, {cx, cy + g, cx, cy + s + g} } end,
    dot          = function(cx, cy, s, t, g) return { {cx - 2, cy, cx + 2, cy}, {cx, cy - 2, cx, cy + 2} } end,
    circle_cross = function(cx, cy, s, t, g) return {
        {cx - s - g, cy, cx - g, cy}, {cx + g, cy, cx + s + g, cy},
        {cx, cy - s - g, cx, cy - g}, {cx, cy + g, cx, cy + s + g},
        {circle = true, radius = s * 0.6} } end,
    chevron      = function(cx, cy, s, t, g) return {
        {cx - s, cy + s, cx, cy - s}, {cx, cy - s, cx + s, cy + s} } end,
    cross_gap    = function(cx, cy, s, t, g) return {
        {cx - s * 1.5, cy, cx - g * 2, cy}, {cx + g * 2, cy, cx + s * 1.5, cy},
        {cx, cy - s * 1.5, cx, cy - g * 2}, {cx, cy + g * 2, cx, cy + s * 1.5} } end,
    dot_circle   = function(cx, cy, s, t, g) return {
        {cx - 2, cy, cx + 2, cy}, {cx, cy - 2, cx, cy + 2},
        {circle = true, radius = s * 0.8} } end,
    t_shape      = function(cx, cy, s, t, g) return {
        {cx - s, cy, cx + s, cy}, {cx, cy + g, cx, cy + s + g} } end,
}
local function _ch_Draw()
    pcall(function()
        local Canvas = _G._CrosshairCanvas
        if not Canvas then return end
        local pc = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
        if not slua.isValid(pc) then return end
        local vp = require("client.common.ui_util").GetViewportSize()
        local cx, cy = vp.X * 0.5, vp.Y * 0.5
        local fn = _ch_styles[_ch.style] or _ch_styles.cross
        for _, p in ipairs(fn(cx, cy, _ch.size, _ch.thickness, _ch.gap)) do
            if p.circle then Canvas:DrawCircle(cx, cy, p.radius, _ch.color, _ch.thickness)
            else Canvas:DrawLine(p[1], p[2], p[3], p[4], _ch.color, _ch.thickness) end
        end
    end)
end
_G._CH_Draw = _ch_Draw
"""

GRAPHICS_LUA = r"""
-- SYSTEM & GRAPHICS
local _gfx = { ipad_perspective = false, fov_degree = 110, visual_cleanup = false,
               potato_mode = false, fps_unlock = false, orig_fov = nil }
local function _gfx_fov()
    pcall(function()
        local pc = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
        if not slua.isValid(pc) then return end
        local cam = import("GameplayStatics").GetPlayerCameraManager(pc, 0)
        if not slua.isValid(cam) then return end
        if not _gfx.orig_fov then _gfx.orig_fov = cam.DefaultFOV end
        if _gfx.ipad_perspective then cam.DefaultFOV = _gfx.fov_degree; cam:SetFOV(_gfx.fov_degree)
        else cam:SetFOV(_gfx.orig_fov) end
    end)
end
local function _gfx_visual()
    pcall(function()
        local K = import("KismetSystemLibrary"); local w = slua.getWorld()
        if not K or not w then return end
        if _gfx.visual_cleanup then
            K.ExecuteConsoleCommand(w, "foliage.DensityScale 0.2")
            K.ExecuteConsoleCommand(w, "r.Fog 0"); K.ExecuteConsoleCommand(w, "r.VolumetricFog 0")
        else
            K.ExecuteConsoleCommand(w, "foliage.DensityScale 1.0")
            K.ExecuteConsoleCommand(w, "r.Fog 1"); K.ExecuteConsoleCommand(w, "r.VolumetricFog 1")
        end
    end)
end
local function _gfx_potato()
    pcall(function()
        local K = import("KismetSystemLibrary"); local w = slua.getWorld()
        if not K or not w then return end
        if _gfx.potato_mode then
            K.ExecuteConsoleCommand(w, "r.ScreenPercentage 60")
            K.ExecuteConsoleCommand(w, "r.ShadowQuality 0")
            K.ExecuteConsoleCommand(w, "sg.ViewDistanceQuality 0")
        else
            K.ExecuteConsoleCommand(w, "r.ScreenPercentage 100")
            K.ExecuteConsoleCommand(w, "sg.ViewDistanceQuality 3")
        end
    end)
end
local function _gfx_fps()
    pcall(function()
        local K = import("KismetSystemLibrary"); local w = slua.getWorld()
        if not K or not w then return end
        if _gfx.fps_unlock then
            K.ExecuteConsoleCommand(w, "t.MaxFPS 165")
            K.ExecuteConsoleCommand(w, "r.VSync 0")
        else K.ExecuteConsoleCommand(w, "t.MaxFPS 60") end
    end)
end
_G._GFX = {
    SetIPadPerspective = function(v) _gfx.ipad_perspective = v; _gfx_fov() end,
    SetFOV             = function(d) _gfx.fov_degree = math.max(90, math.min(135, d)); _gfx_fov() end,
    SetVisualCleanup   = function(v) _gfx.visual_cleanup = v; _gfx_visual() end,
    SetPotatoMode      = function(v) _gfx.potato_mode = v; _gfx_potato() end,
    SetFPSUnlock       = function(v) _gfx.fps_unlock = v; _gfx_fps() end,
}
"""

PLAYER_ESP_LUA = r"""
-- PLAYER ESP (with real-time names)
local _esp = { enabled = true, style = "$esp_style", rotate = $esp_rotate,
    name_on = $esp_name_bool, last_rotate = os.time(),
    styles = {"box","line","circle","skeleton","head","distance","name","health"} }
local function _esp_pick()
    if _esp.style ~= "auto" then return _esp.style end
    return _esp.styles[math.random(#_esp.styles)]
end
local function _esp_name(pawn)
    local n = nil
    pcall(function() n = pawn.PlayerName end)
    if not n then pcall(function() n = pawn:GetPlayerName() end) end
    if not n and pawn.PlayerState then pcall(function() n = pawn.PlayerState.PlayerName end) end
    if not n then pcall(function()
        local ps = pawn:GetPlayerStateSafety()
        if slua.isValid(ps) then n = ps.PlayerName end
    end) end
    if not n and pawn.PlayerKey then n = "Bot_" .. tostring(pawn.PlayerKey) end
    return tostring(n or "?")
end
local function _esp_apply(pawn)
    if not slua.isValid(pawn) then return end
    local vis = {R = 1.0, G = 0.0, B = 0.0, A = 1.0}
    local occ = {R = 1.0, G = 0.8, B = 0.0, A = 1.0}
    pcall(function()
        if slua.isValid(pawn.Mesh) then
            pawn.Mesh:SetDrawDyeing(true); pawn.Mesh:SetDrawDyeingMode(1)
            pawn.Mesh:SetVisibleDyeingColor(vis); pawn.Mesh:SetOccludedDyeingColor(occ)
            pawn.Mesh:SetDyeingColorFadeDistance(99999.0)
            pawn.Mesh:SetDyeingColorMinMaxDistance(0.0, 99999.0)
            pawn.Mesh:SetDrawHighlight(true); pawn.Mesh:OverrideHighlightColor(vis)
            pawn.Mesh:SetHighlightCanBeOccluded(false)
            pawn.Mesh:SetDrawIdeaOutline(true); pawn.Mesh:SetIdeaOutlineNew(true)
            pawn.Mesh:SetIdeaOutlineOcclusionHighlight(true)
            pawn.Mesh:OverrideIdeaOutlineColor(vis); pawn.Mesh:SetIdeaOutlineOcclusionColor(occ)
            pawn.Mesh:OverrideIdeaOutlineThickness(18.0)
        end
    end)
end
local _name_widgets = {}
local function _esp_tag(pawn, pc)
    if not _esp.name_on then return end
    local key = pawn.PlayerKey or tostring(pawn)
    local w = _name_widgets[key]
    if not w or not slua.isValid(w) then
        pcall(function()
            local BP = "/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"
            w = slua.loadUI(BP)
            if not w or not slua.isValid(w) then return end
            require("game_frontend_hud").AddToContainer(UIContainers.Top, w, 9000)
            if w.RichText_Content then
                local fi = w.RichText_Content.Font
                if fi then fi.Size = 12; w.RichText_Content:SetFont(fi) end
                w.RichText_Content:SetColorAndOpacity(FSlateColor(FLinearColor(1, 0.85, 0, 1)))
            end
            w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
            w:SetBackgroundColor(FLinearColor(0, 0, 0, 0.55))
            _name_widgets[key] = w
        end)
        w = _name_widgets[key]
    end
    if not w or not slua.isValid(w) then return end
    pcall(function()
        local loc = pawn:K2_GetActorLocation()
        local s = import("Vector2D")()
        if pc:ProjectWorldLocationToScreen({X = loc.X, Y = loc.Y, Z = loc.Z + 200}, s, false) then
            if s.X < 0 or s.Y < 0 then w:SetWidgetVisibility(UEnums.ESlateVisibility.Hidden); return end
            w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
            w:SetPositionInViewport(FVector2D(s.X - 60, s.Y - 20), true)
            w:SetDesiredSizeInViewport(FVector2D(120, 20))
            local name = _esp_name(pawn)
            local me = GameplayData.GetPlayerCharacter()
            if slua.isValid(me) then
                local mp = me:K2_GetActorLocation()
                local d = math.sqrt((mp.X-loc.X)^2 + (mp.Y-loc.Y)^2 + (mp.Z-loc.Z)^2) / 100
                name = name .. " [" .. string.format("%.0fm", d) .. "]"
            end
            if w.RichText_Content then w.RichText_Content:SetText(name) end
        end
    end)
end
local function _esp_tick()
    if not _esp.enabled then return end
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    local now = os.time()
    if now - _esp.last_rotate >= _esp.rotate then
        _esp.style = _esp_pick(); _esp.last_rotate = now
    end
    local me = GameplayData.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me:GetTeamID() or 0
    local pc = me:GetPlayerControllerSafety()
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me then
            local t = p.TeamID or 0
            if t ~= myTeam and (p.Health or 0) > 0 then
                _esp_apply(p)
                if _esp.name_on and slua.isValid(pc) then _esp_tag(p, pc) end
            end
        end
    end
end
_G._ESP_Tick = _esp_tick
"""

LOOT_ESP_LUA = r"""
-- SUPPLY & LOOT ESP
local _loot = { enabled = $loot_enabled, weapons = true, ammo = true, meds = true,
    armor = true, attachments = true, airdrop = true, tomb = true, max_range = 150,
    tiers = {
        legendary = {R = 1.0, G = 0.5, B = 0.0, A = 1.0},
        epic      = {R = 0.6, G = 0.0, B = 1.0, A = 1.0},
        rare      = {R = 0.0, G = 0.5, B = 1.0, A = 1.0},
        common    = {R = 1.0, G = 1.0, B = 1.0, A = 1.0},
    } }
local function _tier(id)
    local n = tonumber(id) or 0
    if n >= 100000 then return "legendary" end
    if n >= 50000  then return "epic" end
    if n >= 10000  then return "rare" end
    return "common"
end
local function _cat(a)
    local c = tostring(a)
    if c:find("AirDrop") then return "airdrop" end
    if c:find("TombBox") or c:find("DeadBox") then return "tomb" end
    if c:find("Weapon") then return "weapons" end
    if c:find("Ammo") or c:find("Bullet") then return "ammo" end
    if c:find("Med") or c:find("Heal") then return "meds" end
    if c:find("Armor") or c:find("Helmet") then return "armor" end
    if c:find("Attachment") or c:find("Scope") then return "attachments" end
end
local function _show(c)
    if c == "weapons" then return _loot.weapons end
    if c == "ammo" then return _loot.ammo end
    if c == "meds" then return _loot.meds end
    if c == "armor" then return _loot.armor end
    if c == "attachments" then return _loot.attachments end
    if c == "airdrop" then return _loot.airdrop end
    if c == "tomb" then return _loot.tomb end
    return false
end
local function _mesh(mesh, t)
    if not mesh or not slua.isValid(mesh) then return end
    local c = _loot.tiers[t] or _loot.tiers.common
    pcall(function()
        mesh:SetDrawDyeing(true); mesh:SetDrawDyeingMode(1)
        mesh:SetVisibleDyeingColor(c); mesh:SetOccludedDyeingColor(c)
        mesh:SetDyeingColorFadeDistance(99999.0)
        mesh:SetDrawHighlight(true); mesh:OverrideHighlightColor(c)
        mesh:SetHighlightCanBeOccluded(false)
        mesh:SetDrawIdeaOutline(true); mesh:SetIdeaOutlineNew(true)
        mesh:OverrideIdeaOutlineColor(c); mesh:OverrideIdeaOutlineThickness(6.0)
    end)
end
_G._Loot_Tick = function()
    if not _loot.enabled then return end
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    local me = GameplayData.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local mp = me:K2_GetActorLocation()
    pcall(function()
        for _, cn in ipairs({"PickupActor", "PlayerTombBox", "AirDropBox", "PickupActorBase"}) do
            local ok, cls = pcall(import, cn)
            if ok and cls then
                local actors = Game:GetActorsByClass(cls)
                if actors and actors.Num then
                    for i = 0, actors:Num() - 1 do
                        local a = actors:Get(i)
                        if slua.isValid(a) then
                            local loc = a:K2_GetActorLocation()
                            local d = math.sqrt((mp.X-loc.X)^2 + (mp.Y-loc.Y)^2 + (mp.Z-loc.Z)^2) / 100
                            if d <= _loot.max_range then
                                local c = _cat(a)
                                if c and _show(c) then
                                    local m = a.Mesh or a.StaticMeshComponent or a.SkeletalMeshComponent
                                    if m then _mesh(m, _tier(a.ItemID or a.PickupID)) end
                                end
                            end
                        end
                    end
                end
            end
        end
    end)
end
"""

MENU_LUA = r"""
-- DEVIL MENU
local _menu = { open = false, widget = nil, active_tab = "PLAYER ESP",
    tabs = {"PLAYER ESP", "COMBAT ENGINE", "VEHICLE RADAR", "SUPPLY & LOOT ESP", "SYSTEM & GRAPHICS"},
    right_sections = {"CONTROLS", "GRAPHICS", "CUSTOMIZE BUTTONS", "SENSITIVITY", "PICK UP",
                      "CROSSHAIR & EFFECTS", "AUDIO & HAPTICS", "PRIVACY & SOCIAL"} }
_G._Menu_Toggle  = function() _menu.open = not _menu.open end
_G._Menu_SetTab  = function(t) for _, x in ipairs(_menu.tabs) do if x == t then _menu.active_tab = t end end end
_G._Menu_GetTab  = function() return _menu.active_tab end
_G._Menu_GetRight = function() return _menu.right_sections end
"""

# ============================================================
# MASTER TEMPLATE
# ============================================================
MASTER = Template(r"""
-- =============================================================
-- DEVIL MENU — Generated by $bot_name
-- PROFILE: $profile | AIMBOT: $aimbot/100
-- MB: $mb_state @ ${mb_range}m ($mb_chance% roll)
-- ESP: $esp_style | NAME: $esp_name_state | LOOT: $loot_state
-- CROSSHAIR: $crosshair | BUILT: $built_at
-- =============================================================

local EXPIRY_TIMESTAMP = os.time({ year = 2027, month = 10, day = 28, hour = 22, min = 40, sec = 0 })
local TELEGRAM_LINK = "https://t.me/$bot_name"
local _expiredShown = false
function _G.CheckExpiration()
    if os.time() >= EXPIRY_TIMESTAMP then _G._MOD_EXPIRED = true; return false end
    _G._MOD_EXPIRED = false; return true
end
function _G.ShowExpiredPopup()
    if _expiredShown then return end
    _expiredShown = true
    pcall(function()
        local Msg = require("client.slua.logic.common.logic_common_msg_box")
        Msg.Show(4, "[$bot_name] EXPIRED", "Trial complete.\nTelegram: " .. TELEGRAM_LINK,
            function()
                local Web = require("client.slua.logic.url.logic_webview_sdk")
                if Web then Web:OpenURL(TELEGRAM_LINK) end
            end)
    end)
end

local AIMBOT_STRENGTH = $aimbot
local MB_ENABLED      = $mb_bool
local MB_RANGE        = $mb_range
local MB_CHANCE       = $mb_chance
local ESP_STYLE       = "$esp_style"
local ESP_ROTATE_SEC  = $esp_rotate
local ESP_NAME_ON     = $esp_name_bool
local LOOT_ENABLED    = $loot_bool
local CROSSHAIR_STYLE = "$crosshair"

local AIM_LERP   = 0.05 + (AIMBOT_STRENGTH / 100) * 0.90
local AIM_JITTER = 0.00030 * (100 - AIMBOT_STRENGTH) / 100

$security_layers

$crosshair_lua
$graphics_lua
$player_esp_lua
$loot_esp_lua
$menu_lua

local GameplayData = require("GameLua.GameCore.Data.GameplayData")
local function _dm(a, b)
    if not a or not b then return 99999 end
    return math.sqrt((a.X-b.X)^2 + (a.Y-b.Y)^2 + (a.Z-b.Z)^2) / 100
end
local function _Enemies()
    local out = {}
    local me = GameplayData.GetPlayerCharacter()
    if not slua.isValid(me) then return out end
    local myTeam = me:GetTeamID() or 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me then
            local t = p.TeamID or 0
            if t ~= myTeam and (p.Health or 0) > 0 then table.insert(out, p) end
        end
    end
    return out
end
local function _Head(a)
    for _, b in ipairs({"Head","head","neck_01","Bip001-Head","Bip01-Head"}) do
        local ok, pos = pcall(function() return a:GetBonePos(b, {X=0,Y=0,Z=0}) end)
        if ok and pos then return pos end
    end
    local ok, loc = pcall(function() return a:K2_GetActorLocation() end)
    if ok and loc then return {X=loc.X, Y=loc.Y, Z=loc.Z + 160} end
end

local _last_id = -1
local function _Aim(weapon, player, pc)
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    local shoot = weapon.ShootWeaponComponent
    if not shoot then return end
    local curId = shoot.CurShootID or -1
    if curId == _last_id then return end
    _last_id = curId
    local cam = import("GameplayStatics").GetPlayerCameraManager(pc, 0)
    if not slua.isValid(cam) then return end
    local camLoc = cam:GetCameraLocation()
    local vp = require("client.common.ui_util").GetViewportSize()
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local best, bestPos = 99999, nil
    for _, e in ipairs(_Enemies()) do
        local vis = false
        pcall(function() vis = pc:LineOfSightTo(e, camLoc, true) end)
        if vis then
            local hp = _Head(e)
            if hp then
                local s = import("Vector2D")()
                if pc:ProjectWorldLocationToScreen(hp, s, false) then
                    local d = math.sqrt((s.X-cx)^2 + (s.Y-cy)^2)
                    if d < best then best, bestPos = d, hp end
                end
            end
        end
    end
    if not bestPos then return end
    local muzzle = nil
    pcall(function()
        local we = weapon.ShootWeaponEntityComp
        if we and we.GetMuzzleLocation then muzzle = we:GetMuzzleLocation() end
    end)
    if not muzzle then pcall(function() muzzle = player:GetBonePos("head", {X=0,Y=0,Z=0}) end) end
    if not muzzle then return end
    local rot = import("KismetMathLibrary").FindLookAtRotation(muzzle, bestPos)
    rot.Pitch = rot.Pitch + (math.random() - 0.5) * AIM_JITTER
    rot.Yaw   = rot.Yaw   + (math.random() - 0.5) * AIM_JITTER
    shoot:ShootBulletInner(bestPos, rot, curId)
    if _G._S5_ON_SHOT then _G._S5_ON_SHOT(true, false) end
end

local function _MB(weapon, player, pc)
    if not MB_ENABLED then return end
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    if math.random(100) > MB_CHANCE then return end
    local mp = player:K2_GetActorLocation()
    local near, nd = nil, 99999
    for _, e in ipairs(_Enemies()) do
        local d = _dm(mp, e:K2_GetActorLocation())
        if d < nd then nd, near = d, e end
    end
    if not near or nd > MB_RANGE then return end
    local shoot = weapon.ShootWeaponComponent
    if not shoot then return end
    local head = _Head(near)
    if not head then return end
    local muzzle = nil
    pcall(function() muzzle = player:GetBonePos("head", {X=0,Y=0,Z=0}) end)
    if not muzzle then return end
    local rot = import("KismetMathLibrary").FindLookAtRotation(muzzle, head)
    shoot:ShootBulletInner(head, rot, shoot.CurShootID or -1)
    if _G._S5_ON_SHOT then _G._S5_ON_SHOT(true, false) end
end

local function _Tick()
    if _G._MOD_PAUSED then return end
    pcall(function()
        local player = GameplayData.GetPlayerCharacter()
        if not slua.isValid(player) then return end
        local wm = player.WeaponManagerComponent
        if not wm then return end
        local weapon = wm.CurrentWeaponReplicated
        if not slua.isValid(weapon) then return end
        local pc = player:GetPlayerControllerSafety()
        if not slua.isValid(pc) then return end
        _Aim(weapon, player, pc)
        _MB(weapon, player, pc)
        if _G._ESP_Tick then _G._ESP_Tick() end
        if _G._Loot_Tick then _G._Loot_Tick() end
        if _G._CH_Draw then _G._CH_Draw() end
        if _G._S4_TICK then _G._S4_TICK() end
    end)
end

local ticker = require("common.time_ticker")
if not _G._DEVIL_LOOP then
    _G._DEVIL_LOOP = true
    local function _loop() _Tick(); ticker.AddTimerOnce(0.016, _loop) end
    ticker.AddTimerOnce(0.5, _loop)
end

print("[DEVIL MENU] LOADED — $profile | AIM:$aimbot | MB:${mb_range}m | CH:$crosshair")
""")

def _b(v): return "true" if v else "false"

def generate_lua(settings: dict, bot_name: str = "devil_menu") -> str:
    cfg = dict(settings)
    aimbot    = max(1, min(100, int(cfg.get("aimbot", 35))))
    mb_on     = bool(cfg.get("mb_on", True))
    mb_range  = max(1.0, min(50.0, float(cfg.get("mb_range", 20))))
    mb_chance = max(0, min(100, int(cfg.get("mb_chance", 15))))
    esp_style = cfg.get("esp_style", "auto")
    esp_rot   = max(5, min(300, int(cfg.get("esp_rotate", 30))))
    esp_name  = bool(cfg.get("esp_name", True))
    loot_on   = bool(cfg.get("loot_esp", True))
    crosshair = cfg.get("crosshair", "cross")
    profile   = cfg.get("profile", "safe")

    return MASTER.safe_substitute(
        bot_name        = bot_name,
        profile         = profile,
        aimbot          = aimbot,
        mb_bool         = _b(mb_on),
        mb_state        = "ON" if mb_on else "OFF",
        mb_range        = int(mb_range) if mb_range == int(mb_range) else mb_range,
        mb_chance       = mb_chance,
        esp_style       = esp_style,
        esp_rotate      = esp_rot,
        esp_name_bool   = _b(esp_name),
        esp_name_state  = "ON" if esp_name else "OFF",
        loot_bool       = _b(loot_on),
        loot_state      = "ON" if loot_on else "OFF",
        loot_enabled    = _b(loot_on),
        crosshair       = crosshair,
        built_at        = time.strftime("%Y-%m-%d %H:%M:%S"),
        security_layers = "\n".join(SECURITY_LAYERS),
        crosshair_lua   = CROSSHAIR_LUA,
        graphics_lua    = GRAPHICS_LUA,
        player_esp_lua  = PLAYER_ESP_LUA,
        loot_esp_lua    = LOOT_ESP_LUA,
        menu_lua        = MENU_LUA,
    )

# ============================================================
# BOT LOGIC
# ============================================================
DEFAULT_SETTINGS = {
    "profile": "safe", "aimbot": 35, "mb_on": True, "mb_range": 20, "mb_chance": 15,
    "esp_style": "auto", "esp_rotate": 30, "esp_name": True, "loot_esp": True, "crosshair": "cross",
}

def get_settings(ctx):
    s = ctx.user_data.get("settings")
    if not s:
        s = dict(DEFAULT_SETTINGS); ctx.user_data["settings"] = s
    return s

def settings_text(s):
    return (
        f"*Profile:* `{s['profile']}`\n"
        f"*Aimbot:* `{s['aimbot']}/100`\n"
        f"*Magic Bullet:* `{'ON' if s['mb_on'] else 'OFF'}` @ `{s['mb_range']}m` ({s['mb_chance']}% roll)\n"
        f"*ESP:* `{s['esp_style']}` · *Name:* `{'ON' if s['esp_name'] else 'OFF'}`\n"
        f"*Loot:* `{'ON' if s['loot_esp'] else 'OFF'}` · *Crosshair:* `{s['crosshair']}`"
    )

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Full", callback_data="preset:full"),
         InlineKeyboardButton("🟢 Safe", callback_data="preset:safe"),
         InlineKeyboardButton("🎲 Random", callback_data="preset:random")],
        [InlineKeyboardButton("🎯 Aimbot", callback_data="menu:aimbot"),
         InlineKeyboardButton("💥 MB", callback_data="menu:mb")],
        [InlineKeyboardButton("👁 ESP", callback_data="menu:esp"),
         InlineKeyboardButton("📛 Name", callback_data="menu:name"),
         InlineKeyboardButton("📦 Loot", callback_data="menu:loot")],
        [InlineKeyboardButton("➕ Crosshair", callback_data="menu:crosshair"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings")],
        [InlineKeyboardButton("🛠 Generate .lua", callback_data="generate")],
    ])

async def start(update, ctx):
    s = get_settings(ctx)
    txt = f"*{BOT_NAME}* — Devil Menu builder\n\n{settings_text(s)}"
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_full(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["full"]); s["profile"]="full"
    await update.message.reply_text("🔴 Full.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_safe(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["safe"]); s["profile"]="safe"
    await update.message.reply_text("🟢 Safe.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_random(update, ctx):
    s = get_settings(ctx); s.update(PROFILES["random"]); s["profile"]="random"
    await update.message.reply_text("🎲 Random.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_aimbot(update, ctx):
    s = get_settings(ctx)
    if not ctx.args: await update.message.reply_text("`/aimbot 1-100`", parse_mode="Markdown"); return
    try: v = int(ctx.args[0])
    except: await update.message.reply_text("Number."); return
    if not 1 <= v <= 100: await update.message.reply_text("1-100."); return
    s["aimbot"] = v
    await update.message.reply_text(f"🎯 `{v}/100`", parse_mode="Markdown")

async def cmd_mb(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/mb on|off`", parse_mode="Markdown"); return
    s["mb_on"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"💥 `{'ON' if s['mb_on'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_range(update, ctx):
    s = get_settings(ctx)
    if not ctx.args: await update.message.reply_text("`/range <m>`", parse_mode="Markdown"); return
    try: v = float(ctx.args[0])
    except: await update.message.reply_text("Number."); return
    if not 1 <= v <= 50: await update.message.reply_text("1-50."); return
    s["mb_range"] = v
    await update.message.reply_text(f"💥 `{v}m`", parse_mode="Markdown")

async def cmd_esp(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or (ctx.args[0] not in ESP_STYLES and ctx.args[0] != "auto"):
        await update.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in ESP_STYLES)+", `auto`", parse_mode="Markdown"); return
    s["esp_style"] = ctx.args[0]
    await update.message.reply_text(f"👁 `{s['esp_style']}`", parse_mode="Markdown")

async def cmd_name(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/name on|off`", parse_mode="Markdown"); return
    s["esp_name"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"📛 `{'ON' if s['esp_name'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_loot(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0].lower() not in ("on","off"):
        await update.message.reply_text("`/loot on|off`", parse_mode="Markdown"); return
    s["loot_esp"] = ctx.args[0].lower()=="on"
    await update.message.reply_text(f"📦 `{'ON' if s['loot_esp'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_crosshair(update, ctx):
    s = get_settings(ctx)
    if not ctx.args or ctx.args[0] not in CROSSHAIRS:
        await update.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown"); return
    s["crosshair"] = ctx.args[0]
    await update.message.reply_text(f"➕ `{s['crosshair']}`", parse_mode="Markdown")

async def cmd_settings(update, ctx):
    await update.message.reply_text(settings_text(get_settings(ctx)), parse_mode="Markdown", reply_markup=main_menu_kb())

async def cmd_generate(update, ctx):
    await _send(update, ctx, get_settings(ctx))

async def _send(update, ctx, s):
    try:
        lua = generate_lua(s, bot_name=BOT_NAME)
    except Exception as e:
        t = update.message or update.callback_query.message
        await t.reply_text(f"Error: `{e}`", parse_mode="Markdown"); return
    fname = "BRPlayerCharacterBase.lua"
    buf = io.BytesIO(lua.encode("utf-8")); buf.name = fname
    cap = f"📦 *{fname}*\n\n{settings_text(s)}"
    t = update.message or update.callback_query.message
    await t.reply_document(document=InputFile(buf, filename=fname), caption=cap, parse_mode="Markdown")

async def on_callback(update, ctx):
    q = update.callback_query; await q.answer()
    d = q.data; s = get_settings(ctx)
    if d.startswith("preset:"):
        p = d.split(":",1)[1]
        if p in PROFILES: s.update(PROFILES[p]); s["profile"]=p
        await q.edit_message_text(f"*{p.upper()}*.\n\n{settings_text(s)}", parse_mode="Markdown", reply_markup=main_menu_kb())
    elif d == "menu:aimbot":     await q.edit_message_text("`/aimbot 1-100`", parse_mode="Markdown")
    elif d == "menu:mb":         await q.edit_message_text("`/mb on|off` · `/range <m>`", parse_mode="Markdown")
    elif d == "menu:esp":        await q.edit_message_text("`/esp <style>` — "+", ".join(f"`{k}`" for k in ESP_STYLES), parse_mode="Markdown")
    elif d == "menu:name":       await q.edit_message_text("`/name on|off`", parse_mode="Markdown")
    elif d == "menu:loot":       await q.edit_message_text("`/loot on|off`", parse_mode="Markdown")
    elif d == "menu:crosshair":  await q.edit_message_text("`/crosshair <style>` — "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown")
    elif d == "menu:settings":   await q.edit_message_text(settings_text(s), parse_mode="Markdown", reply_markup=main_menu_kb())
    elif d == "generate":
        await q.edit_message_text("Generating…"); await _send(update, ctx, s)

async def cmd_help(update, ctx):
    await update.message.reply_text(
        "*Commands*\n/start /full /safe /random\n/aimbot 1-100\n/mb on|off\n/range <m>\n"
        "/esp <style>\n/name on|off\n/loot on|off\n/crosshair <style>\n/settings\n/generate\n",
        parse_mode="Markdown")

def main():
    if not BOT_TOKEN: raise SystemExit("Set BOT_TOKEN env.")
    app = Application.builder().token(BOT_TOKEN).build()
    for cmd, fn in [("start",start),("full",cmd_full),("safe",cmd_safe),("random",cmd_random),
                    ("aimbot",cmd_aimbot),("mb",cmd_mb),("range",cmd_range),("esp",cmd_esp),
                    ("name",cmd_name),("loot",cmd_loot),("crosshair",cmd_crosshair),
                    ("settings",cmd_settings),("generate",cmd_generate),("help",cmd_help)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(on_callback))
    print(f"[{BOT_NAME}] running…")
    app.run_polling()

if __name__ == "__main__":
    main()
