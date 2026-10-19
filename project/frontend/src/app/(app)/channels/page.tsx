"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Archive,
  Check,
  Pencil,
  Plus,
  Radio,
  RefreshCw,
  X,
} from "lucide-react";
import {
  api,
  archiveDurableChannelCas,
  patchDurableChannel,
  type DurableChannel,
  type DurableChannelRole,
} from "@/lib/api";

// Approved contract (CHANNEL_API.md §3): role is exactly source | production.
// There is NO `both` role and NO /api/v2/channels endpoint.
const APPROVED_ROLES: { value: DurableChannelRole; label: string; hint: string }[] = [
  {
    value: "source",
    label: "Kênh Nguồn",
    hint: "Nhóm các video nguồn đầu vào của chuỗi nội dung.",
  },
  {
    value: "production",
    label: "Kênh Sản Xuất",
    hint: "Nhóm các phiên bản đầu ra đã xử lý của chuỗi nội dung.",
  },
];

const ROLE_BADGE: Record<DurableChannelRole, { label: string; className: string }> = {
  source: {
    label: "Nguồn",
    className: "border border-cyan-500/20 bg-cyan-500/10 text-cyan-400",
  },
  production: {
    label: "Sản xuất",
    className: "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
  },
};

const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  active: {
    label: "Đang hoạt động",
    className: "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
  },
  archived: {
    label: "Đã lưu trữ",
    className: "border border-zinc-500/20 bg-zinc-500/10 text-zinc-400",
  },
};

const date = (value: string) =>
  new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));

