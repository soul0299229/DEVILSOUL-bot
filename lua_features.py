"""
lua_features.py — feature registry + build_mod() for the Lua mod generator.
Import this from bot.py. Every build forces menu + bypass in.
"""

from __future__ import annotations
from datetime import datetime, timezone

REGISTRY: dict[str, dict] = {}

def feature(fid, label, deps=()):
    def deco(fn):
        REGISTRY[fid] = {"id": fid, "label": label, "deps": list(deps), "fn": fn}
        return fn
    return deco


# ── menu ────────────────────────────────────────────────────────
@feature("menu", "Feature toggle table")
def _f_menu(c):
    lines = ",\n    ".join(
        f'{{ id = "{e["id"]}", name = "{e["name"]}", val = {e["val"]}, type = "{e["type"]}"'
        + (f', options = {{{", ".join(repr(o) for o in e["options"])}}}' if e.get("options") else "")
        + " }" for e in c["menu_entries"])
    return {"lua": f"""
_G.xvakuex_Features = {{
    {lines}
}}

function _G.xvakuex_GetVal(id)
    for _, f in ipairs(_G.xvakuex_Features) do
        if f.id == id then return f.val end
    end
    return 0
end

function _G.xvakuex_SetVal(id, val)
    for _, f in ipairs(_G.xvakuex_Features) do
        if f.id == id then f.val = val return true end
    end
    return false
end
""".rstrip(), "init": "", "menu": []}


# ── expiry ──────────────────────────────────────────────────────
@feature("expiry", "Expiry gate")
def _f_expiry(c):
    y, m, d = c["expiry"]
    brand = c["brand"]
    return {"lua": f"""
local EXPIRY_TIMESTAMP = os.time({{ year = {y}, month = {m}, day = {d}, hour = 12, min = 0, sec = 0 }})

local function Fmt(sec)
    if sec <= 0 then return "0d 0h 0m 0s" end
    local d = math.floor(sec/86400); sec = sec % 86400
    local h = math.floor(sec/3600);  sec = sec % 3600
    local m = math.floor(sec/60)
    local s = sec % 60
    return string.format("%dd %dh %dm %ds", d, h, m, s)
end

function _G.CheckExpiration()
    local rem = EXPIRY_TIMESTAMP - os.time()
    if rem <= 0 then _G._MOD_EXPIRED = true return false end
    _G._MOD_EXPIRED = false
    _G._MOD_REMAINING_SECONDS = rem
    return true
end

function _G.ShowExpiryPopup(expired)
    pcall(function()
        local Msg = package.loaded["client.slua.logic.common.logic_common_msg_box"]
            or require("client.slua.logic.common.logic_common_msg_box")
        local at = os.date("!%Y-%m-%d %H:%M:%S UTC", EXPIRY_TIMESTAMP)
        if expired then
            Msg.Show(4, "Mod Expired", "This Mod Has Expired.\\n\\nExpired On: "..at.."\\n\\nJoin {brand}",
                function() end)
        else
            local rem = _G._MOD_REMAINING_SECONDS or (EXPIRY_TIMESTAMP - os.time())
            Msg.Show(4, "Notification", "Mod Validity: "..Fmt(rem).."\\nExpires at: "..at..
                "\\n\\nfor Renewal Dm {brand}", function() end)
        end
    end)
end

function _G.TryShowWelcome()
    if _G.WelcomeShown then return end
    if not _G.CheckExpiration() then _G.ShowExpiryPopup(true) return end
    _G.ShowExpiryPopup(false)
    _G.WelcomeShown = true
end
""".rstrip(), "init": "", "menu": []}


