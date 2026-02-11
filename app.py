# HTML s JAVASCRIPTEM PRO ZOOMOVÁNÍ A POSOUVÁNÍ
        html_content = f"""
        <div id="zoom-container" style="
            background-color: #1a1a1a; 
            color: #ffffff; 
            padding: 25px; 
            font-family: 'Roboto Mono', monospace; 
            font-size: 24px; 
            white-space: pre; 
            line-height: 1.4;
            border-radius: 12px;
            border: 1px solid #444;
            /* touch-action: pan-y; umožní posun nahoru/dolů, ale pinch-zoom si pořešíme sami */
            touch-action: pan-y; 
            user-select: none;
            -webkit-user-select: none;
        ">{finalni_text}</div>

        <script>
            const el = document.getElementById('zoom-container');
            let fontSize = 24;
            let initialDist = -1;

            el.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 2) {{
                    // Pokud jsou dva prsty, vypočítáme vzdálenost a zabráníme posunu stránky
                    initialDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
                }}
            }}, {{passive: false}});

            el.addEventListener('touchmove', (e) => {{
                if (e.touches.length === 2 && initialDist > 0) {{
                    // Důležité: Tady zablokujeme posun stránky jen při zoomování
                    e.preventDefault();
                    
                    const currentDist = Math.hypot(
                        e.touches[0].pageX - e.touches[1].pageX,
                        e.touches[0].pageY - e.touches[1].pageY
                    );
                    
                    const diff = currentDist - initialDist;
                    if (Math.abs(diff) > 5) {{
                        fontSize += diff > 0 ? 0.8 : -0.8;
                        fontSize = Math.min(Math.max(12, fontSize), 100); 
                        el.style.fontSize = fontSize + 'px';
                        initialDist = currentDist;
                    }}
                }}
                // Pokud je tam jen jeden prst, e.preventDefault() se nezavolá a stránka se normálně posune
            }}, {{passive: false}});

            el.addEventListener('touchend', (e) => {{
                if (e.touches.length < 2) {{
                    initialDist = -1;
                }}
            }});
        </script>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
        """
        
        # Plynulá výška
        vyska = (len(finalni_text.split('\n')) * 60) + 300
        components.html(html_content, height=vyska, scrolling=False)