function errorDetail(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

/** Status filter — the explicit Active / Archived / All visibility control. */
type ChannelFilter = "active" | "archived" | "all";

const FILTER_OPTIONS: { value: ChannelFilter; label: string; hint: string }[] = [
  { value: "active", label: "Đang hoạt động", hint: "Chỉ kênh chưa lưu trữ (active_only=true)" },
  { value: "archived", label: "Đã lưu trữ", hint: "Chỉ kênh đã lưu trữ (active_only=false)" },
  { value: "all", label: "Tất cả", hint: "Cả kênh hoạt động và đã lưu trữ (active_only=false)" },
];

export default function ChannelsPage() {
  const queryClient = useQueryClient();
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [selected, setSelected] = useState<DurableChannel | null>(null);
  const [name, setName] = useState("");
  const [role, setRole] = useState<DurableChannelRole>("source");
  const [language, setLanguage] = useState("vi");
  const [description, setDescription] = useState("");
  const [validation, setValidation] = useState("");
  const [filter, setFilter] = useState<ChannelFilter>("active");

  const query = useQuery({
    // The filter is part of the cache key — switching tabs refetches with the
    // correct visibility. "Archived"/"All" request the full list through
    // active_only=false; "Active" keeps the default active_only=true.
    queryKey: ["durable-channels", filter],
    queryFn: () =>
      api.listDurableChannels({ active_only: filter === "active" }),
  });
  // Discovery endpoints — the exact approved role/status sets from the API.
  const rolesQuery = useQuery({
    queryKey: ["durable-channel-roles"],
    queryFn: () => api.getDurableChannelRoles(),
    staleTime: 60_000,
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["durable-channels"] });
  };

  const create = useMutation({
    mutationFn: () =>
      api.createDurableChannel({
        name: name.trim(),
        role,
        target_language: language || null,
        description: description.trim(),
      }),
    onSuccess: async () => {
      await invalidate();
      resetForm();
    },
  });

  const update = useMutation({
    mutationFn: () =>
      patchDurableChannel(
        selected!.channel_id,
        {
          name: name.trim(),
          description: description.trim(),
          target_language: language || null,
        },
        selected!.revision,
      ),
    onSuccess: async () => {
      await invalidate();
      resetForm();
    },
  });

  const archive = useMutation({
    mutationFn: (channel: DurableChannel) => archiveDurableChannelCas(channel.channel_id, channel.revision),
    onSuccess: async () => {
      await invalidate();
      if (selected?.channel_id === archive.variables?.channel_id) {
        setSelected(null);
        setFormMode(null);
      }
    },
  });

  const resetForm = () => {
    setFormMode(null);
    setSelected(null);
    setName("");
    setRole("source");
    setLanguage("vi");
    setDescription("");
    setValidation("");
  };

  const openCreate = () => {
    setSelected(null);
    setName("");
    setRole("source");
    setLanguage("vi");
    setDescription("");
    setValidation("");
    setFormMode("create");
  };

  const openEdit = (channel: DurableChannel) => {
    setSelected(channel);
    setName(channel.name);
    setLanguage(channel.target_language ?? "vi");
    setDescription(channel.description ?? "");
    setValidation("");
    setFormMode("edit");
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) {
      setValidation("Vui lòng nhập tên kênh (1–200 ký tự).");
      return;
    }
    setValidation("");
    if (formMode === "edit" && selected) update.mutate();
    else create.mutate();
  };

  const requestArchive = (channel: DurableChannel) => {
    if (!confirm(`Lưu trữ kênh "${channel.name}"? Kênh đã lưu trữ không còn xuất hiện trong danh sách hoạt động.`)) return;
    archive.mutate(channel);
  };

  const activeMutation = create.isPending || update.isPending || archive.isPending;
  const error = query.isError ? "Không thể tải danh sách kênh từ backend durable." : create.error ? `Không thể tạo kênh: ${errorDetail(create.error)}` : update.error ? `Không thể cập nhật kênh: ${errorDetail(update.error)}` : archive.error ? `Không thể lưu trữ kênh: ${errorDetail(archive.error)}` : null;

  // Truthful visibility: the backend applies active_only; the "Đã lưu trữ"
  // tab narrows the full (active_only=false) list to archived rows client-side.
  const allChannels = query.data?.channels ?? [];
  const visibleChannels =
    filter === "archived" ? allChannels.filter((c) => c.status === "archived") : allChannels;

  return (
    <div className="flex min-h-[calc(100vh-4rem)]">
      <div className="min-w-0 flex-1 p-6 lg:p-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 className="font-display text-2xl font-semibold">Kênh</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Quản lý kênh nguồn và kênh sản xuất (chỉ hai vai trò được phê duyệt: <code className="font-mono">source</code> · <code className="font-mono">production</code>).
            </p>
          </div>
          <button
            type="button"
            onClick={openCreate}
            disabled={activeMutation}
            className="flex min-h-10 items-center gap-2 rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white hover:bg-[var(--primary-600)] disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
            title="Tạo kênh nguồn hoặc kênh sản xuất mới"
          >
            <Plus size={17} aria-hidden="true" />
            Tạo kênh
          </button>
        </div>

        {/* Explicit Active / Archived / All visibility filter */}
        <div className="mb-6">
          <div
            role="group"
            aria-label="Lọc trạng thái kênh"
            className="inline-flex flex-wrap gap-1 rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-1"
          >
            {FILTER_OPTIONS.map((option) => {
              const active = filter === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setFilter(option.value)}
                  aria-pressed={active}
                  className={`inline-flex min-h-9 items-center rounded-lg px-3.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)] ${
                    active
                      ? "bg-[var(--primary-700)] text-white"
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-800)] hover:text-[var(--text-primary)]"
                  }`}
                  title={option.hint}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-[11px] text-[var(--text-muted)]">
            {FILTER_OPTIONS.find((o) => o.value === filter)?.hint} — kênh đã lưu trữ chỉ hiển thị khi chọn{" "}
            &quot;Đã lưu trữ&quot; hoặc &quot;Tất cả&quot; và không thể sửa / lưu trữ lại.
          </p>
        </div>

        {/* Mutation/conflict errors — visible, never silent */}
        {error && (
          <div
            role="alert"
            className="mb-6 flex flex-wrap items-center gap-3 rounded-xl border border-[var(--danger)] bg-[var(--surface-900)] p-4 text-sm text-[var(--danger)]"
          >
            <AlertCircle size={18} aria-hidden="true" />
            <span className="min-w-0 flex-1">{error}</span>
            {query.isError && (
              <button
                type="button"
                onClick={() => void query.refetch()}
                className="inline-flex min-h-9 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-3 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--surface-700)]"
              >
                <RefreshCw size={14} aria-hidden="true" />
                Thử lại
              </button>
            )}
          </div>
        )}

        {/* Create / Edit form */}
        {formMode && (
          <form onSubmit={submit} className="mb-6 rounded-xl border border-[var(--surface-700)] bg-[var(--surface-900)] p-4">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display font-semibold">{formMode === "edit" ? `Chỉnh sửa kênh: ${selected?.name ?? ""}` : "Kênh mới"}</h3>
              <button
                type="button"
                aria-label="Đóng biểu mẫu"
                onClick={resetForm}
                className="grid size-8 place-items-center rounded-lg hover:bg-[var(--surface-800)]"
              >
                <X size={17} />
              </button>
            </div>

            {formMode === "create" && (
              <fieldset className="mb-4">
                <legend className="mb-2 text-sm font-medium text-[var(--text-secondary)]">Vai trò kênh</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {APPROVED_ROLES.map((option) => {
                    const active = role === option.value;
                    return (
                      <label
                        key={option.value}
                        className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors focus-within:ring-2 focus-within:ring-[var(--primary-300)] ${
                          active ? "border-[var(--primary-400)] bg-[var(--surface-800)]" : "border-[var(--surface-700)] hover:bg-[var(--surface-850)]"
                        }`}
                      >
                        <input
                          type="radio"
                          name="channel-role"
                          value={option.value}
                          checked={active}
                          onChange={() => setRole(option.value)}
                          className="mt-0.5 accent-[var(--primary-500)]"
                        />
                        <span>
                          <span className="block text-sm font-semibold text-[var(--text-primary)]">{option.label}</span>
                          <span className="mt-0.5 block text-[11px] text-[var(--text-muted)]">{option.hint}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            )}

            <div className="grid gap-4 sm:grid-cols-[1fr_10rem_auto]">
              <label className="text-sm text-[var(--text-secondary)]">
                Tên kênh
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={200}
                  className="mt-1 min-h-10 w-full rounded-lg border border-[var(--surface-700)] bg-[var(--surface-950)] px-3 text-[var(--text-primary)]"
                />
              </label>
              <label className="text-sm text-[var(--text-secondary)]">
                Ngôn ngữ
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="mt-1 min-h-10 w-full rounded-lg border border-[var(--surface-700)] bg-[var(--surface-950)] px-3"
                >
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">Tiếng Anh</option>
                </select>
              </label>
              <button
                type="submit"
                disabled={activeMutation}
                className="min-h-10 self-end rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              >
                {create.isPending || update.isPending ? "Đang lưu..." : formMode === "edit" ? "Lưu thay đổi" : "Lưu kênh"}
              </button>
            </div>
            <label className="mt-3 block text-sm text-[var(--text-secondary)]">
              Mô tả
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded-lg border border-[var(--surface-700)] bg-[var(--surface-950)] px-3 text-[var(--text-primary)]"
              />
            </label>
            {validation && <p className="mt-2 text-sm text-[var(--danger)]">{validation}</p>}
            <p className="mt-3 text-[11px] text-[var(--text-muted)]">
              {formMode === "edit"
                ? "Cập nhật dùng khóa phiên bản (revision) — nếu có người khác vừa sửa, hệ thống tự tải lại và thử lại một lần; xung đột tên vẫn hiện rõ lỗi."
                : "Tên kênh phải duy nhất trong cùng vai trò (không phân biệt hoa thường). Kênh đã lưu trữ có thể đặt lại tên cũ."}
            </p>
          </form>
        )}

        {query.isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true" aria-label="Đang tải danh sách kênh">
            {[1, 2, 3].map((n) => <div key={n} className="h-44 animate-pulse rounded-xl bg-[var(--surface-850)]" />)}
          </div>
        )}

        {!query.isLoading && query.data && visibleChannels.length === 0 && (
          <div className="rounded-xl border border-dashed border-[var(--surface-700)] bg-[var(--surface-900)] p-10 text-center">
            <Radio className="mx-auto text-[var(--accent-300)]" size={32} aria-hidden="true" />
            <h3 className="mt-4 font-display text-lg font-semibold">
              {filter === "archived" ? "Không có kênh đã lưu trữ" : "Chưa có kênh nào"}
            </h3>
            <p className="mx-auto mt-2 max-w-lg text-sm text-[var(--text-muted)]">
              {filter === "archived"
                ? "Kênh đã lưu trữ sẽ xuất hiện ở đây. Lưu trữ một kênh đang hoạt động để xem nó trong mục này."
                : "Tạo kênh nguồn để nhóm video đầu vào, hoặc kênh sản xuất để nhóm các phiên bản đầu ra."}
            </p>
            {filter !== "archived" && (
              <button
                type="button"
                onClick={openCreate}
                className="mt-5 min-h-10 rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white hover:bg-[var(--primary-600)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              >
                Tạo kênh
              </button>
            )}
          </div>
        )}

        {query.data && visibleChannels.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {visibleChannels.map((channel) => {
              const roleBadge = ROLE_BADGE[channel.role] ?? { label: channel.role, className: "bg-[var(--surface-800)] text-[var(--text-secondary)]" };
              const statusBadge = STATUS_BADGE[channel.status] ?? { label: channel.status, className: "bg-[var(--surface-800)] text-[var(--text-secondary)]" };
              const archived = channel.status === "archived";
              return (
                <article
                  key={channel.channel_id}
                  className={`flex min-h-44 flex-col rounded-xl border bg-[var(--surface-900)] p-5 ${
                    selected?.channel_id === channel.channel_id ? "border-[var(--primary-400)]" : "border-[var(--surface-800)]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-[var(--surface-800)] text-[var(--accent-300)]">
                      <Radio size={20} aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <h3 className="truncate font-display font-semibold text-[var(--text-primary)]">{channel.name}</h3>
                      <p className="truncate font-mono text-xs text-[var(--text-muted)]">{channel.channel_id}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    <span className={`rounded-full px-2.5 py-1 ${roleBadge.className}`} title={`Vai trò: ${channel.role}`}>
                      {roleBadge.label}
                    </span>
                    <span className={`rounded-full px-2.5 py-1 ${statusBadge.className}`} title={`Trạng thái: ${channel.status}`}>
                      {statusBadge.label}
                    </span>
                    {channel.target_language && (
                      <span className="rounded-full bg-[var(--surface-800)] px-2.5 py-1 text-[var(--text-secondary)]">
                        Ngôn ngữ: {channel.target_language === "vi" ? "Tiếng Việt" : channel.target_language}
                      </span>
                    )}
                  </div>
                  {channel.description && (
                    <p className="mt-3 line-clamp-2 text-xs text-[var(--text-muted)]">{channel.description}</p>
                  )}
                  <p className="mt-3 text-[11px] text-[var(--text-muted)]">Tạo ngày {date(channel.created_at)}</p>
                  <div className="mt-auto flex items-center gap-2 border-t border-[var(--surface-800)] pt-3">
                    <button
                      type="button"
                      onClick={() => openEdit(channel)}
                      disabled={archived || activeMutation}
                      className="inline-flex min-h-8 items-center gap-1.5 rounded-lg bg-[var(--surface-800)] px-3 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--surface-700)] disabled:cursor-not-allowed disabled:opacity-50"
                      title={archived ? "Kênh đã lưu trữ không thể chỉnh sửa" : "Chỉnh sửa tên, mô tả, ngôn ngữ"}
                    >
                      <Pencil size={13} aria-hidden="true" />
                      Sửa
                    </button>
                    <button
                      type="button"
                      onClick={() => requestArchive(channel)}
                      disabled={archived || activeMutation}
                      className="inline-flex min-h-8 items-center gap-1.5 rounded-lg bg-[var(--surface-800)] px-3 text-xs font-medium text-[var(--danger)] hover:bg-[var(--surface-700)] disabled:cursor-not-allowed disabled:opacity-50"
                      title={archived ? "Kênh đã được lưu trữ" : "Lưu trữ kênh (thao tác lưu trữ duy nhất, không xóa hẳn)"}
                    >
                      <Archive size={13} aria-hidden="true" />
                      {archived ? "Đã lưu trữ" : "Lưu trữ"}
                    </button>
                    {!archived && <Check size={13} className="ml-auto text-[var(--success)]" aria-label="Kênh đang hoạt động" />}
                  </div>
                </article>
              );
            })}
          </div>
        )}

        <p className="mt-6 text-[11px] text-[var(--text-muted)]">
          Vai trò được phê duyệt (từ <code className="font-mono">GET /api/channels/roles</code>):{" "}
          {rolesQuery.data?.roles.join(", ") ?? "source, production"} — không có vai trò &quot;both&quot;. Kênh không thể xóa hẳn;
          chỉ lưu trữ (archive) theo hợp đồng.
        </p>
      </div>
    </div>
  );
}