# ── bypass (FORCED IN EVERY BUILD) ──────────────────────────────
@feature("bypass", "Security function bypass")
def _f_bypass(c):
    return {"lua": """
-- ─── security bypass layer ───
local nop = function() end
local blocked = {
    "reportattackflow","reportsecattackflow","reporthurtflow","reportfirearms",
    "reportverifyinfoflow","reportmrpcsflow","reportplayerbehavior",
    "reportplayermoveroute","reportplayerposition","reportvehiclemoveflow",
    "reportwallhack","reportaimbot","reportspeedhack","reportmagicbullet",
    "reportabnormalmaterial","reportdepthtestchange","reportmaterialscan",
    "reportshaderoverride","reportmemoryexception",
    "sendsectlog","senddataminingtlog","sendactivitytlog",
    "sendserveravgtickdelta","reporthitflow",
    "sendtsssdkantidatatolobby","senddserrorlogtolobby",
    "swifthawk","clientswifthawk","swifthawkreport","swifthawkdata",
    "anticheatreport","cheatdetection","violationreport",
    "integritycheck","signatureverify","filecheck","pakcheck",
}
local origRequire = require
local secPatterns = {"Security","AntiCheat","Integrity","SwiftHawk","TssSdk",
                     "ShootVerify","CoronaLab","HiggsBoson"}
local dummies = {
    ["GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent"] = { bMHActive = false, BlackList = {} },
    ["GameLua.Mod.BaseMod.Common.Security.AvatarCheckCallback"] = {},
    ["GameLua.Mod.BaseMod.Common.Security.GameSafeCallbacks"] = {},
}
local function isSec(name)
    for _, p in ipairs(secPatterns) do
        if name:find(p, 1, true) then return true end
    end
    return false
end

_G.require = function(name)
    if dummies[name] then return dummies[name] end
    local mod = origRequire(name)
    if type(mod) == "table" and isSec(name) and not mod.__ak_patched then
        pcall(function()
            for k, v in pairs(mod) do
                if type(v) == "function" then
                    local lk = tostring(k):lower():gsub("[^%w]", "")
                    for _, b in ipairs(blocked) do
                        if lk == b then mod[k] = nop break end
                    end
                end
            end
            mod.__ak_patched = true
        end)
    end
    return mod
end

pcall(function()
    local SM = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if not SM or SM.__ak_hooked then return end
    local realGet = SM.Get
    local targets = {
        "ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem",
        "ClientAimTrackingSubsystem","ClientAntiCheatSubsystem",
        "ClientHawkEyePatrolSubsystem","ShootVerifySubSystemClient",
        "MemoryCheckSubsystem","SpeedCheckSubsystem","WallCheckSubsystem",
        "ClientReportPlayerSubsystem","FileCheckSubsystem","PakCheckSubsystem",
        "ClientKernelCheckSubsystem","ClientMemoryGuardSubsystem",
        "SwiftHawkSubsystem","HeartbeatSubsystem",
    }
    SM.Get = function(self, name)
        local sub = realGet(self, name)
        if type(sub) == "table" and not sub.__ak_sub_patched then
            for _, t in ipairs(targets) do
                if name == t then
                    for k, v in pairs(sub) do
                        if type(v) == "function" then
                            local lk = tostring(k):lower():gsub("[^%w]", "")
                            for _, b in ipairs(blocked) do
                                if lk == b then sub[k] = nop break end
                            end
                        end
                    end
                    sub.__ak_sub_patched = true
                    break
                end
            end
        end
        return sub
    end
    SM.__ak_hooked = true
end)
""".rstrip(), "init": "", "menu": []}


# ── fps165 ──────────────────────────────────────────────────────
@feature("fps165", "165 FPS unlock")
def _f_fps165(c):
    return {"lua": """
local function Enable165FPS()
    if _G.__FPS165_LOADED then return end
    pcall(function()
        local g = require("client.slua.logic.setting.logic_setting_graphics")
        if g then
            local orig = g.SetFPS
            g.SetFPS = function(settings, lvl)
                if orig then orig(settings, lvl) end
                if lvl == 8 and _G.xvakuex_GetVal("FPS165") == 1
                   and Game and Game.IsInGame and Game:IsInGame() then
                    pcall(function()
                        settings:ExecuteCMD("t.MaxFPS", "165")
                        settings:ExecuteCMD("r.FrameRateLimit", "165")
                    end)
                end
            end
        end
    end)
    pcall(function()
        local GSC = require("client.slua.umg.NewSetting.GraphicsNew.Comps.GSC_FPS")
        if GSC and GSC.__inner_impl then
            GSC.__inner_impl.GetMaxFPSLevel = function() return 8, 8 end
        end
    end)
    _G.__FPS165_LOADED = true
end
Enable165FPS()
""".rstrip(), "init": "", "menu": [
        {"id": "FPS165", "name": "165 FPS Unlock", "val": 1, "type": "toggle"}]}


