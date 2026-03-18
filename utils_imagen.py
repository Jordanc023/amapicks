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
    
    # 2. Degradado Radial Dorado Estándar para todos los clubes
    gradient = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    
    # Color Dorado Brillante (RGB)
    gold_rgb = (212, 175, 55)
    
    center_x, center_y = WIDTH // 2, HEIGHT // 3
    max_radius = 900
    
    for r in range(max_radius, 0, -10):
        # Curva de opacidad (Efecto brillo inmersivo dorado en el centro)
        alpha = int(((1 - (r / max_radius))**2) * 110) 
        draw_grad.ellipse(
            (center_x - r, center_y - r, center_x + r, center_y + r),
            fill=(gold_rgb[0], gold_rgb[1], gold_rgb[2], alpha)
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


async def generar_tarjeta_jugador(nombre_jugador, avatar_url, equipo_nombre, color_hex, escudo_url, posicion, dorsal, goles, partidos, historial):
    """
    Genera visualmente una 'Player Card' coleccionable para el Comando Historial.
    Historial debe ser lista de tuplas: [(fecha_str, 'FICHAJE'/'DESPIDO'/'RENUNCIA', 'Equipo'), ...]
    """
    WIDTH = 800
    # Calcular alto dinámico en función del tamaño del historial
    base_height = 920
    if historial and len(historial) > 0:
        base_height += len(historial) * 85
    HEIGHT = base_height
    
    # 1. Lienzo Oscuro Global (Fondo base Negro Profundo)
    img = Image.new('RGBA', (WIDTH, HEIGHT), color=(10, 10, 12, 255))
    
    # 2. Degradado Radial Dorado Estándar
    gradient = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    gold_rgb = (212, 175, 55)
    
    center_x, center_y = WIDTH // 2, 400
    max_radius = 700
    
    for r in range(max_radius, 0, -10):
        # Curva de opacidad (Efecto brillo inmersivo dorado en el centro)
        alpha = int(((1 - (r / max_radius))**2) * 110) 
        draw_grad.ellipse(
            (center_x - r, center_y - r, center_x + r, center_y + r),
            fill=(gold_rgb[0], gold_rgb[1], gold_rgb[2], alpha)
        )
    img.alpha_composite(gradient)
    
    color_rgb = hex_to_rgb(color_hex)
    
    # 3. Cargar Fuentes
    try:
        font_title = ImageFont.truetype(FONT_DEFAULT, 75)
        font_subtitle = ImageFont.truetype(FONT_REGULAR, 32)
        font_box = ImageFont.truetype(FONT_DEFAULT, 48)
        font_tag = ImageFont.truetype(FONT_REGULAR, 22)
        font_hist_date = ImageFont.truetype(FONT_DEFAULT, 18)
        font_hist_text = ImageFont.truetype(FONT_REGULAR, 24)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_box = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        font_hist_date = ImageFont.load_default()
        font_hist_text = ImageFont.load_default()
        
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 4. Escudo Posterior Gigante (Opcional, si tiene)
    if escudo_url:
        logo = await descargar_imagen(escudo_url)
        if logo:
            watermark = logo.copy()
            a = watermark.getchannel('A')
            a = a.point(lambda i: int(i * 0.05)) # Solo 5% Opacidad
            watermark.putalpha(a)
            watermark.thumbnail((800, 800), Image.Resampling.LANCZOS)
            img.alpha_composite(watermark, (WIDTH//2 - watermark.width//2, 200))
            
            # Escudo Cabecera Alta-Derecha
            logo.thumbnail((120, 120), Image.Resampling.LANCZOS)
            img.alpha_composite(logo, (WIDTH - 150, 30))

    # 5. Avatar Circular (Corte Perfecto)
    avatar_img = None
    if avatar_url:
        avatar_img = await descargar_imagen(avatar_url)
        
    if avatar_img:
        av_size = 280
        avatar_img = avatar_img.resize((av_size, av_size), Image.Resampling.LANCZOS).convert("RGBA")
        
        # Crear máscara circular redonda perfecta
        mask = Image.new('L', (av_size, av_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, av_size, av_size), fill=255)
        
        avatar_circle = Image.new('RGBA', (av_size, av_size), (0,0,0,0))
        avatar_circle.paste(avatar_img, (0, 0), mask)
        
        avatar_x = WIDTH//2 - av_size//2
        avatar_y = 110
        
        # Dibujar anillo detrás (Color del Club y Borde interior)
        ring_pad = 10
        draw.ellipse((avatar_x - ring_pad, avatar_y - ring_pad, avatar_x + av_size + ring_pad, avatar_y + av_size + ring_pad), fill=(color_rgb[0], color_rgb[1], color_rgb[2], 255))
        draw.ellipse((avatar_x - 3, avatar_y - 3, avatar_x + av_size + 3, avatar_y + av_size + 3), fill=(10,10,12,255))
        
        img.alpha_composite(avatar_circle, (avatar_x, avatar_y))

    # 6. Posición (Badge Alta-Izquierda)
    if posicion:
        draw.rounded_rectangle([30, 40, 160, 100], radius=15, fill=(gold_rgb[0], gold_rgb[1], gold_rgb[2], 255))
        try:
            ptw = draw.textlength(str(posicion), font=font_subtitle)
        except:
            ptw = 60
        draw.text((30 + (130 - ptw)//2, 53), str(posicion), font=font_subtitle, fill=(0,0,0,255))
    
    y_offset = 430
    
    # 7. Nombre del Jugador
    text_nombre = str(nombre_jugador).upper()
    try:
        tw = draw.textlength(text_nombre, font=font_title)
    except:
        tw = 300
    draw.text((WIDTH//2 - tw//2 + 3, y_offset + 3), text_nombre, font=font_title, fill=(0, 0, 0, 180))
    draw.text((WIDTH//2 - tw//2, y_offset), text_nombre, font=font_title, fill="white")
    y_offset += 80
    
    # 8. Equipo Actual Name
    try:
        etw = draw.textlength(str(equipo_nombre).upper(), font=font_subtitle)
    except:
        etw = 150
    draw.text((WIDTH//2 - etw//2, y_offset), str(equipo_nombre).upper(), font=font_subtitle, fill=(200, 200, 200, 255))
    y_offset += 80
    
    # 9. Cajas de Estadísticas (FUT Panels)
    box_w = 210
    box_h = 100
    gap = 35
    start_x = (WIDTH - (box_w * 3 + gap * 2)) // 2
    
    def dibujar_stat(x, y, titulo, valor):
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=15, fill=(255, 255, 255, 12), outline=(255, 255, 255, 30), width=1)
        # raya top
        draw.rounded_rectangle([x + 30, y, x + box_w - 30, y + 4], radius=2, fill=(color_rgb[0], color_rgb[1], color_rgb[2], 255))
        
        # titulo
        try:
            ttw = draw.textlength(titulo, font=font_tag)
        except:
            ttw = 60
        draw.text((x + box_w//2 - ttw//2, y + 14), titulo, font=font_tag, fill=(180, 180, 180, 255))
        
        # valor numerico
        val_str = str(valor)
        try:
            vtw = draw.textlength(val_str, font=font_box)
        except:
            vtw = 40
        draw.text((x + box_w//2 - vtw//2, y + 42), val_str, font=font_box, fill="white")

    dibujar_stat(start_x, y_offset, "PARTIDOS", partidos)
    dibujar_stat(start_x + box_w + gap, y_offset, "GOLES", goles)
    dibujar_stat(start_x + (box_w + gap)*2, y_offset, "DORSAL", dorsal)
    
    y_offset += box_h + 60
    
    # Línea separadora
    draw.line((100, y_offset, WIDTH - 100, y_offset), fill=(255,255,255,40), width=2)
    y_offset += 40
    
    # 10. Timeline Historial
    hist_title = "HISTORIAL DE TRANSFERENCIAS"
    try:
        htw = draw.textlength(hist_title, font=font_tag)
    except:
        htw = 200
    draw.text((WIDTH//2 - htw//2, y_offset), hist_title, font=font_tag, fill=(gold_rgb[0], gold_rgb[1], gold_rgb[2], 255))
    y_offset += 55
    
    if len(historial) == 0:
        draw.text((WIDTH//2 - 140, y_offset + 20), "SIN REGISTROS DE LIGA", font=font_hist_text, fill=(120, 120, 120, 255))
    else:
        for (fecha, tipo, eq_hist) in historial:
            hx = 70
            
            # Colorimetría del Timeline
            bar_color = (150, 150, 150, 255)
            if tipo == 'FICHAJE':
                bar_color = (46, 204, 113, 255) # Verde Esmeralda
                icon_text = "FICHADO POR"
            elif tipo == 'DESPIDO':
                bar_color = (231, 76, 60, 255) # Rojo Fuerte
                icon_text = "DESPEDIDO DE"
            elif tipo == 'RENUNCIA':
                bar_color = (241, 196, 15, 255) # Amarillo 
                icon_text = "RENUNCIÓ A"
            else:
                icon_text = str(tipo)
                
            # Renderizado de caja del evento
            draw.rounded_rectangle([hx, y_offset, WIDTH - hx, y_offset + 70], radius=12, fill=(255,255,255, 12), outline=(255, 255, 255, 20), width=1)
            # Rayita identificadora estado 
            draw.rounded_rectangle([hx, y_offset, hx + 8, y_offset + 70], radius=4, fill=bar_color)
            
            # Píldora de Fecha
            draw.rounded_rectangle([hx + 25, y_offset + 22, hx + 105, y_offset + 48], radius=8, fill=(0,0,0,200))
            draw.text((hx + 33, y_offset + 25), str(fecha), font=font_hist_date, fill=(200,200,200,255))
            
            # Texto Acción principal
            action_str = f"{icon_text}  {str(eq_hist).upper()}"
            draw.text((hx + 125, y_offset + 20), action_str, font=font_hist_text, fill="white")
            
            y_offset += 85

    # Convertir a RGB sólido para Discord PNG
    img_final = img.convert('RGB')

    output = io.BytesIO()
    img_final.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
