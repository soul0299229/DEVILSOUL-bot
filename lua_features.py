"""
lua_features.py — DEVILSOUL ELITE v5
Floating button panel (proven to render). No native menu injection.
"""
from __future__ import annotations
from datetime import datetime, timezone

REGISTRY = {}
def feature(fid, label, deps=(), menu=None):
    def deco(fn):
        REGISTRY[fid] = {"id": fid, "label": label, "deps": list(deps), "fn": fn, "menu": menu or []}
        return fn
    return deco

HEADER_API = r"""
_G.DS = _G.DS or {}
_G.DS.Ticks = {}
_G.DS.Slow = {}
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
@feature("menu", "Feature state")
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
    # ── SAB FEATURES ON ──
    on = {
        # ESP
        "esp_box","esp_skeleton","esp_line","esp_distance","esp_name",
        "esp_hp","esp_weapon","esp_radar","esp_vis","esp_fov_circle",
        # AIMBOT
        "aim_silent","aim_smooth","aim_bone","aim_pred","aim_recoil",
        "aim_autofire","aim_shotgun",
        # MAGIC BULLET
        "magic_full","magic_head","magic_neck","magic_body","magic_legs",
        "magic_custom","magic_hitbox","magic_safe",
        # CROSSHAIR
        "cross_cross","cross_dot","cross_circle","cross_tstyle","cross_rainbow",
        # SKINS
        "skin_weapon","skin_outfit","skin_vehicle","skin_parachute",
        "skin_emote","skin_deadbox","skin_killmsg",
        # MISC
        "wallhack","enemy_counter","fps165",
    }
    rows = ",\n    ".join(f'{{ id = "{i}", val = {1 if i in on else 0} }}' for i in ids)
    return {"lua": f"_G.DS_Features = {{\n    {rows}\n}}\n".rstrip()}
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
        "behavior","misconduct","teammatehurt","teamhurt","wallhack","esp",
        "anticheat","seccheck","integrity"}) do
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
                                   or lk:find("judge") or lk:find("kick")
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
@feature("antikick", "Anti-Kick")
def _f_antikick(c):
    return {"lua": r"""
