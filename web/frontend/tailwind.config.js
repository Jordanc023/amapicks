/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                gold: {
                    50: '#f9f7eb',
                    100: '#f0ebc5',
                    200: '#ecdfa0',
                    300: '#e8d27a',
                    400: '#e4c655',
                    500: '#d4af37', // Base Gold
                    600: '#aa8c2c',
                    700: '#806921',
                    800: '#554616',
                    900: '#2b230b',
                },
                dark: {
                    950: '#050505', // Almost Black
                    900: '#0a0a0a', // Dark Background
                    800: '#121212', // Card Background
                    700: '#1c1c1c', // Card Hover
                },
                club: {
                    blue: '#034694', // Chelsea Blue example
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Montserrat', 'sans-serif'],
            },
            backgroundImage: {
                'hero-pattern': "url('https://www.transparenttextures.com/patterns/carbon-fibre.png')", // Textura sutil si se desea
                'gradient-gold': 'linear-gradient(135deg, #d4af37 0%, #aa8c2c 100%)',
            },
            boxShadow: {
                'gold': '0 10px 30px -10px rgba(212, 175, 55, 0.3)',
                'card': '0 0 20px rgba(0,0,0,0.5)',
            },
            keyframes: {
                shimmer: {
                    '100%': { transform: 'translateX(100%)' }
                }
            }
        },
    },
    plugins: [],
}
