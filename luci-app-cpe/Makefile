#将openwrt顶层目录下的rules.mk文件中的内容导入进来
include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-cpe
LUCI_TITLE:=LuCI support for Modem CPE
PKG_VERSION:=5.0.1

PKF_MAINTAINER:=daocaoren <168620188@qq.com>
PKG_LICENSE:=GPLv3
PKG_LINCESE_FILES:=LICENSE

PKG_BUILD_DIR:= $(BUILD_DIR)/$(PKG_NAME)
 
include $(INCLUDE_DIR)/package.mk
 
define Package/$(PKG_NAME)
	PKGARCH:=all
	SECTION:=luci
	CATEGORY:=Luci
	SUBMENU:=3. Applications
	TITLE:=$(LUCI_TITLE)
	DEPENDS:=+sendat \
		+luci-compat \
		+kmod-usb2 +kmod-usb3 \
		+kmod-usb-ohci \
		+kmod-usb-uhci \
		+kmod-usb-net \
		+kmod-usb-net-cdc-ether \
		+kmod-usb-acm \
		+kmod-usb-net-qmi-wwan \
		+kmod-usb-net-rndis \
		+kmod-usb-serial-qualcomm \
		+kmod-usb-net-sierrawireless \
		+kmod-usb-serial \
		+kmod-usb-serial-option \
		+kmod-usb-wdm \
		+kmod-usb-net-cdc-mbim \
		+quectel-cm \
		+usbutils
endef

include $(TOPDIR)/feeds/luci/luci.mk
# call BuildPackage - OpenWrt buildroot signature