# ── esp_screen ──────────────────────────────────────────────────
@feature("esp_screen", "Screen-space ESP")
def _f_esp_screen(c):
    return {"lua": """
local ESP = { Widgets = {}, Canvas = nil }
local FVector2D = import("Vector2D")
local FLinearColor = import("LinearColor")

local function GetCanvas()
    if ESP.Canvas and Game:IsValid(ESP.Canvas) then return ESP.Canvas end
    local ok, UI = pcall(require, "GameLua.Mod.BaseMod.Common.UI.InGameUITools")
    if not ok or not UI then return nil end
    local base = UI.GetMainControlBaseUI()
    if not base or not Game:IsValid(base) then return nil end
    ESP.Canvas = base.CanvasPanel_0 or base.CanvasPanel_42
    return ESP.Canvas
end

local function CreateLabel()
    local canvas = GetCanvas()
    if not canvas then return nil end
    local tb = CGame:NewObjectFromPath("/Script/UMG.TextBlock", canvas)
    if not tb or not slua.isValid(tb) then return nil end
    tb:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    tb:SetColorAndOpacity(FSlateColor(FLinearColor(1, 1, 0, 1)))
    local slot = canvas:AddChildToCanvas(tb)
    if slot then slot:SetAutoSize(true) slot:SetZOrder(30) end
    return { text = tb, slot = slot, pos = FVector2D(0, 0) }
end

local function Remove(key)
    local w = ESP.Widgets[key]
    if w and w.text and slua.isValid(w.text) then
        pcall(function() w.text:RemoveFromParent() w.text:ConditionalBeginDestroy() end)
    end
    ESP.Widgets[key] = nil
end

function ESP.Tick()
    if _G.xvakuex_GetVal("ESP_V2") ~= 1 then
        for k in pairs(ESP.Widgets) do Remove(k) end
        return
    end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local seen = {}
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= me.TeamID then
            local key = tostring(p)
            seen[key] = true
            local loc = p:K2_GetActorLocation()
            if loc then
                loc.Z = loc.Z + 85
                local out = FVector2D(0, 0)
                local ok = false
                pcall(function() ok = PC:ProjectWorldLocationToScreen(loc, out, true) end)
                if ok and (out.X ~= 0 or out.Y ~= 0) then
                    local w = ESP.Widgets[key] or CreateLabel()
                    if w then
                        ESP.Widgets[key] = w
                        w.text:SetText((p.GetPlayerNameSafety and p:GetPlayerNameSafety()) or "Enemy")
                        w.pos.X = out.X
                        w.pos.Y = out.Y
                        w.slot:SetPosition(w.pos)
                    end
                else Remove(key) end
            end
        end
    end
    for k in pairs(ESP.Widgets) do if not seen[k] then Remove(k) end end
end
""".rstrip(), "init": "", "menu": [
        {"id": "ESP_V2", "name": "Screen ESP Master", "val": 1, "type": "toggle"},
        {"id": "ESP9_Name", "name": "ESP Name", "val": 1, "type": "toggle"},
        {"id": "ESP9_Distance", "name": "ESP Distance", "val": 1, "type": "toggle"},
        {"id": "ESP9_HP", "name": "ESP Health", "val": 1, "type": "toggle"}]}


# ── esp_map ─────────────────────────────────────────────────────
@feature("esp_map", "Map marker ESP")
def _f_esp_map(c):
    return {"lua": """
local MapESP = {}
MapESP.Config = {
    UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
    MaxWidgetNum = 99, MaxShowDistance = 6000000,
    bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
    BindSocketName = "head", bUseLuaWorldSocketName = true,
    WorldPositionOffset = FVector(0, 0, 50), bNeedPreLoad = true, Priority = 2,
}

function MapESP.Init()
    pcall(function()
        local tools = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
        local cfg = tools.GetCurrentConfig("ScreenMarkConfig")
        if cfg then cfg[9999] = MapESP.Config end
        for n, m in pairs(package.loaded) do
            if type(n) == "string" and n:find("ScreenMarkConfig") and type(m) == "table" then
                m[9999] = MapESP.Config
            end
        end
    end)
end

function MapESP.Tick()
    if _G.xvakuex_GetVal("ESP_MAP") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools")
    for _, e in pairs(GDP.GetAllPlayerCharacters and GDP.GetAllPlayerCharacters() or {}) do
        if slua.isValid(e) and e ~= me and e.TeamID ~= me.TeamID then
            local dead = false
            pcall(function()
                if type(e.IsDead) == "function" then dead = e:IsDead() end
                if e.bHidden then dead = true end
            end)
            if not dead and not e.bHasAKMapMark then
                pcall(function()
                    e.NativeMapMark = IMT.ClientAddMapMark(9999, FVector(0,0,0), 0, "", 4, e)
                    e.bHasAKMapMark = true
                end)
            elseif dead and e.bHasAKMapMark then
                pcall(function() IMT.ClientRemoveMapMark(e.NativeMapMark) end)
                e.bHasAKMapMark = false
            end
        end
    end
end

MapESP.Init()
""".rstrip(), "init": "", "menu": [
        {"id": "ESP_MAP", "name": "Mini Map ESP", "val": 1, "type": "toggle"}]}


