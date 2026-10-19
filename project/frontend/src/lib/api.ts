/**
 * MotionForge 2D — API Client
 *
 * Typed client for all backend endpoints.
 */

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8888";
const API_BASE = rawApiUrl.replace(/\/+$/, "");

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE}${cleanPath}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ─── Types ─────────────────────────────────────────────────────────────────

export interface VideoMetadata {
  width: number;
  height: number;
  fps: number;
  duration_seconds: number;
  total_frames: number;
  codec: string;
  has_audio: boolean;
  audio_codec: string | null;
}

export interface SceneInfo {
  scene_id: number;
  start_frame: number;
  end_frame: number;
  start_time_sec: number;
  end_time_sec: number;
  duration_sec: number;
  frame_count: number;
}

export interface SceneDetail {
  scene_id: number;
  start_frame: number;
  end_frame: number;
  start_time_sec: number;
  end_time_sec: number;
  duration_sec: number;
  frame_count: number;
  status: "pending" | "draft" | "approved";
  audio_path: string;
  notes: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface SelectionInput {
  mode: "point" | "bounding_box";
  frame_index: number;
  x: number;
  y: number;
  width?: number;
  height?: number;
}

export interface FrameMotion {
  frame_index: number;
  centroid_x: number;
  centroid_y: number;
  bbox: BoundingBox;
  scale_x: number;
  scale_y: number;
  rotation_deg: number;
  opacity: number;
  visibility: boolean;
  area: number;
  confidence: number;
  occluded: boolean;
  needs_review: boolean;
  mask_path: string | null;
}

export type ClipMode = "asset_alpha" | "original_mask" | "intersection";

export interface ReplacementConfig {
  mode: "none" | "static_asset" | "frame_sequence";
  asset_path: string | null;
  anchor: { x: number; y: number };
  offset: { x: number; y: number };
  scale: number;
  rotation_offset_deg: number;
  opacity: number;
  fit_mode: "contain" | "cover" | "stretch";
  clip_mode: ClipMode;
  frameSequenceDir?: string;
  frameSequenceFps?: number;
}

export interface TrackedObject {
  object_id: string;
  name: string;
  kind: string;
  selection: SelectionInput;
  scene_id: number;
  replacement: ReplacementConfig | null;
  thumbnail_base64?: string;
  motion: {
    scene_id: number;
    frames: FrameMotion[];
    reference_bbox: BoundingBox | null;
    tracking_backend: string;
    model_version: string;
  } | null;
}

export interface ProjectData {
  version: string;
  name: string;
  source_video: string;
  video_metadata: VideoMetadata | null;
  scenes: SceneInfo[];
  scene_details: SceneDetail[];
  objects: TrackedObject[];
}

export interface JobInfo {
  job_id: string;
  status: "queued" | "running" | "cancelling" | "cancelled" | "completed" | "failed";
  progress: number;
  message: string;
  current_step: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  result: Record<string, unknown> | null;
}

export interface GalleryFrame {
  frame_index: number;
  crop_path: string;
  mask_path: string;
  reason: string;
}

export interface GalleryManifest {
  object_id: string;
  project_id: string;
  thumbnail_path: string;
  crops: GalleryFrame[];
}

export interface MaskPreviewRequest {
  frame_index: number;
  selection: SelectionInput;
  backend?: string;
}

export interface MaskPreviewResponse {
  mask_png_base64: string;
  frame_index: number;
  nonzero_pixels: number;
}

export interface DubbingConfig {
  scene_id: number;
  source_lang: string;
  target_lang: string;
  whisper_model: string;
  tts_voice: string;
}

export interface DubbingResult {
  vocal_track: string;
  bgm_track: string;
  original_srt: string;
  translated_srt: string;
  final_audio: string;
  segments: Array<{ start: number; end: number; text: string; original?: string }>;
}

export interface DubbingSegment {
  start: number;
  end: number;
  text: string;
  original?: string;
}

export interface CharacterMapping {
  original_name: string;
  replacement_asset: string;
  voice_config: Record<string, unknown>;
  replacement_config: Record<string, unknown>;
}

export interface ProjectPreset {
  name: string;
  description: string;
  version: string;
  mappings: CharacterMapping[];
  dubbing_config: Record<string, unknown>;
}

export interface PresetInfo {
  filename: string;
  name: string;
  description: string;
  mapping_count: number;
}

export interface GpuInfo {
  has_nvenc: boolean;
  gpu_name: string;
  encoder: string;
}

export interface ChannelWorkspace {
  channel_id: string;
  name: string;
  target_lang: string;
  default_preset_id: string;
  created_at: string;
}

export interface ProjectSummary {
  project_id: string;
  name: string;
  task_status: string;
  source_video: string;
  scenes_count: number;
  updated_at: string;
  created_at: string;
}

export interface ChannelProject {
  project_id: string;
  name: string;
  task_status: "draft" | "in_progress" | "ready_to_stitch" | "completed";
  created_at: string;
  scene_count: number;
  object_count: number;
}

// ─── Durable (v2) Project DTOs ──────────────────────────────────────────────
// Typed mirrors of the durable SQLite DTOs (app/schemas). The durable routes
// live under /api/v2/projects/{project_id:uuid} and every item PATCH requires
// the optimistic-concurrency `revision` (409 on stale).

export interface DurableProjectData {
  project_id: string;
  workspace_id: string;
  name: string;
  description: string;
  status: string;
  source_channel_id: string | null;
  production_channel_id: string | null;
  default_output_profile: string | null;
  resume_step: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  revision: number;
}

export interface DurableVideoItem {
  video_item_id: string;
  project_id: string;
  workspace_id: string;
  title: string;
  position: number;
  status: string;
  source_artifact_id: string | null;
  source_channel_id: string | null;
  duration_ms: number | null;
  width: number | null;
  height: number | null;
  fps_num: number | null;
  fps_den: number | null;
  resume_step: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  revision: number;
}

export interface DurableVideoList {
  project_id: string;
  workspace_id: string;
  active_only: boolean;
  videos: DurableVideoItem[];
}

// ─── Durable Project Summary DTOs (S03-T04 read model) ────────────────────
// Typed mirrors of app/schemas ProjectSummaryData/ProjectSummaryListResponse.
// The dashboard collection endpoint is GET /api/v2/projects/summaries — the
// ONLY approved dashboard contract (there is no /api/v2/jobs collection).

export interface ProjectChannelSummary {
  channel_id: string;
  name: string;
  role: string;
  status: string;
}

export interface VideoCountsSummary {
  active: number;
  archived: number;
  total: number;
  completed: number;
  attention: number;
  completion_percent: number;
  by_status: Record<string, number>;
}

export type NextActionCode =
  | "none"
  | "analyze_video"
  | "map_objects"
  | "create_demo"
  | "apply_reskin"
  | "review_work"
  | "export_video"
  | "retry_failed";

export type NextActionBlocker =
  | "qc_unavailable"
  | "output_unavailable"
  | "capability_unavailable";

export interface NextActionSummary {
  code: NextActionCode;
  video_item_id: string | null;
  enabled: boolean;
  blocker: NextActionBlocker | null;
}

export interface ActiveJobSummary {
  job_id: string;
  job_type: string;
  owner_type: string;
  owner_id: string;
  state: string;
  progress: number;
  created_at: string | null;
}

export interface StorageSummary {
  total_bytes: number;
  artifact_count: number;
  ready_count: number;
  missing_count: number;
  trash_count: number;
  unknown_size_count: number;
}

export interface ProjectSummaryData {
  project_id: string;
  workspace_id: string;
  name: string;
  description: string;
  status: string;
  revision: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  source_channel: ProjectChannelSummary | null;
  production_channel: ProjectChannelSummary | null;
  video_counts: VideoCountsSummary;
  next_action: NextActionSummary;
  active_jobs: ActiveJobSummary[];
  active_job_count: number;
  last_activity_at: string | null;
  storage: StorageSummary;
}

export interface ProjectSummaryListResponse {
  workspace_id: string;
  active_only: boolean;
  status: string | null;
  limit: number;
  offset: number;
  total: number;
  has_more: boolean;
  summaries: ProjectSummaryData[];
}

// ─── Durable Channel DTOs (S03-T01 approved contract, CHANNEL_API.md) ─────
// Route family is /api/channels (NOT /api/v2/channels). Roles are exactly
// `source` | `production` — the contract has no `both` role and no
// hard-delete endpoint: archive is the only removal path.

export type DurableChannelRole = "source" | "production";
export type DurableChannelStatus = "active" | "archived";

export interface DurableChannel {
  channel_id: string;
  workspace_id: string;
  name: string;
  role: DurableChannelRole;
  description: string;
  color: string | null;
  avatar_artifact_id: string | null;
  target_language: string | null;
  default_output_profile: string | null;
  status: DurableChannelStatus;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  revision: number;
}

export interface DurableChannelList {
  workspace_id: string;
  active_only: boolean;
  channels: DurableChannel[];
}

export interface DurableChannelCreateInput {
  name: string;
  role: DurableChannelRole;
  description?: string;
  color?: string | null;
  avatar_artifact_id?: string | null;
  target_language?: string | null;
  default_output_profile?: string | null;
}

export interface DurableChannelUpdateInput {
  name?: string | null;
  description?: string | null;
  color?: string | null;
  avatar_artifact_id?: string | null;
  target_language?: string | null;
  default_output_profile?: string | null;
  revision: number;
}

export interface DurableVideoCreateInput {
  title: string;
  source_channel_id?: string | null;
  resume_step?: string | null;
}

export interface DurableVideoUpdateInput {
  title?: string | null;
  source_channel_id?: string | null;
  resume_step?: string | null;
  revision: number;
}

export interface DurableProjectPatch {
  revision: number;
  resume_step?: string | null;
  description?: string | null;
  default_output_profile?: string | null;
  source_channel_id?: string | null;
  production_channel_id?: string | null;
}

/**
 * Strict UUID check — the durable v2 item routes are UUID-constrained
 * (`/api/v2/projects/{project_id:uuid}`). Legacy filesystem project ids
 * (e.g. `2dc14177a212`) must never be sent to the durable endpoint (AC6).
 */
export function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

// ─── API Functions ──────────────────────────────────────────────────────────

export const api = {
  // Projects
  createProject: (name: string) =>
    apiFetch<{ project_id: string }>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  listAllProjects: () =>
    apiFetch<ProjectSummary[]>("/api/projects"),

  getProject: (id: string) =>
    apiFetch<ProjectData>(`/api/projects/${id}`),

  uploadVideo: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/projects/${projectId}/video`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json() as Promise<{ video_path: string }>;
  },

  triggerIngest: (projectId: string) =>
    apiFetch<{ job_id: string }>(`/api/projects/${projectId}/ingest`, {
      method: "POST",
    }),

  getScenes: (projectId: string) =>
    apiFetch<SceneInfo[]>(`/api/projects/${projectId}/scenes`),

  getFrameUrl: (projectId: string, frameIndex: number) =>
    `${API_BASE}/api/projects/${projectId}/frames/${frameIndex}`,

  // Objects
  previewMask: (projectId: string, req: MaskPreviewRequest) =>
    apiFetch<MaskPreviewResponse>(
      `/api/projects/${projectId}/objects/preview-mask`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      },
    ),

  createObject: (projectId: string, obj: { name: string; selection: SelectionInput; scene_id: number }) =>
    apiFetch<{ object_id: string; project: ProjectData }>(`/api/projects/${projectId}/objects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj),
    }),

  propagateObject: (projectId: string, objectId: string) =>
    apiFetch<{ job_id: string }>(
      `/api/projects/${projectId}/objects/${objectId}/propagate`,
      { method: "POST" },
    ),

  getObject: (projectId: string, objectId: string) =>
    apiFetch<TrackedObject>(`/api/projects/${projectId}/objects/${objectId}`),

  getGallery: (projectId: string, objectId: string) =>
    apiFetch<GalleryManifest>(
      `/api/projects/${projectId}/objects/${objectId}/gallery`,
    ),

  uploadReplacement: async (projectId: string, objectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(
      `${API_BASE}/api/projects/${projectId}/objects/${objectId}/replacement`,
      { method: "POST", body: form },
    );
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json() as Promise<{ asset_path: string }>;
  },

  updateReplacementSettings: (
    projectId: string,
    objectId: string,
    settings: Partial<ReplacementConfig>,
  ) =>
    apiFetch<ReplacementConfig>(
      `/api/projects/${projectId}/objects/${objectId}/replacement-settings`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        // Backend expects { replacement_config: {...} }
        body: JSON.stringify({ replacement_config: settings }),
      },
    ),

  // Render
  triggerPreview: (projectId: string) =>
    apiFetch<{ job_id: string }>(`/api/projects/${projectId}/preview`, {
      method: "POST",
    }),

  triggerRender: (projectId: string) =>
    apiFetch<{ job_id: string }>(`/api/projects/${projectId}/render`, {
      method: "POST",
    }),

  // Jobs
  getJob: (jobId: string) => apiFetch<JobInfo>(`/api/jobs/${jobId}`),

  cancelJob: (jobId: string) =>
    apiFetch<{ ok: boolean }>(`/api/jobs/${jobId}/cancel`, {
      method: "POST",
    }),

  // Image URLs (direct links, no fetch)
  getMaskImageUrl: (projectId: string, objectId: string, frameIndex: number) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/masks/${frameIndex}`,

  getCropImageUrl: (projectId: string, objectId: string, frameIndex: number) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/crops/${frameIndex}`,

  getReplacementImageUrl: (projectId: string, objectId: string) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/replacement-image`,

  getInpaintedFrameUrl: (projectId: string, objectId: string, frameIndex: number) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/inpainted/${frameIndex}`,

  getObjectCropUrl: (projectId: string, objectId: string) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/crop`,

  listObjects: (projectId: string) =>
    apiFetch<
      Array<
        TrackedObject & { thumbnail_base64: string }
      >
    >(`/api/projects/${projectId}/objects`),

  clearObjects: (projectId: string) =>
    apiFetch<{ status: string; project: ProjectData }>(
      `/api/projects/${projectId}/objects`,
      { method: "DELETE" },
    ),

  deleteObject: (projectId: string, objectId: string) =>
    apiFetch<{ status: string; project: ProjectData }>(
      `/api/projects/${projectId}/objects/${objectId}`,
      { method: "DELETE" },
    ),

  // ─── Scene Approval ───────────────────────────────────────────────────

  chunkScenes: (projectId: string, threshold?: number) =>
    apiFetch<{ scene_count: number; scenes: SceneDetail[] }>(
      `/api/projects/${projectId}/scenes/chunk?threshold=${threshold ?? 27.0}`,
      { method: "POST" },
    ),

  getSceneDetails: (projectId: string) =>
    apiFetch<SceneDetail[]>(`/api/projects/${projectId}/scenes/details`),

  updateSceneStatus: (
    projectId: string,
    sceneId: number,
    status: "pending" | "draft" | "approved",
    notes?: string,
  ) =>
    apiFetch<{ ok: boolean }>(
      `/api/projects/${projectId}/scenes/${sceneId}/status`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, notes: notes ?? "" }),
      },
    ),

  getSceneAudioUrl: (projectId: string, sceneId: number) =>
    `${API_BASE}/api/projects/${projectId}/scenes/${sceneId}/audio`,

  stitchScenes: (projectId: string) =>
    apiFetch<{ ok: boolean; output_path: string }>(
      `/api/projects/${projectId}/scenes/stitch`,
      { method: "POST" },
    ),

  extractSceneFrames: (projectId: string, sceneId: number, format = "jpg") =>
    apiFetch<{ scene_id: number; frame_count: number; format: string }>(
      `/api/projects/${projectId}/scenes/${sceneId}/extract-frames?format=${format}`,
      { method: "POST" },
    ),

  // ─── Bulk Mapping ────────────────────────────────────────────────────

  applyBulkMapping: (
    projectId: string,
    objectId: string,
    sceneIds: number[],
  ) =>
    apiFetch<{ applied_to: string[]; scene_ids: number[] }>(
      `/api/projects/${projectId}/objects/${objectId}/apply-bulk`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ object_id: objectId, scene_ids: sceneIds }),
      },
    ),

  // ─── Inpainting ──────────────────────────────────────────────────────

  inpaintScene: (projectId: string, sceneId: number) =>
    apiFetch<{ ok: boolean }>(
      `/api/projects/${projectId}/scenes/${sceneId}/inpaint`,
      { method: "POST" },
    ),

  // ─── Sequence Frame URL ─────────────────────────────────────────────

  getSequenceFrameUrl: (projectId: string, objectId: string, index: number) =>
    `${API_BASE}/api/projects/${projectId}/objects/${objectId}/sequence-frame?index=${index}`,

  // ─── Dubbing ────────────────────────────────────────────────────────

  separateAudio: (projectId: string, sceneId: number) =>
    apiFetch<{ vocal_track: string; bgm_track: string }>(
      `/api/projects/${projectId}/dubbing/separate?scene_id=${sceneId}`,
      { method: "POST" },
    ),

  transcribeScene: (
    projectId: string,
    sceneId: number,
    sourceLang?: string,
    whisperModel?: string,
  ) =>
    apiFetch<{ segments: DubbingSegment[]; srt_path: string }>(
      `/api/projects/${projectId}/dubbing/transcribe?scene_id=${sceneId}&source_lang=${sourceLang ?? "vi"}&whisper_model=${whisperModel ?? "base"}`,
      { method: "POST" },
    ),

  translateSubtitles: (
    projectId: string,
    sceneId: number,
    targetLang: string,
    sourceLang?: string,
  ) =>
    apiFetch<{ segments: DubbingSegment[]; srt_path: string }>(
      `/api/projects/${projectId}/dubbing/translate?scene_id=${sceneId}&target_lang=${targetLang}&source_lang=${sourceLang ?? "auto"}`,
      { method: "POST" },
    ),

  generateTts: (
    projectId: string,
    sceneId: number,
    targetLang?: string,
    ttsVoice?: string,
  ) =>
    apiFetch<{ tts_count: number; tts_dir: string }>(
      `/api/projects/${projectId}/dubbing/tts?scene_id=${sceneId}&target_lang=${targetLang ?? "en"}&tts_voice=${ttsVoice ?? "en-US-AriaNeural"}`,
      { method: "POST" },
    ),

  remuxDubbedAudio: (projectId: string, sceneId: number) =>
    apiFetch<{ final_audio: string }>(
      `/api/projects/${projectId}/dubbing/remux?scene_id=${sceneId}`,
      { method: "POST" },
    ),

  fullDubbingPipeline: (projectId: string, config: DubbingConfig) =>
    apiFetch<DubbingResult>(
      `/api/projects/${projectId}/dubbing/full`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      },
    ),

  // ─── Scene Objects ──────────────────────────────────────────────────────

  getSceneObjects: (projectId: string, sceneId: number) =>
    apiFetch<TrackedObject[]>(
      `/api/projects/${projectId}/scenes/${sceneId}/objects`,
    ),

  // ─── Presets ────────────────────────────────────────────────────────────

  savePreset: (projectId: string, name: string, description?: string) =>
    apiFetch<{ ok: boolean; path: string; mapping_count: number }>(
      `/api/projects/${projectId}/presets/save`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description: description ?? "" }),
      },
    ),

  listPresets: (projectId: string) =>
    apiFetch<PresetInfo[]>(
      `/api/projects/${projectId}/presets`,
    ),

  applyPreset: (projectId: string, presetFilename: string) =>
    apiFetch<{ ok: boolean; updated_objects: number }>(
      `/api/projects/${projectId}/presets/${presetFilename}/apply`,
      { method: "POST" },
    ),

  // ─── Character Preset Library (multi-pose templates) ────────────────────

  listCharacterPresets: () =>
    apiFetch<{
      status: string;
      characters: {
        id: string;
        label: string;
        poses: { pose: string; label: string; filename: string; url: string }[];
      }[];
    }>(`/api/projects/presets/characters`),

  getCharacterPresetImageUrl: (setKey: string, pose: string) =>
    `${API_BASE}/api/projects/presets/characters/${setKey}/${pose}/image`,

  applyCharacterPreset: (projectId: string, setKey: string, pose: string) =>
    apiFetch<{
      status: string;
      object_id: string;
      asset_path: string;
      pose: string;
      set_key: string;
    }>(`/api/projects/${projectId}/presets/characters/${setKey}/${pose}/apply`, {
      method: "POST",
    }),

  // ─── Multi-Format Render ────────────────────────────────────────────────

  renderWithFormat: (projectId: string, format: string) =>
    apiFetch<{ job_id: string }>(
      `/api/projects/${projectId}/render?format=${format}`,
      { method: "POST" },
    ),

  // ─── Export ─────────────────────────────────────────────────────────────

  exportProjectZip: (projectId: string) =>
    `/api/projects/${projectId}/export`,

  // ─── Channels ───────────────────────────────────────────────────────────

  createChannel: (name: string, targetLang?: string) =>
    apiFetch<ChannelWorkspace>(
      `/api/projects/channels`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, target_lang: targetLang ?? "en" }),
      },
    ),

  listChannels: () =>
    apiFetch<ChannelWorkspace[]>("/api/projects/channels"),

  getChannelProjects: (channelId: string) =>
    apiFetch<ChannelProject[]>(`/api/projects/channels/${channelId}/projects`),

  deleteChannel: (channelId: string) =>
    apiFetch<{ ok: boolean }>(
      `/api/projects/channels/${channelId}`,
      { method: "DELETE" },
    ),

  updateTaskStatus: (projectId: string, taskStatus: string) =>
    apiFetch<{ ok: boolean }>(
      `/api/projects/${projectId}/task-status`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_status: taskStatus }),
      },
    ),

  assignChannel: (projectId: string, channelId: string) =>
    apiFetch<{ ok: boolean }>(
      `/api/projects/${projectId}/assign-channel?channel_id=${channelId}`,
      { method: "PATCH" },
    ),

  // ─── Performance & Automation ─────────────────────────────────────────

  getGpuInfo: () =>
    apiFetch<GpuInfo>("/api/projects/gpu-info"),

  autoMatchCharacter: (projectId: string, objectId: string) =>
    apiFetch<{ matched: string[]; count: number }>(
      `/api/projects/${projectId}/objects/${objectId}/auto-match`,
      { method: "POST" },
    ),

  cleanupProject: (projectId: string) =>
    apiFetch<{ ok: boolean; files_removed: number; dirs_removed: number; bytes_freed: number }>(
      `/api/projects/${projectId}/cleanup`,
      { method: "POST" },
    ),

  deleteProject: (projectId: string) =>
    apiFetch<{ ok: boolean; deleted: string }>(
      `/api/projects/${projectId}`,
      { method: "DELETE" },
    ),

  autoSegmentObjects: (projectId: string, sceneId = 0) =>
    apiFetch<{
      scene_id: number;
      objects_found: number;
      objects: Array<{
        object_index: number;
        name?: string;
        crop_png_base64?: string;
        bbox: { x: number; y: number; width: number; height: number };
        area: number;
        centroid: { x: number; y: number };
      }>;
    }>(
      `/api/projects/${projectId}/auto-segment-objects?scene_id=${sceneId}`,
      { method: "POST" },
    ),

  // ─── Durable Projects (v2 namespace, UUID-constrained) ─────────────────

  getDurableProject: (projectId: string) =>
    apiFetch<DurableProjectData>(`/api/v2/projects/${projectId}`),

  listDurableProjectVideos: (projectId: string) =>
    apiFetch<DurableVideoList>(`/api/v2/projects/${projectId}/videos`),

  getDurableVideo: (projectId: string, videoId: string) =>
    apiFetch<DurableVideoItem>(`/api/v2/projects/${projectId}/videos/${videoId}`),

  /** Dashboard collection: durable Project summaries (S03-T04 read model).
   * This is the REAL dashboard contract — there is no /api/v2/jobs endpoint. */
  listProjectSummaries: (params?: { limit?: number; offset?: number; status?: string }) =>
    apiFetch<ProjectSummaryListResponse>(`/api/v2/projects/summaries?${new URLSearchParams({
      limit: String(params?.limit ?? 200),
      offset: String(params?.offset ?? 0),
      ...(params?.status ? { status: params.status } : {}),
    }).toString()}`),

  // ─── Durable Channels (approved /api/channels contract — S03-T01) ───────

  listDurableChannels: (params?: { role?: DurableChannelRole; active_only?: boolean }) =>
    apiFetch<DurableChannelList>(`/api/channels?${new URLSearchParams({
      ...(params?.role ? { role: params.role } : {}),
      active_only: String(params?.active_only ?? true),
    }).toString()}`),

  getDurableChannelRoles: () =>
    apiFetch<{ roles: DurableChannelRole[] }>("/api/channels/roles"),

  getDurableChannelStatuses: () =>
    apiFetch<{ statuses: DurableChannelStatus[] }>("/api/channels/statuses"),

  getDurableChannel: (channelId: string) =>
    apiFetch<DurableChannel>(`/api/channels/${channelId}`),

  createDurableChannel: (input: DurableChannelCreateInput) =>
    apiFetch<DurableChannel>("/api/channels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),

  updateDurableChannel: (channelId: string, patch: DurableChannelUpdateInput) =>
    apiFetch<DurableChannel>(`/api/channels/${channelId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),

  archiveDurableChannel: (channelId: string, revision: number) =>
    apiFetch<DurableChannel>(`/api/channels/${channelId}/archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revision }),
    }),

  // ─── Durable Video Items (approved /api/v2/projects/{pid}/videos) ───────

  createDurableVideo: (projectId: string, input: DurableVideoCreateInput) =>
    apiFetch<DurableVideoItem>(`/api/v2/projects/${projectId}/videos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),

  updateDurableVideo: (projectId: string, videoId: string, patch: DurableVideoUpdateInput) =>
    apiFetch<DurableVideoItem>(`/api/v2/projects/${projectId}/videos/${videoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),

  archiveDurableVideo: (projectId: string, videoId: string, revision: number) =>
    apiFetch<DurableVideoItem>(`/api/v2/projects/${projectId}/videos/${videoId}/archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revision }),
    }),

  reorderDurableVideos: (projectId: string, projectRevision: number, videoItemIds: string[]) =>
    apiFetch<DurableVideoList>(`/api/v2/projects/${projectId}/videos/reorder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_revision: projectRevision, video_item_ids: videoItemIds }),
    }),

  updateDurableProject: (projectId: string, patch: DurableProjectPatch) =>
    apiFetch<DurableProjectData>(`/api/v2/projects/${projectId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }),
};

