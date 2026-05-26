import { redirect } from "next/navigation";

// The middleware handles auth redirects.
// This just sends the root URL to /chat which middleware will
// further redirect to /login if not authenticated.
export default function RootPage() {
  redirect("/chat/new");
}