pcall(function()
    local DS_ = require("GameLua.GameCore.Module.Subsystem.DisconnectSubsystem")
    if DS_ and DS_.OnDisconnect then
        local o = DS_.OnDisconnect
        DS_.OnDisconnect = function(self, reason, ...)
            local r = tostring(reason or ""):lower()
            if r:find("data error") or r:find("desync") then return end
            return o(self, reason, ...)
        end
    end
end)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# FLOATING BUTTON PANEL — proven render path
# ═════════════════════════════════════════════════════════════════
@feature("floating_menu", "Floating Menu Panel")
def _f_floating_menu(c):
    return {"lua": r"""
-- Devil Floating Menu - Red/Black Theme
local FM = { ready = false, main = nil, panel = nil, expanded = false, toggles = {} }
local BTN = "/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"

local ROWS = {
    { cat = "ESP", ids = {
        {"Box","esp_box"},{"Dist","esp_distance"},{"Name","esp_name"},{"Line","esp_line"},
        {"Vis","esp_vis"},{"HP","esp_hp"},{"Wep","esp_weapon"},{"Radar","esp_radar"},
    }},
    { cat = "AIM", ids = {
        {"Bone","aim_bone"},{"Silent","aim_silent"},{"Smooth","aim_smooth"},
        {"Pred","aim_pred"},{"Recoil","aim_recoil"},{"Auto","aim_autofire"},{"SG","aim_shotgun"},
    }},
    { cat = "MAG", ids = {
        {"Full","magic_full"},{"Head","magic_head"},{"Neck","magic_neck"},
        {"Body","magic_body"},{"Legs","magic_legs"},{"Safe","magic_safe"},
    }},
    { cat = "SKIN", ids = {
        {"Wep","skin_weapon"},{"Out","skin_outfit"},{"Veh","skin_vehicle"},{"Para","skin_parachute"},
    }},
    { cat = "MISC", ids = {
        {"Wall","wallhack"},{"Count","enemy_counter"},{"165","fps165"},
    }},
}

local function makeBtn(txt, x, y, w, h, onClick)
    local btn = nil
    pcall(function() btn = slua.loadUI(BTN) end)
    if not btn or not slua.isValid(btn) then return nil end
    pcall(function() require("game_frontend_hud").AddToContainer(UIContainers.Top, btn, 9500) end)
    pcall(function()
        if btn.RichText_Content then
            btn.RichText_Content:SetText(txt)
            local f = btn.RichText_Content.Font
            if f then f.Size = 12 btn.RichText_Content:SetFont(f) end
        end
    end)
    pcall(function()
        local WLL = import("WidgetLayoutLibrary")
        local slot = WLL.SlotAsCanvasSlot(btn)
        if slot then
            slot:SetAnchors(FAnchors(0, 0, 0, 0))
            slot:SetAlignment(FVector2D(0, 0))
            slot:SetPosition(FVector2D(x, y))
            slot:SetSize(FVector2D(w, h))
        end
    end)
    pcall(function() btn:SetWidgetVisibility(UEnums.ESlateVisibility.Visible) end)
    pcall(function() btn:SetRenderOpacity(0.95) end)
    if onClick then pcall(function() if btn.OnClicked then btn.OnClicked:Add(onClick) end end) end
    return btn
end

local function setColor(btn, on)
    local FC = import("LinearColor")
    local FSC = import("SlateColor")
    -- ON = Green, OFF = White
    local textCol = on and FSC(FC(0, 1, 0, 1)) or FSC(FC(1, 1, 1, 1))
    -- Background: Black (always)
    local bgCol = FC(0, 0, 0, 1)
    pcall(function() if btn.SetBackgroundColor then btn:SetBackgroundColor(bgCol) end end)
    pcall(function() if btn.RichText_Content then btn.RichText_Content:SetColorAndOpacity(textCol) end end)
end

function FM.Build()
    if FM.ready and FM.main and slua.isValid(FM.main) then return true end

    -- Main button "Devil" (Red text)
    FM.main = makeBtn("Devil", 20, 200, 160, 40, function()
        FM.expanded = not FM.expanded
        local vis = FM.expanded and UEnums.ESlateVisibility.Visible or UEnums.ESlateVisibility.Collapsed
        for _, b in ipairs(FM.toggles) do
            if b.w and slua.isValid(b.w) then
                pcall(function() b.w:SetWidgetVisibility(vis) end)
            end
        end
    end)
    if not FM.main then return false end
    
    -- Main button color: Red text, Black bg
    pcall(function()
        local FC = import("LinearColor")
        local FSC = import("SlateColor")
        if FM.main.SetBackgroundColor then FM.main:SetBackgroundColor(FC(0, 0, 0, 1)) end
        if FM.main.RichText_Content then FM.main.RichText_Content:SetColorAndOpacity(FSC(FC(1, 0, 0, 1))) end
    end)

    -- Toggle rows
    local startY = 244
    local rowH = 38
    local btnW = 68
    local btnH = 32
    for _, row in ipairs(ROWS) do
        local x = 20
        for _, item in ipairs(row.ids) do
            local lbl = item[1]
            local id = item[2]
            -- Hack Name: Red/Blue (using Red for category, Blue for toggle name) -> We'll set it via text color
            local btn = makeBtn(lbl, x, startY, btnW, btnH, function()
                local cur = _G.DS_Get(id)
                _G.DS_Set(id, cur == 1 and 0 or 1)
            end)
            if btn then
                table.insert(FM.toggles, { id = id, w = btn })
            end
            x = x + btnW + 4
            if x + btnW > 380 then
                x = 20
                startY = startY + btnH + 4
            end
        end
        startY = startY + rowH
    end

    for _, b in ipairs(FM.toggles) do
        if b.w and slua.isValid(b.w) then
            pcall(function() b.w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end)
        end
    end
    FM.ready = true
    return true
end

function FM.Tick()
    if FM.ready and FM.main and not slua.isValid(FM.main) then
        FM.ready = false
        FM.main = nil
        FM.toggles = {}
    end
    for _, b in ipairs(FM.toggles) do
        if b.w and slua.isValid(b.w) then
            setColor(b.w, _G.DS_Get(b.id) == 1)
        end
    end
end

if _G.DS_SlowReg then
    _G.DS_SlowReg("floating_menu", function()
        if not FM.ready then pcall(FM.Build) end
        if FM.ready then pcall(FM.Tick) end
    end)
end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ESP — uses SCREEN MARK system (proven to render)
# ═════════════════════════════════════════════════════════════════
@feature("esp_box", "Box ESP via Screen Marks")
def _f_esp_box(c):
    return {"lua": r"""
-- Uses game's native ScreenMark system (proven working with 9999 config).
-- Renders as 3D tracked markers on enemies that stay on screen.

local BOX = {}
pcall(function()
    local t = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
    local c = t.GetCurrentConfig("ScreenMarkConfig")
    if c then
        c[9997] = {
            UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
            MaxWidgetNum = 99, MaxShowDistance = 6000000,
            bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
            BindSocketName = "spinel_03", bUseLuaWorldSocketName = true,
            WorldPositionOffset = FVector(0, 0, 0), bNeedPreLoad = true, Priority = 2,
        }
    end
end)

local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)