/**
 * Durable PATCH with the required revision/CAS contract (AC5).
 *
 * - Always sends the expected `revision` (fetches it first when unknown).
 * - On 409 (stale revision) refetches the project to obtain the current
 *   revision and retries, up to `maxRetries` times.
 * - Every other failure (and a still-stale retry) propagates — persistence
 *   failures are never swallowed silently.
 *
 * Legacy/non-UUID ids are rejected outright: they must never reach the
 * UUID-constrained durable endpoint (AC6).
 */
export async function patchDurableProject(
  projectId: string,
  patch: Omit<DurableProjectPatch, "revision">,
  revision: number | null,
  maxRetries = 1,
): Promise<DurableProjectData> {
  if (!isUuid(projectId)) {
    throw new Error(`Không thể cập nhật dự án legacy (không phải UUID): ${projectId}`);
  }
  let currentRevision = revision;
  if (currentRevision === null) {
    currentRevision = (await api.getDurableProject(projectId)).revision;
  }
  let attempt = 0;
  for (;;) {
    try {
      return await api.updateDurableProject(projectId, {
        ...patch,
        revision: currentRevision,
      });
    } catch (err) {
      const isConflict = err instanceof Error && /^API 409/.test(err.message);
      if (isConflict && attempt < maxRetries) {
        attempt += 1;
        currentRevision = (await api.getDurableProject(projectId)).revision;
        continue;
      }
      throw err;
    }
  }
}

