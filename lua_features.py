"""
lua_features.py — DEVILSOUL ELITE
35-Layer Firewall + Multi-Variant ESP/Aimbot/Magic/Crosshair/Skin
Drop-in for bot.py.
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
_G.DS_Cfg = _G.DS_Cfg or {}

function _G.DS_Reg(n, f) if type(f) == "function" then _G.DS.Ticks[n] = f end end
function _G.DS_SlowReg(n, f) if type(f) == "function" then _G.DS.Slow[n] = f end end
function _G.DS_Get(id)
    for _, f in ipairs(_G.DS_Features or {}) do if f.id == id then return f.val end end
    return 0
end
"""

# ═════════════════════════════════════════════════════════════════
# MENU
# ═════════════════════════════════════════════════════════════════
@feature("menu", "Feature toggle table")
def _f_menu(c):
    rows = ",\n    ".join(
        f'{{ id = "{e["id"]}", name = "{e["name"]}", val = {e["val"]}, type = "{e["type"]}"'
        + (f', options = {{{", ".join(repr(o) for o in e["options"])}}}' if e.get("options") else "")
        + " }" for e in c["menu_entries"])
    return {"lua": f"""
_G.DS_Features = {{
    {rows}
}}

function _G.DS_Set(id, val)
    for _, f in ipairs(_G.DS_Features) do
        if f.id == id then f.val = val return true end
    end
    return false
end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# 35-LAYER FIREWALL
# ═════════════════════════════════════════════════════════════════
@feature("bypass", "35-Layer Report / Detection Firewall")
def _f_bypass(c):
    return {"lua": r"""
-- ═══════════════════════════════════════════════════════════════
-- DEVILSOUL 35-LAYER FIREWALL
-- Report-proof from lobby-wide + teammate reports
-- ═══════════════════════════════════════════════════════════════
local DS = _G.DS
DS.firewall = DS.firewall or { active = true, layers = {} }

local nop = function() end
local T = function() return true end
local F = function() return false end
local Z = function() return 0 end
local E = function() return {} end

local function mark(n, name) DS.firewall.layers[n] = name end
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

-- ─── L01 — Report send killer ────────────────────────────────
pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...) if isRep(n) then return nil end return o(n, ...) end
    end
end)
mark(1, "ReportSendKiller")

-- ─── L02 — RPC send killer ───────────────────────────────────
pcall(function()
    if _G.SendRPC then
        local o = _G.SendRPC
        _G.SendRPC = function(n, ...) if isRep(n) then return end return o(n, ...) end
    end
end)
mark(2, "RPCSendKiller")

-- ─── L03 — ProtocolManager send hook ─────────────────────────
pcall(function()
    local PM = require("client.network.Protocol.ProtocolManager")
    if PM and PM.Send then
        local o = PM.Send
        PM.Send = function(self, n, ...) if isRep(n) then return end return o(self, n, ...) end
    end
end)
mark(3, "ProtocolSendKiller")

-- ─── L04 — NetworkService send hook ──────────────────────────
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
mark(4, "NetworkServiceKiller")

-- ─── L05 — GameplayCallbacks nuke ────────────────────────────
pcall(function()
    _G.GameplayCallbacks = _G.GameplayCallbacks or {}
    local GC = _G.GameplayCallbacks
    for _, k in ipairs({
        "ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow","ReportFireArms",
        "ReportVerifyInfoFlow","ReportMrpcsFlow","ReportPlayerBehavior","ReportTeammatHurt",
        "ReportTeammathurt","ReportMisKillByTeammate","ReportForbitPick",
        "ReportPlayerMoveRoute","ReportPlayerPosition","ReportVehicleMoveFlow",
        "ReportSecRegameMovingFlow","ReportParachuteData","ReportAimFlow","ReportHitFlow",
        "ReportWallHack","ReportWallhack","ReportAimbot","ReportSpeedHack",
        "ReportMagicBullet","ReportAbnormalMaterial","ReportDepthTestChange",
        "ReportMemoryException","ReportMaterialScan","ReportShaderOverride",
        "ReportCircleFlow","ReportDSCircleFlow","ReportJumpFlow","ReportAIStrategyInfo",
        "ReportPlayerKillFlow","ClientSecPlayerKillFlow","CheckReportSecAttackFlow",
        "CheckReportSecAttackFlowWithAttackFlow","OnPlayerRPCValidateFailed",
        "OnPlayerActorChannelError","OnPlayerSpectateException","OnShutdownAfterError"
    }) do GC[k] = nop end
end)
mark(5, "GameplayCallbacksNuke")

-- ─── L06 — Report patterns across package.loaded ─────────────
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
mark(6, "PackageLoadedScrub")

-- ─── L07 — Global report functions nuke ──────────────────────
pcall(function()
    for _, k in ipairs({"ReportESPBox","ReportESPHealth","ReportMiniMapESP",
        "ReportEnemyFrameUI","ReportMarkCreated","ReportMarkDestroyed",
        "MarkSuspiciousESP","OnScreenMarkAdd","OnScreenMarkRemove",
        "ReportDistanceMarker","ReportWallhackESP","SendESPData","UploadESPInfo"}) do
        if _G[k] then _G[k] = nop end
    end
end)
mark(7, "GlobalReportScrub")

-- ─── L08 — Subsystem silencer ────────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if not sm or sm.__ds_sil then return end
    local realGet = sm.Get
    local targets = {
        "ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem",
        "ClientAimTrackingSubsystem","ClientAntiCheatSubsystem",
        "ClientHawkEyePatrolSubsystem","DSHawkEyePatrolSubsystem",
        "CoronaLabSubsystem","PlayerSecurityInfoSubsystem",
        "ClientSecMrpcsFlowSubsystem","MrpcsFlowSubsystem",
        "ShootVerifySubSystemClient","MemoryCheckSubsystem","SpeedCheckSubsystem",
        "WallCheckSubsystem","BehaviorScoreSubsystem","AFKReportorSubsystem",
        "AvatarExceptionSubsystem","GameReportSubsystem","SwiftHawkSubsystem",
        "HeartbeatSubsystem","ClientReportPlayerSubsystem","DSReportPlayerSubsystem",
        "ModifierExceptionSubsystem","SimulateCharacterSubsystem",
        "ClientRenderCheckSubsystem","ClientMemoryGuardSubsystem",
        "ClientKernelCheckSubsystem","FileCheckSubsystem","PakCheckSubsystem",
        "IntegrityCheckSubsystem","PlayerReportSubsystem","KickVoteSubsystem",
        "TeammateHurtReportSubsystem","AccusePlayerSubsystem"
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
                    if n == "ClientWallhackDetectionSubsystem" then s.IsVisionNormal = T s.GetVisibilityRate = function() return math.random(62,78) end
                    elseif n == "ClientESPDetectionSubsystem" then s.HasESP = F s.CheckOverlay = function() return "clean" end
                    elseif n == "ClientAimTrackingSubsystem" then s.GetAimData = function() return {accuracy=math.random(42,58),headshotRate=math.random(12,28),trackingTime=math.random(200,400),aimLockCount=0} end s.IsAimNormal = T
                    elseif n == "ClientMemoryGuardSubsystem" then s.IsMemoryClean = function() return true,{code=0} end s.ScanResult = function() return "clean" end
                    elseif n == "ShootVerifySubSystemClient" then s.OnShootVerifyFailed = nop s.VerifyShot = T
                    elseif n == "ClientHawkEyePatrolSubsystem" then s.IsBeingWatched = F s.GetSpectatorCount = Z s.GetPatrolData = E
                    elseif n == "GameReportSubsystem" or n == "ClientReportPlayerSubsystem" then s.SubmitReport = T s.OnReportReceived = nop end
                    s.__ds_sil = true
                    break
                end
            end
        end
        return s
    end
    sm.__ds_sil = true
end)
mark(8, "SubsystemSilencer")

-- ─── L09 — Deep packet filter ────────────────────────────────
pcall(function()
    if not NetUtil or not NetUtil.SendPacket then return end
    local o = NetUtil.SendPacket
    NetUtil.SendPacket = function(n, ...)
        local a = {...}
        for _, x in ipairs(a) do if isRep(x) then return nil end end
        return o(n, ...)
    end
end)
mark(9, "DeepPacketFilter")

-- ─── L10 — Socket write filter ───────────────────────────────
pcall(function()
    local S = require("common.socket_util")
    if S and S.Send then
        local o = S.Send
        S.Send = function(self, d, ...) if isRep(d) then return end return o(self, d, ...) end
    end
end)
mark(10, "SocketWriteFilter")

-- ─── L11 — Behavior spoof ────────────────────────────────────
pcall(function()
    local GRU = package.loaded["GameLua.Mod.BaseMod.GamePlay.GameReport.GameReportUtils"]
    if GRU and GRU.ReportGameResult then
        local o = GRU.ReportGameResult
        GRU.ReportGameResult = function(self, d)
            if d then d.accuracy=0.30+math.random()*0.18 d.headshotRate=0.08+math.random()*0.12 d.aimLockCount=0 d.suspicionScore=0 d.integrityScore=math.random(85,98) end
            return o(self, d)
        end
    end
end)
mark(11, "BehaviorSpoof")

-- ─── L12 — Battle result scramble ────────────────────────────
pcall(function()
    local SR = package.loaded["GameLua.Mod.BaseMod.Client.BattleResult.ProcessBase.BattleResultShowResultLogic"]
    if SR and SR.ReceiveData then
        local o = SR.ReceiveData
        SR.ReceiveData = function(self, r)
            if r then r.Accuracy=(30+math.random(18))/100 r.HeadShotRate=(8+math.random(12))/100 end
            return o(self, r)
        end
    end
end)
mark(12, "BattleResultScramble")

-- ─── L13 — Screenshot blocker ────────────────────────────────
pcall(function()
    local SS = import("ScreenshotManager")
    if SS then SS.RequestScreenshot = F SS.HasPendingScreenshot = F SS.IsCapturing = F end
    local S2 = import("ScreenshotMaker") or import("ScreenshotMTDer")
    if S2 then S2.MakePicture = function() return "" end S2.ReMakePicture = function() return "" end S2.HasCaptured = T end
end)
mark(13, "ScreenshotBlocker")

