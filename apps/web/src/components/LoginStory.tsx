import { motion, useReducedMotion } from "motion/react"

const FACTS = [
  "See what is late.",
  "Read the order.",
  "Ask one question about the rows.",
] as const

const STOPS = ["UK", "EU", "US"] as const

export function LoginStory() {
  const reduce = useReducedMotion() === true

  return (
    <section className="flex h-full flex-col justify-between gap-10 bg-primary px-6 py-10 text-primary-foreground md:min-h-svh md:px-10 md:py-12">
      <div className="flex max-w-md flex-col gap-4">
        <h2 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Spaceship</h2>
        <p className="text-base text-primary-foreground/80">The company desk for the lanes it ships.</p>
      </div>
      <div className="max-w-lg">
        <svg viewBox="0 0 480 48" className="w-full text-primary-foreground" aria-hidden>
          <motion.path
            d="M16 24 H464"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            initial={reduce ? false : { pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: reduce ? 0 : 1.1, ease: "easeInOut" }}
          />
          {[16, 240, 464].map((cx) => (
            <circle key={cx} cx={cx} cy="24" r="4" fill="currentColor" />
          ))}
        </svg>
        <div className="mt-3 flex justify-between text-sm">
          {STOPS.map((stop) => (
            <span key={stop}>{stop}</span>
          ))}
        </div>
      </div>
      <motion.ul
        className="flex max-w-md flex-col gap-3 text-base"
        initial={reduce ? false : "hidden"}
        animate="show"
        variants={{
          hidden: {},
          show: { transition: { delayChildren: reduce ? 0 : 1.1, staggerChildren: 0.12 } },
        }}
      >
        {FACTS.map((fact) => (
          <motion.li
            key={fact}
            variants={{
              hidden: { opacity: 0, y: 8 },
              show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
            }}
          >
            {fact}
          </motion.li>
        ))}
      </motion.ul>
    </section>
  )
}