/**
 * Durable Channel PATCH with the required revision/CAS contract (AC4).
 *
 * A 409 means either a stale revision (refetch the channel, retry once) or a
 * real active-name conflict (rethrow with the actionable backend message).
 * Every other failure propagates — persistence failures are never swallowed.
 */
export async function patchDurableChannel(
  channelId: string,
  patch: Omit<DurableChannelUpdateInput, "revision">,
  revision: number,
  maxRetries = 1,
): Promise<DurableChannel> {
  let currentRevision = revision;
  let attempt = 0;
  for (;;) {
    try {
      return await api.updateDurableChannel(channelId, {
        ...patch,
        revision: currentRevision,
      });
    } catch (err) {
      const isConflict = err instanceof Error && /^API 409/.test(err.message);
      if (isConflict && attempt < maxRetries) {
        attempt += 1;
        currentRevision = (await api.getDurableChannel(channelId)).revision;
        continue;
      }
      throw err;
    }
  }
}

/**
 * Durable Channel archive with the required revision/CAS contract (AC5).
 *
 * A 409 means the expected revision is stale (another writer archived/updated
 * the channel) — refetch the channel's current revision and retry once. The
 * backend treats an already-archived channel as an idempotent 200 no-op, so a
 * conflict here always means a stale revision, never a duplicate archive.
 * Every other failure propagates — persistence failures are never swallowed.
 */
