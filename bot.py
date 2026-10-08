# bot.py — DEVIL MULTI-PROFILE BUILDER
# Profiles: only (ESP+aim+cross), esp_mb, wh_mb, wh
# Crosshair: 10 styles via /x_<name>
# Security: 19 to 30+ layers per file
# Python 3.10+ | python-telegram-bot v20+
import os, io, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_NAME  = os.environ.get("BOT_NAME", "devil_multi")

CROSSHAIRS = {
    "plus_dot":    "✛", "x_dot": "✖", "diamond": "◆", "star": "★",
    "ring_cross":  "⊕", "mini_cross": "+", "t_shape": "⊤",
    "triangle":    "△", "target": "◎", "dot": "●",
}

# =============================================================
# SECURITY LAYER BUILDING BLOCKS (stack up to 30)
# =============================================================
SEC_SYSCALL = r"""
-- [SYS] syscall indirection
local _sc = {}
_G._S_IMPORT = function(n) local h=_sc[n]; if h~=nil then return h end; local ok,c=pcall(import,n); _sc[n]=ok and c or nil; return _sc[n] end
"""
SEC_STRCRYPT = r"""
-- [STR] string crypt
local _sk={0x4D,0x21,0x7A,0x03,0x1E}
local function _sd(b) local o={} for i=1,#b do o[i]=string.char(bit32.bxor(b[i],_sk[(i-1)%#_sk+1])) end return table.concat(o) end
_G._S_STR={rwh=_sd({0x0E,0x05,0x0B,0x3F,0x77,0x4D,0x1F,0x3E,0x2A,0x32,0x6F,0x22,0x5B,0x12}),rab=_sd({0x0E,0x05,0x0B,0x3F,0x77,0x40,0x10,0x22,0x30,0x22,0x6F})}
"""
SEC_RPC = r"""
-- [RPC] rpc jitter
do local o=_G.SendRPC if o then _G.SendRPC=function(n,...) local j=0.02+math.random()*0.18 local a={...} a[#a+1]=string.rep("\0",math.random(4,32)) local t=0 local function f() t=t+0.016 if t>=j then return o(n,table.unpack(a)) end local tk=package.loaded["common.time_ticker"] if tk then tk.AddTimerOnce(0.016,f) end end f() end end end
"""
SEC_DRIFT = r"""
-- [DRIFT] behavior drift
local _d={a=0.55+math.random()*0.10,h=0.22+math.random()*0.08,r=0.28+math.random()*0.10,v=0.72+math.random()*0.10}
local function _st(v,lo,hi,s) v=v+(math.random()-0.5)*s if v<lo then v=lo+math.random()*s end if v>hi then v=hi-math.random()*s end return v end
_G._S_DRIFT=function() _d.a=_st(_d.a,0.42,0.72,0.010) _d.h=_st(_d.h,0.14,0.34,0.005) _d.r=_st(_d.r,0.20,0.42,0.008) _d.v=_st(_d.v,0.60,0.88,0.010) end
"""
SEC_THROTTLE = r"""
-- [THROTTLE] stat throttle
local _st={win=60,k={},hs=0,hits=0,last=os.time()} local _cap={hs=0.45,kpm=3.5}
_G._S_SHOT=function(ih,ik) local n=os.time() if n-_st.last>=_st.win then _st.k={};_st.hs=0;_st.hits=0;_st.last=n end _st.hits=_st.hits+1 if ih then _st.hs=_st.hs+1 end if ik then table.insert(_st.k,n) end end
_G._S_SCALE=function() local n=os.time() local w=0 for _,t in ipairs(_st.k) do if n-t<=_st.win then w=w+1 end end local kpm=w/(_st.win/60.0) local hs=_st.hits>0 and (_st.hs/_st.hits) or 0 local sc=1.0 if kpm>_cap.kpm then sc=sc*(_cap.kpm/kpm) end if hs>_cap.hs then sc=sc*(_cap.hs/hs) end if sc>1.0 then sc=1.0 end if sc<0.30 then sc=0.30 end return sc end
"""
SEC_ANTIDBG = r"""
-- [ADBG] anti-debug
do local o=debug and debug.sethook local t=0 if debug then debug.sethook=function(...) t=t+1 if t>=2 then _G._MOD_PAUSED=true end return o and o(...) end end end
"""
SEC_MEMATT = r"""
-- [MATT] mem attest
do local s={} local sd=os.time()%0x7FFFFFFF for i=1,32 do s[i]=(sd*1103515245+12345)%256 sd=s[i] end local o=_G.GetFileMD5 _G.GetFileMD5=function(p) if p and tostring(p):find("lua") then return string.format("%02x",table.unpack(s)) end if o then return o(p) end return "" end end
"""
SEC_TRAF = r"""
-- [TRAF] traffic shape
do local tk=package.loaded["common.time_ticker"] if tk and NetUtil and NetUtil.SendPacket then local o=NetUtil.SendPacket NetUtil.SendPacket=function(n,...) if math.random()<0.03 then tk.AddTimerOnce(0.05+math.random()*0.15,function() o(n,...) end) return nil end return o(n,...) end local function _f() pcall(function() o("KeepAlive",string.rep("\0",math.random(2,12))) end) tk.AddTimerOnce(1.5+math.random()*2.5,_f) end tk.AddTimerOnce(2.0,_f) end end
"""
SEC_KERNEL = r"""
-- [KRN] kernel subsystem spoof (deep)
pcall(function() local sm=pcall(require,"GameLua.GameCore.Module.Subsystem.SubsystemMgr") if not sm then return end local mgr=require("GameLua.GameCore.Module.Subsystem.SubsystemMgr") if not mgr then return end local k=mgr:Get("ClientKernelCheckSubsystem") if k then k.IsKernelClean=function() return true,{code=0} end k.GetKernelVersion=function() return "5.15.0-generic" end k.IsBootloaderLocked=function() return true end end local m=mgr:Get("ClientMemoryGuardSubsystem") if m then m.IsMemoryClean=function() return true,{code=0} end m.ScanResult=function() return "clean" end end end)
"""
SEC_FILEHASH = r"""
-- [FHASH] file hash spoof
do local orig=_G.VerifyFileSignature if orig then _G.VerifyFileSignature=function(...) return true end end local orig2=_G.CheckFileIntegrity if orig2 then _G.CheckFileIntegrity=function(...) return true,0 end end end
"""
SEC_PROCSCAN = r"""
-- [PSCAN] process scan hide
pcall(function() local o=_G.GetRunningProcesses if o then _G.GetRunningProcesses=function() return {} end end local o2=_G.ScanModules if o2 then _G.ScanModules=function() return {} end end end)
"""
SEC_HOOKHIDE = r"""
-- [HOOK] hook introspection hide
pcall(function() local A=import("Actor") if A then local mt=getmetatable(A) or {} mt.__index=function(t,k) local s=tostring(k) if s:find("Hook") or s:find("Detour") or s:find("Trampoline") then return nil end return rawget(t,k) end setmetatable(A,mt) end end)
"""
SEC_TIMECHK = r"""
-- [TIME] time tamper resist
do _G._DEVIL_T0=os.time() _G._DEVIL_TICK=0 local tk=package.loaded["common.time_ticker"] if tk then local function _tc() _G._DEVIL_TICK=_G._DEVIL_TICK+1 tk.AddTimerOnce(1.0,_tc) end tk.AddTimerOnce(1.0,_tc) end end
"""
SEC_PKTSIG = r"""
-- [PKTS] packet signature strip
pcall(function() if NetUtil and NetUtil.SendPacket then local o=NetUtil.SendPacket NetUtil.SendPacket=function(n,...) local a={...} for i=1,#a do if type(a[i])=="string" and #a[i]>256 then a[i]=a[i]:sub(1,128)..a[i]:sub(-64) end end return o(n,table.unpack(a)) end end end)
"""
SEC_LOGMASK = r"""
-- [LOG] log masker
pcall(function() local lf=package.loaded["common.log_filter"] if lf and lf.SetLogTreeEnable then local o=lf.SetLogTreeEnable lf.SetLogTreeEnable=function(...) _G._LOG_MASKED=true return o(...) end end end)
"""
SEC_UAPROT = r"""
-- [UAP] user agent spoof
pcall(function() local o=_G.GetDeviceUserAgent if o then _G.GetDeviceUserAgent=function() return "Mozilla/5.0 (Linux; Android 13)" end end end)
"""
SEC_MODRELOAD = r"""
-- [MRLD] module reload guard
do _G._MOD_LOAD_GUARD={} local o=require _G.require=function(n) if _G._MOD_LOAD_GUARD[n] then return _G._MOD_LOAD_GUARD[n] end local m=o(n) _G._MOD_LOAD_GUARD[n]=m return m end end
"""
SEC_MEMGUARD = r"""
-- [MGRD] memory guard bypass (deep)
pcall(function() local SubMgr=require("GameLua.GameCore.Module.Subsystem.SubsystemMgr") if SubMgr then for _,sn in ipairs({"ClientMemoryGuardSubsystem","ClientKernelCheckSubsystem","ClientAntiCheatSubsystem"}) do local s=SubMgr:Get(sn) if s then for k,v in pairs(s) do if type(v)=="function" then local kl=tostring(k):lower() if kl:find("scan") or kl:find("detect") or kl:find("check") or kl:find("verify") then s[k]=function() return true,{code=0,clean=true} end end end end end end end)
"""
SEC_ANTIDUMP = r"""
-- [ADMP] anti memory dump
pcall(function() local o=_G.MemoryDump if o then _G.MemoryDump=function() return nil end end end)
"""
SEC_SLEEPOBF = r"""
-- [SLP] sleep obfuscation
do local tk=package.loaded["common.time_ticker"] if tk then local o=tk.AddTimerOnce tk.AddTimerOnce=function(t,f) if t and t>=0.5 then t=t+math.random()*0.05 end return o(t,f) end end end
"""
SEC_ETWHIDE = r"""
-- [ETW] ETW-like hide
pcall(function() local o=_G.TraceLog if o then _G.TraceLog=function() return nil end end local o2=_G.RaiseEvent if o2 then _G.RaiseEvent=function() return nil end end end)
"""
SEC_ANTIQ = r"""
-- [AQ] anti quick-scan
do local _qs={} _G._S_QUICK=function(id) local n=os.time() if _qs[id] and (n-_qs[id])<0.5 then return false end _qs[id]=n return true end end
"""
SEC_MODVER = r"""
-- [MVER] module version spoof
pcall(function() local o=_G.GetModuleVersion if o then _G.GetModuleVersion=function() return "1.2.3-release" end end end)
"""
SEC_DEVMOCK = r"""
-- [DMCK] device mock
pcall(function() local o=_G.GetDeviceModel if o then _G.GetDeviceModel=function() return "SM-G991B" end end local o2=_G.GetBuildNumber if o2 then _G.GetBuildNumber=function() return "TP1A.220624.014" end end end)
"""
SEC_SIGNVER = r"""
-- [SVER] signature verify bypass
pcall(function() local o=_G.VerifySignature if o then _G.VerifySignature=function() return true end end end)
"""
SEC_ANTIFRIDA = r"""
-- [FRI] anti-frida detect mock
do if _G.frida then _G.frida=nil end _G.Process={} _G.Maps={} end
"""