-- ─── L14 — Replay blocker ────────────────────────────────────
pcall(function()
    local RP = import("ReplayManager") or _G.ReplayManager
    if RP then RP.StartRecord = nop RP.StopRecord = nop RP.SaveReplay = F end
end)
mark(14, "ReplayBlocker")

-- ─── L15 — Spectator count spoof ─────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local ss = sm:Get("ClientHawkEyePatrolSubsystem") or sm:Get("DSHawkEyePatrolSubsystem")
        if ss then ss.IsBeingWatched = F ss.GetSpectatorCount = Z ss.GetWatchers = E end
    end
end)
mark(15, "SpectatorSpoof")

-- ─── L16 — Spectator data block ──────────────────────────────
pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...)
            local p = tostring(n or ""):lower()
            if p:find("spectat") or p:find("replay") or p:find("record") then return nil end
            return o(n, ...)
        end
    end
end)
mark(16, "SpectatorDataBlock")

-- ─── L17 — Match stat scramble ───────────────────────────────
pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...)
            local p = tostring(n or ""):lower()
            if p:find("position") or p:find("location") or p:find("coord") then
                local a = {...}
                for _, x in ipairs(a) do
                    if type(x) == "table" and x.X then x.X = x.X + (math.random() - 0.5) * 2 x.Y = x.Y + (math.random() - 0.5) * 2 end
                end
            end
            return o(n, ...)
        end
    end
end)
mark(17, "MatchStatScramble")

-- ─── L18 — Device fingerprint rotate ─────────────────────────
pcall(function()
    local ch = "0123456789ABCDEF"
    local function g(n) local s = "" for i=1,n do s = s..ch:sub(math.random(1,#ch),math.random(1,#ch)) end return s end
    _G.DS_FakeDev = g(32)
    _G.DS_FakeAnd = g(16)
    _G.DS_FakeMac = string.format("%02X:%02X:%02X:%02X:%02X:%02X", math.random(0,255),math.random(0,255),math.random(0,255),math.random(0,255),math.random(0,255),math.random(0,255))
    _G.DS_FakeIMEI = "35"..math.random(100000,999999)..math.random(100000,999999)
    local SI = import("SystemInfo")
    if SI then
        if SI.GetDeviceID then SI.GetDeviceID = function() return _G.DS_FakeDev end end
        if SI.GetUniqueDeviceId then SI.GetUniqueDeviceId = function() return _G.DS_FakeDev end end
        if SI.GetMacAddress then SI.GetMacAddress = function() return _G.DS_FakeMac end end
        if SI.GetAndroidId then SI.GetAndroidId = function() return _G.DS_FakeAnd end end
        if SI.GetIMEI then SI.GetIMEI = function() return _G.DS_FakeIMEI end end
        if SI.GetDeviceName then SI.GetDeviceName = function() return "Pixel 6" end end
    end
end)
mark(18, "DeviceFingerprintRotate")

-- ─── L19 — TssSdk neutralizer ────────────────────────────────
pcall(function()
    local t = _G.TssSdk
    if t then
        t.GetFileMD5 = function() return "" end t.VerifyFileSignature = T t.CheckIntegrity = T
        t.ScanMemory = function() return true, {} end t.IsEmulator = F t.OnRecvData = nop
        t.GetDeviceInfo = function() return {deviceId=_G.DS_FakeDev,androidId=_G.DS_FakeAnd,mac=_G.DS_FakeMac,imei=_G.DS_FakeIMEI,model="Pixel 6",brand="google",sdkInt=33} end
    end
end)
mark(19, "TssSdkNeutralizer")

-- ─── L20 — HiggsBoson disabler ───────────────────────────────
pcall(function()
    local h = package.loaded["GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent"]
    if h then h.bMHActive = false h.bCallPreReplication = false h.ControlMHActive = nop h.StartAvatarCheck = nop if h.BlackList then for k in pairs(h.BlackList) do h.BlackList[k] = nil end end end
    if _G.AvatarCheckCallback then _G.AvatarCheckCallback.StartAvatarCheck = nop _G.AvatarCheckCallback.OnReportItemID = nop end
    _G.BlackList = {}
end)
mark(20, "HiggsBosonDisable")

-- ─── L21 — Kernel check spoof ────────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local k = sm:Get("ClientKernelCheckSubsystem")
        if k then k.IsKernelClean = T k.GetKernelVersion = function() return "4.19.150-generic" end k.IsBootloaderLocked = T end
    end
end)
mark(21, "KernelSpoof")

-- ─── L22 — Memory guard spoof ────────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local m = sm:Get("ClientMemoryGuardSubsystem")
        if m then m.IsMemoryClean = function() return true, {code=0} end m.ScanResult = function() return "clean" end end
    end
end)
mark(22, "MemoryGuardSpoof")

-- ─── L23 — Pak integrity killer ──────────────────────────────
pcall(function()
    local PS = package.loaded["GameLua.GameCore.Module.Subsystem.PakFileSubsystem"]
    if PS then PS.CheckPakIntegrity = nop PS.ReportPakMismatch = nop end
    local FP = import("FPakFile") or import("FPakPlatformFile")
    if FP then FP.GetPakEntries = E FP.GetPakFolders = E FP.FindFileInPakFiles = F end
end)
mark(23, "PakIntegrityKiller")

-- ─── L24 — File hash spoofer ─────────────────────────────────
pcall(function()
    local FH = import("FFileHelper")
    if FH then
        if FH.GetFileSize then local o = FH.GetFileSize FH.GetFileSize = function(p) local s = o(p) if p and tostring(p):lower():match(".pak") then return 2000000000 end return s end end
        if FH.SaveStringToFile then local o = FH.SaveStringToFile FH.SaveStringToFile = function(s, p, ...) if p and tostring(p):lower():match(".pak") then return true end return o(s, p, ...) end end
    end
end)
mark(24, "FileHashSpoofer")

-- ─── L25 — Signature verify killer ───────────────────────────
pcall(function()
    local M = import("Material")
    if M then M.GetMaterialHash = function() return "FAKE_HASH" end M.VerifyMaterial = T M.GetDisableDepthTest = F M.GetBlendMode = Z end
end)
mark(25, "SignatureVerifyKiller")

-- ─── L26 — Movement speed normalizer ─────────────────────────
pcall(function()
    local CM = import("CharacterMovementComponent")
    if CM then CM.GetMaxSpeed = function(self) local s = CM.__o and CM.__o(self) if _G.DS.firewall.active then return 600.0 end return s end end
end)
mark(26, "MovementNormalize")

-- ─── L27 — Aim tracking spoofer ──────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local a = sm:Get("ClientAimTrackingSubsystem")
        if a then a.GetAimData = function() return {accuracy=math.random(45,60),headshotRate=math.random(15,25),trackingTime=math.random(200,400),aimLockCount=0} end a.IsAimNormal = T end
    end
end)
mark(27, "AimTrackingSpoof")

-- ─── L28 — Wallhack detection killer ─────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local w = sm:Get("ClientWallhackDetectionSubsystem")
        if w then w.IsVisionNormal = T w.GetVisibilityRate = function() return math.random(70,80) end end
    end
end)
mark(28, "WallhackDetKiller")

-- ─── L29 — ESP detection killer ──────────────────────────────
pcall(function()
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local e = sm:Get("ClientESPDetectionSubsystem")
        if e then e.HasESP = F e.CheckOverlay = function() return "clean" end end
    end
end)
mark(29, "ESPDetKiller")

-- ─── L30 — Shot verify killer ────────────────────────────────
pcall(function()
    local sv = package.loaded["GameLua.Dev.Subsystem.ShootVerifySubSystemClient"]
    if sv then sv.VerifyShot = T end
end)
mark(30, "ShotVerifyKiller")

-- ─── L31 — Movement delta spoofer ────────────────────────────
pcall(function()
    if NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(n, ...)
            local p = tostring(n or ""):lower()
            if p:find("move") or p:find("teleport") then return nil end
            return o(n, ...)
        end
    end
end)
mark(31, "MoveDeltaSpoofer")

-- ─── L32 — Vote/kick killer ──────────────────────────────────
pcall(function()
    for _, k in ipairs({"KickVoteStart","KickVoteEnd","VoteKick","OnKickVote",
        "OnPlayerVoted","OnVoteResult","StartKickVote","VoteKickPlayer"}) do
        if _G[k] then _G[k] = nop end
    end
end)
mark(32, "VoteKickKiller")

-- ─── L33 — Ban popup kill ────────────────────────────────────
pcall(function()
    local M = package.loaded["client.slua.logic.common.logic_common_msg_box"]
    if M and M.Show then
        local o = M.Show
        M.Show = function(t_, title, content, ...)
            local t = tostring(title or ""):lower()
            local c = tostring(content or ""):lower()
            if t:find("ban") or t:find("kick") or t:find("punish") or t:find("suspend")
               or c:find("banned") or c:find("suspended") or c:find("violation") or c:find("cheat") then
                return
            end
            return o(t_, title, content, ...)
        end
    end
end)
mark(33, "BanPopupKill")

-- ─── L34 — Force disconnect block ────────────────────────────
pcall(function()
    _G.OnShutdownAfterError = nop
    _G.OnPlayerActorChannelError = nop
    _G.OnPlayerRPCValidateFailed = nop
    _G.OnPlayerNetConnectionClosed = nop
    local sm = require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if sm then
        local pcS = sm:Get("PlayerControllerSubsystem")
        if pcS then if pcS.KickPlayer then pcS.KickPlayer = nop end if pcS.BanPlayer then pcS.BanPlayer = nop end if pcS.ForceDisconnect then pcS.ForceDisconnect = nop end end
    end
end)
mark(34, "ForceDisconnectBlock")

