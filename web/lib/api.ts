import { cookies } from "next/headers";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

/** Server-side fetch to the API, forwarding the member's session cookie. Returns null on 401/404. */
export async function api<T>(path: string): Promise<T | null> {
  const jar = await cookies();
  const res = await fetch(`${API_URL}${path}`, {
    headers: { cookie: jar.toString() },
    cache: "no-store",
  });
  if (res.status === 401 || res.status === 403 || res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return (await res.json()) as T;
}

// ---- shapes the API returns (kept loose on purpose; the API is the source of truth) ----
export type Tier = { name: string; emoji: string; color: string };
export type QuestSummary = {
  id: string; title: string; rank: number; difficulty: string; tier: Tier; specializations: string[]; required: boolean; taster_for: string[];
  subjects: string[]; xp: number; time_min: number | null; kind: "required" | "elective" | "capstone"; spine: boolean;
  verify_type: string; has_quiz: boolean; quiz_len: number; owner: string;
  affinity: "major" | "adjacent" | "other" | null; status?: string; tag?: string | null;
};
/** One of the member's specializations; the primary drives ranks and the nameplate. */
export type MySpecialization = { key: string; title: string; primary: boolean };
export type SpecializationOption = { key: string; title: string; blurb: string };
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
  id: number | string; name: string | null; avatar: string | null;
  specialization: string; specialization_title: string; specializations: MySpecialization[]; specialization_options?: SpecializationOption[];
  rank: number; rank_title: string; rank_color: string; xp: number; xp_floor: number; xp_next: number | null;
  streak_days: number; ue_version: string | null; rank_since: string | null; member_since: string | null;
  next_rank: { n: number; title: string; xp: number; opens: string | null; xp_to_go: number; required_left: number; tier_left: number; requirements_met: boolean; human_review: boolean } | null;
  tier_progress: { done: number; need: number; available: number; tier: string; name: string; emoji: string; color: string } | null;
  medals: { medal_key: string; earned_at: string }[]; done_count: number;
  recent_xp?: { amount: number; reason: string; created_at: string }[]; known?: boolean;
  review?: { can: boolean; mentor: boolean; pending: number }; admin?: boolean; staff?: string | null;
  avatar_frame?: string; avatar_frame_art?: string | null; title?: string | null; nameplate?: string;
};
export type ReviewItem = {
  id: number; status: string; route: string; created_at: string; decided_at: string | null; notes: string | null; reviewer_id: number | null;
  member: { id: number | string; name: string | null; avatar: string | null; rank: number | null; specialization: string | null };
  quest: QuestSummary; payload: { text?: string; ue_version?: string; attachments?: string[] };
  reviewed_by_me: boolean; blocked: string | null;
  quest_detail?: { done_when: string | null; do: string | null; checklist: { text: string; kind: string }[]; verify_type: string | null };
  actions?: { reviewer_id: number; verdict: string; is_peer: number; notes: string | null; created_at: string; name: string | null }[];
  previous?: { id: number; status: string; route: string; notes: string | null; created_at: string; decided_at: string | null; payload: Record<string, unknown> }[];
  access?: ReviewAccess;
};
export type ReviewAccess = { mentor: boolean; rank: number; can_review: boolean };
export type Specializations = {
  tiers: Record<string, { name: string; emoji: string; color: string; quiz_len: number }>;
  ranks: { n: number; key: string; title: string; tier: string; xp: number; color: string | null; opens?: string; quests_to_leave?: number }[];
  specializations: Record<string, { key: string; title: string; prefix: string | null; blurb?: string | null; capstones: Record<string, { id: string; title: string; brief: string }> }>;
  quest_count: number;
};
export type PathData = {
  specialization: string; specialization_title: string; specializations: MySpecialization[]; rank: number; now: string | null; reason: string;
  sections: { key: string; title: string; rank?: number; quests: QuestSummary[]; tier?: { done: number; need: number; available: number; tier: string; name: string; emoji: string } | null }[];
  locked: { n: number; title: string; xp: number; opens: string | null; gate_tier: { need: number; name: string } | null; quests: QuestSummary[]; tasters: { id: string; title: string }[][]; capstone: { id: string; title: string; brief: string } | null } | null;
};
export type Next = { main: QuestSummary | null; reason: string; electives: QuestSummary[]; adjacent: QuestSummary | null; remaining_minutes: number };
export type Achievement = { key: string; name: string; desc: string; icon: string; need: number; of: string; have: number; earned: boolean; earned_at: string | null; outfit?: string; badge?: number };
/** One entitlement (an unlock an account can hold) as the card editor sees it. `art` is the art-pack id for frames. */
export type EntitlementOption = { id: string; name: string; value?: string; art?: string | null; desc?: string; owned: boolean; hint: string | null; granted?: boolean };
export type EntitlementKind = "outfit" | "nameplate" | "avatar_frame" | "card_frame" | "title" | "achievement";
export type Card = Me & {
  worn: { id: string; name: string; flavour: string; tier: string; color: string; art_id: string };
  cosmetics: { nameplate?: string; banner?: string; appearance?: Record<string, string>; outfit?: string; featured?: string[]; public?: boolean; title?: string };
  style: string; body: string; nameplate: string; nameplate_id: string; avatar_frame: string; avatar_frame_art: string | null; card_frame: string; card_frame_art: string | null;
  title: string | null; title_id: string; motto: string; public: boolean;
  entitlements: { nameplate: EntitlementOption[]; avatar_frame: EntitlementOption[]; card_frame: EntitlementOption[]; title: EntitlementOption[] };
  achievements_earned: number; achievements_total: number;
  featured: Achievement[]; nameplate_colors: string[]; earned_achievements: Achievement[]; mine?: boolean;
};