SECURITY_POOL = [
    SEC_SYSCALL, SEC_STRCRYPT, SEC_RPC, SEC_DRIFT, SEC_THROTTLE,
    SEC_ANTIDBG, SEC_MEMATT, SEC_TRAF, SEC_KERNEL, SEC_FILEHASH,
    SEC_PROCSCAN, SEC_HOOKHIDE, SEC_TIMECHK, SEC_PKTSIG, SEC_LOGMASK,
    SEC_UAPROT, SEC_MODRELOAD, SEC_MEMGUARD, SEC_ANTIDUMP, SEC_SLEEPOBF,
    SEC_ETWHIDE, SEC_ANTIQ, SEC_MODVER, SEC_DEVMOCK, SEC_SIGNVER,
    SEC_ANTIFRIDA,
]

def build_layers(count):
    pool = SECURITY_POOL[:]
    # always keep first 8 (core) then add more randomly
    out = pool[:8]
    remaining = pool[8:]
    need = max(0, count - 8)
    if need > 0:
        if need >= len(remaining):
            out.extend(remaining)
        else:
            out.extend(remaining[:need])
    return "\n".join(out)

# =============================================================
# BASE BYPASS (from working CHIKU_OWNER file, unchanged)
# =============================================================
BYPASS = r"""
-- ========================================================================
-- [CORE] ULTIMATE WALLHACK BYPASS
-- ========================================================================
_G._executionLock = false
local function withLock(func) return function(...) if _G._executionLock then return end _G._executionLock=true local ok,err=pcall(func,...) _G._executionLock=false if not ok then print("[T] "..tostring(err)) end end end

local function InstallUltimateWallhackBypass()
    if _G.__ULTIMATE_WH_BYPASS_LOADED then return end
    local nop=function() end local retTrue=function() return true end local retFalse=function() return false end local retZero=function() return 0 end
    local function isBypassActive() return _G._WHA_BYPASS_ACTIVE and not _G._MOD_EXPIRED end
    pcall(function()
        local FPSP=import("PrimitiveSceneProxy")
        if FPSP then
            local o=FPSP.GetViewRelevance
            FPSP.GetViewRelevance=function(self,V) local VR=o(self,V) if isBypassActive() and VR then VR.bRenderCustomDepth=false VR.bUsesSceneDepth=false end return VR end
            local o2=FPSP.GetDepthPriorityGroup
            FPSP.GetDepthPriorityGroup=function(self) if not isBypassActive() then return o2(self) end return 0 end
        end
    end)
    pcall(function()
        local UMesh=import("MeshComponent")
        if UMesh then
            UMesh.__oGRCD=UMesh.GetRenderCustomDepth UMesh.GetRenderCustomDepth=function(s) if not isBypassActive() then return UMesh.__oGRCD(s) end return false end
            UMesh.__oIRCD=UMesh.IsRenderedOnCustomDepth UMesh.IsRenderedOnCustomDepth=function(s) if not isBypassActive() then return UMesh.__oIRCD(s) end return false end
            UMesh.__oGCDSV=UMesh.GetCustomDepthStencilValue UMesh.GetCustomDepthStencilValue=function(s) if not isBypassActive() then return UMesh.__oGCDSV(s) end return 0 end
            UMesh.__oSR=UMesh.ShouldRender UMesh.ShouldRender=function(s) if not isBypassActive() then return UMesh.__oSR(s) end return true end
            UMesh.__oIV=UMesh.IsVisible UMesh.IsVisible=function(s) if not isBypassActive() then return UMesh.__oIV(s) end return true end
        end
        local UPrim=import("PrimitiveComponent")
        if UPrim then
            for _,fn in ipairs({"IsRenderedOnCustomDepth","GetRenderCustomDepth","GetCustomDepthStencilValue","GetCustomDepthStencilWriteMask","GetVisibleFlag"}) do
                local o=UPrim[fn] UPrim["__o_"..fn]=o
                UPrim[fn]=function(self,...) if not isBypassActive() then return o(self,...) end if fn=="GetVisibleFlag" then return true end if fn=="GetCustomDepthStencilValue" then return 0 end return false end
            end
        end
    end)
    pcall(function()
        local UMat=import("Material") local UMatInst=import("MaterialInstance") local UMatDyn=import("MaterialInstanceDynamic")
        if UMat then
            UMat.GetDisableDepthTest=function() return false end UMat.GetBlendMode=function() return 0 end
            UMat.GetMaterialHash=function() return "F_HASH" end UMat.VerifyMaterial=retTrue
        end
        if UMatInst then UMatInst.GetDisableDepthTest=function() return false end UMatInst.GetBlendMode=function() return 0 end UMatInst.GetBaseMaterial=function() return nil end end
        if UMatDyn then
            UMatDyn.K2_GetVectorParameterValue=function(s,n) local nn=tostring(n or "") if nn:find("Color") or nn:find("Emissive") or nn:find("Tint") then return {R=255,G=255,B=255,A=255} end return {R=0,G=0,B=0,A=0} end
            UMatDyn.K2_GetScalarParameterValue=function(s,n) if tostring(n or ""):find("Emissive") then return 0.0 end return 0 end
        end
    end)
    pcall(function()
        local UObj=import("Object")
        if UObj and UObj.GetObjectsOfClass then UObj.GetObjectsOfClass=function(C,I) if isBypassActive() and C and tostring(C):find("MaterialInstanceDynamic") then return {} end return {} end end
    end)
    pcall(function()
        local SubMgr=require("GameLua.GameCore.Module.Subsystem.SubsystemMgr")
        if SubMgr then
            for _,sn in ipairs({"ClientWallhackDetectionSubsystem","ClientESPDetectionSubsystem","ClientAimTrackingSubsystem","ShootVerifySubSystemClient","ClientRenderCheckSubsystem","ClientMemoryGuardSubsystem","ClientKernelCheckSubsystem","ClientHawkEyePatrolSubsystem","ClientAntiCheatSubsystem","IntegrityCheckSubsystem","FileCheckSubsystem","AvatarExceptionSubsystem"}) do
                local sub=SubMgr:Get(sn)
                if sub then
                    for k,v in pairs(sub) do if type(v)=="function" then local kl=tostring(k) if kl:find("Report") or kl:find("Send") or kl:find("Verify") or kl:find("Check") or kl:find("Detect") or kl:find("Scan") then sub[k]=nop end end end
                    if sn=="ClientWallhackDetectionSubsystem" then sub.IsVisionNormal=retTrue sub.GetVisibilityRate=function() return math.random(70,82) end
                    elseif sn=="ClientESPDetectionSubsystem" then sub.HasESP=retFalse sub.CheckOverlay=function() return "clean" end
                    elseif sn=="ClientAimTrackingSubsystem" then sub.GetAimData=function() return {accuracy=math.random(48,58),headshotRate=math.random(18,28)} end sub.IsAimNormal=retTrue
                    elseif sn=="ClientMemoryGuardSubsystem" then sub.IsMemoryClean=function() return true,{code=0} end sub.ScanResult=function() return "clean" end
                    elseif sn=="ClientKernelCheckSubsystem" then sub.IsKernelClean=function() return true,{code=0,message="clean"} end sub.GetKernelVersion=function() return "5.4.0-generic" end sub.IsBootloaderLocked=retTrue
                    elseif sn=="ShootVerifySubSystemClient" then sub.OnShootVerifyFailed=nop sub.VerifyShot=retTrue
                    elseif sn=="ClientHawkEyePatrolSubsystem" then sub.GetPatrolData=function() return {} end sub.IsBeingWatched=retFalse sub.GetSpectatorCount=retZero
                    elseif sn=="ClientRenderCheckSubsystem" then sub.IsRenderClean=retTrue sub.GetRenderState=function() return "normal" end
                    end
                end
            end
        end
    end)
    pcall(function()
        if not _G.GameplayCallbacks then _G.GameplayCallbacks={} end
        local GC=_G.GameplayCallbacks
        for _,fn in ipairs({"ReportAttackFlow","ReportSecAttackFlow","ReportHurtFlow","ReportFireArms","ReportVerifyInfoFlow","ReportMrpcsFlow","ReportPlayerBehavior","ReportTeammatHurt","ReportPlayerMoveRoute","ReportPlayerPosition","ReportAimFlow","ReportHitFlow","ReportWallHack","ReportAimbot","ReportSpeedHack","ReportMagicBullet","ReportAbnormalMaterial","ReportDepthTestChange","ReportMemoryException","ReportMaterialScan","ReportShaderOverride","ReportCircleFlow","ReportESPBox","ReportESPHealth","ReportMiniMapESP","ReportEnemyFrameUI","ReportDistanceMarker","ReportWallhackESP","SendESPData","UploadESPInfo","OnPlayerRPCValidateFailed","OnPlayerActorChannelError","OnPlayerSpectateException","OnShutdownAfterError"}) do GC[fn]=nop end
    end)
    pcall(function()
        local t=_G.TssSdk if t then t.GetFileMD5=function() return "" end t.VerifyFileSignature=retTrue t.CheckIntegrity=retTrue t.ScanMemory=function() return true,{} end t.IsEmulator=retFalse t.OnRecvData=nop t.CheckKernel=function() return true,{status="verified",tampered=false} end t.VerifyBoot=function() return true,{locked=true,verified=true} end end
    end)
    pcall(function() local SS=import("ScreenshotMaker") or import("ScreenshotMTDer") if SS then SS.MakePicture=function() return "" end SS.ReMakePicture=function() return "" end SS.HasCaptured=retTrue end end)
    pcall(function()
        local hbc=pcall(require,"GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent")
        if hbc then local h=require("GameLua.Mod.BaseMod.Common.Security.HiggsBosonComponent") if h then h.bMHActive=false h.bCallPreReplication=false if h.ControlMHActive then h.ControlMHActive=nop end if h.StartAvatarCheck then h.StartAvatarCheck=nop end end end
        _G.BlackList={}
    end)
    pcall(function()
        local MM=InGameMarkTools and InGameMarkTools.ScreenMarkManager
        if MM then
            if MM.GetAllActiveMarks then local o=MM.GetAllActiveMarks MM.GetAllActiveMarks=function(self,...) local m=o(self,...) if not isBypassActive() or not m then return m end local out={} for _,x in ipairs(m) do local g=x.MarkGroupID if not (g==1006 or g==9999) then table.insert(out,x) end end return out end end
            if MM.OnAddMark then MM.OnAddMark=nop end if MM.OnRemoveMark then MM.OnRemoveMark=nop end
        end
    end)
    pcall(function() local UH=import("UIHelper") if UH and UH.GetAllWidgetsOfClass then UH.GetAllWidgetsOfClass=function() return {} end end end)
    pcall(function() if NetUtil and NetUtil.SendPacket then local o=NetUtil.SendPacket NetUtil.SendPacket=function(n,...) if isBypassActive() and n and tostring(n):lower():match("esp") then return nil end return o(n,...) end end end)
    _G.__ULTIMATE_WH_BYPASS_LOADED=true
    print("[BYPASS] installed")
end
InstallUltimateWallhackBypass()

local _cache={}
_G._S_IMPORT=function(n) local h=_cache[n] if h~=nil then return h end local ok,c=pcall(import,n) _cache[n]=ok and c or nil return _cache[n] end
"""

