import { motion, useReducedMotion } from "motion/react"

const POINTS = [
  {
    title: "See what is late.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
        <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M12 8.5 V12 L14.5 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: "Read every order.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
        <path
          d="M7 4.5 H14 L18 8.5 V19.5 H7 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path d="M14 4.5 V8.5 H18" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M10 12.5 H15 M10 16 H15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: "Ask questions about the rows.",
    icon: (
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
        <path
          d="M5 7 H13.5 A2.5 2.5 0 0 1 13.5 12 H9 L6.5 14.5 V12 H5 A2.5 2.5 0 0 1 5 7 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M11 13.5 H18 A2 2 0 0 1 18 17.5 H16 L14.5 19.5 V17.5 H11 A2 2 0 0 1 11 13.5 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
] as const

const STOPS = ["UK", "EU", "US"] as const

export function LoginStory() {
  const reduce = useReducedMotion() === true

  return (
    <section className="flex h-full flex-col justify-between gap-10 bg-primary px-6 py-10 text-primary-foreground md:min-h-svh md:px-10 md:py-12">
      <div className="flex max-w-md flex-col gap-4">
        <h2 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Spaceship</h2>
        <p className="text-base text-primary-foreground/80">
          The company desk for every lane you ship. Late freight, the order behind it, and questions about the rows.
        </p>
      </div>
      <div className="max-w-lg">
        <svg viewBox="0 0 480 96" className="w-full text-primary-foreground" aria-hidden>
          <motion.path
            d="M20 62 C120 62 120 28 240 28 C360 28 360 62 460 62"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            initial={reduce ? false : { pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: reduce ? 0 : 1.2, ease: "easeInOut" }}
          />
          <circle cx="20" cy="62" r="4" fill="currentColor" />
          <circle cx="240" cy="28" r="4" fill="currentColor" />
          <circle cx="460" cy="62" r="4" fill="currentColor" />
          <motion.g
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: reduce ? 0 : 0.8, duration: 0.3 }}
          >
            <rect x="222" y="40" width="36" height="22" rx="3" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="M222 48 H258 M234 40 V62 M246 40 V62" fill="none" stroke="currentColor" strokeWidth="1.5" />
          </motion.g>
        </svg>
        <div className="mt-1 flex justify-between text-sm">
          {STOPS.map((stop) => (
            <span key={stop}>{stop}</span>
          ))}
        </div>
      </div>
      <motion.ul
        className="flex max-w-md flex-col gap-4 text-base"
        initial={reduce ? false : "hidden"}
        animate="show"
        variants={{
          hidden: {},
          show: { transition: { delayChildren: reduce ? 0 : 0.9, staggerChildren: 0.12 } },
        }}
      >
        {POINTS.map((point) => (
          <motion.li
            key={point.title}
            className="flex items-center gap-3"
            variants={{
              hidden: { opacity: 0, y: 8 },
              show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
            }}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
              {point.icon}
            </span>
            {point.title}
          </motion.li>
        ))}
      </motion.ul>
    </section>
  )
}
