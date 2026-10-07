# bot.py — Devil Menu ULTIMATE (FIXED)
# 17 security layers (9 engine bypass + 8 behavioral)
# Python 3.10+ | python-telegram-bot v20+
import os, io, time, random
from string import Template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_NAME  = os.environ.get("BOT_NAME", "devil_menu")

PROFILES = {
    "full":   {"aimbot": 85, "mb_on": True, "mb_range": 20, "mb_chance": 100,
               "esp_style": "auto", "esp_rotate": 30, "esp_name": True,
               "loot_esp": True, "crosshair": "cross"},
    "safe":   {"aimbot": 35, "mb_on": True, "mb_range": 15, "mb_chance": 15,
               "esp_style": "auto", "esp_rotate": 60, "esp_name": True,
               "loot_esp": True, "crosshair": "dot"},
    "random": {"aimbot": 30, "mb_on": True, "mb_range": 18, "mb_chance": 25,
               "esp_style": "auto", "esp_rotate": 30, "esp_name": True,
               "loot_esp": True, "crosshair": "circle_cross"},
}

ESP_STYLES = ["box", "line", "circle", "skeleton", "head", "distance", "name", "health"]
CROSSHAIRS = ["cross", "dot", "circle_cross", "chevron", "cross_gap", "dot_circle", "t_shape"]

# =============================================================
# 17 SECURITY LAYERS
# =============================================================