-- ─── L35 — Background sweep (re-assert every 4s) ─────────────
pcall(function()
    local ticker = require("common.time_ticker")
    if ticker and ticker.AddTimerLoop then
        ticker.AddTimerLoop(0, function()
            _G.DS.firewall.active = true
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
mark(35, "BackgroundSweep")

print("[DS FIREWALL] 35 layers active")
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# ESP VARIANTS
# ═════════════════════════════════════════════════════════════════
ESP_HEADER = r"""
local ESP = _G.DS_ESP or {}
_G.DS_ESP = ESP
ESP.widgets = ESP.widgets or {}
ESP.canvas = ESP.canvas or nil

local function GetCanvas()
    if ESP.canvas and Game:IsValid(ESP.canvas) then return ESP.canvas end
    local ok, U = pcall(require, "GameLua.Mod.BaseMod.Common.UI.InGameUITools")
    if not ok or not U then return nil end
    local b = U.GetMainControlBaseUI()
    if not b or not Game:IsValid(b) then return nil end
    ESP.canvas = b.CanvasPanel_0 or b.CanvasPanel_42
    return ESP.canvas
end

local function GetPC()
    if _G.slua_GameFrontendHUD then
        local pc = _G.slua_GameFrontendHUD:GetPlayerController()
        if slua.isValid(pc) then return pc end
    end
    return nil
end

local function GetLocal()
    local ok, GD = pcall(require, "GameLua.GameCore.Data.GameplayData")
    if ok and GD and GD.GetPlayerCharacter then
        local p = GD.GetPlayerCharacter()
        if slua.isValid(p) then return p end
    end
    return nil
end

local function Proj(PC, loc)
    local out = import("Vector2D")(0, 0)
    local ok = false
    pcall(function() ok = PC:ProjectWorldLocationToScreen(loc, out, true) end)
    if not ok or (out.X == 0 and out.Y == 0) then return false, 0, 0 end
    return true, out.X, out.Y
end

local function LoS(PC, target)
    local r = false
    pcall(function() r = PC:LineOfSightTo(target, import("Vector")(0, 0, 0), false) end)
    return r
end

local function MakeBorder(parent, color, z)
    local b = nil
    pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", parent) end)
    if not b or not slua.isValid(b) then return nil end
    b:SetBrushColor(color)
    b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(b)
    if s then s:SetAutoSize(false) s:SetZOrder(z or 10) end
    return { w = b, s = s }
end

local function MakeText(parent, color, size, z)
    local t = nil
    pcall(function() t = CGame:NewObjectFromPath("/Script/UMG.TextBlock", parent) end)
    if not t or not slua.isValid(t) then return nil end
    local FC = import("LinearColor")
    local SC = import("SlateColor") or import("/Script/SlateCore.SlateColor")
    if SC then t:SetColorAndOpacity(SC(color)) else t:SetColorAndOpacity(color) end
    if t.Font then local f = t.Font f.Size = size or 12 t.Font = f end
    t:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(t)
    if s then s:SetAutoSize(true) s:SetZOrder(z or 20) end
    return { w = t, s = s }
end

local function EachEnemy(cb)
    local local_player = GetLocal()
    if not slua.isValid(local_player) then return end
    local PC = GetPC()
    if not slua.isValid(PC) then return end
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= local_player and p.TeamID ~= local_player.TeamID then
            local hp = 0 pcall(function() hp = p.Health or 0 end)
            if hp > 0 then cb(p, local_player, PC) end
        end
    end
end
"""


@feature("esp_box", "Screen Box ESP", menu=[
    {"id": "ESP_BOX", "name": "Box ESP", "val": 1, "type": "toggle"}])
def _f_esp_box(c):
    return {"lua": ESP_HEADER + r"""

local boxes = {}
function ESP.TickBox()
    if _G.DS_Get("ESP_BOX") ~= 1 then for k, v in pairs(boxes) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end boxes[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    local seen = {}
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        seen[key] = true
        local loc = e:K2_GetActorLocation()
        if not loc then return end
        loc.Z = loc.Z + 90
        local ok, cx, cy = Proj(PC, loc)
        if not ok then return end
        local _, bpy = Proj(PC, e:K2_GetActorLocation())
        if not bpy then return end
        local h = math.abs(bpy - cy) * 1.6
        local w = h * 0.55
        if not boxes[key] then
            boxes[key] = MakeBorder(canvas, FC(1, 0, 0, 0.8), 15)
        end
        local b = boxes[key]
        if b and b.s and slua.isValid(b.s) then
            b.s:SetPosition(FC(cx - w/2, cy - h/2))
            b.s:SetSize(FC(w, h))
        end
    end)
    for k, v in pairs(boxes) do
        if not seen[k] and slua.isValid(v.w) then v.w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end
    end
end
if _G.DS_Reg then _G.DS_Reg("esp_box", ESP.TickBox) end
""".rstrip()}


@feature("esp_skeleton", "Skeleton ESP", menu=[
    {"id": "ESP_SKEL", "name": "Skeleton ESP", "val": 1, "type": "toggle"}])
def _f_esp_skeleton(c):
    return {"lua": ESP_HEADER + r"""

local SKEL_CHAINS = {
    {"head","neck_01","pelvis"},
    {"neck_01","upperarm_l","lowerarm_l","hand_l"},
    {"neck_01","upperarm_r","lowerarm_r","hand_r"},
    {"pelvis","thigh_l","calf_l","foot_l"},
    {"pelvis","thigh_r","calf_r","foot_r"},
}
local skel = {}
function ESP.TickSkel()
    if _G.DS_Get("ESP_SKEL") ~= 1 then for k, tbl in pairs(skel) do for _, v in ipairs(tbl) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end skel[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local mesh = e.Mesh
        if not slua.isValid(mesh) then return end
        skel[key] = skel[key] or {}
        local idx = 0
        local visible = LoS(PC, e)
        local color = visible and FC(0, 1, 0, 0.85) or FC(1, 0, 0, 0.7)
        for _, chain in ipairs(SKEL_CHAINS) do
            local prev = nil
            for _, bone in ipairs(chain) do
                local bp = nil
                pcall(function() bp = mesh:GetSocketLocation(bone) end)
                if bp then
                    local ok, x, y = Proj(PC, bp)
                    if ok and prev then
                        idx = idx + 1
                        skel[key][idx] = skel[key][idx] or MakeBorder(canvas, color, 5)
                        local w = skel[key][idx]
                        local dx, dy = x - prev.x, y - prev.y
                        local len = math.sqrt(dx*dx + dy*dy)
                        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
                        if w and w.s and slua.isValid(w.s) then
                            w.w:SetBrushColor(color)
                            w.s:SetPosition(FC(prev.x, prev.y - 0.4))
                            w.s:SetSize(FC(len, 0.8))
                            w.w:SetRenderAngle(ang)
                            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
                        end
                    end
                    if ok then prev = {x = x, y = y} end
                end
            end
        end
        for i = idx + 1, #skel[key] do
            if slua.isValid(skel[key][i].w) then skel[key][i].w:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_skel", ESP.TickSkel) end
""".rstrip()}


@feature("esp_line", "Snap Line ESP", menu=[
    {"id": "ESP_LINE", "name": "Snap Lines", "val": 1, "type": "toggle"}])
def _f_esp_line(c):
    return {"lua": ESP_HEADER + r"""

local lines = {}
function ESP.TickLine()
    if _G.DS_Get("ESP_LINE") ~= 1 then for k, v in pairs(lines) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end lines[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    local sx, sy = 960, 60
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation()
        if not loc then return end
        loc.Z = loc.Z + 90
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        lines[key] = lines[key] or MakeBorder(canvas, FC(1, 1, 0, 0.7), 1)
        local w = lines[key]
        local dx, dy = x - sx, y - sy
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local visible = LoS(PC, e)
        if w and w.s and slua.isValid(w.s) then
            w.w:SetBrushColor(visible and FC(0, 1, 0, 0.7) or FC(1, 0, 0, 0.7))
            w.s:SetPosition(FC(sx, sy))
            w.s:SetSize(FC(len, 1.5))
            w.w:SetRenderAngle(ang)
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_line", ESP.TickLine) end
""".rstrip()}


@feature("esp_distance", "Distance ESP", menu=[
    {"id": "ESP_DIST", "name": "Distance ESP", "val": 1, "type": "toggle"}])
def _f_esp_distance(c):
    return {"lua": ESP_HEADER + r"""

local dist = {}
function ESP.TickDist()
    if _G.DS_Get("ESP_DIST") ~= 1 then for k, v in pairs(dist) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end dist[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 130
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        local m = math.floor(lp:GetDistanceTo(e) / 100)
        dist[key] = dist[key] or MakeText(canvas, FC(0, 1, 1, 1), 14, 30)
        local w = dist[key]
        if w and w.w and slua.isValid(w.w) then
            w.w:SetText(m .. "m")
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_dist", ESP.TickDist) end
""".rstrip()}


@feature("esp_name", "Name ESP", menu=[
    {"id": "ESP_NAME", "name": "Name ESP", "val": 1, "type": "toggle"}])
def _f_esp_name(c):
    return {"lua": ESP_HEADER + r"""

local names = {}
function ESP.TickName()
    if _G.DS_Get("ESP_NAME") ~= 1 then for k, v in pairs(names) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end names[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 150
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        local nm = "Unknown"
        pcall(function() nm = e:GetPlayerNameSafety() or "Unknown" end)
        names[key] = names[key] or MakeText(canvas, FC(1, 1, 0, 1), 12, 28)
        local w = names[key]
        if w and w.w and slua.isValid(w.w) then
            w.w:SetText(nm)
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_name", ESP.TickName) end
""".rstrip()}


@feature("esp_hp", "HP Bar ESP", menu=[
    {"id": "ESP_HP", "name": "HP Bar", "val": 1, "type": "toggle"}])
def _f_esp_hp(c):
    return {"lua": ESP_HEADER + r"""

local hps = {}
function ESP.TickHP()
    if _G.DS_Get("ESP_HP") ~= 1 then for k, v in pairs(hps) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end hps[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 105
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        local hp, mx = 0, 100
        pcall(function() hp = e.Health or 0 mx = e.HealthMax or 100 end)
        if mx <= 0 then mx = 100 end
        local pct = hp / mx
        if pct > 1 then pct = 1 end
        if pct < 0 then pct = 0 end
        local col = pct > 0.5 and FC(0, 1, 0, 0.9) or (pct > 0.25 and FC(1, 0.5, 0, 0.9) or FC(1, 0, 0, 0.9))
        if not hps[key] then
            hps[key] = { bg = MakeBorder(canvas, FC(0, 0, 0, 0.7), 40), fg = MakeBorder(canvas, FC(0, 1, 0, 1), 41) }
        end
        local h = hps[key]
        if h.bg and slua.isValid(h.bg.w) then
            h.bg.s:SetPosition(FC(x - 30, y))
            h.bg.s:SetSize(FC(60, 5))
            h.bg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
        if h.fg and slua.isValid(h.fg.w) then
            h.fg.w:SetBrushColor(col)
            h.fg.s:SetPosition(FC(x - 30, y))
            h.fg.s:SetSize(FC(60 * pct, 5))
            h.fg.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_hp", ESP.TickHP) end
""".rstrip()}


@feature("esp_weapon", "Weapon Icon ESP", menu=[
    {"id": "ESP_WEP", "name": "Weapon Icon", "val": 1, "type": "toggle"}])
def _f_esp_weapon(c):
    return {"lua": ESP_HEADER + r"""

local weps = {}
function ESP.TickWep()
    if _G.DS_Get("ESP_WEP") ~= 1 then for k, v in pairs(weps) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end weps[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 175
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        local wname = "Fist"
        pcall(function()
            local w = e.CurrentWeapon or (e.GetCurrentWeapon and e:GetCurrentWeapon())
            if slua.isValid(w) and w.GetWeaponName then wname = w:GetWeaponName() end
        end)
        weps[key] = weps[key] or MakeText(canvas, FC(1, 0.8, 0.2, 1), 11, 26)
        local w = weps[key]
        if w and w.w and slua.isValid(w.w) then
            w.w:SetText(wname)
            w.s:SetPosition(FC(x, y))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_wep", ESP.TickWep) end
""".rstrip()}


@feature("esp_radar", "Minimap Radar ESP", menu=[
    {"id": "ESP_RADAR", "name": "Minimap Radar", "val": 1, "type": "toggle"}])
def _f_esp_radar(c):
    return {"lua": r"""
-- Radar ESP: uses InGameMarkTools distance markers
local RADAR = { active = false, cfg = {
    UIPathName = "/Game/Mod/EvoBase/BluePrints/UIBP/QuickSign/QuickSign_TipHitEnemy_UIBP_New.QuickSign_TipHitEnemy_UIBP_New_C",
    MaxWidgetNum = 99, MaxShowDistance = 6000000,
    bBindOutScreen = true, bBindBlocked = true, bIsBindingActor = true,
    BindSocketName = "head", bUseLuaWorldSocketName = true,
    WorldPositionOffset = FVector(0, 0, 50), bNeedPreLoad = true, Priority = 2,
}}
local IMT = nil
pcall(function() IMT = require("GameLua.Mod.BaseMod.Common.InGameMarkTools") end)

function RADAR.Tick()
    if _G.DS_Get("ESP_RADAR") ~= 1 then return end
    if not IMT then return end
    local GDP = require("GameLua.GameCore.Data.GameplayData")
    local me = GDP.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    pcall(function()
        local tools = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
        local c = tools.GetCurrentConfig("ScreenMarkConfig")
        if c then c[9999] = RADAR.cfg end
    end)
    for _, e in pairs(GDP.GetAllPlayerCharacters and GDP.GetAllPlayerCharacters() or {}) do
        if slua.isValid(e) and e ~= me and e.TeamID ~= me.TeamID then
            local dead = false
            pcall(function() if type(e.IsDead) == "function" then dead = e:IsDead() end if e.bHidden then dead = true end end)
            if not dead and not e.DS_RadarMark then
                pcall(function()
                    e.DS_RadarMark = IMT.ClientAddMapMark(9999, FVector(0, 0, 0), 0, "", 4, e)
                end)
            elseif dead and e.DS_RadarMark then
                pcall(function() IMT.ClientRemoveMapMark(e.DS_RadarMark) end)
                e.DS_RadarMark = nil
            end
        end
    end
end
pcall(function()
    local t = require("GameLua.Mod.BaseMod.Common.GamePlayTools")
    local c = t.GetCurrentConfig("ScreenMarkConfig")
    if c then c[9999] = RADAR.cfg end
end)
if _G.DS_SlowReg then _G.DS_SlowReg("esp_radar", RADAR.Tick) end
""".rstrip()}


@feature("esp_vis", "Visibility Color ESP", menu=[
    {"id": "ESP_VIS", "name": "Visibility Color", "val": 1, "type": "toggle"}])
def _f_esp_vis(c):
    return {"lua": ESP_HEADER + r"""

local visboxes = {}
function ESP.TickVis()
    if _G.DS_Get("ESP_VIS") ~= 1 then for k, v in pairs(visboxes) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end visboxes[k] = nil end return end
    local canvas = GetCanvas() if not canvas then return end
    local FC = import("LinearColor")
    EachEnemy(function(e, lp, PC)
        local key = tostring(e)
        local loc = e:K2_GetActorLocation() if not loc then return end
        loc.Z = loc.Z + 90
        local ok, x, y = Proj(PC, loc)
        if not ok then return end
        local visible = LoS(PC, e)
        visboxes[key] = visboxes[key] or MakeBorder(canvas, FC(1, 0, 0, 0.8), 14)
        local w = visboxes[key]
        if w and w.s and slua.isValid(w.s) then
            w.w:SetBrushColor(visible and FC(0, 1, 0, 0.9) or FC(1, 0, 0, 0.9))
            w.s:SetPosition(FC(x - 15, y - 15))
            w.s:SetSize(FC(30, 30))
            w.w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
    end)
end
if _G.DS_Reg then _G.DS_Reg("esp_vis", ESP.TickVis) end
""".rstrip()}


@feature("esp_fov_circle", "FOV Circle", menu=[
    {"id": "ESP_FOV", "name": "FOV Circle", "val": 1, "type": "toggle"}])
def _f_esp_fov(c):
    return {"lua": r"""
local FOV = { container = nil, lines = {}, N = 40, last = nil }
function FOV.Create()
    if FOV.container and slua.isValid(FOV.container) then return true end
    local c = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U.GetMainControlBaseUI()
        if slua.isValid(b) then c = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    if not c then return false end
    local panel = nil
    pcall(function() panel = CGame:NewObjectFromPath("/Script/UMG.CanvasPanel", c) end)
    if not panel then return false end
    local F2 = import("Vector2D")
    for i = 1, FOV.N do
        local b = nil
        pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", panel) end)
        if b then
            b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
            b:SetRenderTransformPivot(F2(0, 0.5))
            local s = panel:AddChildToCanvas(b)
            if s then s:SetAlignment(F2(0, 0.5)) end
            FOV.lines[i] = { w = b, s = s }
        end
    end
    local slot = c:AddChildToCanvas(panel)
    if slot then slot:SetSize(F2(0, 0)) slot:SetPosition(F2(0, 0)) slot:SetZOrder(995) end
    FOV.container = panel
    return true
end
function FOV.Tick()
    if _G.DS_Get("ESP_FOV") ~= 1 then
        if FOV.container and slua.isValid(FOV.container) then FOV.container:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed) end
        return
    end
    if not FOV.Create() then return end
    FOV.container:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize()
    if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local R = 120
    local FC = import("LinearColor")
    local color = FC(1, 1, 1, 0.55)
    for i = 1, FOV.N do
        local a1 = (i - 1) * 2 * math.pi / FOV.N
        local a2 = i * 2 * math.pi / FOV.N
        local x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        local x2, y2 = cx + R * math.cos(a2), cy + R * math.sin(a2)
        local dx, dy = x2 - x1, y2 - y1
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local l = FOV.lines[i]
        if l and l.s then
            l.s:SetPosition(import("Vector2D")(x1, y1))
            l.s:SetSize(import("Vector2D")(len + 0.8, 1.5))
            l.w:SetRenderAngle(ang)
            l.w:SetBrushColor(color)
        end
    end
end
if _G.DS_Reg then _G.DS_Reg("esp_fov", FOV.Tick) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# AIMBOT VARIANTS
# ═════════════════════════════════════════════════════════════════
AIM_HEADER = r"""
local AIM = _G.DS_AIM or {}
_G.DS_AIM = AIM

local function GetChar()
    local ok, GD = pcall(require, "GameLua.GameCore.Data.GameplayData")
    if ok and GD and GD.GetPlayerCharacter then
        local p = GD.GetPlayerCharacter()
        if slua.isValid(p) then return p end
    end
    return nil
end

local function GetPC()
    if _G.slua_GameFrontendHUD then
        local pc = _G.slua_GameFrontendHUD:GetPlayerController()
        if slua.isValid(pc) then return pc end
    end
    return nil
end

local function GetEnemies()
    local out = {}
    local me = GetChar()
    if not slua.isValid(me) then return out end
    local myTeam = me.TeamID or 0
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me and p.TeamID ~= myTeam then
            local hp = 0 pcall(function() hp = p.Health or 0 end)
            if hp > 0 then out[#out+1] = p end
        end
    end
    return out
end

local function GetBone(e, name)
    local b = nil
    pcall(function()
        if e.GetBonePos then b = e:GetBonePos(name, {X = 0, Y = 0, Z = 0}) end
    end)
    if not b then pcall(function() if e.Mesh and e.Mesh.GetSocketLocation then b = e.Mesh:GetSocketLocation(name) end end) end
    return b
end
"""


@feature("aim_silent", "Silent Aim", menu=[
    {"id": "AIM_SILENT", "name": "Silent Aim", "val": 1, "type": "toggle"}])
def _f_aim_silent(c):
    return {"lua": AIM_HEADER + r"""

local function pick()
    local me = GetChar() if not slua.isValid(me) then return nil end
    local PC = GetPC() if not slua.isValid(PC) then return nil end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return nil end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local best, bestD = nil, 99999
    for _, e in ipairs(GetEnemies()) do
        local head = GetBone(e, "head")
        if head then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(head, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < bestD then bestD = d best = e end
            end
        end
    end
    return best
end
function AIM.TickSilent()
    if _G.DS_Get("AIM_SILENT") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local best = pick() if not best then return end
    local head = GetBone(best, "head") if not head then return end
    local cur = PC:GetControlRotation()
    local KM = import("KismetMathLibrary")
    local camMgr = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(camMgr) then return end
    local camLoc = camMgr:GetCameraLocation()
    local target = KM.FindLookAtRotation(camLoc, head)
    if target then
        target.Pitch = target.Pitch + (math.random() - 0.5) * 0.02
        target.Yaw = target.Yaw + (math.random() - 0.5) * 0.02
        PC:SetControlRotation(target, "SilentAim")
    end
end
if _G.DS_Reg then _G.DS_Reg("aim_silent", AIM.TickSilent) end
""".rstrip()}


@feature("aim_smooth", "Smooth Aim", menu=[
    {"id": "AIM_SMOOTH", "name": "Smooth Aim", "val": 1, "type": "toggle"},
    {"id": "AIM_SMOOTH_SPD", "name": "Smooth Speed", "val": 40, "type": "slider"}])
def _f_aim_smooth(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickSmooth()
    if _G.DS_Get("AIM_SMOOTH") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local best, bestD = nil, 99999
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local radius = 200
    for _, e in ipairs(GetEnemies()) do
        local head = GetBone(e, "spine_03") or GetBone(e, "head")
        if head then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(head, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < radius and d < bestD then bestD = d best = e end
            end
        end
    end
    if not best then return end
    local head = GetBone(best, "spine_03") or GetBone(best, "head") if not head then return end
    local cur = PC:GetControlRotation()
    local KM = import("KismetMathLibrary")
    local camMgr = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(camMgr) then return end
    local camLoc = camMgr:GetCameraLocation()
    local tgt = KM.FindLookAtRotation(camLoc, head)
    if not tgt then return end
    local dy = tgt.Yaw - cur.Yaw
    if dy > 180 then dy = dy - 360 end
    if dy < -180 then dy = dy + 360 end
    local dp = tgt.Pitch - cur.Pitch
    local speed = (_G.DS_Get("AIM_SMOOTH_SPD") or 40) / 100
    local nY = cur.Yaw + dy * speed * 0.3
    local nP = cur.Pitch + dp * speed * 0.3
    PC:SetControlRotation({ Pitch = nP, Yaw = nY, Roll = 0 }, "SmoothAim")
end
if _G.DS_Reg then _G.DS_Reg("aim_smooth", AIM.TickSmooth) end
""".rstrip()}


@feature("aim_bone", "Bone Lock Aimbot (Head/Neck/Chest)", menu=[
    {"id": "AIM_BONE", "name": "Bone Aimbot", "val": 1, "type": "toggle"},
    {"id": "AIM_BONE_SEL", "name": "Bone", "val": 1, "type": "dropdown",
     "options": ["Head", "Neck", "Chest", "Pelvis"]}])
def _f_aim_bone(c):
    return {"lua": AIM_HEADER + r"""

local BONE_NAMES = { "head", "neck_01", "spine_03", "pelvis" }
function AIM.TickBone()
    if _G.DS_Get("AIM_BONE") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring and not me.bIsGunADS then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local boneIdx = _G.DS_Get("AIM_BONE_SEL") or 1
    local boneName = BONE_NAMES[boneIdx + 1] or "head"
    local best, bestD = nil, 99999
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    for _, e in ipairs(GetEnemies()) do
        local b = GetBone(e, boneName)
        if b then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(b, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < bestD and d < 300 then bestD = d best = e end
            end
        end
    end
    if not best then return end
    local b = GetBone(best, boneName) if not b then return end
    local camMgr = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(camMgr) then return end
    local camLoc = camMgr:GetCameraLocation()
    local tgt = import("KismetMathLibrary").FindLookAtRotation(camLoc, b)
    if tgt then PC:SetControlRotation(tgt, "BoneAim") end
end
if _G.DS_Reg then _G.DS_Reg("aim_bone", AIM.TickBone) end
""".rstrip()}


@feature("aim_pred", "Prediction Aimbot", menu=[
    {"id": "AIM_PRED", "name": "Prediction Aim", "val": 1, "type": "toggle"},
    {"id": "AIM_PRED_STR", "name": "Pred Strength", "val": 50, "type": "slider"}])
def _f_aim_pred(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickPred()
    if _G.DS_Get("AIM_PRED") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local best, bestD = nil, 99999
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    for _, e in ipairs(GetEnemies()) do
        local head = GetBone(e, "head")
        if head then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(head, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < bestD and d < 400 then bestD = d best = e end
            end
        end
    end
    if not best then return end
    local head = GetBone(best, "head") if not head then return end
    local vel = nil
    pcall(function() if best.GetVelocity then vel = best:GetVelocity() end end)
    if vel then
        local dist = me:GetDistanceTo(best) / 100
        local str = (_G.DS_Get("AIM_PRED_STR") or 50) / 100
        local tof = (dist / 800) * str
        head.X = head.X + vel.X * tof
        head.Y = head.Y + vel.Y * tof
    end
    local camMgr = import("GameplayStatics").GetPlayerCameraManager(PC, 0)
    if not slua.isValid(camMgr) then return end
    local camLoc = camMgr:GetCameraLocation()
    local tgt = import("KismetMathLibrary").FindLookAtRotation(camLoc, head)
    if tgt then PC:SetControlRotation(tgt, "PredictAim") end
end
if _G.DS_Reg then _G.DS_Reg("aim_pred", AIM.TickPred) end
""".rstrip()}


@feature("aim_recoil", "Recoil Compensation", menu=[
    {"id": "AIM_RECOIL", "name": "Recoil Comp", "val": 1, "type": "toggle"},
    {"id": "AIM_RECOIL_STR", "name": "Strength", "val": 30, "type": "slider"}])
def _f_aim_recoil(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickRecoil()
    if _G.DS_Get("AIM_RECOIL") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    if not me.bIsWeaponFiring or not me.bIsGunADS then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local str = (_G.DS_Get("AIM_RECOIL_STR") or 30) / 50
    local cur = PC:GetControlRotation()
    cur.Pitch = cur.Pitch - str * 0.4
    PC:SetControlRotation(cur, "RecoilComp")
end
if _G.DS_Reg then _G.DS_Reg("aim_recoil", AIM.TickRecoil) end
""".rstrip()}


@feature("aim_autofire", "Auto Fire", menu=[
    {"id": "AIM_AUTOFIRE", "name": "Auto Fire", "val": 1, "type": "toggle"}])
def _f_aim_autofire(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickAutoFire()
    if _G.DS_Get("AIM_AUTOFIRE") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local fire = false
    for _, e in ipairs(GetEnemies()) do
        local head = GetBone(e, "head") or GetBone(e, "spine_03")
        if head then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(head, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < 60 then fire = true break end
            end
        end
    end
    if fire then
        pcall(function()
            me.bIsWeaponFiring = true
            if me.SetIsWeaponFiring then me:SetIsWeaponFiring(true) end
            if PC.SetIsWeaponFiring then PC:SetIsWeaponFiring(true) end
            local wm = me.WeaponManagerComponent
            if slua.isValid(wm) then wm.bIsWeaponFiring = true end
        end)
    else
        pcall(function()
            me.bIsWeaponFiring = false
            if me.SetIsWeaponFiring then me:SetIsWeaponFiring(false) end
            if PC.SetIsWeaponFiring then PC:SetIsWeaponFiring(false) end
        end)
    end
end
if _G.DS_Reg then _G.DS_Reg("aim_autofire", AIM.TickAutoFire) end
""".rstrip()}


@feature("aim_shotgun", "Shotgun Auto Aim", menu=[
    {"id": "AIM_SG", "name": "Shotgun Auto", "val": 1, "type": "toggle"}])
def _f_aim_shotgun(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickSG()
    if _G.DS_Get("AIM_SG") ~= 1 then return end
    local me = GetChar() if not slua.isValid(me) then return end
    local w = me.CurrentWeapon or (me.GetCurrentWeapon and me:GetCurrentWeapon())
    if not slua.isValid(w) then return end
    local nm = ""
    pcall(function() nm = (w.GetWeaponName and w:GetWeaponName()) or "" end)
    if not (nm:find("S686") or nm:find("S1897") or nm:find("S12") or nm:find("DBS") or nm:find("M1014")) then return end
    local PC = GetPC() if not slua.isValid(PC) then return end
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    for _, e in ipairs(GetEnemies()) do
        local head = GetBone(e, "head") or GetBone(e, "spine_03")
        if head then
            local out = import("Vector2D")(0, 0)
            if PC:ProjectWorldLocationToScreen(head, out, false) and out.X > 0 then
                local d = math.sqrt((out.X-cx)^2 + (out.Y-cy)^2)
                if d < 50 and me:GetDistanceTo(e) < 2500 then
                    pcall(function()
                        me.bIsWeaponFiring = true
                        if me.SetIsWeaponFiring then me:SetIsWeaponFiring(true) end
                        if w.StartFire then w:StartFire() end
                    end)
                end
            end
        end
    end
end
if _G.DS_Reg then _G.DS_Reg("aim_sg", AIM.TickSG) end
""".rstrip()}


@feature("aim_visibility", "Visibility Check Aimbot", menu=[
    {"id": "AIM_VIS", "name": "Visible Only", "val": 1, "type": "toggle"}])
def _f_aim_visibility(c):
    return {"lua": AIM_HEADER + r"""

function AIM.TickVis()
    if _G.DS_Get("AIM_VIS") ~= 1 then return end
    -- This filter gets consumed by other aimbots via _G.DS_AIM.VisibleOnly
    _G.DS_AIM.VisibleOnly = true
end
if _G.DS_Reg then _G.DS_Reg("aim_vis", AIM.TickVis) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# MAGIC BULLET VARIANTS
# ═════════════════════════════════════════════════════════════════
MAGIC_HEADER = r"""
local MB = _G.DS_MB or {}
_G.DS_MB = MB
MB.installed = false

local function hook_body_type()
    if MB.installed then return end
    MB.installed = true
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
                    local force = MB.get_force and MB.get_force()
                    if force then return force end
                    return o1 and o1(self, imp, vec)
                end
                local o2 = m.GetHitBodyTypeByHitPos
                m.GetHitBodyTypeByHitPos = function(self, vec)
                    local force = MB.get_force and MB.get_force()
                    if force then return force end
                    return o2 and o2(self, vec)
                end
            end
        end
    end)
end

function MB.Disable()
    MB.get_force = nil
end
"""


@feature("magic_full", "Magic Bullet — Full", menu=[
    {"id": "MAGIC_FULL", "name": "Magic Full", "val": 1, "type": "toggle"}])
def _f_magic_full(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickFull()
    if _G.DS_Get("MAGIC_FULL") ~= 1 then return end
    local E = import("EAvatarDamagePosition")
    MB.get_force = function() return E and E.BigHead or nil end
end
if _G.DS_Reg then _G.DS_Reg("magic_full", MB.TickFull) end
""".rstrip()}


@feature("magic_head", "Magic Bullet — Head Only", menu=[
    {"id": "MAGIC_HEAD", "name": "Magic Head", "val": 1, "type": "toggle"}])
def _f_magic_head(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickHead()
    if _G.DS_Get("MAGIC_HEAD") ~= 1 then return end
    local E = import("EAvatarDamagePosition")
    MB.get_force = function() return E and E.BigHead or nil end
end
if _G.DS_Reg then _G.DS_Reg("magic_head", MB.TickHead) end
""".rstrip()}


@feature("magic_neck", "Magic Bullet — Neck", menu=[
    {"id": "MAGIC_NECK", "name": "Magic Neck", "val": 1, "type": "toggle"}])
def _f_magic_neck(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickNeck()
    if _G.DS_Get("MAGIC_NECK") ~= 1 then return end
    MB.get_force = function() return "neck" end
end
if _G.DS_Reg then _G.DS_Reg("magic_neck", MB.TickNeck) end
""".rstrip()}


@feature("magic_body", "Magic Bullet — Body", menu=[
    {"id": "MAGIC_BODY", "name": "Magic Body", "val": 1, "type": "toggle"}])
def _f_magic_body(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickBody()
    if _G.DS_Get("MAGIC_BODY") ~= 1 then return end
    MB.get_force = function() return "spine_02" end
end
if _G.DS_Reg then _G.DS_Reg("magic_body", MB.TickBody) end
""".rstrip()}


@feature("magic_legs", "Magic Bullet — Legs", menu=[
    {"id": "MAGIC_LEGS", "name": "Magic Legs", "val": 1, "type": "toggle"}])
def _f_magic_legs(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickLegs()
    if _G.DS_Get("MAGIC_LEGS") ~= 1 then return end
    MB.get_force = function() return "calf_l" end
end
if _G.DS_Reg then _G.DS_Reg("magic_legs", MB.TickLegs) end
""".rstrip()}


@feature("magic_custom", "Magic Bullet — Custom Ratio", menu=[
    {"id": "MAGIC_CUSTOM", "name": "Custom Magic", "val": 1, "type": "toggle"},
    {"id": "MAGIC_RATIO", "name": "Head Bias %", "val": 60, "type": "slider"}])
def _f_magic_custom(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickCustom()
    if _G.DS_Get("MAGIC_CUSTOM") ~= 1 then return end
    MB.get_force = function()
        local ratio = (_G.DS_Get("MAGIC_RATIO") or 60) / 100
        if math.random() < ratio then
            local E = import("EAvatarDamagePosition")
            return E and E.BigHead or nil
        end
        return nil
    end
end
if _G.DS_Reg then _G.DS_Reg("magic_custom", MB.TickCustom) end
""".rstrip()}


@feature("magic_hitbox", "Hitbox Expand", menu=[
    {"id": "MAGIC_HITBOX", "name": "Hitbox Expand", "val": 1, "type": "toggle"},
    {"id": "MAGIC_HITBOX_MUL", "name": "Multiplier", "val": 3, "type": "slider"}])
def _f_magic_hitbox(c):
    return {"lua": r"""
local HX = {}
function HX.Tick()
    if _G.DS_Get("MAGIC_HITBOX") ~= 1 then return end
    local mul = (_G.DS_Get("MAGIC_HITBOX_MUL") or 3)
    if mul < 1 then mul = 1 end
    if mul > 6 then mul = 6 end
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local myTeam = me.TeamID or 0
    for _, e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e ~= me and e.TeamID ~= myTeam then
            local mesh = e.Mesh
            if slua.isValid(mesh) and e.DS_LastHitMul ~= mul then
                pcall(function() mesh:SetRelativeScale3D(import("Vector")(1.0, 1.0, mul)) end)
                e.DS_LastHitMul = mul
            end
        end
    end
end
if _G.DS_SlowReg then _G.DS_SlowReg("magic_hitbox", HX.Tick) end
""".rstrip()}


@feature("magic_safe", "Safe 60% Magic", menu=[
    {"id": "MAGIC_SAFE", "name": "Safe Magic", "val": 1, "type": "toggle"}])
def _f_magic_safe(c):
    return {"lua": MAGIC_HEADER + r"""
hook_body_type()
function MB.TickSafe()
    if _G.DS_Get("MAGIC_SAFE") ~= 1 then return end
    MB.get_force = function()
        -- 40% head, 40% chest, 20% natural
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
if _G.DS_Reg then _G.DS_Reg("magic_safe", MB.TickSafe) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# CROSSHAIR VARIANTS
# ═════════════════════════════════════════════════════════════════
CROSS_HEADER = r"""
local CH = _G.DS_CH or {}
_G.DS_CH = CH
CH.widgets = CH.widgets or {}

local function canvas()
    local c = nil
    pcall(function()
        local U = require("GameLua.Mod.BaseMod.Common.UI.InGameUITools")
        local b = U.GetMainControlBaseUI()
        if slua.isValid(b) then c = b.CanvasPanel_0 or b.CanvasPanel_42 end
    end)
    return c
end

local function makeBorder(parent, color, w, h)
    local b = nil
    pcall(function() b = CGame:NewObjectFromPath("/Script/UMG.Border", parent) end)
    if not b then return nil end
    b:SetBrushColor(color)
    b:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    local s = parent:AddChildToCanvas(b)
    return { w = b, s = s }
end
"""


@feature("cross_cross", "Crosshair — Cross", menu=[
    {"id": "CH_CROSS", "name": "Cross", "val": 1, "type": "toggle"}])
def _f_cross_cross(c):
    return {"lua": CROSS_HEADER + r"""

function CH.TickCross()
    local canvas_ = canvas()
    if _G.DS_Get("CH_CROSS") ~= 1 then
        if CH.widgets.cross then
            for _, v in pairs(CH.widgets.cross) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end
            CH.widgets.cross = nil
        end
        return
    end
    if not canvas_ then return end
    local FC = import("LinearColor")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize()
    if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    if not CH.widgets.cross then
        CH.widgets.cross = {
            h = makeBorder(canvas_, FC(1, 0, 0, 1), 20, 2),
            v = makeBorder(canvas_, FC(1, 0, 0, 1), 2, 20),
        }
    end
    CH.widgets.cross.h.s:SetPosition(FC(cx - 10, cy - 1))
    CH.widgets.cross.h.s:SetSize(FC(20, 2))
    CH.widgets.cross.v.s:SetPosition(FC(cx - 1, cy - 10))
    CH.widgets.cross.v.s:SetSize(FC(2, 20))
end
if _G.DS_Reg then _G.DS_Reg("cross_cross", CH.TickCross) end
""".rstrip()}


@feature("cross_dot", "Crosshair — Dot", menu=[
    {"id": "CH_DOT", "name": "Dot", "val": 1, "type": "toggle"}])
def _f_cross_dot(c):
    return {"lua": CROSS_HEADER + r"""

function CH.TickDot()
    local canvas_ = canvas()
    if _G.DS_Get("CH_DOT") ~= 1 then
        if CH.widgets.dot and slua.isValid(CH.widgets.dot.w) then CH.widgets.dot.w:RemoveFromParent() CH.widgets.dot = nil end
        return
    end
    if not canvas_ then return end
    local FC = import("LinearColor")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    if not CH.widgets.dot then CH.widgets.dot = makeBorder(canvas_, FC(0, 1, 0, 1), 6, 6) end
    CH.widgets.dot.s:SetPosition(FC(cx - 3, cy - 3))
    CH.widgets.dot.s:SetSize(FC(6, 6))
end
if _G.DS_Reg then _G.DS_Reg("cross_dot", CH.TickDot) end
""".rstrip()}


@feature("cross_circle", "Crosshair — Circle", menu=[
    {"id": "CH_CIRCLE", "name": "Circle", "val": 1, "type": "toggle"}])
def _f_cross_circle(c):
    return {"lua": CROSS_HEADER + r"""

function CH.TickCircle()
    local canvas_ = canvas()
    if _G.DS_Get("CH_CIRCLE") ~= 1 then
        if CH.widgets.circle then for _, v in pairs(CH.widgets.circle) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end CH.widgets.circle = nil end
        return
    end
    if not canvas_ then return end
    local FC = import("LinearColor")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local R = 12
    local N = 20
    if not CH.widgets.circle then
        CH.widgets.circle = {}
        for i = 1, N do
            CH.widgets.circle[i] = makeBorder(canvas_, FC(0, 1, 1, 1), 4, 1)
            CH.widgets.circle[i].w:SetRenderTransformPivot(import("Vector2D")(0, 0.5))
        end
    end
    for i = 1, N do
        local a1 = (i - 1) * 2 * math.pi / N
        local a2 = i * 2 * math.pi / N
        local x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        local x2, y2 = cx + R * math.cos(a2), cy + R * math.sin(a2)
        local dx, dy = x2 - x1, y2 - y1
        local len = math.sqrt(dx*dx + dy*dy)
        local ang = math.deg(math.atan2 and math.atan2(dy, dx) or math.atan(dy, dx))
        local l = CH.widgets.circle[i]
        l.s:SetPosition(import("Vector2D")(x1, y1))
        l.s:SetSize(import("Vector2D")(len + 0.5, 1))
        l.w:SetRenderAngle(ang)
    end
end
if _G.DS_Reg then _G.DS_Reg("cross_circle", CH.TickCircle) end
""".rstrip()}


@feature("cross_tstyle", "Crosshair — T-Style", menu=[
    {"id": "CH_TSTYLE", "name": "T-Style", "val": 1, "type": "toggle"}])
def _f_cross_tstyle(c):
    return {"lua": CROSS_HEADER + r"""

function CH.TickT()
    local canvas_ = canvas()
    if _G.DS_Get("CH_TSTYLE") ~= 1 then
        if CH.widgets.t then for _, v in pairs(CH.widgets.t) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end CH.widgets.t = nil end
        return
    end
    if not canvas_ then return end
    local FC = import("LinearColor")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    if not CH.widgets.t then
        CH.widgets.t = {
            top = makeBorder(canvas_, FC(1, 1, 0, 1), 2, 10),
            left = makeBorder(canvas_, FC(1, 1, 0, 1), 10, 2),
            right = makeBorder(canvas_, FC(1, 1, 0, 1), 10, 2),
        }
    end
    CH.widgets.t.top.s:SetPosition(FC(cx - 1, cy - 12))
    CH.widgets.t.top.s:SetSize(FC(2, 10))
    CH.widgets.t.left.s:SetPosition(FC(cx - 12, cy - 1))
    CH.widgets.t.left.s:SetSize(FC(10, 2))
    CH.widgets.t.right.s:SetPosition(FC(cx + 2, cy - 1))
    CH.widgets.t.right.s:SetSize(FC(10, 2))
end
if _G.DS_Reg then _G.DS_Reg("cross_tstyle", CH.TickT) end
""".rstrip()}


@feature("cross_rainbow", "Crosshair — Animated Rainbow", menu=[
    {"id": "CH_RAINBOW", "name": "Rainbow", "val": 1, "type": "toggle"}])
def _f_cross_rainbow(c):
    return {"lua": CROSS_HEADER + r"""

function CH.TickRainbow()
    local canvas_ = canvas()
    if _G.DS_Get("CH_RAINBOW") ~= 1 then
        if CH.widgets.rainbow then for _, v in pairs(CH.widgets.rainbow) do if slua.isValid(v.w) then v.w:RemoveFromParent() v.w:ConditionalBeginDestroy() end end CH.widgets.rainbow = nil end
        return
    end
    if not canvas_ then return end
    local FC = import("LinearColor")
    local ui = require("client.common.ui_util")
    local vp = ui and ui.GetViewportSize() if not vp then return end
    local cx, cy = vp.X * 0.5, vp.Y * 0.5
    local t = os.clock() * 2
    local r = (math.sin(t) + 1) / 2
    local g = (math.sin(t + 2) + 1) / 2
    local b = (math.sin(t + 4) + 1) / 2
    local col = FC(r, g, b, 1)
    if not CH.widgets.rainbow then
        CH.widgets.rainbow = {
            h = makeBorder(canvas_, col, 20, 2),
            v = makeBorder(canvas_, col, 2, 20),
        }
    end
    CH.widgets.rainbow.h.w:SetBrushColor(col)
    CH.widgets.rainbow.v.w:SetBrushColor(col)
    CH.widgets.rainbow.h.s:SetPosition(FC(cx - 10, cy - 1))
    CH.widgets.rainbow.h.s:SetSize(FC(20, 2))
    CH.widgets.rainbow.v.s:SetPosition(FC(cx - 1, cy - 10))
    CH.widgets.rainbow.v.s:SetSize(FC(2, 20))
end
if _G.DS_Reg then _G.DS_Reg("cross_rainbow", CH.TickRainbow) end
""".rstrip()}


# ═════════════════════════════════════════════════════════════════
# SKIN FEATURES
# ═════════════════════════════════════════════════════════════════
SKIN_HEADER = r"""
local SK = _G.DS_SKIN or {}
_G.DS_SKIN = SK
SK.injected = SK.injected or {}
SK.byWeapon = SK.byWeapon or {}

local function getEntity()
    local ok, dc = pcall(require, "client.slua.logic.wardrobe.logic_wardrobe_data_center")
    if not ok or not dc then return nil end
    local ok2, e = pcall(dc.GetWardrobeData)
    return ok2 and e or nil
end
local function getWD()
    local ok, wd = pcall(require, "client.slua.logic.wardrobe.wardrobe_data")
    return ok and wd or nil
end
local function getPC()
    if _G.slua_GameFrontendHUD then
        local pc = _G.slua_GameFrontendHUD:GetPlayerController()
        if slua.isValid(pc) then return pc end
    end
    return nil
end

function SK.inject(resID, insID, sub)
    local e = getEntity()
    if not e or not e.bInit then return false end
    local row = {
        instid = insID, res_id = resID, count = 1, lock_cnt = 0, isnew = 0,
        valid_hours = 0, expire_ts = 0,
    }
    pcall(function() e:AddData(row) end)
    SK.injected[resID] = insID
    if sub and SK.byWeapon then SK.byWeapon[sub] = SK.byWeapon[sub] or {} SK.byWeapon[sub][resID] = insID end
    return true
end

function SK.refresh()
    pcall(function()
        if EventSystem and EVENTTYPE_WARDROBE and EVENTID_WARDROBE_UPDATE_ITEM_LIST then
            EventSystem:postEvent(EVENTTYPE_WARDROBE, EVENTID_WARDROBE_UPDATE_ITEM_LIST)
        end
    end)
end

function SK.putOn(insID)
    local e = getEntity()
    if not e then return end
    pcall(function()
        local WRH = require("client.network.Protocol.WardRobeHandler")
        local d = nil
        pcall(function() d = e:GetDataByInsID(insID) end)
        if d then
            local item = { res_id = d.resID, ins_id = insID, count = 1, expire_ts = 0 }
            WRH.on_depot_put_on_rsp(0, item, nil, 3, insID, 0)
        end
    end)
end
"""


@feature("skin_weapon", "Weapon Skin Mod", menu=[
    {"id": "SK_WEAPON", "name": "Weapon Skin", "val": 1, "type": "toggle"}])
def _f_skin_weapon(c):
    return {"lua": SKIN_HEADER + r"""

local WEAPON_SKINS = {
    [101001] = 1101001174,   -- AKM
    [101004] = 1101004163,   -- M416
    [101003] = 1101003146,   -- SCAR-L
    [101008] = 1101008081,   -- M762
    [101006] = 1101006062,   -- AUG
    [103001] = 1103001202,   -- Kar98
    [103003] = 1103003079,   -- AWM
    [103002] = 1103002030,   -- M24
    [103004] = 1103004037,   -- SKS
    [102001] = 1102001120,   -- UZI
    [102002] = 1102002043,   -- UMP45
}

function SK.TickWeapon()
    if _G.DS_Get("SK_WEAPON") ~= 1 then return end
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
    local skinID = WEAPON_SKINS[wid]
    if not skinID then return end
    pcall(function()
        local wac = w.WeaponAvatarComponent
        if slua.isValid(wac) then
            if wac.ChangeWeaponAvatar then wac:ChangeWeaponAvatar(skinID, false) end
            if wac.ReloadAllEquippedAvatar then wac:ReloadAllEquippedAvatar(1) end
        end
    end)
end
if _G.DS_SlowReg then _G.DS_SlowReg("skin_weapon", SK.TickWeapon) end
""".rstrip()}


@feature("skin_outfit", "Outfit Skin Mod", menu=[
    {"id": "SK_OUTFIT", "name": "Outfit Skin", "val": 1, "type": "toggle"},
    {"id": "SK_OUTFIT_ID", "name": "Outfit ID", "val": 1407870, "type": "slider"}])
def _f_skin_outfit(c):
    return {"lua": SKIN_HEADER + r"""

function SK.TickOutfit()
    if _G.DS_Get("SK_OUTFIT") ~= 1 then return end
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local outfitID = _G.DS_Get("SK_OUTFIT_ID") or 1407870
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    pcall(function()
        comp:PutOnCustomEquipmentByID(outfitID)
    end)
end
if _G.DS_SlowReg then _G.DS_SlowReg("skin_outfit", SK.TickOutfit) end
""".rstrip()}


@feature("skin_vehicle", "Vehicle Skin Mod", menu=[
    {"id": "SK_VEH", "name": "Vehicle Skin", "val": 1, "type": "toggle"}])
def _f_skin_vehicle(c):
    return {"lua": SKIN_HEADER + r"""

local VEH_SKINS = {
    [1961010] = true, [1961014] = true, [1961147] = true,  -- McLaren
    [1961016] = true, [1961017] = true, [1961018] = true,  -- Koenigsegg
    [1961020] = true, [1961021] = true,                     -- Lambo
    [1961043] = true, [1961044] = true,                     -- Bugatti
    [1961048] = true, [1961049] = true,                     -- Aston
}

function SK.TickVehicle()
    if _G.DS_Get("SK_VEH") ~= 1 then return end
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local veh = me.CurrentVehicle
    if not slua.isValid(veh) then return end
    local av = veh.VehicleAvatarComponent_BP
    if not slua.isValid(av) then return end
    local skinID = nil
    for k in pairs(VEH_SKINS) do skinID = k break end
    if skinID then
        pcall(function() av:ChangeItemAvatar(skinID, false) end)
    end
end
if _G.DS_SlowReg then _G.DS_SlowReg("skin_vehicle", SK.TickVehicle) end
""".rstrip()}


@feature("skin_parachute", "Parachute Skin Mod", menu=[
    {"id": "SK_PARA", "name": "Parachute Skin", "val": 1, "type": "toggle"}])
def _f_skin_parachute(c):
    return {"lua": SKIN_HEADER + r"""

local PARA_SKINS = { 1401000, 1401010, 1401020, 1401085, 1401180 }
function SK.TickPara()
    if _G.DS_Get("SK_PARA") ~= 1 then return end
    local me = nil
    pcall(function()
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
    end)
    if not slua.isValid(me) then return end
    local comp = me.CharacterAvatarComp2_BP
    if not slua.isValid(comp) then return end
    local skin = PARA_SKINS[math.random(1, #PARA_SKINS)]
    pcall(function() comp:PutOnCustomEquipmentByID(skin) end)
end
if _G.DS_SlowReg then _G.DS_SlowReg("skin_para", SK.TickPara) end
""".rstrip()}


@feature("skin_emote", "Emote Unlock", menu=[
    {"id": "SK_EMOTE", "name": "Emote Unlock", "val": 1, "type": "toggle"}])
def _f_skin_emote(c):
    return {"lua": r"""
local EM = { hooked = false }
function EM.Hook()
    if EM.hooked then return end
    EM.hooked = true
    pcall(function()
        local le = require("GameLua.Mod.Library.GamePlay.Avatar.Emote.logic_emote")
        if le and le.IsEmoteExist then
            local o = le.IsEmoteExist
            le.IsEmoteExist = function(id)
                if _G.DS_Get("SK_EMOTE") == 1 then return true end
                return o(id)
            end
        end
        if le and le.CheckEmoteDownloaded then
            local o = le.CheckEmoteDownloaded
            le.CheckEmoteDownloaded = function(id, ...)
                if _G.DS_Get("SK_EMOTE") == 1 then return true end
                return o(id, ...)
            end
        end
    end)
    pcall(function()
        local QEU = require("GameLua.Mod.BaseMod.Client.Emote.QuickExpressionUtils")
        if QEU and QEU.GetShowExpressionList then
            local o = QEU.GetShowExpressionList
            QEU.GetShowExpressionList = function()
                local list, wid = o()
                if _G.DS_Get("SK_EMOTE") == 1 and type(list) == "table" then
                    for id = 12200001, 12220000, 1000 do
                        list[#list+1] = { DefineID = { TypeSpecificID = id }, Name = "Emote_" .. id }
                    end
                end
                return list, wid
            end
        end
    end)
end
EM.Hook()
""".rstrip()}


@feature("skin_deadbox", "Deadbox Skin Mod", menu=[
    {"id": "SK_BOX", "name": "Deadbox Skin", "val": 1, "type": "toggle"}])
def _f_skin_deadbox(c):
    return {"lua": r"""
local DB = {}
function DB.Tick()
    if _G.DS_Get("SK_BOX") ~= 1 then return end
    -- Patches deadbox skin to match current weapon skin
    pcall(function()
        local me = nil
        local GD = require("GameLua.GameCore.Data.GameplayData")
        me = GD.GetPlayerCharacter()
        if not slua.isValid(me) then return end
        local w = me:GetCurrentWeapon()
        if not slua.isValid(w) then return end
        _G.DS_LastWeaponSkinID = w.WeaponAvatarComponent and w.WeaponAvatarComponent.CachedLoadedID or 0
    end)
end
if _G.DS_SlowReg then _G.DS_SlowReg("skin_box", DB.Tick) end
""".rstrip()}


@feature("skin_killmsg", "Kill Message Skin", menu=[
    {"id": "SK_KILLMSG", "name": "Kill Message", "val": 1, "type": "toggle"}])
def _f_skin_killmsg(c):
    return {"lua": r"""
pcall(function()
    local SKI = require("GameLua.Mod.BaseMod.Client.KillInfoTips.KillInfo")
    if SKI and SKI.__inner_impl and SKI.__inner_impl.FileItem then
        local o = SKI.__inner_impl.FileItem
        SKI.__inner_impl.FileItem = function(self, data)
            if _G.DS_Get("SK_KILLMSG") == 1 and data then
                local skinID = _G.DS_LastWeaponSkinID or 0
                if skinID > 1000000 then
                    pcall(function()
                        local exp = slua.LuaArchiverDecode(LuaStateWrapper, data.ExpandDataContent) or {}
                        exp.CauserWeaponAvatarID = skinID
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
# WALLHACK / COUNTER / FPS / EXPIRY / TICK / BUILDER
# ═════════════════════════════════════════════════════════════════
@feature("wallhack", "Wallhack", deps=("menu",), menu=[
    {"id": "WALLHACK", "name": "Wallhack", "val": 1, "type": "toggle"}])
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
    if _G.DS_Get("WALLHACK") ~= 1 then return end
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
if _G.DS_Reg then _G.DS_Reg("wallhack", WH.Tick) end
""".rstrip()}


@feature("enemy_counter", "Enemy Counter", deps=("menu",), menu=[
    {"id": "ENEMY_COUNTER", "name": "Enemy Counter", "val": 1, "type": "toggle"}])
def _f_enemy_counter(c):
    return {"lua": r"""
local EC = { t = nil, w = nil }
function EC.Tick()
    if _G.DS_Get("ENEMY_COUNTER") ~= 1 then return end
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
                local dx, dy, dz = pos.X - myPos.X, pos.Y - myPos.Y, pos.Z - myPos.Z
                if dx*dx + dy*dy + dz*dz <= 900000000 then
                    total = total + 1
                    local b = false pcall(function() b = Game:IsAI(p) end)
                    if b then bots = bots + 1 else real = real + 1 end
                end
            end
        end
    end
    local txt = ""
    local col = { R = 0, G = 255, B = 200, A = 255 }
    if total == 0 then txt = "[ AREA SECURE ]"
    else
        txt = string.format("ENEMIES: %d  (Bots: %d | Real: %d)", total, bots, real)
        col = total == 1 and { R = 255, G = 255, B = 0, A = 255 } or { R = 255, G = 165, B = 0, A = 255 }
    end
    local off = { X = 0, Y = 0, Z = 35 }
    hud:AddDebugText(txt, me, 1.1, off, off, col, true, false, true, nil, 1.2, true)
end
if _G.DS_SlowReg then _G.DS_SlowReg("enemy_counter", EC.Tick) end
""".rstrip()}


@feature("fps165", "165 FPS Unlock", menu=[
    {"id": "FPS165", "name": "165 FPS", "val": 1, "type": "toggle"}])
def _f_fps165(c):
    return {"lua": r"""
pcall(function()
    local g = require("client.slua.logic.setting.logic_setting_graphics")
    if g and g.SetFPS then
        local o = g.SetFPS
        g.SetFPS = function(s, lvl)
            o(s, lvl)
            if lvl == 8 and _G.DS_Get("FPS165") == 1 and Game and Game.IsInGame and Game:IsInGame() then
                pcall(function() s:ExecuteCMD("t.MaxFPS", "165") s:ExecuteCMD("r.FrameRateLimit", "165") end)
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
    local r = TS - os.time()
    if r <= 0 then _G._MOD_EXPIRED = true return false end
    _G._MOD_EXPIRED = false
    return true
end
function _G.ShowExpiredPopup(exp)
    pcall(function()
        local M = require("client.slua.logic.common.logic_common_msg_box")
        local at = os.date("!%Y-%m-%d %H:%M:%S UTC", TS)
        if exp then M.Show(4, "Mod Expired", "Expired: "..at.."\\n\\n".."{brand}", function() end)
        else M.Show(4, "Mod", "Expires: "..at.."\\n\\n{brand}", function() end) end
    end)
end
""".rstrip()}


@feature("tick_manager", "Tick Loop Manager")
def _f_tick_manager(c):
    return {"lua": r"""
local TM = { started = false, boot = nil }
function TM.RunTicks()
    for _, fn in pairs(_G.DS.Ticks) do pcall(fn) end
end
function TM.RunSlow()
    for _, fn in pairs(_G.DS.Slow) do pcall(fn) end
end
function TM.Try()
    if TM.started then return end
    local pc = nil
    pcall(function()
        if slua_GameFrontendHUD then pc = slua_GameFrontendHUD:GetPlayerController() end
    end)
    if not slua.isValid(pc) or not pc.AddGameTimer then return end
    pcall(function()
        pc:AddGameTimer(0.15, true, TM.RunTicks)
        pc:AddGameTimer(0.5, true, TM.RunSlow)
    end)
    TM.started = true
    print("[DS] Tick loops started")
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
FORCED_HEAD = ("menu", "bypass")
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


def _collect_menu(ids):
    entries, seen = [], set()
    for i in ids:
        if i == "menu": continue
        for e in REGISTRY[i]["menu"]:
            if e["id"] not in seen:
                seen.add(e["id"])
                entries.append(e)
    return entries


def build_mod(features, brand="DEVILSOUL", expiry=(2027, 1, 1), filename="DEVILSOUL.lua"):
    user = [f for f in features if f in REGISTRY and f not in FORCED_HEAD and f not in FORCED_TAIL]
    all_ids = list(FORCED_HEAD) + user + list(FORCED_TAIL)
    order = _topo(all_ids)
    if "tick_manager" in order:
        order.remove("tick_manager")
        order.append("tick_manager")
    ctx = {"brand": brand, "expiry": expiry, "menu_entries": _collect_menu(order)}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (f"-- {filename}\n-- {ts}  brand: {brand}\n-- features: {', '.join(order)}\n")
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