export async function archiveDurableChannelCas(
  channelId: string,
  revision: number,
  maxRetries = 1,
): Promise<DurableChannel> {
  let currentRevision = revision;
  let attempt = 0;
  for (;;) {
    try {
      return await api.archiveDurableChannel(channelId, currentRevision);
    } catch (err) {
      const isConflict = err instanceof Error && /^API 409/.test(err.message);
      if (isConflict && attempt < maxRetries) {
        attempt += 1;
        currentRevision = (await api.getDurableChannel(channelId)).revision;
        continue;
      }
      throw err;
    }
  }
}

/**
 * Durable Video Item PATCH with the required revision/CAS contract (AC4).
 * A 409 refetches the item's current revision and retries once; a still-
 * stale or genuine conflict (422 channel reference, 404) propagates.
 */
export async function patchDurableVideo(
  projectId: string,
  videoId: string,
  patch: Omit<DurableVideoUpdateInput, "revision">,
  revision: number,
  maxRetries = 1,
): Promise<DurableVideoItem> {
  let currentRevision = revision;
  let attempt = 0;
  for (;;) {
    try {
      return await api.updateDurableVideo(projectId, videoId, {
        ...patch,
        revision: currentRevision,
      });
    } catch (err) {
      const isConflict = err instanceof Error && /^API 409/.test(err.message);
      if (isConflict && attempt < maxRetries) {
        attempt += 1;
        currentRevision = (await api.getDurableVideo(projectId, videoId)).revision;
        continue;
      }
      throw err;
    }
  }
}
