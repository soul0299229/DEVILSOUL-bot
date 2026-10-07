"""
lua_features.py — DEVILSOUL ELITE v4
Fixes: Vector2D positions, tab sections, working ESP.
"""
from __future__ import annotations
from datetime import datetime, timezone

REGISTRY: dict[str, dict] = {}

def feature(fid, label, deps=(), menu=None):
    def deco(fn):
        REGISTRY[fid] = {"id": fid, "label": label, "deps": list(deps),
                         "fn": fn, "menu": list(menu) if menu else []}
        return fn
    return deco

HEADER_API = r"""
_G.DS = _G.DS or {}
_G.DS.Ticks = _G.DS.Ticks or {}
_G.DS.Slow = _G.DS.Slow or {}
_G.DS_Features = _G.DS_Features or {}
function _G.DS_Reg(n, f) if type(f) == "function" then _G.DS.Ticks[n] = f end end
function _G.DS_SlowReg(n, f) if type(f) == "function" then _G.DS.Slow[n] = f end end
function _G.DS_Get(id)
    for _, f in ipairs(_G.DS_Features) do if f.id == id then return f.val end end
    return 0
end
function _G.DS_Set(id, val)
    for _, f in ipairs(_G.DS_Features) do
        if f.id == id then f.val = val return true end
    end
    return false
end
"""

# ═════════════════════════════════════════════════════════════════
# MENU STATE
# ═════════════════════════════════════════════════════════════════
@feature("menu", "Feature state table")
def _f_menu(c):
    ids = [
        "esp_box","esp_skeleton","esp_line","esp_distance","esp_name",
        "esp_hp","esp_weapon","esp_radar","esp_vis","esp_fov_circle",
        "aim_silent","aim_smooth","aim_bone","aim_pred","aim_recoil",
        "aim_autofire","aim_shotgun",
        "magic_full","magic_head","magic_neck","magic_body","magic_legs",
        "magic_custom","magic_hitbox","magic_safe",
        "cross_cross","cross_dot","cross_circle","cross_tstyle","cross_rainbow",
        "skin_weapon","skin_outfit","skin_vehicle","skin_parachute",
        "skin_emote","skin_deadbox","skin_killmsg",
        "wallhack","enemy_counter","fps165",
    ]
    on = {
        "esp_box", "esp_skeleton", "esp_hp", "esp_distance", "esp_name",
        "esp_line", "esp_vis",
        "aim_bone", "aim_recoil",
        "magic_head",
        "cross_cross",
        "wallhack", "enemy_counter",
    }
    rows = ",\n    ".join(
        f'{{ id = "{i}", val = {1 if i in on else 0} }}' for i in ids)
    return {"lua": f"_G.DS_Features = {{\n    {rows}\n}}\n".rstrip()}