# ── aimbot ──────────────────────────────────────────────────────
@feature("aimbot", "Aimbot / recoil suppress", deps=("menu",))
def _f_aimbot(c):
    return {"lua": """
function _G.ApplyHardAimbot()
    if _G.xvakuex_GetVal("AIMBOT") ~= 1 then return end
    pcall(function()
        local pc = slua_GameFrontendHUD:GetPlayerController()
        if not slua.isValid(pc) then return end
        local char = pc:GetPlayerCharacterSafety()
        if not slua.isValid(char) then return end
        local wm = char.WeaponManagerComponent
        if not slua.isValid(wm) then return end
        local weapon = wm.CurrentWeaponReplicated
        if not slua.isValid(weapon) then return end
        local entity = weapon.ShootWeaponEntityComp
        if not slua.isValid(entity) then return end

        entity.RecoilKickADS = 0.020
        entity.GameDeviationFactor = 0.01
        entity.GameDeviationAccuracy = 0.01

        if entity.AutoAimingConfig then
            for _, r in ipairs({"OuterRange", "InnerRange"}) do
                local cfg = entity.AutoAimingConfig[r]
                if cfg then
                    cfg.Speed = 4.0 cfg.RangeRate = 4.5 cfg.SpeedRate = 4.0
                    cfg.RangeRateSight = 3.0 cfg.SpeedRateSight = 3.0
                    cfg.CrouchRate = 4.5 cfg.ProneRate = 4.0
                    cfg.adsorbMaxRange = 200 cfg.adsorbMinRange = 20
                    cfg.adsorbMinAttenuationDis = 100 cfg.adsorbMaxAttenuationDis = 8000
                    cfg.adsorbActiveMinRange = 20
                end
            end
        end

        pcall(function()
            local ac = char.BP_AutoAimingComponent_C or char.AutoAimingComponent
            if slua.isValid(ac) and ac.Bones then
                pcall(function() ac.Bones[0] = "neck_01" end)
                pcall(function() ac.Bones[1] = "neck_01" end)
                pcall(function() ac.Bones[2] = "neck_01" end)
            end
        end)
    end)
end
""".rstrip(), "init": "", "menu": [
        {"id": "AIMBOT", "name": "Aimbot", "val": 1, "type": "toggle"}]}