# =============================================================
# FEATURE: WALLHACK
# =============================================================
FEAT_WALLHACK = r"""
-- ========================================================================
-- [FEAT] WALLHACK
-- ========================================================================
local LinearColor=import("LinearColor")
local CONSOLE_READY=false local PROCESSED_PAWNS={} local TICK_COUNT=0 local WH_TIMER=nil
local TICK_INTERVAL=0.3 local MAX_PAWNS_PER_TICK=20 local RESET_PROCESSED_EVERY=6
local AVATAR_SLOTS={0,1,2,3,4,5,6,7}
local colors={vis=LinearColor(100,0,0,100),occ=LinearColor(100,100,0,100),bVis=LinearColor(100,0,100,100),bOcc=LinearColor(0,0,100,100)}
local function SetupConsole() if CONSOLE_READY then return end pcall(function() local K=import("KismetSystemLibrary") local w=slua.getWorld() if not K or not w then return end K.ExecuteConsoleCommand(w,"r.EnableDrawDyeingColor 1") K.ExecuteConsoleCommand(w,"r.CustomDepth 3") K.ExecuteConsoleCommand(w,"r.IdeaOutline.Enable 1") K.ExecuteConsoleCommand(w,"r.Highlight.Enable 1") CONSOLE_READY=true end) end
local function ApplyToMesh(mesh,visColor,occColor) if not mesh or not slua.isValid(mesh) then return end pcall(function() mesh:SetDrawDyeing(true) mesh:SetDrawDyeingMode(1) mesh:SetVisibleDyeingColor(visColor) mesh:SetOccludedDyeingColor(occColor) mesh:SetDyeingColorFadeDistance(99999.0) mesh:SetDyeingColorMinMaxDistance(0.0,99999.0) mesh:SetDrawHighlight(true) mesh:OverrideHighlightColor(visColor) mesh:SetHighlightCanBeOccluded(false) mesh:SetDrawIdeaOutline(true) mesh:SetIdeaOutlineNew(true) mesh:SetIdeaOutlineOcclusionHighlight(true) mesh:OverrideIdeaOutlineColor(visColor) mesh:SetIdeaOutlineOcclusionColor(occColor) mesh:OverrideIdeaOutlineThickness(20.0) mesh:SetIdeaOverrideOutlineAndOcclusion(true) mesh:SetRenderCustomDepth(true) mesh:SetCustomDepthStencilValue(255) end) end
local function IsPawnAlive(pawn) if not slua.isValid(pawn) then return false end if pawn.Health and pawn.Health>0 then return true end return false end
local function PBCtick()
    if not CheckExpiration() then ShowExpiredPopup() return end
    pcall(function()
        local localPawn=GameplayData.GetPlayerCharacter() if not slua.isValid(localPawn) then return end
        SetupConsole() if not colors then return end
        TICK_COUNT=TICK_COUNT+1 if TICK_COUNT%RESET_PROCESSED_EVERY==0 then PROCESSED_PAWNS={} end
        local myTeamId=localPawn.TeamID or 0 local allPawns=Game:GetAllPlayerPawns() or {} local processedCount=0
        for _,pawn in pairs(allPawns) do
            if processedCount>=MAX_PAWNS_PER_TICK then break end
            if not slua.isValid(pawn) or pawn==localPawn then goto continue end
            if pawn.PlayerKey and PROCESSED_PAWNS[pawn.PlayerKey] then goto continue end
            if IsPawnAlive(pawn) and pawn.TeamID and pawn.TeamID~=myTeamId then
                local isAI=false
                if pawn.IsAIPawn and type(pawn.IsAIPawn)=="function" then isAI=pawn:IsAIPawn() elseif Game.IsAI and type(Game.IsAI)=="function" then isAI=Game:IsAI(pawn) end
                local vis=isAI and colors.bVis or colors.vis local occ=isAI and colors.bOcc or colors.occ
                pcall(function()
                    if slua.isValid(pawn.Mesh) then ApplyToMesh(pawn.Mesh,vis,occ) end
                    local av=pawn.CharacterAvatarComp2_BP or (pawn.getAvatarComponent2 and pawn:getAvatarComponent2())
                    if av and av.GetMeshCompBySlot then for _,slot in ipairs(AVATAR_SLOTS) do local m=av:GetMeshCompBySlot(slot) if slua.isValid(m) then ApplyToMesh(m,vis,occ) end end end
                    local w=pawn.GetCurrentWeapon and pawn:GetCurrentWeapon()
                    if slua.isValid(w) and slua.isValid(w.Mesh) then ApplyToMesh(w.Mesh,vis,occ) end
                end)
                if pawn.PlayerKey then PROCESSED_PAWNS[pawn.PlayerKey]=true end
                processedCount=processedCount+1
            end
            ::continue::
        end
    end)
end
local function StartPBC()
    SetupConsole() if not colors then return false end
    if WH_TIMER then pcall(function() if _G.Game then _G.Game:RemoveGameTimer(WH_TIMER) end end) WH_TIMER=nil end
    local wrapped=withLock(PBCtick)
    if _G.Game and _G.Game.AddGameTimer then WH_TIMER=_G.Game:AddGameTimer(TICK_INTERVAL,true,wrapped) return true end
    local pc=slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if slua.isValid(pc) and pc.AddGameTimer then WH_TIMER=pc:AddGameTimer(TICK_INTERVAL,true,wrapped) return true end
    return false
end
local _rc=0
local function RetryStart() if _rc>=30 then return end _rc=_rc+1 if StartPBC() then print("[WH] ok") else if _G.Game and _G.Game.AddGameTimer then _G.Game:AddGameTimer(1.0,false,RetryStart) end end end
function _G.StartNewWallhack() if WH_TIMER then return end RetryStart() end
"""