# ---------------- ENGINE BYPASS CORE (L01-L09) ----------------
BYPASS_CORE = r"""
-- ========================================================================
-- ENGINE BYPASS CORE — 9 engine-level layers
-- ========================================================================
_G._WHA_BYPASS_ACTIVE = true

local function _nop() end
local function _rtrue() return true end
local function _rfalse() return false end
local function _rzero() return 0 end
local function _rtab() return {} end

local function _tryReq(p) local ok,m = pcall(require,p); return ok and m or nil end
local function _tryImp(n) local ok,m = pcall(import,n); return ok and m or nil end
local function _isOn()
    return _G._WHA_BYPASS_ACTIVE and not _G._MOD_PAUSED and not _G._MOD_EXPIRED
end

-- [L01] PrimitiveComponent render getters
pcall(function()
    local P = _tryImp("PrimitiveComponent")
    if not P then return end
    for _, fn in ipairs({"IsRenderedOnCustomDepth","GetRenderCustomDepth",
                         "GetCustomDepthStencilValue","GetCustomDepthStencilWriteMask","GetVisibleFlag"}) do
        local o = P[fn]
        P["__o_"..fn] = o
        P[fn] = function(self, ...)
            if not _isOn() then return o and o(self, ...) end
            if fn == "GetVisibleFlag" then return true end
            if fn == "GetCustomDepthStencilValue" then return 0 end
            return false
        end
    end
end)

-- [L02] MeshComponent render getters
pcall(function()
    local M = _tryImp("MeshComponent")
    if not M then return end
    M.__oSR  = M.ShouldRender
    M.__oGSR = M.GetShouldRender
    M.__oIV  = M.IsVisible
    M.ShouldRender    = function(s) if not _isOn() then return M.__oSR  and M.__oSR(s)  end return true end
    M.GetShouldRender = function(s) if not _isOn() then return M.__oGSR and M.__oGSR(s) end return true end
    M.IsVisible       = function(s) if not _isOn() then return M.__oIV  and M.__oIV(s)  end return true end
end)

-- [L03] Material getters
pcall(function()
    local Mat = _tryImp("Material")
    if Mat then
        Mat.__oDDT = Mat.GetDisableDepthTest
        Mat.__oBM  = Mat.GetBlendMode
        Mat.__oH   = Mat.GetMaterialHash
        Mat.__oV   = Mat.VerifyMaterial
        Mat.GetDisableDepthTest = function(s) if not _isOn() then return Mat.__oDDT and Mat.__oDDT(s) end return false end
        Mat.GetBlendMode        = function(s) if not _isOn() then return Mat.__oBM  and Mat.__oBM(s)  end return 0     end
        Mat.GetMaterialHash     = function(s) if not _isOn() then return Mat.__oH   and Mat.__oH(s)   end return "F_HASH" end
        Mat.VerifyMaterial      = function(s) if not _isOn() then return Mat.__oV   and Mat.__oV(s)   end return true  end
    end
    local MI = _tryImp("MaterialInstance")
    if MI then
        MI.__oDDT = MI.GetDisableDepthTest
        MI.__oBM  = MI.GetBlendMode
        MI.GetDisableDepthTest = function(s) if not _isOn() then return MI.__oDDT and MI.__oDDT(s) end return false end
        MI.GetBlendMode        = function(s) if not _isOn() then return MI.__oBM  and MI.__oBM(s)  end return 0     end
    end
    local MID = _tryImp("MaterialInstanceDynamic")
    if MID then
        local oV = MID.K2_GetVectorParameterValue
        MID.K2_GetVectorParameterValue = function(s, name)
            if not _isOn() then return oV and oV(s, name) end
            local n = tostring(name or "")
            if n:find("Color") or n:find("Emissive") or n:find("Tint") then return {R=255,G=255,B=255,A=255} end
            return oV and oV(s, name)
        end
        local oS = MID.K2_GetScalarParameterValue
        MID.K2_GetScalarParameterValue = function(s, name)
            if not _isOn() then return oS and oS(s, name) end
            if tostring(name or ""):find("Emissive") then return 0.0 end
            return oS and oS(s, name)
        end
    end
end)

-- [L04] 12 detection subsystems nop
pcall(function()
    local sm = _tryReq("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
    if not sm then return end
    for _, sn in ipairs({
        "ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem",
        "ClientAimTrackingSubsystem","ShootVerifySubSystemClient",
        "ClientRenderCheckSubsystem","ClientMemoryGuardSubsystem",
        "ClientKernelCheckSubsystem","ClientHawkEyePatrolSubsystem",
        "ClientAntiCheatSubsystem","IntegrityCheckSubsystem",
        "FileCheckSubsystem","AvatarExceptionSubsystem" }) do
        local sub = sm:Get(sn)
        if sub then
            for k, v in pairs(sub) do
                if type(v) == "function" then
                    local kl = tostring(k)
                    if kl:find("Report") or kl:find("Send") or kl:find("Verify")
                       or kl:find("Check") or kl:find("Detect") or kl:find("Scan") then
                        sub[k] = _nop
                    end
                end
            end
            if sn == "ClientWallhackDetectionSubsystem" then
                sub.IsVisionNormal = _rtrue
                sub.GetVisibilityRate = function() return math.random(70,82) end
            elseif sn == "ClientESPDetectionSubsystem" then
                sub.HasESP = _rfalse
                sub.CheckOverlay = function() return "clean" end
            elseif sn == "ClientAimTrackingSubsystem" then
                sub.GetAimData = function() return {accuracy=math.random(48,58), headshotRate=math.random(18,28)} end
                sub.IsAimNormal = _rtrue
            elseif sn == "ClientMemoryGuardSubsystem" then
                sub.IsMemoryClean = function() return true, {code=0} end
                sub.ScanResult = function() return "clean" end
            elseif sn == "ClientKernelCheckSubsystem" then
                sub.IsKernelClean = function() return true, {code=0, message="clean"} end
                sub.GetKernelVersion = function() return "5.4.0-generic" end
                sub.IsBootloaderLocked = _rtrue
            elseif sn == "ShootVerifySubSystemClient" then
                sub.OnShootVerifyFailed = _nop
                sub.VerifyShot = _rtrue
            elseif sn == "ClientHawkEyePatrolSubsystem" then
                sub.GetPatrolData = _rtab
                sub.IsBeingWatched = _rfalse
                sub.GetSpectatorCount = _rzero
            elseif sn == "ClientRenderCheckSubsystem" then
                sub.IsRenderClean = _rtrue
                sub.GetRenderState = function() return "normal" end
            end
        end
    end
end)

-- [L05] GameplayCallbacks nop
pcall(function()
    if not _G.GameplayCallbacks then _G.GameplayCallbacks = {} end
    local GC = _G.GameplayCallbacks
    for _, fn in ipairs({
        "ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow","ReportFireArms",
        "ReportVerifyInfoFlow","ReportMrpcsFlow","ReportPlayerBehavior","ReportTeammatHurt",
        "ReportPlayerMoveRoute","ReportPlayerPosition","ReportAimFlow","ReportHitFlow",
        "ReportWallHack","ReportAimbot","ReportSpeedHack","ReportMagicBullet",
        "ReportAbnormalMaterial","ReportDepthTestChange","ReportMemoryException",
        "ReportMaterialScan","ReportShaderOverride","ReportCircleFlow",
        "ReportESPBox","ReportESPHealth","ReportMiniMapESP","ReportEnemyFrameUI",
        "ReportDistanceMarker","ReportWallhackESP","SendESPData","UploadESPInfo",
        "OnPlayerRPCValidateFailed","OnPlayerActorChannelError",
        "OnPlayerSpectateException","OnShutdownAfterError"}) do
        GC[fn] = _nop
    end
    local oSC = GC.OnDSPlayerStateChanged
    GC.OnDSPlayerStateChanged = function(uid, state, ...)
        if type(state) == "string" then
            local s = state:lower()
            if s:find("cheat") or s:find("ban") or s:find("integrity") then return end
        end
        if oSC then return oSC(uid, state, ...) end
    end
end)

-- [L06] TssSdk spoof
pcall(function()
    local t = _G.TssSdk
    if not t then return end
    t.GetFileMD5          = function() return "" end
    t.VerifyFileSignature = _rtrue
    t.CheckIntegrity      = _rtrue
    t.ScanMemory          = function() return true, {} end
    t.IsEmulator          = _rfalse
    t.OnRecvData          = _nop
    t.CheckKernel         = function() return true, {status="verified", tampered=false} end
    t.VerifyBoot          = function() return true, {locked=true, verified=true} end
end)

-- [L07] Screenshot block
pcall(function()
    local SS = _tryImp("ScreenshotMaker") or _tryImp("ScreenshotMTDer")
    if not SS then return end
    SS.MakePicture   = function() return "" end
    SS.ReMakePicture = function() return "" end
    SS.HasCaptured   = _rtrue
end)

-- [L08] HiggsBoson avatar anomaly disable
pcall(function()
    local hb = _tryReq("GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent")
    if hb then
        hb.bMHActive = false
        hb.bCallPreReplication = false
        if hb.ControlMHActive then hb.ControlMHActive = _nop end
        if hb.StartAvatarCheck then hb.StartAvatarCheck = _nop end
        if hb.BlackList then for k in pairs(hb.BlackList) do hb.BlackList[k] = nil end end
    end
    if _G.AvatarCheckCallback then
        _G.AvatarCheckCallback.StartAvatarCheck = _nop
        _G.AvatarCheckCallback.OnReportItemID = _nop
    end
    _G.BlackList = {}
end)

-- [L09] MarkManager own-mark filter
pcall(function()
    local MM = InGameMarkTools and InGameMarkTools.ScreenMarkManager
    if not MM then return end
    if MM.GetAllActiveMarks then
        local o = MM.GetAllActiveMarks
        MM.GetAllActiveMarks = function(self, ...)
            local m = o(self, ...)
            if not _isOn() or not m then return m end
            local out = {}
            for _, x in ipairs(m) do
                local g = x.MarkGroupID
                if not (g == 1006 or g == 9999) then table.insert(out, x) end
            end
            return out
        end
    end
    if MM.GetMarksByGroup then
        local o = MM.GetMarksByGroup
        MM.GetMarksByGroup = function(self, gid)
            if _isOn() and (gid == 1006 or gid == 9999) then return {} end
            return o(self, gid)
        end
    end
    if MM.OnAddMark    then MM.OnAddMark    = _nop end
    if MM.OnRemoveMark then MM.OnRemoveMark = _nop end
end)

print("[BYPASS CORE] 9 engine layers installed")
"""

# ---------------- BEHAVIORAL LAYERS (L10-L17) ----------------
L10_SYSCALL = r"""
-- [L10] SYSCALL INDIRECTION
local _cache = {}
_G._S_IMPORT = function(name)
    local h = _cache[name]
    if h ~= nil then return h end
    local ok, cls = pcall(import, name)
    _cache[name] = ok and cls or nil
    return _cache[name]
end
"""

