# 编译
```sh
# 添加软件源
echo 'src-git fm350webui https://gitee.com/kcro/luci-app-fm350webui.git;master' >> feeds.conf.default

# 更新并安装软件源包
./scripts/feeds update fm350webui
./scripts/feeds install -a -p fm350webui

# (可选) 强制安装以覆盖现有的驱动程序/应用
./scripts/feeds install -a -f -p luci-app-fm350webui

# 进入构建配置菜单
make menuconfig
```