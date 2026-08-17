"""Utilities for animal face feature detection with MMPose.

This module wraps :class:`mmpose.apis.MMPoseInferencer` and adds a small
post-processing layer that groups keypoints into face features (eyes, nose,
mouth/ears when available) and draws feature boxes for quick visual checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import pkgutil
import logging
import warnings
import io
from contextlib import redirect_stdout, redirect_stderr

import numpy as np
from PIL import Image, ImageDraw


# Python 3.12 removed pkgutil.ImpImporter/ImpLoader, but some third-party
# dependency stacks (via pkg_resources) still reference them at import time.
if not hasattr(pkgutil, "ImpImporter"):
	class _CompatImpImporter:  # pragma: no cover - import-time compatibility shim
		pass

	pkgutil.ImpImporter = _CompatImpImporter  # type: ignore[attr-defined]

if not hasattr(pkgutil, "ImpLoader"):
	class _CompatImpLoader:  # pragma: no cover - import-time compatibility shim
		pass

	pkgutil.ImpLoader = _CompatImpLoader  # type: ignore[attr-defined]


# Fallback labels for AP-10K-style ordering when keypoint names are not
# available in the MMPose prediction payload.
_AP10K_FALLBACK_NAMES = [
	"left_eye",
	"right_eye",
	"nose",
	"neck",
	"tail_root",
	"left_shoulder",
	"left_elbow",
	"left_front_paw",
	"right_shoulder",
	"right_elbow",
	"right_front_paw",
	"left_hip",
	"left_knee",
	"left_back_paw",
	"right_hip",
	"right_knee",
	"right_back_paw",
]

_FEATURE_KEYWORDS = {
	"left_eye": ("left_eye", "l_eye", "eye_l"),
	"right_eye": ("right_eye", "r_eye", "eye_r"),
	"eyes": ("eye",),
	"nose": ("nose", "snout"),
	"mouth": ("mouth", "lip", "chin", "jaw"),
	"left_ear": ("left_ear", "l_ear", "ear_l"),
	"right_ear": ("right_ear", "r_ear", "ear_r"),
	"ears": ("ear",),
}


_INFERENCER_CACHE: dict[str, Any] = {}


def _configure_mmlab_runtime_quiet_mode() -> None:
	"""Reduce noisy runtime output from MMLab dependencies in notebooks."""

	warnings.filterwarnings("ignore", category=FutureWarning, module=r"mmdet\\..*")
	warnings.filterwarnings("ignore", category=FutureWarning, module=r"mmengine\\..*")
	warnings.filterwarnings(
		"ignore",
		message=r"`torch\.cuda\.amp\.autocast\(args\.\.\.\)` is deprecated.*",
		category=FutureWarning,
	)

	for logger_name in ("mmengine", "mmcv", "mmdet", "mmpose"):
		logger = logging.getLogger(logger_name)
		logger.setLevel(logging.ERROR)
		logger.propagate = False


def _call_quietly(func: Any, /, *args: Any, **kwargs: Any) -> Any:
	"""Run a callable while suppressing noisy stdout/stderr side output."""

	stdout_buffer = io.StringIO()
	stderr_buffer = io.StringIO()
	with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
		with warnings.catch_warnings():
			warnings.simplefilter("ignore", FutureWarning)
			warnings.simplefilter("ignore", UserWarning)
			return func(*args, **kwargs)


@dataclass(frozen=True)
class FeatureBox:
	"""Axis-aligned bounding box around one feature."""

	name: str
	bbox_xyxy: tuple[int, int, int, int]
	keypoint_indices: tuple[int, ...]
	average_score: float


@dataclass(frozen=True)
class AnimalFaceDetection:
	"""Normalized output for one detected animal instance."""

	keypoints: np.ndarray
	keypoint_scores: np.ndarray
	keypoint_names: tuple[str, ...]
	feature_boxes: tuple[FeatureBox, ...]
	face_bbox_xyxy: tuple[int, int, int, int] | None


def _load_mmpose_inferencer() -> Any:
	try:
		from mmpose.apis import MMPoseInferencer
	except (ImportError, AttributeError) as exc:
		raise ImportError(
			"MMPose backend import failed. Install compatible deps with: "
			"pip install mmpose mmdet mmengine \"mmcv<2.2.0\""
		) from exc
	return MMPoseInferencer


def _get_cached_inferencer(pose2d: str) -> Any:
	if pose2d in _INFERENCER_CACHE:
		return _INFERENCER_CACHE[pose2d]

	_configure_mmlab_runtime_quiet_mode()
	MMPoseInferencer = _load_mmpose_inferencer()
	inferencer = _call_quietly(MMPoseInferencer, pose2d=pose2d)
	_INFERENCER_CACHE[pose2d] = inferencer
	return inferencer


def _to_pil_image(image: str | Path | np.ndarray | Image.Image) -> Image.Image:
	if isinstance(image, Image.Image):
		return image
	if isinstance(image, (str, Path)):
		return Image.open(image).convert("RGB")
	if isinstance(image, np.ndarray):
		if image.ndim == 2:
			return Image.fromarray(image.astype(np.uint8), mode="L").convert("RGB")
		return Image.fromarray(image.astype(np.uint8)).convert("RGB")
	raise TypeError("image must be a path, numpy array, or PIL image")


def _normalize_name(name: str) -> str:
	return name.strip().lower().replace(" ", "_")


def _resolve_keypoint_names(
	instance: dict[str, Any], keypoints: np.ndarray, keypoint_names: list[str] | None
) -> list[str]:
	if keypoint_names and len(keypoint_names) == len(keypoints):
		return [_normalize_name(name) for name in keypoint_names]

	instance_names = instance.get("keypoint_names")
	if isinstance(instance_names, list) and len(instance_names) == len(keypoints):
		return [_normalize_name(str(name)) for name in instance_names]

	if len(keypoints) == len(_AP10K_FALLBACK_NAMES):
		return _AP10K_FALLBACK_NAMES.copy()

	return [f"kp_{i}" for i in range(len(keypoints))]


def _collect_indices_by_feature(keypoint_names: list[str]) -> dict[str, list[int]]:
	indices: dict[str, list[int]] = {feature: [] for feature in _FEATURE_KEYWORDS}
	for idx, kp_name in enumerate(keypoint_names):
		for feature, keywords in _FEATURE_KEYWORDS.items():
			if any(keyword in kp_name for keyword in keywords):
				indices[feature].append(idx)

	# Prefer concrete left/right eyes when available, otherwise fallback to all eyes.
	if not indices["left_eye"] and not indices["right_eye"] and indices["eyes"]:
		if len(indices["eyes"]) >= 2:
			indices["left_eye"] = [indices["eyes"][0]]
			indices["right_eye"] = [indices["eyes"][1]]
		else:
			indices["left_eye"] = indices["eyes"]

	if not indices["left_ear"] and not indices["right_ear"] and indices["ears"]:
		if len(indices["ears"]) >= 2:
			indices["left_ear"] = [indices["ears"][0]]
			indices["right_ear"] = [indices["ears"][1]]
		else:
			indices["left_ear"] = indices["ears"]

	return indices


def _bbox_from_points(points: np.ndarray, image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
	width, height = image_size
	min_xy = np.floor(points.min(axis=0)).astype(int)
	max_xy = np.ceil(points.max(axis=0)).astype(int)

	x1 = max(0, int(min_xy[0]) - padding)
	y1 = max(0, int(min_xy[1]) - padding)
	x2 = min(width - 1, int(max_xy[0]) + padding)
	y2 = min(height - 1, int(max_xy[1]) + padding)
	return x1, y1, x2, y2


def _build_feature_boxes(
	keypoints: np.ndarray,
	scores: np.ndarray,
	keypoint_names: list[str],
	image_size: tuple[int, int],
	score_threshold: float,
	feature_padding: int,
) -> list[FeatureBox]:
	feature_indices = _collect_indices_by_feature(keypoint_names)
	feature_boxes: list[FeatureBox] = []

	for feature_name in ("left_eye", "right_eye", "nose", "mouth", "left_ear", "right_ear"):
		candidate_indices = feature_indices.get(feature_name, [])
		if not candidate_indices:
			continue

		valid_indices = [idx for idx in candidate_indices if scores[idx] >= score_threshold]
		if not valid_indices:
			continue

		points = keypoints[valid_indices]
		bbox = _bbox_from_points(points, image_size=image_size, padding=feature_padding)
		avg_score = float(np.mean(scores[valid_indices]))
		feature_boxes.append(
			FeatureBox(
				name=feature_name,
				bbox_xyxy=bbox,
				keypoint_indices=tuple(valid_indices),
				average_score=avg_score,
			)
		)

	return feature_boxes


def detect_animal_face_features(
	image: str | Path | np.ndarray | Image.Image,
	*,
	pose2d: str = "animal",
	score_threshold: float = 0.25,
	feature_padding: int = 10,
	inferencer: Any | None = None,
) -> list[AnimalFaceDetection]:
	"""Run MMPose and extract facial feature boxes for each animal instance."""

	pil_image = _to_pil_image(image)
	image_size = pil_image.size
	_configure_mmlab_runtime_quiet_mode()

	if inferencer is None:
		inferencer = _get_cached_inferencer(pose2d=pose2d)

	result_generator = _call_quietly(inferencer, np.array(pil_image), show=False)
	results = _call_quietly(next, result_generator)

	predictions_groups = results.get("predictions", [])
	all_instances: list[dict[str, Any]] = []
	for group in predictions_groups:
		if isinstance(group, list):
			all_instances.extend(group)

	metadata = results.get("metainfo", {})
	meta_keypoint_names = metadata.get("keypoint_names") if isinstance(metadata, dict) else None

	detections: list[AnimalFaceDetection] = []
	for instance in all_instances:
		if not isinstance(instance, dict):
			continue

		keypoints = np.asarray(instance.get("keypoints", []), dtype=float)
		scores = np.asarray(instance.get("keypoint_scores", []), dtype=float)
		if keypoints.size == 0 or scores.size == 0 or len(keypoints) != len(scores):
			continue

		names = _resolve_keypoint_names(instance, keypoints, meta_keypoint_names)
		feature_boxes = _build_feature_boxes(
			keypoints=keypoints,
			scores=scores,
			keypoint_names=names,
			image_size=image_size,
			score_threshold=score_threshold,
			feature_padding=feature_padding,
		)

		face_indices = [
			idx
			for idx, name in enumerate(names)
			if ("eye" in name or "nose" in name or "mouth" in name or "lip" in name or "ear" in name)
			and scores[idx] >= score_threshold
		]
		face_bbox = (
			_bbox_from_points(keypoints[face_indices], image_size=image_size, padding=feature_padding)
			if face_indices
			else None
		)

		detections.append(
			AnimalFaceDetection(
				keypoints=keypoints,
				keypoint_scores=scores,
				keypoint_names=tuple(names),
				feature_boxes=tuple(feature_boxes),
				face_bbox_xyxy=face_bbox,
			)
		)

	return detections


def draw_feature_boxes(
	image: str | Path | np.ndarray | Image.Image,
	detections: list[AnimalFaceDetection],
	*,
	draw_face_bbox: bool = True,
	line_width: int = 2,
) -> Image.Image:
	"""Draw per-feature boxes (and optional face box) on a copy of the input image."""

	palette = {
		"left_eye": "#f94144",
		"right_eye": "#f3722c",
		"nose": "#f9c74f",
		"mouth": "#43aa8b",
		"left_ear": "#277da1",
		"right_ear": "#577590",
	}

	image_pil = _to_pil_image(image).copy()
	draw = ImageDraw.Draw(image_pil)

	for detection in detections:
		if draw_face_bbox and detection.face_bbox_xyxy is not None:
			draw.rectangle(detection.face_bbox_xyxy, outline="#ffffff", width=line_width)

		for feature_box in detection.feature_boxes:
			color = palette.get(feature_box.name, "#ffffff")
			draw.rectangle(feature_box.bbox_xyxy, outline=color, width=line_width)
			x1, y1, _, _ = feature_box.bbox_xyxy
			draw.text((x1 + 2, max(0, y1 - 12)), feature_box.name, fill=color)

	return image_pil


def detect_and_draw_animal_face_features(
	image: str | Path | np.ndarray | Image.Image,
	*,
	pose2d: str = "animal",
	score_threshold: float = 0.25,
	feature_padding: int = 10,
	draw_face_bbox: bool = True,
	line_width: int = 2,
) -> tuple[Image.Image, list[AnimalFaceDetection]]:
	"""Convenience helper that runs detection and returns an annotated image."""

	detections = detect_animal_face_features(
		image=image,
		pose2d=pose2d,
		score_threshold=score_threshold,
		feature_padding=feature_padding,
	)
	annotated = draw_feature_boxes(
		image=image,
		detections=detections,
		draw_face_bbox=draw_face_bbox,
		line_width=line_width,
	)
	return annotated, detections


def append_eye_center_dot_strokes(
	stroke_sequence: Any,
	detections: list[AnimalFaceDetection],
	*,
	brush_diameter: int = 4,
	pigment: float = 1.0,
	min_feature_score: float = 0.0,
) -> int:
	"""Append black dot-like strokes at the center of detected eye features.

	Returns the number of eye-center dot strokes appended.
	"""

	from datatypes import StrokePath

	canvas_width, canvas_height = stroke_sequence.image_size
	appended = 0

	for detection in detections:
		for feature_box in detection.feature_boxes:
			if feature_box.name not in ("left_eye", "right_eye"):
				continue
			if feature_box.average_score < min_feature_score:
				continue

			points = detection.keypoints[list(feature_box.keypoint_indices)]
			if points.size == 0:
				continue

			center_xy = np.mean(points, axis=0)
			cx = int(round(float(center_xy[0])))
			cy = int(round(float(center_xy[1])))
			cx = max(0, min(canvas_width - 1, cx))
			cy = max(0, min(canvas_height - 1, cy))

			end_x = min(canvas_width - 1, cx + 1)
			start_x = max(0, cx - 1)
			if end_x == cx and start_x < cx:
				path = [(start_x, cy), (cx, cy)]
			else:
				path = [(cx, cy), (end_x, cy)]

			stroke_sequence.strokes.append(
				StrokePath(
					color=(0, 0, 0),
					path=path,
					pigment=pigment,
					hex_color="#000000",
					brushDiameter=brush_diameter,
				)
			)
			appended += 1

	return appended


__all__ = [
	"AnimalFaceDetection",
	"FeatureBox",
	"detect_animal_face_features",
	"draw_feature_boxes",
	"detect_and_draw_animal_face_features",
	"append_eye_center_dot_strokes",
]
