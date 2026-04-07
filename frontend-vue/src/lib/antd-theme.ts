import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: '#00d9ff',
    colorBgContainer: '#112240',
    colorBgElevated: '#112240',
    colorBgLayout: '#0a192f',
    colorBorder: '#1e293b',
    colorBorderSecondary: '#1e293b',
    colorText: '#ffffff',
    colorTextSecondary: '#8892a0',
    colorTextTertiary: '#8892a0',
    borderRadius: 8,
    fontFamily: 'inherit',
  },
  components: {
    Modal: {
      contentBg: '#112240',
      headerBg: '#112240',
    },
    Select: {
      optionActiveBg: '#172a45',
      optionSelectedBg: 'rgba(0, 217, 255, 0.12)',
    },
    Table: {
      headerBg: '#0a192f',
      rowHoverBg: 'rgba(23, 42, 69, 0.5)',
    },
    Input: {
      activeBorderColor: '#00d9ff',
      activeShadow: '0 0 0 2px rgba(0, 217, 255, 0.1)',
    },
    Tabs: {
      itemActiveColor: '#00d9ff',
      inkBarColor: '#00d9ff',
    },
  },
}
