"""
mindmap_renderer.py — Renders the interactive Mermaid Mind Map.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from mindmap_generator import generate_mindmap

# HTML template for the Mermaid renderer.
# This uses mermaid.min.js for rendering and svg-pan-zoom for interactivity.
_MERMAID_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: transparent;
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100vh;
            color: #F8FAFC;
        }}
        #toolbar {{
            display: flex;
            gap: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            justify-content: center;
            flex-wrap: wrap;
        }}
        button {{
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.4);
            color: #C7D2FE;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        button:hover {{
            background: rgba(99, 102, 241, 0.4);
            color: #fff;
        }}
        #container {{
            flex: 1;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        /* Target the mermaid svg */
        svg {{
            width: 100% !important;
            height: 100% !important;
            max-width: none !important;
        }}
        .error-msg {{
            color: #ef4444;
            padding: 20px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 8px;
            margin: 20px;
            text-align: center;
        }}
        pre {{
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            overflow: auto;
            text-align: left;
            margin: 0 20px;
        }}
    </style>
</head>
<body>
    <div id="toolbar">
        <button id="btn-zoom-in">🔍 Zoom In</button>
        <button id="btn-zoom-out">🔍 Zoom Out</button>
        <button id="btn-fit">🎯 Fit to Screen</button>
        <button id="btn-dl-svg">⬇ Download SVG</button>
        <button id="btn-dl-png">⬇ Download PNG</button>
        <button id="btn-copy">📋 Copy Code</button>
    </div>
    <div id="container">
        <div class="mermaid" id="mermaid-graph">
{mermaid_code}
        </div>
    </div>

    <script>
        const mermaidCode = `{mermaid_code_escaped}`;
        let panZoomInstance = null;

        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            fontFamily: 'Inter, sans-serif'
        }});

        // After mermaid renders, initialize pan/zoom
        setTimeout(() => {{
            const svgElement = document.querySelector('#mermaid-graph svg');
            if (svgElement) {{
                // Initialize pan/zoom
                panZoomInstance = svgPanZoom(svgElement, {{
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: true,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 10
                }});
            }} else {{
                // Rendering failed, show fallback
                document.getElementById('container').innerHTML = 
                    '<div class="error-msg"><h3>Mermaid Rendering Failed</h3><p>Displaying source code fallback:</p></div>' + 
                    '<pre>' + mermaidCode.replace(/</g, "&lt;").replace(/>/g, "&gt;") + '</pre>';
            }}
        }}, 500);

        // Toolbar Actions
        document.getElementById('btn-zoom-in').addEventListener('click', () => {{
            if (panZoomInstance) panZoomInstance.zoomIn();
        }});
        
        document.getElementById('btn-zoom-out').addEventListener('click', () => {{
            if (panZoomInstance) panZoomInstance.zoomOut();
        }});
        
        document.getElementById('btn-fit').addEventListener('click', () => {{
            if (panZoomInstance) {{
                panZoomInstance.fit();
                panZoomInstance.center();
            }}
        }});

        document.getElementById('btn-copy').addEventListener('click', () => {{
            navigator.clipboard.writeText(mermaidCode).then(() => {{
                alert('Mermaid code copied to clipboard!');
            }});
        }});

        document.getElementById('btn-dl-svg').addEventListener('click', () => {{
            const svgElement = document.querySelector('#mermaid-graph svg');
            if (!svgElement) return;
            const serializer = new XMLSerializer();
            let source = serializer.serializeToString(svgElement);
            source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
            const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
            
            const link = document.createElement("a");
            link.href = url;
            link.download = "mindmap.svg";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }});

        document.getElementById('btn-dl-png').addEventListener('click', () => {{
            const svgElement = document.querySelector('#mermaid-graph svg');
            if (!svgElement) return;
            
            // Need to reset zoom before exporting to get crisp full image
            const oldZoom = panZoomInstance ? panZoomInstance.getZoom() : 1;
            const oldPan = panZoomInstance ? panZoomInstance.getPan() : {{x:0, y:0}};
            
            if (panZoomInstance) {{
                panZoomInstance.fit();
                panZoomInstance.center();
            }}

            const serializer = new XMLSerializer();
            const source = serializer.serializeToString(svgElement);
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            const img = new Image();
            
            img.onload = function() {{
                canvas.width = img.width * 2; // High-res
                canvas.height = img.height * 2;
                ctx.scale(2, 2);
                ctx.drawImage(img, 0, 0);
                
                const link = document.createElement("a");
                link.download = "mindmap.png";
                link.href = canvas.toDataURL("image/png");
                link.click();
                
                // Restore old zoom
                if (panZoomInstance) {{
                    panZoomInstance.zoom(oldZoom);
                    panZoomInstance.pan(oldPan);
                }}
            }};
            img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(source)));
        }});
    </script>
</body>
</html>
"""

def render_mindmap_tab() -> None:
    """Render the Mind Map tab and handle user interactions."""
    st.markdown("<h2 class='text-section'>🗺 Mind Map</h2>", unsafe_allow_html=True)
    
    # ── Check if a mind map exists in session state ───────────────────────────
    if not st.session_state.get("mermaid_code"):
        st.info("No Mind Map Generated.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_clicked = st.button("🗺 Generate Mind Map", type="primary", use_container_width=True)
            
        if generate_clicked:
            # Enforce that study material is already generated.
            study_output = st.session_state.get("study_output")
            if not study_output or "summary" not in study_output:
                st.warning("⚠️ Generate Study Material first.")
                return
                
            with st.spinner("Generating Mind Map using Groq API..."):
                try:
                    generate_mindmap()
                    st.success("Mind Map generated successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Mind Map generation failed: {exc}")
        return

    # ── A mind map exists, render it ──────────────────────────────────────────
    
    # Header actions (Regenerate button)
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("🔄 Regenerate", key="btn_regen_mindmap", use_container_width=True):
            st.session_state.mermaid_code = None
            st.session_state.mindmap_svg = None
            st.rerun()
            
    # Inject the HTML interactive block
    mermaid_code = st.session_state.mermaid_code
    # Escape backticks and backslashes for JS injection
    mermaid_code_escaped = mermaid_code.replace("\\", "\\\\").replace("`", "\\`")
    
    html_content = _MERMAID_HTML_TEMPLATE.format(
        mermaid_code=mermaid_code,
        mermaid_code_escaped=mermaid_code_escaped
    )
    
    # Render with a height of 600px
    st.markdown("<div class='glass-card' style='padding: 0;'>", unsafe_allow_html=True)
    components.html(html_content, height=650, scrolling=False)
    st.markdown("</div>", unsafe_allow_html=True)
