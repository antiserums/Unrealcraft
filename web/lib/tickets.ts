/** Ticket vocabulary shared by server pages and the client components. Keys are what the API stores; the words
 *  are translated where they are shown. */
export type TicketMessage = { id: number; staff: boolean; body: string; created_at: string };
export type Ticket = {
  id: number; category: string; subject: string; status: "open" | "answered" | "closed"; created_at: string; updated_at: string;
  member_id: number | string; name?: string | null; avatar?: string | null; messages: TicketMessage[] | number; last?: string | null;
};
export const CATEGORY: Record<string, string> = { account: "My account", quest: "A quest", review: "A review", bug: "Something is broken", donation: "A donation", other: "Something else" };
export const STATUS: Record<string, string> = { open: "Open", answered: "Answered", closed: "Closed" };
