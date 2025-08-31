  export default function BackgroundFX() {
    return (
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        {/* Gradient blobs */}
        <div className="absolute -top-32 -left-32 h-[36rem] w-[36rem] rounded-full blur-3xl opacity-60 bg-blue-400/30 dark:bg-blue-500/20" />
        <div className="absolute -top-24 right-[-10rem] h-[28rem] w-[28rem] rounded-full blur-3xl opacity-50 bg-emerald-400/25 dark:bg-emerald-500/20" />
        <div className="absolute bottom-[-12rem] left-1/2 -translate-x-1/2 h-[40rem] w-[40rem] rounded-full blur-3xl opacity-40 bg-violet-400/25 dark:bg-violet-500/20" />

        {/* Subtle grid - light */}
        <div
          className="absolute inset-0 opacity-[0.08] dark:hidden"
          style={{
            backgroundImage:
              "linear-gradient(to right, #0f172a 1px, transparent 1px), linear-gradient(to bottom, #0f172a 1px, transparent 1px)",
            backgroundSize: "32px 32px, 32px 32px",
            mixBlendMode: "multiply",
          }}
        />
        {/* Subtle grid - dark */}
        <div
          className="hidden dark:block absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(to right, rgba(255,255,255,0.7) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.7) 1px, transparent 1px)",
            backgroundSize: "32px 32px, 32px 32px",
            mixBlendMode: "screen",
          }}
        />

        {/* Noise overlay */}
        <div
          className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]"
          style={{
            backgroundImage:
              "url('data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100\\' height=\\'100\\' viewBox=\\'0 0 100 100\\'><filter id=\\'n\\'><feTurbulence type=\\'fractalNoise\\' baseFrequency=\\'0.8\\' numOctaves=\\'4\\' stitchTiles=\\'stitch\\'/></filter><rect width=\\'100%\\' height=\\'100%\\' filter=\\'url(%23n)\\' opacity=\\'0.6\\'/></svg>')",
            backgroundSize: "auto 100%",
          }}
        />
      </div>
    )
  }


