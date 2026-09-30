import { cookies } from "next/headers";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

/** Server-side fetch to the API, forwarding the member's session cookie. Returns null on 401/404. */
export async function api<T>(path: string): Promise<T | null> {
  const jar = await cookies();
  const res = await fetch(`${API_URL}${path}`, {
    headers: { cookie: jar.toString() },
    cache: "no-store",
  });
  if (res.status === 401 || res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

// ---- shapes the API returns (kept loose on purpose; the API is the source of truth) ----
export type Tier = { name: string; emoji: string; color: string };
export type QuestSummary = {
  id: string; title: string; rank: number; difficulty: string; tier: Tier; track: string; subjects: string[];
  xp: number; time_min: number | null; kind: "required" | "elective" | "capstone"; spine: boolean;
  verify_type: string; has_quiz: boolean; quiz_len: number; owner: string; required_for: string[];
  adjacent_for: string[]; affinity: "major" | "adjacent" | "other" | null; status?: string; tag?: string | null;
  cross?: boolean;
};
export type Reading = { label: string; url: string; kind: string };
export type ChecklistItem = { text: string; state: "done" | "todo" | "on_submit" | "honor" | "optional" };
export type QuestFull = QuestSummary & {
  why: string | null; do: string | null; reading: Reading[]; checklist: ChecklistItem[]; done_when: string | null;
  step: string | null; quiz: { q: string; choices: string[] }[]; file: string;
};
export type Progress = {
  status: string | null; quiz_passed: boolean; completed_at: string | null; unlocked: boolean; quiz_attempts: number;
  submissions: { id: number; status: string; route: string; notes: string | null; created_at: string; decided_at: string | null; payload: Record<string, unknown> }[];
} | null;
export type Me = {
  id: number; name: string | null; avatar: string | null; major: string; major_title: string; minor: string | null;
  rank: number; rank_title: string; rank_color: string; seal: string | null; xp: number; xp_floor: number; xp_next: number | null;
  streak_days: number; ue_version: string | null; rank_since: string | null; member_since: string | null;
  next_rank: { n: number; title: string; xp: number; opens: string | null; xp_to_go: number; required_left: number; tier_left: number; requirements_met: boolean; human_review: boolean } | null;
  tier_progress: { done: number; need: number; available: number; tier: string; name: string; emoji: string; color: string } | null;
  medals: { medal_key: string; earned_at: string }[]; done_count: number;
  recent_xp?: { amount: number; reason: string; created_at: string }[]; known?: boolean;
};
export type Majors = {
  tiers: Record<string, { name: string; emoji: string; color: string; quiz_len: number }>;
  ranks: { n: number; key: string; title: string; tier: string; xp: number; color: string | null; opens?: string; quests_to_leave?: number }[];
  seals: Record<string, { title: string; color: string }>;
  majors: Record<string, { key: string; title: string; prefix: string | null; seals: string[]; capstones: Record<string, { id: string; title: string; brief: string }> }>;
  quest_count: number;
};
export type PathData = {
  major: string; major_title: string; rank: number; now: string | null; reason: string;
  sections: { key: string; title: string; rank?: number; quests: QuestSummary[]; tier?: { done: number; need: number; available: number; tier: string; name: string; emoji: string } | null }[];
  locked: { n: number; title: string; xp: number; opens: string | null; gate_tier: { need: number; name: string } | null; quests: QuestSummary[]; tasters: { id: string; title: string }[][]; capstone: { id: string; title: string; brief: string } | null } | null;
};
export type Next = { main: QuestSummary | null; reason: string; electives: QuestSummary[]; adjacent: QuestSummary | null; remaining_minutes: number };
export type Achievement = { key: string; name: string; desc: string; icon: string; need: number; of: string; have: number; earned: boolean; earned_at: string | null; outfit?: string };
export type Card = Me & {
  worn: { id: string; name: string; flavour: string; tier: string; color: string; art_id: string };
  cosmetics: { nameplate?: string; banner?: string; appearance?: Record<string, string>; outfit?: string; featured?: string[]; public?: boolean };
  nameplate: string; motto: string; public: boolean; achievements_earned: number; achievements_total: number;
  featured: Achievement[]; nameplate_colors: string[]; earned_achievements: Achievement[]; mine?: boolean;
};