function BOX.Tick()
    if _G.DS_Get("esp_box") ~= 1 then
        -- remove all marks
        if not IMT then return end
        for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
            if slua.isValid(e) and e.DS_BoxMark then
                pcall(function() IMT.ClientRemoveMapMark(e.DS_BoxMark) end)
                e.DS_BoxMark = nil
            end
        end
        return
    end
    if not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 100 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 and not e.DS_BoxMark then
                    pcall(function()
                        e.DS_BoxMark = IMT.ClientAddMapMark(9997, FVector(0, 0, 0), 0, "", 4, e)
                    end)
                elseif hp <= 0 and e.DS_BoxMark then
                    pcall(function() IMT.ClientRemoveMapMark(e.DS_BoxMark) end)
                    e.DS_BoxMark = nil
                end
            end
        end
    end
end
if _G.DS_SlowReg then _G.DS_SlowReg("esp_box", BOX.Tick) end
""".rstrip()}


@feature("esp_distance", "Distance ESP via Screen Marks")
def _f_esp_distance(c):
    return {"lua": r"""
local DIST = {}
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
local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)
function DIST.Tick()
    if _G.DS_Get("esp_distance") ~= 1 then
        if not IMT then return end
        for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
            if slua.isValid(e) and e.DS_DistMark then
                pcall(function() IMT.ClientRemoveMapMark(e.DS_DistMark) end)
                e.DS_DistMark = nil
            end
        end
        return
    end
    if not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 100 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 and not e.DS_DistMark then
                    pcall(function()
                        e.DS_DistMark = IMT.ClientAddMapMark(9999, FVector(0, 0, 0), 0, "", 4, e)
                    end)
                elseif hp <= 0 and e.DS_DistMark then
                    pcall(function() IMT.ClientRemoveMapMark(e.DS_DistMark) end)
                    e.DS_DistMark = nil
                end
            end
        end
    end
end
if _G.DS_SlowReg then _G.DS_SlowReg("esp_distance", DIST.Tick) end
""".rstrip()}


@feature("esp_name", "Name ESP via HUD")
def _f_esp_name(c):
    return {"lua": r"""
function _G.DS_NameTick()
    if _G.DS_Get("esp_name") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 100 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 then
                    local nm = "Enemy"
                    pcall(function() nm = e:GetPlayerNameSafety() or "Enemy" end)
                    local dist = 0 pcall(function() dist = me:GetDistanceTo(e) / 100 end)
                    local txt = string.format("%s [%dm]", nm, math.floor(dist))
                    local off = {X=0, Y=0, Z=120}
                    hud:AddDebugText(txt, e, 0.1, off, off, {R=255,G=255,B=0,A=255}, true, false, true, nil, 0.85, true)
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_name", _G.DS_NameTick)
""".rstrip()}


@feature("esp_vis", "Visibility ESP via HUD")
def _f_esp_vis(c):
    return {"lua": r"""
function _G.DS_VisTick()
    if _G.DS_Get("esp_vis") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 100 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 then
                    local vis = false
                    pcall(function() vis = PC:LineOfSightTo(e, import("Vector")(0,0,0), false) end)
                    local col = vis and {R=0,G=255,B=0,A=255} or {R=255,G=0,B=0,A=255}
                    local off = {X=0, Y=0, Z=100}
                    hud:AddDebugText("\u25CF", e, 0.1, off, off, col, true, false, true, nil, 1.4, true)
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_vis", _G.DS_VisTick)
""".rstrip()}


@feature("esp_line", "Snap Lines")
def _f_esp_line(c):
    return {"lua": r"""
-- Snap line indicator via HUD marks (limitation: uses text dots along line)
function _G.DS_LineTick()
    if _G.DS_Get("esp_line") ~= 1 then return end
    -- placeholder — uses esp_vis dots in a chain