# =============================================================
# FEATURE: CROSSHAIR
# =============================================================
def FEAT_CROSSHAIR(glyph):
    return r"""
-- ========================================================================
-- [FEAT] CROSSHAIR
-- ========================================================================
local BTN_BP="/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"
local _chW=nil
local function DrawCrosshair()
    pcall(function()
        if not _chW or not slua.isValid(_chW) then
            _chW=slua.loadUI(BTN_BP) if not _chW or not slua.isValid(_chW) then return end
            require("game_frontend_hud").AddToContainer(UIContainers.Top,_chW,12000)
            local WLL=import("WidgetLayoutLibrary") local slot=WLL.SlotAsCanvasSlot(_chW)
            if slot then slot:SetAnchors(FAnchors(0.5,0.5,0.5,0.5)) slot:SetAlignment(FVector2D(0.5,0.5)) slot:SetPosition(FVector2D(0,0)) slot:SetSize(FVector2D(40,40)) end
            if _chW.RichText_Content then local fi=_chW.RichText_Content.Font if fi then fi.Size=32 _chW.RichText_Content:SetFont(fi) end _chW.RichText_Content:SetColorAndOpacity(FSlateColor(FLinearColor(1,1,1,1))) end
            _chW:SetBackgroundColor(FLinearColor(0,0,0,0)) _chW:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
        end
        if _chW and _chW.RichText_Content then _chW.RichText_Content:SetText("GLYPH") end
    end)
end
_G._DrawCrosshair=DrawCrosshair
""".replace("GLYPH", glyph)

# =============================================================
# FEATURE: AIMBOT
# =============================================================
def FEAT_AIMBOT(strength):
    jitter = 0.00030 * (100 - strength) / 100
    return r"""
-- ========================================================================
-- [FEAT] AIMBOT (bullet track)
-- ========================================================================
local _btLastShootId=-1 local _btLastWeapon=nil local _btPendingFire=false local _btDeferFrames=0
local AIM_JITTER=JITTER

local function GetEnemyTargets()
    local r={} local p=GameplayData.GetPlayerCharacter() if not slua.isValid(p) then return r end
    local mt=p:GetTeamID() or 0
    pcall(function()
        local ASTExtra=import("STExtraPlayerCharacter") if not ASTExtra then return end
        local actors=Game:GetActorsByClass(ASTExtra) if not actors then return end
        local count=actors:Num() or 0
        for i=0,count-1 do local a=actors:Get(i) if slua.isValid(a) and a~=p then if a.GetTeamID and a:GetTeamID()~=mt then if a.IsAlive and a:IsAlive() then table.insert(r,a) end end end end
    end)
    return r
end
local function GetHeadPosition(actor)
    local hp=nil
    for _,b in ipairs({"Head","neck_01","Neck","head","Bip001-Head","Bip01-Head"}) do if not hp then pcall(function() hp=actor:GetBonePos(b,{X=0,Y=0,Z=0}) end) end end
    if not hp then pcall(function() hp=actor:GetHeadLocation(false) end) end
    if not hp then pcall(function() local l=actor:K2_GetActorLocation() if l then hp={X=l.X,Y=l.Y,Z=l.Z+160} end end) end
    return hp
end
local function ExecuteShot(player,weapon,pc,camLoc)
    pcall(function()
        local sc=weapon.ShootWeaponComponent if not sc then return end
        local cid=sc.CurShootID or -1 if cid==_btLastShootId then return end _btLastShootId=cid
        local ui=require("client.common.ui_util") if not ui then return end
        local vp=ui.GetViewportSize() if not vp then return end
        local cx=vp.X*0.5 local cy=vp.Y*0.5
        local enemies=GetEnemyTargets() local bd=99999 local bh=nil
        for _,e in ipairs(enemies) do
            local vis=false pcall(function() vis=pc:LineOfSightTo(e,camLoc,true) end)
            if vis then
                local hp=GetHeadPosition(e)
                if hp then
                    local s=import("Vector2D")()
                    if pc:ProjectWorldLocationToScreen(hp,s,false) then
                        if s.X>0 and s.Y>0 then
                            local d=math.sqrt((s.X-cx)^2+(s.Y-cy)^2)
                            if d<bd then bd=d bh=hp end
                        end
                    end
                end
            end
        end
        if not bh then return end
        local muzzle=nil
        pcall(function() local we=weapon.ShootWeaponEntityComp if we and we.GetMuzzleLocation then muzzle=we:GetMuzzleLocation() end end)
        if not muzzle then pcall(function() muzzle=player:GetBonePos("head",{X=0,Y=0,Z=0}) end) end
        if not muzzle then return end
        local rot=import("KismetMathLibrary").FindLookAtRotation(muzzle,bh)
        if not rot then return end
        rot.Pitch=rot.Pitch+(math.random()-0.5)*AIM_JITTER rot.Yaw=rot.Yaw+(math.random()-0.5)*AIM_JITTER
        sc:ShootBulletInner(bh,rot,cid)
        if _G._S_SHOT then _G._S_SHOT(true,false) end
    end)
end
local function BulletTrack()
    if not CheckExpiration() then ShowExpiredPopup() return end
    pcall(function()
        local player=GameplayData.GetPlayerCharacter() if not slua.isValid(player) then return end
        local wm=player.WeaponManagerComponent if not wm then return end
        local weapon=wm.CurrentWeaponReplicated if not slua.isValid(weapon) then return end
        if weapon~=_btLastWeapon then _btLastWeapon=weapon _btLastShootId=-1 _btPendingFire=false _btDeferFrames=0 end
        local pc=player:GetPlayerControllerSafety() if not slua.isValid(pc) then return end
        local cam=import("GameplayStatics").GetPlayerCameraManager(pc,0) if not slua.isValid(cam) then return end
        local camLoc=cam:GetCameraLocation() if not camLoc then return end
        local sc=weapon.ShootWeaponComponent if not sc then return end
        local cid=sc.CurShootID or -1
        local ns=(cid~=_btLastShootId and cid~=-1) or player.bIsWeaponFiring
        if ns and not _btPendingFire then _btPendingFire=true _btDeferFrames=1 return end
        if _btPendingFire then if _btDeferFrames>0 then _btDeferFrames=_btDeferFrames-1 return end _btPendingFire=false ExecuteShot(player,weapon,pc,camLoc) end
    end)
end
if not _G._DEVIL_BT then
    _G._DEVIL_BT=true
    local tk=require("common.time_ticker")
    local function _btLoop() pcall(BulletTrack) tk.AddTimerOnce(0.016,_btLoop) end
    tk.AddTimerOnce(0.5,_btLoop)
end
""".replace("JITTER", str(jitter))