L11_STRCRYPT = r"""
-- [L11] STRING CRYPT
local _k = {0x4D,0x21,0x7A,0x03,0x1E}
local function _d(b)
    local o = {}
    for i=1,#b do o[i]=string.char(bit32.bxor(b[i],_k[(i-1)%#_k+1])) end
    return table.concat(o)
end
_G._S_STR = {
    rwh = _d({0x0E,0x05,0x0B,0x3F,0x77,0x4D,0x1F,0x3E,0x2A,0x32,0x6F,0x22,0x5B,0x12}),
    rab = _d({0x0E,0x05,0x0B,0x3F,0x77,0x40,0x10,0x22,0x30,0x22,0x6F}),
}
"""

L12_RPC = r"""
-- [L12] RPC NORMALIZE
do
    local _o = _G.SendRPC
    if _o then
        _G.SendRPC = function(name, ...)
            local j = 0.020 + math.random() * 0.180
            local a = {...}
            a[#a+1] = string.rep("\0", math.random(4,32))
            local t = 0
            local function f()
                t = t + 0.016
                if t >= j then return _o(name, table.unpack(a)) end
                local tk = package.loaded["common.time_ticker"]
                if tk then tk.AddTimerOnce(0.016, f) end
            end
            f()
        end
    end
end
"""

L13_DRIFT = r"""
-- [L13] BEHAVIOR DRIFT
local _s = {a=0.55+math.random()*0.10, h=0.22+math.random()*0.08,
            r=0.28+math.random()*0.10, v=0.72+math.random()*0.10}
local function _st(v, lo, hi, s)
    v = v + (math.random()-0.5)*s
    if v < lo then v = lo + math.random()*s end
    if v > hi then v = hi - math.random()*s end
    return v
end
_G._S_DRIFT = function()
    _s.a = _st(_s.a, 0.42, 0.72, 0.010)
    _s.h = _st(_s.h, 0.14, 0.34, 0.005)
    _s.r = _st(_s.r, 0.20, 0.42, 0.008)
    _s.v = _st(_s.v, 0.60, 0.88, 0.010)
end
_G._S_DRIFT_GET = function()
    return {accuracy=_s.a, headshotRate=_s.h, reactionTime=_s.r, visibilityRate=_s.v}
end
"""

L14_THROTTLE = r"""
-- [L14] STAT THROTTLE
local _s = {win=60, k={}, hs=0, hits=0, last=os.time()}
local _c = {hs=0.45, kpm=3.5}
_G._S_SHOT = function(ih, ik)
    local n = os.time()
    if n - _s.last >= _s.win then _s.k={}; _s.hs=0; _s.hits=0; _s.last=n end
    _s.hits = _s.hits + 1
    if ih then _s.hs = _s.hs + 1 end
    if ik then table.insert(_s.k, n) end
end
_G._S_SCALE = function()
    local n = os.time()
    local w = 0
    for _, t in ipairs(_s.k) do if n - t <= _s.win then w = w + 1 end end
    local kpm = w / (_s.win/60.0)
    local hs = _s.hits > 0 and (_s.hs/_s.hits) or 0
    local sc = 1.0
    if kpm > _c.kpm then sc = sc * (_c.kpm/kpm) end
    if hs  > _c.hs  then sc = sc * (_c.hs /hs ) end
    if sc > 1.0 then sc = 1.0 end
    if sc < 0.30 then sc = 0.30 end
    return sc
end
"""

L15_ANTIDBG = r"""
-- [L15] ANTI-DEBUG
local _o = debug and debug.sethook
local _t = 0
if debug then
    debug.sethook = function(...)
        _t = _t + 1
        if _t >= 2 then _G._MOD_PAUSED = true end
        return _o and _o(...)
    end
end
_G._S_WATCH = function(tbl)
    if not tbl then return end
    local mt = getmetatable(tbl)
    if not mt then return end
    local old = mt.__index
    mt.__index = function(t, k)
        local s = tostring(k)
        if s:find("Report") or s:find("Verify") then
            _t = _t + 1
            return function() end
        end
        if old then return old(t, k) end
    end
end
"""

L16_MEM = r"""
-- [L16] MEM ATTEST
local _sig = {}
do
    local s = os.time() % 0x7FFFFFFF
    for i=1,32 do _sig[i] = (s * 1103515245 + 12345) % 256; s = _sig[i] end
end
local _o = _G.GetFileMD5
_G.GetFileMD5 = function(p)
    if p and tostring(p):find("lua") then
        return string.format("%02x", table.unpack(_sig))
    end
    if _o then return _o(p) end
    return ""
end
"""

L17_TRAFFIC = r"""
-- [L17] TRAFFIC SHAPE
do
    local tk = package.loaded["common.time_ticker"]
    if tk and NetUtil and NetUtil.SendPacket then
        local o = NetUtil.SendPacket
        NetUtil.SendPacket = function(name, ...)
            if math.random() < 0.03 then
                tk.AddTimerOnce(0.05 + math.random()*0.15, function() o(name, ...) end)
                return nil
            end
            return o(name, ...)
        end
        local function _f()
            pcall(function() o("KeepAlive", string.rep("\0", math.random(2,12))) end)
            tk.AddTimerOnce(1.5 + math.random()*2.5, _f)
        end
        tk.AddTimerOnce(2.0, _f)
    end
end
"""

SECURITY_LAYERS = [BYPASS_CORE,
                   L10_SYSCALL, L11_STRCRYPT, L12_RPC, L13_DRIFT,
                   L14_THROTTLE, L15_ANTIDBG, L16_MEM, L17_TRAFFIC]

# =============================================================
# CROSSHAIR (uses $crosshair)
# =============================================================
CROSSHAIR_LUA = r"""
-- CROSSHAIR
local _ch_style = "$crosshair"
local _ch_glyphs = {
    cross="✛", dot="●", circle_cross="✛", chevron="❮",
    cross_gap="┼", dot_circle="◉", t_shape="⊤"
}
local _ch_w = nil
_G._CH_Draw = function()
    pcall(function()
        if not _ch_w or not slua.isValid(_ch_w) then
            local BP = "/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"
            _ch_w = slua.loadUI(BP)
            if not _ch_w or not slua.isValid(_ch_w) then return end
            require("game_frontend_hud").AddToContainer(UIContainers.Top, _ch_w, 12000)
            local WLL = import("WidgetLayoutLibrary")
            local slot = WLL.SlotAsCanvasSlot(_ch_w)
            if slot then
                slot:SetAnchors(FAnchors(0.5, 0.5, 0.5, 0.5))
                slot:SetAlignment(FVector2D(0.5, 0.5))
                slot:SetPosition(FVector2D(0, 0))
                slot:SetSize(FVector2D(40, 40))
            end
            if _ch_w.RichText_Content then
                local fi = _ch_w.RichText_Content.Font
                if fi then fi.Size = 32; _ch_w.RichText_Content:SetFont(fi) end
                _ch_w.RichText_Content:SetColorAndOpacity(FSlateColor(FLinearColor(1,1,1,1)))
            end
            _ch_w:SetBackgroundColor(FLinearColor(0,0,0,0))
            _ch_w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
        if _ch_w and _ch_w.RichText_Content then
            _ch_w.RichText_Content:SetText(_ch_glyphs[_ch_style] or "✛")
        end
    end)
end
"""