# ── wallhack ────────────────────────────────────────────────────
@feature("wallhack", "Draw-dyeing wallhack", deps=("menu",))
def _f_wallhack(c):
    return {"lua": """
local WH = {
    Colors = {
        vis  = LinearColor(255, 255, 0, 100),
        occ  = LinearColor(0, 255, 255, 100),
        bVis = LinearColor(255, 255, 0, 100),
        bOcc = LinearColor(0, 255, 255, 100),
    },
    Slots = {0,1,2,3,4,5,6,7},
}

function WH.SetupConsole()
    if WH._ready then return end
    pcall(function()
        local KSL = import("KismetSystemLibrary")
        local world = slua.getWorld()
        if not KSL or not world then return end
        KSL.ExecuteConsoleCommand(world, "r.EnableDrawDyeingColor 1")
        KSL.ExecuteConsoleCommand(world, "r.CustomDepth 3")
        KSL.ExecuteConsoleCommand(world, "r.IdeaOutline.Enable 1")
        KSL.ExecuteConsoleCommand(world, "r.Highlight.Enable 1")
        WH._ready = true
    end)
end

local function Apply(mesh, vis, occ)
    if not mesh or not slua.isValid(mesh) then return end
    pcall(function()
        mesh:SetDrawDyeing(true)
        mesh:SetDrawDyeingMode(1)
        mesh:SetVisibleDyeingColor(vis)
        mesh:SetOccludedDyeingColor(occ)
        mesh:SetDyeingColorFadeDistance(99999.0)
        mesh:SetDyeingColorMinMaxDistance(0.0, 99999.0)
        mesh:SetDrawHighlight(true)
        mesh:OverrideHighlightColor(vis)
        mesh:SetHighlightCanBeOccluded(false)
        mesh:SetDrawIdeaOutline(true)
        mesh:SetIdeaOutlineNew(true)
        mesh:SetIdeaOutlineOcclusionHighlight(true)
        mesh:OverrideIdeaOutlineColor(vis)
        mesh:SetIdeaOutlineOcclusionColor(occ)
        mesh:OverrideIdeaOutlineThickness(20.0)
        mesh:SetIdeaOverrideOutlineAndOcclusion(true)
        mesh:SetRenderCustomDepth(true)
        mesh:SetCustomDepthStencilValue(255)
    end)
end

function WH.Tick()
    if _G.xvakuex_GetVal("WALLHACK") ~= 1 then return end
    pcall(function()
        WH.SetupConsole()
        local GDP = require("GameLua.GameCore.Data.GameplayData")
        local me = GDP.GetPlayerCharacter()
        if not slua.isValid(me) then return end
        local myTeam = me.TeamID or 0
        for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
            if slua.isValid(p) and p ~= me and p.TeamID ~= myTeam
               and p.Health and p.Health > 0 then
                local isAI = Game.IsAI and Game:IsAI(p)
                local vis = isAI and WH.Colors.bVis or WH.Colors.vis
                local occ = isAI and WH.Colors.bOcc or WH.Colors.occ
                if slua.isValid(p.Mesh) then Apply(p.Mesh, vis, occ) end
                local av = p.CharacterAvatarComp2_BP or (p.getAvatarComponent2 and p:getAvatarComponent2())
                if av and av.GetMeshCompBySlot then
                    for _, s in ipairs(WH.Slots) do
                        local m = av:GetMeshCompBySlot(s)
                        if slua.isValid(m) then Apply(m, vis, occ) end
                    end
                end
                local wp = p.GetCurrentWeapon and p:GetCurrentWeapon()
                if slua.isValid(wp) and slua.isValid(wp.Mesh) then
                    Apply(wp.Mesh, vis, occ)
                end
            end
        end
    end)
end
WH.SetupConsole()
""".rstrip(), "init": "", "menu": [
        {"id": "WALLHACK", "name": "Wallhack", "val": 1, "type": "toggle"}]}


# ── enemy_counter ───────────────────────────────────────────────
@feature("enemy_counter", "Enemy counter HUD", deps=("menu",))
def _f_enemy_counter(c):
    return {"lua": """
local EC = { Timer = nil }

function EC.Loop()
    if _G.xvakuex_GetVal("ENEMY_COUNTER") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local pc = slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(pc) then return end
    local hud = pc:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID or 0
    local myPos = me:K2_GetActorLocation()
    if not myPos then return end
    local total, bots, real = 0, 0, 0
    local MAX = 900000000
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= myTeam then
            local pos = p:K2_GetActorLocation()
            if pos then
                local dx, dy, dz = pos.X - myPos.X, pos.Y - myPos.Y, pos.Z - myPos.Z
                if dx*dx + dy*dy + dz*dz <= MAX then
                    total = total + 1
                    local isBot = false
                    pcall(function() isBot = Game:IsAI(p) end)
                    if isBot then bots = bots + 1 else real = real + 1 end
                end
            end
        end
    end
    local text, color
    if total == 0 then
        text = "[ AREA SECURE ]"
        color = { R = 0, G = 255, B = 200, A = 255 }
    else
        text = string.format("ENEMIES: %d  (Bots: %d | Real: %d)", total, bots, real)
        color = total == 1 and { R = 255, G = 255, B = 0, A = 255 }
                           or { R = 255, G = 165, B = 0, A = 255 }
    end
    local off = { X = 0, Y = 0, Z = 35 }
    hud:AddDebugText(text, me, 1.1, off, off, color, true, false, true, nil, 1.2, true)
end

function EC.Start()
    if EC.Timer then return end
    local pc = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if slua.isValid(pc) and pc.AddGameTimer then
        EC.Timer = pc:AddGameTimer(1.0, true, function() pcall(EC.Loop) end)
    end
end
""".rstrip(), "init": "", "menu": [
        {"id": "ENEMY_COUNTER", "name": "Enemy Counter", "val": 1, "type": "toggle"}]}


