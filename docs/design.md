# Design

Spaceship is the screen an ops analyst opens to see the 2025 shipping book. The job is to notice what is late or stuck, read the order, and ask a question about the rows. It is not a marketing site and it is not a settings product.

## Audience and job

One person, at a desk, during the workday. They already know what a carrier and a warehouse are. The interface names those things the way the book does: `delayed`, `DHL`, `LON-FC1`, `CL-1023`. It does not rename them into friendlier abstractions.

## Tokens

One typeface: [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible), loaded from the font source package, used for titles, body, and digits. Tabular figures for counts and money. There is no second display face and no monospace label row. Order ids are the same face as everything else.

Color is a paper ledger, not a dark console and not a warm cream template.

| Token | Hex | Use |
| --- | --- | --- |
| Paper | `#E4EAE4` | Page background |
| Surface | `#F4F7F4` | Table and chat panel |
| Ink | `#1A2E24` | Text, rules, primary button |
| Arrived | `#1F6B4A` | Delivered count and badge only |
| Delay | `#B45309` | Delayed and exception only |
| Muted | `#5C6B63` | Secondary text |

In transit uses ink. Canceled uses muted. Amber and green do not appear on charts. Chat plots use ink for every bar and line. Status badges still use arrived for delivered and delay for delayed and exception.

shadcn semantic tokens (`background`, `foreground`, `primary`, `muted`, `border`, `card`) are mapped to these hex values in `apps/web/src/styles/globals.css`. Components use those tokens. Feature code does not use raw palette classes such as `text-amber-700`.

Radius is 2px. Shadows are not part of the system. Separation is a 1px ink rule at 15% opacity.

## Layout

Left aligned. The page is a route sheet.

```
Ask                                    Spaceship          1 Jan 2025 – 30 Dec 2025
one question                           The 2025 shipping book
[ transcript ]
  answer
  [ plot preview ]
[ question ] [ Ask ]                   delivered 304   delayed 55   in transit 27
                                       exception 11    canceled 3

                                       order id  client  dates  carrier  warehouse
                                       region  lane  status  sku  qty  prices  promo
                                       ------------------------------------------------
                                       ...
                                       Previous                         Next
```

On a narrow viewport the chat column stacks above the table. The status rail wraps. Nothing becomes a stack of equal cards.

Plots are not drawn on the desk page. When the question asks for a plot, the reply includes one Recharts series built from the rows Postgres returned: a line or area over time, a bar comparison, a pie for a small share of a whole, or a scatter of two numeric columns. The reply shows a dummy plot, the same bars for every chart. Hovering it shows "Click me". Activating it opens the real plot in a dialog in the center of the screen. Plot and Data are an underline row that scrolls sideways, and the data table scrolls when it overflows. Axes are labeled in the same sentence case as the rest of the UI. Bars, lines, areas, and scatter use ink. Pie slices use ink, arrived, delay, the delayed wash, and the paper greens. A question that does not ask for a plot has no chart.

## Screens

`/login` — email, password, a button that says "Sign in". The error under the form is the API detail, which is one sentence for both unknown email and wrong password. No illustration.

`/dashboard` — the desk. It requires a signed-in session. `/` redirects here. A missing session navigates to `/login`. The header button says "Sign out" and calls logout.

The order table shows ten rows at a time, with the total and a way to move by offset. Each row shows the order id, client, dates, carrier, warehouse, region, origin, destination, status, SKU, category, quantity, unit price, value, and promo. Filters are status, region, and carrier, each a select that includes "Any". Empty results say "No orders match these filters." and leave the filters in place.

The right panel is a chat. A row of conversations sits at the top and scrolls sideways. Each tab is named from its first question. The active tab uses the same surface as the transcript and covers the rule under it, so the tab and the conversation are one piece. Inactive tabs sit on the paper behind that rule, and their close control appears on hover. A plus button starts a new chat, and each tab can be closed. Closing the last one leaves an empty chat. The conversations are saved in this browser and stay after a refresh. The panel has one text area and a send icon. While the request is in flight the button is disabled and a skeleton sits in the transcript that asked. The reply is the model's paragraph and, when a plot was required, the dummy plot. If the service is unavailable the reply says "Questions are unavailable until an Anthropic key is configured." and has no plot. It does not show a stack trace.

## Writing

Sentence case. Buttons name the action: "Sign in", "Sign out", "Ask", "Next", "Previous". Status words match the data: "in transit", not "on the way". Errors say what happened and what to do. They do not apologize.

The page does not have eyebrow labels, numbered section markers, or a tagline under the product name beyond "The 2025 shipping book".

## Motion and accessibility

No entrance animation. Focus rings use the ink color and stay visible. The status rail text and the badge text meet contrast on the paper background. `prefers-reduced-motion` is respected by not adding motion in the first place. The desk works at 375px wide and at a typical laptop width. Charts get a text alternative in the status rail and in the list under the open plot, so the numbers exist outside the SVG.
