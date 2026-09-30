import { redirect } from "next/navigation";

/** The review inbox lives in the admin panel now. Old links still work. */
export default function Review() {
  redirect("/admin/review");
}
