/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          base:   '#0f1117',
          card:   '#161b27',
          raised: '#1d2333',
          border: '#252d3f',
          hover:  '#2a3347',
        },
        accent: {
          blue:   '#4e9ef5',
          purple: '#a78bfa',
          pink:   '#f472b6',
          green:  '#34d399',
          yellow: '#fbbf24',
          red:    '#f87171',
        },
        text: {
          primary:   '#e2e8f0',
          secondary: '#94a3b8',
          muted:     '#64748b',
          link:      '#60a5fa',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
