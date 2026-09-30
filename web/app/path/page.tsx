import { redirect } from "next/navigation";

/** The path lives on the quest board now. Old links still work. */
export default function Path() {
  redirect("/quests?view=path");
}