# ═════════════════════════════════════════════════════════════════
# FIREWALL (compact)
# ═════════════════════════════════════════════════════════════════
@feature("bypass", "Report Firewall")
def _f_bypass(c):
    return {"lua": r"""
local nop = function() end
local T = function() return true end
local F = function() return false end
local function isRep(s)
    if not s then return false end
    s = tostring(s):lower()
    for _, p in ipairs({"report","accuse","judge","kick","vote","ban","watch",
        "suspicion","cheat","hack","blacklist","punish","ticket","complain",
        "behavior","misconduct","teammatehurt","teamhurt","aimabnormal",
        "wallhack","esp","anticheat","seccheck","integrity"}) do
        if s:find(p, 1, true) then return true end
    end
    return false
end
pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...) if isRep(n) then return nil end return o(n, ...) end
    end
end)
pcall(function()
    if _G.SendRPC then
        local o = _G.SendRPC
        _G.SendRPC = function(n, ...) if isRep(n) then return end return o(n, ...) end
    end
end)
pcall(function()
    _G.GameplayCallbacks = _G.GameplayCallbacks or {}
    for _, k in ipairs({"ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow",
        "ReportVerifyInfoFlow","ReportPlayerBehavior","ReportTeammatHurt",
        "ReportPlayerPosition","ReportAimFlow","ReportHitFlow","ReportWallHack",
        "ReportAimbot","ReportMagicBullet","ReportPlayerKillFlow",
        "OnPlayerRPCValidateFailed","OnPlayerActorChannelError","OnShutdownAfterError"}) do
        _G.GameplayCallbacks[k] = nop
    end
end)
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if not sm or sm.__ds_sil then return end
    local rg = sm.Get
    sm.Get = function(self, n)
        local s = rg(self, n)
        if type(s) == "table" and not s.__ds_sil then
            for _, t in ipairs({"ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem",
                "ClientAimTrackingSubsystem","ShootVerifySubSystemClient","ClientAntiCheatSubsystem",
                "ClientMemoryGuardSubsystem","ClientKernelCheckSubsystem","GameReportSubsystem",
                "ClientReportPlayerSubsystem","KickVoteSubsystem","TeammateHurtReportSubsystem"}) do
                if n == t then
                    pcall(function()
                        for k, v in pairs(s) do
                            if type(v) == "function" then
                                local lk = tostring(k):lower()
                                if lk:find("report") or lk:find("send") or lk:find("verify")
                                   or lk:find("check") or lk:find("detect") or lk:find("scan")
                                   or lk:find("judge") or lk:find("accuse") or lk:find("kick")
                                   or lk:find("vote") or lk:find("punish") or lk:find("watch") then
                                    s[k] = nop
                                end
                            end
                        end
                    end)
                    if n == "ClientAimTrackingSubsystem" then
                        s.GetAimData = function() return {accuracy=math.random(42,58),headshotRate=math.random(12,28),aimLockCount=0} end
                        s.IsAimNormal = T
                    end
                    if n == "ShootVerifySubSystemClient" then s.VerifyShot = T end
                    if n == "ClientKernelCheckSubsystem" then s.IsKernelClean = T end
                    if n == "ClientMemoryGuardSubsystem" then s.IsMemoryClean = function() return true,{code=0} end end
                    if n == "ClientWallhackDetectionSubsystem" then s.IsVisionNormal = T end
                    if n == "ClientESPDetectionSubsystem" then s.HasESP = F end
                    s.__ds_sil = true
                    break
                end
            end
        end
        return s
    end
    sm.__ds_sil = true
end)
pcall(function()
    local t = _G.TssSdk
    if t then t.GetFileMD5 = function() return "" end t.VerifyFileSignature = T t.CheckIntegrity = T t.IsEmulator = F end
end)
pcall(function()
    local M = package.loaded["client.slua.logic.common.logic_common_msg_box"]
    if M and M.Show then
        local o = M.Show
        M.Show = function(t_, title, content, ...)
            local tt = tostring(title or ""):lower()
            local cc = tostring(content or ""):lower()
            if tt:find("ban") or tt:find("kick") or tt:find("suspend")
               or cc:find("banned") or cc:find("terminated your connection")
               or cc:find("data error with your client") then
                return
            end
            return o(t_, title, content, ...)
        end
    end
end)
print("[DS FIREWALL] active")
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ANTI-KICK MINIMAL (no state filter — freeze fix)
# ═════════════════════════════════════════════════════════════════
@feature("antikick", "Anti-Kick (minimal)")
def _f_antikick(c):
    return {"lua": r"""
pcall(function()
    local DS_ = require("GameLua.GameCore.Module.Subsystem.DisconnectSubsystem")
    if DS_ and DS_.OnDisconnect then
        local o = DS_.OnDisconnect
        DS_.OnDisconnect = function(self, reason, ...)
            local r = tostring(reason or ""):lower()
            if r:find("data error") or r:find("desync") then
                print("[DS] blocked fake disconnect")
                return
            end
            return o(self, reason, ...)
        end
    end
end)
pcall(function()
    if _G.SendRPC then
        local o = _G.SendRPC
        _G.SendRPC = function(n, ...)
            local s = tostring(n or ""):lower()
            if s:find("validate") or s:find("checksum") then return end
            return o(n, ...)
        end
    end
end)
print("[DS] Anti-kick minimal")
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# IN-GAME SETTINGS MENU — with proper sections
# ═════════════════════════════════════════════════════════════════
@feature("ingame_menu", "In-Game Settings Menu")
def _f_ingame_menu(c):
    return {"lua": r"""
local MENU = { ready = false }

local TID = { title=990000, esp=990001, combat=990002, vehicle=990003, loot=990004, sys=990005 }
local FAKE = {
    [990000] = "DEVILSOUL",
    [990001] = "PLAYER ESP",
    [990002] = "COMBAT ENGINE",
    [990003] = "VEHICLE RADAR",
    [990004] = "SUPPLY & LOOT",
    [990005] = "SYSTEM & GRAPHICS",
}

local CATALOG = {
    -- PLAYER ESP
    {"esp_box","Box ESP","ESP"},
    {"esp_skeleton","Skeleton ESP","ESP"},
    {"esp_line","Snap Lines","ESP"},
    {"esp_distance","Distance Numbers","ESP"},
    {"esp_name","Player Names","ESP"},
    {"esp_hp","Health Bars","ESP"},
    {"esp_weapon","Weapon Icons","ESP"},
    {"esp_vis","Visibility Colors","ESP"},
    {"esp_radar","MiniMap Radar","ESP"},
    {"esp_fov_circle","FOV Circle","ESP"},
    -- COMBAT ENGINE
    {"aim_silent","Silent Aim","COMBAT"},
    {"aim_smooth","Smooth Aim","COMBAT"},
    {"aim_bone","Bone Lock","COMBAT"},
    {"aim_pred","Prediction Aim","COMBAT"},
    {"aim_recoil","Recoil Compensation","COMBAT"},
    {"aim_autofire","Auto Fire","COMBAT"},
    {"aim_shotgun","Shotgun Auto","COMBAT"},
    {"magic_full","Magic Full Body","COMBAT"},
    {"magic_head","Magic Head Only","COMBAT"},
    {"magic_neck","Magic Neck","COMBAT"},
    {"magic_body","Magic Body","COMBAT"},
    {"magic_legs","Magic Legs","COMBAT"},
    {"magic_custom","Magic Custom","COMBAT"},
    {"magic_hitbox","Hitbox Expand","COMBAT"},
    {"magic_safe","Safe 60% Magic","COMBAT"},
    {"cross_cross","Crosshair Cross","COMBAT"},
    {"cross_dot","Crosshair Dot","COMBAT"},
    {"cross_circle","Crosshair Circle","COMBAT"},
    {"cross_tstyle","Crosshair T","COMBAT"},
    {"cross_rainbow","Crosshair Rainbow","COMBAT"},
    -- VEHICLE RADAR
    {"skin_vehicle","Vehicle Skin","VEHICLE"},
    {"skin_parachute","Parachute Skin","VEHICLE"},
    -- SUPPLY & LOOT
    {"skin_weapon","Weapon Skin","LOOT"},
    {"skin_outfit","Outfit Skin","LOOT"},
    {"skin_emote","Emote Unlock","LOOT"},
    {"skin_deadbox","Deadbox Skin","LOOT"},
    {"skin_killmsg","Kill Message","LOOT"},
    -- SYSTEM & GRAPHICS
    {"wallhack","Wallhack","SYS"},
    {"enemy_counter","Enemy Counter","SYS"},
    {"fps165","165 FPS Unlock","SYS"},
}

function MENU.Init()
    if MENU.ready then return end
    MENU.ready = true
    pcall(function()
        local SPD = require("client.logic.NewSetting.SettingPageDefine")
        local SC  = require("client.logic.NewSetting.SettingCatalog")
        local AM  = require("client.slua.umg.NewSetting.Item.AliasMap")

        pcall(function()
            local Loc = require("client.common.LocUtil")
            if Loc and not Loc._ds_menu_hooked then
                Loc._ds_menu_hooked = true
                for _, fn in ipairs({"GetLocalizeResStr","GetText","GetTextByID","GetLocalText","GetLocalizeStr"}) do
                    if Loc[fn] then
                        local o = Loc[fn]
                        Loc[fn] = function(i)
                            if FAKE[i] then return FAKE[i] end
                            return o(i)
                        end
                    end
                end
            end
        end)

        local nextId = 990100
        for _, row in ipairs(CATALOG) do
            nextId = nextId + 1
            FAKE[nextId] = row[2]
            row._tid = nextId
        end

        local groups = { ESP={}, COMBAT={}, VEHICLE={}, LOOT={}, SYS={} }
        for _, row in ipairs(CATALOG) do
            table.insert(groups[row[3]], {
                Key = "DS_" .. row[1],
                UI = AM.Switcher,
                Text = row._tid,
                GetFunc = function() return _G.DS_Get(row[1]) end,
                SetFunc = function(_, v) _G.DS_Set(row[1], (v and v ~= 0) and 1 or 0) return true end,
            })
        end

        if SPD.DS_Menu then return end
        SPD.DS_Menu = {
            Key = "DS_Menu", Text = TID.title, UIKey = "Setting_Page_Privacy",
            Category = {
                { Key="DS_ESP",   Text=TID.esp,     UI=AM.TitleSwitcher, Stack=groups.ESP },
                { Key="DS_COMBAT",Text=TID.combat,  UI=AM.TitleSwitcher, Stack=groups.COMBAT },
                { Key="DS_VEH",   Text=TID.vehicle, UI=AM.TitleSwitcher, Stack=groups.VEHICLE },
                { Key="DS_LOOT",  Text=TID.loot,    UI=AM.TitleSwitcher, Stack=groups.LOOT },
                { Key="DS_SYS",   Text=TID.sys,     UI=AM.TitleSwitcher, Stack=groups.SYS },
            }
        }
        table.insert(SC, 1, SPD.DS_Menu)

        local UIMgr = _G.UIManager
        if UIMgr and not UIMgr._ds_menu_hooked then
            UIMgr._ds_menu_hooked = true
            local oShow = UIMgr.ShowUI
            UIMgr.ShowUI = function(cfg, ...)
                if cfg and cfg.keyName then
                    local lk = string.lower(cfg.keyName)
                    if string.find(lk, "setting_main") and not string.find(lk, "custom") then
                        local args = {...}
                        local cat = args[1]
                        if type(cat) == "table" and cat[1] and cat[1].Key then
                            local has = false
                            for _, p in ipairs(cat) do
                                if type(p) == "table" and p.Key == "DS_Menu" then has = true break end
                            end
                            if not has then table.insert(cat, 1, SPD.DS_Menu) end
                        end
                    end
                end
                return oShow(cfg, ...)
            end
        end
    end)
end
MENU.Init()
if _G.DS_SlowReg then _G.DS_SlowReg("ds_menu", MENU.Init) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ESP — FIXED VECTOR2D
# ═════════════════════════════════════════════════════════════════
ESP_HEADER = r"""
local ESP = _G.DS_ESP or {}
_G.DS_ESP = ESP

local V2 = import("Vector2D")
local FC = import("LinearColor")
local SC = import("SlateColor") or import("/Script/SlateCore.SlateColor")

local function GC()
    if ESP.canvas and Game:IsValid(ESP.canvas) then return ESP.canvas end
    local ok, U = pcall(require("GameLua.Mod.BaseMod.Common.UI.InGameUITools"))
    if not ok or not U then return nil end
    local b = U.GetMainControlBaseUI()
    if not b or not Game:IsValid(b) then return nil end
    ESP.canvas = b.CanvasPanel_0 or b.CanvasPanel_42
    return ESP.canvas
end

local function GPC()
    if _G.slua_GameFrontendHUD then
        local pc = _G.slua_GameFrontendHUD:GetPlayerController()
        if slua.isValid(pc) then return pc end
    end
    return nil
end

local function GL()
    local ok, GD = pcall(require("GameLua.GameCore.Data.GameplayData"))
    if ok and GD and GD.GetPlayerCharacter then
        local p = GD.GetPlayerCharacter()
        if slua.isValid(p) then return p end
    end
    return nil
end

local function PJ(PC, loc)
    local out = V2(0, 0)
    local ok = false
    pcall(function() ok = PC:ProjectWorldLocationToScreen(loc, out, true) end)
    if not ok or (out.X == 0 and out.Y == 0) then return false, 0, 0 end
    return true, out.X, out.Y
end

local function LoS(PC, t)
    local r = false
    pcall(function() r = PC:LineOfSightTo(t, import("Vector")(0,0,0), false) end)
    return r
end

local function PB(parent, color, z)
    local b = nil
    pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", parent) end)
    if not b or not slua.isValid(b) then return nil end
    pcall(function() b:SetBrushColor(color) end)
    pcall(function() b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
    local s = parent:AddChildToCanvas(b)
    if s then
        pcall(function() s:SetAutoSize(false) end)
        pcall(function() s:SetZOrder(z or 10) end)
    end
    return { w = b, s = s }
end

local function PT(parent, color, size, z)
    local t = nil
    pcall(function() t = CGame:NewObjectFromPath("/Script/UMG.TextBlock", parent) end)
    if not t or not slua.isValid(t) then return nil end
    if SC then pcall(function() t:SetColorAndOpacity(SC(color)) end) else pcall(function() t:SetColorAndOpacity(color) end) end
    pcall(function() if t.Font then local f = t.Font f.Size = size or 12 t.Font = f end end)
    pcall(function() t:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
    local s = parent:AddChildToCanvas(t)
    if s then
        pcall(function() s:SetAutoSize(true) end)
        pcall(function() s:SetZOrder(z or 20) end)
    end
    return { w = t, s = s }
end

-- Enemy iteration — works in training AND real matches
local function EE(cb)
    local lp = GL() if not slua.isValid(lp) then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local myTeam = nil
    pcall(function() myTeam = lp.TeamID end)
    local seen = {}
    local function process(p)
        if not slua.isValid(p) or p == lp then return end
        local key = tostring(p)
        if seen[key] then return end
        seen[key] = true
        local t = nil
        pcall(function() t = p.TeamID end)
        -- only filter team if BOTH teams are non-nil and different from 0
        if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then return end
        local hp = 0
        pcall(function() if p.Health then hp = p.Health end end)
        pcall(function() if hp == 0 and p.GetHealth then hp = p:GetHealth() or 0 end end)
        -- if can't read HP, assume alive
        if hp == 0 then hp = 100 end
        if hp > 0 then cb(p, lp, PC) end
    end
    pcall(function()
        for _, p in pairs(Game:GetAllPlayerPawns() or {}) do process(p) end
    end)
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        if GD and GD.GetAllPlayerCharacters then
            for _, p in pairs(GD.GetAllPlayerCharacters() or {}) do process(p) end
        end
    end)
end
"""


@feature("esp_box", "Box ESP")
def _f_esp_box(c):
    return {"lua": ESP_HEADER + r"""
local boxes = {}
function ESP.TickBox()
    if _G.DS_Get("esp_box") ~= 1 then
        for k, v in pairs(boxes) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            boxes[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    local seen = {}
    EE(function(e, lp, PC)
        local key = tostring(e) seen[key] = true
        local loc = e:K2_GetActorLocation() if not loc then return end
        local headZ = loc.Z + 90
        local feetZ = loc.Z - 90
        local headLoc = { X = loc.X, Y = loc.Y, Z = headZ }
        local feetLoc = { X = loc.X, Y = loc.Y, Z = feetZ }
        local ok1, x1, y1 = PJ(PC, headLoc)
        local ok2, x2, y2 = PJ(PC, feetLoc)
        if not ok1 or not ok2 then
            if boxes[key] and boxes[key].w then
                pcall(function() boxes[key].w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end)
            end
            return
        end
        local w = math.abs(x1 - x2)
        local h = math.abs(y1 - y2)
        if w < 20 then w = 40 end
        if h < 40 then h = 80 end
        local cx = (x1 + x2) / 2
        local cy = (y1 + y2) / 2
        if not boxes[key] or not boxes[key].w or not slua.isValid(boxes[key].w) then
            boxes[key] = PB(cv, FC(1, 0, 0, 0.9), 15)
        end
        local b = boxes[key]
        if b and b.s and slua.isValid(b.s) then
            pcall(function() b.s:SetPosition(V2(cx - w/2, cy - h/2)) end)
            pcall(function() b.s:SetSize(V2(w, h)) end)
            pcall(function() b.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_box", ESP.TickBox)
""".rstrip()}


@feature("esp_skeleton", "Skeleton ESP")
def _f_esp_skeleton(c):
    return {"lua": ESP_HEADER + r"""
local CHAINS = {
    {"head","neck_01","pelvis"},
    {"neck_01","upperarm_l","lowerarm_l","hand_l"},
    {"neck_01","upperarm_r","lowerarm_r","hand_r"},
    {"pelvis","thigh_l","calf_l","foot_l"},
    {"pelvis","thigh_r","calf_r","foot_r"},
}
local st = {}
function ESP.TickSkel()
    if _G.DS_Get("esp_skeleton") ~= 1 then
        for k, t in pairs(st) do
            for _, v in ipairs(t) do
                if v and v.w and slua.isValid(v.w) then
                    pcall(function() v.w:RemoveFromParent() end)
                    pcall(function() v.w:ConditionalBeginDestroy() end)
                end
            end
            st[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local mesh = e.Mesh if not slua.isValid(mesh) then return end
        st[key] = st[key] or {}
        local idx = 0
        local vis = LoS(PC, e)
        local col = vis and FC(0, 1, 0, 0.9) or FC(1, 0, 0, 0.7)
        for _, chain in ipairs(CHAINS) do
            local prev = nil
            for _, bone in ipairs(chain) do
                local bp = nil
                pcall(function() bp = mesh:GetSocketLocation(bone) end)
                if bp then
                    local ok, x, y = PJ(PC, bp)
                    if ok and prev then
                        idx = idx + 1
                        if not st[key][idx] or not st[key][idx].w or not slua.isValid(st[key][idx].w) then
                            st[key][idx] = PB(cv, col, 5)
                        end
                        local w = st[key][idx]
                        local dx, dy = x - prev.x, y - prev.y
                        local len = math.sqrt(dx*dx + dy*dy)
                        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
                        if w and w.s and slua.isValid(w.s) then
                            pcall(function() w.w:SetBrushColor(col) end)
                            pcall(function() w.s:SetPosition(V2(prev.x, prev.y - 0.4)) end)
                            pcall(function() w.s:SetSize(V2(len, 0.8)) end)
                            pcall(function() w.w:SetRenderAngle(ang) end)
                            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
                        end
                    end
                    if ok then prev = {x = x, y = y} end
                end
            end
        end
        for i = idx + 1, #st[key] do
            if st[key][i] and st[key][i].w and slua.isValid(st[key][i].w) then
                pcall(function() st[key][i].w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end)
            end
        end
    end)
end
_G.DS_Reg("esp_skeleton", ESP.TickSkel)
""".rstrip()}


@feature("esp_line", "Snap Line ESP")
def _f_esp_line(c):
    return {"lua": ESP_HEADER + r"""
local L = {}
function ESP.TickLine()
    if _G.DS_Get("esp_line") ~= 1 then
        for k, v in pairs(L) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            L[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    local sx, sy = 960, 60
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local headLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 90 }
        local ok, x, y = PJ(PC, headLoc) if not ok then return end
        if not L[key] or not L[key].w or not slua.isValid(L[key].w) then
            L[key] = PB(cv, FC(1, 1, 0, 0.75), 1)
        end
        local w = L[key]
        local dx, dy = x - sx, y - sy
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local vis = LoS(PC, e)
        if w and w.s and slua.isValid(w.s) then
            pcall(function() w.w:SetBrushColor(vis and FC(0, 1, 0, 0.75) or FC(1, 0, 0, 0.75)) end)
            pcall(function() w.s:SetPosition(V2(sx, sy)) end)
            pcall(function() w.s:SetSize(V2(len, 1.5)) end)
            pcall(function() w.w:SetRenderAngle(ang) end)
            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_line", ESP.TickLine)
""".rstrip()}


@feature("esp_distance", "Distance ESP")
def _f_esp_distance(c):
    return {"lua": ESP_HEADER + r"""
local D = {}
function ESP.TickDist()
    if _G.DS_Get("esp_distance") ~= 1 then
        for k, v in pairs(D) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            D[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local hLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 130 }
        local ok, x, y = PJ(PC, hLoc) if not ok then return end
        local m = math.floor(lp:GetDistanceTo(e) / 100)
        if not D[key] or not D[key].w or not slua.isValid(D[key].w) then
            D[key] = PT(cv, FC(0, 1, 1, 1), 14, 30)
        end
        local w = D[key]
        if w and w.w and slua.isValid(w.w) then
            pcall(function() w.w:SetText(m .. "m") end)
            pcall(function() w.s:SetPosition(V2(x, y)) end)
            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_distance", ESP.TickDist)
""".rstrip()}


@feature("esp_name", "Name ESP")
def _f_esp_name(c):
    return {"lua": ESP_HEADER + r"""
local N = {}
function ESP.TickName()
    if _G.DS_Get("esp_name") ~= 1 then
        for k, v in pairs(N) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            N[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local hLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 150 }
        local ok, x, y = PJ(PC, hLoc) if not ok then return end
        local nm = "Unknown"
        pcall(function() nm = e:GetPlayerNameSafety() or "Unknown" end)
        if not N[key] or not N[key].w or not slua.isValid(N[key].w) then
            N[key] = PT(cv, FC(1, 1, 0, 1), 12, 28)
        end
        local w = N[key]
        if w and w.w and slua.isValid(w.w) then
            pcall(function() w.w:SetText(nm) end)
            pcall(function() w.s:SetPosition(V2(x, y)) end)
            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_name", ESP.TickName)
""".rstrip()}


@feature("esp_hp", "HP Bar ESP")
def _f_esp_hp(c):
    return {"lua": ESP_HEADER + r"""
local HP = {}
function ESP.TickHP()
    if _G.DS_Get("esp_hp") ~= 1 then
        for k, v in pairs(HP) do
            if v and v.bg and v.bg.w and slua.isValid(v.bg.w) then
                pcall(function() v.bg.w:RemoveFromParent() end)
                pcall(function() v.bg.w:ConditionalBeginDestroy() end)
            end
            if v and v.fg and v.fg.w and slua.isValid(v.fg.w) then
                pcall(function() v.fg.w:RemoveFromParent() end)
                pcall(function() v.fg.w:ConditionalBeginDestroy() end)
            end
            HP[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local hLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 105 }
        local ok, x, y = PJ(PC, hLoc) if not ok then return end
        local hp, mx = 100, 100
        pcall(function() hp = e.Health or 100 mx = e.HealthMax or 100 end)
        if mx <= 0 then mx = 100 end
        local pct = hp / mx
        if pct > 1 then pct = 1 end
        if pct < 0 then pct = 0 end
        local col = pct > 0.5 and FC(0, 1, 0, 0.9) or (pct > 0.25 and FC(1, 0.5, 0, 0.9) or FC(1, 0, 0, 0.9))
        if not HP[key] or not HP[key].bg or not slua.isValid(HP[key].bg.w) then
            HP[key] = { bg = PB(cv, FC(0, 0, 0, 0.7), 40), fg = PB(cv, col, 41) }
        end
        local h = HP[key]
        if h.bg and h.bg.s and slua.isValid(h.bg.s) then
            pcall(function() h.bg.s:SetPosition(V2(x - 30, y)) end)
            pcall(function() h.bg.s:SetSize(V2(60, 5)) end)
            pcall(function() h.bg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
        if h.fg and h.fg.s and slua.isValid(h.fg.s) then
            pcall(function() h.fg.w:SetBrushColor(col) end)
            pcall(function() h.fg.s:SetPosition(V2(x - 30, y)) end)
            pcall(function() h.fg.s:SetSize(V2(60 * pct, 5)) end)
            pcall(function() h.fg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_hp", ESP.TickHP)
""".rstrip()}


@feature("esp_weapon", "Weapon Icon ESP")
def _f_esp_weapon(c):
    return {"lua": ESP_HEADER + r"""
local W = {}
function ESP.TickWep()
    if _G.DS_Get("esp_weapon") ~= 1 then
        for k, v in pairs(W) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            W[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local hLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 175 }
        local ok, x, y = PJ(PC, hLoc) if not ok then return end
        local wn = "Fist"
        pcall(function()
            local w = e.CurrentWeapon or (e.GetCurrentWeapon and e:GetCurrentWeapon())
            if slua.isValid(w) and w.GetWeaponName then wn = w:GetWeaponName() end
        end)
        if not W[key] or not W[key].w or not slua.isValid(W[key].w) then
            W[key] = PT(cv, FC(1, 0.8, 0.2, 1), 11, 26)
        end
        local w = W[key]
        if w and w.w and slua.isValid(w.w) then
            pcall(function() w.w:SetText(wn) end)
            pcall(function() w.s:SetPosition(V2(x, y)) end)
            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_weapon", ESP.TickWep)
""".rstrip()}


@feature("esp_vis", "Visibility Color ESP")
def _f_esp_vis(c):
    return {"lua": ESP_HEADER + r"""
local V = {}
function ESP.TickVis()
    if _G.DS_Get("esp_vis") ~= 1 then
        for k, v in pairs(V) do
            if v and v.w and slua.isValid(v.w) then
                pcall(function() v.w:RemoveFromParent() end)
                pcall(function() v.w:ConditionalBeginDestroy() end)
            end
            V[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        local hLoc = { X = loc.X, Y = loc.Y, Z = loc.Z + 90 }
        local ok, x, y = PJ(PC, hLoc) if not ok then return end
        local vis = LoS(PC, e)
        if not V[key] or not V[key].w or not slua.isValid(V[key].w) then
            V[key] = PB(cv, FC(1, 0, 0, 0.85), 14)
        end
        local w = V[key]
        if w and w.s and slua.isValid(w.s) then
            pcall(function() w.w:SetBrushColor(vis and FC(0, 1, 0, 0.9) or FC(1, 0, 0, 0.9)) end)
            pcall(function() w.s:SetPosition(V2(x - 15, y - 15)) end)
            pcall(function() w.s:SetSize(V2(30, 30)) end)
            pcall(function() w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
        end
    end)
end
_G.DS_Reg("esp_vis", ESP.TickVis)
""".rstrip()}


@feature("esp_radar", "Radar ESP")
def _f_esp_radar(c):
    return {"lua": r"""
local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)
pcall(function()
    local t = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
    local c = t.GetCurrentConfig("ScreenMarkConfig")
    if c then
        c[9999] = {
            UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
            MaxWidgetNum = 99, MaxShowDistance = 6000000,
            bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
            BindSocketName = "head", bUseLuaWorldSocketName = true,
            WorldPositionOffset = FVector(0, 0, 50), bNeedPreLoad = true, Priority = 2,
        }
    end
end)
local function tick()
    if _G.DS_Get("esp_radar") ~= 1 or not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID
    for _, e in pairs(GDP.GetAllPlayerCharacters and GDP.GetAllPlayerCharacters() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local dead = false
                pcall(function() if type(e.IsDead) == "function" then dead = e:IsDead() end if e.bHidden then dead = true end end)
                if not dead and not e.DS_Radar then
                    pcall(function() e.DS_Radar = IMT.ClientAddMapMark(9999, FVector(0,0,0), 0, "", 4, e) end)
                elseif dead and e.DS_Radar then
                    pcall(function() IMT.ClientRemoveMapMark(e.DS_Radar) end)
                    e.DS_Radar = nil
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_radar", tick)
""".rstrip()}


@feature("esp_fov_circle", "FOV Circle")
def _f_esp_fov_circle(c):
    return {"lua": r"""
local F = { c = nil, lines = {}, N = 40 }
function F.Create()
    if F.c and slua.isValid(F.c) then return true end
    local cv = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U.GetMainControlBaseUI()
        if slua.isValid(b) then cv = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    if not cv then return false end
    local p = nil
    pcall(function() p = CGame:NewObjectFromPath("/Script/UMG.CanvasPanel", cv) end)
    if not p then return false end
    local V2 = import("Vector2D")
    for i = 1, F.N do
        local b = nil
        pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", p) end)
        if b then
            b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
            b:SetRenderTransformPivot(V2(0, 0.5))
            local s = p:AddChildToCanvas(b)
            if s then s:SetAlignment(V2(0, 0.5)) end
            F.lines[i] = { w = b, s = s }
        end
    end
    local s = cv:AddChildToCanvas(p)
    if s then
        s:SetSize(V2(0, 0))
        s:SetPosition(V2(0, 0))
        s:SetZOrder(995)
    end
    F.c = p
    return true
end
function F.Tick()
    if _G.DS_Get("esp_fov_circle") ~= 1 then
        if F.c and slua.isValid(F.c) then F.c:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end
        return
    end
    if not F.Create() then return end
    F.c:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local R = 120
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local col = FC(1, 1, 1, 0.55)
    for i = 1, F.N do
        local a1 = (i-1) * 2 * math.pi / F.N
        local a2 = i * 2 * math.pi / F.N
        local x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        local x2, y2 = cx + R * math.cos(a2), cy + R * math.sin(a2)
        local dx, dy = x2 - x1, y2 - y1
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local l = F.lines[i]
        if l and l.s then
            pcall(function() l.s:SetPosition(V2(x1, y1)) end)
            pcall(function() l.s:SetSize(V2(len + 0.8, 1.5)) end)
            pcall(function() l.w:SetRenderAngle(ang) end)
            pcall(function() l.w:SetBrushColor(col) end)
        end
    end
end
_G.DS_Reg("esp_fov", F.Tick)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# AIMBOT
# ═════════════════════════════════════════════════════════════════
AIM_HEADER = r"""
local AIM = _G.DS_AIM or {}
_G.DS_AIM = AIM
local function GC()
    local ok, GD = pcall(require("GameLua.GameCore.Data.GameplayData"))
    if ok and GD and GD.GetPlayerCharacter then
        local p = GD.GetPlayerCharacter()
        if slua.isValid(p) then return p end
    end
    return nil
end
local function GPC()
    if _G.slua_GameFrontendHUD then
        local pc = _G.slua_GameFrontendHUD:GetPlayerController()
        if slua.isValid(pc) then return pc end
    end
    return nil
end
local function GEB(e, n)
    local b = nil
    pcall(function() if e.GetBonePos then b = e:GetBonePos(n, {X=0,Y=0,Z=0}) end end)
    if not b then
        pcall(function() if e.Mesh and e.Mesh.GetSocketLocation then b = e.Mesh:GetSocketLocation(n) end end)
    end
    return b
end
local function ENEMIES()
    local out = {}
    local me = GC() if not slua.isValid(me) then return out end
    local mt = nil pcall(function() mt = me.TeamID end)
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me then
            local t = nil pcall(function() t = p.TeamID end)
            local skip = false
            if mt and mt ~= 0 and t and t ~= 0 and t == mt then skip = true end
            if not skip then
                local hp = 100 pcall(function() if p.Health then hp = p.Health end end)
                if hp > 0 then out[#out+1] = p end
            end
        end
    end
    return out
end
local function SCREEN_PICK(PC, bone, maxR)
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return nil end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    maxR = maxR or 200
    local best, bestD, bestBone = nil, 99999, nil
    for _, e in ipairs(ENEMIES()) do
        local b = GEB(e, bone)
        if b then
            local V2 = import("Vector2D")
            local out = V2(0, 0)
            if PC:ProjectWorldLocationToScreen(b, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < maxR and d < bestD then
                    bestD = d best = e bestBone = b
                end
            end
        end
    end
    return best, bestBone
end
local function SMOOTH_SET(PC, target, pct)
    if not target then return end
    local cur = PC:GetControlRotation()
    if not cur then return end
    local dy = target.Yaw - cur.Yaw
    if dy > 180 then dy = dy - 360 end
    if dy < -180 then dy = dy + 360 end
    local dp = target.Pitch - cur.Pitch
    pct = pct or 0.4
    local nY = cur.Yaw + dy * pct
    local nP = cur.Pitch + dp * pct
    PC:SetControlRotation({ Pitch = nP, Yaw = nY, Roll = cur.Roll }, "DS_Aim")
end
"""


@feature("aim_silent", "Silent Aim")
def _f_aim_silent(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickSilent()
    if _G.DS_Get("aim_silent") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local now = os.clock()
    if now - CD < 0.08 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 250)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.35)
    CD = now
end
_G.DS_Reg("aim_silent", AIM.TickSilent)
""".rstrip()}


@feature("aim_smooth", "Smooth Aim")
def _f_aim_smooth(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickSmooth()
    if _G.DS_Get("aim_smooth") ~= 1 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local now = os.clock()
    if now - CD < 0.05 then return end
    local tgt, bone = SCREEN_PICK(PC, "spine_03", 260)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.30)
    CD = now
end
_G.DS_Reg("aim_smooth", AIM.TickSmooth)
""".rstrip()}


@feature("aim_bone", "Bone Lock Aimbot")
def _f_aim_bone(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickBone()
    if _G.DS_Get("aim_bone") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local now = os.clock()
    if now - CD < 0.08 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 180)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.42)
    CD = now
end
_G.DS_Reg("aim_bone", AIM.TickBone)
""".rstrip()}


@feature("aim_pred", "Prediction Aim")
def _f_aim_pred(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickPred()
    if _G.DS_Get("aim_pred") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local now = os.clock()
    if now - CD < 0.08 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 300)
    if not tgt or not bone then return end
    local vel = nil
    pcall(function() if tgt.GetVelocity then vel = tgt:GetVelocity() end end)
    if vel then
        local dist = me:GetDistanceTo(tgt) / 100
        local tof = dist / 800 * 0.5
        bone.X = bone.X + vel.X * tof
        bone.Y = bone.Y + vel.Y * tof
    end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.40)
    CD = now
end
_G.DS_Reg("aim_pred", AIM.TickPred)
""".rstrip()}


@feature("aim_recoil", "Recoil Compensation")
def _f_aim_recoil(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickRecoil()
    if _G.DS_Get("aim_recoil") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local now = os.clock()
    if now - CD < 0.05 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local cur = PC:GetControlRotation()
    if not cur then return end
    cur.Pitch = cur.Pitch - 0.6
    PC:SetControlRotation(cur, "DS_Recoil")
    CD = now
end
_G.DS_Reg("aim_recoil", AIM.TickRecoil)
""".rstrip()}


@feature("aim_autofire", "Auto Fire")
def _f_aim_autofire(c):
    return {"lua": AIM_HEADER + r"""
function AIM.TickAutoFire()
    if _G.DS_Get("aim_autofire") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local fire = false
    for _, e in ipairs(ENEMIES()) do
        local b = GEB(e, "head") or GEB(e, "spine_03")
        if b then
            local V2 = import("Vector2D")
            local out = V2(0, 0)
            if PC:ProjectWorldLocationToScreen(b, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < 55 then fire = true break end
            end
        end
    end
    if fire then
        pcall(function()
            me.bIsWeaponFiring = true
            if me.SetIsWeaponFiring then me:SetIsWeaponFiring(true) end
            if PC.SetIsWeaponFiring then PC:SetIsWeaponFiring(true) end
        end)
    end
end
_G.DS_Reg("aim_autofire", AIM.TickAutoFire)
""".rstrip()}


@feature("aim_shotgun", "Shotgun Auto Aim")
def _f_aim_shotgun(c):
    return {"lua": AIM_HEADER + r"""
function AIM.TickSG()
    if _G.DS_Get("aim_shotgun") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    local w = me.CurrentWeapon or (me.GetCurrentWeapon and me:GetCurrentWeapon())
    if not slua.isValid(w) then return end
    local nm = ""
    pcall(function() nm = (w.GetWeaponName and w:GetWeaponName()) or "" end)
    if not (nm:find("S686") or nm:find("S1897") or nm:find("S12") or nm:find("DBS") or nm:find("M1014")) then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    for _, e in ipairs(ENEMIES()) do
        local b = GEB(e, "head") or GEB(e, "spine_03")
        if b then
            local V2 = import("Vector2D")
            local out = V2(0, 0)
            if PC:ProjectWorldLocationToScreen(b, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < 50 and me:GetDistanceTo(e) < 2500 then
                    pcall(function()
                        me.bIsWeaponFiring = true
                        if w.StartFire then w:StartFire() end
                    end)
                end
            end
        end
    end
end
_G.DS_Reg("aim_shotgun", AIM.TickSG)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# MAGIC BULLET
# ═════════════════════════════════════════════════════════════════
MAGIC_HEADER = r"""
local MB = _G.DS_MB or {}
_G.DS_MB = MB
MB.hooked = false
if not MB.hooked then
    MB.hooked = true
    pcall(function()
        local E = import("EAvatarDamagePosition")
        if not E then return end
        for _, path in ipairs({
            "GameLua.Mod.BaseMod.Common.Weapon.ShootWeaponEntity",
            "GameLua.Logic.Weapon.ShootWeaponEntity"
        }) do
            local m = package.loaded[path]
            if m then
                local o1 = m.GetHitBodyType
                m.GetHitBodyType = function(self, imp, vec)
                    if MB.force then return MB.force() end
                    return o1 and o1(self, imp, vec)
                end
                local o2 = m.GetHitBodyTypeByHitPos
                m.GetHitBodyTypeByHitPos = function(self, vec)
                    if MB.force then return MB.force() end
                    return o2 and o2(self, vec)
                end
            end
        end
    end)
end
"""


@feature("magic_full", "Magic Full Body")
def _f_magic_full(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickFull()
    if _G.DS_Get("magic_full") ~= 1 then return end
    local E = import("EAvatarDamagePosition")
    MB.force = function() return E and E.BigHead or nil end
end
_G.DS_Reg("magic_full", MB.TickFull)
""".rstrip()}


@feature("magic_head", "Magic Head")
def _f_magic_head(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickHead()
    if _G.DS_Get("magic_head") ~= 1 then return end
    local E = import("EAvatarDamagePosition")
    MB.force = function() return E and E.BigHead or nil end
end
_G.DS_Reg("magic_head", MB.TickHead)
""".rstrip()}


@feature("magic_neck", "Magic Neck")
def _f_magic_neck(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickNeck()
    if _G.DS_Get("magic_neck") ~= 1 then return end
    MB.force = function() return "neck" end
end
_G.DS_Reg("magic_neck", MB.TickNeck)
""".rstrip()}


@feature("magic_body", "Magic Body")
def _f_magic_body(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickBody()
    if _G.DS_Get("magic_body") ~= 1 then return end
    MB.force = function() return "spine_02" end
end
_G.DS_Reg("magic_body", MB.TickBody)
""".rstrip()}


@feature("magic_legs", "Magic Legs")
def _f_magic_legs(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickLegs()
    if _G.DS_Get("magic_legs") ~= 1 then return end
    MB.force = function() return "calf_l" end
end
_G.DS_Reg("magic_legs", MB.TickLegs)
""".rstrip()}


@feature("magic_custom", "Magic Custom Ratio")
def _f_magic_custom(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickCustom()
    if _G.DS_Get("magic_custom") ~= 1 then return end
    MB.force = function()
        if math.random() < 0.6 then
            local E = import("EAvatarDamagePosition")
            return E and E.BigHead or nil
        end
        return nil
    end
end
_G.DS_Reg("magic_custom", MB.TickCustom)
""".rstrip()}


@feature("magic_hitbox", "Magic Hitbox")
def _f_magic_hitbox(c):
    return {"lua": r"""
-- visual neutral. hitbox advantage via magic_head/body only.
""".rstrip()}


@feature("magic_safe", "Safe 60% Magic")
def _f_magic_safe(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickSafe()
    if _G.DS_Get("magic_safe") ~= 1 then return end
    MB.force = function()
        local r = math.random()
        if r < 0.40 then
            local E = import("EAvatarDamagePosition")
            return E and E.BigHead or nil
        elseif r < 0.80 then
            return "spine_03"
        end
        return nil
    end
end
_G.DS_Reg("magic_safe", MB.TickSafe)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# CROSSHAIR — FIXED VECTOR2D
# ═════════════════════════════════════════════════════════════════
CROSS_HEADER = r"""
local CH = _G.DS_CH or {}
_G.DS_CH = CH
local V2 = import("Vector2D")
local FC = import("LinearColor")

local function CV()
    local c = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U.GetMainControlBaseUI()
        if slua.isValid(b) then c = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    return c
end
local function BB(parent, color)
    local b = nil
    pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", parent) end)
    if not b or not slua.isValid(b) then return nil end
    pcall(function() b:SetBrushColor(color) end)
    pcall(function() b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) end)
    local s = parent:AddChildToCanvas(b)
    if s then pcall(function() s:SetZOrder(40) end) end
    return { w = b, s = s }
end
local function CLEAR(bucket)
    if not bucket then return end
    for _, v in pairs(bucket) do
        if v and v.w and slua.isValid(v.w) then
            pcall(function() v.w:RemoveFromParent() end)
            pcall(function() v.w:ConditionalBeginDestroy() end)
        end
    end
end
"""


@feature("cross_cross", "Crosshair — Cross")
def _f_cross_cross(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickCross()
    local cv = CV()
    if _G.DS_Get("cross_cross") ~= 1 then CLEAR(CH.cross) CH.cross = nil return end
    if not cv then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.cross then
        CH.cross = { h = BB(cv, FC(1, 0, 0, 1)), v = BB(cv, FC(1, 0, 0, 1)) }
    end
    if CH.cross.h and CH.cross.h.s then
        pcall(function() CH.cross.h.s:SetPosition(V2(cx-10, cy-1)) end)
        pcall(function() CH.cross.h.s:SetSize(V2(20, 2)) end)
    end
    if CH.cross.v and CH.cross.v.s then
        pcall(function() CH.cross.v.s:SetPosition(V2(cx-1, cy-10)) end)
        pcall(function() CH.cross.v.s:SetSize(V2(2, 20)) end)
    end
end
_G.DS_Reg("cross_cross", CH.TickCross)
""".rstrip()}


@feature("cross_dot", "Crosshair — Dot")
def _f_cross_dot(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickDot()
    local cv = CV()
    if _G.DS_Get("cross_dot") ~= 1 then
        if CH.dot and CH.dot.w and slua.isValid(CH.dot.w) then
            pcall(function() CH.dot.w:RemoveFromParent() end)
            CH.dot = nil
        end
        return
    end
    if not cv then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.dot then CH.dot = BB(cv, FC(0, 1, 0, 1)) end
    if CH.dot and CH.dot.s then
        pcall(function() CH.dot.s:SetPosition(V2(cx-3, cy-3)) end)
        pcall(function() CH.dot.s:SetSize(V2(6, 6)) end)
    end
end
_G.DS_Reg("cross_dot", CH.TickDot)
""".rstrip()}


@feature("cross_circle", "Crosshair — Circle")
def _f_cross_circle(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickCircle()
    local cv = CV()
    if _G.DS_Get("cross_circle") ~= 1 then CLEAR(CH.circle) CH.circle = nil return end
    if not cv then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    local R, N = 12, 20
    if not CH.circle then
        CH.circle = {}
        for i = 1, N do
            CH.circle[i] = BB(cv, FC(0, 1, 1, 1))
            pcall(function() CH.circle[i].w:SetRenderTransformPivot(V2(0, 0.5)) end)
        end
    end
    for i = 1, N do
        local a1 = (i-1)*2*math.pi/N
        local a2 = i*2*math.pi/N
        local x1, y1 = cx+R*math.cos(a1), cy+R*math.sin(a1)
        local x2, y2 = cx+R*math.cos(a2), cy+R*math.sin(a2)
        local dx, dy = x2-x1, y2-y1
        local len = math.sqrt(dx*dx+dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy,dx) or math.atan(dy,dx))
        local l = CH.circle[i]
        if l and l.s then
            pcall(function() l.s:SetPosition(V2(x1, y1)) end)
            pcall(function() l.s:SetSize(V2(len+0.5, 1)) end)
            pcall(function() l.w:SetRenderAngle(ang) end)
        end
    end
end
_G.DS_Reg("cross_circle", CH.TickCircle)
""".rstrip()}


@feature("cross_tstyle", "Crosshair — T-Style")
def _f_cross_tstyle(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickT()
    local cv = CV()
    if _G.DS_Get("cross_tstyle") ~= 1 then CLEAR(CH.ts) CH.ts = nil return end
    if not cv then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.ts then
        CH.ts = { top = BB(cv, FC(1, 1, 0, 1)), left = BB(cv, FC(1, 1, 0, 1)), right = BB(cv, FC(1, 1, 0, 1)) }
    end
    if CH.ts.top and CH.ts.top.s then
        pcall(function() CH.ts.top.s:SetPosition(V2(cx-1, cy-12)) end)
        pcall(function() CH.ts.top.s:SetSize(V2(2, 10)) end)
    end
    if CH.ts.left and CH.ts.left.s then
        pcall(function() CH.ts.left.s:SetPosition(V2(cx-12, cy-1)) end)
        pcall(function() CH.ts.left.s:SetSize(V2(10, 2)) end)
    end
    if CH.ts.right and CH.ts.right.s then
        pcall(function() CH.ts.right.s:SetPosition(V2(cx+2, cy-1)) end)
        pcall(function() CH.ts.right.s:SetSize(V2(10, 2)) end)
    end
end
_G.DS_Reg("cross_tstyle", CH.TickT)
""".rstrip()}


@feature("cross_rainbow", "Crosshair — Rainbow")
def _f_cross_rainbow(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickRB()
    local cv = CV()
    if _G.DS_Get("cross_rainbow") ~= 1 then CLEAR(CH.rb) CH.rb = nil return end
    if not cv then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    local t = os.clock() * 2
    local r, g, b = (math.sin(t)+1)/2, (math.sin(t+2)+1)/2, (math.sin(t+4)+1)/2
    local col = FC(r, g, b, 1)
    if not CH.rb then CH.rb = { h = BB(cv, col), v = BB(cv, col) } end
    if CH.rb.h and CH.rb.h.w then pcall(function() CH.rb.h.w:SetBrushColor(col) end) end
    if CH.rb.v and CH.rb.v.w then pcall(function() CH.rb.v.w:SetBrushColor(col) end) end
    if CH.rb.h and CH.rb.h.s then
        pcall(function() CH.rb.h.s:SetPosition(V2(cx-10, cy-1)) end)
        pcall(function() CH.rb.h.s:SetSize(V2(20, 2)) end)
    end
    if CH.rb.v and CH.rb.v.s then
        pcall(function() CH.rb.v.s:SetPosition(V2(cx-1, cy-10)) end)
        pcall(function() CH.rb.v.s:SetSize(V2(2, 20)) end)
    end
end
_G.DS_Reg("cross_rb", CH.TickRB)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# SKIN / WALLHACK / COUNTER / FPS
# ═════════════════════════════════════════════════════════════════
@feature("skin_weapon", "Weapon Skin")
def _f_skin_weapon(c):
    return {"lua": r"""
local SK = { _cd = 0 }
local MAP = { [101001]=1101001174, [101004]=1101004163, [101003]=1101003146, [101008]=1101008081 }
function SK.Tick()
    if _G.DS_Get("skin_weapon") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 1.5 then return end
    SK._cd = now
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local wm = me.WeaponManagerComponent
    if not slua.isValid(wm) then return end
    local w = wm.CurrentWeaponReplicated
    if not slua.isValid(w) then return end
    local wid = 0 pcall(function() wid = w:GetWeaponID() end)
    local skin = MAP[wid]
    if not skin then return end
    pcall(function()
        local wac = w.WeaponAvatarComponent
        if slua.isValid(wac) then
            if wac.ChangeWeaponAvatar then wac:ChangeWeaponAvatar(skin, false) end
            if wac.ReloadAllEquippedAvatar then wac:ReloadAllEquippedAvatar(1) end
        end
    end)
end
_G.DS_SlowReg("skin_weapon", SK.Tick)
""".rstrip()}


@feature("skin_outfit", "Outfit Skin")
def _f_skin_outfit(c):
    return {"lua": r"""
local SK = { _cd = 0, ID = 1407870 }
function SK.Tick()
    if _G.DS_Get("skin_outfit") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.0 then return end
    SK._cd = now
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    pcall(function() comp:PutOnCustomEquipmentByID(SK.ID) end)
end
_G.DS_SlowReg("skin_outfit", SK.Tick)
""".rstrip()}


@feature("skin_vehicle", "Vehicle Skin")
def _f_skin_vehicle(c):
    return {"lua": r"""
local SK = { _cd = 0, ID = 1961010 }
function SK.Tick()
    if _G.DS_Get("skin_vehicle") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.0 then return end
    SK._cd = now
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local v = me.CurrentVehicle
    if not slua.isValid(v) then return end
    local av = v.VehicleAvatarComponent_BP
    if not slua.isValid(av) then return end
    pcall(function() av:ChangeItemAvatar(SK.ID, false) end)
end
_G.DS_SlowReg("skin_vehicle", SK.Tick)
""".rstrip()}


@feature("skin_parachute", "Parachute Skin")
def _f_skin_parachute(c):
    return {"lua": r"""
local SK = { _cd = 0, ID = 1401000 }
function SK.Tick()
    if _G.DS_Get("skin_parachute") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.5 then return end
    SK._cd = now
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    pcall(function() comp:PutOnCustomEquipmentByID(SK.ID) end)
end
_G.DS_SlowReg("skin_parachute", SK.Tick)
""".rstrip()}


@feature("skin_emote", "Emote Unlock")
def _f_skin_emote(c):
    return {"lua": r"""
pcall(function()
    local le = require("GameLua.Mod.Library.GamePlay.Avatar.Emote.logic_emote")
    if le and le.IsEmoteExist and not le._ds_emote_hook then
        le._ds_emote_hook = true
        local o = le.IsEmoteExist
        le.IsEmoteExist = function(id)
            if _G.DS_Get("skin_emote") == 1 then return true end
            return o(id)
        end
    end
end)
""".rstrip()}


@feature("skin_deadbox", "Deadbox Skin")
def _f_skin_deadbox(c):
    return {"lua": r"""
_G.DS_SKIN = _G.DS_SKIN or {}
function _G.DS_DeadboxTick()
    if _G.DS_Get("skin_deadbox") ~= 1 then return end
    pcall(function()
        local me = nil
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
        if not slua.isValid(me) then return end
        local w = me:GetCurrentWeapon()
        if not slua.isValid(w) then return end
        local wac = w.WeaponAvatarComponent
        if slua.isValid(wac) then _G.DS_SKIN.last = wac.CachedLoadedID or 0 end
    end)
end
_G.DS_SlowReg("skin_deadbox", _G.DS_DeadboxTick)
""".rstrip()}


@feature("skin_killmsg", "Kill Message")
def _f_skin_killmsg(c):
    return {"lua": r"""
pcall(function()
    local SKI = require("GameLua.Mod.BaseMod.Client.KillInfoTips.KillInfo")
    if SKI and SKI.__inner_impl and SKI.__inner_impl.FileItem and not SKI.__inner_impl._ds_km_hook then
        SKI.__inner_impl._ds_km_hook = true
        local o = SKI.__inner_impl.FileItem
        SKI.__inner_impl.FileItem = function(self, data)
            if _G.DS_Get("skin_killmsg") == 1 and data then
                local skin = _G.DS_SKIN and _G.DS_SKIN.last or 0
                if skin > 1000000 then
                    pcall(function()
                        local exp = slua.LuaArchiverDecode(LuaStateWrapper, data.ExpandDataContent) or {}
                        exp.CauserWeaponAvatarID = skin
                        data.ExpandDataContent = slua.LuaArchiverEncode(LuaStateWrapper, exp)
                        data.bShowBottomBothSidesKillInfo = true
                    end)
                end
            end
            return o(self, data)
        end
    end
end)
""".rstrip()}


@feature("wallhack", "Wallhack")
def _f_wallhack(c):
    return {"lua": r"""
local WH = { ready = false, colors = {
    vis = import("LinearColor")(255, 255, 0, 100),
    occ = import("LinearColor")(0, 255, 255, 100),
}, slots = {0,1,2,3,4,5,6,7} }
function WH.Setup()
    if WH.ready then return end
    pcall(function()
        local K = import("KismetSystemLibrary")
        local w = slua.getWorld()
        if not K or not w then return end
        K.ExecuteConsoleCommand(w, "r.EnableDrawDyeingColor 1")
        K.ExecuteConsoleCommand(w, "r.CustomDepth 3")
        K.ExecuteConsoleCommand(w, "r.IdeaOutline.Enable 1")
        K.ExecuteConsoleCommand(w, "r.Highlight.Enable 1")
        WH.ready = true
    end)
end
local function apply(mesh, vis, occ)
    if not mesh or not slua.isValid(mesh) then return end
    pcall(function()
        mesh:SetDrawDyeing(true) mesh:SetDrawDyeingMode(1)
        mesh:SetVisibleDyeingColor(vis) mesh:SetOccludedDyeingColor(occ)
        mesh:SetDyeingColorFadeDistance(99999.0) mesh:SetDyeingColorMinMaxDistance(0.0, 99999.0)
        mesh:SetDrawHighlight(true) mesh:OverrideHighlightColor(vis)
        mesh:SetDrawIdeaOutline(true) mesh:SetIdeaOutlineNew(true)
        mesh:OverrideIdeaOutlineColor(vis) mesh:SetIdeaOutlineOcclusionColor(occ)
        mesh:SetRenderCustomDepth(true) mesh:SetCustomDepthStencilValue(255)
    end)
end
function WH.Tick()
    if _G.DS_Get("wallhack") ~= 1 then return end
    WH.Setup()
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local myTeam = nil pcall(function() myTeam = me.TeamID end)
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and (p.Health or 100) > 0 then
            local t = nil pcall(function() t = p.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                if slua.isValid(p.Mesh) then apply(p.Mesh, WH.colors.vis, WH.colors.occ) end
            end
        end
    end
end
_G.DS_Reg("wallhack", WH.Tick)
""".rstrip()}


@feature("enemy_counter", "Enemy Counter")
def _f_enemy_counter(c):
    return {"lua": r"""
function _G.DS_CounterTick()
    if _G.DS_Get("enemy_counter") ~= 1 then return end
    local me = nil
    pcall(function() local GD = require("GameLua.GameCore.Data.GameplayData") me = GD.GetPlayerCharacter() end)
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID
    local myPos = me:K2_GetActorLocation()
    if not myPos then return end
    local total, bots, real = 0, 0, 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me then
            local t = nil pcall(function() t = p.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local pos = p:K2_GetActorLocation()
                if pos then
                    local dx, dy, dz = pos.X-myPos.X, pos.Y-myPos.Y, pos.Z-myPos.Z
                    if dx*dx + dy*dy + dz*dz <= 900000000 then
                        total = total + 1
                        local b = false pcall(function() b = Game:IsAI(p) end)
                        if b then bots = bots + 1 else real = real + 1 end
                    end
                end
            end
        end
    end
    local txt, col
    if total == 0 then txt = "[ AREA SECURE ]" col = {R=0,G=255,B=200,A=255}
    else
        txt = string.format("ENEMIES: %d  (Bots: %d | Real: %d)", total, bots, real)
        col = total == 1 and {R=255,G=255,B=0,A=255} or {R=255,G=165,B=0,A=255}
    end
    local off = {X=0, Y=0, Z=35}
    hud:AddDebugText(txt, me, 1.1, off, off, col, true, false, true, nil, 1.2, true)
end
_G.DS_SlowReg("enemy_counter", _G.DS_CounterTick)
""".rstrip()}


@feature("fps165", "165 FPS Unlock")
def _f_fps165(c):
    return {"lua": r"""
pcall(function()
    local g = require("client.slua.logic.setting.logic_setting_graphics")
    if g and g.SetFPS then
        local o = g.SetFPS
        g.SetFPS = function(s, lvl)
            o(s, lvl)
            if lvl == 8 and _G.DS_Get("fps165") == 1 and Game and Game.IsInGame and Game:IsInGame() then
                pcall(function()
                    s:ExecuteCMD("t.MaxFPS", "165")
                    s:ExecuteCMD("r.FrameRateLimit", "165")
                end)
            end
        end
    end
end)
pcall(function()
    local g = require("client.slua.umg.NewSetting.GraphicsNew.Comps.GSC_FPS")
    if g and g.__inner_impl then g.__inner_impl.GetMaxFPSLevel = function() return 8, 8 end end
end)
""".rstrip()}


@feature("expiry", "Expiry Gate")
def _f_expiry(c):
    y, m, d = c["expiry"]
    brand = c["brand"]
    return {"lua": f"""
local TS = os.time({{ year = {y}, month = {m}, day = {d}, hour = 12, min = 0, sec = 0 }})
function _G.CheckExpiration()
    if TS - os.time() <= 0 then _G._MOD_EXPIRED = true return false end
    _G._MOD_EXPIRED = false
    return true
end
function _G.ShowExpiredPopup(e)
    pcall(function()
        local M = require("client.slua.logic.common.logic_common_msg_box")
        local at = os.date("!%Y-%m-%d %H:%M:%S UTC", TS)
        M.Show(4, "DEVILSOUL", (e and "Expired: " or "Active: ")..at.."\\n\\n{brand}", function() end)
    end)
end
""".rstrip()}


@feature("tick_manager", "Tick Loop Manager")
def _f_tick_manager(c):
    return {"lua": r"""
local TM = { started = false, boot = nil }
local function runTicks()
    for _, f in pairs(_G.DS.Ticks) do pcall(f) end
end
local function runSlow()
    for _, f in pairs(_G.DS.Slow) do pcall(f) end
end
function TM.Try()
    if TM.started then return end
    local pc = nil
    pcall(function()
        if slua_GameFrontendHUD then pc = slua_GameFrontendHUD:GetPlayerController() end
    end)
    if not slua.isValid(pc) or not pc.AddGameTimer then return end
    pcall(function()
        pc:AddGameTimer(0.15, true, runTicks)
        pc:AddGameTimer(0.5, true, runSlow)
    end)
    TM.started = true
    print("[DS] ticks up")
end
function TM.Start()
    TM.Try()
    if TM.started or TM.boot then return end
    pcall(function()
        if _G.Game and _G.Game.AddGameTimer then
            TM.boot = _G.Game:AddGameTimer(0.5, true, function()
                TM.Try()
                if TM.started and TM.boot then
                    pcall(function() _G.Game:RemoveGameTimer(TM.boot) end)
                    TM.boot = nil
                end
            end)
        end
    end)
end
""".rstrip(), "init": "TM.Start()"}


# ═════════════════════════════════════════════════════════════════
# BUILDER
# ═════════════════════════════════════════════════════════════════
FORCED_HEAD = ("menu", "bypass", "antikick", "ingame_menu")
FORCED_TAIL = ("tick_manager",)


def _topo(ids):
    out, seen = [], set()
    def visit(i):
        if i in seen: return
        seen.add(i)
        for d in REGISTRY[i]["deps"]: visit(d)
        out.append(i)
    for i in ids: visit(i)
    return out


def build_mod(features, brand="DEVILSOUL", expiry=(2027, 1, 1), filename="DEVILSOUL.lua"):
    user = [f for f in features if f in REGISTRY and f not in FORCED_HEAD and f not in FORCED_TAIL]
    all_ids = list(FORCED_HEAD) + user + list(FORCED_TAIL)
    order = _topo(all_ids)
    if "tick_manager" in order:
        order.remove("tick_manager")
        order.append("tick_manager")
    ctx = {"brand": brand, "expiry": expiry}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = f"-- {filename}\n-- {ts}  brand: {brand}\n-- features: {', '.join(order)}\n"
    parts = [header, HEADER_API]
    inits = []
    for fid in order:
        built = REGISTRY[fid]["fn"](ctx)
        parts.append(f"-- ── {fid} ──\n{built['lua']}")
        if built.get("init"): inits.append(built["init"])
    parts.append("-- ── main ──\nfunction _G.DS_Start()")
    if "expiry" in order:
        parts.append("    if not _G.CheckExpiration() then _G.ShowExpiredPopup(true) return end")
    for line in inits: parts.append("    " + line)
    parts.append("end\n_G.DS_Start()")
    parts.append('print("[DEVILSOUL] loaded — ' + ",".join(order) + '")')
    return "\n\n".join(parts) + "\n"


def list_features():
    return [(k, REGISTRY[k]["label"], REGISTRY[k]["deps"]) for k in sorted(REGISTRY)]