end
_G.DS_SlowReg("esp_line", _G.DS_LineTick)
""".rstrip()}


@feature("esp_hp", "HP text")
def _f_esp_hp(c):
    return {"lua": r"""
function _G.DS_HPTick()
    if _G.DS_Get("esp_hp") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 0 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 then
                    local col = hp > 60 and {R=0,G=255,B=0,A=255} or (hp > 30 and {R=255,G=200,B=0,A=255} or {R=255,G=0,B=0,A=255})
                    local txt = string.format("%d HP", math.floor(hp))
                    local off = {X=0, Y=0, Z=110}
                    hud:AddDebugText(txt, e, 0.1, off, off, col, true, false, true, nil, 0.75, true)
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_hp", _G.DS_HPTick)
""".rstrip()}


@feature("esp_weapon", "Weapon name text")
def _f_esp_weapon(c):
    return {"lua": r"""
function _G.DS_WepTick()
    if _G.DS_Get("esp_weapon") ~= 1 then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 0 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 then
                    local wname = ""
                    pcall(function()
                        local w = e.CurrentWeapon or (e.GetCurrentWeapon and e:GetCurrentWeapon())
                        if slua.isValid(w) and w.GetWeaponName then wname = w:GetWeaponName() end
                    end)
                    if wname ~= "" then
                        local off = {X=0, Y=0, Z=135}
                        hud:AddDebugText(wname, e, 0.1, off, off, {R=255,G=200,B=50,A=255}, true, false, true, nil, 0.7, true)
                    end
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_weapon", _G.DS_WepTick)
""".rstrip()}


@feature("esp_radar", "MiniMap Radar")
def _f_esp_radar(c):
    return {"lua": r"""
local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)
pcall(function()
    local t = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
    local c = t.GetCurrentConfig("ScreenMarkConfig")
    if c then
        c[9998] = {
            UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
            MaxWidgetNum = 99, MaxShowDistance = 6000000,
            bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
            BindSocketName = "head", bUseLuaWorldSocketName = true,
            WorldPositionOffset = FVector(0, 0, 30), bNeedPreLoad = true, Priority = 2,
        }
    end
end)
function _G.DS_RadarTick()
    if _G.DS_Get("esp_radar") ~= 1 then
        if not IMT then return end
        for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
            if slua.isValid(e) and e.DS_Radar then
                pcall(function() IMT.ClientRemoveMapMark(e.DS_Radar) end)
                e.DS_Radar = nil
            end
        end
        return
    end
    if not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me then
            local t = nil pcall(function() t = e.TeamID end)
            local skip = false
            if myTeam and myTeam ~= 0 and t and t ~= 0 and t == myTeam then skip = true end
            if not skip then
                local hp = 100 pcall(function() if e.Health then hp = e.Health end end)
                if hp > 0 and not e.DS_Radar then
                    pcall(function() e.DS_Radar = IMT.ClientAddMapMark(9998, FVector(0, 0, 0), 0, "", 4, e) end)
                elseif hp <= 0 and e.DS_Radar then
                    pcall(function() IMT.ClientRemoveMapMark(e.DS_Radar) end)
                    e.DS_Radar = nil
                end
            end
        end
    end
end
_G.DS_SlowReg("esp_radar", _G.DS_RadarTick)
""".rstrip()}


@feature("esp_fov_circle", "FOV circle")
def _f_esp_fov_circle(c):
    return {"lua": r"""
function _G.DS_FOVTick()
    -- visual-only; skip implementation
end
""".rstrip()}


@feature("esp_skeleton", "Skeleton placeholder")
def _f_esp_skeleton(c):
    return {"lua": r"""
function _G.DS_SkelTick()
    -- visual-only; skip implementation (caused freezes)
end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# AIMBOT — off by default
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
local function MOVING(me)
    local v = nil pcall(function() if me.GetVelocity then v = me:GetVelocity() end end)
    if v and (v.X*v.X + v.Y*v.Y) > 90000 then return true end
    return false
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
    PC:SetControlRotation({ Pitch = cur.Pitch + dp*pct, Yaw = cur.Yaw + dy*pct, Roll = cur.Roll }, "DS_Aim")
