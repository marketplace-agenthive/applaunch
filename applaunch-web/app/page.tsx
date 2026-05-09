// applaunch-web/app/page.tsx — Landing page
import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 px-4 text-center">
      <div className="space-y-4 max-w-2xl">
        <h1 className="text-5xl font-bold tracking-tight">
          Deploy mobile apps{" "}
          <span className="text-green-500">in one click</span>
        </h1>
        <p className="text-xl text-muted-foreground">
          AppLaunch takes your LLM-generated React Native, Expo, or Flutter app
          and ships it to Google Play — no DevOps required.
        </p>
      </div>

      <div className="flex gap-4">
        <Link
          href="/login"
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
        >
          Get Started Free
        </Link>
        <Link
          href="https://docs.applaunch.dev"
          className="border border-border hover:bg-secondary px-8 py-3 rounded-xl transition-colors"
          target="_blank"
        >
          View Docs
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-6 mt-8 max-w-2xl text-sm">
        {[
          { icon: "⚡", title: "< 8 min builds", desc: "Parallel Android builds on dedicated workers" },
          { icon: "🔒", title: "KMS-encrypted", desc: "Your keystores never leave our encrypted vault" },
          { icon: "🤖", title: "Claude MCP", desc: "Deploy directly from a Claude conversation" },
        ].map((f) => (
          <div key={f.title} className="rounded-xl border border-border p-4 text-left space-y-1">
            <div className="text-2xl">{f.icon}</div>
            <div className="font-semibold">{f.title}</div>
            <div className="text-muted-foreground">{f.desc}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
