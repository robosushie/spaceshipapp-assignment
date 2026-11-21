# Design

Spaceship is the screen an ops analyst opens to see the 2025 shipping book. The job is to notice what is late or stuck, read the order, and ask a question about the rows. It is not a marketing site and it is not a settings product.

## Audience and job

One person, at a desk, during the workday. They already know what a carrier and a warehouse are. The interface names those things the way the book does: `delayed`, `DHL`, `LON-FC1`, `CL-1023`. It does not rename them into friendlier abstractions.

## Tokens

One typeface: Inter (the stand-in for the gallery face), used for titles, body, and digits. Tabular figures for counts and money. JetBrains Mono is only for code and annotations, with wider tracking. Order ids stay in Inter.

The desk, the order table, filters, and the sign-in form are 14px. The desk title is 20px. The sign-in title is 40px. The question field and the empty chat prompt stay at 16px. Chat messages and chat tabs are 14px. The left rail icons are 20px, and the rocket mark is 24px.

Color is a white gallery. Black text, white surfaces, and one electric indigo for the action that should be switched on. Charts and status stay inside that set.

| Token | Hex | Use |
| --- | --- | --- |
| Paper | `#FFFFFF` | Page, table, and chat |
| Mist | `#E2E2E2` | Quiet rules, assistant replies, hover wash |
| Ink | `#000000` | Text, outlined controls, delivered badge |
| Graphite | `#595959` | Secondary text |
| Indigo | `#4D49FC` | Sign in, the send icon, the active desk icon, exception, focus |

Delivered is a black pill. Delayed, in transit, and canceled are outlined. Exception is the indigo pill outline. Bars and lines use ink. Pie slices use ink, indigo, graphite, and mist.

shadcn semantic tokens (`background`, `foreground`, `primary`, `muted`, `border`, `card`) are mapped to these hex values in `apps/web/src/index.css`. Components use those tokens. Feature code does not use raw palette classes such as `text-amber-700`.

Radius is four steps: 2px for fine controls, 8px for inputs and outlined buttons, 16px for cards and messages, and a pill for the primary button and status chips. The only drop shadow is the open plot dialog. Table rules are mist, not black.

## Layout

Left aligned. The page is a route sheet.

```
Ask                                    Spaceship
one question
[ transcript ]
  answer
  [ plot preview ]
[ question ] [ Ask ]                   [ filter ]

                                       order id  client  dates  carrier  warehouse
                                       region  lane  status  sku  qty  prices  promo
                                       ------------------------------------------------
                                       ...
                                       < Previous                       Next >
```

On a narrow viewport the chat column stacks above the table. Nothing becomes a stack of equal cards.

Plots are not drawn on the desk page. When the question asks for a plot, the reply includes one Recharts series built from the rows Postgres returned: a line or area over time, a bar comparison, a pie for a small share of a whole, or a scatter of two numeric columns. The reply shows a short dummy plot, narrower than the message: a line over a light grid, the same drawing for every chart. Hovering it shows "Click me". Activating it opens the real plot in a dialog in the center of the screen. Plot and Data are an underline row that scrolls sideways, and the data table scrolls when it overflows. Axes are labeled in the same sentence case as the rest of the UI. Bars, lines, areas, and scatter use ink. Pie slices use ink, indigo, graphite, and mist. A question that does not ask for a plot has no chart.

## Screens

`/login` — email, password, a button that says "Sign in". The error under the form is the API detail, which is one sentence for both unknown email and wrong password. No illustration.

`/dashboard` — the desk. It requires a signed-in session. `/` redirects here. A missing session navigates to `/login`. The header button says "Sign out" and calls logout.

The order table shows forty rows at a time, with the total and a way to move by offset. Each row shows the order id, client, dates, carrier, warehouse, region, origin, destination, status, SKU, category, quantity, unit price, value, and promo. Filter, with a funnel icon, drops a sentence chip into the bar and opens a panel directly under that chip. Previous and Next carry a chevron on the side the page moves. The panel is a popover, not a hover tooltip: it holds the column, the operator, and the value, stays open while those change, and closes on Escape or a click outside. The table does not move to make room. Clicking the chip opens the same panel again. Several filters apply together. Empty results say "No orders match these filters." and leave the filters in place.

The right panel is a chat. A short vertical handle on its inner edge can be dragged, or moved with the arrow keys, to make the panel wider or narrower. That width stays in this browser. A row of conversations sits at the top and scrolls sideways. Each tab is named by gpt-5-nano from the first question, in a few words. Until that name arrives, the tab shows the question itself. The active tab uses the same surface as the transcript and covers the rule under it, so the tab and the conversation are one piece. Inactive tabs sit on the paper behind that rule, and their close control appears on hover. A plus button starts a new chat, and each tab can be closed. Closing the last one leaves an empty chat. The conversations are saved in this browser and stay after a refresh. The panel has one text area and a send icon. While the request is in flight the button is disabled and a skeleton sits in the transcript that asked. The reply is the model's paragraph and, when a plot was required, the dummy plot. If the service is unavailable the reply says "Questions are unavailable until an Anthropic key is configured." and has no plot. It does not show a stack trace.

## Writing

Sentence case. Buttons name the action: "Sign in", "Sign out", "Ask", "Next", "Previous". Status words match the data: "in transit", not "on the way". Errors say what happened and what to do. They do not apologize.

The page does not have eyebrow labels, numbered section markers, or a tagline under the product name.

## Motion and accessibility

No entrance animation. Focus rings use the ink color and stay visible. The badge text meets contrast on the paper background. `prefers-reduced-motion` is respected by not adding motion in the first place. The desk works at 375px wide and at a typical laptop width. Charts get a text alternative in the list under the open plot, so the numbers exist outside the SVG.