# =============================================================
# FEATURE: MAGIC BULLET
# =============================================================
def FEAT_MB(range_m, chance):
    return r"""
-- ========================================================================
-- [FEAT] MAGIC BULLET (capped)
-- ========================================================================
local MB_RANGE=RANGEM local MB_CHANCE=CHANCE
local function GetEnemiesMB()
    local r={} local p=GameplayData.GetPlayerCharacter() if not slua.isValid(p) then return r end
    local mt=p:GetTeamID() or 0
    for _,e in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(e) and e~=p then local t=e.TeamID or 0 if t~=mt and (e.Health or 0)>0 then table.insert(r,e) end end
    end
    return r
end
local function MB_Head(a)
    for _,b in ipairs({"Head","head","neck_01","Bip001-Head","Bip01-Head"}) do local ok,pos=pcall(function() return a:GetBonePos(b,{X=0,Y=0,Z=0}) end) if ok and pos then return pos end end
    local ok,loc=pcall(function() return a:K2_GetActorLocation() end)
    if ok and loc then return {X=loc.X,Y=loc.Y,Z=loc.Z+160} end
end
local function MB_Tick()
    if not CheckExpiration() then return end
    if math.random(100)>MB_CHANCE then return end
    pcall(function()
        local player=GameplayData.GetPlayerCharacter() if not slua.isValid(player) then return end
        local wm=player.WeaponManagerComponent if not wm then return end
        local weapon=wm.CurrentWeaponReplicated if not slua.isValid(weapon) then return end
        local shoot=weapon.ShootWeaponComponent if not shoot then return end
        local mp=player:K2_GetActorLocation()
        local near,nd=nil,99999
        for _,e in ipairs(GetEnemiesMB()) do
            local el=e:K2_GetActorLocation()
            local d=math.sqrt((mp.X-el.X)^2+(mp.Y-el.Y)^2+(mp.Z-el.Z)^2)/100
            if d<nd then nd=d near=e end
        end
        if not near or nd>MB_RANGE then return end
        local head=MB_Head(near) if not head then return end
        local muzzle=nil
        pcall(function() muzzle=player:GetBonePos("head",{X=0,Y=0,Z=0}) end)
        if not muzzle then return end
        local rot=import("KismetMathLibrary").FindLookAtRotation(muzzle,head)
        shoot:ShootBulletInner(head,rot,shoot.CurShootID or -1)
        if _G._S_SHOT then _G._S_SHOT(true,false) end
    end)
end
if not _G._DEVIL_MB then
    _G._DEVIL_MB=true
    local tk=require("common.time_ticker")
    local function _mbLoop() pcall(MB_Tick) tk.AddTimerOnce(0.05,_mbLoop) end
    tk.AddTimerOnce(1.0,_mbLoop)
end
""".replace("RANGEM", str(range_m)).replace("CHANCE", str(chance))

# =============================================================
# FEATURE: NAME ESP
# =============================================================
FEAT_NAMES = r"""
-- ========================================================================
-- [FEAT] NAME ESP
-- ========================================================================
local BTN_BP_N="/Game/UMG/UI_BP/Common/BaseComponent/CommonBaseComponent_TextButton_UIBP.CommonBaseComponent_TextButton_UIBP"
local _nameTags={}
local function _getName(pawn)
    local n=nil
    pcall(function() n=pawn.PlayerName end)
    if not n then pcall(function() n=pawn:GetPlayerName() end) end
    if not n then pcall(function() local ps=pawn:GetPlayerStateSafety() if slua.isValid(ps) then n=ps.PlayerName end end) end
    if not n and pawn.PlayerKey then n="Bot_"..tostring(pawn.PlayerKey) end
    return tostring(n or "?")
end
local function UpdateNameTags()
    local pc=slua_GameFrontendHUD and slua_GameFrontendHUD:GetPlayerController()
    if not slua.isValid(pc) then return end
    local me=GameplayData.GetPlayerCharacter() if not slua.isValid(me) then return end
    local mt=me.TeamID or 0 local seen={}
    for _,p in pairs(Game:GetAllPlayerPawns() or {}) do
        if slua.isValid(p) and p~=me then
            local t=p.TeamID or 0
            if t~=mt and (p.Health or 0)>0 then
                local key=p.PlayerKey or tostring(p) seen[key]=true
                local w=_nameTags[key]
                if not w or not slua.isValid(w) then
                    pcall(function()
                        w=slua.loadUI(BTN_BP_N) if not w or not slua.isValid(w) then return end
                        require("game_frontend_hud").AddToContainer(UIContainers.Top,w,9000)
                        if w.RichText_Content then local fi=w.RichText_Content.Font if fi then fi.Size=13 w.RichText_Content:SetFont(fi) end w.RichText_Content:SetColorAndOpacity(FSlateColor(FLinearColor(1,0.85,0,1))) end
                        w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible) w:SetBackgroundColor(FLinearColor(0,0,0,0.5))
                        _nameTags[key]=w
                    end)
                    w=_nameTags[key]
                end
                if w and slua.isValid(w) then
                    pcall(function()
                        local loc=p:K2_GetActorLocation()
                        local s=import("Vector2D")()
                        if pc:ProjectWorldLocationToScreen({X=loc.X,Y=loc.Y,Z=loc.Z+200},s,false) then
                            w:SetWidgetVisibility(UEnums.ESlateVisibility.SelfHitTestInvisible)
                            w:SetPositionInViewport(FVector2D(s.X-70,s.Y-20),true)
                            w:SetDesiredSizeInViewport(FVector2D(140,20))
                            local nm=_getName(p)
                            local mp=me:K2_GetActorLocation()
                            local d=math.sqrt((mp.X-loc.X)^2+(mp.Y-loc.Y)^2+(mp.Z-loc.Z)^2)/100
                            nm=nm.." ["..string.format("%.0fm",d).."]"
                            if w.RichText_Content then w.RichText_Content:SetText(nm) end
                        else w:SetWidgetVisibility(UEnums.ESlateVisibility.Hidden) end
                    end)
                end
            end
        end
    end
    for k,w in pairs(_nameTags) do if not seen[k] and slua.isValid(w) then w:SetWidgetVisibility(UEnums.ESlateVisibility.Hidden) end end
end
_G._UpdateNameTags=UpdateNameTags
"""

# =============================================================
# FEATURE: LOOT ESP
# =============================================================
FEAT_LOOT = r"""
-- ========================================================================
-- [FEAT] LOOT ESP
-- ========================================================================
local lootGreen=import("LinearColor")(0,100,0,100)
local function ApplyLoot(m)
    if not m or not slua.isValid(m) then return end
    pcall(function() m:SetDrawDyeing(true) m:SetDrawDyeingMode(1) m:SetVisibleDyeingColor(lootGreen) m:SetOccludedDyeingColor(lootGreen) m:SetDyeingColorFadeDistance(99999.0) m:SetDrawIdeaOutline(true) m:SetIdeaOutlineNew(true) m:OverrideIdeaOutlineColor(lootGreen) m:OverrideIdeaOutlineThickness(6.0) end)
end
local function UpdateLoot()
    pcall(function()
        local me=GameplayData.GetPlayerCharacter() if not slua.isValid(me) then return end
        local mp=me:K2_GetActorLocation()
        for _,cn in ipairs({"PickupActor","PlayerTombBox","AirDropBox","PickupActorBase"}) do
            local ok,cls=pcall(import,cn)
            if ok and cls then
                local actors=Game:GetActorsByClass(cls)
                if actors and actors.Num then
                    for i=0,actors:Num()-1 do
                        local a=actors:Get(i)
                        if slua.isValid(a) then
                            local loc=a:K2_GetActorLocation()
                            local d=math.sqrt((mp.X-loc.X)^2+(mp.Y-loc.Y)^2+(mp.Z-loc.Z)^2)/100
                            if d<=150 then local m=a.Mesh or a.StaticMeshComponent or a.SkeletalMeshComponent if m then ApplyLoot(m) end end
                        end
                    end
                end
            end
        end
    end)
end
_G._UpdateLoot=UpdateLoot
"""

