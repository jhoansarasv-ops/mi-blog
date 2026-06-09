import streamlit as st
from datetime import datetime
import json
import os
import base64
from io import BytesIO
from PIL import Image

# ==================== CONFIGURACIÓN ====================
st.set_page_config(
    page_title="✨ Mi Blog",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== FUNCIONES ====================
ARCHIVO = "posts.json"

def cargar():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar(lista):
    with open(ARCHIVO, 'w', encoding='utf-8') as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

def comprimir_imagen(imagen, max_size_mb=10):
    """Comprime imagen a máximo 10MB"""
    img = Image.open(imagen)

    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Redimensionar si es muy grande
    max_width = 2000
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Comprimir
    buffer = BytesIO()
    quality = 95
    max_size_kb = max_size_mb * 1024

    while True:
        buffer.seek(0)
        buffer.truncate()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        size_kb = buffer.tell() / 1024

        if size_kb <= max_size_kb or quality <= 10:
            break
        quality -= 5

    return buffer.getvalue(), size_kb

def imagen_a_base64(imagen_bytes):
    return base64.b64encode(imagen_bytes).decode()

# ==================== HEADER ====================
st.title("✨ Mi Blog de Publicaciones")
st.caption("Ciencia, tecnología y reflexiones del día a día")

# ==================== ESTADÍSTICAS ====================
posts = cargar()
total_posts = len(posts)
total_lecturas = sum(p.get("lecturas", 0) for p in posts)
total_likes = sum(p.get("likes", 0) for p in posts)
categorias_unicas = len(set(p["categoria"] for p in posts)) if posts else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("📝 Publicaciones", total_posts)
col2.metric("👁️ Lecturas", total_lecturas)
col3.metric("❤️ Me gusta", total_likes)
col4.metric("🏷️ Categorías", categorias_unicas)

# ==================== BOTÓN Y BÚSQUEDA ====================
st.divider()

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("➕ Nueva Publicación", use_container_width=True):
        st.session_state.mostrar_form = True

with col2:
    busqueda = st.text_input("🔍 Buscar publicaciones...", placeholder="Escribe para buscar...")

# ==================== FILTROS SIDEBAR ====================
st.sidebar.markdown("### 🏷️ Filtrar por categoría")
categorias = ["Todas"] + list(set(p["categoria"] for p in posts))
cat_filtro = st.sidebar.selectbox("Categoría", categorias)

if cat_filtro != "Todas":
    posts = [p for p in posts if p["categoria"] == cat_filtro]

if busqueda:
    posts = [p for p in posts if busqueda.lower() in p["titulo"].lower() or busqueda.lower() in p.get("resumen", "").lower()]

posts = sorted(posts, key=lambda x: x["fecha"], reverse=True)

# ==================== FORMULARIO NUEVA PUBLICACIÓN ====================
if st.session_state.get("mostrar_form", False):
    with st.container():
        st.subheader("✍️ Crear nueva publicación")

        with st.form("formulario"):
            col1, col2 = st.columns(2)
            with col1:
                titulo = st.text_input("📌 Título *", placeholder="Título atractivo...")
                autor = st.text_input("👤 Autor", placeholder="Tu nombre")
            with col2:
                categoria = st.selectbox("🏷️ Categoría", [
                    "ciencia", "tecnologia", "dia-a-dia", "opinion",
                    "arte", "salud", "viajes", "cocina", "fotografia", "musica"
                ])
                tags = st.text_input("🏷️ Tags", placeholder="python, IA, tutorial...")

            resumen = st.text_area("📝 Resumen", max_chars=300, placeholder="Breve descripción...", height=80)

            # 📸 SUBIR IMAGEN (LÍMITE 10MB)
            st.markdown("### 📸 Imagen de portada (opcional)")
            st.info("📏 Máximo 10 MB. Formatos: PNG, JPG, JPEG, GIF.")

            imagen_subida = st.file_uploader(
                "Selecciona imagen",
                type=['png', 'jpg', 'jpeg', 'gif'],
                help="Tamaño máximo: 10MB"
            )

            imagen_base64 = None
            imagen_tamano = 0

            if imagen_subida is not None:
                tamaño_original = len(imagen_subida.getvalue()) / (1024 * 1024)
                st.write(f"📁 Tamaño original: {tamaño_original:.2f} MB")

                if tamaño_original > 10:
                    st.error(f"❌ La imagen pesa {tamaño_original:.2f} MB. Máximo permitido: 10 MB.")
                else:
                    try:
                        with st.spinner("🔄 Comprimiendo imagen..."):
                            imagen_bytes, tamano_kb = comprimir_imagen(imagen_subida, max_size_mb=10)
                            imagen_base64 = imagen_a_base64(imagen_bytes)
                            imagen_tamano = tamano_kb

                        st.image(imagen_bytes, caption=f"✅ Imagen lista: {tamano_kb:.1f} KB", width=300)

                    except Exception as e:
                        st.error(f"❌ Error al procesar imagen: {e}")

            contenido = st.text_area("📄 Contenido completo *", height=200, placeholder="Escribe tu artículo aquí...")

            col1, col2 = st.columns(2)
            with col1:
                publicar = st.form_submit_button("🚀 Publicar ahora", use_container_width=True)
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

            if publicar and titulo and contenido:
                if imagen_subida and not imagen_base64:
                    st.error("❌ La imagen es demasiado grande. Máximo 10MB.")
                else:
                    posts = cargar()
                    nuevo = {
                        "id": len(posts) + 1,
                        "titulo": titulo,
                        "autor": autor or "Anónimo",
                        "fecha": datetime.now().strftime("%Y-%m-%d"),
                        "categoria": categoria,
                        "tags": [t.strip() for t in tags.split(",") if t.strip()],
                        "resumen": resumen,
                        "contenido": contenido,
                        "lectura": max(1, len(contenido.split()) // 200),
                        "lecturas": 0,
                        "likes": 0,
                        "imagen": imagen_base64,
                        "imagen_size": imagen_tamano
                    }
                    posts.append(nuevo)
                    guardar(posts)
                    st.success("✅ ¡Publicación creada con éxito!")
                    st.balloons()
                    st.session_state.mostrar_form = False
                    st.rerun()

            if cancelar:
                st.session_state.mostrar_form = False
                st.rerun()

# ==================== PUBLICACIONES ====================
st.divider()
st.subheader(f"📚 {len(posts)} publicaciones encontradas")

if not posts:
    st.info("📝 No hay publicaciones aún. ¡Crea la primera!")

for i, post in enumerate(posts):
    emoji_cat = {
        "ciencia": "🔬", "tecnologia": "💻", "dia-a-dia": "☕",
        "opinion": "💭", "arte": "🎨", "salud": "❤️",
        "viajes": "✈️", "cocina": "🍳", "fotografia": "📷", "musica": "🎵"
    }.get(post["categoria"], "📝")

    # TARJETA DE POST con componentes nativos de Streamlit
    with st.container():
        # Header con color
        st.markdown(f"### {emoji_cat} {post['titulo']}")

        # Mostrar imagen si existe
        if post.get("imagen"):
            try:
                imagen_bytes = base64.b64decode(post["imagen"])
                st.image(imagen_bytes, use_container_width=True)
            except:
                pass

        # Meta info
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"👤 **{post['autor']}**")
        with col2:
            st.write(f"📅 {post['fecha']}")
        with col3:
            st.write(f"⏱️ {post.get('lectura', 1)} min")

        # Tags
        tags = post.get("tags", [])
        if tags:
            tag_text = " · ".join([f"🏷️ {t}" for t in tags])
            st.caption(tag_text)

        # Resumen
        st.write(post.get("resumen", "Sin resumen"))

        # Botones
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button(f"📖 Leer artículo", key=f"leer_{post['id']}", use_container_width=True):
                st.session_state.ver_post = post["id"]
                posts_data = cargar()
                for p in posts_data:
                    if p["id"] == post["id"]:
                        p["lecturas"] = p.get("lecturas", 0) + 1
                guardar(posts_data)
                st.rerun()

        with col2:
            likes = post.get("likes", 0)
            if st.button(f"❤️ {likes}", key=f"like_{post['id']}", use_container_width=True):
                posts_data = cargar()
                for p in posts_data:
                    if p["id"] == post["id"]:
                        p["likes"] = p.get("likes", 0) + 1
                guardar(posts_data)
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_{post['id']}", use_container_width=True):
                posts_data = cargar()
                posts_data = [p for p in posts_data if p["id"] != post["id"]]
                guardar(posts_data)
                st.success("🗑️ Eliminado")
                st.rerun()

        # Contenido completo
        if st.session_state.get("ver_post") == post["id"]:
            with st.expander("📄 Artículo completo", expanded=True):
                st.markdown(f"### {post['titulo']}")
                st.write(f"*{post['autor']} | {post['fecha']}*")

                # Imagen grande
                if post.get("imagen"):
                    try:
                        imagen_bytes = base64.b64decode(post["imagen"])
                        st.image(imagen_bytes, use_container_width=True)
                    except:
                        pass

                st.write(post["contenido"])

                likes = post.get("likes", 0)
                lecturas = post.get("lecturas", 0)
                st.write(f"❤️ **{likes}** me gusta · 👁️ **{lecturas}** lecturas")

                if st.button("✖️ Cerrar", key=f"cerrar_{post['id']}"):
                    st.session_state.ver_post = None
                    st.rerun()

        st.divider()

# ==================== FOOTER ====================
st.divider()
st.markdown("### 🚀 Mi Blog")
st.caption("Compartiendo conocimiento desde 2026 | Hecho con ❤️ usando Streamlit + Python | 📸 Imágenes hasta 10MB")
