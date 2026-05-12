include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI Support for FM350 WebUI
LUCI_DEPENDS:= +python3 +python3-aiohttp +python3-pyserial +python3-websockets +luci-app-qmodem
LUCI_PKGARCH:=all

PKG_NAME:=luci-app-fm350webui
PKG_VERSION:=1.0.3
PKG_RELEASE:=1

PKG_MAINTAINER:=KCrO <Charsiton@qq.com>
PKG_LICENSE:=MIT

include $(TOPDIR)/feeds/luci/luci.mk

define Package/$(PKG_NAME)/postinst
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
    chmod +x /etc/init.d/fm350webui

    # 启用服务（不自动启动）
    /etc/init.d/fm350webui enable >/dev/null 2>&1

    # 清理LuCI缓存
    rm -f /tmp/luci-indexcache 2>/dev/null
    
    echo "FM350 WebUI installed successfully."
    echo "Configuration path: Services > FM350 WebUI"
}
exit 0
endef

define Package/$(PKG_NAME)/prerm
#!/bin/sh
[ -n "$${IPKG_INSTROOT}" ] || {
    # 停止服务
    [ -x "/etc/init.d/fm350webui" ] && {
        /etc/init.d/fm350webui stop
        /etc/init.d/fm350webui disable
    }
    
    # 清理进程
    pkill -f "python3 /usr/share/fm350webui/server.py" 2>/dev/null
}
exit 0
endef
# call BuildPackage - OpenWrt buildroot signature