# =============================================================
# BASE SKELETON (from working file)
# =============================================================
def build_skeleton(extra_hooks=""):
    return r"""
-- ========================================================================
-- EXPIRY
-- ========================================================================
local EXPIRY_TIMESTAMP=os.time({year=2027,month=10,day=28,hour=22,min=40,sec=0})
local TELEGRAM_LINK="https://t.me/devil_owner"
local _expiredShown=false
local function CheckExpiration() if os.time()>=EXPIRY_TIMESTAMP then _G._MOD_EXPIRED=true return false end _G._MOD_EXPIRED=false return true end
local function ShowExpiredPopup() if _expiredShown then return end _expiredShown=true pcall(function() local Msg=require("client.slua.logic.common.logic_common_msg_box") Msg.Show(4,"[DEVIL] EXPIRED","Trial complete.",function() end) end) end
_G.CheckExpiration=CheckExpiration _G.ShowExpiredPopup=ShowExpiredPopup
print("[DEVIL] loading...")

local BRPlayerCharacterBase={ServerRPC={},ClientRPC={},MulticastRPC={},LuaEventContainer={}}
BRPlayerCharacterBase.ServerRPC.ServerRPC_NearDeathGiveupRescue={Reliable=true,Params={}}
BRPlayerCharacterBase.ServerRPC.ServerRPC_CarryDeadBox={Reliable=true,Params={UEnums.EPropertyClass.Object}}
BRPlayerCharacterBase.ServerRPC.RPC_Server_GmPlayAction={Reliable=true,Params={UEnums.EPropertyClass.Int}}
BRPlayerCharacterBase.MulticastRPC.MulticastRPC_GmPlayAction={Reliable=true,Params={UEnums.EPropertyClass.Int}}
BRPlayerCharacterBase.ClientRPC.RPC_Client_SetShouldCheckPassWall={Reliable=true,Params={UEnums.EPropertyClass.Bool}}

local ENetRole=import("ENetRole") local EPawnState=import("EPawnState")
local ESpecialMovementType=import("ESpecialMovementType") local ESpiderSwingMoveState=import("ESpiderSwingMoveState")
local ESurviveWeaponPropSlot=import("ESurviveWeaponPropSlot") local EParachuteState=import("EParachuteState")
local EMovementMode=import("EMovementMode") local EStateType=import("EStateType")
local ESTEPoseState=import("ESTEPoseState") local EGameModeType=import("EGameModeType")
local STExtraGameStateBase=import("STExtraGameStateBase") local UKismetSystemLibrary=import("KismetSystemLibrary")
local USTExtraBlueprintFunctionLibrary=import("STExtraBlueprintFunctionLibrary")
local GameplayData=require("GameLua.GameCore.Data.GameplayData")
local GamePlayTools=require("GameLua.Mod.BaseMod.Common.GamePlayTools")
local MatchModeIds=require("GameLua.Mod.BaseMod.GamePlay.Config.MatchModeIdsConfig")

EXTRAS

function BRPlayerCharacterBase:ctor() end
function BRPlayerCharacterBase:_PostConstruct()
  BRPlayerCharacterBase.__super._PostConstruct(self)
  self:InitAddSpecialMoveInfo()
  self.bCanNearDeathGiveup=true
  pcall(function()
    if not CheckExpiration() then ShowExpiredPopup() return end
    _G._WHA_BYPASS_ACTIVE=true
    if _G.StartNewWallhack then _G.StartNewWallhack() end
  end)
  if Client then
    self:AddGameTimer(0.5,false,function() pcall(function() if _G._UpdateNameTags then _G._UpdateNameTags() end end) end)
    self:AddGameTimer(0.5,false,function() pcall(function() if _G._UpdateLoot then _G._UpdateLoot() end end) end)
    self:AddGameTimer(0.1,false,function() pcall(function() if _G._DrawCrosshair then _G._DrawCrosshair() end end) end)
  end
end

function BRPlayerCharacterBase:ReceiveBeginPlay()
  BRPlayerCharacterBase.__super.ReceiveBeginPlay(self)
  self:AddControlEvent(self,"MovementModeChangedDelegate",self.HandleOnMovementModeChangedNew,self)
  if self:HasAuthority() and self:CheckAddCheckFallingDistanceComponent() then
    local C=import("CheckFallingDistanceComponent")
    if slua.isValid(C) and not slua.isValid(self:GetComponentByClass(C)) then Game:AddComponent(C,self,"CheckFallingDistanceComponent") end
  end
  if slua.isValid(self.STCharacterMovement) then self.STCharacterMovement.bPositiveBlowUp=true end
  if self.Role==ENetRole.ROLE_AutonomousProxy then
    self:AddControlEvent(self,"OnPawnStateDisabled",self.OnPawnStateChange,self)
    self:AddControlEvent(self,"OnPawnStateEnabled",self.OnPawnStateChange,self)
    self:AddControlEventConditionOnly(self,"OnAttrChangeEventDelegate",{AttrName={"bCanSelfRescue"}},self.CharacterAttrChangeEvent,self)
  end
  if Client then GameplayData.AddCharacter(self.Object)
  else self:AddCommonEventWithConditions(EVENTTYPE_INGAME_NORMAL,EVENTID_GAME_MODE_STATE_CHANGE,{[1]="FinishedState"},self.HandleFinishedState,self) end
end

function BRPlayerCharacterBase:CharacterAttrChangeEvent(uPawn,AttrName,AttrVal)
  BRPlayerCharacterBase.__super.CharacterAttrChangeEvent(self,uPawn,AttrName,AttrVal)
  if self.Object~=uPawn then return end
  if self.Role==ENetRole.ROLE_AutonomousProxy and AttrName=="bCanSelfRescue" then local uPC=self:GetPlayerControllerSafety() if slua.isValid(uPC) then uPC:BroadcastUIMessage("UIMsg_CanSelfRescue",0,"","") end end
end
function BRPlayerCharacterBase:OnPawnStateChange(PawnState)
  if PawnState==EPawnState.SwitchPP then local uPC=self:GetPlayerControllerSafety() if slua.isValid(uPC) then uPC:BroadcastUIMessage("UIMsg_FPPModeChange",0,"","") end end
end
function BRPlayerCharacterBase:HandleFinishedState()
  if slua.isValid(self.STCharacterMovement) and self.STCharacterMovement.SetDynamicSimpleQueryConfigDisable then local M=import("EDynamicSimpleQueryConfigDisableMask") self.STCharacterMovement:SetDynamicSimpleQueryConfigDisable(M.Bit0,true) end
end
function BRPlayerCharacterBase:CheckAddCheckFallingDistanceComponent()
  if CGameMode and CGameMode.GameModeType and CGameState and CGameState.GameModeID then
    local GT=CGameMode.GameModeType local GID=tonumber(CGameState.GameModeID)
    local bT=GT==EGameModeType.ETypicalGameMode or GT==EGameModeType.EFourInOneGameMode or GT==EGameModeType.EHeavyWeaponGameMode
    local bI=not MatchModeIds[GID] return bT and bI
  end
  return false
end
function BRPlayerCharacterBase:LuaHandleParachuteStateChanged(L,N)
  BRPlayerCharacterBase.__super.LuaHandleParachuteStateChanged(self,L,N)
  if not Client then local uPC=self:GetPlayerControllerSafety() if slua.isValid(uPC) and uPC.CheckParachuteOpenFeature then
    if N==EParachuteState.PS_Opening then if uPC.CheckParachuteOpenFeature.SatrtCheckShowParachuteCloseUI then uPC.CheckParachuteOpenFeature:SatrtCheckShowParachuteCloseUI() end
    elseif N==EParachuteState.PS_None then if uPC.CheckParachuteOpenFeature.RecoverParachuteOpenParam then uPC.CheckParachuteOpenFeature:RecoverParachuteOpenParam() end if uPC.CheckParachuteOpenFeature.ClearTimerAndState then uPC.CheckParachuteOpenFeature:ClearTimerAndState() end end
  end end
end
function BRPlayerCharacterBase:OnLanded()
  if self.HandleOnLanded then self:HandleOnLanded(-1) end
  if not Client then local uPC=self:GetPlayerControllerSafety() if slua.isValid(uPC) and uPC.CheckParachuteOpenFeature then if uPC.CheckParachuteOpenFeature.ClearTimerAndState then uPC.CheckParachuteOpenFeature:ClearTimerAndState() end if uPC.CheckParachuteOpenFeature.ResetCheckShowUI then uPC.CheckParachuteOpenFeature:ResetCheckShowUI() end end end
end
function BRPlayerCharacterBase:ReceiveEndPlay(reason) BRPlayerCharacterBase.__super.ReceiveEndPlay(self,reason) if Client then GameplayData.RemoveCharacter(self.Object) end end
function BRPlayerCharacterBase:IsWarGameMode() local gs=GameplayData:GetGameState() if slua.isValid(gs) and Game:IsClassOf(gs,STExtraGameStateBase) then return gs.GameModeType==EGameModeType.EWarGameMode end return false end
function BRPlayerCharacterBase:BPOnRecycled() if Client then self:ResetMeshRelativeLocationAndRotation() end end
function BRPlayerCharacterBase:BPOnRespawned() if Client then self:ResetMeshRelativeLocationAndRotation() end end
function BRPlayerCharacterBase:ReceiveOnRecycle() if Client then self:ResetMeshRelativeLocationAndRotation() GameplayData.RemoveCharacter(self.Object) end end
function BRPlayerCharacterBase:ReceiveOnSpawn() if Client then self:ResetMeshRelativeLocationAndRotation() GameplayData.AddCharacter(self.Object) end end
function BRPlayerCharacterBase:ResetMeshRelativeLocationAndRotation()
  if Game:IsValid(self.Object) and Game:IsValid(self.Mesh) then local rot=FRotator(0,-90,0) local loc=FVector(0,0,0) if self.Mesh.K2_SetRelativeRotation then self.Mesh:K2_SetRelativeRotation(rot,false,nil,false) end self:CacheInitialMeshOffset(loc,rot) end
end
function BRPlayerCharacterBase:HandleOnMovementModeChangedNew()
  if Game:IsValid(self.STCharacterMovement) and self.STCharacterMovement.MovementMode==EMovementMode.MOVE_Swimming and self:CheckBaseIsMoveable() then self.CharacterMovement:SetBase(nil,"",true) end
  if self.Role==ENetRole.ROLE_AutonomousProxy and Game:IsValid(self.STCharacterMovement) and self.STCharacterMovement.MovementMode==EMovementMode.MOVE_Walking and UIManager.UI_Config_InGame.ParachuteOpenUI then UIManager.CloseUI(UIManager.UI_Config_InGame.ParachuteOpenUI) end
end
function BRPlayerCharacterBase:BPOnMissPlayerDamageRecord() end
function BRPlayerCharacterBase:PreAttachedToVehicle()
  local IsDS=UKismetSystemLibrary.IsDedicatedServer(self) if not IsDS then return end
  local MPC=self:GetPlayerControllerSafety() if not slua.isValid(MPC) then return end
  local CAC=self.CharacterAvatarComp2_BP if not slua.isValid(CAC) then return end
  local CA=require("GameLua.Activity.Commercialize.GamePlay.CommerAvatarDataUtil")
  local cid=CA:ChangeVehicleSkinByClothes(MPC,CAC)
  local VST=import("ESTExtraVehicleShapeType")
  if cid then local AU=import("AvatarUtils") if AU.GetVehicleShapeBySkinID(cid)==VST.VST_Horse then local ps=self:GetPlayerStateSafety() if slua.isValid(ps) then ps:AddGeneralCount(468,1,false) end end end
end
function BRPlayerCharacterBase:ParachuteJump()
  local uPC=self:GetControllerSafety()
  if slua.isValid(uPC) then
    if not self:GetEnsure() then if uPC:GetCurrentStateType()~=EStateType.State_ParachuteJump and uPC:GetCurrentStateType()~=EStateType.State_ParachuteOpen then self:SwitchPoseState(ESTEPoseState.Stand,true,true,true,false) uPC:ReInitParachuteItem() uPC:ServerChangeStatePC(EStateType.State_ParachuteJump) end
    else EventSystem:postEvent(EVENTTYPE_INGAME_NORMAL,EVENTID_AI_CALL_PARACHUTE_JUMP,self.Object) end
  end
end
function BRPlayerCharacterBase:OnMovementBaseChangedEvent(uC,uN,uO)
  if uC~=self.Object then return end
  local MC=self:GetMedievalCraneFromBase(uN)
  if MC and MC.AddCharacter then MC:AddCharacter(self.Object) else MC=self:GetMedievalCraneFromBase(uO) if MC and MC.RemoveCharacter then MC:RemoveCharacter(self.Object) end end
end
function BRPlayerCharacterBase:GetMedievalCraneFromBase(B) if not slua.isValid(B) or not B.GetOwner then return end local L=B:GetOwner() if not slua.isValid(L) then return end if not L.AddCharacter then return end return L end
function BRPlayerCharacterBase:CheckForbidFlaregun()
  local ps=self:GetPlayerStateSafety() if not slua.isValid(ps) then return false end
  if ps.CanUseFlaregun==false and self:IsLocallyControlled() then local uPC=self:GetPlayerControllerSafety() if slua.isValid(uPC) then uPC:DisplayGameTipWithMsgID(48532) end end
  return not ps.CanUseFlaregun
end
function BRPlayerCharacterBase:ServerRPC_NearDeathGiveupRescue() self:HandleNearDeathGiveupRescue() end
function BRPlayerCharacterBase:HandleNearDeathGiveupRescue()
  local c=self.NearDeatchComponent
  if self:IsNearDeath() and slua.isValid(c) and self.bCanNearDeathGiveup==true then local ps=self:GetPlayerStateSafety() if slua.isValid(ps) then ps:AddGeneralCount(1613,1,false) end c:TriggerGotoDieExplictly(self.Object) end
end
function BRPlayerCharacterBase:RPC_Server_GmPlayAction(a) if USTExtraBlueprintFunctionLibrary.IsDevelopment() then self:MulticastRPC_GmPlayAction(a) end end
function BRPlayerCharacterBase:MulticastRPC_GmPlayAction(a)
  if not Client then return end
  local uPEC=self:GetPlayEmoteComponent() if not slua.isValid(uPEC) then return end
  local LF=require("common.log_filter") LF.SetLogTreeEnable(true)
  local cfg=CDataTable.GetTableData("EmoteBPTable",a) if not cfg then return end
  local EHA=slua.loadObject(cfg.Path)
  local arr=slua.Array(UEnums.EPropertyClass.Struct,import("/Script/CoreUObject.SoftObjectPath"))
  local h=EHA() uPEC:OnLoadEmoteAssetBegin(h,a,arr,"")
  local tb=FuncUtil.LuaArrayToTable(arr)
  local au=require("common.asset_util") au.GetAssetsArrayAsyncParallel(tb,function() uPEC:OnLoadEmoteAssetEnd(h,a,0) end)
end
function BRPlayerCharacterBase:RPC_Client_SetShouldCheckPassWall(b) if slua.isValid(self.ParachuteComponent) then self.ParachuteComponent.bServerSyncShouldCheckPassWall=b end end
function BRPlayerCharacterBase:OnPlayerEnterCarryBoxState() self.Super:OnPlayerEnterCarryBoxState() if self.CarryDeadBoxFeature then self.CarryDeadBoxFeature:OnPlayerEnterCarryBoxState() end end
function BRPlayerCharacterBase:OnPlayerLeaveCarryBoxState(b) self.Super:OnPlayerLeaveCarryBoxState(b) if self.CarryDeadBoxFeature then self.CarryDeadBoxFeature:OnPlayerLeaveCarryBoxState(b) end end
function BRPlayerCharacterBase:ServerRPC_CarryDeadBox(u) if slua.isValid(u) and Game:IsClassOf(u,import("/Script/ShadowTrackerExtra.PlayerTombBox")) and self.CarryDeadBoxFeature then self.CarryDeadBoxFeature:CarryDeadBox(u) end end
function BRPlayerCharacterBase:SetAreaID(a) self:SetAttrValue("AreaID",a,-1) end
function BRPlayerCharacterBase:GetAreaID() return math.floor(self:GetAttrValue("AreaID")+0.5) end
function BRPlayerCharacterBase:CannotChangeIntoPetSpectator() return self.bCannotChangeIntoPetSpectator end
function BRPlayerCharacterBase:DoModChangeToBT() if self:HasState(EPawnState.SpecialSuit) then self:TriggerEntrySkillWithID(4301101,true) end end
function BRPlayerCharacterBase:SwitchCameraToParachuteOpening() self.Super:SwitchCameraToParachuteOpening() if self.ParachuteFormation and self.ParachuteFormation.ShouldApplyFormationCamera and self.ParachuteFormation:ShouldApplyFormationCamera() then self.ParachuteFormation:OverlayFormationCameraParams() end end
function BRPlayerCharacterBase:SwitchCameraToParachuteFalling() self.Super:SwitchCameraToParachuteFalling() if self.ParachuteFormation and self.ParachuteFormation.ShouldApplyFormationCamera and self.ParachuteFormation:ShouldApplyFormationCamera() then self.ParachuteFormation:OverlayFormationCameraParams() end end
function BRPlayerCharacterBase:SwitchCameraToNormal() self.Super:SwitchCameraToNormal() if self.ParachuteFormation and self.ParachuteFormation.OnLandingClearFormationCamera then self.ParachuteFormation:OnLandingClearFormationCamera() end end
function BRPlayerCharacterBase:SwitchWeaponCheck(Slot,IgnoreState)
  if self:HasState(EPawnState.AttachToOther) then local W=self:GetWeaponBySlot(Slot) if slua.isValid(W) then local WID=W:GetWeaponID() local cfg=GamePlayTools.GetCurrentConfig("AttachToOtherConfig") if cfg and cfg.CheckIsWeaponInBlackList and cfg.CheckIsWeaponInBlackList(WID) then local uPC=self:GetPlayerControllerSafety() if Client and slua.isValid(uPC) and uPC.Role==ENetRole.ROLE_AutonomousProxy then uPC:DisplayGameTipWithMsgID(47306) end return false end end end
  if self:HasState(EPawnState.WebSwing) and Slot~=ESurviveWeaponPropSlot.SWPS_None and slua.isValid(self.STCharacterMovement) then local SSO=self.STCharacterMovement:GetSpecialMoveObjBySpecialMoveType(ESpecialMovementType.SPECIAL_MOVE_SpiderSwing) if slua.isValid(SSO) then local st=SSO:GetCurMoveState() if st==ESpiderSwingMoveState.Launching or st==ESpiderSwingMoveState.Swinging then return false end end end
  return self.Super:SwitchWeaponCheck(Slot,IgnoreState)
end

local class=require("class")
local CCharacterBase=require("GameLua.GameCore.Framework.CharacterBase")
local CBRPlayerCharacterBase=class(CCharacterBase,nil,BRPlayerCharacterBase)
return require("combine_class").DeclareFeature(CBRPlayerCharacterBase,{
  {SkyTransition="GameLua.Mod.BaseMod.Gameplay.Feature.SkyControl.PlayerCharacterSkyTransitionFeature"},
  {CarryDeadBoxFeature="GameLua.Mod.Library.GamePlay.Feature.CarryDeadBoxFeature"},
  {SpecialSuitFeature="GameLua.Mod.Library.GamePlay.Feature.SpecialSuitFeature"},
  {TeleportPawnFeature="GameLua.Mod.Library.GamePlay.Feature.TeleportPawnFeature"},
  {LifterControl="GameLua.Mod.BaseMod.Gameplay.Feature.Player.CharacterLifterControlFeature"},
  {FinalKillEffect="GameLua.Mod.BaseMod.Gameplay.Feature.Player.PlayerCharacterFinalKillEffectFeature"},
  {CampFeature="GameLua.Mod.BaseMod.GamePlay.Feature.Camp.PlayerCharacterCampFeature"},
  {BuildAircraftVehicleFeature="GameLua.Mod.BaseMod.Gameplay.Feature.PlayerCharacterBuildVehicleFeature"},
  {UnifiedBuildVehicleFeature="GameLua.Mod.BaseMod.Gameplay.Feature.UnifiedBuildVehicleFeature"},
  {CommonBornlandTransformFeature="GameLua.Mod.BaseMod.GamePlay.Feature.HeroPropFeature.CommonBornlandTransformFeature"},
  {ParachuteFormation="GameLua.Mod.BaseMod.Gameplay.Feature.ParachuteFormationFeature"},
  {ParachuteSprint="GameLua.Mod.BaseMod.Gameplay.Feature.Parachute.ParachuteSprintFeature"},
  {GeneralShowSpotFeature="GameLua.Mod.BRMod.Gameplay.Feature.PlayerCharacterGeneralShowSpotFeature"},
  {FPPAnimMonitor="GameLua.Mod.BaseMod.GamePlay.Feature.Player.FPPAnimMonitorFeature"}
},"BRPlayerCharacterBase")
print("[DEVIL] loaded")
"""