# =============================================================
# GRAPHICS (static)
# =============================================================
GRAPHICS_LUA = r"""
-- SYSTEM & GRAPHICS state + functions
_G._GFX = {
    ipad_perspective = false,
    fov_degree = 110,
    visual_cleanup = false,
    potato_mode = false,
    fps_unlock = false,
    _orig_fov = nil,
}
local function _fov()
    pcall(function()
        local pc = slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
        if not slua.isValid(pc) then return end
        local cam = import("GameplayStatics").GetPlayerCameraManager(pc, 0)
        if not slua.isValid(cam) then return end
        if not _G._GFX._orig_fov then _G._GFX._orig_fov = cam.DefaultFOV end
        if _G._GFX.ipad_perspective then
            cam.DefaultFOV = _G._GFX.fov_degree
            cam:SetFOV(_G._GFX.fov_degree)
        else
            cam:SetFOV(_G._GFX._orig_fov)
        end
    end)
end
local function _gfxcmd(c) 
    local K = import("KismetSystemLibrary"); local w = slua.getWorld()
    if K and w then K.ExecuteConsoleCommand(w, c) end
end
_G._GFX.SetIPad     = function(v) _G._GFX.ipad_perspective = v; _fov() end
_G._GFX.SetFOV      = function(d) _G._GFX.fov_degree = math.max(90, math.min(135, d)); _fov() end
_G._GFX.SetCleanup  = function(v)
    _G._GFX.visual_cleanup = v
    if v then
        _gfxcmd("foliage.DensityScale 0.2"); _gfxcmd("r.Fog 0"); _gfxcmd("r.VolumetricFog 0")
    else
        _gfxcmd("foliage.DensityScale 1.0"); _gfxcmd("r.Fog 1"); _gfxcmd("r.VolumetricFog 1")
    end
end
_G._GFX.SetPotato   = function(v)
    _G._GFX.potato_mode = v
    if v then
        _gfxcmd("r.ScreenPercentage 60"); _gfxcmd("r.ShadowQuality 0"); _gfxcmd("sg.ViewDistanceQuality 0")
    else
        _gfxcmd("r.ScreenPercentage 100"); _gfxcmd("sg.ViewDistanceQuality 3")
    end
end
_G._GFX.SetFPS      = function(v)
    _G._GFX.fps_unlock = v
    if v then _gfxcmd("t.MaxFPS 165"); _gfxcmd("r.VSync 0") else _gfxcmd("t.MaxFPS 60") end
end
"""

# =============================================================
# PLAYER ESP (uses $esp_*) — GameplayData moved to top, so no scope bug
# =============================================================
PLAYER_ESP_LUA = r"""
-- PLAYER ESP
_G._ESP = {
    enabled = true,
    style = "$esp_style",
    rotate = $esp_rotate,
    name_on = $esp_name_bool,
    last_rotate = os.time(),
    styles = {"box","line","circle","skeleton","head","distance","name","health"},
}
local function _pick()
    if _G._ESP.style ~= "auto" then return _G._ESP.style end
    return _G._ESP.styles[math.random(#_G._ESP.styles)]
end
local function _name(pawn)
    local n = nil
    pcall(function() n = pawn.PlayerName end)
    if not n then pcall(function() n = pawn:GetPlayerName() end) end
    if not n and pawn.PlayerState then pcall(function() n = pawn.PlayerState.PlayerName end) end
    if not n then pcall(function()
        local ps = pawn:GetPlayerStateSafety()
        if slua.isValid(ps) then n = ps.PlayerName end
    end) end
    if not n and pawn.PlayerKey then n = "Bot_"..tostring(pawn.PlayerKey) end
    return tostring(n or "?")
end
local function _apply(pawn)
    if not slua.isValid(pawn) then return end
    local vis = {R=1.0, G=0.0, B=0.0, A=1.0}
    local occ = {R=1.0, G=0.8, B=0.0, A=1.0}
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
            pawn.Mesh:OverrideIdeaOutlineColor(vis)
            pawn.Mesh:SetIdeaOutlineOcclusionColor(occ)
            pawn.Mesh:OverrideIdeaOutlineThickness(18.0)
        end
    end)
end
local _tags = {}
local function _tag(pawn, pc)
    if not _G._ESP.name_on then return end
    local key = pawn.PlayerKey or tostring(pawn)
    local w = _tags[key]
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
            w:SetBackgroundColor(FLinearColor(0,0,0,0.55))
            _tags[key] = w
        end)
        w = _tags[key]
    end
    if not w or not slua.isValid(w) then return end
    pcall(function()
        local loc = pawn:K2_GetActorLocation()
        local s = import("Vector2D")()
        if pc:ProjectWorldLocationToScreen({X=loc.X, Y=loc.Y, Z=loc.Z+200}, s, false) then
            if s.X < 0 or s.Y < 0 then
                w:SetWidgetVisibility(UEnums.ESlateVisibility.Hidden); return
            end
            w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
            w:SetPositionInViewport(FVector2D(s.X - 60, s.Y - 20), true)
            w:SetDesiredSizeInViewport(FVector2D(120, 20))
            local nm = _name(pawn)
            local me = _G.GameplayData and _G.GameplayData.GetPlayerCharacter and _G.GameplayData.GetPlayerCharacter()
            if slua.isValid(me) then
                local mp = me:K2_GetActorLocation()
                local d = math.sqrt((mp.X-loc.X)^2 + (mp.Y-loc.Y)^2 + (mp.Z-loc.Z)^2) / 100
                nm = nm .. " [" .. string.format("%.0fm", d) .. "]"
            end
            if w.RichText_Content then w.RichText_Content:SetText(nm) end
        end
    end)
end
_G._ESP_Tick = function()
    if not _G._ESP.enabled then return end
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    local now = os.time()
    if now - _G._ESP.last_rotate >= _G._ESP.rotate then
        _G._ESP.style = _pick(); _G._ESP.last_rotate = now
    end
    local me = _G.GameplayData and _G.GameplayData.GetPlayerCharacter and _G.GameplayData.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local myTeam = me:GetTeamID() or 0
    local pc = me:GetPlayerControllerSafety()
    for _, p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p ~= me then
            local t = p.TeamID or 0
            if t ~= myTeam and (p.Health or 0) > 0 then
                _apply(p)
                if _G._ESP.name_on and slua.isValid(pc) then _tag(p, pc) end
            end
        end
    end
end
"""

