import { redirect } from "next/navigation";

export default async function ReviewItem({ params }: PageProps<"/review/[id]">) {
  const { id } = await params;
  redirect(`/admin/review/${id}`);
}