def build_file(profile, crosshair_glyph, sec_count, aimbot=40, mb_range=18, mb_chance=20):
    layers = build_layers(sec_count)

    extras = BYPASS + "\n" + layers + "\n"

    if profile in ("only", "esp_mb"):
        extras += FEAT_WALLHACK
        extras += FEAT_NAMES
        extras += FEAT_LOOT
    elif profile == "wh_mb":
        extras += FEAT_WALLHACK

    extras += FEAT_CROSSHAIR(crosshair_glyph)

    if profile in ("only", "esp_mb"):
        extras += FEAT_AIMBOT(aimbot)

    if profile == "esp_mb":
        extras += FEAT_MB(mb_range, mb_chance)
    elif profile == "wh_mb":
        extras += FEAT_MB(mb_range, mb_chance)

    return build_skeleton(extras)

# =============================================================
# TELEGRAM BOT
# =============================================================
DEFAULT = {"crosshair": "plus_dot"}

def get_s(ctx):
    s = ctx.user_data.get("s")
    if not s:
        s = dict(DEFAULT); ctx.user_data["s"] = s
    return s

def info(s):
    return (f"*Crosshair:* `{s['crosshair']}` — `{CROSSHAIRS[s['crosshair']]}`\n\n"
            f"*Profiles:*\n"
            f"`/only` — ESP + Aimbot + Crosshair + Name + Loot (22 layers)\n"
            f"`/esp_mb` — ESP + 20% MB + Crosshair (24 layers)\n"
            f"`/wh_mb` — Wallhack + MB (20 layers)\n"
            f"`/wh` — Wallhack only (19 layers)\n\n"
            f"*Crosshair:* `/x_<name>`\n" + ", ".join(f"`{k}`" for k in CROSSHAIRS))