end
"""


@feature("aim_bone", "Bone Lock")
def _f_aim_bone(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickBone()
    if _G.DS_Get("aim_bone") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    if MOVING(me) then return end
    local now = os.clock()
    if now - CD < 0.10 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 150)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.40)
    CD = now
end
_G.DS_Reg("aim_bone", AIM.TickBone)
""".rstrip()}


@feature("aim_silent", "Silent Aim")
def _f_aim_silent(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickSilent()
    if _G.DS_Get("aim_silent") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    if MOVING(me) then return end
    local now = os.clock()
    if now - CD < 0.10 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 220)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.30)
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
    if MOVING(me) then return end
    local now = os.clock()
    if now - CD < 0.08 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "spine_03", 220)
    if not tgt or not bone then return end
    local cm = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(cm) then return end
    local camLoc = cm:GetCameraLocation()
    local rot = import("KismetMathLibrary").FindLookAtRotation(camLoc, bone)
    SMOOTH_SET(PC, rot, 0.25)
    CD = now
end
_G.DS_Reg("aim_smooth", AIM.TickSmooth)
""".rstrip()}


@feature("aim_pred", "Prediction")
def _f_aim_pred(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickPred()
    if _G.DS_Get("aim_pred") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    if MOVING(me) then return end
    local now = os.clock()
    if now - CD < 0.10 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local tgt, bone = SCREEN_PICK(PC, "head", 250)
    if not tgt or not bone then return end
    local vel = nil pcall(function() if tgt.GetVelocity then vel = tgt:GetVelocity() end end)
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
    SMOOTH_SET(PC, rot, 0.35)
    CD = now
end
_G.DS_Reg("aim_pred", AIM.TickPred)
""".rstrip()}


@feature("aim_recoil", "Recoil")
def _f_aim_recoil(c):
    return {"lua": AIM_HEADER + r"""
local CD = 0
function AIM.TickRecoil()
    if _G.DS_Get("aim_recoil") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    if MOVING(me) then return end
    local now = os.clock()
    if now - CD < 0.06 then return end
    local PC = GPC() if not slua.isValid(PC) then return end
    local cur = PC:GetControlRotation()
    if not cur then return end
    cur.Pitch = cur.Pitch - 0.15
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
    if MOVING(me) then return end
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
                if d < 50 then fire = true break end
            end
        end
    end
    if fire then
        pcall(function()
            me.bIsWeaponFiring = true
            if me.SetIsWeaponFiring then me:SetIsWeaponFiring(true) end
        end)
    end
end
_G.DS_Reg("aim_autofire", AIM.TickAutoFire)
""".rstrip()}


