"""
Dependency-free diagram generator for deep-engineering-documentation.

Use this when no mermaid renderer / cairosvg / network access is available.
Produces PNG files: one component diagram + one sequence diagram per entry point.

Usage pattern:
    1. Copy this file into your working script.
    2. Fill in COMPONENT_SPEC and SEQUENCES below for your system.
    3. Run: python3 gen_diagrams.py
    4. Diagrams land in OUT_DIR as component_diagram.png and seq_<name>.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = "./diagrams"


def draw_sequence(actors, messages, title, outfile, fig_width=15):
    """
    actors: list[str] — column labels, left to right
    messages: list[tuple(from_actor, to_actor, label, style)]
        style: "sync" (solid arrow) or "async" (dashed, e.g. goroutine/event publish)
    """
    n = len(actors)
    fig_height = 1.6 + 0.60 * len(messages)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, n + 1)
    ax.set_ylim(0, len(messages) + 2)
    ax.axis("off")

    x_positions = {actor: i + 1 for i, actor in enumerate(actors)}

    ax.text((n + 1) / 2, len(messages) + 1.6, title, ha="center", va="center",
            fontsize=14, fontweight="bold", color="#1a1a2e")

    box_y = len(messages) + 0.85
    for actor in actors:
        x = x_positions[actor]
        ax.add_patch(FancyBboxPatch((x - 0.46, box_y - 0.28), 0.92, 0.56,
                                     boxstyle="round,pad=0.02,rounding_size=0.06",
                                     linewidth=1.3, edgecolor="#2b4c7e",
                                     facecolor="#dce8f7"))
        ax.text(x, box_y, actor, ha="center", va="center", fontsize=8.6,
                fontweight="bold", color="#12233f")

    for actor in actors:
        x = x_positions[actor]
        ax.plot([x, x], [0.3, box_y - 0.28], linestyle=(0, (4, 3)),
                color="#8a94a6", linewidth=1.1, zorder=1)

    top_y = box_y - 0.53
    for i, (frm, to, label, style) in enumerate(messages):
        y = top_y - i * 0.60
        x1, x2 = x_positions[frm], x_positions[to]
        color = "#c0392b" if style == "async" else "#1a1a2e"
        arrow = FancyArrowPatch((x1, y), (x2, y),
                                 arrowstyle="-|>", mutation_scale=13,
                                 linewidth=1.3,
                                 linestyle="dashed" if style == "async" else "solid",
                                 color=color, zorder=2,
                                 shrinkA=2, shrinkB=2)
        ax.add_patch(arrow)
        mid = (x1 + x2) / 2
        ax.text(mid, y + 0.15, f"{i+1}. {label}", ha="center", va="bottom",
                fontsize=7.6, color="#1a1a2e",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                          edgecolor="none", alpha=0.85))

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/{outfile}", dpi=210, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved", outfile)


def draw_component_diagram(title, rows, edges, notes, outfile, figsize=(15, 10)):
    """
    rows: list of rows; each row is list[dict(x, y, w, h, text, fc)] — pre-laid-out boxes
          (simplest approach: lay out by hand in a grid, see example below)
    edges: list[tuple(x1, y1, x2, y2, style)] — style "sync" or "async"
    notes: list[str] — italic footer notes (e.g. "X is commented out, not running")
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#dce8f7", ec="#2b4c7e", fs=9.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                     linewidth=1.4, edgecolor=ec, facecolor=fc))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold", color="#12233f")

    def arrow(x1, y1, x2, y2, style="sync"):
        color = "#c0392b" if style == "async" else "#1a1a2e"
        a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                             linewidth=1.3, linestyle="dashed" if style == "async" else "solid",
                             color=color, shrinkA=3, shrinkB=3)
        ax.add_patch(a)

    ax.text(5, 9.7, title, ha="center", fontsize=15, fontweight="bold", color="#1a1a2e")

    for row in rows:
        for b in row:
            box(b["x"], b["y"], b["w"], b["h"], b["text"], fc=b.get("fc", "#dce8f7"), fs=b.get("fs", 9.5))
    for e in edges:
        arrow(*e[:4], style=e[4] if len(e) > 4 else "sync")

    y_note = 0.7
    for note in notes:
        ax.text(5, y_note, note, ha="center", fontsize=8.5, style="italic", color="#8a1f1f")
        y_note -= 0.35

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/{outfile}", dpi=210, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved", outfile)


# ============================================================
# EXAMPLE (delete/replace with your own system's shape)
# ============================================================
if __name__ == "__main__":
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    draw_sequence(
        actors=["Client", "Handler", "Service", "DB"],
        messages=[
            ("Client", "Handler", "Request", "sync"),
            ("Handler", "Service", "Delegate", "sync"),
            ("Service", "DB", "Query", "sync"),
            ("DB", "Service", "Rows", "sync"),
            ("Service", "Handler", "Result", "sync"),
            ("Handler", "Client", "Response", "sync"),
        ],
        title="Example Entry Point — Request Flow",
        outfile="seq_example.png",
    )

    draw_component_diagram(
        title="Example System — Component Diagram",
        rows=[
            [{"x": 0.5, "y": 8, "w": 2, "h": 0.8, "text": "Client", "fc": "#f7e7dc"}],
            [{"x": 0.5, "y": 6, "w": 2, "h": 0.8, "text": "Handler"}],
            [{"x": 0.5, "y": 4, "w": 2, "h": 0.8, "text": "DB", "fc": "#dcf7e3"}],
        ],
        edges=[(1.5, 8, 1.5, 6.8), (1.5, 6, 1.5, 4.8)],
        notes=["Replace this example with your own system's layout before use."],
        outfile="component_diagram.png",
    )
