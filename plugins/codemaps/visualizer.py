"""Full Vis.js Network Interactive Visualizer Generator for Code-Maps."""

import json
from pathlib import Path
from typing import Dict, Any


def generate_map_html(graph_data: Dict[str, Any], output_path: Path) -> None:
    """Generate high-definition Vis.js Sphere Balloon graph with full zoom, pan, and dragging."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Structural selection: Focus on key modules, classes, and top entry functions
    if len(nodes) > 150:
        file_nodes = [n for n in nodes if n.get("type") == "file"][:40]
        class_nodes = [n for n in nodes if n.get("type") == "class"][:40]
        func_nodes = [n for n in nodes if n.get("type") == "func"][:70]
        nodes = file_nodes + class_nodes + func_nodes
        valid_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e.get("source") in valid_ids and e.get("target") in valid_ids][:250]

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    total_nodes = len(nodes)
    total_edges = len(edges)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ Code-Maps — Floating Sphere Balloon Architecture</title>
    <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        :root {{
            --bg-color: #050811;
            --surface-color: #0b1120;
            --surface-border: rgba(255, 255, 255, 0.08);
            --accent-file: #38bdf8;
            --accent-func: #34d399;
            --accent-class: #a855f7;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-main);
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
        }}

        #sidebar {{
            width: 380px;
            background: var(--surface-color);
            border-right: 1px solid var(--surface-border);
            display: flex;
            flex-direction: column;
            padding: 24px;
            z-index: 10;
            box-shadow: 12px 0 32px rgba(0, 0, 0, 0.6);
        }}

        .brand-header {{
            padding-bottom: 16px;
            border-bottom: 1px solid var(--surface-border);
            margin-bottom: 20px;
        }}

        .stats-badge {{
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
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
        }}

        .tag {{
            font-size: 0.65rem;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .tag.file {{ background: rgba(56, 189, 248, 0.2); color: var(--accent-file); border: 1px solid rgba(56, 189, 248, 0.4); }}
        .tag.func {{ background: rgba(52, 211, 153, 0.2); color: var(--accent-func); border: 1px solid rgba(52, 211, 153, 0.4); }}
        .tag.class {{ background: rgba(168, 85, 247, 0.2); color: var(--accent-class); border: 1px solid rgba(168, 85, 247, 0.4); }}

        .conn-list {{
            list-style: none;
            margin-top: 12px;
            font-size: 0.85rem;
            max-height: 320px;
            overflow-y: auto;
        }}
        .conn-list li {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-dim);
        }}

        #network-container {{
            flex: 1;
            height: 100%;
            background: radial-gradient(circle at center, #0f172a 0%, #02040a 100%);
        }}

        .hud-legend {{
            position: absolute;
            top: 24px;
            left: 404px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid var(--surface-border);
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 0.8rem;
            display: flex;
            gap: 20px;
            pointer-events: none;
            z-index: 5;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; font-weight: 500; }}
        .legend-ball {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            display: inline-block;
            box-shadow: inset -2px -2px 4px rgba(0,0,0,0.5), inset 2px 2px 4px rgba(255,255,255,0.6);
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="brand-header">
            <h1 style="font-size: 1.15rem; font-weight: 700; color: #38bdf8;">🫧 Code-Maps Balloon Graph</h1>
            <span class="stats-badge" id="stats-badge">{total_nodes} Balloons • {total_edges} Strands</span>
        </div>

        <div class="panel">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="tag file" id="inspect-tag">FILE</span>
                <span style="font-size:0.75rem; color:var(--text-dim);" id="inspect-id">#1</span>
            </div>
            <h2 style="font-size: 1.15rem; margin-top: 8px; color: #fff; font-weight: 700;" id="inspect-title">-</h2>
            <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 6px; line-height: 1.5;" id="inspect-desc">Select a balloon to inspect connections</p>
        </div>

        <div class="panel" style="flex: 1; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.75rem; color: var(--text-dim); font-weight: 700; text-transform: uppercase;">Connected Balloons</span>
                <span style="font-size: 0.7rem; color: #38bdf8;" id="inspect-count">0 links</span>
            </div>
            <ul class="conn-list" id="inspect-links"></ul>
        </div>
    </div>

    <div class="hud-legend">
        <div class="legend-item"><span class="legend-ball" style="background:#0284c7;"></span> File Module Balloon</div>
        <div class="legend-item"><span class="legend-ball" style="background:#7c3aed;"></span> Class Balloon</div>
        <div class="legend-item"><span class="legend-ball" style="background:#059669;"></span> Function Balloon</div>
    </div>

    <div id="network-container"></div>

    <script>
        function createBalloonSVG(label, type, state = 'normal') {{
            let baseColor, specularColor, strokeColor, textColor;

            if (state === 'dim') {{
                baseColor = type === 'file' ? '#081726' : (type === 'class' ? '#140c24' : '#071a13');
                specularColor = 'rgba(255, 255, 255, 0.05)';
                strokeColor = 'rgba(255, 255, 255, 0.05)';
                textColor = '#334155';
            }} else if (state === 'active') {{
                baseColor = type === 'file' ? '#0284c7' : (type === 'class' ? '#7c3aed' : '#059669');
                specularColor = '#ffffff';
                strokeColor = '#ffffff';
                textColor = '#ffffff';
            }} else {{
                baseColor = type === 'file' ? '#0369a1' : (type === 'class' ? '#6d28d9' : '#047857');
                specularColor = 'rgba(255, 255, 255, 0.85)';
                strokeColor = type === 'file' ? '#38bdf8' : (type === 'class' ? '#a855f7' : '#34d399');
                textColor = '#f8fafc';
            }}

            const size = type === 'file' ? 140 : (type === 'class' ? 110 : 90);
            const r = size / 2 - 4;
            const cx = size / 2;
            const cy = size / 2;
            const fontSize = type === 'file' ? 13 : (type === 'class' ? 11 : 10);

            let displayLabel = label;
            if (displayLabel.length > 14) {{
                displayLabel = displayLabel.substring(0, 12) + '..';
            }}

            const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="${{size}}" height="${{size}}" viewBox="0 0 ${{size}} ${{size}}">
                <defs>
                    <radialGradient id="sphereGrad_${{type}}_${{state}}" cx="35%" cy="30%" r="70%">
                        <stop offset="0%" stop-color="${{specularColor}}" stop-opacity="${{state === 'dim' ? '0.2' : '0.9'}}"/>
                        <stop offset="25%" stop-color="${{baseColor}}" stop-opacity="0.95"/>
                        <stop offset="85%" stop-color="#02040a" stop-opacity="0.95"/>
                    </radialGradient>
                    <filter id="glow_${{type}}" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="${{strokeColor}}" flood-opacity="${{state === 'dim' ? '0' : '0.4'}}"/>
                    </filter>
                </defs>
                <circle cx="${{cx}}" cy="${{cy}}" r="${{r}}" fill="url(#sphereGrad_${{type}}_${{state}})" stroke="${{strokeColor}}" stroke-width="${{state === 'active' ? '3' : '1.5'}}" filter="url(#glow_${{type}})"/>
                <ellipse cx="${{cx - r*0.25}}" cy="${{cy - r*0.35}}" rx="${{r*0.35}}" ry="${{r*0.18}}" fill="#ffffff" opacity="${{state === 'dim' ? '0.05' : '0.35'}}" transform="rotate(-20 ${{cx - r*0.25}} ${{cy - r*0.35}})"/>
                <text x="${{cx}}" y="${{cy + 4}}" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="${{fontSize}}px" font-weight="700" fill="${{textColor}}" letter-spacing="-0.02em">
                    ${{displayLabel}}
                </text>
            </svg>`;

            return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
        }}

        const rawNodes = {nodes_json};
        const rawEdges = {edges_json};

        const nodesList = rawNodes.map(n => ({{
            id: n.id,
            rawLabel: n.name,
            group: n.type,
            shape: 'image',
            image: createBalloonSVG(n.name, n.type, 'normal'),
            desc: n.desc || n.full_name
        }}));

        const edgesList = rawEdges.map((e, idx) => ({{
            id: 'edge_' + idx,
            from: e.source,
            to: e.target,
            label: e.label || '',
            color: {{ color: 'rgba(255, 255, 255, 0.15)' }},
            width: 1
        }}));

        const nodesDataSet = new vis.DataSet(nodesList);
        const edgesDataSet = new vis.DataSet(edgesList);
        const container = document.getElementById('network-container');
        const data = {{ nodes: nodesDataSet, edges: edgesDataSet }};
        const options = {{
            physics: {{
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {{
                    gravitationalConstant: -100,
                    centralGravity: 0.008,
                    springLength: 110,
                    springConstant: 0.05,
                    damping: 0.35
                }},
                maxVelocity: 35,
                minVelocity: 0,
                stabilization: false,
                timestep: 0.5
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                hideEdgesOnDrag: false,
                zoomView: true,
                dragView: true,
                dragNodes: true
            }}
        }};

        const network = new vis.Network(container, data, options);

        setInterval(() => {{
            network.startSimulation();
        }}, 1500);

        function applyFocusAndDim(selectedId) {{
            if (!selectedId) {{
                nodesDataSet.update(rawNodes.map(n => ({{
                    id: n.id,
                    image: createBalloonSVG(n.name, n.type, 'normal')
                }})));
                edgesDataSet.update(edgesList.map(e => ({{
                    id: e.id,
                    color: {{ color: 'rgba(255, 255, 255, 0.15)' }},
                    width: 1
                }})));
                network.startSimulation();
                return;
            }}

            const connectedNodeIds = new Set([selectedId]);
            const connectedEdgeIds = new Set();

            edgesDataSet.forEach(e => {{
                if (e.from === selectedId) {{
                    connectedNodeIds.add(e.to);
                    connectedEdgeIds.add(e.id);
                }} else if (e.to === selectedId) {{
                    connectedNodeIds.add(e.from);
                    connectedEdgeIds.add(e.id);
                }}
            }});

            nodesDataSet.update(rawNodes.map(n => ({{
                id: n.id,
                image: createBalloonSVG(n.name, n.type, n.id === selectedId ? 'active' : (connectedNodeIds.has(n.id) ? 'normal' : 'dim'))
            }})));

            edgesDataSet.update(edgesList.map(e => ({{
                id: e.id,
                color: {{ color: connectedEdgeIds.has(e.id) ? 'rgba(56, 189, 248, 0.9)' : 'rgba(255, 255, 255, 0.02)' }},
                width: connectedEdgeIds.has(e.id) ? 2.5 : 0.5
            }})));

            network.startSimulation();
        }}

        function updateInspector(nodeId) {{
            const node = rawNodes.find(n => n.id === nodeId);
            if (!node) return;

            document.getElementById('inspect-title').innerText = node.name;
            document.getElementById('inspect-id').innerText = node.id;
            document.getElementById('inspect-desc').innerText = node.desc || node.full_name;
            const tag = document.getElementById('inspect-tag');
            tag.innerText = (node.type || 'node').toUpperCase();
            tag.className = 'tag ' + node.type;

            const activeLinks = rawEdges.filter(e => e.source === node.id || e.target === node.id);
            document.getElementById('inspect-count').innerText = `${{activeLinks.length}} connections`;

            const list = document.getElementById('inspect-links');
            list.innerHTML = '';
            activeLinks.forEach(e => {{
                const isOut = e.source === node.id;
                const peerId = isOut ? e.target : e.source;
                const peer = rawNodes.find(n => n.id === peerId);
                const li = document.createElement('li');
                li.innerHTML = `<span>${{peer ? peer.name : 'external'}}</span> <span style="color:#38bdf8; font-weight:600;">${{isOut ? '→ ' + e.label : '← ' + e.label}}</span>`;
                list.appendChild(li);
            }});
        }}

        network.on('selectNode', function (params) {{
            if (params.nodes.length > 0) {{
                const selId = params.nodes[0];
                updateInspector(selId);
                applyFocusAndDim(selId);
            }}
        }});

        network.on('deselectNode', function () {{
            applyFocusAndDim(null);
        }});

        if (rawNodes.length > 0) updateInspector(rawNodes[0].id);
    </script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding='utf-8')
