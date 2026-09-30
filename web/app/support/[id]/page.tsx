import { redirect } from "next/navigation";

/** Tickets are read and answered in the inbox now. */
export default async function TicketPage({ params }: PageProps<"/support/[id]">) {
  const { id } = await params;
  redirect(`/inbox?ticket=${id}`);
}
