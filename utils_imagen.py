import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import os
import urllib.request

FONT_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
FONT_DEFAULT = os.path.join(FONT_DIR, "Montserrat-Black.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "Montserrat-SemiBold.ttf")

def asegurar_fuentes():
    """Descarga automáticamente las fuentes de Google Fonts si no existen en el VPS."""
    os.makedirs(FONT_DIR, exist_ok=True)
    if not os.path.exists(FONT_DEFAULT):
        url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf"
        try:
            urllib.request.urlretrieve(url, FONT_DEFAULT)
        except Exception as e:
            print(f"Error bajando fuente Black: {e}")
            
    if not os.path.exists(FONT_REGULAR):
        url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-SemiBold.ttf"
        try:
            urllib.request.urlretrieve(url, FONT_REGULAR)
        except Exception as e:
            print(f"Error bajando fuente SemiBold: {e}")

# Llamar al cargar el módulo
asegurar_fuentes()

async def descargar_imagen(url):
    """Descarga de forma asíncrona la imagen del escudo del club y la convierte en un objeto PIL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception as e:
        print(f"Error descargando logo desde {url}: {e}")
    return None

def hex_to_rgb(hex_color):
    """Convierte colores Hexadecimales a tuplas RGB compatibles con Pillow."""
    if not hex_color:
        return (50, 50, 50)
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (50, 50, 50)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (50, 50, 50)

async def generar_imagen_plantilla(nombre_equipo, color_hex, escudo_url, dt_nombre, jugadores):
    """
    Motor Gráfico principal. 
    Genera y devuelve un buffer (io.BytesIO) en PNG con la tarjeta estética de alineación.
    - jugadores = [(nombre_jugador, boolean_es_dt), ...]
    """
    WIDTH = 1080
    # Auto-expandir el lienzo hacia abajo si hay muchísimos jugadores (más de 12)
    HEIGHT = 1024 + max(0, (len(jugadores)-10)*65) 
    
    # 1. Lienzo Oscuro Global (Fondo base Negro Profundo)
    img = Image.new('RGBA', (WIDTH, HEIGHT), color=(10, 10, 12, 255))
    
    # 2. Degradado Radial del Color del Equipo
    gradient = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    
    # Usar el color del equipo para el degradado
    team_rgb = hex_to_rgb(color_hex)
    
    center_x, center_y = WIDTH // 2, HEIGHT // 3
    max_radius = 900
    
    for r in range(max_radius, 0, -10):
        # Curva de opacidad (Efecto brillo inmersivo del color del equipo en el centro)
        alpha = int(((1 - (r / max_radius))**2) * 110) 
        draw_grad.ellipse(
            (center_x - r, center_y - r, center_x + r, center_y + r),
            fill=(team_rgb[0], team_rgb[1], team_rgb[2], alpha)
        )
    img.alpha_composite(gradient)
    
    # Extraemos el color del equipo solo para detalles menores
    color_rgb = hex_to_rgb(color_hex)
    
    # 3. Cargar Fuentes
    try:
        font_title = ImageFont.truetype(FONT_DEFAULT, 90)
        font_dt = ImageFont.truetype(FONT_REGULAR, 38)
        font_box = ImageFont.truetype(FONT_DEFAULT, 32)
        font_tag = ImageFont.truetype(FONT_REGULAR, 22)
    except:
        font_title = ImageFont.load_default()
        font_dt = ImageFont.load_default()
        font_box = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 4. Descargar y dibujar escudos
    logo = None
    if escudo_url:
        logo = await descargar_imagen(escudo_url)
        
    if logo:
        # A. Marca de Agua (Fondo difuminado SUPER GRANDE)
        watermark = logo.copy()
        a = watermark.getchannel('A')
        a = a.point(lambda i: int(i * 0.08)) # Solo 8% opacidad (muy sutil)
        watermark.putalpha(a)
        
        wm_size = 1100
        watermark.thumbnail((wm_size, wm_size), Image.Resampling.LANCZOS)
        img.alpha_composite(watermark, (WIDTH//2 - watermark.width//2, HEIGHT//2 - watermark.height//2 + 50))
        
        # B. Escudo Principal Superior (Vibrante)
        logo.thumbnail((260, 260), Image.Resampling.LANCZOS)
        img.alpha_composite(logo, (WIDTH//2 - logo.width//2, 70))
        
    y_offset = 350
    
    # 5. Textos (Cabecera)
    text = nombre_equipo.upper()
    try:
        bbox = draw.textbbox((0, 0), text, font=font_title)
        tw = bbox[2] - bbox[0]
    except:
        tw = draw.textlength(text, font=font_title)
        
    # Sombra del texto
    draw.text((WIDTH//2 - tw//2 + 4, y_offset + 4), text, font=font_title, fill=(0, 0, 0, 180))
    # Texto principal
    draw.text((WIDTH//2 - tw//2, y_offset), text, font=font_title, fill="white")
    y_offset += 105
    
    # DT Nombre con Badge
    dt_text = f"DIRECTOR TÉCNICO: {dt_nombre.upper()}"
    try:
        bbox = draw.textbbox((0, 0), dt_text, font=font_dt)
        dt_tw = bbox[2] - bbox[0]
        dt_th = bbox[3] - bbox[1]
    except:
        dt_tw = draw.textlength(dt_text, font=font_dt)
        dt_th = 40
        
    # Dibujar pastilla de fondo para el DT
    pad_x, pad_y = 30, 15
    draw.rounded_rectangle(
        [WIDTH//2 - dt_tw//2 - pad_x, y_offset - pad_y, WIDTH//2 + dt_tw//2 + pad_x, y_offset + dt_th + pad_y],
        radius=25, 
        fill=(0, 0, 0, 160),
        outline=(color_rgb[0], color_rgb[1], color_rgb[2], 255),
        width=2
    )
    draw.text((WIDTH//2 - dt_tw//2, y_offset), dt_text, font=font_dt, fill=(230, 230, 230, 255))
    y_offset += 110
    
    # 6. Dibujar Jugadores en Cajas Estilo "FUT" (Paneles)
    if len(jugadores) == 0:
        texto_vacio = "LA PLANTILLA ESTÁ VACÍA"
        draw.text((WIDTH//2 - 180, y_offset + 50), texto_vacio, font=font_dt, fill=(150, 150, 150, 255))
    
    col_width = WIDTH // 2
    box_width = 400
    box_height = 90
    
    # Coordenadas X para las 2 columnas
    col1_x = (col_width // 2) - (box_width // 2) + 20
    col2_x = col_width + (col_width // 2) - (box_width // 2) - 20
    
    current_col = 1
    current_y_col1 = y_offset
    current_y_col2 = y_offset
    
    for idx, (j_nombre, is_dt) in enumerate(jugadores):
        x = col1_x if current_col == 1 else col2_x
        y = current_y_col1 if current_col == 1 else current_y_col2
        
        # Panel de fondo del jugador (Cristal Oscuro)
        draw.rounded_rectangle(
            [x, y, x + box_width, y + box_height],
            radius=15,
            fill=(255, 255, 255, 12),  # Blanco súper transparente
            outline=(255, 255, 255, 30), # Borde sutil
            width=1
        )
        
        # Barra lateral de color del equipo (Decoración)
        draw.rounded_rectangle(
            [x, y, x + 12, y + box_height],
            radius=4,
            fill=(color_rgb[0], color_rgb[1], color_rgb[2], 255)
        )
        
        # Nombre del Jugador
        p_text = j_nombre.upper()
        draw.text((x + 35, y + 25), p_text, font=font_box, fill=(255, 255, 255, 255))
        
        # Etiqueta especial si es el Capitán/DT que también juega
        if is_dt:
            # Pastilla dorada
            draw.rounded_rectangle(
                [x + box_width - 90, y + 30, x + box_width - 15, y + 60],
                radius=8,
                fill=(255, 215, 0, 200) # Dorado
            )
            draw.text((x + box_width - 80, y + 34), "CAP", font=font_tag, fill=(0, 0, 0, 255))
        
        # Siguiente iteración
        if current_col == 1:
            current_y_col1 += box_height + 20
            current_col = 2
        else:
            current_y_col2 += box_height + 20
            current_col = 1

    # Convertir a RGB sólido para guardar compatible como PNG
    img_final = img.convert('RGB')

    # 7. Empaquetar bytes finales
    output = io.BytesIO()
    img_final.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


async def generar_tarjeta_jugador(nombre_jugador, avatar_url, equipo_nombre, color_hex, escudo_url, posicion, dorsal, goles, partidos, historial, asistencias=0, mvps=0, precio=0):
    """
    Player Card minimalista rediseñada.
    Historial: [(fecha_str, 'FICHAJE'/'DESPIDO'/'RENUNCIA', 'Equipo'), ...]
    """
    W = 780
    hist_rows = len(historial) if historial else 0
    H = 580 + hist_rows * 72
    BG   = (11, 11, 14, 255)
    CARD = (20, 20, 26, 255)

    color_rgb = hex_to_rgb(color_hex) if color_hex and color_hex != "#1a1a1a" else (212, 175, 55)
    ACCENT = color_rgb
    GOLD   = (212, 175, 55)

    img = Image.new('RGBA', (W, H), BG)
    draw = ImageDraw.Draw(img, 'RGBA')

    # ── Barra lateral de color del equipo (izquierda)
    draw.rectangle([0, 0, 6, H], fill=(*ACCENT, 255))

    # ── Degradado sutil del color del equipo en esquina superior derecha
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for r in range(340, 0, -8):
        a = int(((1 - r / 340) ** 2) * 55)
        gd.ellipse((W - r, -r//2, W + r, r + r//2), fill=(*ACCENT, a))
    img.alpha_composite(grad)

    # ── Fuentes
    try:
        fn_big   = ImageFont.truetype(FONT_DEFAULT, 54)
        fn_med   = ImageFont.truetype(FONT_DEFAULT, 26)
        fn_small = ImageFont.truetype(FONT_REGULAR, 20)
        fn_xs    = ImageFont.truetype(FONT_REGULAR, 16)
        fn_stat  = ImageFont.truetype(FONT_DEFAULT, 38)
    except:
        fn_big = fn_med = fn_small = fn_xs = fn_stat = ImageFont.load_default()

    # ── Helper: texto centrado en X
    def cx(text, font, x, y, fill):
        try:
            tw = draw.textlength(text, font=font)
        except:
            tw = len(text) * 10
        draw.text((x - tw // 2, y), text, font=font, fill=fill)

    # ── Descargas asíncronas
    logo_img   = await descargar_imagen(escudo_url) if escudo_url else None
    avatar_img = await descargar_imagen(avatar_url)  if avatar_url  else None

    # ── Marca de agua del escudo (fondo)
    if logo_img:
        wm = logo_img.copy()
        a  = wm.getchannel('A')
        a  = a.point(lambda i: int(i * 0.06))
        wm.putalpha(a)
        wm.thumbnail((480, 480), Image.Resampling.LANCZOS)
        img.alpha_composite(wm, (W // 2 - wm.width // 2, 30))

    # ══════════════════════════════════════════
    # SECCIÓN SUPERIOR: avatar + info
    # ══════════════════════════════════════════
    PAD   = 32
    AV    = 160   # tamaño avatar
    av_x  = PAD + 10
    av_y  = 36

    # Anillo del equipo
    ring = 8
    draw.ellipse((av_x - ring, av_y - ring, av_x + AV + ring, av_y + AV + ring),
                 fill=(*ACCENT, 255))
    draw.ellipse((av_x - 2, av_y - 2, av_x + AV + 2, av_y + AV + 2),
                 fill=BG)

    if avatar_img:
        av = avatar_img.resize((AV, AV), Image.Resampling.LANCZOS).convert('RGBA')
        mask = Image.new('L', (AV, AV), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, AV, AV), fill=255)
        circle = Image.new('RGBA', (AV, AV), (0, 0, 0, 0))
        circle.paste(av, (0, 0), mask)
        img.alpha_composite(circle, (av_x, av_y))

    # Info lateral derecha del avatar
    tx = av_x + AV + 26
    ty = av_y + 4

    # Nombre
    nombre_up = str(nombre_jugador).upper()
    try:
        nw = draw.textlength(nombre_up, font=fn_big)
    except:
        nw = 300
    # Recortar si es muy largo
    max_name_w = W - tx - PAD - 10
    if nw > max_name_w:
        nombre_up = nombre_up[:int(len(nombre_up) * max_name_w / nw) - 1] + '…'
    draw.text((tx, ty), nombre_up, font=fn_big, fill=(245, 245, 245, 255))
    ty += 62

    # Equipo actual con píldora de color
    eq_text = str(equipo_nombre).upper()
    try:
        eq_w = draw.textlength(eq_text, font=fn_med)
    except:
        eq_w = 120
    pill_pad = 14
    draw.rounded_rectangle(
        [tx - 2, ty - 4, tx + eq_w + pill_pad * 2, ty + 32],
        radius=10, fill=(*ACCENT, 200)
    )
    draw.text((tx + pill_pad, ty), eq_text, font=fn_med, fill=(0, 0, 0, 255))
    ty += 52

    # Posición y dorsal en línea
    badges = []
    if posicion:
        badges.append(str(posicion).upper())
    if dorsal and str(dorsal) != '??':
        badges.append(f"#{dorsal}")
    for badge in badges:
        try:
            bw = draw.textlength(badge, font=fn_small)
        except:
            bw = 50
        draw.rounded_rectangle(
            [tx - 2, ty - 3, tx + bw + 22, ty + 26],
            radius=8, fill=(255, 255, 255, 18), outline=(255, 255, 255, 35), width=1
        )
        draw.text((tx + 11, ty), badge, font=fn_small, fill=(0, 0, 0, 255))
        tx += bw + 36

    # Precio (esquina superior derecha)
    precio_str = f"${precio:,}" if precio else "—"
    try:
        pw = draw.textlength(precio_str, font=fn_med)
    except:
        pw = 80
    pr_x = W - PAD - pw - 16
    pr_y = av_y
    draw.rounded_rectangle(
        [pr_x - 10, pr_y - 2, pr_x + pw + 10, pr_y + 34],
        radius=10, fill=(*GOLD, 30), outline=(*GOLD, 120), width=1
    )
    draw.text((pr_x, pr_y), precio_str, font=fn_med, fill=(*GOLD, 255))
    label_p = "PRECIO"
    try:
        lw = draw.textlength(label_p, font=fn_xs)
    except:
        lw = 40
    draw.text((pr_x + (pw - lw) // 2, pr_y + 36), label_p, font=fn_xs, fill=(0, 0, 0, 255))

    # Logo escudo (arriba derecha, pequeño)
    if logo_img:
        sm = logo_img.copy()
        sm.thumbnail((52, 52), Image.Resampling.LANCZOS)
        img.alpha_composite(sm, (W - PAD - sm.width, pr_y + 62))

    # ══════════════════════════════════════════
    # SEPARADOR
    # ══════════════════════════════════════════
    sep_y = av_y + AV + 28
    draw.line((PAD, sep_y, W - PAD, sep_y), fill=(255, 255, 255, 22), width=1)

    # ══════════════════════════════════════════
    # STATS: PJ · GOLES · ASIST · MVPs
    # ══════════════════════════════════════════
    stats_y  = sep_y + 20
    stats    = [("PJ", partidos), ("GOLES", goles), ("ASIST", asistencias), ("MVPs", mvps)]
    n_stats  = len(stats)
    box_w    = (W - PAD * 2 - 12 * (n_stats - 1)) // n_stats
    box_h    = 88

    for i, (label, val) in enumerate(stats):
        bx = PAD + i * (box_w + 12)
        by = stats_y
        draw.rounded_rectangle(
            [bx, by, bx + box_w, by + box_h],
            radius=12, fill=(255, 255, 255, 10), outline=(255, 255, 255, 22), width=1
        )
        # acento top
        draw.rounded_rectangle(
            [bx + box_w // 2 - 22, by, bx + box_w // 2 + 22, by + 3],
            radius=2, fill=(*ACCENT, 220)
        )
        cx(label, fn_xs, bx + box_w // 2, by + 10, (0, 0, 0, 255))
        cx(str(val), fn_stat, bx + box_w // 2, by + 32, (0, 0, 0, 255))

    # ══════════════════════════════════════════
    # HISTORIAL DE EQUIPOS
    # ══════════════════════════════════════════
    hist_y = stats_y + box_h + 28
    draw.line((PAD, hist_y, W - PAD, hist_y), fill=(255, 255, 255, 22), width=1)
    hist_y += 16

    label_hist = "HISTORIAL DE EQUIPOS"
    try:
        lhw = draw.textlength(label_hist, font=fn_xs)
    except:
        lhw = 150
    draw.text((PAD, hist_y), label_hist, font=fn_xs, fill=(*GOLD, 200))
    hist_y += 28

    TIPO_COLOR = {
        'FICHAJE':  (46,  204, 113),
        'DESPIDO':  (231, 76,  60),
        'RENUNCIA': (241, 196, 15),
    }
    TIPO_LABEL = {
        'FICHAJE':  'FICHADO POR',
        'DESPIDO':  'DESPEDIDO DE',
        'RENUNCIA': 'RENUNCIÓ A',
    }

    if not historial:
        draw.text((PAD, hist_y + 10), "Sin registros de transferencias", font=fn_small, fill=(0, 0, 0, 255))
    else:
        for (fecha, tipo, eq_hist) in historial:
            bar_col = TIPO_COLOR.get(tipo, (120, 120, 120))
            accion  = TIPO_LABEL.get(tipo, tipo)
            row_h   = 56

            draw.rounded_rectangle(
                [PAD, hist_y, W - PAD, hist_y + row_h],
                radius=10, fill=(255, 255, 255, 8), outline=(255, 255, 255, 16), width=1
            )
            # barra lateral coloreada
            draw.rounded_rectangle(
                [PAD, hist_y, PAD + 5, hist_y + row_h],
                radius=3, fill=(*bar_col, 255)
            )
            # fecha
            draw.text((PAD + 16, hist_y + 8),  str(fecha),  font=fn_xs,    fill=(0, 0, 0, 255))
            # acción
            draw.text((PAD + 16, hist_y + 26), accion,      font=fn_small, fill=(*bar_col, 230))
            # equipo
            eq_up = str(eq_hist).upper()
            try:
                eqw = draw.textlength(eq_up, font=fn_med)
            except:
                eqw = 100
            draw.text((W - PAD - eqw - 6, hist_y + 16), eq_up, font=fn_med, fill=(0, 0, 0, 255))

            hist_y += row_h + 10

    # ══════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════
    footer_y = H - 28
    footer   = "AMAPICKS"
    try:
        fw = draw.textlength(footer, font=fn_xs)
    except:
        fw = 60
    draw.text((W // 2 - fw // 2, footer_y), footer, font=fn_xs, fill=(0, 0, 0, 255))

    img_final = img.convert('RGB')
    output = io.BytesIO()
    img_final.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
