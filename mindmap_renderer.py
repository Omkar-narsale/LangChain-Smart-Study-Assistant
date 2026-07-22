"""
mindmap_renderer.py — Renders the interactive Markdown-based Mind Map using Markmap.js.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from mindmap_generator import generate_mindmap

# HTML template for the Markmap renderer.
_MARKMAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Mind Map</title>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.16.0"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.16.0"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            background-color: #0F172A; /* Tailwind slate-900 */
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100vh;
            color: #F8FAFC;
        }
        #toolbar {
            display: flex;
            gap: 10px;
            padding: 12px 20px;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            z-index: 100;
        }
        .toolbar-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .search-container {
            position: relative;
            display: flex;
            align-items: center;
        }
        .search-input {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #F8FAFC;
            padding: 6px 12px;
            padding-right: 30px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
            transition: all 0.2s;
            min-width: 200px;
        }
        .search-input:focus {
            border-color: #6366F1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
            background: rgba(255, 255, 255, 0.1);
        }
        .search-clear {
            position: absolute;
            right: 8px;
            cursor: pointer;
            color: #94A3B8;
            font-size: 14px;
            display: none;
            user-select: none;
        }
        button {
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #C7D2FE;
            padding: 7px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            user-select: none;
        }
        button:hover {
            background: rgba(99, 102, 241, 0.3);
            color: #FFFFFF;
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-1px);
        }
        button:active {
            transform: translateY(0);
        }
        #container {
            flex: 1;
            position: relative;
            overflow: hidden;
            width: 100%;
            height: 100%;
        }
        svg#mindmap-svg {
            width: 100%;
            height: 100%;
            background-color: #0F172A;
        }
        /* Custom Markmap node styling for dark mode premium aesthetic */
        .markmap-node {
            cursor: pointer;
        }
        .markmap-foreign-object {
            padding: 4px 8px;
            transition: background-color 0.3s, color 0.3s;
            font-size: 13px;
            color: #E2E8F0;
        }
        .markmap-foreign-object strong,
        .markmap-foreign-object h1,
        .markmap-foreign-object h2,
        .markmap-foreign-object h3 {
            color: #FFFFFF;
            margin: 0;
        }
        .markmap-node-circle {
            fill: #6366F1 !important;
            stroke: #818CF8 !important;
            stroke-width: 2px !important;
            transition: r 0.2s, fill 0.2s;
        }
        .markmap-node:hover .markmap-node-circle {
            r: 8px !important;
            fill: #818CF8 !important;
        }
        .markmap-link {
            fill: none;
            stroke-width: 2.5px !important;
            transition: stroke 0.3s;
        }
        /* Style nodes search highlight */
        .highlighted {
            background-color: rgba(234, 179, 8, 0.3) !important;
            border: 1px solid #EAB308 !important;
            border-radius: 6px !important;
            color: #FFFFFF !important;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <div class="toolbar-group">
            <div class="search-container">
                <input type="text" id="search-input" class="search-input" placeholder="Search nodes...">
                <span id="search-clear" class="search-clear">&times;</span>
            </div>
            <button id="btn-fit">🎯 Fit Screen</button>
            <button id="btn-fullscreen">📺 Fullscreen</button>
        </div>
        <div class="toolbar-group">
            <button id="btn-dl-svg">⬇ SVG</button>
            <button id="btn-dl-png">⬇ PNG (High-Res)</button>
        </div>
    </div>
    <div id="container">
        <svg id="mindmap-svg"></svg>
    </div>

    <script>
        const markdownCode = `{mindmap_markdown_escaped}`;
        
        // Parse markdown outline using markmap-lib
        const { Transformer } = window.markmap;
        const transformer = new Transformer();
        const { root: rootData } = transformer.transform(markdownCode);

        // Render Markmap
        const { Markmap } = window.markmap;
        const mm = Markmap.create('#mindmap-svg', {
            autoFit: true,
            duration: 300,
            style: (id) => `
                .markmap-link { stroke: #334155; }
            `
        }, rootData);

        // Track fullscreen state
        const btnFullscreen = document.getElementById('btn-fullscreen');
        btnFullscreen.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().then(() => {
                    btnFullscreen.textContent = "Exit Fullscreen";
                }).catch(err => {
                    alert(`Error enabling fullscreen: ${err.message}`);
                });
            } else {
                document.exitFullscreen().then(() => {
                    btnFullscreen.textContent = "📺 Fullscreen";
                });
            }
        });

        // Auto-fit to screen
        document.getElementById('btn-fit').addEventListener('click', () => {
            mm.fit();
        });

        // Search nodes function
        const searchInput = document.getElementById('search-input');
        const searchClear = document.getElementById('search-clear');

        function doSearch() {
            const query = searchInput.value.trim().toLowerCase();
            
            // Toggle clear button
            searchClear.style.display = query ? 'block' : 'none';

            // Clear previous highlights
            document.querySelectorAll('.markmap-foreign-object').forEach(el => {
                el.classList.remove('highlighted');
            });

            if (!query) return;

            let rootChanged = false;
            
            // Helper to recursively expand nodes that contain query (or have children containing query)
            function expandToMatches(node) {
                let matches = false;
                if (node.content && node.content.toLowerCase().includes(query)) {
                    matches = true;
                }
                let childMatch = false;
                if (node.children) {
                    node.children.forEach(c => {
                        if (expandToMatches(c)) {
                            childMatch = true;
                        }
                    });
                }
                if (matches || childMatch) {
                    if (node.payload && node.payload.fold) {
                        node.payload.fold = 0;
                        rootChanged = true;
                    }
                    return true;
                }
                return false;
            }

            expandToMatches(rootData);

            if (rootChanged) {
                mm.setData(rootData);
            }

            // Highlight matches in the DOM
            setTimeout(() => {
                document.querySelectorAll('.markmap-foreign-object').forEach(el => {
                    if (el.textContent.toLowerCase().includes(query)) {
                        el.classList.add('highlighted');
                    }
                });
            }, 60);
        }

        searchInput.addEventListener('input', doSearch);
        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            doSearch();
            searchInput.focus();
        });

        // SVG Export
        document.getElementById('btn-dl-svg').addEventListener('click', () => {
            const svgElement = document.getElementById('mindmap-svg');
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
        });

        // PNG High-Res Export
        document.getElementById('btn-dl-png').addEventListener('click', () => {
            const svgElement = document.getElementById('mindmap-svg');
            if (!svgElement) return;

            mm.fit();

            setTimeout(() => {
                const serializer = new XMLSerializer();
                const source = serializer.serializeToString(svgElement);
                const canvas = document.createElement("canvas");
                const ctx = canvas.getContext("2d");
                const img = new Image();

                img.onload = function() {
                    const scale = 3; // High-res
                    canvas.width = img.width * scale;
                    canvas.height = img.height * scale;
                    
                    // Dark theme background
                    ctx.fillStyle = '#0F172A';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    
                    ctx.scale(scale, scale);
                    ctx.drawImage(img, 0, 0);

                    const link = document.createElement("a");
                    link.download = "mindmap.png";
                    link.href = canvas.toDataURL("image/png");
                    link.click();
                };
                img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(source)));
            }, 200);
        });
    </script>
</body>
</html>
"""