@feature("aim_shotgun", "Shotgun auto")
def _f_aim_shotgun(c):
    return {"lua": AIM_HEADER + r"""
function AIM.TickSG()
    if _G.DS_Get("aim_shotgun") ~= 1 then return end
    local me = GC() if not slua.isValid(me) then return end
    if MOVING(me) then return end
    local w = me.CurrentWeapon or (me.GetCurrentWeapon and me:GetCurrentWeapon())
    if not slua.isValid(w) then return end
    local nm = "" pcall(function() nm = (w.GetWeaponName and w:GetWeaponName()) or "" end)
    if not (nm:find("S686") or nm:find("S1897") or nm:find("S12") or nm:find("DBS")) then return end
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
# MAGIC
# ═════════════════════════════════════════════════════════════════
MAGIC_HEADER = r"""
local MB = _G.DS_MB or {}
_G.DS_MB = MB
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


@feature("magic_full", "Magic Full")
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


@feature("magic_custom", "Magic Custom")
def _f_magic_custom(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickCustom()
    if _G.DS_Get("magic_custom") ~= 1 then return end
    MB.force = function()
        if math.random() < 0.6 then
            local E = import("EAvatarDamagePosition")
            return E and E.BigHead or nil
        end
    end
end
_G.DS_Reg("magic_custom", MB.TickCustom)
""".rstrip()}


@feature("magic_hitbox", "Hitbox")
def _f_magic_hitbox(c):
    return {"lua": r"-- neutral placeholder"}


@feature("magic_safe", "Safe Magic")
def _f_magic_safe(c):
    return {"lua": MAGIC_HEADER + r"""
function MB.TickSafe()
    if _G.DS_Get("magic_safe") ~= 1 then return end
    MB.force = function()
        local r = math.random()
        if r < 0.4 then
            local E = import("EAvatarDamagePosition")
            return E and E.BigHead or nil
        elseif r < 0.8 then
            return "spine_03"
        end
    end
end
_G.DS_Reg("magic_safe", MB.TickSafe)
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# CROSSHAIR via HUD dots
# ═════════════════════════════════════════════════════════════════
@feature("cross_cross", "Crosshair")
def _f_cross_cross(c):
    return {"lua": r"""
function _G.DS_CrossTick()
    if _G.DS_Get("cross_cross") ~= 1 then return end
    local PC = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(PC) then return end
    local hud = PC:GetHUD()
    if not slua.isValid(hud) then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    -- crosshair via HUD markers around center
    -- (skip complex — user has native crosshair)
end
_G.DS_SlowReg("cross_cross", _G.DS_CrossTick)
""".rstrip()}


@feature("cross_dot", "Dot crosshair")
def _f_cross_dot(c):
    return {"lua": r"-- placeholder"}


@feature("cross_circle", "Circle crosshair")
def _f_cross_circle(c):
    return {"lua": r"-- placeholder"}


@feature("cross_tstyle", "T crosshair")
def _f_cross_tstyle(c):
    return {"lua": r"-- placeholder"}


@feature("cross_rainbow", "Rainbow crosshair")
def _f_cross_rainbow(c):
    return {"lua": r"-- placeholder"}


# ═════════════════════════════════════════════════════════════════
# SKIN (basic)
# ═════════════════════════════════════════════════════════════════
@feature("skin_weapon", "Weapon skin")
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


@feature("skin_outfit", "Outfit skin")
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


@feature("skin_vehicle", "Vehicle skin")
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


@feature("skin_parachute", "Parachute skin")
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


@feature("skin_emote", "Emote unlock")
def _f_skin_emote(c):
    return {"lua": r"""
pcall(function()
    local le = require("GameLua.Mod.Library.GamePlay.Avatar.Emote.logic_emote")
    if le and le.IsEmoteExist and not le._ds_hook then
        le._ds_hook = true
        local o = le.IsEmoteExist
        le.IsEmoteExist = function(id)
            if _G.DS_Get("skin_emote") == 1 then return true end
            return o(id)
        end
    end
end)
""".rstrip()}


@feature("skin_deadbox", "Deadbox skin")
def _f_skin_deadbox(c):
    return {"lua": r"-- placeholder"}


@feature("skin_killmsg", "Kill message")
def _f_skin_killmsg(c):
    return {"lua": r"-- placeholder"}


# ═════════════════════════════════════════════════════════════════
@feature("wallhack", "Wallhack")
def _f_wallhack(c):
    return {"lua": r"""
local WH = { ready = false, colors = {
    vis = import("LinearColor")(255, 255, 0, 100),
    occ = import("LinearColor")(0, 255, 255, 100),
} }
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
_G.DS_SlowReg("wallhack", WH.Tick)
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


@feature("fps165", "165 FPS")
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
""".rstrip()}


@feature("expiry", "Expiry")
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


@feature("tick_manager", "Tick Manager")
def _f_tick_manager(c):
    return {"lua": r"""
local TM = { started = false, boot = nil }
local function runTicks() for _, f in pairs(_G.DS.Ticks) do pcall(f) end end
local function runSlow() for _, f in pairs(_G.DS.Slow) do pcall(f) end end
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
FORCED_HEAD = ("menu", "bypass", "antikick", "floating_menu")
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
    
# ═════════════════════════════════════════════════════════════════
# DEVIL COMMAND SYSTEM (Chat Commands → Lua Builder)
# ═════════════════════════════════════════════════════════════════
import random as _random
import os as _os

# Devil menu ka floating button ka naam aur brand
DEVIL_BRAND = "Devil"
DEVIL_EXPIRY = (2027, 1, 1)
OUTPUT_DIR = "./build"  # Output folder

# Ensure output folder exists
_os.makedirs(OUTPUT_DIR, exist_ok=True)


def _write_lua(content, filename):
    """Write generated Lua to file."""
    path = _os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[DEVIL] ✅ File ban gayi: {path}")
    return path


def command_all():
    """Build Lua with ALL registered features."""
    all_feats = [k for k in REGISTRY.keys()
                 if k not in ("menu", "expiry", "tick_manager",
                              "bypass", "antikick", "floating_menu")]
    # Force essentials
    all_feats = ["menu", "bypass", "antikick", "floating_menu"] + all_feats
    lua = build_mod(
        features=all_feats,
        brand=DEVIL_BRAND,
        expiry=DEVIL_EXPIRY,
        filename="Devil_ALL.lua"
    )
    return _write_lua(lua, "Devil_ALL.lua")


def command_random():
    """Build Lua with ONE random feature (plus essentials)."""
    optional = [k for k in REGISTRY.keys()
                if k not in ("menu", "expiry", "tick_manager",
                             "bypass", "antikick", "floating_menu")]
    if not optional:
        print("[DEVIL] ❌ Koi feature registered nahi hai.")
        return None
    picked = _random.choice(optional)
    print(f"[DEVIL] 🎲 Random pick: {picked}")
    feats = ["menu", "bypass", "antikick", "floating_menu", picked]
    lua = build_mod(
        features=feats,
        brand=DEVIL_BRAND,
        expiry=DEVIL_EXPIRY,
        filename=f"Devil_{picked}.lua"
    )
    return _write_lua(lua, f"Devil_{picked}.lua")


def command_feature(feature_name: str):
    """Build Lua with a SPECIFIC feature."""
    feature_name = feature_name.strip().lower()
    # Try to find by id or label
    found = None
    for fid, meta in REGISTRY.items():
        if fid.lower() == feature_name or meta["label"].lower() == feature_name:
            found = fid
            break
    if not found:
        print(f"[DEVIL] ❌ Feature nahi mila: {feature_name}")
        print(f"[DEVIL] Available: {', '.join(sorted(REGISTRY.keys()))}")
        return None
    print(f"[DEVIL] 🎯 Feature mil gaya: {found}")
    feats = ["menu", "bypass", "antikick", "floating_menu", found]
    lua = build_mod(
        features=feats,
        brand=DEVIL_BRAND,
        expiry=DEVIL_EXPIRY,
        filename=f"Devil_{found}.lua"
    )
    return _write_lua(lua, f"Devil_{found}.lua")


def handle_command(text: str):
    """
    Main dispatcher. Chat me aane wala text parse karta hai.
    
    Usage:
        /all
        /random
        /feature esp_box
    """
    if not text or not text.startswith("/"):
        return None
    text = text.strip()
    low = text.lower()

    if low == "/all":
        return command_all()
    elif low == "/random":
        return command_random()
    elif low.startswith("/feature"):
        parts = text.split(None, 1)
        if len(parts) < 2:
            print("[DEVIL] ⚠️ Usage: /feature <naam>")
            print(f"[DEVIL] Available: {', '.join(sorted(REGISTRY.keys()))}")
            return None
        return command_feature(parts[1])
    else:
        print(f"[DEVIL] ❌ Unknown command: {text}")
        return None


# ═════════════════════════════════════════════════════════════════
# DEVIL FLOATING MENU OVERRIDE
# (Chat ke bajaye, agar koi direct build karna chahe)
# ═════════════════════════════════════════════════════════════════
def build_devil_menu(features=None):
    """
    Shortcut: Devil brand + floating menu ke sath build.
    Agar features=None, saare features use honge.
    """
    if features is None:
        features = [k for k in REGISTRY.keys()
                    if k not in ("menu", "expiry", "tick_manager")]
    feats = ["menu", "bypass", "antikick", "floating_menu"] + \
            [f for f in features if f not in ("menu", "bypass", "antikick", "floating_menu")]
    lua = build_mod(
        features=feats,
        brand=DEVIL_BRAND,
        expiry=DEVIL_EXPIRY,
        filename="Devil_Menu.lua"
    )
    return _write_lua(lua, "Devil_Menu.lua")


# ═════════════════════════════════════════════════════════════════
# CLI (agar terminal se chalana ho)
# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        handle_command(cmd)
    else:
        print("=" * 50)
        print("  DEVILSOUL ELITE v5 - Command Interface")
        print("=" * 50)
        print("Commands:")
        print("  /all              → Saare features wali Lua file")
        print("  /random           → Random 1 feature wali file")
        print("  /feature <naam>   → Specific feature wali file")
        print()
        print("Available features:")
        for fid in sorted(REGISTRY.keys()):
            print(f"  • {fid:20s} — {REGISTRY[fid]['label']}")
        print()
        while True:
            try:
                user_in = input("Devil> ").strip()
                if user_in.lower() in ("exit", "quit", "q"):
                    break
                handle_command(user_in)
            except (KeyboardInterrupt, EOFError):
                break