module("luci.controller.fm350webui", package.seeall)

local i18n = require "luci.i18n"
local _ = i18n.translate
local uci = require "luci.model.uci".cursor()
local sys = require "luci.sys"

function index()
    entry({"admin", "services", "fm350webui"}, alias("admin", "services", "fm350webui", "panel"), _("FM350 WebUI"), 60)
    entry({"admin", "services", "fm350webui", "panel"}, call("show_panel"), _("Web Panel"), 10)
    entry({"admin", "services", "fm350webui", "config"}, cbi("fm350webui"), _("Configuration"), 20)
    entry({"admin", "services", "fm350webui", "open"}, call("open_webui"), nil, 30)
    entry({"admin", "services", "fm350webui", "config", "start"}, call("start_service"), nil, 40)
    entry({"admin", "services", "fm350webui", "config", "stop"}, call("stop_service"), nil, 40)
    entry({"admin", "services", "fm350webui", "config", "restart"}, call("restart_service"), nil, 40)
    entry({"admin", "services", "fm350webui", "status"}, call("get_status"), nil, 50)
end

function show_panel()
    local port = uci:get("fm350webui", "main", "port") or "8001"
    local running = sys.call("/etc/init.d/fm350webui status >/dev/null 2>&1") == 0
    local ip = luci.http.getenv("SERVER_ADDR")
    
    if ip:match(":") then
        ip = "["..ip.."]"
    end
    
    local url = "http://" .. ip .. ":" .. port
    
    luci.template.render("fm350webui_panel", {
        title = _("FM350 WebUI Panel"),
        url = url,
        running = running
    })
end

function open_webui()
    local port = uci:get("fm350webui", "main", "port") or "8001"
    local ip = luci.http.getenv("SERVER_ADDR")
    
    if ip:match(":") then
        ip = "["..ip.."]"
    end
    
    local url = "http://" .. ip .. ":" .. port
    
    luci.http.redirect(url)
end

function start_service()
    sys.call("chmod +x /etc/init.d/fm350webui")
    sys.call("/etc/init.d/fm350webui start >/dev/null 2>&1")
    luci.http.redirect(luci.dispatcher.build_url("admin/services/fm350webui/panel"))
end

function stop_service()
    sys.call("/etc/init.d/fm350webui stop >/dev/null 2>&1")
    luci.http.redirect(luci.dispatcher.build_url("admin/services/fm350webui/panel"))
end

function restart_service()
    sys.call("/etc/init.d/fm350webui restart >/dev/null 2>&1")
    luci.http.redirect(luci.dispatcher.build_url("admin/services/fm350webui/panel"))
end

function get_status()
    local running = sys.call("/etc/init.d/fm350webui status >/dev/null 2>&1") == 0
    
    luci.http.prepare_content("application/json")
    luci.http.write_json({
        running = running
    })
end