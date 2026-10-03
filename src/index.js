// 终端 miniapp —— 首页（最小可用性测试：纯 JS + render(h)，不依赖 falcon-ui）
// 目的：验证 1) 明文 .js 页面能否被框架加载 2) render(h) 能否渲染 3) 样式/组件是否可用

export default {
  name: 'index',

  data() {
    return {
      lines: [
        'TERM TEST 0.1',
        'plain .js page loaded',
        'render(h) works',
        'weex/vue 2.6.12',
      ],
      typed: '',
    };
  },

  methods: {
    onType(e) {
      this.typed = (e && e.value) || '';
      console.log('[term] input=' + this.typed);
    },
    poke() {
      console.log('[term] clicked, lines=' + this.lines.length);
      this.lines.push('click #' + (this.lines.length + 1));
    },
  },

  onShow() { try { console.warn('[term] page index onShow (enter)'); } catch(e){}
    console.warn('[term] page index onShow');
  },
  onLoad() {
    console.warn('[term] page index onLoad');
  },

  render(h) {
    const row = (t, i) =>
      h(
        'text',
        {
          key: 'l' + i,
          staticStyle: { color: i === 0 ? '#7ee787' : '#d0d0d0', fontSize: '18px', lineHeight: '22px' },
        },
        t
      );
    return h(
      'div',
      {
        staticStyle: {
          flexDirection: 'column',
          width: '960px',
          height: '266px',
          backgroundColor: '#0b0f14',
          paddingLeft: '10px',
          paddingTop: '6px',
        },
      },
      [
        h(
          'div',
          { staticStyle: { flexDirection: 'column', height: '200px' } },
          this.lines.map(row)
        ),
        h('text', { staticStyle: { color: '#58a6ff', fontSize: '16px' } }, 'tap here to add a line'),
        h('input', {
          staticStyle: {
            width: '600px',
            height: '34px',
            backgroundColor: '#161b22',
            color: '#e6edf3',
            fontSize: '16px',
          },
          attrs: { type: 'text', placeholder: 'type here' },
          on: { input: this.onType, change: this.onType, click: this.poke },
        }),
      ]
    );
  },
};
