"""
lua_features.py — DEVILSOUL ELITE v3
Fixed aim, no model stretch, manual number panel.
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
    rows = ",\n    ".join(f'{{ id = "{i}", val = 0 }}' for i in ids)
    return {"lua": f"_G.DS_Features = {{\n    {rows}\n}}\n".rstrip()}


# ═════════════════════════════════════════════════════════════════
# FIREWALL (kept from v2 — works)
# ═════════════════════════════════════════════════════════════════
@feature("bypass", "35-Layer Firewall")
def _f_bypass(c):
    return {"lua": r"""
local DS = _G.DS
DS.firewall = DS.firewall or { active = true, layers = {} }
local nop = function() end
local T = function() return true end
local F = function() return false end
local Z = function() return 0 end
local E = function() return {} end

local function isRep(s)
    if not s then return false end
    s = tostring(s):lower()
    for _, p in ipairs({"report","accuse","judge","kick","vote","ban","watch",
        "suspicion","cheat","hack","blacklist","punish","ticket","complain",
        "behavior","misconduct","teammatehurt","teamhurt","aimabnormal",
        "wallhack","esp","anticheat","seccheck","valided","integrity"}) do
        if s:find(p, 1, true) then return true end
    end
    return false
end
DS.isRep = isRep

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
    local PM = require("client.network.Protocol.ProtocolManager")
    if PM and PM.Send then
        local o = PM.Send
        PM.Send = function(self, n, ...) if isRep(n) then return end return o(self, n, ...) end
    end
