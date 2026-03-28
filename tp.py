import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import random

# ======================
# CUSTOMIZE
# ======================
HER_NAME = "Prachita (aka useless)"

# ======================
# HEART
# ======================
def heart(t, scale=1):
    x = scale * 16 * np.sin(t)**3
    y = scale * (
        13*np.cos(t)
        - 5*np.cos(2*t)
        - 2*np.cos(3*t)
        - np.cos(4*t)
    )
    return x, y

# ======================
# FLOWER
# ======================
def flower(theta, k=6, scale=2):
    r = scale * np.cos(k * theta)
    return r*np.cos(theta), r*np.sin(theta)

# ======================
# FIGURE
# ======================
fig = plt.figure(figsize=(8, 10))
ax = fig.add_axes([0, 0.22, 1, 0.78])
ax.set_xlim(-20, 20)
ax.set_ylim(-20, 25)
ax.axis("off")
ax.set_facecolor("#12001a")

# ======================
# TEXT
# ======================
title = ax.text(
    0, 12,
    f"Helloo {HER_NAME}, Will You Be My Valentine? 💖",
    ha="center",
    fontsize=26,
    color="pink",
    alpha=0
)

response = ax.text(
    0, -15,
    "",
    ha="center",
    fontsize=22,
    color="hotpink"
)

# ======================
# HEART
# ======================
t = np.linspace(0, 2*np.pi, 400)
heart_line, = ax.plot([], [], lw=3, color="crimson")

# ======================
# FLOWERS
# ======================
theta = np.linspace(0, 2*np.pi, 300)
flowers = []
flower_pos = [(-10, -5), (10, -5), (-8, 8), (8, 8)]
flowers_drawn = False

# ======================
# SPARKLES
# ======================
sx = np.random.uniform(-20, 20, 80)
sy = np.random.uniform(-10, 25, 80)
sparkles = ax.scatter(sx, sy, s=8, color="white", alpha=0.3)

# ======================
# ROSE PETALS
# ======================
px = np.random.uniform(-20, 20, 30)
py = np.random.uniform(20, 30, 30)
ps = np.random.uniform(0.05, 0.15, 30)
petals = ax.scatter(px, py, s=30, color="deeppink", alpha=0.8)

# ======================
# CONFETTI
# ======================
cx = np.random.uniform(-20, 20, 60)
cy = np.random.uniform(20, 30, 60)
cs = np.random.uniform(0.1, 0.3, 60)
confetti = ax.scatter(cx, cy, s=20, color="hotpink", alpha=0)

celebrate = False

# ======================
# BUTTONS
# ======================
ax_yes = fig.add_axes([0.25, 0.08, 0.2, 0.07])
ax_no  = fig.add_axes([0.55, 0.08, 0.2, 0.07])

btn_yes = Button(ax_yes, "YES 💖", color="pink", hovercolor="hotpink")
btn_no  = Button(ax_no,  "NO 🙃", color="lightgray", hovercolor="gray")

# ======================
# BUTTON CALLBACKS
# ======================
def yes_clicked(event):
    global celebrate
    response.set_text("YAYYYY!!! 💕🎉 I LOVE YOU 💖")
    celebrate = True
    confetti.set_alpha(1)

btn_yes.on_clicked(yes_clicked)

# Move NO button ONLY if cursor is over it
def on_mouse_move(event):
    if event.inaxes == ax_no:
        pos = ax_no.get_position()
        ax_no.set_position([
            random.uniform(0.1, 0.7),
            pos.y0,
            pos.width,
            pos.height
        ])
        fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)

# ======================
# ANIMATION
# ======================
def animate(frame):
    global py, cy, flowers_drawn

    # Beating heart
    scale = 1 + 0.06*np.sin(frame / 8)
    hx, hy = heart(t, scale)
    heart_line.set_data(hx, hy)

    # Fade-in title
    if frame < 60:
        title.set_alpha(frame / 60)

    # Draw flowers once
    if frame > 80 and not flowers_drawn:
        for fx, fy in flower_pos:
            x, y = flower(theta)
            f, = ax.plot(x + fx, y + fy, color="hotpink", lw=2)
            flowers.append(f)
        flowers_drawn = True

    # Sparkles
    sparkles.set_alpha(abs(np.sin(frame / 15)))

    # Petals fall
    py -= ps
    py[py < -20] = np.random.uniform(20, 30)
    petals.set_offsets(np.c_[px, py])

    # Confetti if YES
    if celebrate:
        cy -= cs
        cy[cy < -20] = np.random.uniform(20, 30)
        confetti.set_offsets(np.c_[cx, cy])

# IMPORTANT: blit=False (THIS FIXES EVERYTHING)
ani = FuncAnimation(fig, animate, interval=30, blit=False)
plt.show()
