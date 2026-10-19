"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ImageOff,
  Lock,
  RefreshCw,
  Send,
  X,
} from "lucide-react";

// ─── Durable Character Library API types (S06-T01 contract) ──────────────────

interface AssetData {
  id: string;
  pack_version_id: string;
  workspace_id: string;
  pose_slot: string;
  artifact_id: string;
  created_at: string;
  updated_at: string;
}

interface PackVersionData {
  id: string;
  character_id: string;
  workspace_id: string;
  version: number;
  status: string;
  validation_json: string | null;
  published_at: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  assets: AssetData[];
}

interface CharacterData {
  id: string;
  workspace_id: string;
  name: string;
  code: string;
  character_type: string;
  symmetry: string;
  status: string;
  default_version_id: string | null;
  description: string | null;
  revision: number;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

interface CharacterListResponse {
  workspace_id: string;
  limit: number;
  offset: number;
  total: number;
  characters: CharacterData[];
}

// ─── Core pose slot contract (matches backend CORE_POSE_SLOTS) ───────────────

const CORE_SLOTS: { slot: string; label: string; hint: string }[] = [
  { slot: "front", label: "Mặt trước", hint: "Front" },
  { slot: "three_quarter", label: "3/4", hint: "Three-quarter" },
  { slot: "side", label: "Nghiêng", hint: "Side" },
  { slot: "back", label: "Sau lưng", hint: "Back" },
  { slot: "sitting", label: "Ngồi", hint: "Sitting" },
  { slot: "walking", label: "Đi bộ", hint: "Walking" },
];

const STATUS_LABEL: Record<string, string> = {
  draft: "Bản nháp",
  validating: "Đang kiểm định",
  ready: "Sẵn sàng",
  published: "Đã xuất bản",
  archived: "Đã lưu trữ",
};

function poseImageUrl(characterId: string, version: number, slot: string): string {
  return `/api/v2/characters/${characterId}/versions/${version}/assets/${slot}/image`;
}

export default function CharactersPage() {
  const [characters, setCharacters] = useState<CharacterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selectedChar, setSelectedChar] = useState<CharacterData | null>(null);
  const [versions, setVersions] = useState<PackVersionData[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [activeVersion, setActiveVersion] = useState<PackVersionData | null>(null);

  const [confirmPublish, setConfirmPublish] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);

  const [attachSlot, setAttachSlot] = useState<string | null>(null);
  const [attachArtifactId, setAttachArtifactId] = useState("");
  const [attaching, setAttaching] = useState(false);
  const [attachError, setAttachError] = useState<string | null>(null);

  // ── Character list ──────────────────────────────────────────────────────────

