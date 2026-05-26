"use client";

import { useState, FormEvent } from "react";
import { useRouter }            from "next/navigation";
import Link                     from "next/link";
import { Loader2, Cpu }         from "lucide-react";
import { useAuth }              from "@/hooks/useAuth";
import { cn }                   from "@/lib/utils";

export default function RegisterPage() {
  const { register }                = useAuth();
  const router                      = useRouter();
  const [email,    setEmail]        = useState("");
  const [username, setUsername]     = useState("");
  const [password, setPassword]     = useState("");
  const [error,    setError]        = useState<string | null>(null);
  const [loading,  setLoading]      = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, username, password);
      router.push("/chat/new");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-4">
      <div className="w-full max-w-sm animate-fade-up">

        {/* Brand */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-12 h-12 rounded-2xl bg-ink flex items-center justify-center mb-4 shadow-lg">
            <Cpu size={22} className="text-amber" />
          </div>
          <h1 className="font-display text-3xl text-ink mb-1">Create account</h1>
          <p className="text-mist text-sm">Start chatting with your documents</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5 tracking-wide uppercase">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full px-4 py-3 rounded-xl border border-border bg-white text-ink text-[15px]
                         placeholder:text-mist focus:outline-none focus:border-amber/60
                         focus:ring-2 focus:ring-amber/10 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5 tracking-wide uppercase">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="yourname"
              required
              minLength={3}
              className="w-full px-4 py-3 rounded-xl border border-border bg-white text-ink text-[15px]
                         placeholder:text-mist focus:outline-none focus:border-amber/60
                         focus:ring-2 focus:ring-amber/10 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5 tracking-wide uppercase">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              required
              minLength={8}
              className="w-full px-4 py-3 rounded-xl border border-border bg-white text-ink text-[15px]
                         placeholder:text-mist focus:outline-none focus:border-amber/60
                         focus:ring-2 focus:ring-amber/10 transition-all"
            />
          </div>

          {error && (
            <p className="text-sm text-danger bg-red-50 border border-red-200 px-4 py-2.5 rounded-xl animate-fade-in">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className={cn(
              "w-full py-3 rounded-xl font-semibold text-[15px] transition-all duration-150 flex items-center justify-center gap-2",
              loading
                ? "bg-ink/60 text-paper/60 cursor-not-allowed"
                : "bg-ink text-paper hover:bg-ink/85 shadow-sm hover:shadow-md"
            )}
          >
            {loading ? <><Loader2 size={16} className="animate-spin" /> Creating account…</> : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-mist mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-amber font-medium hover:underline underline-offset-2">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
