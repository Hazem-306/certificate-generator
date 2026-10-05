import os
import tempfile
import zipfile
import shutil
import base64
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

# Running the app
# streamlit run web/main.py

# Add project root to sys.path
from excel_parser import ExcelParser
from pdf_handler import PDFHandler
from config import PRIMARY_RED, APP_NAME

# Declare custom lightweight interactive box canvas component
BOX_CANVAS_DIR = Path(__file__).resolve().parent / "box_canvas"

box_canvas = components.declare_component(
    "box_canvas",
    path=str(BOX_CANVAS_DIR)
)

# Page setup
st.set_page_config(
    page_title=f"{APP_NAME} - Web Interface",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown(f"""
    <style>
    .main-header {{
        background-color: {PRIMARY_RED};
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(229, 0, 0, 0.2);
    }}
    .main-header h1 {{
        color: white !important;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }}
    .main-header p {{
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }}
    .stButton>button {{
        background-color: {PRIMARY_RED};
        color: white;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #b30000;
        color: white;
        transform: translateY(-1px);
    }}
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
    .box-card {{
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid {PRIMARY_RED};
        margin-bottom: 12px;
    }}
    </style>
""", unsafe_allow_html=True)


def create_default_text_box(label="Name", source_type="Excel Column", column="", fixed_text="",
                           x_start=15, x_end=85, y_start=42, y_end=58,
                           font="Arial", size=60, color="#000000", align="center", bold=True, italic=False):
    return {
        "label": label,
        "source_type": source_type,
        "column": column,
        "fixed_text": fixed_text,
        "x_start_pct": x_start,
        "x_end_pct": x_end,
        "y_start_pct": y_start,
        "y_end_pct": y_end,
        "font": font,
        "size": size,
        "color": color,
        "align": align,
        "bold": bold,
        "italic": italic
    }


def init_session_state():
    if "template_img" not in st.session_state:
        st.session_state.template_img = None
    if "template_path" not in st.session_state:
        st.session_state.template_path = None
    if "excel_data" not in st.session_state:
        st.session_state.excel_data = None
    if "columns" not in st.session_state:
        st.session_state.columns = []
    if "text_boxes" not in st.session_state:
        st.session_state.text_boxes = [create_default_text_box(label="Recipient Name")]
    if "output_folder" not in st.session_state:
        st.session_state.output_folder = ""
    if "active_box_idx" not in st.session_state:
        st.session_state.active_box_idx = 0
    if "preview_row_idx" not in st.session_state:
        st.session_state.preview_row_idx = 0
    if "canvas_version" not in st.session_state:
        st.session_state.canvas_version = 0


def render_preview_image_multi(img, text_boxes, excel_data=None, sample_row_idx=0, draw_boxes=True):
    """
    Renders a live preview with all text boxes and styled text overlays using Pillow.
    """
    if img is None:
        return None

    preview = img.copy().convert("RGB")
    draw = ImageDraw.Draw(preview)
    img_w, img_h = preview.size

    box_colors = [(229, 0, 0), (0, 102, 204), (0, 153, 76), (153, 0, 204), (204, 102, 0)]

    for idx, box in enumerate(text_boxes):
        color = box_colors[idx % len(box_colors)]

        # Box coordinates
        x_min = int(img_w * (box["x_start_pct"] / 100.0))
        x_max = int(img_w * (box["x_end_pct"] / 100.0))
        y_min = int(img_h * (box["y_start_pct"] / 100.0))
        y_max = int(img_h * (box["y_end_pct"] / 100.0))

        if draw_boxes:
            line_w = max(2, int(min(img_w, img_h) / 300))
            draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=line_w)

            # Draw label tag above box
            label_text = f"#{idx+1} {box.get('label', 'Box')}"
            draw.text((x_min + 4, max(2, y_min - 22)), label_text, fill=color)

        # Obtain text value
        if box["source_type"] == "Excel Column":
            col_name = box.get("column")
            if excel_data and col_name and sample_row_idx < len(excel_data):
                sample_text = str(excel_data[sample_row_idx].get(col_name, ""))
            else:
                sample_text = f"[{col_name or 'Select Column'}]"
        else:
            sample_text = box.get("fixed_text", "Fixed Text")

        if not sample_text:
            continue

        # Font styling
        font_size = int(box.get("size", 60))
        color_hex = box.get("color", "#000000").lstrip("#")
        if len(color_hex) == 6:
            text_color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        else:
            text_color = (0, 0, 0)

        font_name = box.get("font", "Arial")
        font_file = "arial.ttf"
        if font_name == "Calibri":
            font_file = "calibri.ttf"
        elif font_name == "Times-Roman":
            font_file = "times.ttf"
        elif font_name == "Courier":
            font_file = "cour.ttf"

        try:
            font = ImageFont.truetype(font_file, font_size)
        except Exception:
            font = ImageFont.load_default()

        box_w = x_max - x_min
        box_h = y_max - y_min
        center_y = y_min + box_h / 2

        try:
            bbox = font.getbbox(sample_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(sample_text, font=font)

        align = box.get("align", "center")
        if align == "center":
            text_x = x_min + (box_w - text_w) / 2
        elif align == "right":
            text_x = x_max - text_w
        else:
            text_x = x_min

        text_y = center_y - text_h / 2
        draw.text((text_x, text_y), sample_text, fill=text_color, font=font)

    return preview


def safe_fragment_rerun():
    """
    Reruns the current fragment if currently executing in a fragment-scoped run,
    otherwise safely falls back to standard st.rerun() to avoid StreamlitInvalidLayoutContextError.
    """
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


@st.fragment
def preview_and_box_editor_fragment():
    st.subheader("🖼️ Live Visual Preview & Interactive Box Editor")

    if st.session_state.template_img is not None:
        excel_rows = st.session_state.excel_data or []

        c_row, c_box = st.columns([0.55, 0.45])
        with c_row:
            if excel_rows:
                st.session_state.preview_row_idx = st.selectbox(
                    "Preview Recipient Row:",
                    options=list(range(len(excel_rows))),
                    index=min(st.session_state.preview_row_idx, len(excel_rows) - 1),
                    format_func=lambda i: f"Row #{i+1}: " + " | ".join([f"{k}: {v}" for k, v in list(excel_rows[i].items())[:2]]),
                    key="frag_preview_row_select"
                )
            else:
                st.caption("ℹ️ Upload Excel in sidebar to preview real recipient rows.")

        num_boxes = len(st.session_state.text_boxes)
        with c_box:
            if num_boxes > 1:
                st.session_state.active_box_idx = st.selectbox(
                    "Active Box to Drag / Resize / Draw:",
                    options=list(range(num_boxes)),
                    index=min(st.session_state.active_box_idx, num_boxes - 1),
                    format_func=lambda idx: f"Box #{idx+1}: {st.session_state.text_boxes[idx].get('label', 'Text Box')}",
                    key="frag_active_box_select"
                )
            else:
                st.session_state.active_box_idx = 0
                st.caption(f"Active: Box #1 ({st.session_state.text_boxes[0].get('label', 'Recipient Name')})")

        # Render preview image with live text (draw_boxes=False so canvas component overlays interactive handles)
        preview_img = render_preview_image_multi(
            st.session_state.template_img,
            st.session_state.text_boxes,
            excel_data=excel_rows,
            sample_row_idx=st.session_state.preview_row_idx,
            draw_boxes=False
        )

        buf = BytesIO()
        preview_img.save(buf, format="JPEG", quality=88)
        b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
        img_url = f"data:image/jpeg;base64,{b64_data}"

        # Interactive Canvas Component directly overlaid on live preview
        res = box_canvas(
            image_url=img_url,
            boxes=st.session_state.text_boxes,
            active_idx=st.session_state.active_box_idx,
            key=f"box_canvas_{st.session_state.get('canvas_version', 0)}"
        )

        if res and isinstance(res, dict):
            action = res.get("action")
            if action == "select_box":
                new_idx = res.get("active_idx", 0)
                if new_idx != st.session_state.active_box_idx:
                    st.session_state.active_box_idx = new_idx
                    safe_fragment_rerun()
            elif action == "update_box":
                idx = res.get("active_idx", 0)
                if idx < len(st.session_state.text_boxes):
                    tb = st.session_state.text_boxes[idx]
                    new_xs = float(res.get("x_start", tb["x_start_pct"]))
                    new_xe = float(res.get("x_end", tb["x_end_pct"]))
                    new_ys = float(res.get("y_start", tb["y_start_pct"]))
                    new_ye = float(res.get("y_end", tb["y_end_pct"]))
                    changed = (
                        abs(tb["x_start_pct"] - new_xs) > 0.05 or
                        abs(tb["x_end_pct"] - new_xe) > 0.05 or
                        abs(tb["y_start_pct"] - new_ys) > 0.05 or
                        abs(tb["y_end_pct"] - new_ye) > 0.05
                    )
                    if changed:
                        tb["x_start_pct"] = new_xs
                        tb["x_end_pct"] = new_xe
                        tb["y_start_pct"] = new_ys
                        tb["y_end_pct"] = new_ye
                        safe_fragment_rerun()

        active_box = st.session_state.text_boxes[st.session_state.active_box_idx]
        col_badge, col_center, col_top = st.columns([0.6, 0.2, 0.2])
        with col_badge:
            st.info(
                f"📍 **Box #{st.session_state.active_box_idx+1} ({active_box.get('label', 'Text Box')}) Coordinates:** "
                f"**X:** {active_box['x_start_pct']}% → {active_box['x_end_pct']}% &nbsp;|&nbsp; "
                f"**Y:** {active_box['y_start_pct']}% → {active_box['y_end_pct']}%"
            )
        with col_center:
            if st.button("Center Box", key="btn_frag_center", use_container_width=True):
                active_box["x_start_pct"], active_box["x_end_pct"] = 15.0, 85.0
                st.session_state.canvas_version = st.session_state.get("canvas_version", 0) + 1
                safe_fragment_rerun()
        with col_top:
            if st.button("Top / Code", key="btn_frag_top", use_container_width=True):
                active_box["x_start_pct"], active_box["x_end_pct"] = 60.0, 95.0
                active_box["y_start_pct"], active_box["y_end_pct"] = 10.0, 25.0
                st.session_state.canvas_version = st.session_state.get("canvas_version", 0) + 1
                safe_fragment_rerun()
    else:
        st.info("👈 Upload a certificate template image in the sidebar to view live preview and draw text boxes directly on it.")


@st.fragment
def output_settings_fragment():
    st.subheader("⚙️ Output Settings")

    export_mode = st.radio(
        "Export Options:",
        options=["Single Files", "Merged File", "Compressed File"],
        index=0,
        help=(
            "• Single Files: Download a ZIP containing separate PDF files for each recipient.\n"
            "• Merged File: Download a single PDF containing all certificates.\n"
            "• Compressed File: Download a compressed ZIP containing the merged PDF."
        )
    )

    # Validate Readiness
    excel_rows = st.session_state.excel_data or []
    has_template = st.session_state.template_path is not None and os.path.exists(st.session_state.template_path)
    has_data = len(excel_rows) > 0

    if not has_template:
        st.warning("⚠️ Please upload a certificate template image in the sidebar.")
    if not has_data:
        st.warning("⚠️ Please upload a recipient Excel spreadsheet in the sidebar.")

    can_generate = has_template and has_data

    if st.button("🚀 Generate Certificates Now", disabled=not can_generate, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(excel_rows)

        # Build text_configs for reportlab canvas
        img_w, img_h = st.session_state.template_img.size
        text_configs = []
        for box in st.session_state.text_boxes:
            x_min = int(img_w * (box["x_start_pct"] / 100.0))
            x_max = int(img_w * (box["x_end_pct"] / 100.0))
            y_min = int(img_h * (box["y_start_pct"] / 100.0))
            y_max = int(img_h * (box["y_end_pct"] / 100.0))
            text_configs.append({
                "box": (x_min, y_min, x_max, y_max),
                "font": box.get("font", "Arial"),
                "size": box.get("size", 60),
                "color": box.get("color", "#000000"),
                "align": box.get("align", "center"),
                "bold": box.get("bold", True),
                "italic": box.get("italic", False)
            })

        # Build row field values
        rows_fields_values = []
        for row in excel_rows:
            f_vals = []
            for box in st.session_state.text_boxes:
                if box["source_type"] == "Excel Column":
                    col_name = box.get("column")
                    val = str(row.get(col_name, "")) if col_name else ""
                else:
                    val = box.get("fixed_text", "")
                f_vals.append(val)
            rows_fields_values.append(f_vals)

        try:
            if export_mode == "Merged File":
                status_text.text("Generating merged PDF document...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as out_pdf:
                    out_path = out_pdf.name

                def progress_cb(curr, tot, msg):
                    progress_bar.progress(curr / tot)
                    status_text.text(f"{msg}: {curr}/{tot}")

                PDFHandler.generate_merged_certificates_multi(
                    st.session_state.template_path,
                    rows_fields_values,
                    text_configs,
                    out_path,
                    progress_cb=progress_cb
                )

                with open(out_path, "rb") as f:
                    pdf_data = f.read()

                os.remove(out_path)
                progress_bar.progress(1.0)
                status_text.success(f"✅ Generated {total} certificates in 1 merged PDF file!")

                st.download_button(
                    label="📥 Download Merged File (PDF)",
                    data=pdf_data,
                    file_name="Certificates_Merged.pdf",
                    mime="application/pdf"
                )

            elif export_mode == "Compressed File":
                status_text.text("Generating merged certificates...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as out_pdf:
                    out_path = out_pdf.name

                def progress_cb(curr, tot, msg):
                    progress_bar.progress(curr / tot)
                    status_text.text(f"{msg}: {curr}/{tot}")

                PDFHandler.generate_merged_certificates_multi(
                    st.session_state.template_path,
                    rows_fields_values,
                    text_configs,
                    out_path,
                    progress_cb=progress_cb
                )

                status_text.text("Compressing merged file into ZIP...")
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(out_path, arcname="Certificates_Merged.pdf")

                zip_data = zip_buffer.getvalue()
                os.remove(out_path)
                progress_bar.progress(1.0)
                status_text.success(f"✅ Generated {total} certificates in 1 compressed (zipped) file!")

                st.download_button(
                    label="📥 Download Compressed File (ZIP)",
                    data=zip_data,
                    file_name="Certificates_Compressed.zip",
                    mime="application/zip"
                )

            else: # "Single Files"
                status_text.text("Generating separate certificate PDF files...")
                zip_buffer = BytesIO()

                with tempfile.TemporaryDirectory() as temp_dir:
                    pdf_paths = []
                    for i, row in enumerate(excel_rows):
                        f_vals = rows_fields_values[i]
                        file_name_label = f_vals[0] if f_vals and f_vals[0] else f"Certificate_{i+1}"
                        safe_name = "".join([c for c in file_name_label if c.isalnum() or c in (" ", "_", "-")]).strip()
                        if not safe_name:
                            safe_name = f"Certificate_{i+1}"

                        out_single = os.path.join(temp_dir, f"{safe_name}.pdf")
                        PDFHandler.generate_certificate_multi(
                            st.session_state.template_path,
                            f_vals,
                            text_configs,
                            out_single
                        )
                        pdf_paths.append((out_single, f"{safe_name}.pdf"))
                        progress_bar.progress((i + 1) / total)
                        status_text.text(f"Generating certificate {i+1} of {total}: {safe_name}.pdf")

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for pdf_file, arc_name in pdf_paths:
                            zip_file.write(pdf_file, arcname=arc_name)

                zip_buffer.seek(0)
                progress_bar.progress(1.0)
                status_text.success(f"✅ Generated {total} separate certificate PDF files (1 per recipient)!")

                st.download_button(
                    label="📥 Download Single Files (ZIP of separate PDFs)",
                    data=zip_buffer,
                    file_name="Certificates_Single_Files.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"❌ Error during generation: {e}")


def main():
    init_session_state()

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("⚙️ Certificate Controls")

        # 1. Assets Upload Section
        st.subheader("**1. 📁 Assets Upload**")

        uploaded_template = st.file_uploader(
            "Certificate Template (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key="sb_template_uploader"
        )
        if uploaded_template is not None:
            image = Image.open(uploaded_template)
            st.session_state.template_img = image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                image.save(tmp_file.name)
                st.session_state.template_path = tmp_file.name
            st.success(f"Template: {image.width} &times; {image.height} px")

        uploaded_excel = st.file_uploader(
            "Recipient Excel Data (.xlsx/.xls)",
            type=["xlsx", "xls"],
            key="sb_excel_uploader"
        )
        if uploaded_excel is not None:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel:
                    tmp_excel.write(uploaded_excel.getvalue())
                    tmp_excel_path = tmp_excel.name

                df, columns = ExcelParser.load_dataframe(tmp_excel_path)
                st.session_state.excel_data = df
                st.session_state.columns = columns

                # Update default column for existing text boxes if unassigned
                if columns and st.session_state.text_boxes:
                    default_col = columns[0]
                    for c in columns:
                        if 'name' in c.lower() or 'الاسم' in c:
                            default_col = c
                            break
                    for b in st.session_state.text_boxes:
                        if not b.get("column"):
                            b["column"] = default_col

                st.info(f"Loaded Excel: **{len(df)}** rows, **{len(columns)}** columns")
                os.remove(tmp_excel_path)
            except Exception as e:
                st.error(f"Excel error: {e}")

        st.markdown("---")

        # 2 & 3. Multiple Text Boxes & Styling Section
        st.subheader("**2 & 3. ✍️ Text Boxes & Styling**")

        if st.button("➕ Add Another Text Box"):
            new_idx = len(st.session_state.text_boxes) + 1
            default_col = st.session_state.columns[0] if st.session_state.columns else ""
            st.session_state.text_boxes.append(
                create_default_text_box(
                    label=f"Text Box #{new_idx}",
                    column=default_col,
                    y_start=min(90, 42 + (new_idx - 1) * 15),
                    y_end=min(95, 58 + (new_idx - 1) * 15)
                )
            )

        boxes_to_remove = []
        for i, box in enumerate(st.session_state.text_boxes):
            with st.expander(f"📌 Box #{i+1}: {box.get('label', 'Text Box')}", expanded=(i == 0)):
                box["label"] = st.text_input(f"Box #{i+1} Label", value=box.get("label", f"Field #{i+1}"), key=f"label_{i}")
                
                box["source_type"] = st.radio(
                    "Data Source:",
                    ["Excel Column", "Fixed Text"],
                    index=0 if box.get("source_type") == "Excel Column" else 1,
                    key=f"source_type_{i}"
                )

                if box["source_type"] == "Excel Column":
                    cols = st.session_state.columns
                    if cols:
                        current_col = box.get("column")
                        selected_col_idx = cols.index(current_col) if current_col in cols else 0
                        box["column"] = st.selectbox("Select Excel Column:", cols, index=selected_col_idx, key=f"col_{i}")
                    else:
                        st.warning("Upload an Excel file to pick a column.")
                        box["column"] = ""
                else:
                    box["fixed_text"] = st.text_input("Fixed Text Content:", value=box.get("fixed_text", ""), key=f"fixed_{i}")

                st.write("**Box Positioning:**")
                st.caption("🖱️ *Positioned directly by drawing with mouse/hand on the canvas.*")
                st.markdown(
                    f"<div style='background: #f1f3f5; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 8px;'>"
                    f"<b>X:</b> {box['x_start_pct']}% &rarr; {box['x_end_pct']}% &nbsp;|&nbsp; "
                    f"<b>Y:</b> {box['y_start_pct']}% &rarr; {box['y_end_pct']}%"
                    f"</div>",
                    unsafe_allow_html=True
                )
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    if st.button("Center", key=f"btn_center_{i}"):
                        box["x_start_pct"], box["x_end_pct"] = 15, 85
                        st.session_state["canvas_version"] = st.session_state.get("canvas_version", 0) + 1
                        st.rerun()
                with p_c2:
                    if st.button("Top / Code", key=f"btn_top_{i}"):
                        box["x_start_pct"], box["x_end_pct"] = 60, 95
                        box["y_start_pct"], box["y_end_pct"] = 10, 25
                        st.session_state["canvas_version"] = st.session_state.get("canvas_version", 0) + 1
                        st.rerun()

                st.write("**Styling:**")
                st_c1, st_c2 = st.columns(2)
                with st_c1:
                    font_opts = ["Arial", "Calibri", "Helvetica", "Times-Roman", "Courier"]
                    curr_font = box.get("font", "Arial")
                    box["font"] = st.selectbox("Font:", font_opts, index=font_opts.index(curr_font) if curr_font in font_opts else 0, key=f"font_{i}")
                    box["size"] = st.slider("Font Size (pt):", 10, 180, box.get("size", 60), key=f"size_{i}")
                    align_opts = ["center", "left", "right"]
                    curr_align = box.get("align", "center")
                    box["align"] = st.selectbox("Align:", align_opts, index=align_opts.index(curr_align) if curr_align in align_opts else 0, key=f"align_{i}")

                with st_c2:
                    box["color"] = st.color_picker("Color:", box.get("color", "#000000"), key=f"color_{i}")
                    box["bold"] = st.checkbox("Bold", value=box.get("bold", True), key=f"bold_{i}")
                    box["italic"] = st.checkbox("Italic", value=box.get("italic", False), key=f"italic_{i}")

                if len(st.session_state.text_boxes) > 1:
                    if st.button(f"🗑️ Delete Box #{i+1}", key=f"del_{i}"):
                        boxes_to_remove.append(i)

        for i in reversed(boxes_to_remove):
            st.session_state.text_boxes.pop(i)
            st.rerun()

    # --- MAIN CONTENT AREA ---
    st.title('✨ :shimmer[:red[Certificates Generator]] ✨', 
                text_alignment='center')

    col_preview, col_export = st.columns([0.72, 0.28], gap="large")

    # Left: Unified Live Visual Preview & Interactive Direct Box Editor (Streamlit Fragment)
    with col_preview:
        preview_and_box_editor_fragment()

    # Right: Output Folder & Export Settings (Streamlit Fragment)
    with col_export:
        output_settings_fragment()


if __name__ == "__main__":
    main()