# =============================================================
# LOOT ESP (uses $loot_enabled)
# =============================================================
LOOT_ESP_LUA = r"""
-- SUPPLY & LOOT ESP
_G._LOOT = {
    enabled = $loot_enabled,
    weapons=true, ammo=true, meds=true, armor=true,
    attachments=true, airdrop=true, tomb=true,
    max_range=150,
    tiers = {
        legendary = {R=1.0,G=0.5,B=0.0,A=1.0},
        epic      = {R=0.6,G=0.0,B=1.0,A=1.0},
        rare      = {R=0.0,G=0.5,B=1.0,A=1.0},
        common    = {R=1.0,G=1.0,B=1.0,A=1.0},
    },
}
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
    if not c then return false end
    return _G._LOOT[c] == true
end
local function _mesh(m, t)
    if not m or not slua.isValid(m) then return end
    local col = _G._LOOT.tiers[t] or _G._LOOT.tiers.common
    pcall(function()
        m:SetDrawDyeing(true); m:SetDrawDyeingMode(1)
        m:SetVisibleDyeingColor(col); m:SetOccludedDyeingColor(col)
        m:SetDyeingColorFadeDistance(99999.0)
        m:SetDrawHighlight(true); m:OverrideHighlightColor(col)
        m:SetHighlightCanBeOccluded(false)
        m:SetDrawIdeaOutline(true); m:SetIdeaOutlineNew(true)
        m:OverrideIdeaOutlineColor(col)
        m:OverrideIdeaOutlineThickness(6.0)
    end)
end
_G._LOOT_Tick = function()
    if not _G._LOOT.enabled then return end
    if _G._MOD_PAUSED or not CheckExpiration() then return end
    local me = _G.GameplayData and _G.GameplayData.GetPlayerCharacter and _G.GameplayData.GetPlayerCharacter()
    if not slua.isValid(me) then return end
    local mp = me:K2_GetActorLocation()
    pcall(function()
        for _, cn in ipairs({"PickupActor","PlayerTombBox","AirDropBox","PickupActorBase"}) do
            local ok, cls = pcall(import, cn)
            if ok and cls then
                local actors = Game:GetActorsByClass(cls)
                if actors and actors.Num then
                    for i=0, actors:Num()-1 do
                        local a = actors:Get(i)
                        if slua.isValid(a) then
                            local loc = a:K2_GetActorLocation()
                            local d = math.sqrt((mp.X-loc.X)^2+(mp.Y-loc.Y)^2+(mp.Z-loc.Z)^2)/100
                            if d <= _G._LOOT.max_range then
                                local c = _cat(a)
                                if _show(c) then
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

# =============================================================
# VISIBLE MENU — fixes: enabled toggle, double-build guard, layout
# =============================================================
MENU_LUA = r"""
-- ============================================================
-- DEVIL MENU — visible UI with tabs + sidebar + toggles
-- ============================================================
local MENU_BP = "/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"

local _menu = {
    open = true,
    root = nil,
    tab = 1,
    tabs = {"PLAYER ESP","COMBAT ENGINE","VEHICLE RADAR","SUPPLY & LOOT ESP","SYSTEM & GRAPHICS"},
    sections = {"DEVIL MENU","CONTROLS","GRAPHICS","CUSTOMIZE BUTTONS","SENSITIVITY",
                "PICK UP","CROSSHAIR & EFFECTS","AUDIO & HAPTICS","PRIVACY & SOCIAL"},
    tab_btns = {},
    side_btns = {},
    content = {},
}

local function _mk(text, x, y, w, h, size, r, g, b, bg_a, interactive)
    local wd = slua.loadUI(MENU_BP)
    if not wd or not slua.isValid(wd) then return nil end
    require("game_frontend_hud").AddToContainer(UIContainers.Top, wd, 11000)
    wd:SetPositionInViewport(FVector2D(x, y), true)
    wd:SetDesiredSizeInViewport(FVector2D(w, h))
    wd:SetBackgroundColor(FLinearColor(0.05, 0.05, 0.08, bg_a or 0.95))
    wd:SetRenderOpacity(0.98)
    if interactive then
        wd:SetWidgetVisibility(UEnums.ESlateVisibility.Visible)
    else
        wd:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
    end
    if wd.RichText_Content then
        wd.RichText_Content:SetText(text)
        local fi = wd.RichText_Content.Font
        if fi then fi.Size = size or 13; wd.RichText_Content:SetFont(fi) end
        wd.RichText_Content:SetColorAndOpacity(FSlateColor(FLinearColor(r or 1, g or 1, b or 1, 1)))
    end
    return wd
end

local function _bind(wd, fn)
    if not wd then return end
    pcall(function()
        if wd.OnClicked then
            if wd.OnClicked.Add then wd.OnClicked:Add(fn)
            elseif wd.OnClicked.AddDynamic then wd.OnClicked:AddDynamic(wd, fn) end
        end
    end)
    pcall(function() if wd.BindOnClicked then wd:BindOnClicked(fn) end end)
end

local function _clear_content()
    for _, w in ipairs(_menu.content) do
        pcall(function() if slua.isValid(w) then w:RemoveFromParent() end end)
    end
    _menu.content = {}
end

