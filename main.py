
import streamlit as st
import cv2
import numpy as np
import pytesseract
#pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Chemin pour Streamlit Cloud

from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw
import os

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

st.title("Anonymiseur de levés topographiques")
uploaded_file = st.file_uploader("Télécharge une image ou un PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    # Convertir PDF en image si nécessaire
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        img_pil = images[0]
    else:
        img_pil = Image.open(uploaded_file)

    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # OCR pour obtenir les coordonnées des mots
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    # Dessiner l'image originale avec annotations OCR (optionnel pour debug)
    img_preview = img_pil.copy()
    draw = ImageDraw.Draw(img_preview)
    for i in range(len(data['text'])):
        if data['text'][i].strip():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            draw.rectangle([x, y, x + w, y + h], outline="red")

    st.image(img_preview, caption="Texte détecté (encadré en rouge)")

    st.write("Utilise la souris pour *sélectionner les zones à supprimer* (via clic droit si tu veux relancer).")

    # Redimensionner l’image pour le canvas
    scale = 0.5
    resized_pil = img_pil.resize((int(img_pil.width * scale), int(img_pil.height * scale)))

    # Zone de dessin interactif
    from streamlit_drawable_canvas import st_canvas
    canvas_result = st_canvas(
        fill_color="white",
        stroke_width=3,
        background_image=resized_pil,
        update_streamlit=True,
        height=resized_pil.height,
        width=resized_pil.width,
        drawing_mode="rect",
        key="canvas"
    )

    if st.button("Supprimer les zones sélectionnées"):
        if canvas_result.json_data is not None:
            for obj in canvas_result.json_data["objects"]:
                left = int(obj["left"] / scale)
                top = int(obj["top"] / scale)
                width = int(obj["width"] / scale)
                height = int(obj["height"] / scale)
                cv2.rectangle(img_cv, (left, top), (left + width, top + height), (255, 255, 255), -1)

            # Afficher image anonymisée
            st.image(img_cv, caption="Image anonymisée")

            # Téléchargement
            result_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            result_pil = result_pil.convert('L')
            result_pil.save("leve_topographique_anonymise.png")
            with open(f"leve_topographique_anonymise.png", "rb") as f:
                name, ext = os.path.splitext(uploaded_file.name)
                final_name = f"{name}_anonymisee.png"

                st.download_button("📥 Télécharger le fichier anonymisé", f, final_name)