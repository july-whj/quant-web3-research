import { defineConfig } from 'vitepress'

const github = 'https://github.com/july-whj/quant-web3-research'

export default defineConfig({
  lang: 'zh-CN',
  title: '从零开始学 Web3 量化交易',
  titleTemplate: ':title｜Quant Web3 Research',
  description: '一本从 Python、BTC 行情与回测出发，逐步走向 Web3 数据和模拟交易系统的开源入门书。',
  cleanUrls: true,
  lastUpdated: true,
  sitemap: {
    hostname: 'https://quantweb.sryze.cc',
  },
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/assets/logo-primary.png' }],
    ['meta', { name: 'theme-color', content: '#0b5f53' }],
    ['meta', { name: 'author', content: 'Quant Web3 Research' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
    ['meta', { property: 'og:site_name', content: '从零开始学 Web3 量化交易' }],
    ['meta', { property: 'og:image', content: 'https://quantweb.sryze.cc/assets/logo-primary.png' }],
  ],
  markdown: {
    lineNumbers: true,
    image: {
      lazyLoading: true,
    },
  },
  themeConfig: {
    logo: '/assets/logo-primary.png',
    siteTitle: 'Quant Web3 Book',
    nav: [
      { text: '阅读首页', link: '/' },
      { text: '学习路线', link: '/00-roadmap' },
      {
        text: '章节',
        items: [
          { text: '第一部分 · 量化基础', link: '/01-quant-basics/01-what-is-quant-trading' },
          { text: '第二部分 · Web3 基础', link: '/02-web3-basics/09-blockchain-block-transaction-consensus' },
          { text: '第三部分 · 系统实践', link: '/03-system-practice/16-open-source-system-architecture' },
        ],
      },
      { text: '研究系统', link: `${github}#readme` },
    ],
    sidebar: [
      {
        text: '开始阅读',
        collapsed: false,
        items: [
          { text: '在线书首页', link: '/' },
          { text: '前言 · 为什么出发', link: '/00-preface' },
          { text: '项目定位与开源路线', link: '/00-project-positioning' },
          { text: '全书学习路线', link: '/00-roadmap' },
        ],
      },
      {
        text: '第一部分 · 交易与量化基础',
        collapsed: false,
        items: [
          { text: '01 什么是量化交易', link: '/01-quant-basics/01-what-is-quant-trading' },
          { text: '02 收益率、回撤、复利与风险', link: '/01-quant-basics/02-return-drawdown-compounding-risk' },
          { text: '03 Python 与时间序列', link: '/01-quant-basics/03-python-and-time-series' },
          { text: '04 获取第一份 BTC 行情', link: '/01-quant-basics/04-get-first-btc-market-data' },
          { text: '05 BTC 现货双均线策略', link: '/01-quant-basics/05-btc-spot-ma-cross-strategy' },
          { text: '06 完成第一次回测', link: '/01-quant-basics/06-first-backtest' },
          { text: '07 手续费、滑点与资金曲线', link: '/01-quant-basics/07-fees-slippage-equity-curve' },
          { text: '08 识别常见回测陷阱', link: '/01-quant-basics/08-lookahead-survivorship-overfitting' },
        ],
      },
      {
        text: '第二部分 · Web3 基础',
        collapsed: false,
        items: [
          { text: '本部分导读', link: '/02-web3-basics/README' },
          { text: '09 区块链、交易与共识', link: '/02-web3-basics/09-blockchain-block-transaction-consensus' },
          { text: '10 账户、钱包、私钥和助记词', link: '/02-web3-basics/10-account-wallet-private-key-seed-phrase' },
          { text: '11 BTC、ETH、稳定币与 Token', link: '/02-web3-basics/11-btc-eth-stablecoin-token-standard' },
          { text: '12 中心化与去中心化交易所', link: '/02-web3-basics/12-cex-and-dex' },
          { text: '13 公链、Gas 与区块确认', link: '/02-web3-basics/13-chain-id-gas-confirmation' },
          { text: '14 智能合约、RPC 与浏览器', link: '/02-web3-basics/14-contract-rpc-explorer' },
          { text: '15 预言机、跨链桥与安全', link: '/02-web3-basics/15-oracle-bridge-security' },
        ],
      },
      {
        text: '第三部分 · 系统实践',
        collapsed: false,
        items: [
          { text: '本部分导读', link: '/03-system-practice/README' },
          { text: '16 开源系统架构与目录', link: '/03-system-practice/16-open-source-system-architecture' },
          { text: '17 CEX 行情数据模块', link: '/03-system-practice/17-cex-market-data-module' },
        ],
      },
      {
        text: '附录 · 风险与资料',
        collapsed: true,
        items: [
          { text: '量化交易书单', link: '/04-risk-and-product/recommended-books' },
          { text: '策略比较与评估', link: '/04-risk-and-product/strategy-comparison' },
          { text: 'Web3 安全检查表', link: '/04-risk-and-product/web3-security-checklist' },
          { text: '系统架构说明', link: '/architecture/system-architecture' },
          { text: '书稿使用许可', link: '/LICENSE' },
        ],
      },
    ],
    search: {
      provider: 'local',
      options: {
        detailedView: true,
        translations: {
          button: {
            buttonText: '搜索全书',
            buttonAriaLabel: '搜索全书',
          },
          modal: {
            noResultsText: '没有找到相关内容',
            resetButtonTitle: '清除搜索条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },
    outline: {
      level: [2, 3],
      label: '本页目录',
    },
    socialLinks: [
      { icon: 'github', link: github },
    ],
    editLink: {
      pattern: `${github}/edit/main/docs/:path`,
      text: '在 GitHub 上修正本页',
    },
    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short',
      },
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '返回顶部',
    externalLinkIcon: true,
    footer: {
      message: '书稿采用 CC BY-NC-SA 4.0 许可发布 · 内容仅用于学习与研究，不构成投资建议',
      copyright: 'Copyright © 2026 Quant Web3 Research',
    },
  },
})
