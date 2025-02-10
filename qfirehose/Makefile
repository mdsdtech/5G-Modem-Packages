#
# Copyright (C) 2011-2014 OpenWrt.org
#
# This is free software, licensed under the GNU General Public License v2.
# See /LICENSE for more information.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=qfirehose
PKG_VERSION:=1.14.21
PKG_RELEASE:=1

PKG_FLAGS:=nonshared

include $(INCLUDE_DIR)/package.mk

define Package/qfirehose
  SECTION:=net
  CATEGORY:=Network
  SUBMENU:=WWAN
  TITLE:=Quectel Firehose Update Utility
  DEPENDS:= +unzip +kmod-usb2 +kmod-usb3 +kmod-usb-ohci +kmod-usb-uhci +kmod-usb-serial-option +kmod-usb-serial +kmod-usb-serial-qualcomm
endef

define Build/Compile
	$(MAKE) -C $(PKG_BUILD_DIR) \
		CC="$(TARGET_CC)" \
		CFLAGS="$(TARGET_CFLAGS) -Wall"
endef

define Package/qfirehose/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/qfirehose $(1)/usr/bin/qfirehose
endef

$(eval $(call BuildPackage,qfirehose))