end)
pcall(function()
    local NS = require("client.network.NetworkService")
    if NS and NS.Send then
        local o = NS.Send
        NS.Send = function(self, ...)
            local a = {...}
            for _, x in ipairs(a) do if isRep(tostring(x)) then return end end
            return o(self, ...)
        end
    end
end)
pcall(function()
    _G.GameplayCallbacks = _G.GameplayCallbacks or {}
    local GC = _G.GameplayCallbacks
    for _, k in ipairs({
        "ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow","ReportFireArms",
        "ReportVerifyInfoFlow","ReportMrpcsFlow","ReportPlayerBehavior","ReportTeammatHurt",
        "ReportPlayerMoveRoute","ReportPlayerPosition","ReportAimFlow","ReportHitFlow",
        "ReportWallHack","ReportWallhack","ReportAimbot","ReportSpeedHack",
        "ReportMagicBullet","ReportAbnormalMaterial","ReportDepthTestChange",
        "ReportMemoryException","ReportMaterialScan","ReportShaderOverride",
        "ReportPlayerKillFlow","ClientSecPlayerKillFlow",
        "OnPlayerRPCValidateFailed","OnPlayerActorChannelError","OnShutdownAfterError"
    }) do GC[k] = nop end
end)
pcall(function()
    for name, mod in pairs(package.loaded) do
        local ln = tostring(name):lower()
        if ln:find("report") or ln:find("accuse") or ln:find("judge")
           or ln:find("behavior") or ln:find("complain") or ln:find("watch")
           or ln:find("suspicion") or ln:find("cheat") or ln:find("security") then
            if type(mod) == "table" then
                for k, v in pairs(mod) do
                    if type(v) == "function" and isRep(k) then mod[k] = nop end
                end
            end
        end
    end
end)
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if not sm or sm.__ds_sil then return end
    local realGet = sm.Get
    local targets = {
        "ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem",
        "ClientAimTrackingSubsystem","ClientAntiCheatSubsystem",
        "ClientHawkEyePatrolSubsystem","CoronaLabSubsystem",
        "PlayerSecurityInfoSubsystem","ShootVerifySubSystemClient",
        "MemoryCheckSubsystem","SpeedCheckSubsystem","WallCheckSubsystem",
        "BehaviorScoreSubsystem","AFKReportorSubsystem","AvatarExceptionSubsystem",
        "GameReportSubsystem","SwiftHawkSubsystem","HeartbeatSubsystem",
        "ClientReportPlayerSubsystem","ModifierExceptionSubsystem",
        "ClientRenderCheckSubsystem","ClientMemoryGuardSubsystem",
        "ClientKernelCheckSubsystem","FileCheckSubsystem","PakCheckSubsystem",
        "IntegrityCheckSubsystem","KickVoteSubsystem","TeammateHurtReportSubsystem"
    }
    sm.Get = function(self, n)
        local s = realGet(self, n)
        if type(s) == "table" and not s.__ds_sil then
            for _, t in ipairs(targets) do
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
                    if n == "ClientWallhackDetectionSubsystem" then s.IsVisionNormal = T end
                    if n == "ClientESPDetectionSubsystem" then s.HasESP = F end
                    if n == "ClientAimTrackingSubsystem" then
                        s.GetAimData = function() return {accuracy=math.random(42,58),headshotRate=math.random(12,28),aimLockCount=0} end
                        s.IsAimNormal = T
                    end
                    if n == "ClientMemoryGuardSubsystem" then s.IsMemoryClean = function() return true,{code=0} end end
                    if n == "ShootVerifySubSystemClient" then s.VerifyShot = T end
                    if n == "ClientKernelCheckSubsystem" then s.IsKernelClean = T end
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
    local SI = import("SystemInfo")
    if SI then
        local ch = "0123456789ABCDEF"
        local function g(n) local s = "" for i=1,n do s=s..ch:sub(math.random(1,#ch),math.random(1,#ch)) end return s end
        _G.DS_FakeDev = g(32)
        if SI.GetDeviceID then SI.GetDeviceID = function() return _G.DS_FakeDev end end
        if SI.GetUniqueDeviceId then SI.GetUniqueDeviceId = function() return _G.DS_FakeDev end end
        if SI.GetMacAddress then SI.GetMacAddress = function() return g(6)..":"..g(6) end end
    end
end)
pcall(function()
    local t = _G.TssSdk
    if t then
        t.GetFileMD5 = function() return "" end
        t.VerifyFileSignature = T
        t.CheckIntegrity = T
        t.ScanMemory = function() return true, {} end
        t.IsEmulator = F
    end
end)
pcall(function()
    local h = package.loaded["GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent"]
    if h then h.bMHActive = false h.bCallPreReplication = false h.ControlMHActive = nop h.StartAvatarCheck = nop end
    _G.BlackList = {}
end)
pcall(function()
    local M = package.loaded["client.slua.logic.common.logic_common_msg_box"]
    if M and M.Show then
        local o = M.Show
        M.Show = function(t_, title, content, ...)
            local t = tostring(title or ""):lower()
            local cc = tostring(content or ""):lower()
            if t:find("ban") or t:find("kick") or t:find("suspend")
               or cc:find("banned") or cc:find("terminated your connection")
               or cc:find("data error with your client") then
                return
            end
            return o(t_, title, content, ...)
        end
    end
end)
pcall(function()
    local t = require("common.time_ticker")
    if t and t.AddTimerLoop then
        t.AddTimerLoop(0, function()
            local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
            if sm then
                local a = sm:Get("ClientAimTrackingSubsystem")
                if a then a.IsAimNormal = T end
                local w = sm:Get("ClientWallhackDetectionSubsystem")
                if w then w.IsVisionNormal = T end
            end
        end, -1, 4.0)
    end
end)
print("[DS FIREWALL] active")
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ANTI-KICK
# ═════════════════════════════════════════════════════════════════
@feature("antikick", "Anti-Kick (Data Error Blocker)")
def _f_antikick(c):
    return {"lua": r"""
local AK = { active = true }
local lastSend = {}
local RATE_LIMIT_MS = 30
local MAX_PAYLOAD = 4096

local function ok(name)
    local now = os.clock() * 1000
    local last = lastSend[name] or 0
    if now - last < RATE_LIMIT_MS then return false end
    lastSend[name] = now
    return true
end

pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...)
            if not AK.active then return o(n, ...) end
            local s = tostring(n or ""):lower()
            if s:find("position") or s:find("move") or s:find("location")
               or s:find("coord") or s:find("delta") then
                if not ok(s) then return nil end
            end
            return o(n, ...)
        end
    end
end)
pcall(function()
    local DS_ = require("GameLua.GameCore.Module.Subsystem.DisconnectSubsystem")
    if DS_ and DS_.OnDisconnect then
        local o = DS_.OnDisconnect
        DS_.OnDisconnect = function(self, reason, ...)
            local r = tostring(reason or ""):lower()
            if r:find("data error") or r:find("desync") or r:find("network") or r:find("integrity") then
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
            if not AK.active then return o(n, ...) end
            local s = tostring(n or ""):lower()
            if s:find("validate") or s:find("verify") or s:find("integrity")
               or s:find("checksum") or s:find("signature") then return end
            return o(n, ...)
        end
    end
end)
print("[DS] Anti-kick installed")
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# IN-GAME MENU (native settings tab)
# ═════════════════════════════════════════════════════════════════
@feature("ingame_menu", "In-Game Settings Menu")
def _f_ingame_menu(c):
    return {"lua": r"""
local MENU = { ready = false }
local TID = { title=990000, esp=990001, aim=990002, magic=990003, cross=990004, skin=990005, wall=990006 }
local FAKE = {
    [990000] = "DEVILSOUL",
    [990001] = "ESP",
    [990002] = "AIMBOT",
    [990003] = "MAGIC BULLET",
    [990004] = "CROSSHAIR",
    [990005] = "SCRIPT SKIN",
    [990006] = "WALLHACK",
}
local CATALOG = {
    {"esp_box","Box ESP","ESP"},{"esp_skeleton","Skeleton ESP","ESP"},
    {"esp_line","Snap Lines","ESP"},{"esp_distance","Distance","ESP"},
    {"esp_name","Name ESP","ESP"},{"esp_hp","HP Bar","ESP"},
    {"esp_weapon","Weapon Icon","ESP"},{"esp_radar","Radar ESP","ESP"},
    {"esp_vis","Visibility Color","ESP"},{"esp_fov_circle","FOV Circle","ESP"},
    {"aim_silent","Silent Aim","AIM"},{"aim_smooth","Smooth Aim","AIM"},
    {"aim_bone","Bone Lock","AIM"},{"aim_pred","Prediction","AIM"},
    {"aim_recoil","Recoil Comp","AIM"},{"aim_autofire","Auto Fire","AIM"},
    {"aim_shotgun","Shotgun Auto","AIM"},
    {"magic_full","Magic Full","MAGIC"},{"magic_head","Magic Head","MAGIC"},
    {"magic_neck","Magic Neck","MAGIC"},{"magic_body","Magic Body","MAGIC"},
    {"magic_legs","Magic Legs","MAGIC"},{"magic_custom","Custom Ratio","MAGIC"},
    {"magic_hitbox","Hitbox Expand","MAGIC"},{"magic_safe","Safe 60%","MAGIC"},
    {"cross_cross","Cross Style","CROSS"},{"cross_dot","Dot Style","CROSS"},
    {"cross_circle","Circle","CROSS"},{"cross_tstyle","T-Style","CROSS"},
    {"cross_rainbow","Rainbow","CROSS"},
    {"skin_weapon","Weapon Skin","SKIN"},{"skin_outfit","Outfit Skin","SKIN"},
    {"skin_vehicle","Vehicle Skin","SKIN"},{"skin_parachute","Parachute","SKIN"},
    {"skin_emote","Emote Unlock","SKIN"},{"skin_deadbox","Deadbox","SKIN"},
    {"skin_killmsg","Kill Message","SKIN"},
    {"wallhack","Wallhack","WALL"},{"enemy_counter","Enemy Counter","WALL"},
    {"fps165","165 FPS","WALL"},
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

        local groups = { ESP={}, AIM={}, MAGIC={}, CROSS={}, SKIN={}, WALL={} }
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
                { Key="DS_ESP",   Text=TID.esp,   UI=AM.TitleSwitcher, Stack=groups.ESP },
                { Key="DS_AIM",   Text=TID.aim,   UI=AM.TitleSwitcher, Stack=groups.AIM },
                { Key="DS_MAGIC", Text=TID.magic, UI=AM.TitleSwitcher, Stack=groups.MAGIC },
                { Key="DS_CROSS", Text=TID.cross, UI=AM.TitleSwitcher, Stack=groups.CROSS },
                { Key="DS_SKIN",  Text=TID.skin,  UI=AM.TitleSwitcher, Stack=groups.SKIN },
                { Key="DS_WALL",  Text=TID.wall,  UI=AM.TitleSwitcher, Stack=groups.WALL },
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
# MANUAL PANEL — number input per category
# ═════════════════════════════════════════════════════════════════
@feature("manual_panel", "Manual Number Panel")
def _f_manual_panel(c):
    return {"lua": r"""
-- Floating panel — type numbers per category, apply.
-- ESP codes:      1=Box  2=Skel  3=Line  4=Dist  5=Name  6=HP  7=Weap  8=Radar  9=Vis  10=FOV
-- AIMBOT codes:   1=Silent  2=Smooth  3=Bone  4=Pred  5=Recoil  6=AutoFire  7=Shotgun
-- MAGIC codes:    0=Off  1=Full  2=Head  3=Neck  4=Body  5=Legs  6=Custom  7=Hitbox  8=Safe
-- CROSS codes:    0=Off  1=Cross  2=Dot  3=Circle  4=T  5=Rainbow
-- SKIN codes:     0=Off  1=Weapon  2=Outfit  3=Vehicle  4=Para  5=Emote  6=Deadbox  7=KillMsg
-- WALL codes:     1=Wallhack  2=Counter  3=165FPS

local MAP = {
    ESP = {
        {1,"esp_box"},{2,"esp_skeleton"},{3,"esp_line"},{4,"esp_distance"},{5,"esp_name"},
        {6,"esp_hp"},{7,"esp_weapon"},{8,"esp_radar"},{9,"esp_vis"},{10,"esp_fov_circle"},
    },
    AIMBOT = {
        {1,"aim_silent"},{2,"aim_smooth"},{3,"aim_bone"},{4,"aim_pred"},
        {5,"aim_recoil"},{6,"aim_autofire"},{7,"aim_shotgun"},
    },
    MAGIC = {
        {0,"__MAGIC_OFF"},{1,"magic_full"},{2,"magic_head"},{3,"magic_neck"},
        {4,"magic_body"},{5,"magic_legs"},{6,"magic_custom"},{7,"magic_hitbox"},{8,"magic_safe"},
    },
    CROSS = {
        {0,"__CROSS_OFF"},{1,"cross_cross"},{2,"cross_dot"},{3,"cross_circle"},
        {4,"cross_tstyle"},{5,"cross_rainbow"},
    },
    SKIN = {
        {0,"__SKIN_OFF"},{1,"skin_weapon"},{2,"skin_outfit"},{3,"skin_vehicle"},
        {4,"skin_parachute"},{5,"skin_emote"},{6,"skin_deadbox"},{7,"skin_killmsg"},
    },
    WALL = {
        {1,"wallhack"},{2,"enemy_counter"},{3,"fps165"},
    },
}

local MAGIC_IDS = {"magic_full","magic_head","magic_neck","magic_body","magic_legs","magic_custom","magic_hitbox","magic_safe"}
local CROSS_IDS = {"cross_cross","cross_dot","cross_circle","cross_tstyle","cross_rainbow"}
local SKIN_IDS  = {"skin_weapon","skin_outfit","skin_vehicle","skin_parachute","skin_emote","skin_deadbox","skin_killmsg"}

local function allOff(tbl)
    for _, id in ipairs(tbl) do _G.DS_Set(id, 0) end
end

function _G.DS_ApplyManual(cat, str)
    cat = tostring(cat):upper()
    str = tostring(str or "")
    local m = MAP[cat]
    if not m then return false end

    if cat == "MAGIC" then allOff(MAGIC_IDS)
    elseif cat == "CROSS" then allOff(CROSS_IDS)
    elseif cat == "SKIN" then allOff(SKIN_IDS)
    elseif cat == "ESP" then
        for _, pair in ipairs(MAP.ESP) do _G.DS_Set(pair[2], 0) end
    elseif cat == "AIMBOT" then
        for _, pair in ipairs(MAP.AIMBOT) do _G.DS_Set(pair[2], 0) end
    elseif cat == "WALL" then
        for _, pair in ipairs(MAP.WALL) do _G.DS_Set(pair[2], 0) end
    end

    for token in str:gmatch("([^,]+)") do
        local num = tonumber(token:match("^%s*(%d+)%s*$"))
        if num then
            for _, pair in ipairs(m) do
                if pair[1] == num then
                    if pair[2]:sub(1,2) ~= "__" then
                        _G.DS_Set(pair[2], 1)
                    end
                end
            end
        end
    end
    return true
end

-- ── floating panel ─────────────────────────────────
local PANEL = { ready=false, main=nil, expanded=true, inputs={}, buttons={} }
local ROWS = {"ESP","AIMBOT","MAGIC","CROSS","SKIN","WALL"}
local DEFAULTS = {ESP="1,3", AIMBOT="1,3", MAGIC="0", CROSS="2", SKIN="0", WALL="1"}

local function getCanvas()
    local c = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U and U.GetMainControlBaseUI()
        if slua.isValid(b) then c = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    return c
end

local function makeLabel(parent, text, x, y, color)
    local t = nil
    pcall(function() t = CGame:NewObjectFromPath("/Script/UMG.TextBlock", parent) end)
    if not t then return nil end
    local SC = import("SlateColor") or import("/Script/SlateCore.SlateColor")
    local FC = import("LinearColor")
    t:SetText(text)
    if SC then t:SetColorAndOpacity(SC(color or FC(1,1,1,1))) else t:SetColorAndOpacity(color or FC(1,1,1,1)) end
    if t.Font then local f = t.Font f.Size = 12 t.Font = f end
    local s = parent:AddChildToCanvas(t)
    if s then
        s:SetPosition(import("Vector2D")(x, y))
        s:SetAutoSize(true)
        s:SetZOrder(2000)
    end
    return t
end

local function makeEditable(parent, hint, def, x, y, w)
    local e = nil
    pcall(function() e = CGame:NewObjectFromPath("/Script/UMG.EditableTextBox", parent) end)
    if not e then return nil end
    pcall(function()
        if e.SetHintText then e:SetHintText(hint) end
        if e.SetText then e:SetText(def or "") end
    end)
    local s = parent:AddChildToCanvas(e)
    if s then
        s:SetPosition(import("Vector2D")(x, y))
        s:SetSize(import("Vector2D")(w or 220, 28))
        s:SetZOrder(2000)
    end
    return e
end

local function makeButton(parent, text, x, y, w, h, onClick)
    local btn = nil
    pcall(function()
        local cls = slua.loadClass("/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP")
        if cls then btn = slua.newObject(cls, parent) end
    end)
    if not btn then return nil end
    pcall(function()
        if btn.RichText_Content then
            btn.RichText_Content:SetText(text)
            local f = btn.RichText_Content.Font
            if f then f.Size = 13 btn.RichText_Content:SetFont(f) end
        end
        btn:SetWidgetVisibility(UEnums.ESlateVisibility.Visible)
    end)
    local s = parent:AddChildToCanvas(btn)
    if s then
        s:SetPosition(import("Vector2D")(x, y))
        s:SetSize(import("Vector2D")(w or 80, h or 28))
        s:SetZOrder(2000)
    end
    pcall(function()
        if btn.OnClicked then btn.OnClicked:Add(function() if onClick then onClick() end end) end
    end)
    return btn
end

function PANEL.Create()
    if PANEL.ready and PANEL.main and slua.isValid(PANEL.main) then return true end
    local canvas = getCanvas()
    if not canvas then return false end

    local panel = nil
    pcall(function() panel = CGame:NewObjectFromPath("/Script/UMG.CanvasPanel", canvas) end)
    if not panel then return false end

    local FC = import("LinearColor")
    local W, H = 320, 260

    local bg = nil
    pcall(function() bg = CGame:NewObjectFromPath("/Script/UMG.Border", panel) end)
    if bg then
        bg:SetBrushColor(FC(0, 0, 0, 0.85))
        local bgs = panel:AddChildToCanvas(bg)
        if bgs then bgs:SetPosition(import("Vector2D")(0, 0)) bgs:SetSize(import("Vector2D")(W, H)) end
    end

    makeLabel(panel, "DEVILSOUL — Manual", 10, 6, FC(1,1,0,1))

    for i, cat in ipairs(ROWS) do
        local y = 34 + (i - 1) * 33
        makeLabel(panel, cat, 10, y + 6, FC(0.4, 1, 1, 1))
        local inp = makeEditable(panel, "e.g. 1,3", DEFAULTS[cat], 90, y, 140)
        PANEL.inputs[cat] = inp
        local btn = makeButton(panel, "Apply", 240, y, 70, 28, function()
            local txt = ""
            pcall(function() if inp and inp.GetText then txt = inp:GetText() or "" end end)
            _G.DS_ApplyManual(cat, txt)
        end)
        PANEL.buttons[cat] = btn
    end

    makeLabel(panel, "Codes:", 10, 234, FC(1,1,1,0.8))

    local s = canvas:AddChildToCanvas(panel)
    if s then
        s:SetPosition(import("Vector2D")(30, 300))
        s:SetSize(import("Vector2D")(W, H))
        s:SetZOrder(3000)
    end
    PANEL.main = panel
    PANEL.ready = true
    return true
end

function PANEL.Tick()
    if not PANEL.ready or not slua.isValid(PANEL.main) then
        PANEL.ready = false
    end
end

if _G.DS_SlowReg then _G.DS_SlowReg("manual_panel", function()
    pcall(PANEL.Create)
    pcall(PANEL.Tick)
end) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ESP HELPERS
# ═════════════════════════════════════════════════════════════════
ESP_HEADER = r"""
local ESP = _G.DS_ESP or {}
_G.DS_ESP = ESP
local function GC()
    if ESP.canvas and Game:IsValid(ESP.canvas) then return ESP.canvas end
    local ok, U = pcall(require, "GameLua.Mod.BaseMod.Common.UI.InGameUITools")
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
    local out = import("Vector2D")(0, 0)
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
    b:SetBrushColor(color)
    b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(b)
    if s then s:SetAutoSize(false) s:SetZOrder(z or 10) end
    return { w = b, s = s }
end
local function PT(parent, color, size, z)
    local t = nil
    pcall(function() t = CGame:NewObjectFromPath("/Script/UMG.TextBlock", parent) end)
    if not t or not slua.isValid(t) then return nil end
    local SC = import("SlateColor") or import("/Script/SlateCore.SlateColor")
    if SC then t:SetColorAndOpacity(SC(color)) else t:SetColorAndOpacity(color) end
    if t.Font then local f = t.Font f.Size = size or 12 t.Font = f end
    t:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(t)
    if s then s:SetAutoSize(true) s:SetZOrder(z or 20) end
    return { w = t, s = s }
end
local function EE(cb)
    local lp = GL() if not slua.isValid(lp) then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= lp and p.TeamID ~= lp.TeamID then
            local hp = 0 pcall(function() hp = p.Health or 0 end)
            if hp > 0 then cb(p, lp, PC) end
        end
    end
end
"""


@feature("esp_box", "Box ESP")
def _f_esp_box(c):
    return {"lua": ESP_HEADER + r"""
local boxes = {}
function ESP.TickBox()
    if _G.DS_Get("esp_box") ~= 1 then
        for k, v in pairs(boxes) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end boxes[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    local seen = {}
    EE(function(e, lp, PC)
        local key = tostring(e) seen[key] = true
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 90
        local ok, cx, cy = PJ(PC, loc) if not ok then return end
        local _, _, baseY = PJ(PC, e:K2_GetActorLocation()) if not baseY then return end
        local h = math.abs(baseY - cy) * 1.6
        local w = h * 0.55
        if not boxes[key] then boxes[key] = PB(cv, FC(1,0,0,0.85), 15) end
        local b = boxes[key]
        if b and b.s and slua.isValid(b.s) then
            b.s:SetPosition(FC(cx - w/2, cy - h/2))
            b.s:SetSize(FC(w, h))
            b.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
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
        for k, t in pairs(st) do for _, v in ipairs(t) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end st[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local mesh = e.Mesh if not slua.isValid(mesh) then return end
        st[key] = st[key] or {}
        local idx = 0
        local vis = LoS(PC, e)
        local col = vis and FC(0,1,0,0.9) or FC(1,0,0,0.7)
        for _, chain in ipairs(CHAINS) do
            local prev = nil
            for _, bone in ipairs(chain) do
                local bp = nil pcall(function() bp = mesh:GetSocketLocation(bone) end)
                if bp then
                    local ok, x, y = PJ(PC, bp)
                    if ok and prev then
                        idx = idx + 1
                        st[key][idx] = st[key][idx] or PB(cv, col, 5)
                        local w = st[key][idx]
                        local dx, dy = x - prev.x, y - prev.y
                        local len = math.sqrt(dx*dx + dy*dy)
                        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
                        if w and w.s then
                            w.w:SetBrushColor(col)
                            w.s:SetPosition(FC(prev.x, prev.y - 0.4))
                            w.s:SetSize(FC(len, 0.8))
                            w.w:SetRenderAngle(ang)
                            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
                        end
                    end
                    if ok then prev = {x=x, y=y} end
                end
            end
        end
        for i = idx + 1, #st[key] do
            if slua.isValid(st[key][i].w) then st[key][i].w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end
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
        for k, v in pairs(L) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end L[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    local sx, sy = 960, 60
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 90
        local ok, x, y = PJ(PC, loc) if not ok then return end
        L[key] = L[key] or PB(cv, FC(1,1,0,0.7), 1)
        local w = L[key]
        local dx, dy = x - sx, y - sy
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local vis = LoS(PC, e)
        if w and w.s then
            w.w:SetBrushColor(vis and FC(0,1,0,0.75) or FC(1,0,0,0.75))
            w.s:SetPosition(FC(sx, sy))
            w.s:SetSize(FC(len, 1.5))
            w.w:SetRenderAngle(ang)
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
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
        for k, v in pairs(D) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end D[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 130
        local ok, x, y = PJ(PC, loc) if not ok then return end
        local m = math.floor(lp:GetDistanceTo(e) / 100)
        D[key] = D[key] or PT(cv, FC(0,1,1,1), 14, 30)
        local w = D[key]
        if w and w.w then
            w.w:SetText(m .. "m")
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
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
        for k, v in pairs(N) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end N[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 150
        local ok, x, y = PJ(PC, loc) if not ok then return end
        local nm = "Unknown"
        pcall(function() nm = e:GetPlayerNameSafety() or "Unknown" end)
        N[key] = N[key] or PT(cv, FC(1,1,0,1), 12, 28)
        local w = N[key]
        if w and w.w then
            w.w:SetText(nm)
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
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
            if slua.isValid(v.bg.w) then v.bg.w:RemoveFromParent() v.bg.w:ConditionalBeginDestroy() end
            if slua.isValid(v.fg.w) then v.fg.w:RemoveFromParent() v.fg.w:ConditionalBeginDestroy() end
            HP[k] = nil
        end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 105
        local ok, x, y = PJ(PC, loc) if not ok then return end
        local hp, mx = 0, 100
        pcall(function() hp = e.Health or 0 mx = e.HealthMax or 100 end)
        if mx <= 0 then mx = 100 end
        local pct = hp / mx
        if pct > 1 then pct = 1 end if pct < 0 then pct = 0 end
        local col = pct > 0.5 and FC(0,1,0,0.9) or (pct > 0.25 and FC(1,0.5,0,0.9) or FC(1,0,0,0.9))
        if not HP[key] then HP[key] = { bg = PB(cv, FC(0,0,0,0.7), 40), fg = PB(cv, col, 41) } end
        local h = HP[key]
        h.bg.s:SetPosition(FC(x - 30, y))
        h.bg.s:SetSize(FC(60, 5))
        h.bg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        h.fg.w:SetBrushColor(col)
        h.fg.s:SetPosition(FC(x - 30, y))
        h.fg.s:SetSize(FC(60 * pct, 5))
        h.fg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
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
        for k, v in pairs(W) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end W[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 175
        local ok, x, y = PJ(PC, loc) if not ok then return end
        local wn = "Fist"
        pcall(function()
            local w = e.CurrentWeapon or (e.GetCurrentWeapon and e:GetCurrentWeapon())
            if slua.isValid(w) and w.GetWeaponName then wn = w:GetWeaponName() end
        end)
        W[key] = W[key] or PT(cv, FC(1,0.8,0.2,1), 11, 26)
        local w = W[key]
        if w and w.w then
            w.w:SetText(wn)
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
_G.DS_Reg("esp_weapon", ESP.TickWep)
""".rstrip()}


@feature("esp_radar", "Radar ESP")
def _f_esp_radar(c):
    return {"lua": r"""
local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)
local CFG = {
    UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
    MaxWidgetNum = 99, MaxShowDistance = 6000000,
    bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
    BindSocketName = "head", bUseLuaWorldSocketName = true,
    WorldPositionOffset = FVector(0,0,50), bNeedPreLoad = true, Priority = 2,
}
pcall(function()
    local t = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
    local c = t.GetCurrentConfig("ScreenMarkConfig")
    if c then c[9999] = CFG end
end)
local function tick()
    if _G.DS_Get("esp_radar") ~= 1 or not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    for _, e in pairs(GDP.GetAllPlayerCharacters and GDP.GetAllPlayerCharacters() or {}) do
        if slua.isValid(e) and e ~= me and e.TeamID ~= me.TeamID then
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
_G.DS_SlowReg("esp_radar", tick)
""".rstrip()}


@feature("esp_vis", "Visibility Color ESP")
def _f_esp_vis(c):
    return {"lua": ESP_HEADER + r"""
local V = {}
function ESP.TickVis()
    if _G.DS_Get("esp_vis") ~= 1 then
        for k, v in pairs(V) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end V[k] = nil end
        return
    end
    local cv = GC() if not cv then return end
    local FC = import("LinearColor")
    EE(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 90
        local ok, x, y = PJ(PC, loc) if not ok then return end
        local vis = LoS(PC, e)
        V[key] = V[key] or PB(cv, FC(1,0,0,0.85), 14)
        local w = V[key]
        if w and w.s then
            w.w:SetBrushColor(vis and FC(0,1,0,0.9) or FC(1,0,0,0.9))
            w.s:SetPosition(FC(x - 15, y - 15))
            w.s:SetSize(FC(30, 30))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
_G.DS_Reg("esp_vis", ESP.TickVis)
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
    if s then s:SetSize(V2(0,0)) s:SetPosition(V2(0,0)) s:SetZOrder(995) end
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
        local x1, y1 = cx + R*math.cos(a1), cy + R*math.sin(a1)
        local x2, y2 = cx + R*math.cos(a2), cy + R*math.sin(a2)
        local dx, dy = x2 - x1, y2 - y1
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local l = F.lines[i]
        if l and l.s then
            l.s:SetPosition(V2(x1, y1))
            l.s:SetSize(V2(len + 0.8, 1.5))
            l.w:SetRenderAngle(ang)
            l.w:SetBrushColor(col)
        end
    end
end
_G.DS_Reg("esp_fov", F.Tick)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# AIMBOT — FIXED (no glitch)
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
    if not b then pcall(function() if e.Mesh and e.Mesh.GetSocketLocation then b = e.Mesh:GetSocketLocation(n) end end) end
    return b
end
local function ENEMIES()
    local out = {}
    local me = GC() if not slua.isValid(me) then return out end
    local mt = me.TeamID or 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= mt then
            local hp = 0 pcall(function() hp = p.Health or 0 end)
            if hp > 0 then out[#out+1] = p end
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
-- Smooth write: interpolate 40% per call, keep Roll. Only if firing.
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
    local me = GC() if not slua.isValid(me) then return end
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
local BONE = "head"
function AIM.TickBone()
    if _G.DS_Get("aim_bone") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local now = os.clock()
    if now - CD < 0.08 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, BONE, 180)
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
local function HOOK()
    if MB.hooked then return end
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
HOOK()
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
HOOK()
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
HOOK()
function MB.TickNeck()
    if _G.DS_Get("magic_neck") ~= 1 then return end
    MB.force = function() return "neck" end
end
_G.DS_Reg("magic_neck", MB.TickNeck)
""".rstrip()}


@feature("magic_body", "Magic Body")
def _f_magic_body(c):
    return {"lua": MAGIC_HEADER + r"""
HOOK()
function MB.TickBody()
    if _G.DS_Get("magic_body") ~= 1 then return end
    MB.force = function() return "spine_02" end
end
_G.DS_Reg("magic_body", MB.TickBody)
""".rstrip()}


@feature("magic_legs", "Magic Legs")
def _f_magic_legs(c):
    return {"lua": MAGIC_HEADER + r"""
HOOK()
function MB.TickLegs()
    if _G.DS_Get("magic_legs") ~= 1 then return end
    MB.force = function() return "calf_l" end
end
_G.DS_Reg("magic_legs", MB.TickLegs)
""".rstrip()}


@feature("magic_custom", "Magic Custom Ratio")
def _f_magic_custom(c):
    return {"lua": MAGIC_HEADER + r"""
HOOK()
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


@feature("magic_hitbox", "Magic Hitbox Expand")
def _f_magic_hitbox(c):
    return {"lua": r"""
-- SAFE version: NO auto model stretch. Only affects internal damage hitbox.
local HX = { applied = {} }
function HX.Tick()
    -- No-op. The old auto-stretch was causing visual glitch.
    -- Hitbox advantage still comes from magic_head/body which changes damage position.
    return
end
_G.DS_SlowReg("magic_hitbox", HX.Tick)
""".rstrip()}


@feature("magic_safe", "Safe 60% Magic")
def _f_magic_safe(c):
    return {"lua": MAGIC_HEADER + r"""
HOOK()
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
# CROSSHAIR
# ═════════════════════════════════════════════════════════════════
CROSS_HEADER = r"""
local CH = _G.DS_CH or {}
_G.DS_CH = CH
local function CV()
    local c = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U.GetMainControlBaseUI()
        if slua.isValid(b) then c = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    return c
end
local function BB(parent, color, z)
    local b = nil
    pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", parent) end)
    if not b then return nil end
    b:SetBrushColor(color)
    b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(b)
    if s then s:SetZOrder(z or 40) end
    return { w = b, s = s }
end
local function CLEAR(bucket)
    if not bucket then return end
    for _, v in pairs(bucket) do
        if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end
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
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.cross then
        CH.cross = { h = BB(cv, FC(1,0,0,1)), v = BB(cv, FC(1,0,0,1)) }
    end
    CH.cross.h.s:SetPosition(V2(cx-10, cy-1))
    CH.cross.h.s:SetSize(V2(20, 2))
    CH.cross.v.s:SetPosition(V2(cx-1, cy-10))
    CH.cross.v.s:SetSize(V2(2, 20))
end
_G.DS_Reg("cross_cross", CH.TickCross)
""".rstrip()}


@feature("cross_dot", "Crosshair — Dot")
def _f_cross_dot(c):
    return {"lua": CROSS_HEADER + r"""
function CH.TickDot()
    local cv = CV()
    if _G.DS_Get("cross_dot") ~= 1 then if CH.dot and slua.isValid(CH.dot.w) then CH.dot.w:RemoveFromParent() CH.dot = nil end return end
    if not cv then return end
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.dot then CH.dot = BB(cv, FC(0,1,0,1)) end
    CH.dot.s:SetPosition(V2(cx-3, cy-3))
    CH.dot.s:SetSize(V2(6, 6))
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
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    local R, N = 12, 20
    if not CH.circle then
        CH.circle = {}
        for i = 1, N do
            CH.circle[i] = BB(cv, FC(0,1,1,1))
            CH.circle[i].w:SetRenderTransformPivot(V2(0, 0.5))
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
        l.s:SetPosition(V2(x1, y1))
        l.s:SetSize(V2(len+0.5, 1))
        l.w:SetRenderAngle(ang)
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
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    if not CH.ts then
        CH.ts = { top = BB(cv, FC(1,1,0,1)), left = BB(cv, FC(1,1,0,1)), right = BB(cv, FC(1,1,0,1)) }
    end
    CH.ts.top.s:SetPosition(V2(cx-1, cy-12))
    CH.ts.top.s:SetSize(V2(2, 10))
    CH.ts.left.s:SetPosition(V2(cx-12, cy-1))
    CH.ts.left.s:SetSize(V2(10, 2))
    CH.ts.right.s:SetPosition(V2(cx+2, cy-1))
    CH.ts.right.s:SetSize(V2(10, 2))
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
    local FC = import("LinearColor")
    local V2 = import("Vector2D")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X*0.5, vp.Y*0.5
    local t = os.clock() * 2
    local r, g, b = (math.sin(t)+1)/2, (math.sin(t+2)+1)/2, (math.sin(t+4)+1)/2
    local col = FC(r, g, b, 1)
    if not CH.rb then CH.rb = { h = BB(cv, col), v = BB(cv, col) } end
    CH.rb.h.w:SetBrushColor(col)
    CH.rb.v.w:SetBrushColor(col)
    CH.rb.h.s:SetPosition(V2(cx-10, cy-1))
    CH.rb.h.s:SetSize(V2(20, 2))
    CH.rb.v.s:SetPosition(V2(cx-1, cy-10))
    CH.rb.v.s:SetSize(V2(2, 20))
end
_G.DS_Reg("cross_rb", CH.TickRB)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# SKIN
# ═════════════════════════════════════════════════════════════════
@feature("skin_weapon", "Weapon Skin Mod")
def _f_skin_weapon(c):
    return {"lua": r"""
local SK = { _cd = 0 }
local MAP = {
    [101001]=1101001174, [101004]=1101004163, [101003]=1101003146,
    [101008]=1101008081, [101006]=1101006062,
    [103001]=1103001202, [103003]=1103003079, [103002]=1103002030, [103004]=1103004037,
    [102001]=1102001120, [102002]=1102002043,
}
function SK.Tick()
    if _G.DS_Get("skin_weapon") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 1.5 then return end
    SK._cd = now
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local wm = me.WeaponManagerComponent
    if not slua.isValid(wm) then return end
    local w = wm.CurrentWeaponReplicated
    if not slua.isValid(w) then return end
    local wid = 0
    pcall(function() wid = w:GetWeaponID() end)
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


@feature("skin_outfit", "Outfit Skin Mod")
def _f_skin_outfit(c):
    return {"lua": r"""
local SK = { _cd = 0, OUTFIT = 1407870 }
function SK.Tick()
    if _G.DS_Get("skin_outfit") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.0 then return end
    SK._cd = now
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    pcall(function() comp:PutOnCustomEquipmentByID(SK.OUTFIT) end)
end
_G.DS_SlowReg("skin_outfit", SK.Tick)
""".rstrip()}


@feature("skin_vehicle", "Vehicle Skin Mod")
def _f_skin_vehicle(c):
    return {"lua": r"""
local SK = { _cd = 0, SKIN = 1961010 }
function SK.Tick()
    if _G.DS_Get("skin_vehicle") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.0 then return end
    SK._cd = now
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local v = me.CurrentVehicle
    if not slua.isValid(v) then return end
    local av = v.VehicleAvatarComponent_BP
    if not slua.isValid(av) then return end
    pcall(function() av:ChangeItemAvatar(SK.SKIN, false) end)
end
_G.DS_SlowReg("skin_vehicle", SK.Tick)
""".rstrip()}


@feature("skin_parachute", "Parachute Skin Mod")
def _f_skin_parachute(c):
    return {"lua": r"""
local SK = { _cd = 0, SKIN = 1401000 }
function SK.Tick()
    if _G.DS_Get("skin_parachute") ~= 1 then return end
    local now = os.clock()
    if now - SK._cd < 2.5 then return end
    SK._cd = now
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    pcall(function() comp:PutOnCustomEquipmentByID(SK.SKIN) end)
end
_G.DS_SlowReg("skin_parachute", SK.Tick)
""".rstrip()}


@feature("skin_emote", "Emote Unlock")
def _f_skin_emote(c):
    return {"lua": r"""
local EM = { hooked = false }
if not EM.hooked then
    EM.hooked = true
    pcall(function()
        local le = require("GameLua.Mod.Library.GamePlay.Avatar.Emote.logic_emote")
        if le and le.IsEmoteExist then
            local o = le.IsEmoteExist
            le.IsEmoteExist = function(id)
                if _G.DS_Get("skin_emote") == 1 then return true end
                return o(id)
            end
        end
    end)
end
""".rstrip()}


@feature("skin_deadbox", "Deadbox Skin Mod")
def _f_skin_deadbox(c):
    return {"lua": r"""
local SK = { last = nil }
function SK.Tick()
    if _G.DS_Get("skin_deadbox") ~= 1 then return end
    pcall(function()
        local me = nil
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
        if not slua.isValid(me) then return end
        local w = me:GetCurrentWeapon()
        if not slua.isValid(w) then return end
        local wac = w.WeaponAvatarComponent
        if slua.isValid(wac) then SK.last = wac.CachedLoadedID or 0 end
    end)
end
_G.DS_SlowReg("skin_deadbox", SK.Tick)
""".rstrip()}


@feature("skin_killmsg", "Kill Message Skin")
def _f_skin_killmsg(c):
    return {"lua": r"""
pcall(function()
    local SKI = require("GameLua.Mod.BaseMod.Client.KillInfoTips.KillInfo")
    if SKI and SKI.__inner_impl and SKI.__inner_impl.FileItem and not SKI.__inner_impl._ds_hooked then
        SKI.__inner_impl._ds_hooked = true
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


# ═════════════════════════════════════════════════════════════════
# WALLHACK / COUNTER / FPS
# ═════════════════════════════════════════════════════════════════
@feature("wallhack", "Wallhack")
def _f_wallhack(c):
    return {"lua": r"""
local WH = { ready = false, colors = {
    vis  = import("LinearColor")(255, 255, 0, 100),
    occ  = import("LinearColor")(0, 255, 255, 100),
    bVis = import("LinearColor")(255, 255, 0, 100),
    bOcc = import("LinearColor")(0, 255, 255, 100),
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
        mesh:SetDrawHighlight(true) mesh:OverrideHighlightColor(vis) mesh:SetHighlightCanBeOccluded(false)
        mesh:SetDrawIdeaOutline(true) mesh:SetIdeaOutlineNew(true)
        mesh:SetIdeaOutlineOcclusionHighlight(true)
        mesh:OverrideIdeaOutlineColor(vis) mesh:SetIdeaOutlineOcclusionColor(occ)
        mesh:OverrideIdeaOutlineThickness(20.0) mesh:SetIdeaOverrideOutlineAndOcclusion(true)
        mesh:SetRenderCustomDepth(true) mesh:SetCustomDepthStencilValue(255)
    end)
end
function WH.Tick()
    if _G.DS_Get("wallhack") ~= 1 then return end
    WH.Setup()
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID or 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= myTeam and (p.Health or 0) > 0 then
            local isAI = false pcall(function() isAI = Game:IsAI(p) end)
            local vis = isAI and WH.colors.bVis or WH.colors.vis
            local occ = isAI and WH.colors.bOcc or WH.colors.occ
            if slua.isValid(p.Mesh) then apply(p.Mesh, vis, occ) end
            local av = p.CharacterAvatarComp2_BP
            if av and av.GetMeshCompBySlot then
                for _, s in ipairs(WH.slots) do
                    local m = av:GetMeshCompBySlot(s)
                    if slua.isValid(m) then apply(m, vis, occ) end
                end
            end
        end
    end
end
_G.DS_Reg("wallhack", WH.Tick)
""".rstrip()}


@feature("enemy_counter", "Enemy Counter")
def _f_enemy_counter(c):
    return {"lua": r"""
function _G.DS_Counter()
    if _G.DS_Get("enemy_counter") ~= 1 then return end
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID or 0
    local myPos = me:K2_GetActorLocation()
    if not myPos then return end
    local total, bots, real = 0, 0, 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= myTeam then
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
    local txt, col
    if total == 0 then txt = "[ AREA SECURE ]" col = {R=0,G=255,B=200,A=255}
    else
        txt = string.format("ENEMIES: %d  (Bots: %d | Real: %d)", total, bots, real)
        col = total == 1 and {R=255,G=255,B=0,A=255} or {R=255,G=165,B=0,A=255}
    end
    local off = {X=0, Y=0, Z=35}
    hud:AddDebugText(txt, me, 1.1, off, off, col, true, false, true, nil, 1.2, true)
end
_G.DS_SlowReg("enemy_counter", _G.DS_Counter)
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
        M.Show(4, "DEVILSOUL", (e and "Expired: " or "Active until: ")..at.."\\n\\n{brand}", function() end)
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
        pc:AddGameTimer(0.50, true, runSlow)
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
FORCED_HEAD = ("menu", "bypass", "antikick", "ingame_menu", "manual_panel")
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