# ── device_spoof ────────────────────────────────────────────────
@feature("device_spoof", "Device ID spoof")
def _f_device_spoof(c):
    return {"lua": """
local DSpoof = {}

local function FakeHex(n)
    local chars = "0123456789ABCDEF"
    local out = {}
    for i = 1, n do out[i] = chars:sub(math.random(1, #chars), math.random(1, #chars)) end
    return table.concat(out)
end

function DSpoof.Init()
    if DSpoof._done then return end
    DSpoof.fakeDevice  = FakeHex(32)
    DSpoof.fakeAndroid = FakeHex(16)
    DSpoof.fakeMac = string.format("%02X:%02X:%02X:%02X:%02X:%02X",
        math.random(0,255), math.random(0,255), math.random(0,255),
        math.random(0,255), math.random(0,255), math.random(0,255))
    DSpoof.fakeIMEI = "35" .. math.random(100000, 999999) .. math.random(100000, 999999)
    DSpoof._done = true

    pcall(function()
        local SI = import("SystemInfo")
        if not SI then return end
        local hooks = {
            GetDeviceID       = function() return DSpoof.fakeDevice end,
            GetUniqueDeviceId = function() return DSpoof.fakeDevice end,
            GetMacAddress     = function() return DSpoof.fakeMac end,
            GetAndroidId      = function() return DSpoof.fakeAndroid end,
            GetIMEI           = function() return DSpoof.fakeIMEI end,
            GetDeviceName     = function() return "Pixel 6" end,
        }
        for fn, repl in pairs(hooks) do
            if SI[fn] then SI[fn] = repl end
        end
    end)

    pcall(function()
        if not _G.TssSdk then return end
        if _G.TssSdk.GetDeviceInfo then
            _G.TssSdk.GetDeviceInfo = function()
                return {
                    deviceId = DSpoof.fakeDevice,
                    androidId = DSpoof.fakeAndroid,
                    mac = DSpoof.fakeMac,
                    imei = DSpoof.fakeIMEI,
                    model = "Pixel 6", brand = "google", sdkInt = 33,
                    fingerprint = "google/oriole/oriole:13/TQ1A.221205.011/2022120500:user/release-keys",
                }
            end
        end
    end)
end

DSpoof.Init()
""".rstrip(), "init": "", "menu": []}


# ── builder ─────────────────────────────────────────────────────
FORCED = ("menu", "bypass")   # ALWAYS injected

def _topo(ids):
    out, seen = [], set()
    def visit(i):
        if i in seen: return
        seen.add(i)
        for d in REGISTRY[i]["deps"]:
            visit(d)
        out.append(i)
    for i in ids:
        visit(i)
    return out

def _collect_menu(ids):
    entries, seen = [], set()
    for i in ids:
        if i == "menu":  continue
        for e in REGISTRY[i]["fn"]({}).get("menu", []):
            if e["id"] not in seen:
                seen.add(e["id"])
                entries.append(e)
    return entries

def build_mod(features, brand="DEVILSOUL", expiry=(2027, 1, 1), filename="DEVILSOUL.lua"):
    feats = list(dict.fromkeys(list(FORCED) + [f for f in features if f in REGISTRY]))
    order = _topo(feats)
    if "menu" not in order: order.insert(0, "menu")

    ctx = {"brand": brand, "expiry": expiry, "menu_entries": _collect_menu(order)}

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"-- {filename}\n"
        f"-- generated {ts}\n"
        f"-- brand: {brand}\n"
        f"-- features: {', '.join(order)}\n"
        f"-- forced: {', '.join(FORCED)}\n"
    )

    parts = [header]
    inits = []
    for fid in order:
        built = REGISTRY[fid]["fn"](ctx)
        parts.append(f"-- ── feature: {fid} ──\n{built['lua']}")
        if built["init"]:
            inits.append(built["init"])

    parts.append("-- ── main entry ──\nfunction _G.StartMod()")
    if "expiry" in order:
        parts.append("    if not _G.CheckExpiration() then _G.ShowExpiryPopup(true) return end")
    for line in inits:
        parts.append("    " + line)
    parts.append("end\n_G.StartMod()")
    parts.append('print("[DEVILSOUL] loaded — ' + ",".join(order) + '")')
    return "\n\n".join(parts) + "\n"

def list_features():
    return [(k, REGISTRY[k]["label"], REGISTRY[k]["deps"]) for k in sorted(REGISTRY)]