#
# Copyright (C) 2015 OpenWrt.org
#
# This is free software, licensed under the GNU General Public License v2.
# See /LICENSE for more information.
#

include $(TOPDIR)/rules.mk

LUCI_TITLE:=Modem Server
LUCI_DEPENDS:=+luci-compat +quectel-cm +kmod-usb-acm \
	+kmod-usb-net-cdc-ether +kmod-usb-net-cdc-mbim \
	+kmod-usb-net-qmi-wwan +kmod-usb-net-rndis \
	+kmod-usb-serial-option +kmod-usb-wdm \
	+kmod-usb-net-qmi-wwan-fibocom +kmod-usb-net-qmi-wwan-quectel +usbutils

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
