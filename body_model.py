"""
Body Model Widget — 3D Human Body Visualization
Uses matplotlib 3D + custom geometry for an interactive body model
with disease-specific highlighting
"""

import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import matplotlib.cm as cm


def make_sphere(cx, cy, cz, rx, ry, rz, n=20):
    """Generate sphere mesh at given center with radii."""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = cx + rx * np.outer(np.cos(u), np.sin(v))
    y = cy + ry * np.outer(np.sin(u), np.sin(v))
    z = cz + rz * np.outer(np.ones(np.size(u)), np.cos(v))
    return x, y, z


def make_cylinder(cx, cy, cz_bottom, cz_top, rx, ry, n=20):
    """Generate cylinder mesh."""
    theta = np.linspace(0, 2 * np.pi, n)
    z = np.linspace(cz_bottom, cz_top, 2)
    theta_mesh, z_mesh = np.meshgrid(theta, z)
    x = cx + rx * np.cos(theta_mesh)
    y = cy + ry * np.sin(theta_mesh)
    return x, y, z_mesh


def make_ellipsoid(cx, cy, cz, rx, ry, rz, n=20):
    """Ellipsoid surface."""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = cx + rx * np.outer(np.cos(u), np.sin(v))
    y = cy + ry * np.outer(np.sin(u), np.sin(v))
    z = cz + rz * np.outer(np.ones(n), np.cos(v))
    return x, y, z


def make_tapered_torso(cx, cy, cz_bottom, cz_top, rx_base, ry_base, n=20):
    """Generate a contoured human-like torso with a chest swell and waist taper."""
    z = np.linspace(cz_bottom, cz_top, n)
    theta = np.linspace(0, 2 * np.pi, n)
    theta_mesh, z_mesh = np.meshgrid(theta, z)
    
    # Normalized height (0 at pelvis/bottom, 1 at neck/top)
    h = (z_mesh - cz_bottom) / (cz_top - cz_bottom)
    
    # Mathematical scaling factor to shape pelvis, narrow waist, swell chest, and taper shoulders
    mod = 0.95 - 1.6 * h + 4.8 * h**2 - 3.65 * h**3
    
    x = cx + rx_base * mod * np.cos(theta_mesh)
    y = cy + ry_base * mod * np.sin(theta_mesh)
    return x, y, z_mesh


def make_tapered_cylinder(cx, cy, cz_bottom, cz_top, r_bottom, r_top, n=20):
    """Generate a tapered cylinder for natural anatomical limbs."""
    theta = np.linspace(0, 2 * np.pi, n)
    z = np.linspace(cz_bottom, cz_top, n)
    theta_mesh, z_mesh = np.meshgrid(theta, z)
    
    # Taper radius linearly from bottom to top
    h = (z_mesh - cz_bottom) / (cz_top - cz_bottom)
    r = r_bottom + (r_top - r_bottom) * h
    
    x = cx + r * np.cos(theta_mesh)
    y = cy + r * np.sin(theta_mesh)
    return x, y, z_mesh


DISEASE_COLORS = {
    "Malaria": {
        "base": "#1a4060",
        "liver": "#c57552",
        "spleen": "#9c609c",
        "blood": "#b83b3b",
        "brain": "#bfa054",
        "kidneys": "#b3733b",
        "highlight": "#b83b3b",
        "skin": "#2a5080",
    },
    "Dengue Fever": {
        "base": "#1a3060",
        "blood": "#b83b3b",
        "liver": "#b85165",
        "skin": "#b86882",
        "heart": "#b34242",
        "kidneys": "#9b7fa8",
        "highlight": "#b83b3b",
        "brain": "#b86882",
    },
    "Chikungunya": {
        "base": "#2a3020",
        "joints": "#bfa054",
        "muscles": "#b3833b",
        "liver": "#b3733b",
        "skin": "#bfa068",
        "highlight": "#bfa054",
        "brain": "#4fa8b8",
        "blood": "#589e7d",
    },
}


class BodyModelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_disease = "Malaria"
        self.current_day = 0
        self.current_data = {}
        self.selected_organ = None
        self.elevation = 15
        self.azimuth = -60
        self.zoom = 1.0
        self.is_rotating = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(facecolor='#040c1a', figsize=(8, 8))
        self.figure.subplots_adjust(left=0.0, right=1.0, bottom=0.06, top=0.98)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: #040c1a;")
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111, projection='3d')
        self._style_axes()
        self._draw_body(0.0, {})
        self._apply_zoom()
        self.canvas.draw()

        # Mouse events
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

    def _style_axes(self):
        self.ax.set_facecolor('#040c1a')
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor('#0d2040')
        self.ax.yaxis.pane.set_edgecolor('#0d2040')
        self.ax.zaxis.pane.set_edgecolor('#0d2040')
        self.ax.grid(True, color='#0d2040', alpha=0.3, linewidth=0.5)
        self.ax.tick_params(colors='#1a4060', labelsize=6)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_zticks([])
        self.ax.view_init(elev=self.elevation, azim=self.azimuth)
        # Set box aspect ratio to match tall humanoid proportions
        self.ax.set_box_aspect((1, 1, 1.5))

    def set_disease(self, disease):
        self.current_disease = disease
        self.redraw()

    def set_view(self, view):
        views = {
            "Front View": (15, -90),
            "Side View": (15, 0),
            "Back View": (15, 90),
            "Top View": (90, -90),
            "3D Orbit": (25, -60),
        }
        elev, azim = views.get(view, (15, -60))
        self.elevation = elev
        self.azimuth = azim
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw()

    def control_action(self, action):
        if action == "rotate":
            self.azimuth = (self.azimuth + 15) % 360
            self.ax.view_init(elev=self.elevation, azim=self.azimuth)
        elif action == "zoom_in":
            self.zoom = min(5.0, self.zoom * 1.25)
            self._apply_zoom()
        elif action == "zoom_out":
            self.zoom = max(0.4, self.zoom / 1.25)
            self._apply_zoom()
        elif action == "reset":
            self.elevation = 15
            self.azimuth = -60
            self.zoom = 1.0
            self.ax.view_init(elev=self.elevation, azim=self.azimuth)
            self._apply_zoom()
        self.canvas.draw()

    def _apply_zoom(self):
        # Keep data limits constant so the humanoid body model and labels are never clipped
        self.ax.set_xlim(-1.7, 1.7)
        self.ax.set_ylim(-1.7, 1.7)
        self.ax.set_zlim(-1.5, 2.4)
        # Apply camera zoom using the zoom parameter in set_box_aspect (modern Matplotlib 3D approach)
        self.ax.set_box_aspect((1, 1, 1.5), zoom=self.zoom)

    def update_disease_visualization(self, day, data):
        self.current_day = day
        self.current_data = data
        self.redraw()

    def redraw(self):
        prog = self.current_data.get('progression', 0.0)
        self.ax.clear()
        self._style_axes()
        self._draw_body(prog, self.current_data)
        self._draw_labels(prog)
        self._apply_zoom()
        self.canvas.draw()

    def _draw_body(self, progression, data):
        colors = DISEASE_COLORS.get(self.current_disease, DISEASE_COLORS["Malaria"])
        p = progression
        n = 10  # mesh resolution (optimized from 18 to reduce polygon count and increase rendering speed)
        # Body skin is transparent when a disease is selected to show internal organs (increased visibility)
        def alpha(base_alpha):
            if self.selected_organ is not None:
                return base_alpha * 0.05
            return base_alpha * 0.20

        # ── HEAD ──
        head_color = colors.get("skin", "#3a6090")
        hx, hy, hz = make_ellipsoid(0, 0.02, 1.98, 0.22, 0.20, 0.26, n)
        self.ax.plot_surface(hx, hy, hz, color=head_color, alpha=alpha(0.85), shade=True, linewidth=0)

        # Eyes
        for ex in [-0.09, 0.09]:
            ex2, ey2, ez2 = make_sphere(ex, -0.18, 1.98, 0.035, 0.035, 0.035, 8)
            self.ax.plot_surface(ex2, ey2, ez2, color='#7ecbf5', alpha=alpha(0.9), linewidth=0)

        # ── NECK ──
        nx, ny, nz = make_tapered_cylinder(0, 0.01, 1.55, 1.76, 0.11, 0.08, n)
        self.ax.plot_surface(nx, ny, nz, color=head_color, alpha=alpha(0.8), shade=True, linewidth=0)

        # ── TORSO (humanoid tapered shape) ──
        torso_color = colors.get("skin", "#2a5080")
        tx, ty, tz = make_tapered_torso(0, 0, 0.13, 1.55, 0.40, 0.26, n)
        self.ax.plot_surface(tx, ty, tz, color=torso_color, alpha=alpha(0.75), shade=True, linewidth=0)

        # ── INTERNAL ORGANS (shown through semi-transparent torso) ──
        self._draw_organs(p, colors, data, n)

        # ── ARMS ──
        for side in [-1, 1]:
            x_off = side * 0.58
            # Upper arm (tapered)
            ax_, ay_, az_ = make_tapered_cylinder(x_off, 0, 0.45, 1.1, 0.12, 0.09, n)
            arm_col = colors.get("skin", "#2a5080")
            # Chikungunya: highlight joint areas
            if self.current_disease == "Chikungunya" and p > 0.1:
                arm_col = self._blend_color(arm_col, colors.get("joints", "#bfa054"), p * 0.5)
            self.ax.plot_surface(ax_, ay_, az_, color=arm_col, alpha=alpha(0.8), shade=True, linewidth=0)

            # Elbow joint
            ejx, ejy, ez_dummy = make_sphere(x_off, 0, 0.45, 0.12, 0.12, 0.12, 10)
            self.ax.plot_surface(ejx, ejy, ez_dummy, color=arm_col, alpha=alpha(0.8), linewidth=0)

            # Forearm (tapered)
            fax, fay, faz = make_tapered_cylinder(x_off * 1.05, 0, 0.05, 0.45, 0.06, 0.09, n)
            self.ax.plot_surface(fax, fay, faz, color=arm_col, alpha=alpha(0.8), shade=True, linewidth=0)

            # Hand
            hnd_x, hnd_y, hnd_z = make_sphere(x_off * 1.05, 0, 0.0, 0.08, 0.06, 0.07, 10)
            self.ax.plot_surface(hnd_x, hnd_y, hnd_z, color=arm_col, alpha=alpha(0.8), linewidth=0)

        # ── LEGS ──
        for side in [-1, 1]:
            x_off = side * 0.2
            leg_col = colors.get("skin", "#2a5080")
            if self.current_disease == "Chikungunya" and p > 0.1:
                leg_col = self._blend_color(leg_col, colors.get("muscles", "#ffab00"), p * 0.4)

            # Upper leg (tapered thigh)
            ux, uy, uz = make_tapered_cylinder(x_off, 0, -0.6, 0.08, 0.12, 0.16, n)
            self.ax.plot_surface(ux, uy, uz, color=leg_col, alpha=alpha(0.82), shade=True, linewidth=0)

            # Knee joint
            kjx, kjy, kjz = make_sphere(x_off, 0, -0.6, 0.14, 0.12, 0.12, 10)
            self.ax.plot_surface(kjx, kjy, kjz, color=leg_col, alpha=alpha(0.8), linewidth=0)

            # Lower leg (tapered calf)
            lx, ly, lz = make_tapered_cylinder(x_off, 0, -1.15, -0.6, 0.07, 0.11, n)
            self.ax.plot_surface(lx, ly, lz, color=leg_col, alpha=alpha(0.82), shade=True, linewidth=0)

            # Foot
            fx, fy, fz = make_ellipsoid(x_off, 0.08, -1.22, 0.09, 0.20, 0.07, 10)
            self.ax.plot_surface(fx, fy, fz, color=leg_col, alpha=alpha(0.8), linewidth=0)

        # ── BLOOD VESSELS (Malaria / Dengue) ──
        if self.current_disease in ["Malaria", "Dengue Fever"]:
            self._draw_blood_vessels(p, colors)

        # ── SKIN RASH (Dengue / Chikungunya) ──
        if self.current_disease in ["Dengue Fever", "Chikungunya"] and p > 0.10:
            self._draw_rash(p, colors)

        # Title removed to prevent overlapping with bottom control widgets and tabs
        pass

    def _plot_organ_surface(self, x, y, z, color, alpha, is_affected, n_res, organ_name=None):
        """Helper to plot organ surface with optional holographic wireframe grid overlay and selection highlighting."""
        # Handle selection highlighting
        if self.selected_organ is not None:
            is_selected = (organ_name == self.selected_organ) or \
                          (organ_name == "Blood" and self.selected_organ == "Blood System")
            
            if is_selected:
                # Highlight the selected organ
                alpha = 0.95
                if color == "#112233":
                    color = "#7ecbf5" # blue highlight for healthy selected organ
                is_affected = True # Force wireframe overlay for selected organ to look cool!
            else:
                # Dim non-selected organs
                alpha = 0.05
                is_affected = False # disable wireframe for non-selected

        if is_affected:
            # Draw shaded surface
            self.ax.plot_surface(x, y, z, color=color, alpha=alpha * 0.8, linewidth=0, shade=True)
            # Draw glowing wireframe grid overlay
            stride = 2 if n_res >= 15 else 1
            self.ax.plot_wireframe(x, y, z, color=color, alpha=alpha * 0.45, linewidth=0.5,
                                   rstride=stride, cstride=stride)
        else:
            self.ax.plot_surface(x, y, z, color=color, alpha=alpha, linewidth=0)

    def _draw_organs(self, p, colors, data, n):
        """Draw internal organs with disease-specific coloring and highlights."""
        affected = {
            "Malaria": ["Liver", "Spleen", "Blood", "Kidneys", "Brain"],
            "Dengue Fever": ["Liver", "Blood", "Heart", "Kidneys", "Skin"],
            "Chikungunya": ["Liver", "Joints", "Muscles", "Skin"],
        }.get(self.current_disease, [])

        # Check both "Blood" and "Blood System"
        has_blood = ("Blood" in affected) or ("Blood System" in affected)

        # BRAIN (Left and right hemispheres in the head)
        has_brain = "Brain" in affected
        brain_col = "#ffab00" if has_brain else "#112233"
        brain_alpha = 0.90 if has_brain else 0.02
        for side in [-1, 1]:
            bx, by, bz = make_ellipsoid(side * 0.06, 0.02, 1.85, 0.11, 0.13, 0.12, 10)
            self._plot_organ_surface(bx, by, bz, brain_col, brain_alpha, has_brain, 10, "Brain")

        # HEART
        has_heart = "Heart" in affected
        heart_col = "#ff2d55" if has_heart else "#112233"
        heart_alpha = 0.90 if has_heart else 0.02
        hx, hy, hz = make_ellipsoid(0.1, -0.15, 1.05, 0.12, 0.1, 0.14, n)
        self._plot_organ_surface(hx, hy, hz, heart_col, heart_alpha, has_heart, n, "Heart")

        # LUNGS (left and right)
        has_lungs = "Lungs" in affected
        lung_col = "#ff7043" if has_lungs else "#112233"
        lung_alpha = 0.85 if has_lungs else 0.02
        for lx_off in [-0.2, 0.2]:
            lx, ly, lz = make_ellipsoid(lx_off, -0.1, 0.95, 0.18, 0.12, 0.22, n)
            self._plot_organ_surface(lx, ly, lz, lung_col, lung_alpha, has_lungs, n, "Lungs")

        # LIVER
        has_liver = "Liver" in affected
        liver_col = "#ffa726" if has_liver else "#112233"
        liver_alpha = 0.90 if has_liver else 0.02
        lvx, lvy, lvz = make_ellipsoid(0.15, -0.1, 0.72, 0.22, 0.15, 0.12, n)
        self._plot_organ_surface(lvx, lvy, lvz, liver_col, liver_alpha, has_liver, n, "Liver")

        # SPLEEN (Malaria: enlarged)
        has_spleen = "Spleen" in affected
        spleen_col = "#e040fb" if has_spleen else "#112233"
        spleen_alpha = 0.90 if has_spleen else 0.02
        spleen_scale = 1.0 + (data.get('spleen_size', 1.0) - 1.0) * 0.3 if (self.current_disease == "Malaria" and p > 0.05) else 1.0
        sx, sy, sz = make_ellipsoid(-0.28, -0.08, 0.68, 0.1 * spleen_scale, 0.07, 0.12 * spleen_scale, n)
        self._plot_organ_surface(sx, sy, sz, spleen_col, spleen_alpha, has_spleen, n, "Spleen")

        # KIDNEYS
        has_kidneys = "Kidneys" in affected
        kidney_col = "#ff9100" if has_kidneys else "#112233"
        kidney_alpha = 0.90 if has_kidneys else 0.02
        for kx_off in [-0.22, 0.22]:
            kx, ky, kz = make_ellipsoid(kx_off, -0.05, 0.52, 0.08, 0.06, 0.14, n)
            self._plot_organ_surface(kx, ky, kz, kidney_col, kidney_alpha, has_kidneys, n, "Kidneys")

        # STOMACH (unaffected reference)
        stx, sty, stz = make_ellipsoid(-0.1, -0.12, 0.75, 0.12, 0.08, 0.1, n)
        self._plot_organ_surface(stx, sty, stz, "#112233", 0.02, False, n, "Stomach")

        # MUSCLES (Biceps and Thighs)
        has_muscles = "Muscles" in affected
        muscle_col = "#ffa726" if has_muscles else "#112233"
        muscle_alpha = 0.90 if has_muscles else 0.02
        # Draw Left/Right Biceps
        for side in [-1, 1]:
            bx, by, bz = make_ellipsoid(side * 0.58, 0.0, 0.78, 0.08, 0.08, 0.16, 10)
            self._plot_organ_surface(bx, by, bz, muscle_col, muscle_alpha, has_muscles, 10, "Muscles")
        # Draw Left/Right Thigh Muscles
        for side in [-1, 1]:
            tx, ty, tz = make_ellipsoid(side * 0.2, 0.0, -0.26, 0.12, 0.12, 0.22, 10)
            self._plot_organ_surface(tx, ty, tz, muscle_col, muscle_alpha, has_muscles, 10, "Muscles")

        # JOINTS (Elbows, Knees, Wrists, Ankles)
        has_joints = "Joints" in affected
        joint_col = "#ffd600" if has_joints else "#112233"
        joint_alpha = 0.90 if has_joints else 0.02
        # Wrist joints
        for side in [-1, 1]:
            jwx, jwy, jwz = make_sphere(side * 0.6, 0, 0.06, 0.09, 0.08, 0.09, 10)
            self._plot_organ_surface(jwx, jwy, jwz, joint_col, joint_alpha, has_joints, 10, "Joints")
        # Ankle joints
        for side in [-1, 1]:
            jax2, jay2, jaz2 = make_sphere(side * 0.2, 0, -1.15, 0.1, 0.09, 0.09, 10)
            self._plot_organ_surface(jax2, jay2, jaz2, joint_col, joint_alpha, has_joints, 10, "Joints")
        # Elbow joints
        for side in [-1, 1]:
            jex, jey, jez = make_sphere(side * 0.58, 0, 0.45, 0.12, 0.12, 0.12, 10)
            self._plot_organ_surface(jex, jey, jez, joint_col, joint_alpha, has_joints, 10, "Joints")
        # Knee joints
        for side in [-1, 1]:
            jkx, jky, jkz = make_sphere(side * 0.2, 0, -0.6, 0.14, 0.12, 0.12, 10)
            self._plot_organ_surface(jkx, jky, jkz, joint_col, joint_alpha, has_joints, 10, "Joints")

    def _draw_blood_vessels(self, progression, colors):
        """Draw blood vessel network highlighting."""
        # Bright crimson if blood is affected
        vessel_col = "#ff3b30"
        alpha = min(0.90, 0.45 + progression * 0.45)
        
        # Check selection
        if self.selected_organ is not None:
            if self.selected_organ == "Blood System":
                alpha = 0.95
                vessel_col = "#ff2d55"
            else:
                alpha = 0.05
        t = np.linspace(0, 1, 30)

        # Main aorta
        z_aorta = np.linspace(0.3, 1.1, 30)
        x_aorta = 0.05 * np.sin(t * np.pi * 4) * progression
        y_aorta = np.full(30, -0.05)
        self.ax.plot(x_aorta, y_aorta, z_aorta, color=vessel_col, alpha=alpha, linewidth=2.5)

        # Branch vessels
        for i, (x_end, z_end) in enumerate([(0.3, 0.7), (-0.3, 0.7), (0.15, 0.5), (-0.15, 0.5)]):
            x_br = np.linspace(0, x_end, 15)
            z_br = np.linspace(0.9, z_end, 15)
            y_br = np.full(15, -0.1)
            self.ax.plot(x_br, y_br, z_br, color=vessel_col, alpha=alpha * 0.75, linewidth=1.5)

        # Leg vessels
        for x_off in [-0.2, 0.2]:
            x_leg = np.full(20, x_off)
            z_leg = np.linspace(-0.2, -1.1, 20)
            y_leg = np.full(20, -0.05)
            self.ax.plot(x_leg, y_leg, z_leg, color=vessel_col, alpha=alpha * 0.5, linewidth=1.2)

    def _draw_rash(self, progression, colors):
        """Draw skin rash dots for Dengue/Chikungunya."""
        rng = np.random.RandomState(99)
        rash_col = colors.get("skin", "#cc2288")
        num_dots = int(progression * 80)
        
        alpha_val = 0.7
        # Check selection
        if self.selected_organ is not None:
            if self.selected_organ == "Skin":
                alpha_val = 0.95
            else:
                alpha_val = 0.05

        xs, ys, zs = [], [], []
        for _ in range(num_dots):
            # Random position on torso/limbs
            part = rng.choice(['torso', 'arm', 'leg'])
            if part == 'torso':
                x = rng.uniform(-0.35, 0.35)
                y = rng.uniform(-0.2, -0.3)
                z = rng.uniform(0.2, 1.5)
            elif part == 'arm':
                x = rng.choice([-1, 1]) * rng.uniform(0.5, 0.65)
                y = rng.uniform(-0.1, 0.1)
                z = rng.uniform(0.1, 1.0)
            else:
                x = rng.choice([-1, 1]) * rng.uniform(0.15, 0.25)
                y = rng.uniform(-0.1, 0.1)
                z = rng.uniform(-1.1, 0.0)
            xs.append(x)
            ys.append(y)
            zs.append(z)

        if xs:
            # Optimized: Plot all rash dots as a single 3D scatter collection instead of drawing 80 individual spheres
            self.ax.scatter(xs, ys, zs, color=rash_col, alpha=alpha_val, s=12, depthshade=True)

    def _draw_labels(self, progression):
        """Draw organ labels with dotted leader lines when disease is active."""
        label_color = '#4fc3f7'
        organ_labels = {
            "Malaria": [
                (1.3, 0, 0.72, 0.15, -0.1, 0.72, "LIVER ↑ALT"),
                (-1.3, 0, 0.68, -0.28, -0.08, 0.68, "SPLEEN ↑"),
                (1.3, 0, 1.2, 0.0, -0.05, 1.0, "BLOOD SYSTEM"),
                (-1.3, 0, 1.85, 0.0, 0, 1.85, "BRAIN (CEREBRAL)"),
                (1.3, 0, 0.52, 0.22, -0.05, 0.52, "KIDNEYS"),
            ],
            "Dengue Fever": [
                (1.3, 0, 0.72, 0.15, -0.1, 0.72, "LIVER ↑AST"),
                (-1.3, 0, 1.05, 0.1, -0.15, 1.05, "HEART ↓BP"),
                (1.3, 0, 0.52, 0.22, -0.05, 0.52, "KIDNEYS"),
                (-1.3, 0, 1.2, 0.0, -0.05, 1.0, "BLOOD SYSTEM"),
            ],
            "Chikungunya": [
                (1.3, 0, 0.45, 0.58, 0, 0.45, "ELBOW JOINT"),
                (-1.3, 0, -0.6, -0.2, 0, -0.6, "KNEE JOINT"),
                (-1.3, 0, 0.1, -0.2, 0, 0.1, "MUSCLES ↑"),
                (1.3, 0, 0.72, 0.15, -0.1, 0.72, "LIVER"),
            ],
        }

        for lx, ly, lz, ox, oy, oz, lbl in organ_labels.get(self.current_disease, []):
            lbl_upper = lbl.upper()
            is_match = False
            if self.selected_organ:
                so_upper = self.selected_organ.upper()
                if so_upper == "BLOOD SYSTEM" and "BLOOD" in lbl_upper:
                    is_match = True
                elif so_upper in lbl_upper:
                    is_match = True
            
            alpha_val = 0.85
            edge_col = '#5a8fd4'
            line_style = ':'
            line_w = 0.8
            
            if self.selected_organ is not None:
                if is_match:
                    alpha_val = 0.95
                    edge_col = "#4fc3f7"
                    line_style = '-'
                    line_w = 1.2
                else:
                    alpha_val = 0.15
                    edge_col = '#1a3a60'
                    line_style = ':'
                    line_w = 0.5

            # Draw leader line
            self.ax.plot([lx, ox], [ly, oy], [lz, oz], color=edge_col,
                         linestyle=line_style, linewidth=line_w, alpha=alpha_val * 0.6)
            # Draw anchor dots at both ends of the line
            self.ax.plot([lx, ox], [ly, oy], [lz, oz], color=edge_col,
                         marker='o', markersize=3, linestyle='None', alpha=alpha_val * 0.8)
            # Draw HUD callout label box
            self.ax.text(lx, ly, lz, lbl, color=label_color if is_match or self.selected_organ is None else '#1d4875',
                         fontsize=7, fontweight='bold',
                         fontfamily='monospace', alpha=alpha_val,
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='#050d1a',
                                   edgecolor=edge_col, alpha=alpha_val * 0.7, lw=line_w))

    def _blend_color(self, color1, color2, factor):
        """Blend two hex colors."""
        import matplotlib.colors as mcolors
        try:
            c1 = np.array(mcolors.to_rgb(color1))
            c2 = np.array(mcolors.to_rgb(color2))
            blended = c1 * (1 - factor) + c2 * factor
            return tuple(blended)
        except:
            return color1

    def _on_press(self, event):
        if event.button == 1:
            self.is_rotating = True
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y

    def _on_release(self, event):
        self.is_rotating = False

    def _on_motion(self, event):
        if self.is_rotating and event.x is not None:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.azimuth += dx * 0.5
            self.elevation = max(-90, min(90, self.elevation - dy * 0.3))
            self.ax.view_init(elev=self.elevation, azim=self.azimuth)
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.canvas.draw_idle()

    def _on_scroll(self, event):
        if event.button == 'up':
            self.zoom = min(5.0, self.zoom * 1.1)
        else:
            self.zoom = max(0.4, self.zoom / 1.1)
        self._apply_zoom()
        self.canvas.draw_idle()
