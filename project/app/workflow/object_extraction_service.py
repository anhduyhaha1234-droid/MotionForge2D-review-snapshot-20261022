"""Object extraction service — crop PNGs, generate thumbnails and gallery manifests."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from app.schemas import GalleryManifest, ObjectCrop, TrackedObject


class ObjectExtractionService:
    """Generates crop PNGs with alpha for tracked objects."""

    def extract_crops(
        self,
        project_id: str,
        project_dir: Path,
        obj: TrackedObject,
        frame_paths: list[Path],
        masks: list[np.ndarray],
        representative_count: int = 20,
    ) -> GalleryManifest:
        """Extract crop PNGs for representative frames."""
        obj_dir = project_dir / "objects" / obj.object_id
        crops_dir = obj_dir / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        n = len(frame_paths)
        if n == 0:
            return GalleryManifest(
                object_id=obj.object_id,
                project_id=project_id,
            )

        # Select representative frames evenly spaced
        if n <= representative_count:
            indices = list(range(n))
        else:
            step = n / representative_count
            indices = [int(i * step) for i in range(representative_count)]
            if indices[-1] != n - 1:
                indices[-1] = n - 1

        crops: list[ObjectCrop] = []
        thumbnail_path = ""

        for idx in indices:
            frame = cv2.imread(str(frame_paths[idx]))
            if frame is None:
                continue
            mask = masks[idx]

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
            )
            if not contours:
                continue

            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            if w < 2 or h < 2:
                continue

            pad = 5
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(frame.shape[1], x + w + pad)
            y2 = min(frame.shape[0], y + h + pad)

            crop_frame = frame[y1:y2, x1:x2].copy()
            crop_mask = mask[y1:y2, x1:x2].copy()

            bgra = cv2.cvtColor(crop_frame, cv2.COLOR_BGR2BGRA)
            bgra[:, :, 3] = crop_mask

            crop_filename = f"frame_{idx:06d}.png"
            crop_path = crops_dir / crop_filename
            cv2.imwrite(str(crop_path), bgra)

            rel_path = f"objects/{obj.object_id}/crops/{crop_filename}"
            crops.append(ObjectCrop(frame_index=idx, crop_path=rel_path))

        # Generate thumbnail from the first crop
        if crops:
            first_name = f"frame_{indices[0]:06d}.png"
            first_crop = cv2.imread(
                str(crops_dir / first_name), cv2.IMREAD_UNCHANGED,
            )
            if first_crop is not None:
                thumb_size = 128
                h, w = first_crop.shape[:2]
                scale = thumb_size / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                thumb = cv2.resize(
                    first_crop, (new_w, new_h),
                    interpolation=cv2.INTER_AREA,
                )
                thumb_path = obj_dir / "thumbnail.png"
                cv2.imwrite(str(thumb_path), thumb)
                thumbnail_path = f"objects/{obj.object_id}/thumbnail.png"

        manifest = GalleryManifest(
            object_id=obj.object_id,
            project_id=project_id,
            thumbnail_path=thumbnail_path,
            crops=crops,
        )

        manifest_path = obj_dir / "gallery_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)

        return manifest