def render_mindmap_tab() -> None:
    """Render the Mind Map tab and handle user interactions."""
    st.markdown("<h2 class='text-section'>🗺 Mind Map</h2>", unsafe_allow_html=True)
    
    # ── Check if a mind map exists in session state ───────────────────────────
    if not st.session_state.get("mindmap_markdown"):
        st.info("No Mind Map Generated.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_clicked = st.button("🗺 Generate Mind Map", type="primary", use_container_width=True)
            
        if generate_clicked:
            study_output = st.session_state.get("study_output")
            if not study_output or "summary" not in study_output:
                st.warning("⚠️ Generate Study Material first.")
                return
                
            with st.spinner("Generating Mind Map outline..."):
                try:
                    generate_mindmap()
                    st.success("Mind Map generated successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Mind Map generation failed: {exc}")
        return

    # ── A mind map exists, render it ──────────────────────────────────────────
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("🔄 Regenerate", key="btn_regen_mindmap", use_container_width=True):
            st.session_state.mindmap_markdown = None
            st.rerun()
            
    # Inject the HTML interactive block
    mindmap_markdown = st.session_state.mindmap_markdown
    # Escape backticks and backslashes for JS injection
    mindmap_markdown_escaped = mindmap_markdown.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n")
    
    html_content = _MARKMAP_HTML_TEMPLATE.replace(
        "{mindmap_markdown_escaped}", mindmap_markdown_escaped
    )
    
    st.markdown("<div class='glass-card' style='padding: 0;'>", unsafe_allow_html=True)
    components.html(html_content, height=750, scrolling=False)
    st.markdown("</div>", unsafe_allow_html=True)