local function _content_row(idx, label, value, fn)
    local vp = require("client.common.ui_util").GetViewportSize()
    local cx = vp.X * 0.5 - 340
    local y = 260 + idx * 34
    local row = _mk(label, cx, y, 360, 28, 13, 1, 1, 1, 0.0, false)
    table.insert(_menu.content, row)
    local toggle = _mk(tostring(value), cx + 380, y, 110, 28, 13, 1, 1, 0.3, 0.5, true)
    _bind(toggle, fn)
    table.insert(_menu.content, toggle)
    return toggle
end

local function _render_tab()
    _clear_content()
    local vp = require("client.common.ui_util").GetViewportSize()
    local cx = vp.X * 0.5 - 340

    local hdr = _mk("— " .. _menu.tabs[_menu.tab] .. " —", cx, 220, 520, 28, 14, 1, 0.85, 0.1, 0.0, false)
    table.insert(_menu.content, hdr)

    if _menu.tab == 1 then
        _content_row(0, "Player ESP", (_G._ESP.enabled and "ON" or "OFF"), function()
            _G._ESP.enabled = not _G._ESP.enabled; _render_tab()
        end)
        _content_row(1, "ESP Style: " .. _G._ESP.style, "CYCLE", function()
            local styles = {"auto","box","line","circle","skeleton","head","distance","name","health"}
            local i = 1
            for k, v in ipairs(styles) do if v == _G._ESP.style then i = k end end
            _G._ESP.style = styles[(i % #styles) + 1]
            _render_tab()
        end)
        _content_row(2, "Name Tags", (_G._ESP.name_on and "ON" or "OFF"), function()
            _G._ESP.name_on = not _G._ESP.name_on; _render_tab()
        end)
    elseif _menu.tab == 2 then
        _content_row(0, "Aimbot Strength", AIMBOT_STRENGTH .. "/100", function() end)
        _content_row(1, "Magic Bullet", (MB_ENABLED and "ON" or "OFF"), function()
            MB_ENABLED = not MB_ENABLED; _render_tab()
        end)
        _content_row(2, "MB Range", MB_RANGE .. "m", function() end)
    elseif _menu.tab == 3 then
        _content_row(0, "Vehicle Radar", "OFF", function() end)
        _content_row(1, "Vehicle Distance", "150m", function() end)
    elseif _menu.tab == 4 then
        _content_row(0, "Loot ESP", (_G._LOOT.enabled and "ON" or "OFF"), function()
            _G._LOOT.enabled = not _G._LOOT.enabled; _render_tab()
        end)
        _content_row(1, "Weapons", (_G._LOOT.weapons and "ON" or "OFF"), function()
            _G._LOOT.weapons = not _G._LOOT.weapons; _render_tab()
        end)
        _content_row(2, "Ammo", (_G._LOOT.ammo and "ON" or "OFF"), function()
            _G._LOOT.ammo = not _G._LOOT.ammo; _render_tab()
        end)
        _content_row(3, "Meds", (_G._LOOT.meds and "ON" or "OFF"), function()
            _G._LOOT.meds = not _G._LOOT.meds; _render_tab()
        end)
        _content_row(4, "Armor", (_G._LOOT.armor and "ON" or "OFF"), function()
            _G._LOOT.armor = not _G._LOOT.armor; _render_tab()
        end)
    elseif _menu.tab == 5 then
        _content_row(0, "iPad Perspective", (_G._GFX.ipad_perspective and "ON" or "OFF"), function()
            _G._GFX.SetIPad(not _G._GFX.ipad_perspective); _render_tab()
        end)
        _content_row(1, "FOV Degree (90-135)", _G._GFX.fov_degree, function()
            local d = _G._GFX.fov_degree + 5
            if d > 135 then d = 90 end
            _G._GFX.SetFOV(d); _render_tab()
        end)
        _content_row(2, "Visual Cleanup", (_G._GFX.visual_cleanup and "ON" or "OFF"), function()
            _G._GFX.SetCleanup(not _G._GFX.visual_cleanup); _render_tab()
        end)
        _content_row(3, "Potato Mode", (_G._GFX.potato_mode and "ON" or "OFF"), function()
            _G._GFX.SetPotato(not _G._GFX.potato_mode); _render_tab()
        end)
        _content_row(4, "FPS Unlock 165", (_G._GFX.fps_unlock and "ON" or "OFF"), function()
            _G._GFX.SetFPS(not _G._GFX.fps_unlock); _render_tab()
        end)
    end
end

local function _build()
    if _menu.root and slua.isValid(_menu.root) then
        return _menu.root
    end
    local vp = require("client.common.ui_util").GetViewportSize()
    local vx, vy = vp.X, vp.Y
    local root_x = (vx - 700) * 0.5
    local root_y = (vy - 400) * 0.5

    local root = _mk("", root_x, root_y, 700, 400, 14, 1, 1, 1, 0.92, false)
    if root then
        root:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        _menu.root = root
    end

    local tx = root_x + 10
    for i, name in ipairs(_menu.tabs) do
        local tb = _mk(name, tx, root_y + 10, 132, 26, 12, 1, 1, 1, 0.55, true)
        _bind(tb, function()
            _menu.tab = i
            _render_tab()
        end)
        table.insert(_menu.tab_btns, tb)
        tx = tx + 136
    end

    local sy = root_y + 44
    for i, sec in ipairs(_menu.sections) do
        local sb = _mk(sec, root_x + 550, sy, 140, 26, 11, 1, 1, 1, 0.55, true)
        _bind(sb, function() _menu.tab = math.min(i, 5); _render_tab() end)
        table.insert(_menu.side_btns, sb)
        sy = sy + 28
    end

    local cl = _mk("✕", root_x + 668, root_y + 10, 24, 24, 14, 1, 0.2, 0.2, 0.6, true)
    _bind(cl, function()
        _menu.open = false
        if _menu.root and slua.isValid(_menu.root) then
            _menu.root:SetWidgetVisibility(UEnums.ESlateVisibility.Collapsed)
        end
        _clear_content()
    end)

    _render_tab()
    print("[DEVIL MENU] UI built")
end

_G._Menu_Build  = _build
_G._Menu_Toggle = function()
    _menu.open = not _menu.open
    if _menu.open then _build() end
end
_G._Menu_Render = _render_tab
"""

# =============================================================
# MASTER TEMPLATE — GameplayData moved to TOP (fix #1)
# =============================================================
MASTER = Template(r"""
-- =============================================================
-- DEVIL MENU ULTIMATE — Generated by $bot_name
-- PROFILE: $profile | AIMBOT: $aimbot/100
-- MB: $mb_state @ ${mb_range}m ($mb_chance% roll)
-- ESP: $esp_style | NAME: $esp_name_state | LOOT: $loot_state
-- CROSSHAIR: $crosshair | LAYERS: 17
-- BUILT: $built_at
-- =============================================================

-- [[ [FIX #1] GameplayData loaded FIRST so all chunks below can use it ]]
local GameplayData = require("GameLua.GameCore.Data.GameplayData")
_G.GameplayData = GameplayData

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
    if _G._S_SHOT then _G._S_SHOT(true, false) end
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
    if _G._S_SHOT then _G._S_SHOT(true, false) end
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
        if _G._LOOT_Tick then _G._LOOT_Tick() end
        if _G._CH_Draw then _G._CH_Draw() end
        if _G._S_DRIFT then _G._S_DRIFT() end
    end)
end

local ticker = require("common.time_ticker")
if not _G._DEVIL_LOOP then
    _G._DEVIL_LOOP = true
    local function _loop() _Tick(); ticker.AddTimerOnce(0.016, _loop) end
    ticker.AddTimerOnce(0.5, _loop)
end

-- =============================================================
-- GAME HOOK — registers BRPlayerCharacterBase
-- =============================================================
local UEnums = UEnums
local BRPlayerCharacterBase = {
  ServerRPC = {},
  ClientRPC = {},
  MulticastRPC = {},
  LuaEventContainer = {}
}

BRPlayerCharacterBase.ServerRPC.ServerRPC_NearDeathGiveupRescue = { Reliable = true, Params = {} }
BRPlayerCharacterBase.ServerRPC.ServerRPC_CarryDeadBox = { Reliable = true, Params = { UEnums.EPropertyClass.Object } }
BRPlayerCharacterBase.ServerRPC.RPC_Server_GmPlayAction = { Reliable = true, Params = { UEnums.EPropertyClass.Int } }
BRPlayerCharacterBase.MulticastRPC.MulticastRPC_GmPlayAction = { Reliable = true, Params = { UEnums.EPropertyClass.Int } }
BRPlayerCharacterBase.ClientRPC.RPC_Client_SetShouldCheckPassWall = { Reliable = true, Params = { UEnums.EPropertyClass.Bool } }

function BRPlayerCharacterBase:ctor() end

function BRPlayerCharacterBase:_PostConstruct()
    BRPlayerCharacterBase.__super._PostConstruct(self)
    if Client then
        self:AddGameTimer(0.5, false, function()
            pcall(function()
                if not CheckExpiration() then ShowExpiredPopup(); return end
                if _G._Menu_Build then _G._Menu_Build() end
            end)
        end)
    end
end

function BRPlayerCharacterBase:ReceiveBeginPlay()
    BRPlayerCharacterBase.__super.ReceiveBeginPlay(self)
end

function BRPlayerCharacterBase:ReceiveEndPlay(reason)
    BRPlayerCharacterBase.__super.ReceiveEndPlay(self, reason)
end

local class = require("class")
local CCharacterBase = require("GameLua.GameCore.Framework.CharacterBase")
local CBRPlayerCharacterBase = class(CCharacterBase, nil, BRPlayerCharacterBase)
return require("combine_class").DeclareFeature(CBRPlayerCharacterBase, {
  { SkyTransition = "GameLua.Mod.BaseMod.Gameplay.Feature.SkyControl.PlayerCharacterSkyTransitionFeature" },
  { CarryDeadBoxFeature = "GameLua.Mod.Library.GamePlay.Feature.CarryDeadBoxFeature" },
  { SpecialSuitFeature = "GameLua.Mod.Library.GamePlay.Feature.SpecialSuitFeature" },
  { TeleportPawnFeature = "GameLua.Mod.Library.GamePlay.Feature.TeleportPawnFeature" },
  { LifterControl = "GameLua.Mod.BaseMod.Gameplay.Feature.Player.CharacterLifterControlFeature" },
  { FinalKillEffect = "GameLua.Mod.BaseMod.Gameplay.Feature.Player.PlayerCharacterFinalKillEffectFeature" },
  { CampFeature = "GameLua.Mod.BaseMod.GamePlay.Feature.Camp.PlayerCharacterCampFeature" },
  { BuildSkateFeature = "GameLua.Mod.BaseMod.GamePlay.Feature.PlayerCharacterBuildVehicleFeature" },
  { CommonBornlandTransformFeature = "GameLua.Mod.BaseMod.GamePlay.Feature.HeroPropFeature.CommonBornlandTransformFeature" },
  { ParachuteFormation = "GameLua.Mod.BaseMod.GamePlay.Feature.ParachuteFormationFeature" }
}, "BRPlayerCharacterBase")

print("[DEVIL MENU] LOADED — $profile | AIM:$aimbot | MB:${mb_range}m | 17 layers active")
""")

def _b(v): return "true" if v else "false"

def _presub(text, **kw):
    for k, v in kw.items():
        text = text.replace("$" + k, str(v))
    return text

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

    crosshair_lua = _presub(CROSSHAIR_LUA, crosshair=crosshair)
    esp_lua       = _presub(PLAYER_ESP_LUA,
                            esp_style=esp_style,
                            esp_rotate=esp_rot,
                            esp_name_bool=_b(esp_name))
    loot_lua      = _presub(LOOT_ESP_LUA, loot_enabled=_b(loot_on))

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
        crosshair       = crosshair,
        built_at        = time.strftime("%Y-%m-%d %H:%M:%S"),
        security_layers = "\n".join(SECURITY_LAYERS),
        crosshair_lua   = crosshair_lua,
        graphics_lua    = GRAPHICS_LUA,
        player_esp_lua  = esp_lua,
        loot_esp_lua    = loot_lua,
        menu_lua        = MENU_LUA,
    )

# =============================================================
# TELEGRAM BOT
# =============================================================
DEFAULT_SETTINGS = {
    "profile": "safe", "aimbot": 35, "mb_on": True, "mb_range": 20, "mb_chance": 15,
    "esp_style": "auto", "esp_rotate": 30, "esp_name": True,
    "loot_esp": True, "crosshair": "cross",
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
        f"*Loot:* `{'ON' if s['loot_esp'] else 'OFF'}` · *Crosshair:* `{s['crosshair']}`\n"
        f"*Layers:* `17` (9 engine + 8 behavioral)"
    )

def kb_main():
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
    txt = f"*{BOT_NAME}* — Devil Menu Ultimate\n\n{settings_text(s)}"
    if update.message:
        await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=kb_main())
    else:
        await update.callback_query.edit_message_text(txt, parse_mode="Markdown", reply_markup=kb_main())

async def cmd_full(u, c):
    s = get_settings(c); s.update(PROFILES["full"]); s["profile"]="full"
    await u.message.reply_text("🔴 Full.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=kb_main())

async def cmd_safe(u, c):
    s = get_settings(c); s.update(PROFILES["safe"]); s["profile"]="safe"
    await u.message.reply_text("🟢 Safe.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=kb_main())

async def cmd_random(u, c):
    s = get_settings(c); s.update(PROFILES["random"]); s["profile"]="random"
    await u.message.reply_text("🎲 Random.\n\n"+settings_text(s), parse_mode="Markdown", reply_markup=kb_main())

async def cmd_aimbot(u, c):
    s = get_settings(c)
    if not c.args: await u.message.reply_text("`/aimbot 1-100`", parse_mode="Markdown"); return
    try: v = int(c.args[0])
    except: await u.message.reply_text("Number."); return
    if not 1 <= v <= 100: await u.message.reply_text("1-100."); return
    s["aimbot"] = v
    await u.message.reply_text(f"🎯 `{v}/100`", parse_mode="Markdown")

async def cmd_mb(u, c):
    s = get_settings(c)
    if not c.args or c.args[0].lower() not in ("on","off"):
        await u.message.reply_text("`/mb on|off`", parse_mode="Markdown"); return
    s["mb_on"] = c.args[0].lower()=="on"
    await u.message.reply_text(f"💥 `{'ON' if s['mb_on'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_range(u, c):
    s = get_settings(c)
    if not c.args: await u.message.reply_text("`/range <m>`", parse_mode="Markdown"); return
    try: v = float(c.args[0])
    except: await u.message.reply_text("Number."); return
    if not 1 <= v <= 50: await u.message.reply_text("1-50."); return
    s["mb_range"] = v
    await u.message.reply_text(f"💥 `{v}m`", parse_mode="Markdown")

async def cmd_esp(u, c):
    s = get_settings(c)
    if not c.args or (c.args[0] not in ESP_STYLES and c.args[0] != "auto"):
        await u.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in ESP_STYLES)+", `auto`", parse_mode="Markdown"); return
    s["esp_style"] = c.args[0]
    await u.message.reply_text(f"👁 `{s['esp_style']}`", parse_mode="Markdown")

async def cmd_name(u, c):
    s = get_settings(c)
    if not c.args or c.args[0].lower() not in ("on","off"):
        await u.message.reply_text("`/name on|off`", parse_mode="Markdown"); return
    s["esp_name"] = c.args[0].lower()=="on"
    await u.message.reply_text(f"📛 `{'ON' if s['esp_name'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_loot(u, c):
    s = get_settings(c)
    if not c.args or c.args[0].lower() not in ("on","off"):
        await u.message.reply_text("`/loot on|off`", parse_mode="Markdown"); return
    s["loot_esp"] = c.args[0].lower()=="on"
    await u.message.reply_text(f"📦 `{'ON' if s['loot_esp'] else 'OFF'}`", parse_mode="Markdown")

async def cmd_crosshair(u, c):
    s = get_settings(c)
    if not c.args or c.args[0] not in CROSSHAIRS:
        await u.message.reply_text("Styles: "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown"); return
    s["crosshair"] = c.args[0]
    await u.message.reply_text(f"➕ `{s['crosshair']}`", parse_mode="Markdown")

async def cmd_settings(u, c):
    await u.message.reply_text(settings_text(get_settings(c)), parse_mode="Markdown", reply_markup=kb_main())

async def cmd_generate(u, c):
    await _send(u, c, get_settings(c))

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

async def on_cb(update, ctx):
    q = update.callback_query; await q.answer()
    d = q.data; s = get_settings(ctx)
    if d.startswith("preset:"):
        p = d.split(":",1)[1]
        if p in PROFILES: s.update(PROFILES[p]); s["profile"]=p
        await q.edit_message_text(f"*{p.upper()}*.\n\n{settings_text(s)}", parse_mode="Markdown", reply_markup=kb_main())
    elif d == "menu:aimbot":     await q.edit_message_text("`/aimbot 1-100`", parse_mode="Markdown")
    elif d == "menu:mb":         await q.edit_message_text("`/mb on|off` · `/range <m>`", parse_mode="Markdown")
    elif d == "menu:esp":        await q.edit_message_text("`/esp <style>` — "+", ".join(f"`{k}`" for k in ESP_STYLES), parse_mode="Markdown")
    elif d == "menu:name":       await q.edit_message_text("`/name on|off`", parse_mode="Markdown")
    elif d == "menu:loot":       await q.edit_message_text("`/loot on|off`", parse_mode="Markdown")
    elif d == "menu:crosshair":  await q.edit_message_text("`/crosshair <style>` — "+", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown")
    elif d == "menu:settings":   await q.edit_message_text(settings_text(s), parse_mode="Markdown", reply_markup=kb_main())
    elif d == "generate":
        await q.edit_message_text("Generating…"); await _send(update, ctx, s)

async def cmd_help(u, c):
    await u.message.reply_text(
        "*Commands*\n/start /full /safe /random\n/aimbot 1-100\n/mb on|off\n/range <m>\n"
        "/esp <style>\n/name on|off\n/loot on|off\n/crosshair <style>\n/settings\n/generate\n/help",
        parse_mode="Markdown")

def main():
    if not BOT_TOKEN: raise SystemExit("Set BOT_TOKEN env.")
    app = Application.builder().token(BOT_TOKEN).build()
    for cmd, fn in [("start",start),("full",cmd_full),("safe",cmd_safe),("random",cmd_random),
                    ("aimbot",cmd_aimbot),("mb",cmd_mb),("range",cmd_range),("esp",cmd_esp),
                    ("name",cmd_name),("loot",cmd_loot),("crosshair",cmd_crosshair),
                    ("settings",cmd_settings),("generate",cmd_generate),("help",cmd_help)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(on_cb))
    print(f"[{BOT_NAME}] running…")
    app.run_polling()

if __name__ == "__main__":
    main()
