"""Fast Standalone HTML5 Canvas Visualizer Generator for Code-Maps."""

import json
from pathlib import Path
from typing import Dict, Any


def generate_map_html(graph_data: Dict[str, Any], output_path: Path) -> None:
    """Generate lightweight, high-performance HTML5 Canvas Visualizer."""
    # Top modules and symbols (hierarchical structure)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    # Cap visualization to top 350 key structural nodes to prevent browser crash
    if len(nodes) > 350:
        file_nodes = [n for n in nodes if n.get("type") == "file"][:100]
        class_nodes = [n for n in nodes if n.get("type") == "class"][:100]
        func_nodes = [n for n in nodes if n.get("type") == "func"][:150]
        nodes = file_nodes + class_nodes + func_nodes
        valid_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in valid_ids and e["target"] in valid_ids][:600]

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    total_nodes = len(nodes)
    total_edges = len(edges)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ Code-Maps Architecture Explorer</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        :root {{
            --bg: #09090b;
            --surface: #121215;
            --border: rgba(255, 255, 255, 0.08);
            --accent-file: #38bdf8;
            --accent-func: #34d399;
            --accent-class: #a855f7;
            --text: #f4f4f5;
            --dim: #71717a;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
        }}
        #sidebar {{
            width: 360px;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            z-index: 10;
        }}
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-file);
            border: 1px solid rgba(56, 189, 248, 0.25);
            margin-top: 8px;
        }}
        .panel {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            margin-top: 14px;
        }}
        .tag {{
            font-size: 0.65rem;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        .tag.file {{ background: rgba(56, 189, 248, 0.2); color: var(--accent-file); }}
        .tag.func {{ background: rgba(52, 211, 153, 0.2); color: var(--accent-func); }}
        .tag.class {{ background: rgba(168, 85, 247, 0.2); color: var(--accent-class); }}
        .conn-list {{
            list-style: none;
            margin-top: 10px;
            font-size: 0.8rem;
            max-height: 280px;
            overflow-y: auto;
        }}
        .conn-list li {{
            padding: 6px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            display: flex;
            justify-content: space-between;
            color: var(--dim);
        }}
        #viewport {{
            flex: 1;
            position: relative;
            background: radial-gradient(circle at center, #18181b 0%, #09090b 100%);
        }}
        canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <h1 style="font-size: 1.1rem; font-weight: 700; color: #f4f4f5;">⚡ Code-Maps Explorer</h1>
        <span class="badge">{total_nodes} Key Symbols • {total_edges} Links</span>
        
        <div class="panel">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="tag file" id="inspect-tag">FILE</span>
                <span style="font-size:0.75rem; color:var(--dim);" id="inspect-id">#1</span>
            </div>
            <h2 style="font-size: 1.05rem; margin-top: 6px; color: #fff;" id="inspect-title">-</h2>
            <p style="font-size: 0.75rem; color: var(--dim); margin-top: 4px;" id="inspect-desc">Click any balloon sphere to inspect relations</p>
        </div>

        <div class="panel" style="flex: 1; display: flex; flex-direction: column;">
            <span style="font-size: 0.75rem; color: var(--dim); font-weight: 700; text-transform: uppercase;">Direct AST Connections</span>
            <ul class="conn-list" id="inspect-links"></ul>
        </div>
    </div>
    <div id="viewport">
        <canvas id="graphCanvas"></canvas>
    </div>

    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        const canvas = document.getElementById('graphCanvas');
        const ctx = canvas.getContext('2d');

        let width, height;
        function resize() {{
            width = canvas.width = canvas.parentElement.clientWidth;
            height = canvas.height = canvas.parentElement.clientHeight;
        }}
        window.addEventListener('resize', resize);
        resize();

        // Initialize positions in circular layout
        nodes.forEach((n, idx) => {{
            const angle = (idx / nodes.length) * Math.PI * 2;
            const radius = 150 + Math.random() * (Math.min(width, height) * 0.35);
            n.x = width / 2 + Math.cos(angle) * radius;
            n.y = height / 2 + Math.sin(angle) * radius;
            n.vx = (Math.random() - 0.5) * 0.5;
            n.vy = (Math.random() - 0.5) * 0.5;
            n.r = n.type === 'file' ? 24 : (n.type === 'class' ? 18 : 14);
            n.color = n.type === 'file' ? '#38bdf8' : (n.type === 'class' ? '#a855f7' : '#34d399');
            n.bg = n.type === 'file' ? '#0369a1' : (n.type === 'class' ? '#6d28d9' : '#047857');
        }});

        const nodeMap = new Map();
        nodes.forEach(n => nodeMap.set(n.id, n));

        let selectedNode = nodes[0] || null;
        let hoveredNode = null;
        let dragNode = null;
        let isDragging = false;
        let panX = 0, panY = 0, scale = 1;

        function drawBalloon(ctx, n, isTarget, isConnected, isDimmed) {{
            ctx.save();
            const r = n.r;
            
            // Sphere radial gradient for 3D Balloon effect
            const grad = ctx.createRadialGradient(n.x - r*0.3, n.y - r*0.3, r*0.1, n.x, n.y, r);
            if (isDimmed) {{
                grad.addColorStop(0, 'rgba(255,255,255,0.05)');
                grad.addColorStop(1, '#18181b');
                ctx.strokeStyle = 'rgba(255,255,255,0.05)';
            }} else if (isTarget) {{
                grad.addColorStop(0, '#ffffff');
                grad.addColorStop(0.3, n.color);
                grad.addColorStop(1, '#09090b');
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
            }} else {{
                grad.addColorStop(0, 'rgba(255,255,255,0.85)');
                grad.addColorStop(0.25, n.bg);
                grad.addColorStop(1, '#09090b');
                ctx.strokeStyle = n.color;
                ctx.lineWidth = 1.5;
            }}

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            // Specular reflection highlight
            if (!isDimmed) {{
                ctx.fillStyle = 'rgba(255,255,255,0.35)';
                ctx.beginPath();
                ctx.ellipse(n.x - r*0.25, n.y - r*0.35, r*0.35, r*0.18, -0.3, 0, Math.PI * 2);
                ctx.fill();
            }}

            // Label text
            ctx.fillStyle = isDimmed ? '#3f3f46' : '#ffffff';
            ctx.font = `${{n.type === 'file' ? '10px' : '9px'}} -apple-system, sans-serif`;
            ctx.textAlign = 'center';
            const shortName = n.name.length > 12 ? n.name.substring(0, 10) + '..' : n.name;
            ctx.fillText(shortName, n.x, n.y + r + 12);
            ctx.restore();
        }}

        function render() {{
            ctx.clearRect(0, 0, width, height);

            // Simulation step
            nodes.forEach(n => {{
                n.x += n.vx;
                n.y += n.vy;
                if (n.x < 50 || n.x > width - 50) n.vx *= -1;
                if (n.y < 50 || n.y > height - 50) n.vy *= -1;
            }});

            const connectedIds = new Set();
            if (selectedNode) {{
                connectedIds.add(selectedNode.id);
                edges.forEach(e => {{
                    if (e.source === selectedNode.id) connectedIds.add(e.target);
                    if (e.target === selectedNode.id) connectedIds.add(e.source);
                }});
            }}

            // Draw Edges
            edges.forEach(e => {{
                const s = nodeMap.get(e.source);
                const t = nodeMap.get(e.target);
                if (!s || !t) return;

                const isConn = selectedNode && (connectedIds.has(s.id) && connectedIds.has(t.id));
                ctx.beginPath();
                ctx.moveTo(s.x, s.y);
                ctx.lineTo(t.x, t.y);
                ctx.strokeStyle = isConn ? 'rgba(56, 189, 248, 0.85)' : 'rgba(255, 255, 255, 0.05)';
                ctx.lineWidth = isConn ? 2 : 0.8;
                ctx.stroke();
            }});

            // Draw Nodes
            nodes.forEach(n => {{
                const isTarget = selectedNode && selectedNode.id === n.id;
                const isConn = connectedIds.has(n.id);
                const isDim = selectedNode && !isConn;
                drawBalloon(ctx, n, isTarget, isConn, isDim);
            }});

            requestAnimationFrame(render);
        }}
        render();

        function updateInspector(node) {{
            if (!node) return;
            document.getElementById('inspect-title').innerText = node.name;
            document.getElementById('inspect-id').innerText = node.type.toUpperCase();
            document.getElementById('inspect-desc').innerText = node.desc || node.full_name;
            const tag = document.getElementById('inspect-tag');
            tag.innerText = node.type.toUpperCase();
            tag.className = 'tag ' + node.type;

            const activeLinks = edges.filter(e => e.source === node.id || e.target === node.id);
            const list = document.getElementById('inspect-links');
            list.innerHTML = '';
            activeLinks.forEach(e => {{
                const isOut = e.source === node.id;
                const peerId = isOut ? e.target : e.source;
                const peer = nodeMap.get(peerId);
                const li = document.createElement('li');
                li.innerHTML = `<span>${{peer ? peer.name : 'external'}}</span> <span style="color:#38bdf8;">${{isOut ? '→ ' + e.label : '← ' + e.label}}</span>`;
                list.appendChild(li);
            }});
        }}

        canvas.addEventListener('click', e => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let clicked = null;
            nodes.forEach(n => {{
                const dist = Math.hypot(n.x - x, n.y - y);
                if (dist <= n.r) clicked = n;
            }});

            if (clicked) {{
                selectedNode = clicked;
                updateInspector(clicked);
            }} else {{
                selectedNode = null;
            }}
        }});

        if (selectedNode) updateInspector(selectedNode);
    </script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding='utf-8')
