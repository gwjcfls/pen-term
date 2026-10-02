# 自研入口契约（逆向记录）

这份文档记录**框架对 miniapp `app.js` 的隐式要求**，以及把这些要求挖出来的过程。
它们不是文档，而是从官方包里逆向出来的 —— 官方 aiot-vue-cli 在打包时会注入一段"胶水"，
用户源码里看不到（例如 PenBili 的 `src/app.js` 只有 `class App extends $falcon.App` + `export default App`，
但它的 `app.js.bin` 里却有 `__AppClazz` / `__loadModuleDefault` / `__KEYFRAMES` / `__pages` 这些 atom）。

## 1. 契约清单（缺一不可）

| # | 要求 | 缺了会怎样 |
|---|---|---|
| 1 | `$falcon.__AppClazz = App` | launcher 报 `TypeError: not a function`，应用起不来 |
| 2 | `App.meta = {pages, options, name, version, isSingleJsBundle}`，`pages` 的值是 **`.vue` 源码路径** | `TypeError: cannot convert to object` |
| 3 | `$falcon.__loadModuleDefault = m => (m && m.default !== undefined) ? m.default : m` | `loadPage: TypeError: not a function` |
| 4 | `$falcon.__KEYFRAMES = {...}`（关键帧表） | 动画相关隐患 |
| 5 | `onLaunch` 里 `this.setViewPort(960)` + `$falcon.useDefaultBasePageClass(BasePage)` | 页面生命周期缺失 |
| 6 | **入口必须 `import './<页面>.js'`** | 框架**永远不会去求值页面模块**（启动日志里看不到 `page module evaluated`） |

## 2. 页面挂载的关键（卡最久的一条）

框架实例化的是 **`useDefaultBasePageClass` 传进去的那个基类**；
页面模块 `export default` 的那个类**不会被实例化**（`PageLifecycle->onStart` 有日志，但页面类的 `onLoad` 不执行）。

所以挂载必须写在**基类**里：

```js
// base-page.js
import Component from './Component.js';
export class BasePage extends $falcon.Page {
  onLoad(options) {
    super.onLoad(options);
    this.setRootComponentOptions(Component);   // ★ 普通 Vue options 对象用这个
  }
}
```

框架 `Page` 基类的挂载方法有两个（实测原型）：

```
constructor, setRootComponent, setRootComponentOptions,
onLoad, onNewOptions, onShow, onHide, onUnload, finish,
init, register, unRegister, trigger, on, off
```

- `setRootComponentOptions(options对象)` → 给 vue-loader 产物 / 手写 options 用
- `setRootComponent(组件类)` → 给 Vue 组件类用

调用成功的标志（`console.warn` 会被框架转发到 `/data/applog/DictPen_*.log`）：

```
[term-ui] BasePage.onLoad 到
[term-ui] 基类挂载: setRootComponentOptions 已调用
[term-ui] onShow
[term-ui] attach 本地 shell sid=1 vt={"ok":true,"cols":120,"rows":12}
```

## 3. 官方胶水的完整行为（实测 diff）

把官方 `app.js.bin` **复制一份改名为 `glue.js.bin`**（绕过模块缓存），
再用**自己的 entry** 去 `import './glue.js'`（关键是必须用自己的 entry —— 若把官方 bundle 当 entry，
那些写入早就发生过了，diff 永远是空的），配合一个先求值的 `snap.js` 快照模块 diff `$falcon`：

```
[glue] 快照 falcon=21 keys=eventMap,_uniqueId,...,$getTopApp
[glue] 新增键: __AppClazz=fn | __loadModuleDefault=fn | __KEYFRAMES=obj{0..6}
[glue] 变化的键: (空)
[glue] __pages = undefined
[glue] 官方 glue 模块命名空间 keys= (空，连 default 都没有)
[glue] App.meta={"pages":{"index":"pages/index/index.vue", ...},
                 "options":{"style":{"lessPaths":["styles"]}},
                 "name":"文件管理器","version":"1.2.0","isSingleJsBundle":false}
```

结论：**胶水只做第 1~5 条**（外加 `App.meta`），`$falcon.__pages` 官方根本不用。

## 4. 其它实测结论

- **`.js.bin` 容器格式**：`[0x01][varint 字符串数][N×(varint(字节长<<1|wide)+内容)][字节码]`，
  而首字节 `0x01` 就是**这个厂商版 QuickJS 的 BC_VERSION** → 必须**整文件**喂 `JS_ReadObject`（跳过头部会报 `invalid version`）
- **必须用笔自己的 `libquickjs.so` 编**：官方包的字节码比共享库那版新（`invalid tag (tag=15 pos=1324)`），
  框架的 QuickJS 是**静态编进 `/usr/bin/miniapp`** 的（`/proc/<pid>/maps` 里没有 `libquickjs.so`）
- **官方 app 的模块命名**：会 `import '<名字>-<hash>.js'`，页面入口块形如 `<页面名>Page-<hash>.js`
  （例：桌面 app 的 `indexPage-93295cbd.js.bin`），块里是一堆 `./<模块>-<hash>.js` 的相对 import
  （其中必有 `BasePage-<hash>.js`）
- **`<image>` 按 URL 缓存**：同名文件改了内容不会重载 → 每帧写新文件名
- **本地图片必须 `file://` 前缀**，否则 `WXImage::onLoad failed`
- **插件符号必须显式导出**：`-fvisibility=hidden` 会把 `custom_init_jsapis` / `custom_init_jsmodules`
  一起藏掉 → 框架 dlsym 不到 → `import xxx from 'xxx'` 报 `could not load module filename`

## 5. 换包与注册表（很坑，务必看）

- 换包：`uninstall`（等日志 `appDestroyed`）→ `install` → `start <appid> index`
  （**页面名不带 `--`**，`--index` 会让框架去找 `--index.js` → 页面根本不加载）
- 生效校验：`grep appResumed`，看 `getVersion()` 是否已是新版本（旧实例会一直活着误导你）
- **安装注册表**：`/userdata/miniapp/data/mini_app/pkg/packages.json`
  （`{"packages":[{appid,b,category,flag,icon,installPath,name,packageDir,props,version}]}`）
  —— 笔自带应用的 `installPath` 也指向 `/userdisk/secondary/miniapp/...`，所以跨根正常
- **应用在重启后从桌面消失**（日志 `pm name=<应用名> type=removed`）→ 说明注册表条目丢了，
  **重新 install 一次**即可恢复（`type=installed`）
