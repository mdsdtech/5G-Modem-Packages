local i18n = require "luci.i18n"
local _ = i18n.translate
local sys = require "luci.sys"
local uci = require "luci.model.uci".cursor()

m = Map("fm350webui", _("FM350 WebUI Configuration"),
    _("Configure the FM350 WebUI service settings"))

s = m:section(NamedSection, "main", "fm350webui", _("Service Settings"))

-- 启用服务
o = s:option(Flag, "enabled", _("Enable Service"))
o.rmempty = false

-- WebUI端口
o = s:option(Value, "port", _("WebUI Port"))
o.datatype = "port"
o.default = 8001
o.description = _("Default port is 8001. Change only if port conflicts occur.")

-- 服务状态和控制区域
o = s:option(DummyValue, "_control", _("Service Control"))
o.rawhtml = true
o.value = function()
    local running = sys.call("/etc/init.d/fm350webui status >/dev/null 2>&1") == 0
    local port = uci:get("fm350webui", "main", "port") or "8001"
    local ip = luci.http.getenv("SERVER_ADDR")
    
    if ip:match(":") then
        ip = "["..ip.."]"
    end
    
    local url = "http://" .. ip .. ":" .. port
    local panel_url = luci.dispatcher.build_url("admin/services/fm350webui/panel")
    local statusClass = running and "success" or "error"
    local statusText = running and 
        "<span style='color:green; font-weight:bold'>" .. _("Running") .. "</span>" or 
        "<span style='color:red; font-weight:bold'>" .. _("Stopped") .. "</span>"
    
    return [[
        <div class="alert-message ]] .. statusClass .. [[">
            <div style="margin-bottom:10px;">
                <strong>]] .. _("Status:") .. [[</strong>
                <span id="fm350webui-status" style="margin-left:10px">]] .. statusText .. [[</span>
            </div>
            
            <div style="margin-bottom:10px; font-size:0.9em;">
                <strong>]] .. _("Access URL:") .. [[</strong> ]] .. url .. [[
            </div>
            
            <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:15px;">
                <a class="btn cbi-button cbi-button-apply" href="]] .. panel_url .. [[">]] .. 
                _("Web Panel") .. [[</a>
                
                <a class="btn cbi-button cbi-button-apply" href="]] .. url .. [[" target="_blank">]] .. 
                _("Open in New Tab") .. [[</a>
                
                <a class="btn cbi-button cbi-button-action" href="]] .. 
                luci.dispatcher.build_url("admin/services/fm350webui/config/start") .. [[">]] .. 
                _("Start") .. [[</a>
                
                <a class="btn cbi-button cbi-button-reset" href="]] .. 
                luci.dispatcher.build_url("admin/services/fm350webui/config/restart") .. [[">]] .. 
                _("Restart") .. [[</a>
                
                <a class="btn cbi-button cbi-button-negative" href="]] .. 
                luci.dispatcher.build_url("admin/services/fm350webui/config/stop") .. [[">]] .. 
                _("Stop") .. [[</a>
            </div>
        </div>
        
        <script>
            const statusUrl = ']] .. luci.dispatcher.build_url("admin/services/fm350webui/status") .. [[';
            
            function refreshStatus() {
                fetch(statusUrl)
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('fm350webui-status');
                        if (data.running) {
                            statusEl.innerHTML = "<span style='color:green; font-weight:bold'>]] .. _("Running") .. [[</span>";
                            statusEl.parentNode.parentNode.className = 'alert-message success';
                        } else {
                            statusEl.innerHTML = "<span style='color:red; font-weight:bold'>]] .. _("Stopped") .. [[</span>";
                            statusEl.parentNode.parentNode.className = 'alert-message error';
                        }
                    });
            }
            
            setTimeout(refreshStatus, 100);
            setInterval(refreshStatus, 5000);
        </script>
    ]]
end

-- 在配置保存时自动启动/停止服务
function m.on_after_save(self)
    local uci = require "luci.model.uci".cursor()
    local enabled = uci:get("fm350webui", "main", "enabled")
    local sys = require "luci.sys"
    
    if enabled == "1" then
        sys.call("/etc/init.d/fm350webui restart >/dev/null 2>&1")
    else
        sys.call("/etc/init.d/fm350webui stop >/dev/null 2>&1")
    end
    
    sys.call("/etc/init.d/fm350webui enabled >/dev/null 2>&1")
end

return m