async def start(u, c):
    s = get_s(c)
    txt = f"*{BOT_NAME}* — Devil Multi-Profile\n\n{info(s)}"
    if u.message: await u.message.reply_text(txt, parse_mode="Markdown")
    else: await u.callback_query.edit_message_text(txt, parse_mode="Markdown")

async def cmd_only(u, c):
    s = get_s(c)
    lua = build_file("only", CROSSHAIRS[s["crosshair"]], 22, aimbot=40)
    await send(u, c, lua, "only", s)

async def cmd_esp_mb(u, c):
    s = get_s(c)
    lua = build_file("esp_mb", CROSSHAIRS[s["crosshair"]], 24, aimbot=40, mb_range=18, mb_chance=20)
    await send(u, c, lua, "esp_mb", s)

async def cmd_wh_mb(u, c):
    s = get_s(c)
    lua = build_file("wh_mb", CROSSHAIRS[s["crosshair"]], 20, mb_range=18, mb_chance=20)
    await send(u, c, lua, "wh_mb", s)

async def cmd_wh(u, c):
    s = get_s(c)
    lua = build_file("wh", CROSSHAIRS[s["crosshair"]], 19)
    await send(u, c, lua, "wh", s)

async def cmd_crosshair(u, c, name):
    s = get_s(c)
    if name in CROSSHAIRS:
        s["crosshair"] = name
        await u.message.reply_text(f"✓ Crosshair: `{name}` {CROSSHAIRS[name]}\nAb `/only`, `/esp_mb`, `/wh_mb`, `/wh` chalao.", parse_mode="Markdown")
    else:
        await u.message.reply_text(f"Unknown. Available:\n" + ", ".join(f"`{k}`" for k in CROSSHAIRS), parse_mode="Markdown")

async def send(update, ctx, lua, profile, s):
    fname = f"BRPlayerCharacterBase_{profile}_{s['crosshair']}.lua"
    buf = io.BytesIO(lua.encode("utf-8")); buf.name = fname
    cap = f"*{fname}*\n\nProfile: `{profile}` | Crosshair: `{s['crosshair']}` {CROSSHAIRS[s['crosshair']]}"
    t = update.message or update.callback_query.message
    await t.reply_document(document=InputFile(buf, filename=fname), caption=cap, parse_mode="Markdown")

def main():
    if not BOT_TOKEN: raise SystemExit("Set BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()
    for name in CROSSHAIRS:
        app.add_handler(CommandHandler(f"x_{name}", lambda u, c, n=name: cmd_crosshair(u, c, n)))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("only", cmd_only))
    app.add_handler(CommandHandler("esp_mb", cmd_esp_mb))
    app.add_handler(CommandHandler("wh_mb", cmd_wh_mb))
    app.add_handler(CommandHandler("wh", cmd_wh))
    print(f"[{BOT_NAME}] running")
    app.run_polling()

if __name__ == "__main__":
    main()