  const fetchCharacters = async () => {
    setError(null);
    try {
      const res = await fetch("/api/v2/characters");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: CharacterListResponse = await res.json();
      setCharacters(data.characters || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải danh sách nhân vật");
    } finally {
      setLoading(false);
    }
  };

  const loadCharacters = async () => {
    setLoading(true);
    await fetchCharacters();
  };

  useEffect(() => {
    // Initial load: all state updates happen after the first await, so no
    // synchronous setState inside the effect body (react-hooks rule).
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v2/characters");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data: CharacterListResponse = await res.json();
        if (!cancelled) setCharacters(data.characters || []);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Không thể tải danh sách nhân vật");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Pack versions of the selected character ────────────────────────────────

  const loadVersions = async (characterId: string) => {
    setVersionsLoading(true);
    setVersionsError(null);
    setActiveVersion(null);
    try {
      const res = await fetch(`/api/v2/characters/${characterId}/versions`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: PackVersionData[] = await res.json();
      setVersions(data);
      // Default to the latest draft (or the latest version if none is draft).
      const draft = [...data].reverse().find((v) => v.status !== "published");
      setActiveVersion(draft ?? data[data.length - 1] ?? null);
    } catch (err) {
      setVersionsError(err instanceof Error ? err.message : "Không thể tải các phiên bản");
    } finally {
      setVersionsLoading(false);
    }
  };

  const openCharacter = (char: CharacterData) => {
    setSelectedChar(char);
    setPublishError(null);
    setAttachError(null);
    setConfirmPublish(false);
    void loadVersions(char.id);
  };

  const closeCharacter = () => {
    setSelectedChar(null);
    setVersions([]);
    setActiveVersion(null);
    setConfirmPublish(false);
  };

  // ── Completeness of the active version ──────────────────────────────────────

  const missingSlots = useMemo(() => {
    if (!activeVersion) return CORE_SLOTS;
    const present = new Set(activeVersion.assets.map((a) => a.pose_slot));
    return CORE_SLOTS.filter((s) => !present.has(s.slot));
  }, [activeVersion]);

  const isComplete = missingSlots.length === 0;
  const isPublished = activeVersion?.status === "published";

  // ── Publish (CAS revision handling) ─────────────────────────────────────────

  const handlePublish = async () => {
    if (!selectedChar || !activeVersion) return;
    setPublishing(true);
    setPublishError(null);
    try {
      const res = await fetch(
        `/api/v2/characters/${selectedChar.id}/versions/${activeVersion.version}/publish`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ revision: activeVersion.revision }),
        },
      );
      if (res.status === 409) {
        // CAS conflict: the version changed server-side — reload fresh state.
        setPublishError("Phiên bản đã thay đổi ở máy chủ. Đang tải lại trạng thái mới nhất...");
        await loadVersions(selectedChar.id);
        return;
      }
      if (res.status === 422) {
        const detail = await res.json().catch(() => null);
        const missing = detail?.detail?.missing_slots ?? [];
        setPublishError(
          missing.length > 0
            ? `Không thể xuất bản: còn thiếu pose slot: ${missing.join(", ")}`
            : "Không thể xuất bản: pack chưa đạt kiểm định.",
        );
        return;
      }
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail ?? `HTTP ${res.status}`);
      }
      setConfirmPublish(false);
      await loadVersions(selectedChar.id);
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : "Xuất bản thất bại");
    } finally {
      setPublishing(false);
    }
  };

  // ── Attach an asset to an empty pose slot (disabled when published) ─────────

  const handleAttach = async (slot: string) => {
    if (!activeVersion || !attachArtifactId.trim()) return;
    setAttaching(true);
    setAttachError(null);
    try {
      const res = await fetch(`/api/v2/versions/${activeVersion.id}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pose_slot: slot, artifact_id: attachArtifactId.trim() }),
      });
      if (res.status === 409) {
        setAttachError("Version đã xuất bản — không thể thay đổi asset (immutable).");
        return;
      }
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail ?? `HTTP ${res.status}`);
      }
      setAttachSlot(null);
      setAttachArtifactId("");
      if (selectedChar) {
        await loadVersions(selectedChar.id);
      }
    } catch (err) {
      setAttachError(err instanceof Error ? err.message : "Gắn asset thất bại");
    } finally {
      setAttaching(false);
    }
  };

  // ── Filters ─────────────────────────────────────────────────────────────────

  const filtered = characters.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.code.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || c.character_type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-display text-2xl font-semibold">Thư viện nhân vật</h2>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Duyệt bộ nhân vật, xem kiểm định 6 tư thế và xuất bản pack version.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-[var(--danger)] bg-[var(--surface-900)] p-4">
          <div className="flex items-center gap-2 text-sm text-[var(--danger)]">
            <AlertTriangle size={16} />
            <span>Không thể tải thư viện nhân vật ({error})</span>
          </div>
          <button
            onClick={() => void loadCharacters()}
            className="mt-3 flex min-h-10 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-4 text-sm text-[var(--text-primary)] hover:bg-[var(--surface-700)]"
          >
            <RefreshCw size={16} />
            Thử lại
          </button>
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            Tải lại danh sách nhân vật từ API durable characters.
          </p>
        </div>
      )}

      {/* Filter bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Tìm kiếm theo tên hoặc mã..."
          className="flex-1 rounded-lg border border-[var(--surface-700)] bg-[var(--surface-900)] px-4 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-500)]"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-[var(--surface-700)] bg-[var(--surface-900)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-500)]"
        >
          <option value="all">Tất cả loại</option>
          <option value="character">Nhân vật</option>
          <option value="prop">Đạo cụ</option>
          <option value="other">Khác</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-6">
          {[1, 2].map((n) => (
            <div key={n} className="h-64 animate-pulse rounded-xl bg-[var(--surface-850)]" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--surface-700)] bg-[var(--surface-900)] p-10 text-center">
          <ImageOff className="mx-auto text-[var(--text-muted)]" />
          <h3 className="mt-4 font-display text-lg font-semibold">Chưa có nhân vật</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            Thư viện hiện chưa có bộ nhân vật phù hợp bộ lọc.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {filtered.map((character) => (
            <section
              key={character.id}
              className="rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-5"
            >
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-display text-lg font-semibold">{character.name}</h3>
                  <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">{character.code}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full border border-[var(--surface-700)] bg-[var(--surface-850)] px-2.5 py-0.5 text-xs text-[var(--text-secondary)]">
                    {STATUS_LABEL[character.status] ?? character.status}
                  </span>
                  <button
                    onClick={() => openCharacter(character)}
                    className="min-h-10 rounded-lg bg-[var(--primary-600)] px-4 text-sm font-semibold text-white hover:bg-[var(--primary-500)]"
                  >
                    Xem pack &amp; xuất bản
                  </button>
                </div>
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Mở bảng kiểm định 6 pose slot và thao tác xuất bản version của nhân vật này.
              </p>
            </section>
          ))}
        </div>
      )}

      {/* ── Pack Review Panel ─────────────────────────────────────────────────── */}
      {selectedChar && (
        <div className="mt-8 rounded-xl border border-[var(--primary-500)/30] bg-[var(--surface-900)] p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-lg font-semibold">
                Pack Review — {selectedChar.name}
              </h3>
              <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">{selectedChar.code}</p>
            </div>
            <button
              onClick={closeCharacter}
              className="flex min-h-10 items-center gap-1 rounded-lg bg-[var(--surface-800)] px-3 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-700)]"
            >
              <X size={16} />
              Đóng
            </button>
          </div>
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            Đóng bảng review, giữ nguyên trạng thái các version đã tải.
          </p>

          {versionsLoading && (
            <div className="mt-6 h-48 animate-pulse rounded-xl bg-[var(--surface-850)]" />
          )}
          {versionsError && (
            <div className="mt-6 rounded-xl border border-[var(--danger)] bg-[var(--surface-850)] p-4 text-sm text-[var(--danger)]">
              Không thể tải các version: {versionsError}
            </div>
          )}

          {!versionsLoading && !versionsError && (
            <>
              {/* Version selector */}
              {versions.length > 0 && (
                <div className="mt-6 flex flex-wrap gap-2">
                  {versions.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => {
                        setActiveVersion(v);
                        setPublishError(null);
                        setConfirmPublish(false);
                      }}
                      className={`min-h-10 rounded-lg border px-4 text-sm font-medium ${
                        activeVersion?.id === v.id
                          ? "border-[var(--primary-500)] bg-[var(--primary-600)/20] text-[var(--primary-300)]"
                          : "border-[var(--surface-700)] bg-[var(--surface-850)] text-[var(--text-secondary)] hover:bg-[var(--surface-800)]"
                      }`}
                    >
                      v{v.version} · {STATUS_LABEL[v.status] ?? v.status}
                    </button>
                  ))}
                </div>
              )}
              {versions.length === 0 && (
                <p className="mt-6 text-sm text-[var(--text-muted)]">
                  Nhân vật chưa có pack version nào.
                </p>
              )}

              {activeVersion && (
                <div className="mt-6 space-y-6">
                  {/* 6 core pose slots */}
                  <div>
                    <span className="block text-sm font-medium">6 Core Pose Slots</span>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">
                      Pack version v{activeVersion.version} cần đủ 6 tư thế bắt buộc trước khi xuất bản.
                    </p>
                    <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6">
                      {CORE_SLOTS.map(({ slot, label, hint }) => {
                        const asset = activeVersion.assets.find((a) => a.pose_slot === slot);
                        return (
                          <div
                            key={slot}
                            className="overflow-hidden rounded-lg border border-[var(--surface-700)] bg-[var(--surface-850)]"
                          >
                            <div className="aspect-square overflow-hidden bg-black/40">
                              {asset ? (
                                <img
                                  src={poseImageUrl(selectedChar.id, activeVersion.version, slot)}
                                  alt={`${label} (${hint})`}
                                  className="h-full w-full object-contain"
                                />
                              ) : (
                                <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-[var(--text-muted)]">
                                  <ImageOff size={20} />
                                  <span className="text-xs">Chưa có asset</span>
                                </div>
                              )}
                            </div>
                            <div className="space-y-2 p-3">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-semibold text-[var(--text-primary)]">{label}</span>
                                {asset ? (
                                  <span className="rounded-full border border-[var(--success)]/30 bg-[var(--success)]/10 px-2 py-0.5 text-[10px] font-medium text-[var(--success)]">
                                    ✓ Có
                                  </span>
                                ) : (
                                  <span className="rounded-full border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-2 py-0.5 text-[10px] font-medium text-[var(--danger)]">
                                    Thiếu
                                  </span>
                                )}
                              </div>
                              <p className="font-mono text-[10px] text-[var(--text-muted)]">{hint}</p>

                              {/* Attach control — disabled on published (immutable) */}
                              {!asset && !isPublished && (
                                <div className="space-y-1 pt-1">
                                  <div className="flex gap-1">
                                    <input
                                      type="text"
                                      value={attachSlot === slot ? attachArtifactId : ""}
                                      onChange={(e) => {
                                        setAttachSlot(slot);
                                        setAttachArtifactId(e.target.value);
                                        setAttachError(null);
                                      }}
                                      placeholder="artifact_id"
                                      className="w-full min-w-0 flex-1 rounded-md border border-[var(--surface-700)] bg-[var(--surface-900)] px-2 py-1.5 font-mono text-[10px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--primary-500)]"
                                    />
                                    <button
                                      onClick={() => void handleAttach(slot)}
                                      disabled={attaching || !attachArtifactId.trim()}
                                      className="flex min-h-8 items-center gap-1 rounded-md bg-[var(--primary-600)] px-2 text-[10px] font-semibold text-white hover:bg-[var(--primary-500)] disabled:opacity-50"
                                    >
                                      <Send size={12} />
                                      Gắn
                                    </button>
                                  </div>
                                  <p className="text-[10px] text-[var(--text-muted)]">
                                    Nhập artifact_id sẵn sàng để gắn vào slot này.
                                  </p>
                                </div>
                              )}
                              {asset && isPublished && (
                                <p className="text-[10px] text-[var(--success)]">
                                  Đã khóa bởi immutable version.
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Completeness banner */}
                  <div
                    className={`flex items-center gap-3 rounded-xl border p-4 ${
                      isComplete
                        ? "border-[var(--success)]/30 bg-[var(--success)]/10"
                        : "border-amber-500/30 bg-amber-500/10"
                    }`}
                  >
                    {isComplete ? (
                      <CheckCircle2 className="shrink-0 text-[var(--success)]" size={20} />
                    ) : (
                      <AlertTriangle className="shrink-0 text-amber-400" size={20} />
                    )}
                    <div>
                      <p
                        className={`text-sm font-semibold ${
                          isComplete ? "text-[var(--success)]" : "text-amber-400"
                        }`}
                      >
                        {isComplete
                          ? "Publish Ready — pack version đạt đủ 6 pose slot."
                          : `Missing ${missingSlots.length} pose slot${missingSlots.length > 1 ? "s" : ""} — ${missingSlots
                              .map((s) => s.slot)
                              .join(", ")}`}
                      </p>
                      <p className="mt-1 text-xs text-[var(--text-muted)]">
                        {isComplete
                          ? "Có thể xuất bản pack version này ngay bây giờ."
                          : "Gắn đủ asset cho các slot còn thiếu trước khi xuất bản."}
                      </p>
                    </div>
                  </div>

                  {/* Immutable badge / Publish action */}
                  <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[var(--surface-800)] pt-5">
                    {isPublished ? (
                      <span className="inline-flex items-center gap-2 rounded-lg border border-[var(--primary-500)]/40 bg-[var(--primary-600)]/15 px-4 py-2.5 text-sm font-semibold text-[var(--primary-300)]">
                        <Lock size={16} />
                        Version v{activeVersion.version} đã xuất bản (Immutable)
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--text-muted)]">
                        CAS revision hiện tại: <span className="font-mono">r{activeVersion.revision}</span>
                      </span>
                    )}

                    {!isPublished && (
                      <div className="flex flex-col items-end gap-1">
                        <button
                          onClick={() => setConfirmPublish(true)}
                          disabled={!isComplete || publishing}
                          className={`min-h-11 rounded-lg px-5 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-40 ${
                            isComplete
                              ? "bg-[var(--success-strong)] hover:brightness-110"
                              : "bg-[var(--surface-700)]"
                          }`}
                        >
                          {publishing ? "Đang xuất bản..." : `Xuất Bản Pack Version v${activeVersion.version}`}
                        </button>
                        <p className="text-[11px] text-[var(--text-muted)]">
                          Khóa pack version và không thể sửa asset sau khi xuất bản.
                        </p>
                      </div>
                    )}
                  </div>

                  {publishError && (
                    <div className="rounded-xl border border-[var(--danger)] bg-[var(--danger)]/10 p-3 text-sm text-[var(--danger)]">
                      {publishError}
                    </div>
                  )}
                  {attachError && (
                    <div className="rounded-xl border border-[var(--danger)] bg-[var(--danger)]/10 p-3 text-sm text-[var(--danger)]">
                      {attachError}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Publish confirmation dialog */}
          {confirmPublish && activeVersion && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
              <div className="w-full max-w-md rounded-xl border border-[var(--surface-700)] bg-[var(--surface-900)] p-6 shadow-2xl">
                <h4 className="font-display text-lg font-semibold">Xác nhận xuất bản</h4>
                <p className="mt-2 text-sm text-[var(--text-secondary)]">
                  Xuất bản <span className="font-semibold text-[var(--text-primary)]">{selectedChar.name}</span> —
                  pack version <span className="font-mono">v{activeVersion.version}</span>?
                </p>
                <p className="mt-3 rounded-lg bg-[var(--surface-850)] p-3 text-xs text-[var(--text-muted)]">
                  Sau khi xuất bản, version trở thành <span className="font-semibold text-[var(--primary-300)]">immutable</span>:
                  không thể gắn, thay thế hay xóa asset, và không thể xuất bản lại.
                </p>
                {publishError && (
                  <p className="mt-3 text-sm text-[var(--danger)]">{publishError}</p>
                )}
                <div className="mt-5 flex justify-end gap-2">
                  <button
                    onClick={() => setConfirmPublish(false)}
                    disabled={publishing}
                    className="min-h-10 rounded-lg bg-[var(--surface-800)] px-4 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-700)] disabled:opacity-50"
                  >
                    Hủy
                  </button>
                  <button
                    onClick={() => void handlePublish()}
                    disabled={publishing}
                    className="min-h-10 rounded-lg bg-[var(--success-strong)] px-4 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50"
                  >
                    {publishing ? "Đang xuất bản..." : "Xác nhận xuất bản"}
                  </button>
                </div>
                <p className="mt-2 text-right text-[10px] text-[var(--text-muted)]">
                  CAS revision r{activeVersion.revision} sẽ được gửi kèm để tránh ghi đè.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
