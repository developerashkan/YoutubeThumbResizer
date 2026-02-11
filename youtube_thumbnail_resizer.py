#!/usr/bin/env python3
"""
YouTube Thumbnail Resizer
A Tkinter + Pillow desktop app for preparing 1280x720 thumbnails.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Tuple

from PIL import Image, ImageOps, ImageTk


class ThumbnailResizerApp:
    """Main GUI application for resizing/cropping YouTube thumbnails."""

    TARGET_SIZE = (1280, 720)
    TARGET_RATIO = TARGET_SIZE[0] / TARGET_SIZE[1]

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Thumbnail Resizer")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # -------------------------------
        # App state
        # -------------------------------
        self.image_path: Optional[str] = None
        self.original_image: Optional[Image.Image] = None
        self.preview_image_tk: Optional[ImageTk.PhotoImage] = None

        self.preview_scale: float = 1.0
        self.preview_offset: Tuple[float, float] = (0.0, 0.0)
        self.preview_bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)

        self.drag_start: Optional[Tuple[float, float]] = None
        self.drag_current: Optional[Tuple[float, float]] = None
        self.crop_rect_canvas_id: Optional[int] = None
        self.manual_crop_box: Optional[Tuple[int, int, int, int]] = None

        self.resize_mode = tk.StringVar(value="fit")
        self.lock_aspect = tk.BooleanVar(value=True)
        self.jpeg_quality = tk.IntVar(value=90)
        self.status_var = tk.StringVar(value="Load an image to begin.")

        # -------------------------------
        # Styling
        # -------------------------------
        self._setup_style()

        # -------------------------------
        # Layout and widgets
        # -------------------------------
        self._build_ui()

        # -------------------------------
        # Initial widget state
        # -------------------------------
        self._set_processing_enabled(False)
        self._update_manual_crop_ui_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", relief="sunken", anchor="w", padding=(8, 4))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        controls = ttk.Frame(self.root, padding=12)
        controls.grid(row=0, column=0, sticky="ns")

        preview_frame = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        status_bar = ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel")
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Left controls
        ttk.Label(controls, text="YouTube Thumbnail Resizer", style="Header.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        file_box = ttk.LabelFrame(controls, text="File", style="Section.TLabelframe", padding=10)
        file_box.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        file_box.columnconfigure(0, weight=1)

        self.select_btn = ttk.Button(file_box, text="Select Image...", command=self.select_image)
        self.select_btn.grid(row=0, column=0, sticky="ew")

        self.file_label = ttk.Label(file_box, text="No file loaded", wraplength=280, foreground="#555")
        self.file_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        mode_box = ttk.LabelFrame(controls, text="Resize Mode", style="Section.TLabelframe", padding=10)
        mode_box.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Radiobutton(
            mode_box,
            text="Fit with black padding (preserve aspect ratio)",
            value="fit",
            variable=self.resize_mode,
            command=self._on_mode_changed,
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        ttk.Radiobutton(
            mode_box,
            text="Center crop to 16:9 then resize",
            value="center",
            variable=self.resize_mode,
            command=self._on_mode_changed,
        ).grid(row=1, column=0, sticky="w", pady=4)

        ttk.Radiobutton(
            mode_box,
            text="Manual crop (draw rectangle on preview)",
            value="manual",
            variable=self.resize_mode,
            command=self._on_mode_changed,
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        manual_box = ttk.LabelFrame(controls, text="Manual Crop", style="Section.TLabelframe", padding=10)
        manual_box.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        self.aspect_check = ttk.Checkbutton(
            manual_box,
            text="Lock crop ratio to 16:9",
            variable=self.lock_aspect,
            command=self._on_lock_toggle,
        )
        self.aspect_check.grid(row=0, column=0, sticky="w")

        self.clear_crop_btn = ttk.Button(manual_box, text="Clear Selection", command=self.clear_manual_crop)
        self.clear_crop_btn.grid(row=1, column=0, sticky="w", pady=(8, 0))

        quality_box = ttk.LabelFrame(controls, text="Output Quality", style="Section.TLabelframe", padding=10)
        quality_box.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        quality_box.columnconfigure(0, weight=1)

        ttk.Label(quality_box, text="JPEG quality (1-100)").grid(row=0, column=0, sticky="w")
        self.quality_scale = ttk.Scale(
            quality_box,
            from_=1,
            to=100,
            orient="horizontal",
            variable=self.jpeg_quality,
            command=lambda _e: self.quality_value_label.config(text=str(self.jpeg_quality.get())),
        )
        self.quality_scale.grid(row=1, column=0, sticky="ew", pady=(6, 2))
        self.quality_value_label = ttk.Label(quality_box, text=str(self.jpeg_quality.get()))
        self.quality_value_label.grid(row=2, column=0, sticky="w")

        action_box = ttk.Frame(controls)
        action_box.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        action_box.columnconfigure(0, weight=1)

        self.process_btn = ttk.Button(action_box, text="Resize and Save...", command=self.process_and_save)
        self.process_btn.grid(row=0, column=0, sticky="ew")

        # Right preview
        ttk.Label(preview_frame, text="Preview", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="#1f1f1f",
            highlightthickness=1,
            highlightbackground="#444",
            cursor="crosshair",
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew")

        self.preview_canvas.bind("<Configure>", self._on_canvas_resize)
        self.preview_canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.preview_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    # ------------------------------------------------------------------
    # UI state helpers
    # ------------------------------------------------------------------
    def _set_processing_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.process_btn.config(state=state)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def _on_mode_changed(self) -> None:
        self._update_manual_crop_ui_state()
        if self.resize_mode.get() != "manual":
            self._remove_crop_rect_visual()
            self.manual_crop_box = None
        elif self.original_image is not None:
            self._draw_saved_crop_rect()

    def _on_lock_toggle(self) -> None:
        if self.resize_mode.get() == "manual" and self.manual_crop_box is not None:
            self._draw_saved_crop_rect()

    def _update_manual_crop_ui_state(self) -> None:
        is_manual = self.resize_mode.get() == "manual"
        state = "normal" if is_manual else "disabled"
        self.aspect_check.config(state=state)
        self.clear_crop_btn.config(state=state)

    # ------------------------------------------------------------------
    # File loading and preview
    # ------------------------------------------------------------------
    def select_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            with Image.open(file_path) as img:
                img.load()
                self.original_image = ImageOps.exif_transpose(img).convert("RGB")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load image:\n{exc}")
            self._set_status("Failed to load image.")
            return

        self.image_path = file_path
        self.file_label.config(text=os.path.basename(file_path))
        self.manual_crop_box = None
        self._remove_crop_rect_visual()
        self._set_processing_enabled(True)
        self._set_status("Image loaded. Choose a mode and save output.")
        self._render_preview()

    def _render_preview(self) -> None:
        self.preview_canvas.delete("all")
        self._remove_crop_rect_visual()

        if self.original_image is None:
            return

        canvas_w = max(1, self.preview_canvas.winfo_width())
        canvas_h = max(1, self.preview_canvas.winfo_height())
        img_w, img_h = self.original_image.size

        scale = min(canvas_w / img_w, canvas_h / img_h)
        draw_w = max(1, int(img_w * scale))
        draw_h = max(1, int(img_h * scale))

        resized_preview = self.original_image.resize((draw_w, draw_h), Image.Resampling.LANCZOS)
        self.preview_image_tk = ImageTk.PhotoImage(resized_preview)

        offset_x = (canvas_w - draw_w) / 2
        offset_y = (canvas_h - draw_h) / 2

        self.preview_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.preview_image_tk)

        self.preview_scale = scale
        self.preview_offset = (offset_x, offset_y)
        self.preview_bbox = (offset_x, offset_y, offset_x + draw_w, offset_y + draw_h)

        if self.resize_mode.get() == "manual" and self.manual_crop_box is not None:
            self._draw_saved_crop_rect()

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        if self.original_image is not None:
            self._render_preview()

    # ------------------------------------------------------------------
    # Manual crop interactions
    # ------------------------------------------------------------------
    def _on_mouse_down(self, event: tk.Event) -> None:
        if self.resize_mode.get() != "manual" or self.original_image is None:
            return

        x, y = self._clamp_to_preview(event.x, event.y)
        self.drag_start = (x, y)
        self.drag_current = (x, y)
        self._draw_drag_rect(self.drag_start, self.drag_current)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if self.resize_mode.get() != "manual" or self.drag_start is None or self.original_image is None:
            return

        x, y = self._clamp_to_preview(event.x, event.y)
        self.drag_current = self._apply_aspect_lock(self.drag_start, (x, y))
        self._draw_drag_rect(self.drag_start, self.drag_current)

    def _on_mouse_up(self, event: tk.Event) -> None:
        if self.resize_mode.get() != "manual" or self.drag_start is None or self.original_image is None:
            return

        x, y = self._clamp_to_preview(event.x, event.y)
        end = self._apply_aspect_lock(self.drag_start, (x, y))
        self.drag_current = end
        self._draw_drag_rect(self.drag_start, self.drag_current)

        crop_box = self._canvas_rect_to_image_rect(self.drag_start, end)
        if crop_box is None:
            self.manual_crop_box = None
            self._set_status("Manual crop too small. Drag a larger rectangle.")
        else:
            self.manual_crop_box = crop_box
            self._set_status("Manual crop selected.")

        self.drag_start = None
        self.drag_current = None

    def _apply_aspect_lock(self, start: Tuple[float, float], current: Tuple[float, float]) -> Tuple[float, float]:
        if not self.lock_aspect.get():
            return current

        sx, sy = start
        cx, cy = current
        dx = cx - sx
        dy = cy - sy

        if dx == 0 and dy == 0:
            return current

        sign_x = 1 if dx >= 0 else -1
        sign_y = 1 if dy >= 0 else -1
        abs_dx = abs(dx)
        abs_dy = abs(dy)

        if abs_dy == 0:
            abs_dy = 1e-6

        current_ratio = abs_dx / abs_dy
        target = self.TARGET_RATIO

        if current_ratio > target:
            abs_dx = abs_dy * target
        else:
            abs_dy = abs_dx / target if abs_dx != 0 else 0

        return sx + sign_x * abs_dx, sy + sign_y * abs_dy

    def _clamp_to_preview(self, x: float, y: float) -> Tuple[float, float]:
        left, top, right, bottom = self.preview_bbox
        return min(max(x, left), right), min(max(y, top), bottom)

    def _draw_drag_rect(self, start: Tuple[float, float], end: Tuple[float, float]) -> None:
        self._remove_crop_rect_visual()
        x1, y1 = start
        x2, y2 = end
        self.crop_rect_canvas_id = self.preview_canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="#00d4ff",
            width=2,
            dash=(6, 3),
        )

    def _remove_crop_rect_visual(self) -> None:
        if self.crop_rect_canvas_id is not None:
            self.preview_canvas.delete(self.crop_rect_canvas_id)
            self.crop_rect_canvas_id = None

    def _canvas_rect_to_image_rect(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Tuple[int, int, int, int]]:
        if self.original_image is None:
            return None

        x1, y1 = start
        x2, y2 = end

        left, right = sorted([x1, x2])
        top, bottom = sorted([y1, y2])

        if (right - left) < 3 or (bottom - top) < 3:
            return None

        off_x, off_y = self.preview_offset
        scale = self.preview_scale
        img_w, img_h = self.original_image.size

        img_left = int(round((left - off_x) / scale))
        img_top = int(round((top - off_y) / scale))
        img_right = int(round((right - off_x) / scale))
        img_bottom = int(round((bottom - off_y) / scale))

        img_left = max(0, min(img_left, img_w - 1))
        img_top = max(0, min(img_top, img_h - 1))
        img_right = max(1, min(img_right, img_w))
        img_bottom = max(1, min(img_bottom, img_h))

        if img_right <= img_left or img_bottom <= img_top:
            return None

        return img_left, img_top, img_right, img_bottom

    def _draw_saved_crop_rect(self) -> None:
        if self.original_image is None or self.manual_crop_box is None:
            return

        l, t, r, b = self.manual_crop_box
        off_x, off_y = self.preview_offset
        scale = self.preview_scale

        x1 = off_x + l * scale
        y1 = off_y + t * scale
        x2 = off_x + r * scale
        y2 = off_y + b * scale

        self._draw_drag_rect((x1, y1), (x2, y2))

    def clear_manual_crop(self) -> None:
        self.manual_crop_box = None
        self._remove_crop_rect_visual()
        self._set_status("Manual crop cleared.")

    # ------------------------------------------------------------------
    # Processing and save logic
    # ------------------------------------------------------------------
    def process_and_save(self) -> None:
        if self.original_image is None or self.image_path is None:
            messagebox.showwarning("No image", "Please load an image first.")
            return

        mode = self.resize_mode.get()

        if mode == "manual" and self.manual_crop_box is None:
            messagebox.showwarning("Manual crop required", "Draw a crop rectangle on the preview first.")
            return

        try:
            processed = self._process_image(mode)
        except Exception as exc:
            messagebox.showerror("Processing error", f"Failed to process image:\n{exc}")
            self._set_status("Image processing failed.")
            return

        ext = os.path.splitext(self.image_path)[1].lower()
        is_png_source = ext == ".png"

        suggested_ext = ".png" if is_png_source else ".jpg"
        suggested_name = os.path.splitext(os.path.basename(self.image_path))[0] + "_yt_thumb" + suggested_ext

        save_path = filedialog.asksaveasfilename(
            title="Save resized image",
            defaultextension=suggested_ext,
            initialfile=suggested_name,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All files", "*.*")],
        )

        if not save_path:
            self._set_status("Save cancelled.")
            return

        if os.path.exists(save_path):
            overwrite = messagebox.askyesno("Overwrite file?", f"File exists:\n{save_path}\n\nOverwrite?")
            if not overwrite:
                self._set_status("Save cancelled (overwrite declined).")
                return

        try:
            output_ext = os.path.splitext(save_path)[1].lower()
            if output_ext == ".png":
                processed.save(save_path, format="PNG", optimize=True)
            else:
                quality = max(1, min(100, int(self.jpeg_quality.get())))
                processed.save(save_path, format="JPEG", quality=quality, subsampling=0, optimize=True)
        except Exception as exc:
            messagebox.showerror("Save error", f"Failed to save image:\n{exc}")
            self._set_status("Save failed.")
            return

        self._set_status(f"Saved: {save_path}")
        messagebox.showinfo("Success", f"Thumbnail saved successfully:\n{save_path}")

    def _process_image(self, mode: str) -> Image.Image:
        assert self.original_image is not None

        if mode == "fit":
            return self._process_fit_with_padding(self.original_image)

        if mode == "center":
            return self._process_center_crop(self.original_image)

        if mode == "manual":
            if self.manual_crop_box is None:
                raise ValueError("Manual crop box is missing.")
            cropped = self.original_image.crop(self.manual_crop_box)
            return cropped.resize(self.TARGET_SIZE, Image.Resampling.LANCZOS)

        raise ValueError(f"Unknown mode: {mode}")

    def _process_fit_with_padding(self, img: Image.Image) -> Image.Image:
        resized = ImageOps.contain(img, self.TARGET_SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", self.TARGET_SIZE, color=(0, 0, 0))
        x = (self.TARGET_SIZE[0] - resized.width) // 2
        y = (self.TARGET_SIZE[1] - resized.height) // 2
        canvas.paste(resized, (x, y))
        return canvas

    def _process_center_crop(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        ratio = w / h

        if ratio > self.TARGET_RATIO:
            new_w = int(h * self.TARGET_RATIO)
            left = (w - new_w) // 2
            crop_box = (left, 0, left + new_w, h)
        else:
            new_h = int(w / self.TARGET_RATIO)
            top = (h - new_h) // 2
            crop_box = (0, top, w, top + new_h)

        return img.crop(crop_box).resize(self.TARGET_SIZE, Image.Resampling.LANCZOS)


def main() -> None:
    root = tk.Tk()
    app = ThumbnailResizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------
# Setup and usage
# ----------------------------------------------------------------------
# Install dependency:
#   pip install pillow
#
# Run:
#   python youtube_thumbnail_resizer.py
#
# Manual test checklist:
#   [ ] Landscape image: verify all three modes export correctly at 1280x720
#   [ ] Portrait image: verify fit mode pads and crop modes frame as expected
#   [ ] Ultra-wide image: verify center/manual crop behavior and no distortion
#   [ ] Small resolution image: verify upscale quality and no app crashes
#   [ ] Manual crop test: draw/clear/lock 16:9 crop and confirm final output
